#!/usr/bin/env python3
"""Camada 6 — validação determinística da saída do modelo.

A única camada não probabilística da skill: confere, no código, se o que o modelo
afirmou é conferível contra a fonte. Afirmação cuja evidência não existe na fonte é
afirmação fabricada, venha de alucinação ou de injeção bem-sucedida.

Três modos, conforme a forma do projeto (tabela da Fase 0 no SKILL.md):

  decisao   — decisão/classificação. Cada evidência traz `regra_id`, `trecho_citado` e
              `conforme` (bool). Decisão favorável exige >= 1 evidência conforme válida e
              nenhuma contrária válida; desfavorável exige >= 1 contrária válida; sem
              evidência verificável, revisão humana.
  extracao  — extração de campos: todo valor extraído existe literalmente na fonte.
  citacoes  — resumo / busca / Q&A: toda citação é rastreável à fonte.

Trecho curto demais (abaixo de MIN_CHARS após normalização) não verifica nada: um "R$"
ancora em qualquer fatura. Conta como não verificável.

Biblioteca:

    from validar_saida import validar_decisao, validar_extracao, validar_citacoes

CLI:

    python validar_saida.py decisao  saida.json regras.json fonte.txt
    python validar_saida.py extracao saida.json fonte.txt [--ignorar total data] [--numeros]
    python validar_saida.py citacoes saida.json fonte.txt

Sai não-zero quando há incoerência. Só stdlib.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

FINISH_OK = ("STOP", "FINISH_REASON_STOP")
MIN_CHARS = 12   # trecho normalizado abaixo disto não é evidência verificável


@dataclass(frozen=True)
class Vocabulario:
    """Nomes dos resultados no modo `decisao`. Trocáveis por domínio."""
    favoravel: str = "aprovado"
    desfavoravel: str = "reprovado"
    revisao: str = "revisao_humana"


@dataclass
class Resultado:
    modo: str
    incoerencias: list[str] = field(default_factory=list)
    detalhes: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.incoerencias

    def para_dict(self) -> dict:
        return {"modo": self.modo, "ok": self.ok,
                "incoerencias": self.incoerencias, **self.detalhes}


def normalizar(texto: str) -> str:
    """Colapsa espaço, remove acento e caixa.

    Comparação estritamente literal geraria falso positivo em texto de OCR, onde
    espaçamento e acentuação variam. Normalizar reduz isso sem abrir mão da checagem:
    o trecho ainda precisa EXISTIR na fonte.
    """
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", sem_acento).strip().casefold()


def presente_na_fonte(trecho: str, fonte_norm: str, min_chars: int = MIN_CHARS) -> bool | None:
    """True presente · False ausente · None curto demais para verificar."""
    norm = normalizar(trecho) if trecho else ""
    if len(norm) < min_chars:
        return None
    return norm in fonte_norm


def _so_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)


def _checar_truncamento(finish_reason: str | None) -> list[str]:
    if finish_reason and finish_reason not in FINISH_OK:
        return [f"finish_reason={finish_reason} — resposta truncada, não é saída válida"]
    return []


# ---------------------------------------------------------------- modo: decisao

def _ids_de_regras(regras: list[dict]) -> set[str]:
    return {str(r.get("regra_id") or r.get("id") or "") for r in regras} - {""}


def _triar_evidencias(
    evidencias: list[dict], ids_validos: set[str], fonte_norm: str,
    conforme_implicito: bool | None, min_chars: int,
) -> tuple[list[dict], list[dict], list[dict], list[str]]:
    """Devolve (favoráveis válidas, contrárias válidas, descartadas, incoerências).

    `conforme_implicito`: False quando a lista veio da chave `violacoes` (toda entrada é
    contrária); None quando veio de `evidencias` (cada entrada precisa trazer `conforme`).
    """
    favoraveis, contrarias, descartadas, incoerencias = [], [], [], []
    for e in evidencias:
        rid = str(e.get("regra_id", ""))
        trecho = str(e.get("trecho_citado") or e.get("trecho") or "")
        conforme = e.get("conforme", conforme_implicito)
        if rid not in ids_validos:
            descartadas.append(e)
            incoerencias.append(f"regra_id {rid!r} não existe no conjunto recuperado — descartada")
            continue
        if conforme is None:
            descartadas.append(e)
            incoerencias.append(f"evidência {rid} sem campo `conforme` — não verificável")
            continue
        presenca = presente_na_fonte(trecho, fonte_norm, min_chars)
        if presenca is None:
            descartadas.append(e)
            incoerencias.append(
                f"evidência {rid} sem trecho ou com trecho abaixo de {min_chars} caracteres — "
                "não verificável")
            continue
        if presenca is False:
            descartadas.append(e)
            incoerencias.append(f"trecho citado para {rid} não aparece na fonte — evidência fabricada")
            continue
        (favoraveis if bool(conforme) else contrarias).append(e)
    return favoraveis, contrarias, descartadas, incoerencias


def validar_decisao(
    saida: dict,
    regras: list[dict],
    texto_fonte: str,
    manipulacao_detectada: bool = False,
    finish_reason: str | None = None,
    vocab: Vocabulario | None = None,
    min_chars: int = MIN_CHARS,
) -> Resultado:
    """Decisão/classificação: a decisão precisa ser coerente com evidência conferível.

    Regras:
    - favorável: >= 1 evidência `conforme: true` válida e nenhuma `conforme: false` válida;
    - desfavorável: >= 1 evidência `conforme: false` válida;
    - qualquer incoerência, evidência não verificável ou manipulação detectada com decisão
      favorável: revisão humana.
    Favorável sem evidência é exatamente a saída que uma injeção bem-sucedida produz; por
    isso não passa.
    """
    vocab = vocab or Vocabulario()
    original = saida.get("veredito") or saida.get("decisao")
    fonte_norm = normalizar(texto_fonte)

    if "violacoes" in saida:
        lista, implicito = saida.get("violacoes") or [], False
    else:
        lista, implicito = saida.get("evidencias") or [], None
    favoraveis, contrarias, descartadas, incoerencias = _triar_evidencias(
        lista, _ids_de_regras(regras), fonte_norm, implicito, min_chars)
    incoerencias = _checar_truncamento(finish_reason) + incoerencias

    if original == vocab.favoravel:
        if contrarias:
            incoerencias.append("decisão favorável com evidência contrária válida — incoerente")
        if not favoraveis:
            incoerencias.append("decisão favorável sem evidência conforme verificável — sem base")
    elif original == vocab.desfavoravel:
        if not contrarias:
            incoerencias.append("decisão desfavorável sem evidência contrária válida — sem base verificável")
    elif original != vocab.revisao:
        incoerencias.append(f"decisão {original!r} fora do vocabulário")

    final = vocab.revisao if incoerencias else original
    if manipulacao_detectada and final == vocab.favoravel:
        incoerencias.append("manipulação detectada — decisão favorável automática bloqueada")
        final = vocab.revisao

    return Resultado("decisao", incoerencias, {
        "decisao_original": original,
        "decisao_final": final or vocab.revisao,
        "rebaixada": (final or vocab.revisao) != original,
        "evidencias_favoraveis": favoraveis,
        "evidencias_contrarias": contrarias,
        "evidencias_descartadas": descartadas,
    })


# --------------------------------------------------------------- modo: extracao

def validar_extracao(
    campos: dict, texto_fonte: str, finish_reason: str | None = None,
    ignorar: tuple[str, ...] = (), numeros: bool = False, min_chars: int = MIN_CHARS,
) -> Resultado:
    """Extração: todo valor extraído precisa existir literalmente na fonte.

    `ignorar`: campos legitimamente derivados (soma, data normalizada, categoria), que não
    ancoram por definição — exceção explícita, nunca comportamento padrão.
    `numeros`: opcional; valor só de dígitos (após tirar pontuação) é aceito se a sequência
    de dígitos aparece na fonte (18500 ancora em "18.500,00"). Mais permissivo; use só em
    campos numéricos conhecidos.
    """
    fonte_norm = normalizar(texto_fonte)
    fonte_digitos = _so_digitos(texto_fonte) if numeros else ""
    incoerencias = _checar_truncamento(finish_reason)
    ancorados: dict[str, list[str]] = {}
    fabricados: dict[str, list[str]] = {}
    nao_verificaveis: dict[str, list[str]] = {}

    for campo, valor in campos.items():
        if campo in ignorar or valor in (None, "", [], {}):
            continue
        for item in (valor if isinstance(valor, list) else [valor]):
            texto = str(item)
            presenca = presente_na_fonte(texto, fonte_norm, min_chars)
            if presenca is None and numeros and _so_digitos(texto):
                presenca = _so_digitos(texto) in fonte_digitos
            elif presenca is None and len(normalizar(texto)) >= 1 and len(normalizar(texto)) < min_chars:
                # valor curto (número, sigla, data): aceita match literal exato de token
                presenca = bool(re.search(rf"(?<![\w]){re.escape(normalizar(texto))}(?![\w])", fonte_norm))
            if presenca is True:
                ancorados.setdefault(campo, []).append(texto)
            elif presenca is False:
                fabricados.setdefault(campo, []).append(texto)
                incoerencias.append(
                    f"campo {campo!r} com valor {texto[:60]!r} não aparece na fonte — "
                    "valor fabricado ou inferido (campo derivado? use --ignorar)")
            else:
                nao_verificaveis.setdefault(campo, []).append(texto)
                incoerencias.append(f"campo {campo!r} com valor {texto[:60]!r} curto demais para verificar")

    return Resultado("extracao", incoerencias, {
        "campos_ancorados": ancorados, "campos_fabricados": fabricados,
        "campos_nao_verificaveis": nao_verificaveis,
    })


# --------------------------------------------------------------- modo: citacoes

def validar_citacoes(
    citacoes: list[str], texto_fonte: str, finish_reason: str | None = None,
    min_chars: int = MIN_CHARS,
) -> Resultado:
    """Resumo / busca / Q&A: toda citação precisa ser rastreável à fonte."""
    fonte_norm = normalizar(texto_fonte)
    incoerencias = _checar_truncamento(finish_reason)
    rastreaveis, fabricadas, curtas = [], [], []

    for c in citacoes:
        presenca = presente_na_fonte(str(c), fonte_norm, min_chars)
        if presenca is True:
            rastreaveis.append(str(c))
        elif presenca is False:
            fabricadas.append(str(c))
            incoerencias.append(f"citação não encontrada na fonte: {str(c)[:80]!r}")
        else:
            curtas.append(str(c))
            incoerencias.append(f"citação curta demais para verificar: {str(c)[:80]!r}")

    return Resultado("citacoes", incoerencias, {
        "citacoes_rastreaveis": rastreaveis, "citacoes_fabricadas": fabricadas,
        "citacoes_nao_verificaveis": curtas,
    })


# ------------------------------------------------------------------------- CLI

def _ler_json(caminho: Path):
    return json.loads(caminho.read_text(encoding="utf-8"))


def _executar(args) -> Resultado:
    fonte = args.fonte.read_text(encoding="utf-8")
    saida = _ler_json(args.saida)
    if args.modo == "decisao":
        return validar_decisao(saida, _ler_json(args.regras), fonte,
                               manipulacao_detectada=args.manipulacao_detectada,
                               finish_reason=args.finish_reason, min_chars=args.min_chars)
    if args.modo == "extracao":
        campos = saida if isinstance(saida, dict) else {"_": saida}
        return validar_extracao(campos, fonte, finish_reason=args.finish_reason,
                                ignorar=tuple(args.ignorar or ()), numeros=args.numeros,
                                min_chars=args.min_chars)
    citacoes = saida if isinstance(saida, list) else saida.get("citacoes", [])
    return validar_citacoes(citacoes, fonte, finish_reason=args.finish_reason,
                            min_chars=args.min_chars)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="modo", required=True)

    for modo in ("decisao", "extracao", "citacoes"):
        s = sub.add_parser(modo)
        s.add_argument("saida", type=Path, help="JSON da saída do modelo")
        if modo == "decisao":
            s.add_argument("regras", type=Path, help="JSON das regras recuperadas")
            s.add_argument("--manipulacao-detectada", action="store_true")
        s.add_argument("fonte", type=Path, help="texto da fonte (documento extraído)")
        s.add_argument("--finish-reason", default=None)
        s.add_argument("--min-chars", type=int, default=MIN_CHARS,
                       help=f"trecho abaixo disto não verifica (default {MIN_CHARS})")
        if modo == "extracao":
            s.add_argument("--ignorar", nargs="*", help="campos derivados, não literais")
            s.add_argument("--numeros", action="store_true",
                           help="aceita valor numérico pela sequência de dígitos")

    args = p.parse_args()
    resultado = _executar(args)
    print(json.dumps(resultado.para_dict(), ensure_ascii=False, indent=2))
    if not resultado.ok:
        print(f"\nSAÍDA REPROVADA no modo {resultado.modo} — ver incoerencias.", file=sys.stderr)
    return 0 if resultado.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

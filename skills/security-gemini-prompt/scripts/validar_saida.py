#!/usr/bin/env python3
"""Camada 6 — validação determinística da saída do modelo.

A única camada não probabilística da skill: confere, no código, se o que o modelo
afirmou é conferível contra a fonte. Afirmação cuja evidência não existe na fonte é
afirmação fabricada, venha de alucinação ou de injeção bem-sucedida.

Três modos, conforme a forma do projeto (tabela da Fase 0 no SKILL.md):

  decisao   — decisão/classificação: coerência decisão × evidência, regra existente,
              trecho presente na fonte.
  extracao  — extração de campos: todo valor extraído existe literalmente na fonte.
  citacoes  — resumo / busca / Q&A: toda citação é rastreável à fonte.

Biblioteca:

    from validar_saida import validar_decisao, validar_extracao, validar_citacoes

CLI:

    python validar_saida.py decisao  saida.json regras.json fonte.txt
    python validar_saida.py extracao saida.json fonte.txt
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


def presente_na_fonte(trecho: str, fonte_norm: str) -> bool:
    return bool(trecho) and normalizar(trecho) in fonte_norm


def _checar_truncamento(finish_reason: str | None) -> list[str]:
    if finish_reason and finish_reason not in FINISH_OK:
        return [f"finish_reason={finish_reason} — resposta truncada, não é saída válida"]
    return []


# ---------------------------------------------------------------- modo: decisao

def _ids_de_regras(regras: list[dict]) -> set[str]:
    return {str(r.get("regra_id") or r.get("id") or "") for r in regras} - {""}


def _triar_evidencias(
    evidencias: list[dict], ids_validos: set[str], fonte_norm: str
) -> tuple[list[dict], list[dict], list[str]]:
    validas, descartadas, incoerencias = [], [], []
    for e in evidencias:
        rid = str(e.get("regra_id", ""))
        trecho = str(e.get("trecho_citado") or e.get("trecho") or "")
        if rid not in ids_validos:
            descartadas.append(e)
            incoerencias.append(f"regra_id {rid!r} não existe no conjunto recuperado — descartada")
        elif trecho and not presente_na_fonte(trecho, fonte_norm):
            descartadas.append(e)
            incoerencias.append(f"trecho citado para {rid} não aparece na fonte — evidência fabricada")
        else:
            if not trecho:
                incoerencias.append(f"evidência {rid} sem trecho citado — não verificável")
            validas.append(e)
    return validas, descartadas, incoerencias


def validar_decisao(
    saida: dict,
    regras: list[dict],
    texto_fonte: str,
    manipulacao_detectada: bool = False,
    finish_reason: str | None = None,
    vocab: Vocabulario | None = None,
) -> Resultado:
    """Decisão/classificação: a decisão precisa ser coerente com evidência conferível."""
    vocab = vocab or Vocabulario()
    original = saida.get("veredito") or saida.get("decisao")
    fonte_norm = normalizar(texto_fonte)

    validas, descartadas, incoerencias = _triar_evidencias(
        saida.get("violacoes") or saida.get("evidencias") or [],
        _ids_de_regras(regras), fonte_norm,
    )
    incoerencias = _checar_truncamento(finish_reason) + incoerencias
    final = vocab.revisao if incoerencias else original

    if original == vocab.favoravel and validas:
        incoerencias.append("decisão favorável com evidência válida em contrário — incoerente")
        final = vocab.revisao
    if original == vocab.desfavoravel and not validas:
        incoerencias.append("decisão desfavorável sem evidência válida — sem base verificável")
        final = vocab.revisao
    if manipulacao_detectada and final == vocab.favoravel:
        incoerencias.append("manipulação detectada — decisão favorável automática bloqueada")
        final = vocab.revisao
    if original not in (vocab.favoravel, vocab.desfavoravel, vocab.revisao):
        incoerencias.append(f"decisão {original!r} fora do vocabulário")
        final = vocab.revisao

    return Resultado("decisao", incoerencias, {
        "decisao_original": original,
        "decisao_final": final or vocab.revisao,
        "rebaixada": (final or vocab.revisao) != original,
        "evidencias_validas": validas,
        "evidencias_descartadas": descartadas,
    })


# --------------------------------------------------------------- modo: extracao

def validar_extracao(
    campos: dict, texto_fonte: str, finish_reason: str | None = None,
    ignorar: tuple[str, ...] = (),
) -> Resultado:
    """Extração: todo valor extraído precisa existir literalmente na fonte."""
    fonte_norm = normalizar(texto_fonte)
    incoerencias = _checar_truncamento(finish_reason)
    ancorados: dict[str, str] = {}
    fabricados: dict[str, str] = {}

    for campo, valor in campos.items():
        if campo in ignorar or valor in (None, "", [], {}):
            continue
        for item in (valor if isinstance(valor, list) else [valor]):
            texto = str(item)
            if presente_na_fonte(texto, fonte_norm):
                ancorados[campo] = texto
            else:
                fabricados[campo] = texto
                incoerencias.append(
                    f"campo {campo!r} com valor {texto[:60]!r} não aparece na fonte — "
                    "valor fabricado ou inferido"
                )

    return Resultado("extracao", incoerencias, {
        "campos_ancorados": ancorados, "campos_fabricados": fabricados,
    })


# --------------------------------------------------------------- modo: citacoes

def validar_citacoes(
    citacoes: list[str], texto_fonte: str, finish_reason: str | None = None,
) -> Resultado:
    """Resumo / busca / Q&A: toda citação precisa ser rastreável à fonte."""
    fonte_norm = normalizar(texto_fonte)
    incoerencias = _checar_truncamento(finish_reason)
    rastreaveis, fabricadas = [], []

    for c in citacoes:
        (rastreaveis if presente_na_fonte(str(c), fonte_norm) else fabricadas).append(str(c))
    for c in fabricadas:
        incoerencias.append(f"citação não encontrada na fonte: {c[:80]!r}")

    return Resultado("citacoes", incoerencias, {
        "citacoes_rastreaveis": rastreaveis, "citacoes_fabricadas": fabricadas,
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
                               finish_reason=args.finish_reason)
    if args.modo == "extracao":
        campos = saida if isinstance(saida, dict) else {"_": saida}
        return validar_extracao(campos, fonte, finish_reason=args.finish_reason,
                                ignorar=tuple(args.ignorar or ()))
    citacoes = saida if isinstance(saida, list) else saida.get("citacoes", [])
    return validar_citacoes(citacoes, fonte, finish_reason=args.finish_reason)


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
        if modo == "extracao":
            s.add_argument("--ignorar", nargs="*", help="campos derivados, não literais")

    args = p.parse_args()
    resultado = _executar(args)
    print(json.dumps(resultado.para_dict(), ensure_ascii=False, indent=2))
    if not resultado.ok:
        print(f"\nSAÍDA REPROVADA no modo {resultado.modo} — ver incoerencias.", file=sys.stderr)
    return 0 if resultado.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fase 1 — varredura de fragilidades de prompt injection num projeto Gemini/Vertex.

Emite achados por severidade, com arquivo:linha, código do catálogo
(references/fragilidades.md) e correção. Sai não-zero se houver achado.

Heurístico por padrão textual. Ausência de sinal não prova ausência de defesa — prova
que ela não foi reconhecida. Confirme lendo o código antes de concluir.

Uso:
    python auditar_prompt.py <arquivo_ou_diretorio> [--json] [--min-severidade alta]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

IGNORAR = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build",
           ".mypy_cache", ".pytest_cache", ".tox"}
EXTENSOES = {".py", ".ts", ".js", ".java", ".kt", ".go", ".rb"}
SEVERIDADES = ("CRÍTICA", "ALTA", "MÉDIA", "BAIXA")


@dataclass(frozen=True)
class Regra:
    codigo: str
    severidade: str
    titulo: str
    tipo: str            # "ausente" | "presente" | "condicional"
    padrao: str
    risco: str
    correcao: str
    gatilho: str | None = None   # só para "condicional"


RX_TAG = (r"<\s*(documento_nao_confiavel|conteudo_nao_confiavel|untrusted|"
          r"untrusted_content|user_content|document)\s*>")

REGRAS: list[Regra] = [
    Regra("F-01", "CRÍTICA", "Conteúdo não confiável sem delimitação", "ausente", RX_TAG,
          "sem fronteira não há distinção entre instrução e dado; as camadas de prompt "
          "perdem o referente",
          "envolver em <documento_nao_confiavel> e declarar a natureza da tag na system "
          "instruction (camada 2)"),
    Regra("F-03", "CRÍTICA", "Sem saída estruturada", "ausente",
          r"response_schema|responseSchema|response_mime_type|responseMimeType",
          "sem estrutura não há o que validar; a camada 6 fica impossível",
          "responseSchema exigindo evidência (regra_id + trecho_citado), não booleano"),
    Regra("F-02", "CRÍTICA", "Saída aceita sem validação determinística", "ausente",
          r"validar_saida|validar_decisao|validar_extracao|validar_citacoes"
          r"|presente_na_fonte|trecho_citado|evidencia_verificada|validar\s*\(",
          "o resultado do modelo é usado direto; toda a defesa vira aposta no que o "
          "atacante ataca",
          "scripts/validar_saida.py no modo da forma do projeto: decisao, extracao ou citacoes"),
    Regra("F-04", "CRÍTICA", "Detector calibrado só para verbo imperativo", "condicional",
          r"(?i)(source status|disclosure policy|nota interna|compliance[_ ]?review|"
          r"trust_level|status[_ ]da[_ ]revisao|impersona|dacsi|sinal[_ ]de[_ ]controle)",
          "payload DACSI tem 0 pistas de comando; evasão medida em 100% das famílias "
          "controle e cifrada",
          "cobrir as três famílias da camada 4; medir com red_team_local.py",
          gatilho=r"(?i)\b(ignore|ignorar|desconsidere|jailbreak|prompt[_ ]?injection)\b"),
    Regra("F-07", "ALTA", "Tag de fechamento não escapada", "ausente",
          r"(?i)\.replace\s*\(\s*[\"']</|escapar_tag|sanitizar_tag|escape_closing",
          "o documento fecha a própria tag e o resto passa a ser lido como confiável",
          "escapar a sequência de fechamento antes de inserir o texto extraído"),
    Regra("F-08", "ALTA", "Sem reforço depois do conteúdo", "ausente",
          r"(?i)(fim do conte[uú]do n[aã]o confi[aá]vel|reforco[_ ]seguranca|"
          r"security[_ ]reinforcement|thought[_ ]reinforcement)",
          "o efeito de recência favorece o fim do documento, onde o atacante põe a injeção",
          "reforço de segurança APÓS o bloco de conteúdo não confiável"),
    Regra("F-06", "ALTA", "finish_reason não verificado", "condicional",
          r"finish_reason|finishReason",
          "com responseSchema, MAX_TOKENS devolve text=None e parsed=None sem exceção; "
          "vira 'erro de parsing' e pode virar decisão se houver fallback",
          "checar finish_reason antes de ler a saída; truncamento é erro, não resultado",
          gatilho=r"response_schema|responseSchema|response_mime_type"),
    Regra("F-11", "ALTA", "Base de conhecimento sem revisão na ingestão", "ausente",
          r"(?i)(revisao[_ ]ingestao|aprovar[_ ]regra|assinatura[_ ]regra|"
          r"regra[_ ]aprovada|signed_rule)",
          "PoisonedRAG reporta até 97% de ASR contra bases; se o lado confiável é "
          "gravável sem revisão, a separação estrutural perde o chão",
          "revisão humana ou assinatura na ingestão; segregar base compartilhada"),
    Regra("F-12", "MÉDIA", "Sem redação em tempo de recuperação", "ausente",
          r"(?i)\b(redigir|redact|placeholder|mascarar|de[_ ]?identific)\w*\s*\(",
          "valores sensíveis entram no prompt em claro; é a mitigação com melhor número "
          "medido (divulgação indevida a 0,0%)",
          "placeholder antes de montar o prompt; restaurar depois se a política permitir"),
    Regra("F-13", "MÉDIA", "Model Armor sem fatiamento em janelas", "condicional",
          r"(?i)(512|janela|chunk|fatia|overlap|sobrepos)",
          "o filtro de prompt injection aceita 512 tokens; sem fatiar, a maior parte do "
          "texto nunca é classificada e o painel mostra 'protegido'",
          "extrair texto, fatiar em janelas sobrepostas, agregar; indisponibilidade é "
          "'não classificado', não 'limpo'",
          gatilho=r"(?i)model[_ ]?armor|modelArmorConfig"),
    Regra("F-14", "MÉDIA", "Hierarquia declarada só como proibição", "ausente",
          r"(?i)(instru\w+ v[eê]m exclusivamente|vem exclusivamente desta|"
          r"instruction hierarchy|fonte leg[ií]tima de instru)",
          "proibir uma frase endereça a frase; afirmar a fonte endereça a classe, "
          "inclusive DACSI, que não usa imperativo",
          "declarar a fonte legítima + cláusula sobre texto que AFIRME ser nota oficial, "
          "política ou metadado"),
    Regra("F-16", "MÉDIA", "Floor setting em ambiente sem acesso ao projeto", "presente",
          r"(?i)floor[_ ]?setting",
          "floor setting é configuração de projeto; se só arquivos versionados são "
          "editáveis, é recomendação inaplicável que simula tratamento",
          "usar template por request via modelArmorConfig — confirme a superfície editável"),
    Regra("F-22", "MÉDIA", "Defesa apoiada em temperature baixa (modelo a ignora)", "condicional",
          r"(?i)system_instruction|systemInstruction|determinismo|criterio_ordenado",
          "em gemini-3.7-flash / 3.6-flash / 3.5-flash-lite, temperature/topP/topK são "
          "depreciados e ignorados: a defesa existe no código e não existe em execução",
          "mover o determinismo para system instruction: formato, critério ordenado, "
          "o que fazer em ambiguidade, o que não inferir",
          gatilho=r"(?i)gemini-3\.(7-flash|6-flash|5-flash-lite)"),
    Regra("F-23", "MÉDIA", "Conteúdo não confiável em media_resolution baixa", "presente",
          r"(?i)media_?[rR]esolution[\"']?\s*[:=]\s*[\"']?low\b",
          "resolução baixa esconde o payload do classificador e da revisão humana, "
          "não do modelo; não é sanitização",
          "resolução suficiente na parte avaliada; economize nas partes de contexto"),
    Regra("F-17", "BAIXA", "Spotlighting agressivo sobre texto extraído", "presente",
          r"(?i)(rot13|datamarking|b64encode\s*\(.{0,40}(peca|documento|texto_extraido))",
          "datamarking e encoding degradam texto de OCR, que é o que a avaliação precisa "
          "ler; custo em falso negativo pode superar o ganho",
          "delimiting + reforço; datamarking só em texto limpo, encoding não"),
]

# Restrito ao que aparece DENTRO do texto do prompt. Um parâmetro chamado `regras`
# na assinatura da função não indica a posição do bloco no prompt montado.
RX_REGRAS_CONF = re.compile(
    r"(?i)(regras?\s+aplic|rules?\s+appl|pol[ií]ticas?\s+aplic"
    r"|\{\s*regras?\w*\s*\}|\{\s*rules?\w*\s*\}"
    r"|\bSYSTEM_?(PROMPT|INSTRUCTION)?\b|system_instruction)")
RX_CONTEUDO = re.compile(RX_TAG)


def arquivos(alvo: Path):
    if alvo.is_file():
        yield alvo
        return
    for caminho in alvo.rglob("*"):
        if caminho.is_file() and caminho.suffix in EXTENSOES and not IGNORAR & set(caminho.parts):
            yield caminho


def _checar_ordem(caminho: Path, texto: str) -> list[str]:
    """Sinaliza quando o bloco não confiável aparece antes do bloco de regras.

    Compara offsets no arquivo inteiro, não número de linha: prompts costumam ser
    montados numa única f-string multilinha.
    """
    tag = RX_CONTEUDO.search(texto)
    regras = RX_REGRAS_CONF.search(texto)
    if not (tag and regras) or tag.start() >= regras.start():
        return []
    linha_tag = texto.count("\n", 0, tag.start()) + 1
    linha_regras = texto.count("\n", 0, regras.start()) + 1
    return [f"{caminho}:{linha_tag} (bloco de regras só em :{linha_regras})"]


def _indexar(alvo: Path) -> tuple[dict[str, list[str]], list[str]]:
    """Devolve (padrão -> ocorrências 'arquivo:linha', avisos de ordem)."""
    rx = {r.codigo: re.compile(r.padrao) for r in REGRAS}
    rx_gat = {r.codigo: re.compile(r.gatilho) for r in REGRAS if r.gatilho}
    ocorrencias: dict[str, list[str]] = {r.codigo: [] for r in REGRAS}
    gatilhos: dict[str, list[str]] = {c: [] for c in rx_gat}
    ordem: list[str] = []

    for caminho in arquivos(alvo):
        try:
            linhas = caminho.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for n, linha in enumerate(linhas, 1):
            ref = f"{caminho}:{n}"
            for codigo, r in rx.items():
                if r.search(linha):
                    ocorrencias[codigo].append(ref)
            for codigo, g in rx_gat.items():
                if g.search(linha):
                    gatilhos[codigo].append(ref)
        ordem.extend(_checar_ordem(caminho, "\n".join(linhas)))

    ocorrencias["_gatilhos"] = gatilhos  # type: ignore[assignment]
    return ocorrencias, ordem


def auditar(alvo: Path) -> list[dict]:
    ocorrencias, ordem = _indexar(alvo)
    gatilhos: dict[str, list[str]] = ocorrencias.pop("_gatilhos")  # type: ignore[arg-type]
    achados: list[dict] = []

    def add(regra: Regra, onde: list[str]):
        achados.append({
            "codigo": regra.codigo, "severidade": regra.severidade,
            "titulo": regra.titulo, "onde": onde,
            "risco": regra.risco, "correcao": regra.correcao,
        })

    for regra in REGRAS:
        hits = ocorrencias[regra.codigo]
        if regra.tipo == "ausente" and not hits:
            add(regra, [])
        elif regra.tipo == "presente" and hits:
            add(regra, hits)
        elif regra.tipo == "condicional" and gatilhos.get(regra.codigo) and not hits:
            add(regra, gatilhos[regra.codigo][:3])

    if ordem:
        add(Regra("F-05", "CRÍTICA", "Conteúdo não confiável antes das instruções",
                  "presente", "", "o documento é lido antes das regras que deveriam "
                  "governá-lo, e o prefixo cacheável some junto",
                  "reordenar: estável primeiro, não confiável por último"), ordem)

    return sorted(achados, key=lambda a: SEVERIDADES.index(a["severidade"]))


def imprimir(achados: list[dict], alvo: Path) -> None:
    if not achados:
        print(f"Nenhum achado em {alvo}.\n"
              "Heurístico: confirme lendo o código e passe o projeto pelo catálogo "
              "completo em references/fragilidades.md (F-01 a F-21).")
        return

    contagem = {s: sum(1 for a in achados if a["severidade"] == s) for s in SEVERIDADES}
    resumo = "  ".join(f"{s}: {n}" for s, n in contagem.items() if n)
    print(f"{len(achados)} achado(s) — {resumo}\n")

    for a in achados:
        print(f"[{a['severidade']}] {a['codigo']} · {a['titulo']}")
        if a["onde"]:
            for onde in a["onde"][:3]:
                print(f"  onde:     {onde}")
            if len(a["onde"]) > 3:
                print(f"            ... (+{len(a['onde']) - 3})")
        else:
            print("  onde:     nenhum sinal da camada em todo o projeto")
        print(f"  risco:    {a['risco']}")
        print(f"  correção: {a['correcao']}\n")

    print("Ordem de correção: críticas primeiro, uma por vez, verificando cada uma "
          "(Fase 3 e 4 do SKILL.md).")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("alvo", type=Path)
    p.add_argument("--json", action="store_true")
    p.add_argument("--min-severidade", choices=[s.lower() for s in SEVERIDADES], default=None)
    args = p.parse_args()

    if not args.alvo.exists():
        print(f"erro: {args.alvo} não existe", file=sys.stderr)
        return 2

    achados = auditar(args.alvo)
    if args.min_severidade:
        teto = SEVERIDADES.index(args.min_severidade.upper())
        achados = [a for a in achados if SEVERIDADES.index(a["severidade"]) <= teto]

    if args.json:
        print(json.dumps(achados, ensure_ascii=False, indent=2))
    else:
        imprimir(achados, args.alvo)
    return 1 if achados else 0


if __name__ == "__main__":
    raise SystemExit(main())

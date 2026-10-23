#!/usr/bin/env python3
"""Fase 1 — varredura de fragilidades de prompt injection num projeto Gemini/Vertex.

Duas classes de saída:

  ACHADOS     — regra com evidência em arquivo:linha (padrão presente, ou ausente onde um
                gatilho exige). Contam no total e no código de saída.
  VERIFICAR   — camada que o script NÃO reconheceu no projeto. Não é achado: o script
                reconhece a convenção desta skill (tags, nomes de função, frases em pt/en)
                e padrões estruturais; defesa escrita de outro jeito aparece aqui. Vai para
                leitura manual, sem severidade, sem contar no exit code.

Sem sinal de Gemini/Vertex no projeto, nada é auditado (exit 0).

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

# gate: o projeto usa Gemini/Vertex?
RX_GEMINI = re.compile(
    r"google\.genai|from google import genai|google\.generativeai|google-genai|vertexai|"
    r"aiplatform|generate_content|generateContent|GenerateContentConfig|[\"']gemini-[a-z0-9]")

# modelos que ignoram temperature/topP/topK (references/fragilidades.md, F-22)
RX_MODELO_IGNORA = re.compile(r"gemini-(4-argon|3\.8-flash|3\.7-flash|3\.6-flash|3\.5-flash-lite)")
RX_AMOSTRAGEM = re.compile(r"\b(temperature|top_p|top_k|topP|topK)\s*[:=]")


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


RX_TAG = (r"<\s*(documento_nao_confiavel|conteudo_nao_confiavel|untrusted|untrusted_content|"
          r"untrusted_document|retrieved_content|external_content|user_provided_content|"
          r"user_content|document)\s*>")

REGRAS: list[Regra] = [
    Regra("F-01", "CRÍTICA", "Conteúdo não confiável sem delimitação", "ausente", RX_TAG,
          "sem fronteira não há distinção entre instrução e dado; as camadas de prompt "
          "perdem o referente",
          "envolver em <documento_nao_confiavel> (ou equivalente) e declarar a natureza da tag "
          "na system instruction (camada 2)"),
    Regra("F-03", "CRÍTICA", "Sem saída estruturada", "ausente",
          r"response_schema|responseSchema|response_mime_type|responseMimeType|json_schema",
          "sem estrutura não há o que validar; a camada 6 fica impossível",
          "responseSchema exigindo evidência (regra_id + trecho_citado + conforme), não booleano"),
    Regra("F-02", "CRÍTICA", "Saída aceita sem validação determinística", "ausente",
          r"validar_saida|validar_decisao|validar_extracao|validar_citacoes|validate_output|"
          r"validate_decision|validate_extraction|verify_evidence|verify_citations|"
          r"presente_na_fonte|present_in_source|trecho_citado|anchored|grounded_in_source|"
          # estrutural: função aplicada sobre a saída, exceto parse/log/print
          r"evidencia_verificada|"
          r"\b(?!(loads|load|print|len|str|dict|list|repr|log\w*|logger\w*|json|type)\b)"
          r"\w+\s*\(\s*(resp|response|result)\.(parsed|text)\b",
          "o resultado do modelo é usado direto; toda a defesa vira aposta no que o "
          "atacante ataca",
          "scripts/validar_saida.py no modo da forma do projeto: decisao, extracao ou citacoes"),
    Regra("F-04", "CRÍTICA", "Detector calibrado só para verbo imperativo", "condicional",
          r"(?i)(source status|disclosure policy|nota interna|official internal|compliance[_ ]?review|"
          r"trust_level|status[_ ]da[_ ]revisao|impersona|dacsi|sinal[_ ]de[_ ]controle|"
          r"control[_ ]signal|provenance)",
          "payload DACSI tem 0 pistas de comando; evasão de até 100% nas famílias controle e "
          "cifrada, medida com red_team_local.py",
          "cobrir as quatro famílias da camada 4; medir com red_team_local.py --baseline",
          # só dispara em linha que PARECE lista/regex de detecção: alternância `|` ou re.*(
          gatilho=r"(?i)(re\.\w+\s*\(|\|)[^\n]*\b(ignore|ignorar|desconsidere|disregard|jailbreak)\b"
                  r"|\b(ignore|ignorar|desconsidere|disregard|jailbreak)\b[^\n]*(\||re\.\w+\s*\()"),
    Regra("F-07", "ALTA", "Tag de fechamento não escapada", "ausente",
          r"(?i)\.replace\s*\(\s*[\"']</|escapar_tag|sanitizar_tag|escape_closing|escape_tag|"
          r"sanitize_tag|html\.escape|xml\.sax\.saxutils\.escape",
          "o documento fecha a própria tag e o resto passa a ser lido como confiável",
          "escapar a sequência de fechamento antes de inserir o texto extraído"),
    Regra("F-08", "ALTA", "Sem reforço depois do conteúdo", "ausente",
          r"(?i)(fim do conte[uú]do n[aã]o confi[aá]vel|end of untrusted|reforco[_ ]seguranca|"
          r"security[_ ]reinforcement|thought[_ ]reinforcement|reminder:|lembrete:|"
          r"</(documento_nao_confiavel|untrusted\w*|retrieved_content)>\s*[\"']?\s*\\n\s*[\"']?\s*\w)",
          "o efeito de recência favorece o fim do documento, onde o atacante põe a injeção",
          "reforço de segurança APÓS o bloco de conteúdo não confiável"),
    Regra("F-06", "ALTA", "finish_reason não verificado", "condicional",
          r"finish_reason|finishReason",
          "com responseSchema, MAX_TOKENS devolve text=None e parsed=None sem exceção; "
          "vira 'erro de parsing' e pode virar decisão se houver fallback",
          "checar finish_reason antes de ler a saída; truncamento é erro, não resultado",
          gatilho=r"response_schema|responseSchema|response_mime_type|json_schema"),
    Regra("F-11", "ALTA", "Base de conhecimento sem revisão na ingestão", "condicional",
          r"(?i)(revisao[_ ]ingestao|aprovar[_ ]regra|assinatura[_ ]regra|regra[_ ]aprovada|"
          r"signed_rule|review_before_ingest|approved_by|human_review|ingest\w*_approv)",
          "PoisonedRAG reporta até 97% de ASR contra bases; se o lado confiável é "
          "gravável sem revisão, a separação estrutural perde o chão",
          "revisão humana ou assinatura na ingestão; segregar base compartilhada",
          gatilho=r"(?i)(vector|embedding|retriev|\brag\b|rag_engine|chroma|pinecone|faiss|qdrant|"
                  r"weaviate|milvus|ingest|indexar|knowledge[_ ]base|base_de_conhecimento)"),
    Regra("F-12", "MÉDIA", "Sem redação em tempo de recuperação", "ausente",
          r"(?i)\b(redigir|redact|placeholder|mascarar|mask|de[_ ]?identif|anonymi[sz]|"
          r"pseudonymi[sz])\w*\s*\(",
          "valores sensíveis entram no prompt em claro; é a mitigação com melhor número "
          "medido (divulgação indevida a 0,0%)",
          "placeholder antes de montar o prompt; restaurar depois se a política permitir"),
    Regra("F-13", "MÉDIA", "Model Armor sem fatiamento ou sem tipo de documento", "condicional",
          r"(?i)(janela|chunk|fatia|overlap|sobrepos|window|byteDataType|byte_data_type|"
          r"SKIP_DETECTION|MATCH_FOUND)",
          "o filtro de prompt injection aceita 65.536 tokens (quotas: 10.000); acima disso "
          "devolve SKIP_DETECTION se não achou nada; documento só entra pela API com "
          "byteDataType explícito",
          "texto acima do limite em janelas sobrepostas; documento com byteDataType; "
          "SKIP_DETECTION e indisponibilidade são 'não classificado', não 'limpo'",
          gatilho=r"(?i)model[_ ]?armor|modelArmorConfig"),
    Regra("F-14", "MÉDIA", "Hierarquia declarada só como proibição", "ausente",
          r"(?i)(instru\w+ v[eê]m exclusivamente|vem exclusivamente desta|instruction hierarchy|"
          r"fonte leg[ií]tima de instru|instructions come (exclusively|only) from|"
          r"only from this system (message|prompt)|sole source of instructions)",
          "proibir uma frase endereça a frase; afirmar a fonte endereça a classe, "
          "inclusive DACSI, que não usa imperativo",
          "declarar a fonte legítima + cláusula sobre texto que AFIRME ser nota oficial, "
          "política ou metadado"),
    Regra("F-16", "MÉDIA", "Floor setting em ambiente sem acesso ao projeto", "presente",
          r"(?i)floor[_ ]?setting",
          "floor setting é configuração de projeto; se só arquivos versionados são "
          "editáveis, é recomendação inaplicável que simula tratamento",
          "usar template por request via modelArmorConfig — confirme a superfície editável"),
    Regra("F-17", "BAIXA", "Spotlighting agressivo sobre texto extraído", "presente",
          r"(?i)(rot13|datamarking|b64encode\s*\(.{0,40}(peca|documento|texto_extraido|document|text))",
          "datamarking e encoding degradam texto de OCR, que é o que a avaliação precisa "
          "ler; custo em falso negativo pode superar o ganho",
          "delimiting + reforço; datamarking só em texto limpo, encoding não"),
]

RX_F22_TITULO = "temperature/topP/topK enviados a modelo que os ignora"
RX_F23 = re.compile(r"(?i)media_?[rR]esolution[\"']?\s*[:=]\s*[\"']?(low|MEDIA_RESOLUTION_LOW)\b")
RX_NAO_CONFIAVEL = re.compile(r"(?i)nao_confiavel|untrusted|texto_extraido|extracted_text|retrieved")
RX_SYSTEM_CANAL = re.compile(r"system_instruction\s*=|systemInstruction\s*[:=]")
RX_REGRAS_CONF = re.compile(
    r"(?i)(regras?\s+aplic|rules?\s+appl|pol[ií]ticas?\s+aplic"
    r"|\{\s*regras?\w*\s*\}|\{\s*rules?\w*\s*\}|\bSYSTEM_?(PROMPT|INSTRUCTION)\b)")
RX_CONTEUDO = re.compile(RX_TAG)


def arquivos(alvo: Path):
    if alvo.is_file():
        yield alvo
        return
    for caminho in alvo.rglob("*"):
        if caminho.is_file() and caminho.suffix in EXTENSOES and not IGNORAR & set(caminho.parts):
            yield caminho


def _checar_ordem(caminho: Path, texto: str) -> list[str]:
    """F-05: bloco não confiável antes do bloco de regras, DENTRO do prompt montado.

    Se o arquivo passa o system prompt pelo canal próprio (`system_instruction=`), a ordem
    dentro de `contents` não o afeta e a heurística não se aplica. Compara offsets no
    arquivo inteiro, não número de linha: prompts costumam ser f-strings multilinha.
    """
    if RX_SYSTEM_CANAL.search(texto):
        return []
    tag = RX_CONTEUDO.search(texto)
    regras = RX_REGRAS_CONF.search(texto)
    if not (tag and regras) or tag.start() >= regras.start():
        return []
    linha_tag = texto.count("\n", 0, tag.start()) + 1
    linha_regras = texto.count("\n", 0, regras.start()) + 1
    return [f"{caminho}:{linha_tag} (bloco de regras só em :{linha_regras})"]


def _indexar(alvo: Path) -> dict:
    rx = {r.codigo: re.compile(r.padrao) for r in REGRAS}
    rx_gat = {r.codigo: re.compile(r.gatilho) for r in REGRAS if r.gatilho}
    oc: dict[str, list[str]] = {r.codigo: [] for r in REGRAS}
    gat: dict[str, list[str]] = {c: [] for c in rx_gat}
    extra = {"gemini": [], "amostragem": [], "modelo_ignora": [], "f23": [], "f23_contexto": [],
             "ordem": []}

    for caminho in arquivos(alvo):
        try:
            linhas = caminho.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        texto = "\n".join(linhas)
        tem_nao_confiavel = bool(RX_NAO_CONFIAVEL.search(texto))
        for n, linha in enumerate(linhas, 1):
            ref = f"{caminho}:{n}"
            if RX_GEMINI.search(linha):
                extra["gemini"].append(ref)
            if RX_AMOSTRAGEM.search(linha):
                extra["amostragem"].append(ref)
            if RX_MODELO_IGNORA.search(linha):
                extra["modelo_ignora"].append(ref)
            if RX_F23.search(linha):
                (extra["f23"] if tem_nao_confiavel else extra["f23_contexto"]).append(ref)
            for codigo, r in rx.items():
                if r.search(linha):
                    oc[codigo].append(ref)
            for codigo, g in rx_gat.items():
                if g.search(linha):
                    gat[codigo].append(ref)
        extra["ordem"].extend(_checar_ordem(caminho, texto))

    return {"oc": oc, "gat": gat, **extra}


def _item(regra: Regra, onde: list[str]) -> dict:
    return {"codigo": regra.codigo, "severidade": regra.severidade, "titulo": regra.titulo,
            "onde": onde, "risco": regra.risco, "correcao": regra.correcao}


def auditar(alvo: Path) -> dict:
    """Devolve {"gemini": bool, "achados": [...], "verificar": [...]}."""
    idx = _indexar(alvo)
    if not idx["gemini"]:
        return {"gemini": False, "achados": [], "verificar": []}

    achados: list[dict] = []
    verificar: list[dict] = []

    for regra in REGRAS:
        hits = idx["oc"][regra.codigo]
        if regra.tipo == "ausente" and not hits:
            verificar.append({**_item(regra, []), "severidade": None,
                              "motivo": "camada não reconhecida pelo script; confirme lendo o código"})
        elif regra.tipo == "presente" and hits:
            achados.append(_item(regra, hits))
        elif regra.tipo == "condicional" and idx["gat"].get(regra.codigo) and not hits:
            achados.append(_item(regra, idx["gat"][regra.codigo][:3]))

    if idx["ordem"]:
        achados.append(_item(Regra(
            "F-05", "CRÍTICA", "Conteúdo não confiável antes das instruções", "presente", "",
            "o documento é lido antes das regras que deveriam governá-lo, e o prefixo cacheável "
            "some junto",
            "reordenar: estável primeiro, não confiável por último (ou system prompt pelo "
            "canal system_instruction)"), idx["ordem"]))

    if idx["amostragem"] and idx["modelo_ignora"]:
        achados.append(_item(Regra(
            "F-22", "MÉDIA", RX_F22_TITULO, "presente", "",
            "em gemini-4-argon / 3.8-flash / 3.7-flash / 3.6-flash / 3.5-flash-lite, "
            "temperature/topP/topK são ignorados (HTTP 400 em geração futura): qualquer defesa "
            "apoiada neles existe no código e não existe em execução",
            "remover os parâmetros; determinismo por thinking_level + response_schema + system "
            "instruction (formato, critério ordenado, ambiguidade, o que não inferir)"),
            idx["amostragem"][:3] + [f"modelo em {idx['modelo_ignora'][0]}"]))

    if idx["f23"]:
        achados.append(_item(Regra(
            "F-23", "MÉDIA", "Conteúdo não confiável em media_resolution baixa", "presente", "",
            "resolução baixa esconde o payload do classificador e da revisão humana, não do "
            "modelo; não é sanitização",
            "resolução suficiente na parte avaliada; LOW só em partes de contexto"), idx["f23"]))
    if idx["f23_contexto"]:
        verificar.append({"codigo": "F-23", "severidade": None,
                          "titulo": "media_resolution baixa (sem sinal de conteúdo não confiável no arquivo)",
                          "onde": idx["f23_contexto"][:3],
                          "motivo": "LOW em parte de contexto é recomendado; confirme que a parte não "
                                    "é a que carrega conteúdo não confiável",
                          "risco": "", "correcao": ""})

    achados.sort(key=lambda a: SEVERIDADES.index(a["severidade"]))
    return {"gemini": True, "achados": achados, "verificar": verificar}


def imprimir(rel: dict, alvo: Path) -> None:
    if not rel["gemini"]:
        print(f"Nenhum sinal de Gemini/Vertex em {alvo} (google.genai, vertexai, generate_content, "
              "id gemini-*). Nada auditado.")
        return
    achados, verificar = rel["achados"], rel["verificar"]
    if achados:
        contagem = {s: sum(1 for a in achados if a["severidade"] == s) for s in SEVERIDADES}
        resumo = "  ".join(f"{s}: {n}" for s, n in contagem.items() if n)
        print(f"{len(achados)} achado(s) — {resumo}\n")
        for a in achados:
            print(f"[{a['severidade']}] {a['codigo']} · {a['titulo']}")
            for onde in a["onde"][:3]:
                print(f"  onde:     {onde}")
            if len(a["onde"]) > 3:
                print(f"            ... (+{len(a['onde']) - 3})")
            print(f"  risco:    {a['risco']}")
            print(f"  correção: {a['correcao']}\n")
        print("Ordem de correção: críticas primeiro, uma por vez, verificando cada uma "
              "(Fase 3 e 4 do SKILL.md).")
    else:
        print(f"Nenhum achado com arquivo:linha em {alvo}.")

    if verificar:
        print(f"\nVERIFICAR À MÃO ({len(verificar)}) — camadas que o script não reconheceu; não são "
              "achados até você confirmar lendo o código:")
        for v in verificar:
            onde = f" ({', '.join(v['onde'][:2])})" if v.get("onde") else ""
            print(f"  - {v['codigo']} · {v['titulo']}{onde}")
    print("\nO script reconhece a convenção desta skill (tags, nomes de função, frases em pt/en) e "
          "padrões estruturais. Catálogo completo: references/fragilidades.md (F-01 a F-24).")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("alvo", type=Path)
    p.add_argument("--json", action="store_true")
    p.add_argument("--min-severidade", choices=[s.lower() for s in SEVERIDADES], default=None)
    args = p.parse_args()

    if not args.alvo.exists():
        print(f"erro: {args.alvo} não existe", file=sys.stderr)
        return 2

    rel = auditar(args.alvo)
    if args.min_severidade:
        teto = SEVERIDADES.index(args.min_severidade.upper())
        rel["achados"] = [a for a in rel["achados"] if SEVERIDADES.index(a["severidade"]) <= teto]

    if args.json:
        print(json.dumps(rel, ensure_ascii=False, indent=2))
    else:
        imprimir(rel, args.alvo)
    return 1 if rel["achados"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

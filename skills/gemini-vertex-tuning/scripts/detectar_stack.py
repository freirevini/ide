#!/usr/bin/env python3
"""Primeiro passe do Passo 0: mapeia a stack Gemini/Vertex de um repositório.

Heurístico por regex. O resultado é uma lista de candidatos com arquivo:linha
para o agente CONFIRMAR lendo os arquivos — nunca uma conclusão.

Uso:
    python detectar_stack.py <raiz_do_repo> [--json]

Saída não-zero quando algum item obrigatório do Passo 0 (1-5) ficar sem
evidência ou ficar ambíguo. Nesse caso, PARE e reporte o que faltou.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

CODIGO = {".py"}
TEXTO = {".md", ".txt", ".j2", ".jinja", ".jinja2", ".yaml", ".yml", ".toml"}
IGNORAR = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    "dist", "build", ".mypy_cache", ".pytest_cache", ".tox",
}

# categoria -> [(rotulo, regex)]
PADROES: dict[str, list[tuple[str, str]]] = {
    "sdk": [
        ("google-genai (novo)", r"from\s+google\s+import\s+genai|genai\.Client\s*\("),
        ("vertexai (legado)", r"import\s+vertexai|vertexai\.init\s*\(|GenerativeModel\s*\("),
        ("langchain", r"langchain_google_vertexai|ChatVertexAI"),
    ],
    "modelo": [
        ("model id literal", r"[\"']gemini-[0-9][A-Za-z0-9.\-_]*[\"']"),
        ("model id via config", r"(?i)\b(model|model_name|model_id)\s*[:=]\s*(os\.|settings|config|MODEL)"),
    ],
    "config": [
        ("env var", r"os\.environ|os\.getenv"),
        ("settings", r"BaseSettings|pydantic_settings|from\s+.*settings\s+import"),
    ],
    "prompt": [
        ("system instruction", r"system_instruction|systemInstruction|SYSTEM_PROMPT|system_prompt"),
        ("template de prompt", r"PromptTemplate|ChatPromptTemplate|\.j2[\"']|render\s*\(\s*\*\*"),
    ],
    "vetor:RagManagedDb": [
        ("RagManagedDb", r"RagManagedDb|RagCorpus|RagFile|rag_managed_db|from\s+vertexai\s+import\s+rag|vertexai\.preview\.rag"),
    ],
    "vetor:VectorSearch": [
        ("Vector Search", r"MatchingEngineIndex|IndexEndpoint|MatchingEngine|leafNodeEmbeddingCount|leaf_node_embedding_count"),
    ],
    "vetor:VertexAISearch": [
        ("Vertex AI Search", r"discoveryengine|SearchServiceClient"),
    ],
    "vetor:Outro": [
        ("banco vetorial externo", r"(?i)\b(qdrant|pgvector|chromadb|weaviate|pinecone|faiss|milvus|elasticsearch)\b"),
    ],
    "orquestracao": [
        ("async", r"^\s*async\s+def|asyncio\.gather|asyncio\.to_thread"),
        ("client async do SDK", r"\.aio\.|AsyncClient"),
        ("chamada ao modelo", r"generate_content|generateContent|\.invoke\s*\(|\.predict\s*\("),
        ("limite de concorrência", r"Semaphore|ThreadPoolExecutor"),
    ],
    "saida_estruturada": [
        ("schema", r"response_schema|responseSchema|response_mime_type|responseMimeType"),
        ("limite de saída", r"max_output_tokens|maxOutputTokens"),
        ("checagem de finish_reason", r"finish_reason|finishReason"),
    ],
    "thinking": [
        ("thinking 2.5", r"thinking_budget|thinkingBudget|ThinkingConfig"),
        ("thinking 3.x", r"thinking_level|thinkingLevel"),
        ("thoughts", r"include_thoughts|thoughts_token_count"),
    ],
    "caching": [
        ("context caching", r"CachedContent|cached_content|cachedContent|create_cached_content"),
        ("métrica de cache", r"cached_content_token_count|cachedContentTokenCount"),
    ],
    "ambiente": [
        ("location", r"[\"']us-central1[\"']|location\s*=|LOCATION"),
        ("project", r"project\s*=|PROJECT_ID|GOOGLE_CLOUD_PROJECT"),
    ],
}

# item do Passo 0 -> (descricao, categorias que servem de evidência)
ITENS_PASSO_0 = [
    ("1. cliente Vertex/GenAI", ["sdk"]),
    ("2. model id", ["modelo"]),
    ("3. prompts / system instructions", ["prompt"]),
    ("4. backend de vetor", ["vetor:"]),
    ("5. orquestração dos agentes", ["orquestracao"]),
    ("6. saída estruturada", ["saida_estruturada"]),
]


def arquivos(raiz: Path):
    for caminho in raiz.rglob("*"):
        if not caminho.is_file() or caminho.suffix not in CODIGO | TEXTO:
            continue
        if IGNORAR & set(caminho.parts):
            continue
        yield caminho


def varrer(raiz: Path) -> dict[str, list[dict]]:
    compilados = [
        (cat, rot, re.compile(pad, re.MULTILINE))
        for cat, pares in PADROES.items()
        for rot, pad in pares
    ]
    achados: dict[str, list[dict]] = defaultdict(list)
    for caminho in arquivos(raiz):
        try:
            linhas = caminho.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for n, linha in enumerate(linhas, 1):
            if len(linha) > 500:
                continue
            for cat, rot, rx in compilados:
                if rx.search(linha):
                    achados[cat].append({
                        "rotulo": rot,
                        "arquivo": str(caminho.relative_to(raiz)),
                        "linha": n,
                        "trecho": linha.strip()[:160],
                    })
    return achados


def backends_de_vetor(achados: dict[str, list[dict]]) -> list[str]:
    return sorted(c.split(":", 1)[1] for c in achados if c.startswith("vetor:"))


def pendencias(achados: dict[str, list[dict]]) -> list[str]:
    faltando = []
    for descricao, prefixos in ITENS_PASSO_0:
        tem = any(
            cat.startswith(p) if p.endswith(":") else cat == p
            for cat in achados
            for p in prefixos
        )
        if not tem:
            faltando.append(f"{descricao}: sem evidência no repositório")
    backends = backends_de_vetor(achados)
    if len(backends) > 1:
        faltando.append(
            "4. backend de vetor: AMBÍGUO — encontrados " + ", ".join(backends)
            + " (parâmetros de tuning são incompatíveis entre eles)"
        )
    return faltando


def imprimir(achados: dict[str, list[dict]], faltando: list[str], limite: int = 8) -> None:
    for categoria in sorted(achados):
        hits = achados[categoria]
        print(f"\n## {categoria}  ({len(hits)} ocorrência(s))")
        vistos = set()
        mostrados = 0
        for h in hits:
            chave = (h["rotulo"], h["arquivo"])
            if chave in vistos:
                continue
            vistos.add(chave)
            print(f"  {h['arquivo']}:{h['linha']}  [{h['rotulo']}]  {h['trecho']}")
            mostrados += 1
            if mostrados >= limite:
                print(f"  ... (+{len(hits) - mostrados} ocorrência(s))")
                break

    backends = backends_de_vetor(achados)
    print("\n## Backend de vetor")
    print("  " + (", ".join(backends) if backends else "NÃO IDENTIFICADO"))

    print("\n## Passo 0")
    if faltando:
        print("  INCOMPLETO — pare e reporte:")
        for item in faltando:
            print(f"    - {item}")
    else:
        print("  Todos os itens têm evidência. CONFIRME lendo os arquivos antes de agir.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raiz", type=Path)
    parser.add_argument("--json", action="store_true", help="saída em JSON")
    args = parser.parse_args()

    if not args.raiz.is_dir():
        print(f"erro: {args.raiz} não é um diretório", file=sys.stderr)
        return 2

    achados = varrer(args.raiz)
    faltando = pendencias(achados)

    if args.json:
        print(json.dumps({
            "achados": achados,
            "backends_de_vetor": backends_de_vetor(achados),
            "pendencias_passo_0": faltando,
        }, ensure_ascii=False, indent=2))
    else:
        imprimir(achados, faltando)

    # itens 1-5 são bloqueantes; o 6 é diagnóstico
    return 1 if [f for f in faltando if not f.startswith("6.")] else 0


if __name__ == "__main__":
    raise SystemExit(main())

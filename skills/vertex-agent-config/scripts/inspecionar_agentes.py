#!/usr/bin/env python3
"""Passo 0 — varre o projeto e imprime o que já está configurado.

Reporta model ids, locations, tipos de arquivo tratados e presença de responseSchema,
thinking e cache de contexto, com arquivo:linha. Heurístico: confirme lendo o código.

Uso:
    python inspecionar_agentes.py <raiz_do_projeto> [--json]

Sai não-zero quando algum item do Passo 0 fica sem evidência — nesse caso, PERGUNTE ao
usuário em vez de assumir. Só stdlib.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

IGNORAR = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build",
           ".mypy_cache", ".pytest_cache", ".tox"}
EXTENSOES = {".py", ".ts", ".js", ".java", ".kt", ".go", ".yaml", ".yml", ".toml", ".env"}

PADROES: dict[str, list[tuple[str, str]]] = {
    "model_id": [
        ("literal", r"[\"']gemini-[0-9][A-Za-z0-9.\-_]*[\"']"),
        ("via config", r"(?i)\b(model|model_name|model_id)\s*[:=]\s*(os\.|settings|config|MODEL)"),
    ],
    "location": [
        ("location", r"[\"'](us|europe|asia|southamerica)-[a-z]+[0-9][\"']|location\s*="),
        ("project", r"PROJECT_ID|GOOGLE_CLOUD_PROJECT|project\s*="),
    ],
    "thinking": [
        ("thinking_budget (2.5)", r"thinking_budget|thinkingBudget"),
        ("thinking_level (3.x)", r"thinking_level|thinkingLevel"),
        ("ThinkingConfig", r"ThinkingConfig"),
    ],
    "schema": [
        ("response_schema", r"response_schema|responseSchema"),
        ("mime json", r"response_mime_type|responseMimeType"),
    ],
    "cache": [
        ("context caching", r"CachedContent|cached_content|cachedContent|create_cached_content"),
        ("métrica de cache", r"cached_content_token_count|cachedContentTokenCount"),
    ],
    "amostragem": [
        ("temperature", r"\btemperature\s*[:=]"),
        ("top_p / top_k", r"\btop_?[pk]\s*[:=]"),
        ("seed", r"\bseed\s*[:=]"),
    ],
    "orquestracao": [
        ("async", r"^\s*async\s+def|asyncio\.gather"),
        ("chamada ao modelo", r"generate_content|generateContent"),
        ("agentes nomeados", r"(?i)\b(agente|agent)[_ ]?[0-9a-z]{1,12}\s*[:=(]"),
    ],
}

# extensão citada no código -> como a Vertex trata
ARQUIVOS = {
    ".pdf":  "aceito (application/pdf) — confirme se tem texto ou é escaneado",
    ".txt":  "aceito (text/plain)",
    ".csv":  "entra como text/plain",
    ".docx": "NÃO é tipo de entrada — precisa converter para PDF",
    ".doc":  "NÃO é tipo de entrada — precisa converter para PDF",
    ".pptx": "NÃO é tipo de entrada — precisa converter para PDF",
    ".ppt":  "NÃO é tipo de entrada — precisa converter para PDF",
    ".xlsx": "NÃO é tipo de entrada — precisa converter para PDF",
    ".xls":  "NÃO é tipo de entrada — precisa converter para PDF",
    ".jpeg": "imagem — resolução alta se a regra depender de letra miúda",
    ".jpg":  "imagem — resolução alta se a regra depender de letra miúda",
    ".png":  "imagem — resolução alta se a regra depender de letra miúda",
}
RX_CONVERSAO = re.compile(
    r"(?i)\b(libreoffice|unoconv|soffice|docx2pdf|pandoc|to_pdf|para_pdf|convert(er)?_to_pdf"
    r"|pdfplumber|pypdf|fitz|pymupdf|tesseract|ocr)\w*")

# item do Passo 0 -> categorias que servem de evidência
PASSO_0 = [
    ("1. arquitetura de agentes", ["orquestracao"]),
    ("2. model ids configurados", ["model_id"]),
    ("3. tipos de arquivo processados", ["_arquivos"]),
    ("4a. responseSchema", ["schema"]),
    ("4b. configuração de thinking", ["thinking"]),
    ("4c. cache de contexto", ["cache"]),
]


def arquivos(raiz: Path):
    for c in raiz.rglob("*"):
        if c.is_file() and c.suffix in EXTENSOES and not IGNORAR & set(c.parts):
            yield c


def varrer(raiz: Path) -> dict:
    compilados = [(cat, rot, re.compile(p, re.MULTILINE))
                  for cat, pares in PADROES.items() for rot, p in pares]
    achados: dict[str, list[dict]] = defaultdict(list)
    tipos: dict[str, list[str]] = defaultdict(list)
    conversao: list[str] = []

    for caminho in arquivos(raiz):
        try:
            linhas = caminho.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        rel = caminho.relative_to(raiz)
        for n, linha in enumerate(linhas, 1):
            if len(linha) > 500:
                continue
            for cat, rot, rx in compilados:
                if rx.search(linha):
                    achados[cat].append({"rotulo": rot, "onde": f"{rel}:{n}",
                                         "trecho": linha.strip()[:150]})
            for ext in ARQUIVOS:
                if re.search(rf"[\"']?\{ext}\b", linha, re.IGNORECASE):
                    tipos[ext].append(f"{rel}:{n}")
            if RX_CONVERSAO.search(linha):
                conversao.append(f"{rel}:{n}  {linha.strip()[:110]}")

    return {"achados": dict(achados), "tipos_de_arquivo": dict(tipos),
            "conversao_extracao": conversao}


def pendencias(rel: dict) -> list[str]:
    faltando = []
    for desc, cats in PASSO_0:
        if cats == ["_arquivos"]:
            if not rel["tipos_de_arquivo"]:
                faltando.append(f"{desc}: nenhum tipo de arquivo identificado")
            continue
        if not any(rel["achados"].get(c) for c in cats):
            faltando.append(f"{desc}: sem evidência no projeto")
    problematicos = [e for e in rel["tipos_de_arquivo"] if "NÃO é tipo" in ARQUIVOS[e]]
    if problematicos and not rel["conversao_extracao"]:
        faltando.append(
            f"3b. {', '.join(sorted(problematicos))} tratados sem sinal de conversão — "
            "pergunte onde a conversão acontece")
    return faltando


def imprimir(rel: dict, faltando: list[str]) -> None:
    for categoria in sorted(rel["achados"]):
        hits = rel["achados"][categoria]
        print(f"\n## {categoria}  ({len(hits)})")
        vistos = set()
        for h in hits:
            chave = (h["rotulo"], h["onde"].split(":")[0])
            if chave in vistos:
                continue
            vistos.add(chave)
            print(f"  {h['onde']}  [{h['rotulo']}]  {h['trecho']}")
            if len(vistos) >= 6:
                print(f"  ... (+{len(hits) - len(vistos)})")
                break

    print("\n## tipos de arquivo tratados")
    if rel["tipos_de_arquivo"]:
        for ext in sorted(rel["tipos_de_arquivo"]):
            print(f"  {ext:<7} {ARQUIVOS[ext]}")
            print(f"          {', '.join(rel['tipos_de_arquivo'][ext][:3])}")
    else:
        print("  nenhum identificado")

    print("\n## conversão / extração")
    for c in rel["conversao_extracao"][:8] or ["  nenhum sinal"]:
        print(f"  {c}" if not c.startswith("  ") else c)

    print("\n## Passo 0")
    if faltando:
        print("  INCOMPLETO — PERGUNTE ao usuário, não assuma:")
        for f in faltando:
            print(f"    - {f}")
    else:
        print("  Todos os itens têm evidência. CONFIRME lendo o código antes de sugerir.")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("raiz", type=Path)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    if not args.raiz.is_dir():
        print(f"erro: {args.raiz} não é um diretório", file=sys.stderr)
        return 2

    rel = varrer(args.raiz)
    faltando = pendencias(rel)
    if args.json:
        print(json.dumps({**rel, "pendencias_passo_0": faltando}, ensure_ascii=False, indent=2))
    else:
        imprimir(rel, faltando)
    return 1 if faltando else 0


if __name__ == "__main__":
    raise SystemExit(main())

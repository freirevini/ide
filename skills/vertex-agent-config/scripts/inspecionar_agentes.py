#!/usr/bin/env python3
"""Passo 0 — varre o projeto e imprime o que já está configurado.

Reporta model ids (literais, env vars, config), locations, tipos de arquivo tratados e
presença de responseSchema, thinking e cache de contexto, com arquivo:linha. Marca ids
depreciados/retirados e amostragem enviada a modelo que a ignora (references/modelos.md,
verificado em 2026-10-23). Heurístico: confirme lendo o código.

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
        ("literal", r"[\"']gemini-[a-z0-9][A-Za-z0-9.\-_]*[\"']"),
        ("env", r"(?m)^\s*[A-Z0-9_]+\s*=\s*[\"']?gemini-[a-z0-9][A-Za-z0-9.\-_]*"),
        ("via config", r"(?i)\b(model|model_name|model_id)\s*[:=]\s*(os\.|settings|config|MODEL)"),
    ],
    "location": [
        ("location", r"[\"'](us|europe|asia|southamerica)-[a-z]+[0-9][\"']|location\s*="),
        ("project", r"PROJECT_ID|GOOGLE_CLOUD_PROJECT|project\s*="),
    ],
    "thinking": [
        ("thinking_level (3.x)", r"thinking_level|thinkingLevel"),
        ("thinking_budget (2.5 — LEGADO)", r"thinking_budget|thinkingBudget"),
        ("ThinkingConfig", r"ThinkingConfig"),
    ],
    "multimodal": [
        ("media_resolution (3.x)", r"media_resolution|mediaResolution"),
        ("geração de imagem", r"response_modalities|responseModalities|ImageConfig|image_size"),
    ],
    "geracao_legada": [
        ("gemini-2.5 (retirado da Vertex em 2026-10-20)", r"gemini-2\.[05][A-Za-z0-9.\-_]*"),
        ("gemini-3.7-flash (depreciado; retira 2027-01-28 → gemini-3.8-flash)", r"gemini-3\.7-flash"),
        ("gemini-3.6-flash (retira 2026-11-19 → gemini-3.8-flash)", r"gemini-3\.6-flash"),
        ("gemini-3.1-pro sem -preview (id inexistente na Vertex; use gemini-3.1-pro-preview)",
         r"gemini-3\.1-pro(?![-a-z])"),
        ("gemini-3.1-flash-image (depreciado → gemini-nano-banana-2.1)", r"gemini-3\.1-flash-image"),
        ("gemini-omni-flash-preview (depreciado 2026-09-30 → gemini-omni-1.1-flash)",
         r"gemini-omni-flash-preview"),
    ],
    "amostragem_ignorada": [
        ("modelo que ignora temperature/topP/topK",
         r"gemini-(4-argon|3\.8-flash|3\.7-flash|3\.6-flash|3\.5-flash-lite)"),
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
        if not c.is_file() or IGNORAR & set(c.parts):
            continue
        # ".env" e ".env.local" têm suffix vazio ou ".local": checar pelo nome
        if c.suffix in EXTENSOES or c.name.startswith(".env"):
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
    vistos: set[str] = set()
    for h in rel["achados"].get("geracao_legada", []):
        if h["rotulo"] in vistos:
            continue
        vistos.add(h["rotulo"])
        faltando.append(f"LEGADO. {h['rotulo']} (ex.: {h['onde']}) — ver references/modelos.md")
    if any(h["rotulo"].startswith("thinking_budget") for h in rel["achados"].get("thinking", [])):
        faltando.append("LEGADO. thinking_budget é a API 2.5; na 3.x use thinking_level "
                        "(no 4 Argon devolve HTTP 400)")

    amostragem = [h for h in rel["achados"].get("amostragem", [])
                  if h["rotulo"] in ("temperature", "top_p / top_k")]
    ignorantes = rel["achados"].get("amostragem_ignorada", [])
    if amostragem and ignorantes:
        faltando.append(
            f"MIGRAÇÃO. temperature/top_p/top_k enviados ({amostragem[0]['onde']}) a modelo que os "
            f"ignora ({ignorantes[0]['onde']}): hoje sem efeito, HTTP 400 em geração futura — remova; "
            "determinismo vai para thinking_level + response_schema + system instruction")

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
        print("  PENDÊNCIAS — itens 'sem evidência': PERGUNTE ao usuário, não assuma."
              "\n              itens 'LEGADO' e 'MIGRAÇÃO': id ou parâmetro a migrar "
              "(references/modelos.md).")
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

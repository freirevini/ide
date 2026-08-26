#!/usr/bin/env python3
"""Instrumentação e agregação de latência/custo por estágio do pipeline.

Duas metades:

1. Biblioteca — `stage_timer` mede um estágio e grava um evento JSONL.
   Anexe as métricas da resposta com `registrar_uso`:

       from medir_latencia import stage_timer, registrar_uso

       with stage_timer("agente_2", modelo=JUDGE) as ev:
           resp = client.models.generate_content(...)
           registrar_uso(ev, resp)

   O `finish_reason` entra no evento — é assim que `MAX_TOKENS` silencioso
   aparece na medição em vez de virar "erro de parsing" no log.

2. CLI — agrega os eventos:

       python medir_latencia.py agregar eventos.jsonl

Só stdlib. Sem baseline medido, nenhuma otimização deste skill deve começar.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import statistics
import time
from collections import defaultdict
from pathlib import Path

DESTINO_PADRAO = Path(os.getenv("TUNING_EVENTOS", "tuning_eventos.jsonl"))

# modelo -> (USD por 1M de entrada, USD por 1M de saída) — geração 3.x
PRECOS = {
    "gemini-3.1-pro": (2.00, 12.00),
    "gemini-3.7-flash": (0.75, 3.75),   # promocional até 2026-12-31; depois (1.50, 7.50)
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gemini-3-pro-image": (3.00, 15.00),
}
# acima deste contexto o gemini-3.1-pro passa a (4.00, 18.00)
LIMIAR_CONTEXTO_LONGO = 200_000
PRECO_LONGO = {"gemini-3.1-pro": (4.00, 18.00)}
# leitura de cache do gemini-3.1-pro: $0,50/1M sobre $2,00 = 25% do preço cheio
FATOR_CACHE = 0.25

CAMPOS_DE_USO = (
    "prompt_token_count",
    "candidates_token_count",
    "thoughts_token_count",
    "cached_content_token_count",
    "total_token_count",
)


@contextlib.contextmanager
def stage_timer(stage: str, destino: Path | None = None, **extra):
    """Mede um estágio e emite um evento JSONL. Cede o dict do evento."""
    evento = {"stage": stage, **extra}
    inicio = time.perf_counter()
    try:
        yield evento
    except Exception as erro:
        evento["erro"] = type(erro).__name__
        raise
    finally:
        evento["duration_ms"] = round((time.perf_counter() - inicio) * 1000, 2)
        evento.setdefault("ts", time.time())
        caminho = destino or DESTINO_PADRAO
        with caminho.open("a", encoding="utf-8") as f:
            f.write(json.dumps(evento, ensure_ascii=False) + "\n")


def registrar_uso(evento: dict, resposta) -> dict:
    """Copia usage_metadata e finish_reason da resposta para o evento."""
    uso = getattr(resposta, "usage_metadata", None)
    for campo in CAMPOS_DE_USO:
        valor = getattr(uso, campo, None)
        if valor is not None:
            evento[campo] = valor
    candidatos = getattr(resposta, "candidates", None) or []
    if candidatos:
        motivo = getattr(candidatos[0], "finish_reason", None)
        if motivo is not None:
            evento["finish_reason"] = getattr(motivo, "name", str(motivo))
    return evento


def custo_usd(evento: dict) -> float | None:
    modelo = str(evento.get("modelo") or evento.get("model") or "")
    preco = next((p for nome, p in PRECOS.items() if modelo.startswith(nome)), None)
    if preco is None:
        return None
    entrada, saida = preco
    tokens_in = evento.get("prompt_token_count", 0)
    tokens_out = evento.get("candidates_token_count", 0) + evento.get("thoughts_token_count", 0)
    if tokens_in > LIMIAR_CONTEXTO_LONGO:
        for nome, (e_longo, s_longo) in PRECO_LONGO.items():
            if modelo.startswith(nome):
                entrada, saida = e_longo, s_longo
                break
    cacheados = evento.get("cached_content_token_count", 0)
    faturaveis_in = (tokens_in - cacheados) + cacheados * FATOR_CACHE
    return (faturaveis_in * entrada + tokens_out * saida) / 1_000_000


def percentil(valores: list[float], p: float) -> float:
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    if len(ordenados) == 1:
        return ordenados[0]
    pos = min(int(round(p / 100 * (len(ordenados) - 1))), len(ordenados) - 1)
    return ordenados[pos]


def carregar(caminho: Path) -> list[dict]:
    eventos = []
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha:
            eventos.append(json.loads(linha))
    return eventos


def resumir(eventos: list[dict]) -> dict[str, dict]:
    por_estagio: dict[str, list[dict]] = defaultdict(list)
    for ev in eventos:
        por_estagio[ev.get("stage", "?")].append(ev)

    resumo = {}
    for estagio, evs in por_estagio.items():
        duracoes = [e["duration_ms"] for e in evs if "duration_ms" in e]
        custos = [c for c in (custo_usd(e) for e in evs) if c is not None]
        tokens_in = sum(e.get("prompt_token_count", 0) for e in evs)
        cacheados = sum(e.get("cached_content_token_count", 0) for e in evs)
        resumo[estagio] = {
            "n": len(evs),
            "p50_ms": round(percentil(duracoes, 50), 1),
            "p95_ms": round(percentil(duracoes, 95), 1),
            "p99_ms": round(percentil(duracoes, 99), 1),
            "media_ms": round(statistics.fmean(duracoes), 1) if duracoes else 0.0,
            "thinking_tokens": sum(e.get("thoughts_token_count", 0) for e in evs),
            "acerto_cache": round(cacheados / tokens_in, 3) if tokens_in else None,
            "custo_usd": round(sum(custos), 6) if custos else None,
            "max_tokens": sum(1 for e in evs if e.get("finish_reason") == "MAX_TOKENS"),
            "erros": sum(1 for e in evs if "erro" in e),
        }
    return resumo


def imprimir(resumo: dict[str, dict]) -> None:
    if not resumo:
        print("nenhum evento.")
        return
    total_p95 = sum(v["p95_ms"] for v in resumo.values()) or 1.0
    cabecalho = f"{'estágio':<20} {'n':>5} {'p50':>9} {'p95':>9} {'%p95':>6} {'think':>8} {'cache':>7} {'US$':>10}"
    print(cabecalho)
    print("-" * len(cabecalho))
    for estagio, v in sorted(resumo.items(), key=lambda kv: -kv[1]["p95_ms"]):
        cache = "-" if v["acerto_cache"] is None else f"{v['acerto_cache']:.0%}"
        custo = "-" if v["custo_usd"] is None else f"{v['custo_usd']:.5f}"
        print(
            f"{estagio:<20} {v['n']:>5} {v['p50_ms']:>9.1f} {v['p95_ms']:>9.1f} "
            f"{v['p95_ms'] / total_p95:>5.0%} {v['thinking_tokens']:>8} {cache:>7} {custo:>10}"
        )

    alertas = []
    for estagio, v in resumo.items():
        if v["max_tokens"]:
            alertas.append(f"{estagio}: {v['max_tokens']} resposta(s) com finish_reason=MAX_TOKENS "
                           "(thinking estourou maxOutputTokens — ver references/modelos.md)")
        if v["erros"]:
            alertas.append(f"{estagio}: {v['erros']} erro(s)")
        if v["acerto_cache"] == 0.0:
            alertas.append(f"{estagio}: acerto de cache 0% — prefixo instável? ver references/caching.md")
    if alertas:
        print("\nALERTAS")
        for a in alertas:
            print(f"  - {a}")

    dominante = max(resumo.items(), key=lambda kv: kv[1]["p95_ms"])
    print(f"\nOtimize primeiro: {dominante[0]} ({dominante[1]['p95_ms'] / total_p95:.0%} do p95 total).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="comando", required=True)
    ag = sub.add_parser("agregar", help="agrega um arquivo de eventos JSONL")
    ag.add_argument("eventos", type=Path)
    ag.add_argument("--json", action="store_true")
    args = parser.parse_args()

    resumo = resumir(carregar(args.eventos))
    if args.json:
        print(json.dumps(resumo, ensure_ascii=False, indent=2))
    else:
        imprimir(resumo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

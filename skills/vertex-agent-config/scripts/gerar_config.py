#!/usr/bin/env python3
"""Gera o GenerateContentConfig recomendado para um perfil de objetivo e um modelo.

Marca explicitamente quais parâmetros o modelo escolhido IGNORA, e ajusta o thinking
à faixa real do modelo. Prioriza qualidade da avaliação; custo aparece como nota.

Uso:
    python gerar_config.py --perfil avaliacao-regras --modelo gemini-2.5-pro
    python gerar_config.py --perfil extracao --modelo gemini-3.7-flash
    python gerar_config.py --listar

Só stdlib.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field

# --------------------------------------------------------------------- modelos

@dataclass(frozen=True)
class Modelo:
    familia: str                      # "2.5" | "3.x"
    thinking_min: int | None = None   # só 2.5
    thinking_max: int | None = None   # só 2.5
    desliga_thinking: bool = False    # só 2.5
    ignora_amostragem: bool = False   # temperature/topP/topK depreciados e ignorados
    aceita_minimal: bool = True       # só 3.x
    nota: str = ""


MODELOS: dict[str, Modelo] = {
    "gemini-2.5-pro": Modelo("2.5", 128, 32768, desliga_thinking=False,
                             nota="não desliga thinking (faixa 128–32768)"),
    "gemini-2.5-flash": Modelo("2.5", 0, 24576, desliga_thinking=True),
    "gemini-2.5-flash-lite": Modelo("2.5", 512, 24576,
                                    nota="não pensa por padrão (faixa 512–24576)"),
    "gemini-3.5-flash-lite": Modelo("3.x", ignora_amostragem=True),
    "gemini-3.6-flash": Modelo("3.x", ignora_amostragem=True),
    "gemini-3.7-flash": Modelo("3.x", ignora_amostragem=True,
                               nota="flash mais recente da linha 3.x"),
}

APOSENTAM_2_5 = "aposentadoria anunciada para não antes de 2026-10-16 (lifecycle mostra 2026-10-20)"


def resolver_modelo(model_id: str) -> tuple[Modelo, list[str]]:
    """Devolve (modelo, avisos). Modelo desconhecido é inferido e marcado como tal."""
    if model_id in MODELOS:
        return MODELOS[model_id], []
    if model_id.startswith("gemini-3"):
        pro = "pro" in model_id
        return (
            Modelo("3.x", ignora_amostragem=not pro, aceita_minimal=not pro,
                   nota="id não consta na lista documentada desta skill"),
            [f"{model_id!r} não está na lista documentada; comportamento INFERIDO pela "
             "linha 3.x. Confirme na documentação da Vertex antes de fixar."],
        )
    if model_id.startswith("gemini-2.5"):
        return (Modelo("2.5", 128, 32768, nota="id não consta na lista documentada"),
                [f"{model_id!r} não está na lista documentada; faixas INFERIDAS da 2.5."])
    return (Modelo("3.x", nota="família não reconhecida"),
            [f"{model_id!r} não reconhecido. Confirme família, faixas e depreciações."])


# --------------------------------------------------------------------- perfis

@dataclass(frozen=True)
class Perfil:
    descricao: str
    budget_2_5: int
    level_3x: str
    max_output: int
    seed: bool
    schema: bool
    escalonamento: str
    notas: list[str] = field(default_factory=list)


PERFIS: dict[str, Perfil] = {
    "triagem": Perfil(
        "rotear/decidir o próximo passo; erro recuperável a jusante",
        budget_2_5=0, level_3x="LOW", max_output=2048, seed=False, schema=True,
        escalonamento="rota 'indeterminado' quando a confiança não separar duas rotas",
        notas=["thinking baixo é adequado: a decisão é de roteamento, não de mérito"]),
    "classificacao": Perfil(
        "atribuir rótulo de um conjunto fechado",
        budget_2_5=4096, level_3x="LOW", max_output=4096, seed=False, schema=True,
        escalonamento="rótulo 'indeterminado' em vez de forçar a classe mais próxima",
        notas=["se as classes forem ambíguas entre si, suba para HIGH antes de trocar de modelo"]),
    "extracao": Perfil(
        "tirar campos estruturados de um documento",
        budget_2_5=8192, level_3x="HIGH", max_output=16384, seed=True, schema=True,
        escalonamento="campo nulo + motivo, nunca valor inventado para preencher",
        notas=["schema deve exigir o trecho de origem de cada campo, não só o valor",
               "seed liga a reprodutibilidade: mesmo insumo, mesmo resultado"]),
    "avaliacao-regras": Perfil(
        "julgar conteúdo contra regras multicamada, com justificativa",
        budget_2_5=16384, level_3x="HIGH", max_output=32768, seed=True, schema=True,
        escalonamento="'revisão humana' quando a regra depender de julgamento de grau",
        notas=["schema deve exigir regra_id + trecho citado por achado",
               "se alguma regra for posicional/visual, envie a mídia original além do texto"]),
    "alto-risco": Perfil(
        "decisão com consequência difícil de reverter",
        budget_2_5=32768, level_3x="HIGH", max_output=65536, seed=True, schema=True,
        escalonamento="humano no circuito por padrão; automático só na decisão conservadora",
        notas=["thinking no teto da faixa: aqui latência é o recurso barato",
               "registre entrada, seed e model id para poder reproduzir o caso depois"]),
    "documento-longo": Perfil(
        "contexto grande domina a tarefa",
        budget_2_5=16384, level_3x="HIGH", max_output=32768, seed=False, schema=True,
        escalonamento="marcar 'contexto insuficiente' em vez de responder por uma fatia",
        notas=["258 tokens por página de PDF: 300 páginas ≈ 77k tokens só de documento",
               "antes de fatiar, verifique se cada regra é respondível por fatia"]),
    "criativo": Perfil(
        "geração aberta, sem resposta única correta",
        budget_2_5=8192, level_3x="HIGH", max_output=16384, seed=False, schema=False,
        escalonamento="não se aplica",
        notas=["mantenha temperature no default 1.0; é o ponto de calibração do modelo"]),
}


# ------------------------------------------------------------------- montagem

def _ajustar_budget(perfil: Perfil, m: Modelo) -> tuple[int, list[str]]:
    lo, hi = m.thinking_min or 0, m.thinking_max or 0
    pedido = perfil.budget_2_5
    if pedido < lo:
        return lo, [f"thinking_budget {pedido} abaixo do mínimo do modelo; ajustado para {lo}"
                    + ("" if m.desliga_thinking else " (este modelo não desliga thinking)")]
    if pedido > hi:
        return hi, [f"thinking_budget {pedido} acima do máximo do modelo; ajustado para {hi}"]
    return pedido, []


def montar(perfil_nome: str, model_id: str) -> tuple[list[str], list[str], list[str]]:
    """Devolve (linhas do config, notas, avisos)."""
    perfil = PERFIS[perfil_nome]
    m, avisos = resolver_modelo(model_id)
    notas = list(perfil.notas)
    linhas: list[str] = []

    if m.familia == "2.5":
        budget, ajustes = _ajustar_budget(perfil, m)
        avisos += ajustes
        linhas.append(f'    thinking_config=types.ThinkingConfig(thinking_budget={budget}),')
        linhas.append('    temperature=1.0,   # ponto inicial recomendado; ajuste só com evidência')
        linhas.append('    top_p=0.95,        # ajuste DEPOIS da temperature, e para baixo')
        notas.append(f"{model_id}: {APOSENTAM_2_5} — mantenha o model id parametrizado")
    else:
        nivel = perfil.level_3x
        if nivel == "MINIMAL" and not m.aceita_minimal:
            nivel = "LOW"
            avisos.append("MINIMAL indisponível neste modelo (Pro 3.x não aceita); usando LOW")
        linhas.append(f'    thinking_level="{nivel}",')
        if m.ignora_amostragem:
            linhas.append('    # temperature / top_p / top_k: DEPRECIADOS E IGNORADOS neste modelo.')
            linhas.append('    # Determinismo se obtém por system_instruction, não por parâmetro.')
            notas.append("temperature, topP e topK são ignorados aqui — não os envie esperando efeito")
        else:
            linhas.append('    temperature=1.0,   # linha 3.x: mantenha 1.0; baixar causa loops')
            linhas.append('    top_p=0.95,')

    linhas.append(f'    max_output_tokens={perfil.max_output},'
                  '  # thinking + resposta; ver armadilha MAX_TOKENS')
    if perfil.seed:
        linhas.append('    seed=42,           # reprodutibilidade para avaliação auditável')
    if perfil.schema:
        linhas.append('    response_mime_type="application/json",')
        linhas.append('    response_schema=SCHEMA,  # exija evidência, não só o resultado')
    linhas.append('    system_instruction=SYSTEM_INSTRUCTION,')

    if m.nota:
        notas.append(f"{model_id}: {m.nota}")
    notas.append(f"escalonamento: {perfil.escalonamento}")
    return linhas, notas, avisos


def imprimir(perfil_nome: str, model_id: str) -> None:
    perfil = PERFIS[perfil_nome]
    linhas, notas, avisos = montar(perfil_nome, model_id)

    print(f"# perfil: {perfil_nome} — {perfil.descricao}")
    print(f"# modelo: {model_id}\n")
    print("config = types.GenerateContentConfig(")
    for l in linhas:
        print(l)
    print(")\n")

    print("NOTAS")
    for n in notas:
        print(f"  - {n}")
    if avisos:
        print("\nAVISOS")
        for a in avisos:
            print(f"  ! {a}")
    print("\nNunca envie thinking_budget e thinking_level na mesma request (erro 400).")
    print("Se preferir outro modelo, rode de novo com --modelo <outro> — a escolha é sua.")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--perfil", choices=sorted(PERFIS))
    p.add_argument("--modelo")
    p.add_argument("--listar", action="store_true", help="lista perfis e modelos conhecidos")
    args = p.parse_args()

    if args.listar:
        print("PERFIS")
        for nome, perfil in PERFIS.items():
            print(f"  {nome:<18} {perfil.descricao}")
        print("\nMODELOS DOCUMENTADOS")
        for nome, m in MODELOS.items():
            faixa = (f"thinking {m.thinking_min}–{m.thinking_max}" if m.familia == "2.5"
                     else "thinking_level MINIMAL/LOW/HIGH")
            ign = "  [ignora temperature/topP/topK]" if m.ignora_amostragem else ""
            print(f"  {nome:<24} {m.familia:<4} {faixa}{ign}")
        return 0

    if not (args.perfil and args.modelo):
        p.error("--perfil e --modelo são obrigatórios (ou use --listar)")
    imprimir(args.perfil, args.modelo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

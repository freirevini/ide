#!/usr/bin/env python3
"""Gera o GenerateContentConfig recomendado para um perfil de objetivo e um modelo 3.x.

Marca quais parâmetros o modelo escolhido IGNORA e informa o preço ao lado da
recomendação — custo é informação, nunca critério. Cobre também a linha de imagem
Nano Banana.

Uso:
    python gerar_config.py --perfil avaliacao-regras --modelo gemini-3.1-pro
    python gerar_config.py --perfil classificacao --modelo gemini-3.7-flash
    python gerar_config.py --perfil imagem --modelo gemini-3-pro-image
    python gerar_config.py --listar

Só stdlib.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field

NIVEIS = ("MINIMAL", "LOW", "MEDIUM", "HIGH")


@dataclass(frozen=True)
class Modelo:
    tier: str                        # pro | flash | flash-lite | imagem
    preco: str = "consultar tabela oficial"
    ignora_amostragem: bool = False  # temperature/topP/topK depreciados e ignorados
    aceita_minimal: bool = True
    nota: str = ""


MODELOS: dict[str, Modelo] = {
    "gemini-3.1-pro": Modelo(
        "pro", "$2,00 / $12,00 por 1M · acima de 200K de contexto: $4,00 / $18,00",
        aceita_minimal=False,
        nota="contexto 1M · maxOutputTokens default 8.192 (baixo para HIGH)"),
    "gemini-3.7-flash": Modelo(
        "flash", "$0,75 / $3,75 até 2026-12-31; $1,50 / $7,50 a partir de 2027-01-01",
        ignora_amostragem=True, nota="flash mais recente da linha"),
    "gemini-3.6-flash": Modelo("flash", ignora_amostragem=True),
    "gemini-3.5-flash": Modelo("flash"),
    "gemini-3-flash": Modelo("flash"),
    "gemini-3.5-flash-lite": Modelo("flash-lite", "$0,30 / $2,50 por 1M",
                                    ignora_amostragem=True),
    "gemini-3.1-flash-lite": Modelo("flash-lite"),
    "gemini-3-pro-image": Modelo(
        "imagem", "$3,00 / $15,00 por 1M · ou $0,134/imagem 1K-2K, $0,24/imagem 4K "
                  "· batch: $0,067/imagem 2K",
        nota="Nano Banana Pro · 1120 tokens (1K e 2K), 2000 (4K) · melhor em texto na imagem"),
    "gemini-3.1-flash-image": Modelo(
        "imagem", "consultar tabela oficial",
        nota="Nano Banana 2 · generalista · 747 (512px), 1120 (1K), 1680 (2K), 2520 (4K)"),
    "gemini-3.1-flash-lite-image": Modelo("imagem", nota="somente 1K · SynthID always on"),
}


def resolver_modelo(model_id: str) -> tuple[Modelo, list[str]]:
    if model_id in MODELOS:
        return MODELOS[model_id], []
    if model_id.startswith("gemini-2.5"):
        return (Modelo("pro" if "pro" in model_id else "flash"),
                [f"{model_id!r} é da geração 2.5, que esta skill não recomenda para projeto "
                 "novo. Migre para 3.x: thinking_budget vira thinking_level e, nos flash "
                 "recentes, temperature deixa de ter efeito.",
                 "Se a migração não for possível agora, registre como pendência explícita."])
    if model_id.startswith("gemini-3"):
        pro, img = "pro" in model_id, "image" in model_id
        return (Modelo("imagem" if img else ("pro" if pro else "flash"),
                       ignora_amostragem=not pro and not img, aceita_minimal=not pro,
                       nota="id não consta na lista documentada desta skill"),
                [f"{model_id!r} não está na lista documentada; comportamento INFERIDO pela "
                 "linha 3.x. Confirme id, preço e região na documentação da Vertex."])
    return (Modelo("flash", nota="família não reconhecida"),
            [f"{model_id!r} não reconhecido. Confirme família, preço e depreciações."])


@dataclass(frozen=True)
class Perfil:
    descricao: str
    nivel: str
    max_output: int
    seed: bool
    schema: bool
    modelo_sugerido: str
    escalonamento: str
    notas: list[str] = field(default_factory=list)


PERFIS: dict[str, Perfil] = {
    "triagem": Perfil(
        "rotear/decidir o próximo passo; erro recuperável a jusante",
        "LOW", 2048, False, True, "gemini-3.5-flash-lite",
        "rota 'indeterminado' quando a confiança não separar duas rotas",
        ["thinking baixo é adequado: a decisão é de roteamento, não de mérito"]),
    "classificacao": Perfil(
        "atribuir rótulo de um conjunto fechado",
        "MEDIUM", 4096, False, True, "gemini-3.7-flash",
        "rótulo 'indeterminado' em vez de forçar a classe mais próxima",
        ["MEDIUM antes de trocar de modelo: é o degrau entre LOW que erra e HIGH que custa"]),
    "extracao": Perfil(
        "tirar campos estruturados de um documento",
        "HIGH", 16384, True, True, "gemini-3.7-flash",
        "campo nulo + motivo, nunca valor inventado para preencher",
        ["schema deve exigir o trecho de origem de cada campo, não só o valor",
         "media_resolution=high nas páginas que carregam os campos"]),
    "avaliacao-regras": Perfil(
        "julgar conteúdo contra regras multicamada, com justificativa",
        "HIGH", 32768, True, True, "gemini-3.1-pro",
        "'revisão humana' quando a regra depender de julgamento de grau",
        ["schema deve exigir regra_id + trecho citado por achado",
         "se alguma regra for posicional/visual, envie a mídia original além do texto"]),
    "alto-risco": Perfil(
        "decisão com consequência difícil de reverter",
        "HIGH", 65536, True, True, "gemini-3.1-pro",
        "humano no circuito por padrão; automático só na decisão conservadora",
        ["aqui latência é o recurso barato",
         "registre entrada, seed e model id para poder reproduzir o caso depois"]),
    "documento-longo": Perfil(
        "contexto grande domina a tarefa",
        "HIGH", 32768, False, True, "gemini-3.1-pro",
        "marcar 'contexto insuficiente' em vez de responder por uma fatia",
        ["258 tokens por página de PDF: 300 páginas ≈ 77k tokens só de documento",
         "acima de 200K de contexto o Pro dobra a entrada — verifique antes de fatiar"]),
    "criativo": Perfil(
        "geração aberta de texto, sem resposta única correta",
        "HIGH", 16384, False, False, "gemini-3.1-pro",
        "não se aplica",
        ["onde temperature funciona, mantenha 1.0: é o ponto de calibração"]),
    "imagem": Perfil(
        "gerar ou editar imagem",
        "", 0, False, False, "gemini-3.1-flash-image",
        "não se aplica",
        ["Nano Banana 2 é o generalista; Nano Banana Pro quando houver texto na imagem",
         "1K é o default; suba a 2K/4K só se a imagem for ampliada, impressa ou inspecionada",
         "SynthID é sempre aplicado e não é removível"]),
}


def montar(perfil_nome: str, model_id: str) -> tuple[list[str], list[str], list[str]]:
    perfil = PERFIS[perfil_nome]
    m, avisos = resolver_modelo(model_id)
    notas, linhas = list(perfil.notas), []

    if perfil_nome == "imagem" or m.tier == "imagem":
        if perfil_nome != "imagem":
            avisos.append(f"{model_id} é modelo de imagem; use --perfil imagem")
        linhas += ['    response_modalities=["IMAGE"],',
                   '    image_config=types.ImageConfig(image_size="1K"),  # 512px | 1K | 2K | 4K']
    else:
        nivel = perfil.nivel
        if nivel == "MINIMAL" and not m.aceita_minimal:
            nivel = "LOW"
            avisos.append("MINIMAL indisponível neste modelo (Pro não aceita); usando LOW")
        linhas.append(f'    thinking_level="{nivel}",   # MINIMAL | LOW | MEDIUM | HIGH')
        if m.ignora_amostragem:
            linhas += ['    # temperature / top_p / top_k: DEPRECIADOS E IGNORADOS neste modelo.',
                       '    # Determinismo se obtém por system_instruction, não por parâmetro.']
            notas.append("temperature, topP e topK são ignorados aqui — não os envie esperando efeito")
        else:
            linhas += ['    temperature=1.0,   # 3.x: mantenha 1.0; baixar causa loops',
                       '    top_p=0.95,']
        linhas.append(f'    max_output_tokens={perfil.max_output},'
                      '  # thinking + resposta; ver armadilha MAX_TOKENS')
        if perfil.seed:
            linhas.append('    seed=42,           # reprodutibilidade para avaliação auditável')
        if perfil.schema:
            linhas += ['    response_mime_type="application/json",',
                       '    response_schema=SCHEMA,  # exija evidência, não só o resultado']
        notas.append("thinking é cobrado como saída; default do parâmetro é HIGH")

    linhas.append('    system_instruction=SYSTEM_INSTRUCTION,')
    if model_id != perfil.modelo_sugerido:
        notas.append(f"modelo sugerido para este perfil: {perfil.modelo_sugerido}")
    notas.append(f"preço ({model_id}): {m.preco}")
    if m.nota:
        notas.append(f"{model_id}: {m.nota}")
    notas.append(f"escalonamento: {perfil.escalonamento}")
    return linhas, notas, avisos


def imprimir(perfil_nome: str, model_id: str) -> None:
    linhas, notas, avisos = montar(perfil_nome, model_id)
    print(f"# perfil: {perfil_nome} — {PERFIS[perfil_nome].descricao}")
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
    print("\nNunca envie thinking_level e thinking_budget na mesma request (erro).")
    print("Se preferir outro modelo, rode de novo com --modelo <outro> — a escolha é sua.")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--perfil", choices=sorted(PERFIS))
    p.add_argument("--modelo")
    p.add_argument("--listar", action="store_true")
    args = p.parse_args()

    if args.listar:
        print("PERFIS")
        for nome, perfil in PERFIS.items():
            nivel = perfil.nivel or "-"
            print(f"  {nome:<18} {nivel:<7} {perfil.modelo_sugerido:<28} {perfil.descricao}")
        print("\nMODELOS DOCUMENTADOS (geração 3.x)")
        for nome, m in MODELOS.items():
            ign = "  [ignora temperature/topP/topK]" if m.ignora_amostragem else ""
            print(f"  {nome:<30} {m.tier:<11}{ign}")
            print(f"  {'':<30} {m.preco}")
        return 0

    if not (args.perfil and args.modelo):
        p.error("--perfil e --modelo são obrigatórios (ou use --listar)")
    imprimir(args.perfil, args.modelo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

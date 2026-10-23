#!/usr/bin/env python3
"""Gera o GenerateContentConfig recomendado para um perfil de objetivo e um modelo 3.x ou 4.

Imprime o default real de thinking_level do modelo, marca o que ele IGNORA ou REJEITA e
informa o preço ao lado da recomendação — custo é informação, nunca critério. Cobre também
a linha de imagem Nano Banana.

A tabela MODELOS espelha references/modelos.md (verificado em 2026-10-23); tests/ confere
que os dois batem. Modelo fora da tabela: comportamento INFERIDO pela família, nunca MINIMAL.

Uso:
    python gerar_config.py --perfil avaliacao-regras --modelo gemini-4-argon
    python gerar_config.py --perfil classificacao --modelo gemini-3.8-flash
    python gerar_config.py --perfil imagem --modelo gemini-nano-banana-2.1
    python gerar_config.py --listar

Só stdlib.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field

NIVEIS = ("MINIMAL", "LOW", "MEDIUM", "HIGH")
TRES = ("LOW", "MEDIUM", "HIGH")
QUATRO = ("MINIMAL", "LOW", "MEDIUM", "HIGH")


@dataclass(frozen=True)
class Modelo:
    tier: str                              # pro | flash | flash-lite | imagem
    estagio: str = "GA"                    # GA | preview | depreciado | retira | retirado | inferido
    niveis: tuple[str, ...] = TRES
    default_nivel: str = "MEDIUM"
    ignora_amostragem: bool | None = True  # True ignora · False funciona · None a confirmar
    rejeita_amostragem: bool = False       # devolve erro se enviado
    aceita_seed: bool | None = None        # True confirmado · False rejeita · None não documentado
    cache: str = "explícito e implícito"
    retirada: str = ""
    preco: str = "consultar tabela oficial"
    nota: str = ""


MODELOS: dict[str, Modelo] = {
    "gemini-4-argon": Modelo(
        "pro", "GA", TRES, "MEDIUM", True, aceita_seed=None,
        cache="só implícito, durável (sem CachedContent); mínimo 4.096 (modelo) a 6.144 (guia)",
        retirada="≥ 2027-10-13",
        nota="janela UNIFICADA 1.048.576 (entrada + thinking + resposta) · default por request "
             "65.536 (32.768 em HTTP sem streaming) · MINIMAL e thinking_budget → 400 · "
             "candidate_count / frequency_penalty / presence_penalty → 400"),
    "gemini-4-argon-cyber-permissive": Modelo(
        "pro", "GA (allowlist)", TRES, "HIGH", True, aceita_seed=None,
        cache="só implícito, durável", retirada="sem data",
        nota="variante allowlist; default HIGH; sem computer use; global e us"),
    "gemini-3.8-flash": Modelo(
        "flash", "GA", TRES, "MEDIUM", True, aceita_seed=None,
        cache="explícito e implícito; mínimo implícito 6.144", retirada="≥ 2027-09-02",
        nota="Flash principal · MINIMAL → erro de validação · saída máx. 65.536 · usa mais tokens "
             "que o 3.7 em esforço alto"),
    "gemini-3.7-flash": Modelo(
        "flash", "depreciado", TRES, "MEDIUM", True, aceita_seed=None,
        cache="explícito e implícito; mínimo implícito 6.144",
        retirada="2027-01-28 → gemini-3.8-flash",
        preco="$0,75 / $3,75 até 2026-12-31; $1,50 / $7,50 a partir de 2027-01-01",
        nota="substituído pelo 3.8; na Gemini API já roteia para 3.8"),
    "gemini-3.6-flash": Modelo(
        "flash", "retira", QUATRO, "MEDIUM", True, aceita_seed=None,
        retirada="2026-11-19 → gemini-3.8-flash"),
    "gemini-3.5-flash": Modelo(
        "flash", "GA", QUATRO, "MEDIUM", None, aceita_seed=None,
        cache="explícito e implícito; mínimo 4.096", retirada="≥ 2027-05-19"),
    "gemini-3.5-flash-lite": Modelo(
        "flash-lite", "GA", QUATRO, "MINIMAL", True, aceita_seed=None,
        cache="explícito e implícito; mínimo 4.096", retirada="≥ 2027-07-21",
        preco="$0,30 / $2,50 por 1M", nota="default MINIMAL; LOW já é um degrau acima"),
    "gemini-3.1-flash-lite": Modelo(
        "flash-lite", "GA", QUATRO, "MINIMAL", None, aceita_seed=None,
        cache="explícito e implícito; mínimo 4.096", retirada="≥ 2027-05-07"),
    "gemini-3.1-pro-preview": Modelo(
        "pro", "preview", TRES, "HIGH", False, aceita_seed=True,
        cache="implícito, mínimo 6.144; explícito listado", retirada="sem data",
        preco="$2,00 / $12,00 por 1M · acima de 200K de contexto: $4,00 / $18,00",
        nota="PREVIEW, só endpoint global · contexto 1M · saída máx. 65.536 · temperature 1.0 / "
             "topP 0.95 / topK fixo 64 funcionam · introduziu MEDIUM"),
    "gemini-3-flash": Modelo(
        "flash", "preview", QUATRO, "HIGH", None, aceita_seed=None,
        cache="implícito, mínimo 6.144", retirada="sem data"),
    "gemini-nano-banana-2.1": Modelo(
        "imagem", "GA", (), "", False, rejeita_amostragem=True, aceita_seed=False,
        cache="implícito", retirada="sem data",
        nota="Nano Banana 2.1 · generalista · 1K (default), 2K, 4K · 1.120 / 1.680 / 3.780 tokens "
             "por imagem · entrada 1.120 por imagem · contexto 131.072 · C2PA · só global · "
             "seed/temperature/topP/topK → erro de API"),
    "gemini-3-pro-image": Modelo(
        "imagem", "GA", (), "", False, aceita_seed=None, cache="implícito",
        retirada="≥ 2027-05-28",
        preco="$3,00 / $15,00 por 1M · ou $0,134/imagem 1K-2K, $0,24/imagem 4K "
              "· batch: $0,067/imagem 2K",
        nota="Nano Banana Pro · 512px, 1K, 2K, 4K · 1.120 tokens (1K e 2K), 2.000 (4K) · "
             "quando o 2.1 não bastar em texto na imagem"),
    "gemini-3.1-flash-image": Modelo(
        "imagem", "depreciado", (), "", False, aceita_seed=None, cache="implícito",
        retirada="depreciado na Gemini API em 2026-10-06 → gemini-nano-banana-2.1",
        nota="Nano Banana 2 · não use em projeto novo"),
    "gemini-3.1-flash-lite-image": Modelo(
        "imagem", "GA", (), "", False, aceita_seed=None, cache="implícito",
        retirada="≥ 2027-06-28", nota="Nano Banana 2 Lite · somente 1K"),
}

ALIASES = {
    "gemini-3.1-pro": ("gemini-3.1-pro-preview",
                       "'gemini-3.1-pro' não existe na Vertex; o id é 'gemini-3.1-pro-preview' "
                       "(preview, só endpoint global)."),
}


def resolver_modelo(model_id: str) -> tuple[Modelo, list[str]]:
    if model_id in MODELOS:
        return MODELOS[model_id], []
    if model_id in ALIASES:
        alvo, aviso = ALIASES[model_id]
        return MODELOS[alvo], [aviso]
    if model_id.startswith("gemini-2.5") or model_id.startswith("gemini-2.0"):
        return (Modelo("pro" if "pro" in model_id else "flash", "retirado", (), "", None),
                [f"{model_id!r} foi retirado da Vertex (2.5: 2026-10-20). Migre para 3.8 Flash ou "
                 "4 Argon: thinking_budget vira thinking_level e temperature/topP/topK deixam de "
                 "ter efeito.",
                 "Se a migração não for possível agora, registre como pendência explícita."])
    img = "image" in model_id or "nano-banana" in model_id
    if img:
        return (Modelo("imagem", "inferido", (), "", False, aceita_seed=None, cache="implícito",
                       nota="id não consta na lista documentada desta skill"),
                [f"{model_id!r} não está na lista documentada; comportamento INFERIDO. Confirme id, "
                 "estágio, resoluções e parâmetros rejeitados na página do modelo."])
    if model_id.startswith("gemini-4"):
        return (Modelo("pro", "inferido", TRES, "MEDIUM", True, aceita_seed=None,
                       cache="só implícito (inferido)",
                       nota="id não consta na lista documentada; regras do 4 Argon assumidas"),
                [f"{model_id!r} não está na lista documentada; comportamento INFERIDO pela linha 4 "
                 "(sem MINIMAL, amostragem ignorada, cache só implícito). Confirme na página do modelo."])
    if model_id.startswith("gemini-3"):
        pro = "pro" in model_id
        return (Modelo("pro" if pro else "flash", "inferido", TRES, "MEDIUM", None,
                       aceita_seed=None, nota="id não consta na lista documentada desta skill"),
                [f"{model_id!r} não está na lista documentada; comportamento INFERIDO pela linha 3.x "
                 "(níveis LOW/MEDIUM/HIGH, default MEDIUM; MINIMAL NÃO assumido). Confirme id, "
                 "níveis, amostragem, estágio e região na página do modelo."])
    return (Modelo("flash", "inferido", TRES, "MEDIUM", None, nota="família não reconhecida"),
            [f"{model_id!r} não reconhecido. Confirme família, níveis, amostragem e estágio."])


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
        ["thinking baixo é adequado: a decisão é de roteamento, não de mérito",
         "no 3.5-flash-lite o default é MINIMAL; LOW é escolha ativa para cima"]),
    "classificacao": Perfil(
        "atribuir rótulo de um conjunto fechado",
        "MEDIUM", 4096, False, True, "gemini-3.8-flash",
        "rótulo 'indeterminado' em vez de forçar a classe mais próxima",
        ["MEDIUM é o default do 3.8 Flash; LOW se a latência mandar e a acurácia permitir",
         "HIGH antes de trocar de modelo"]),
    "extracao": Perfil(
        "tirar campos estruturados de um documento",
        "HIGH", 16384, True, True, "gemini-3.8-flash",
        "campo nulo + motivo, nunca valor inventado para preencher",
        ["schema deve exigir o trecho de origem de cada campo, não só o valor",
         "media_resolution=HIGH nas páginas que carregam os campos",
         "4 Argon quando a extração exigir raciocínio sobre documento inteiro"]),
    "avaliacao-regras": Perfil(
        "julgar conteúdo contra regras multicamada, com justificativa",
        "HIGH", 32768, True, True, "gemini-4-argon",
        "'revisão humana' quando a regra depender de julgamento de grau",
        ["schema deve exigir regra_id + trecho citado por achado",
         "se alguma regra for posicional/visual, envie a mídia original além do texto",
         "alternativa com temperature/seed funcionando: gemini-3.1-pro-preview (preview, só global)"]),
    "alto-risco": Perfil(
        "decisão com consequência difícil de reverter",
        "HIGH", 65536, True, True, "gemini-4-argon",
        "humano no circuito por padrão; automático só na decisão conservadora",
        ["aqui latência é o recurso barato",
         "registre entrada, system instruction, thinking_level, schema e model id para "
         "reproduzir o caso depois; seed só onde confirmado"]),
    "documento-longo": Perfil(
        "contexto grande domina a tarefa",
        "HIGH", 32768, False, True, "gemini-4-argon",
        "marcar 'contexto insuficiente' em vez de responder por uma fatia",
        ["PDF: 280 a 1.120 tokens por página conforme media_resolution; 300 páginas em MEDIUM "
         "≈ 168k tokens só de documento",
         "4 Argon: janela unificada; entrada grande reduz o espaço de resposta"]),
    "criativo": Perfil(
        "geração aberta de texto, sem resposta única correta",
        "HIGH", 16384, False, False, "gemini-4-argon",
        "não se aplica",
        ["onde temperature funciona, mantenha 1.0: é o ponto de calibração"]),
    "imagem": Perfil(
        "gerar ou editar imagem",
        "", 0, False, False, "gemini-nano-banana-2.1",
        "não se aplica",
        ["Nano Banana 2.1 é o generalista; Nano Banana Pro quando o 2.1 não bastar em texto na imagem",
         "1K é o default; suba a 2K/4K só se a imagem for ampliada, impressa ou inspecionada",
         "marca de proveniência (C2PA/SynthID) é sempre aplicada e não é removível"]),
}


def _nivel_permitido(pedido: str, m: Modelo) -> tuple[str, str | None]:
    """Devolve (nível a usar, aviso). Nunca sobe para MINIMAL; desconhecido cai em LOW."""
    if pedido in m.niveis:
        return pedido, None
    if not m.niveis:
        return "", None
    if pedido == "MINIMAL":
        return "LOW", f"MINIMAL indisponível em {m.tier} ({', '.join(m.niveis)}); usando LOW"
    return "LOW", f"nível {pedido!r} indisponível neste modelo; usando LOW"


def montar(perfil_nome: str, model_id: str) -> tuple[list[str], list[str], list[str]]:
    perfil = PERFIS[perfil_nome]
    m, avisos = resolver_modelo(model_id)
    notas, linhas = list(perfil.notas), []

    if m.estagio == "retirado":
        avisos.append("modelo retirado: nenhuma configuração emitida")
        return [], notas, avisos
    if m.estagio == "preview":
        avisos.append(f"{model_id} é PREVIEW: sem data de retirada e sem garantia de GA; "
                      "registre a decisão de usar preview em produção")
    if m.estagio in ("depreciado", "retira"):
        avisos.append(f"{model_id} está {m.estagio}: {m.retirada}")

    if perfil_nome == "imagem" or m.tier == "imagem":
        if perfil_nome != "imagem":
            avisos.append(f"{model_id} é modelo de imagem; use --perfil imagem")
        if m.tier != "imagem":
            avisos.append(f"{model_id} não é modelo de imagem; use gemini-nano-banana-2.1")
        linhas += ['    response_modalities=["IMAGE"],',
                   '    image_config=types.ImageConfig(image_size="1K"),  # 1K (default) | 2K | 4K']
        if m.rejeita_amostragem:
            linhas.append('    # NÃO envie seed, temperature, top_p, top_k: este modelo devolve erro de API.')
            notas.append("seed, temperature, topP e topK devolvem erro neste modelo — não os envie")
    else:
        nivel, aviso = _nivel_permitido(perfil.nivel, m)
        if aviso:
            avisos.append(aviso)
        igual = " (igual ao default; explícito por clareza)" if nivel == m.default_nivel else ""
        linhas.append(f'    thinking_level="{nivel}",   # níveis: {" | ".join(m.niveis)}'
                      f' · default deste modelo: {m.default_nivel}{igual}')
        if m.ignora_amostragem is True:
            linhas += ['    # NÃO envie temperature / top_p / top_k: ignorados hoje, HTTP 400 em geração futura.',
                       '    # Determinismo: thinking_level + response_schema + system_instruction.']
            notas.append("temperature, topP e topK são ignorados aqui — remova, não comente")
        elif m.ignora_amostragem is False:
            linhas.append('    temperature=1.0,   # funciona neste modelo; mantenha 1.0 (baixar causa loops)')
        else:
            linhas.append('    # amostragem (temperature/top_p/top_k): a confirmar na página do modelo; sem confirmação, não envie.')
            notas.append("efeito de temperature/topP/topK não confirmado neste modelo")
        unificada = "janela unificada: entrada + thinking + resposta ≤ 1.048.576; " if "4-argon" in model_id or m.tier == "pro" and m.estagio == "inferido" and model_id.startswith("gemini-4") else ""
        linhas.append(f'    max_output_tokens={perfil.max_output},'
                      f'  # thinking + resposta; {unificada}ver armadilha MAX_TOKENS')
        if perfil.seed:
            if m.aceita_seed is True:
                linhas.append('    seed=42,           # reprodutibilidade para avaliação auditável')
            elif m.aceita_seed is False:
                linhas.append('    # seed: rejeitado por este modelo.')
            else:
                linhas.append('    # seed: efeito não documentado neste modelo; reprodutibilidade = registrar entrada + model id.')
                notas.append("seed não documentado neste modelo; registre entrada, schema, thinking_level e model id")
        if perfil.schema:
            linhas += ['    response_mime_type="application/json",',
                       '    response_schema=SCHEMA,  # exija evidência, não só o resultado']
        notas.append(f"default de thinking_level deste modelo: {m.default_nivel}; "
                     "chamada sem o parâmetro usa esse valor")
        notas.append("thinking é cobrado como saída")

    linhas.append('    system_instruction=SYSTEM_INSTRUCTION,')
    if model_id != perfil.modelo_sugerido:
        notas.append(f"modelo sugerido para este perfil: {perfil.modelo_sugerido}")
    notas.append(f"estágio ({model_id}): {m.estagio}" + (f" · retirada: {m.retirada}" if m.retirada else ""))
    notas.append(f"cache ({model_id}): {m.cache}")
    notas.append(f"preço ({model_id}): {m.preco}")
    if m.nota:
        notas.append(f"{model_id}: {m.nota}")
    notas.append(f"escalonamento: {perfil.escalonamento}")
    return linhas, notas, avisos


def imprimir(perfil_nome: str, model_id: str) -> None:
    linhas, notas, avisos = montar(perfil_nome, model_id)
    print(f"# perfil: {perfil_nome} — {PERFIS[perfil_nome].descricao}")
    print(f"# modelo: {model_id}\n")
    if linhas:
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
    print("\nNunca envie thinking_level e thinking_budget na mesma request (erro); no 4 Argon, "
          "thinking_budget sozinho já devolve 400.")
    print("Se preferir outro modelo, rode de novo com --modelo <outro> — a escolha é sua.")


def listar() -> None:
    print("PERFIS")
    for nome, perfil in PERFIS.items():
        nivel = perfil.nivel or "-"
        print(f"  {nome:<18} {nivel:<7} {perfil.modelo_sugerido:<28} {perfil.descricao}")
    print("\nMODELOS DOCUMENTADOS (references/modelos.md, verificado em 2026-10-23)")
    for nome, m in MODELOS.items():
        niveis = f"{'/'.join(m.niveis)} (default {m.default_nivel})" if m.niveis else "-"
        amostra = {True: "amostragem ignorada", False: "amostragem funciona",
                   None: "amostragem a confirmar"}[m.ignora_amostragem]
        if m.rejeita_amostragem:
            amostra = "amostragem REJEITADA (erro)"
        print(f"  {nome:<32} {m.tier:<11} {m.estagio:<15} {niveis}")
        print(f"  {'':<32} {amostra} · cache: {m.cache} · retirada: {m.retirada or '-'}")
        print(f"  {'':<32} preço: {m.preco}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--perfil", choices=sorted(PERFIS))
    p.add_argument("--modelo")
    p.add_argument("--listar", action="store_true")
    args = p.parse_args()

    if args.listar:
        listar()
        return 0
    if not (args.perfil and args.modelo):
        p.error("--perfil e --modelo são obrigatórios (ou use --listar)")
    imprimir(args.perfil, args.modelo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

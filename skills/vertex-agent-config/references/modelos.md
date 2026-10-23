# Modelos Gemini na Vertex AI — geração 3.x e 4

**Verificado em 2026-10-23** nas páginas oficiais da Vertex (página de cada modelo, "Thinking",
"Model versions and lifecycle", "Context caching", "Document understanding"). Datas e estágios
são **da Vertex**; a Gemini API deprecia antes e roteia automaticamente (ex.: 3.7 Flash
depreciado lá em 2026-10-08; na Vertex retira em 2027-01-28). Ao fixar um id, confirme nesta
tabela e na página do modelo; esta é a **única fonte** de fatos por modelo nesta skill —
`SKILL.md`, `parametros.md`, `multimodal.md` e `scripts/gerar_config.py` apontam para cá.

A geração 2.5 foi retirada da Vertex em 2026-10-20. Não aparece nas tabelas de decisão.

## Texto e multimodal

| Model id | Tier · estágio | Lançado → retira | `thinking_level` (default) | temperature/topP/topK | Cache | Endpoints |
|---|---|---|---|---|---|---|
| `gemini-4-argon` | topo · **GA** | 2026-10-13 → ≥ 2027-10-13 | LOW, MEDIUM, HIGH (**MEDIUM**); `MINIMAL` e `thinking_budget` → HTTP 400 | ignorados; `candidate_count`, `frequency_penalty`, `presence_penalty` → HTTP 400 | **só implícito**, durável por padrão; mínimo 4.096 (página do modelo) ou 6.144 (guia) | global, us, eu, europe-west2, asia-southeast1 |
| `gemini-4-argon-cyber-permissive` | variante allowlist · GA | 2026-10-13 → sem data | idem (**HIGH**) | idem | idem | global, us |
| `gemini-3.8-flash` | Flash principal · **GA** | 2026-09-02 → ≥ 2027-09-02 | LOW, MEDIUM, HIGH (**MEDIUM**); `MINIMAL` → erro de validação | ignorados (defaults listados: 1.0 / 0.95 / 64, sem efeito) | explícito e implícito; mínimo implícito 6.144 | global, us, eu |
| `gemini-3.7-flash` | Flash · **depreciado** | 2026-08-13 → **2027-01-28**, substituto 3.8 | LOW, MEDIUM, HIGH (**MEDIUM**) | ignorados | explícito e implícito; mínimo implícito 6.144 | global, us, eu |
| `gemini-3.6-flash` | Flash · **retira** | 2026-07-21 → **2026-11-19**, substituto 3.8 | MINIMAL, LOW, MEDIUM, HIGH (MEDIUM) | ignorados | explícito e implícito | — |
| `gemini-3.5-flash` | Flash · GA | 2026-05-19 → ≥ 2027-05-19 | MINIMAL, LOW, MEDIUM, HIGH (MEDIUM) | a confirmar | explícito e implícito; mínimo 4.096 | — |
| `gemini-3.5-flash-lite` | Flash-Lite · GA | 2026-07-21 → ≥ 2027-07-21 | MINIMAL, LOW, MEDIUM, HIGH (**MINIMAL**) | ignorados | explícito e implícito; mínimo 4.096 | — |
| `gemini-3.1-flash-lite` | Flash-Lite · GA | 2026-05-07 → ≥ 2027-05-07 | MINIMAL, LOW, MEDIUM, HIGH (MINIMAL) | a confirmar | explícito e implícito; mínimo 4.096 | — |
| `gemini-3.1-pro-preview` | Pro · **preview** | 2026-02-19 → sem data | LOW, MEDIUM, HIGH (**HIGH**); introduziu `MEDIUM` | **funcionam** (1.0 / 0.95 / topK fixo 64) | implícito, mínimo 6.144; explícito listado | **só global** |
| `gemini-3-flash` | Flash · preview | — | MINIMAL, LOW, MEDIUM, HIGH (HIGH) | a confirmar | implícito, mínimo 6.144 | — |

Notas que mudam a decisão:

- **O id do Pro na Vertex é `gemini-3.1-pro-preview`.** Não existe `gemini-3.1-pro` GA na Vertex.
  Preview em produção é decisão do usuário, registrada; a skill avisa toda vez.
- **Default de `thinking_level` é por modelo**, não da geração: HIGH só no 3.1 Pro preview e no
  3 Flash preview; MEDIUM em 4 Argon e nos Flash 3.5 a 3.8; MINIMAL nos Flash-Lite.
- **`MINIMAL` só existe em 3.6, 3.5, 3.5-lite, 3.1-lite e 3 Flash.** Em 4 Argon, 3.8, 3.7 e
  3.1 Pro devolve erro. Onde existe, exige *thought signatures* em conversa multi-turn
  (`400: INVALID_ARGUMENT` sem elas).
- **`thinking_level` e `thinking_budget` na mesma request devolvem erro** em toda a linha 3.x;
  no 4 Argon, `thinking_budget` sozinho já devolve 400.
- `gemini-3.1-pro-preview`: contexto 1.048.576, saída máxima 65.536. `maxOutputTokens` default
  de 8.192 citado em versões anteriores desta skill: **não consta na página atual**; dimensione
  explicitamente.
- `gemini-3.8-flash`: contexto 1.048.576, saída máxima 65.536. A página diz que usa mais tokens
  que o 3.7 em níveis altos de esforço.
- `gemini-4-argon`: **janela unificada** de 1.048.576 (entrada + thinking + chamadas de função +
  resposta). Detalhe em `parametros.md`, seção "Gemini 4 Argon".
- Preço do Pro acima de 200K tokens de contexto: $2,00 / $12,00 · acima de 200K: $4,00 / $18,00
  (linha mantida da versão anterior desta skill; confira na tabela oficial).

## Especializados

| Model id | Estágio | Nota |
|---|---|---|
| `gemini-omni-1.1-flash` | GA 2026-08-27 | substitui `gemini-omni-flash-preview`, depreciado em 2026-09-30 |
| `gemini-3.5-transcribe`, `gemini-3.5-transcribe-live` | GA 2026-08-26 | transcrição dedicada; não use modelo de raciocínio para transcrever |
| `gemini-3.8-live`, `gemini-3.8-live-extended-thinking` | GA 2026-09-24 (Vertex) | áudio em tempo real |
| `gemini-3.8-flash-tts`, `gemini-3.8-flash-lite-tts` | GA 2026-09-22 | TTS |
| `gemini-embedding-2` | GA 2026-04-22 | embedding |

## Geração de imagem — linha Nano Banana

Única tabela de modelos de imagem desta skill; `multimodal.md` aponta para cá.

| Model id | Nome | Estágio · retira | Resoluções | Tokens de saída por imagem | Contexto | Proveniência | Parâmetros |
|---|---|---|---|---|---|---|---|
| `gemini-nano-banana-2.1` | **Nano Banana 2.1** | **GA 2026-10-06** · sem data | 1K (default), 2K, 4K | **1.120** (1K) · **1.680** (2K) · **3.780** (4K); entrada 1.120 por imagem | 131.072; saída máx. 32.768 | Content Credentials (**C2PA**); SynthID não citado na página | `seed`, `temperature`, `topP`, `topK` → **erro de API** |
| `gemini-3-pro-image` | Nano Banana Pro | GA 2026-05-28 · ≥ 2027-05-28 | 512px, 1K (default), 2K, 4K | 1.120 (1K e 2K), 2.000 (4K) | 65.536 | SynthID (texto anterior desta skill; confirme) | — |
| `gemini-3.1-flash-image` | Nano Banana 2 | **depreciado** na Gemini API em 2026-10-06 (sem data de desligamento); Vertex ≥ 2027-05-28 | 512px, 1K, 2K, 4K | 747 / 1.120 / 1.680 / 2.520 | 131.072 | — | use `gemini-nano-banana-2.1` |
| `gemini-3.1-flash-lite-image` | Nano Banana 2 Lite | GA 2026-06-23 · ≥ 2027-06-28 | somente 1K | — | 65.536 | SynthID *always on* (texto anterior; confirme) | — |

`gemini-3-pro-image` (Nano Banana Pro): preço na Vertex $3,00 / $15,00 por 1M tokens;
alternativamente $0,134 por imagem 1K/2K e $0,24 por imagem 4K; batch/flex $0,067 por imagem
2K (linha mantida da versão anterior desta skill; confira na tabela oficial). Demais modelos
de imagem: consultar tabela oficial.

Escolha: **`gemini-nano-banana-2.1` é o generalista** (GA, 1K a 4K, até 14 imagens de entrada
por prompt, só endpoint `global`). **`gemini-3-pro-image`** quando o 2.1 não bastar em
renderização de texto dentro da imagem. `gemini-3.1-flash-lite-image` só 1K.

Proveniência: a página do 2.1 lista C2PA; SynthID consta nas páginas anteriores do Pro e do
Lite. Trate marca de proveniência como **sempre presente e não removível**; qual tecnologia,
confirme na página do modelo escolhido.

## Antes de fixar um id

Modelos entram, saem e mudam de tier em semanas (3.6 Flash viveu quatro meses). **Confirme na
página do modelo** o id, o estágio, a data de retirada e a disponibilidade na sua região antes
de fixar em configuração; **mantenha o model id parametrizado** (env var ou settings), nunca
literal espalhado pelo código; e registre em `.rules/decisoes.md` (quando o projeto tiver) o id
escolhido com a data de verificação.

Valores "a confirmar" ou "consultar tabela oficial" não foram confirmados nesta verificação;
não os presuma iguais aos do vizinho de tier.

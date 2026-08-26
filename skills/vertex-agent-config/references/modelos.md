# Modelos Gemini na Vertex AI — geração 3.x

Esta skill cobre **exclusivamente a geração 3.x**. A geração 2.5 não é recomendada para
projeto novo e não aparece nas tabelas de decisão.

## Texto e multimodal (GA)

| Model id | Tier | Preço Vertex (entrada / saída por 1M) |
|---|---|---|
| `gemini-3.1-pro` | Pro | **$2,00 / $12,00** · acima de 200K de contexto: **$4,00 / $18,00** |
| `gemini-3.7-flash` | Flash (mais recente) | **$0,75 / $3,75** promocional até **2026-12-31**; **$1,50 / $7,50** a partir de **2027-01-01** |
| `gemini-3.6-flash` | Flash | consultar tabela oficial |
| `gemini-3.5-flash` | Flash | consultar tabela oficial |
| `gemini-3-flash` | Flash | consultar tabela oficial |
| `gemini-3.5-flash-lite` | Flash-Lite | **$0,30 / $2,50** |
| `gemini-3.1-flash-lite` | Flash-Lite | consultar tabela oficial |

Especializados: **`gemini-omni-flash`** (Preview), **`gemini-3.5-transcribe`** (GA).
Embedding: **`gemini-embedding-2`** (GA).

`gemini-3.1-pro`: contexto de **1M tokens**, `maxOutputTokens` default **8.192** — o
default é baixo para tarefas com thinking alto; dimensione explicitamente.

O degrau de preço do Pro acima de **200K tokens de contexto** dobra a entrada e sobe a
saída em 50%. Documento longo cruza esse limiar sem aviso.

## Geração de imagem — linha Nano Banana

| Model id | Nome | Resoluções | Tokens de saída |
|---|---|---|---|
| `gemini-3-pro-image` | **Nano Banana Pro** | 512px, 1K (default), 2K, 4K | **1120** (1K e 2K), **2000** (4K) |
| `gemini-3.1-flash-image` | **Nano Banana 2** | 512px, 1K (default), 2K, 4K | **747** (512px), **1120** (1K), **1680** (2K), **2520** (4K) |
| `gemini-3.1-flash-lite-image` | — | **somente 1K** | — |

**`gemini-3-pro-image` (Nano Banana Pro)** — lançado em **2026-06-18**. Preço na Vertex:
**$3,00 / $15,00 por 1M tokens**; alternativamente **$0,134 por imagem 1K/2K** e
**$0,24 por imagem 4K**. Em modo batch/flex (entrega assíncrona): **$0,067 por imagem 2K**.

**SynthID**: toda imagem gerada ou editada carrega marca d'água invisível identificando-a
como gerada por IA. No `gemini-3.1-flash-lite-image` é *always on*. Não é opcional e não
deve ser tratado como removível.

Escolha entre eles: **Nano Banana 2 (`gemini-3.1-flash-image`) é o generalista** para a
maioria das tarefas; **Nano Banana Pro (`gemini-3-pro-image`)** quando a qualidade de
renderização — especialmente **texto dentro da imagem** — for o critério.

Batch/flex vale quando a entrega pode ser assíncrona: metade do preço por imagem 2K.

## Controle de raciocínio — `thinking_level`

A geração 3.x usa **`thinking_level`**, não `thinking_budget`.

Valores: **`MINIMAL`**, **`LOW`**, **`MEDIUM`**, **`HIGH`**. Default **`HIGH`**.

- **`MEDIUM` foi acrescentado na linha 3.1** para dar um degrau intermediário entre custo,
  desempenho e velocidade. Se `LOW` erra e `HIGH` custa demais, é aqui que se resolve.
- **Pro não aceita `MINIMAL`.**
- **`MINIMAL` exige *thought signatures*.**
- Default `HIGH` significa que **toda chamada sem o parâmetro usa o raciocínio máximo** —
  e paga por ele. É o default certo para qualidade, e vale saber que é uma escolha ativa.

**Enviar `thinking_level` e `thinking_budget` na mesma request devolve erro.**
`thinking_budget` é a API da geração 2.5; não misture.

**Tokens de thinking são cobrados como saída** — no `gemini-3.1-pro`, a $12,00 por 1M.

## Parâmetros de amostragem depreciados

Em **`gemini-3.7-flash`**, **`gemini-3.6-flash`** e **`gemini-3.5-flash-lite`**,
`temperature`, `topP` e `topK` são **depreciados e ignorados** — enviá-los não dá erro e
não faz nada.

Nos demais modelos 3.x, mantenha `temperature` em **1.0**: baixá-la pode causar loops e
degradar o raciocínio.

**Determinismo na geração 3.x se obtém por *system instruction***, não por parâmetro.
Ver `references/parametros.md`.

## Antes de fixar um id

Modelos entram, saem e mudam de tier. **Confirme na tabela oficial da Vertex** o id, o
preço e a disponibilidade na sua região antes de fixar em configuração — e **mantenha o
model id parametrizado** (env var ou settings), nunca literal espalhado pelo código.

Preços marcados "consultar tabela oficial" não foram confirmados nesta pesquisa; não os
presuma iguais aos do vizinho de tier.

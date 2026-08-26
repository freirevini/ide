# Modelos, thinking e roteamento

## Preços aproximados (USD por 1M tokens, entrada/saída)

| Modelo | Entrada | Saída | Observação |
|---|---|---|---|
| Gemini 2.5 Pro | $1,25 | $10,00 | **dobra acima de 200K tokens de contexto** |
| Gemini 2.5 Flash | $0,30 | $2,50 | |
| Gemini 2.5 Flash-Lite | $0,10 | $0,40 | |

Duas leituras que mudam decisão:

- Pro custa **~12x** o Flash-Lite na entrada e **25x** na saída. Manter o agente 1
  (classificação de tipo de arquivo) em Pro é a forma mais cara possível de resolver
  um problema de rótulo.
- O limiar de 200K do Pro é fácil de cruzar com peça grande + muitas regras injetadas,
  e cruza sem aviso. Caching e `top_k` disciplinado pagam duas vezes nessa faixa.

**Tokens de thinking são cobrados como saída.** Um budget alto no agente 2 aparece na
fatura na linha mais cara da tabela.

## Thinking — família 2.5

| Modelo | Intervalo de `thinking_budget` | Desliga? |
|---|---|---|
| 2.5 Pro | **128 – 32768** | **Não** |
| 2.5 Flash | **0 – 24576** | Sim (`0`) |
| 2.5 Flash-Lite | — | Não pensa por padrão |

Consequência direta: se o plano era "desligar o thinking do Pro", não existe esse
plano — a única forma é trocar de modelo.

## Thinking — família 3.x (referência, provavelmente indisponível)

Gemini 3 usa **`thinking_level`**: `MINIMAL`, `LOW`, `HIGH`.
- Pro **não aceita** `MINIMAL`.
- `MINIMAL` exige **thought signatures**.

**Nunca envie `thinking_budget` e `thinking_level` na mesma request — HTTP 400.**

Se o deploy corporativo libera apenas a família 2.5, esta seção é informação de
migração futura, não opção presente. Não proponha `thinking_level` como solução.

## A armadilha do `maxOutputTokens`

Tokens de thinking **contam contra `maxOutputTokens`**. Com `responseSchema`, estourar
o limite devolve:

```
response.text   -> None
response.parsed -> None
finish_reason   -> MAX_TOKENS
```

Sem exceção lançada. Código que faz `json.loads(response.text)` quebra a jusante com
`TypeError`, e o log registra "erro de parsing" — diagnóstico errado que manda o
investigador para o schema em vez do budget.

Padrão correto:

```python
resp = client.models.generate_content(...)

cand = resp.candidates[0] if resp.candidates else None
if cand is None or cand.finish_reason == "MAX_TOKENS":
    # thinking + resposta estouraram o orçamento; não é erro de schema
    raise OrcamentoDeSaidaEstourado(
        f"finish_reason={getattr(cand, 'finish_reason', None)} "
        f"thinking={resp.usage_metadata.thoughts_token_count} "
        f"max_output={config.max_output_tokens}"
    )

veredito = resp.parsed
```

Dimensione `maxOutputTokens` como **thinking + resposta**, com folga. Meça
`thoughts_token_count` real antes de escolher o número em vez de estimar.

## Roteamento por agente

| Agente | Tarefa | Escolha | Thinking |
|---|---|---|---|
| 1 | Classificar tipo de arquivo (conjunto fechado) | Flash, candidato a Flash-Lite | `0` no Flash |
| 2 | Avaliar compliance e justificar veredito | Pro (ou Flash, **só se o golden set passar**) | manter; reduzir com muito cuidado |

Racional: o agente 1 escolhe entre poucas classes com sinal forte (extensão, layout,
primeiras páginas) — raciocínio estendido não agrega e é latência pura. O agente 2
precisa relacionar conteúdo com regras e justificar; é onde cortar thinking degrada
precisão primeiro.

Se o model id hoje é uma constante única compartilhada pelos dois agentes, **essa
refatoração vem antes** — separar a configuração por agente é pré-requisito de
qualquer roteamento, e é mudança de baixo risco.

Rebaixar o agente 2 de Pro para Flash é a mudança de maior economia e maior risco
deste documento. Ela só entra com golden set completo aprovado, incluindo os casos
adversariais de injeção e as peças de fronteira — e a decisão deve considerar a
assimetria de erro (um falso "aprovado" custa mais que muitos falsos "reprovados").

## Lifecycle

Gemini 2.5 Pro / Flash / Flash-Lite: aposentadoria anunciada para **não antes de
2026-10-16**; a página de lifecycle da Vertex mostra **2026-10-20**.

Não é urgente, mas registre a data em comentário junto ao model id, para que a
migração apareça na leitura do código e não numa falha de produção.

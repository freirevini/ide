# Modelos, thinking e roteamento — geração 3.x

Esta skill cobre a **geração 3.x**. A 2.5 aparece apenas como estado legado a migrar.

## Preços na Vertex (por 1M tokens, entrada/saída)

| Modelo | Tier | Preço |
|---|---|---|
| `gemini-3.1-pro` | Pro | **$2,00 / $12,00** · **acima de 200K de contexto: $4,00 / $18,00** |
| `gemini-3.7-flash` | Flash (mais recente) | **$0,75 / $3,75** até **2026-12-31**; **$1,50 / $7,50** a partir de **2027-01-01** |
| `gemini-3.6-flash` | Flash | consultar tabela oficial |
| `gemini-3.5-flash` | Flash | consultar tabela oficial |
| `gemini-3-flash` | Flash | consultar tabela oficial |
| `gemini-3.5-flash-lite` | Flash-Lite | **$0,30 / $2,50** |
| `gemini-3.1-flash-lite` | Flash-Lite | consultar tabela oficial |

Especializados: `gemini-omni-flash` (Preview), `gemini-3.5-transcribe` (GA).
Imagem: `gemini-3-pro-image` (Nano Banana Pro), `gemini-3.1-flash-image` (Nano Banana 2).
Embedding: `gemini-embedding-2` (GA).

Três leituras que mudam decisão de tuning:

- **O Pro custa ~6,7x o Flash-Lite na entrada e ~4,8x na saída.** Manter classificação de
  arquivo no Pro é a forma mais cara possível de resolver um problema de rótulo.
- **O degrau de 200K do Pro dobra a entrada e sobe a saída em 50%.** Peça grande com
  muitas regras injetadas cruza sem aviso. Caching e `top_k` disciplinado pagam duas vezes
  nessa faixa.
- **O preço promocional do `gemini-3.7-flash` termina em 2026-12-31** e dobra em
  2027-01-01. Se o dimensionamento de custo foi feito no preço promocional, revise antes
  da virada.

**Tokens de thinking são cobrados como saída** — no `gemini-3.1-pro`, $12,00 por 1M. Um
`HIGH` desnecessário aparece na fatura, não na latência.

## Thinking — `thinking_level`

Valores: **`MINIMAL`**, **`LOW`**, **`MEDIUM`**, **`HIGH`**. Default **`HIGH`**.

- **`MEDIUM` entrou na linha 3.1.** É o degrau que faltava: quando `LOW` erra e `HIGH`
  custa demais, resolve aqui — **antes** de trocar de modelo. É a alavanca de tuning mais
  subutilizada da geração.
- **Pro não aceita `MINIMAL`.**
- **`MINIMAL` exige *thought signatures*.**
- **Default `HIGH`** significa que toda chamada sem o parâmetro usa raciocínio máximo e
  paga por ele. Num pipeline que nunca setou o parâmetro, **descer para `MEDIUM` no agente
  de classificação costuma ser o maior ganho isolado de custo e latência do sistema**.

**Nunca envie `thinking_level` e `thinking_budget` na mesma request — erro.**
`thinking_budget` é a API da geração 2.5.

## A armadilha do `maxOutputTokens`

Tokens de thinking **contam contra `maxOutputTokens`**. No `gemini-3.1-pro` o default é
**8.192** — baixo para `thinking_level=HIGH`.

Com `responseSchema`, estourar o limite devolve:

```
response.text   -> None
response.parsed -> None
finishReason    -> MAX_TOKENS
```

Sem exceção lançada. Código que faz `json.loads(response.text)` quebra a jusante com
`TypeError`, e o log registra "erro de parsing" — diagnóstico errado, que manda o
investigador para o schema em vez do orçamento.

```python
resp = client.models.generate_content(...)

cand = resp.candidates[0] if resp.candidates else None
if cand is None or cand.finish_reason == "MAX_TOKENS":
    raise OrcamentoDeSaidaEstourado(
        f"finish_reason={getattr(cand, 'finish_reason', None)} "
        f"thinking={resp.usage_metadata.thoughts_token_count} "
        f"max_output={config.max_output_tokens}"
    )

veredito = resp.parsed
```

Dimensione `maxOutputTokens` como **thinking + resposta**. Meça `thoughts_token_count`
real antes de escolher o número.

## Parâmetros de amostragem

Em **`gemini-3.7-flash`**, **`gemini-3.6-flash`** e **`gemini-3.5-flash-lite`**,
`temperature`, `topP` e `topK` são **depreciados e ignorados** — enviá-los não dá erro e
não faz nada. Determinismo ali é *system instruction*.

Nos demais 3.x, mantenha `temperature` em **1.0**: baixá-la pode causar loops e degradar o
raciocínio.

Consequência para tuning: **em boa parte da linha flash, `temperature` deixou de ser
alavanca.** Quem esperava reduzir variabilidade por parâmetro precisa reescrever como
instrução.

## Roteamento por agente

| Agente | Tarefa | Escolha | `thinking_level` |
|---|---|---|---|
| 1 | Classificar tipo de arquivo (conjunto fechado) | `gemini-3.5-flash-lite` ou `gemini-3.7-flash` | `LOW` a `MEDIUM` |
| 2 | Avaliar contra regras e justificar | `gemini-3.1-pro` | `HIGH` |

Racional: o agente 1 escolhe entre poucas classes com sinal forte (extensão, layout,
primeiras páginas) — raciocínio profundo ali é latência e custo puros. O agente 2 precisa
relacionar conteúdo com regras e justificar; é onde baixar o thinking degrada a precisão
primeiro.

Se o model id hoje é uma constante única compartilhada pelos dois agentes, **essa
refatoração vem antes** — separar a configuração por agente é pré-requisito de qualquer
roteamento, e é mudança de baixo risco.

Rebaixar o agente 2 de Pro para Flash é a mudança de maior economia e maior risco desta
skill. Só entra com golden set completo aprovado, incluindo os casos adversariais de
injeção e as peças de fronteira, e considerando a assimetria de erro (um falso "aprovado"
custa mais que muitos falsos "reprovados").

## Se o projeto ainda está na 2.5

Trate como migração pendente, não como configuração a otimizar. A mudança **não é troca de
string**:

- `thinking_budget` (faixa numérica) vira `thinking_level` (`MINIMAL`/`LOW`/`MEDIUM`/`HIGH`);
- nos flash recentes, `temperature`/`topP`/`topK` deixam de ter efeito;
- os preços mudam, e o degrau de 200K muda de valor.

Configuração que dependia de `temperature` baixa precisa ser reescrita como *system
instruction*. **Revalide a qualidade depois de migrar**: mesmo prompt, modelo diferente,
resultado diferente.

**Mantenha o model id parametrizado** (env var ou settings), nunca literal espalhado pelo
código — a linha 3.x já acumula `3-flash`, `3.5-flash`, `3.6-flash` e `3.7-flash`, e vai
continuar.

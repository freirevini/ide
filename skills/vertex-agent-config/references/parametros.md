# Parâmetros de geração — geração 3.x e 4

Verificado em 2026-10-23. Fatos por modelo (níveis, defaults, o que é ignorado) vivem em
`modelos.md`; aqui está o comportamento de cada parâmetro e como usá-lo.

## thinking_level

Valores possíveis: `MINIMAL`, `LOW`, `MEDIUM`, `HIGH`. **Quais existem e qual é o default
depende do modelo** (tabela em `modelos.md`):

| Modelo | Níveis | Default |
|---|---|---|
| `gemini-4-argon` | LOW, MEDIUM, HIGH | MEDIUM |
| `gemini-3.8-flash`, `gemini-3.7-flash` | LOW, MEDIUM, HIGH | MEDIUM |
| `gemini-3.6-flash`, `gemini-3.5-flash` | MINIMAL, LOW, MEDIUM, HIGH | MEDIUM |
| `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite` | MINIMAL, LOW, MEDIUM, HIGH | MINIMAL |
| `gemini-3.1-pro-preview` | LOW, MEDIUM, HIGH | HIGH |

Regras:

- **Chamada sem o parâmetro usa o default do modelo**, que é MEDIUM na maioria. "Default é
  HIGH" só vale para o 3.1 Pro preview. Saiba qual é o default antes de decidir se precisa
  escrever o parâmetro.
- **`MINIMAL`** só onde a tabela lista; em 4 Argon, 3.8, 3.7 e 3.1 Pro devolve erro. Onde
  existe, exige *thought signatures* em conversa multi-turn (`400: INVALID_ARGUMENT` sem elas).
- **`MEDIUM`** entrou com o 3.1 Pro e hoje é o default da maioria. Quando `LOW` erra e `HIGH`
  custa demais, é aqui que se resolve — antes de trocar de modelo.
- **Nunca envie `thinking_level` e `thinking_budget` na mesma request — devolve erro.**
  `thinking_budget` é a API da geração 2.5; no 4 Argon devolve HTTP 400 mesmo sozinho e **não
  é mapeado** para um nível.
- Thinking não desliga em 3.x nem em 4. `MINIMAL` "usa o mínimo de tokens possível", não zero.

**Tokens de thinking são cobrados como saída.** No `gemini-3.1-pro` isso é $12,00 por 1M —
a linha mais cara da tabela. Um `HIGH` desnecessário aparece na fatura, não na latência.
(Linha mantida da versão anterior desta skill; id atual é `gemini-3.1-pro-preview`.)

## temperature, topP, topK

| Modelo | Situação |
|---|---|
| `gemini-4-argon` | **ignorados** pelo backend; `candidate_count`, `frequency_penalty`, `presence_penalty` devolvem **HTTP 400** |
| `gemini-3.8-flash`, `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash-lite` | **ignorados** pelo backend (a página ainda lista defaults 1.0 / 0.95 / 64; não têm efeito) |
| `gemini-3.1-pro-preview` | funcionam: temperature 0.0–2.0 (default 1.0), topP 0.0–1.0 (default 0.95), topK fixo em 64 |
| `gemini-3.5-flash`, `gemini-3.1-flash-lite`, `gemini-3-flash` | a confirmar na página do modelo |
| `gemini-nano-banana-2.1` | `seed`, `temperature`, `topP`, `topK` devolvem **erro de API** |

**Hoje ignorados, amanhã 400.** O guia oficial de migração manda **remover** `temperature`,
`top_p`, `top_k`, `candidate_count`, `frequency_penalty`, `presence_penalty` e turnos de modelo
pré-preenchidos no histórico. No 4 Argon três deles já devolvem 400. Enviar parâmetro ignorado
"não dá erro" é o estado de hoje, não garantia: remova, não comente.

Pior que falhar: o time acredita ter controlado a variabilidade e não controlou.
`scripts/inspecionar_agentes.py` marca `temperature`/`top_p`/`top_k` junto de modelo que os
ignora como pendência de migração.

Onde os parâmetros funcionam (3.1 Pro preview): mantenha `temperature` em **1.0**, o ponto de
calibração. Baixar pode causar loops e degradar o raciocínio. `topP` só depois da temperature
e para baixo; mexer nos dois ao mesmo tempo impede saber qual causou a mudança. Geração
infinita: **aumentar** a temperature para `>= 0.1` pode ajudar — só onde o parâmetro não é
ignorado.

## Determinismo

A orientação oficial para os modelos que ignoram amostragem: **controle a profundidade com
`thinking_level` e o formato com `response_schema`** (ou `json_schema`). É o primeiro passo.

O segundo é a *system instruction*. Parâmetro estreitava a amostragem; instrução precisa
**descrever o comportamento**. O que colocar, em ordem de efeito:

1. **Formato exato da saída** — junto com `responseSchema`, não no lugar dele.
2. **Critério de decisão explícito e ordenado.** "Se A e B, então X; se só A, então Y."
   Critério implícito é onde a variabilidade entra.
3. **O que fazer em caso de ambiguidade** — nomeie o valor de saída para o caso
   indeterminado. Sem isso o modelo escolhe, e escolhe diferente a cada vez.
4. **O que NÃO inferir** — "não deduza informação ausente; devolva campo nulo com o motivo".
   Cobre a maior fonte de variação em extração.

Um agente configurado assim varia menos entre execuções do que um com temperature baixa, e
continua raciocinando, que é o que a temperature baixa quebrava.

## seed

Existe em `GenerationConfig`. Reprodutibilidade confirmada só onde a amostragem funciona
(`gemini-3.1-pro-preview`). Em modelo que ignora amostragem (4 Argon, 3.8 Flash) o efeito de
`seed` **não está documentado**: trate como "a confirmar". `gemini-nano-banana-2.1` rejeita
`seed` com erro.

Reprodutibilidade auditável que não depende de `seed`: registre exatamente o que foi enviado
(entrada, system instruction, `thinking_level`, `response_schema`) mais o model id e a data.
Reproduzir exige isso de qualquer forma; `seed` só reduz a variação da amostragem.

## maxOutputTokens e a armadilha do thinking

**Tokens de thinking contam contra `maxOutputTokens`.** Dimensione como thinking + resposta,
com folga; meça o consumo real de thinking antes de escolher o número.

- `gemini-3.8-flash` e `gemini-3.1-pro-preview`: saída máxima 65.536. Default de 8.192 citado
  em versões anteriores desta skill não consta na página atual; não presuma.
- `gemini-4-argon`: janela **unificada** — ver seção abaixo.

Com `responseSchema`, estourar o limite devolve:

```
response.text   -> None
response.parsed -> None
finishReason    -> MAX_TOKENS
```

**Sem exceção lançada.** Código que faz `json.loads(response.text)` quebra a jusante com
`TypeError`, e o log registra "erro de parsing" — diagnóstico que manda o investigador para o
schema em vez do orçamento de saída.

```python
resp = client.models.generate_content(...)

cand = resp.candidates[0] if resp.candidates else None
if cand is None or cand.finish_reason == "MAX_TOKENS":
    raise OrcamentoDeSaidaEstourado(
        f"finish_reason={getattr(cand, 'finish_reason', None)} "
        f"max_output={config.max_output_tokens}"
    )

resultado = resp.parsed
```

## Gemini 4 Argon — regras próprias

- **Janela unificada de 1.048.576 tokens**: entrada + thinking + chamadas de função + resposta.
  `max_output_tokens` pode ir até 1.048.576 **menos a entrada**; acima disso, HTTP 400.
  Documento grande reduz o espaço de resposta; dimensione os dois juntos.
- **Default por request**: 65.536 tokens (thinking + resposta); **32.768** em HTTP direto
  sem streaming. Estourar devolve `MAX_TOKENS` como acima.
- **Long decode**: saída acima do default, até a janela, só em `v1beta1` (não em `v1`, não na
  Interactions API). O SDK continua automaticamente (`automatic_continuation=False` desliga);
  loop manual usa `continuation_token`. **Não use** em classificação, chat, requisições
  sensíveis a latência ou muitos turnos curtos de agente.
- **`MINIMAL` e `thinking_budget` → HTTP 400.** Níveis: LOW, MEDIUM (default), HIGH.
- **Amostragem ignorada**; `candidate_count`, `frequency_penalty`, `presence_penalty` → 400.
- **Cache só implícito**, durável por padrão; **sem cache explícito** (remova chamadas de
  `CachedContent`). Mínimo: 4.096 tokens na página do modelo, 6.144 no guia do desenvolvedor —
  divergência registrada; use 6.144 como piso seguro.
- Não suporta tuning, RAG Engine, Live API nem quota fixa.
- Migração de 3.x, pelo guia oficial: trocar o id; atualizar o SDK; orçar a janela unificada;
  trocar `thinking_budget`/`MINIMAL` por `thinking_level`; remover cache explícito e colocar o
  conteúdo estático primeiro; remover amostragem, penalties, `candidate_count` e turnos de
  modelo pré-preenchidos.

## Cache de contexto

Regra estrutural: **estável primeiro, variável depois**. Vale para cache explícito e implícito.

```
system instruction ......... estável  ─┐
regras / parâmetros ........ estável   ├─ prefixo candidato a cache
exemplos ................... estável  ─┘
──────────────────────────────
metadados do item .......... variável
conteúdo do item ........... variável
```

O que quebra o cache sem parecer que quebra: timestamp ou id de sessão no prefixo, regras
concatenadas em ordem não determinística (ordene antes de serializar), `json.dumps` sem
`sort_keys=True`.

Mínimos oficiais (Vertex, 2026-10-23):

| Modelos | Mínimo de tokens |
|---|---|
| Gemini 3 "com exceções" e Gemini 4 (explícito e implícito) | 4.096 |
| 3 Flash preview, 3.1 Pro preview, 3.7 Flash, 3.8 Flash (implícito) | 6.144 |
| Gemini 4 Argon (só implícito) | 4.096 na página do modelo, 6.144 no guia |

Suporte: explícito em 3.8, 3.7, 3.6, 3.5, 3.5-lite, 3.1-lite e 3.1 Pro preview; implícito em
toda a linha; implícito **durável** em 4 Argon e 3.8 Flash. 4 Argon **não** tem explícito.
TTL default do explícito: 60 minutos (mínimo 1, sem máximo); prefixo implícito vive até 24 h.

Preços de cache do `gemini-3.1-pro`: escrita **$2,00 / 1M**, leitura **$0,50 / 1M**
(75% de desconto), armazenamento **$4,50 / 1M por hora**. (Linha mantida da versão anterior
desta skill, não reverificada; confira na tabela oficial.)

Feliz coincidência: essa ordem é a mesma que isola conteúdo não confiável do prompt do
sistema. Cache e segurança pedem o mesmo layout.

## responseSchema

Nos perfis de avaliação e extração, o schema deve exigir **evidência**, não só o resultado.
Campo booleano não é conferível; campo que obriga a citar o trecho de origem permite validar a
saída contra o documento.

Configuração de qualidade que serve também à segurança.

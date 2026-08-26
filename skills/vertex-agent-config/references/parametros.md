# Parâmetros de geração — geração 3.x

## temperature, topP, topK

| Modelo | Situação |
|---|---|
| `gemini-3.7-flash` | **depreciados e ignorados** |
| `gemini-3.6-flash` | **depreciados e ignorados** |
| `gemini-3.5-flash-lite` | **depreciados e ignorados** |
| demais 3.x | funcionam — mantenha `temperature` em **1.0** |

Faixa da temperature na Vertex: **0.0 a 2.0**, default **1.0**, e **1.0 é o valor inicial
recomendado**. O default não é meio-termo preguiçoso: é o ponto em que o modelo foi
calibrado.

**Baixar a temperature na geração 3.x pode causar loops e degradar o raciocínio.** Não é
um ajuste conservador — é mudança de regime. Se o objetivo era reduzir variabilidade, o
caminho é *system instruction*, não parâmetro.

Onde os parâmetros são ignorados, enviá-los **não dá erro** — simplesmente não faz nada.
Pior que falhar: o time acredita ter controlado a variabilidade e não controlou.

`topP` default **0.95**. Onde ainda funciona, ajuste **depois** da temperature e **para
baixo**. Mexer nos dois ao mesmo tempo impede saber qual causou a mudança.

Se o modelo entrar em geração infinita, **aumentar** a temperature para **>= 0.1** pode
ajudar — contraintuitivo, e por isso a última coisa que se tenta. Só onde o parâmetro
não é ignorado.

## Determinismo por system instruction

Na geração 3.x o controle de variabilidade migrou para a *system instruction*. Não é o
mesmo trabalho com outro nome: parâmetro estreitava a amostragem, instrução precisa
**descrever o comportamento**.

O que colocar, em ordem de efeito:

1. **Formato exato da saída** — junto com `responseSchema`, não no lugar dele.
2. **Critério de decisão explícito e ordenado.** "Se A e B, então X; se só A, então Y."
   Critério implícito é onde a variabilidade entra.
3. **O que fazer em caso de ambiguidade** — nomeie o valor de saída para o caso
   indeterminado. Sem isso o modelo escolhe, e escolhe diferente a cada vez.
4. **O que NÃO inferir** — "não deduza informação ausente; devolva campo nulo com o
   motivo". Cobre a maior fonte de variação em extração.

Um agente configurado assim varia menos entre execuções do que um com temperature baixa —
e continua raciocinando, que é o que a temperature baixa quebrava.

## seed

Existe em `GenerationConfig`. **Use para reprodutibilidade em avaliação auditável**: com o
mesmo `seed` e a mesma entrada, a saída é reproduzível — permite reexecutar um caso
contestado e obter o mesmo resultado.

Recomendado nos perfis `extracao`, `alto-risco` e em qualquer avaliação que possa ser
questionada depois. Não substitui registrar a entrada: reproduzir exige ter guardado
exatamente o que foi enviado, mais o model id.

## thinking_level

Valores: **`MINIMAL`**, **`LOW`**, **`MEDIUM`**, **`HIGH`**. Default **`HIGH`**.

- **`MEDIUM` entrou na linha 3.1** como degrau intermediário. Quando `LOW` erra e `HIGH`
  custa demais, é aqui que se resolve — antes de trocar de modelo.
- **Pro não aceita `MINIMAL`.**
- **`MINIMAL` exige *thought signatures*.**

**Nunca envie `thinking_level` e `thinking_budget` na mesma request — devolve erro.**
`thinking_budget` é a API da geração 2.5.

**Tokens de thinking são cobrados como saída.** No `gemini-3.1-pro` isso é $12,00 por 1M —
a linha mais cara da tabela. Um `HIGH` desnecessário aparece na fatura, não na latência.

## maxOutputTokens e a armadilha do thinking

**Tokens de thinking contam contra `maxOutputTokens`.**

No `gemini-3.1-pro` o default é **8.192** — baixo para tarefa com `thinking_level=HIGH`.
Dimensione explicitamente.

Com `responseSchema`, estourar o limite devolve:

```
response.text   -> None
response.parsed -> None
finishReason    -> MAX_TOKENS
```

**Sem exceção lançada.** Código que faz `json.loads(response.text)` quebra a jusante com
`TypeError`, e o log registra "erro de parsing" — diagnóstico que manda o investigador
para o schema em vez do orçamento de saída.

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

**Dimensione `maxOutputTokens` como thinking + resposta**, com folga. Meça o consumo real
de thinking antes de escolher o número.

## Cache de contexto

Regra estrutural: **estável primeiro, variável depois**.

```
system instruction ......... estável  ─┐
regras / parâmetros ........ estável   ├─ prefixo candidato a cache
exemplos ................... estável  ─┘
──────────────────────────────
metadados do item .......... variável
conteúdo do item ........... variável
```

Preços de cache do `gemini-3.1-pro`: escrita **$2,00 / 1M**, leitura **$0,50 / 1M**
(75% de desconto), armazenamento **$4,50 / 1M por hora**.

**Mínimo de tokens: fontes divergem** — uma indica **4.096** para a linha 3.x e outra
**32.768** para cache explícito no `gemini-3.1-pro`. **Confirme na documentação oficial da
Vertex antes de dimensionar.** Esta skill não escolhe entre as duas.

O que quebra o cache sem parecer que quebra: timestamp ou id de sessão no prefixo, regras
concatenadas em ordem não determinística (ordene antes de serializar), `json.dumps` sem
`sort_keys=True`.

Feliz coincidência: essa ordem é a mesma que isola conteúdo não confiável do prompt do
sistema. Cache e segurança pedem o mesmo layout.

## responseSchema

Nos perfis de avaliação e extração, o schema deve exigir **evidência**, não só o
resultado. Campo booleano não é conferível; campo que obriga a citar o trecho de origem
permite validar a saída contra o documento.

Configuração de qualidade que serve também à segurança.

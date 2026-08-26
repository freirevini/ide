# Parâmetros de geração

## temperature

| Item | Valor |
|---|---|
| Faixa na Vertex | **0.0 a 2.0** |
| Default | **1.0** |
| Valor inicial recomendado | **1.0** |

**Comece em 1.0 e só mexa com motivo medido.** O default não é um meio-termo preguiçoso;
é o ponto em que o modelo foi calibrado.

### Linha 3.x — mantenha 1.0

Baixar temperature na linha 3.x **pode causar loops e degradar o raciocínio**. Não é um
ajuste conservador: é uma mudança de regime.

Em **`gemini-3.5-flash-lite`, `gemini-3.6-flash` e `gemini-3.7-flash`**, `temperature`,
`topK` e `topP` são **depreciados e ignorados**. Enviá-los não dá erro — simplesmente não
faz nada, o que é pior, porque o time acredita ter controlado a variabilidade.

**Determinismo nesses modelos se obtém por *system instruction***: descrever o formato,
o critério e o que fazer em caso de ambiguidade. Não por parâmetro.

### Linha 2.5 — aqui é alavanca

`temperature` funciona normalmente. Ainda assim comece em `1.0` e ajuste com evidência,
não com intuição.

### Geração infinita

Se o modelo entrar em geração infinita, **aumentar** a temperature para **>= 0.1** pode
ajudar. Contraintuitivo, e por isso costuma ser a última coisa que se tenta. Só se aplica
onde o parâmetro não é ignorado.

## topP

Default **0.95**. Ajuste **depois** da temperature, e **para baixo**. Mexer nos dois ao
mesmo tempo torna impossível saber qual causou a mudança.

Ignorado nos flash 3.5-lite / 3.6 / 3.7, junto com `topK`.

## seed

Existe em `GenerationConfig`. **Use para reprodutibilidade em avaliação auditável**: com
o mesmo `seed` e a mesma entrada, a saída é reproduzível — o que permite reexecutar um
caso contestado e obter o mesmo resultado.

Recomendado nos perfis `extracao`, `alto-risco` e em qualquer avaliação que possa ser
questionada depois. Não substitui registro da entrada: reproduzir exige ter guardado
exatamente o que foi enviado.

## thinking

### Linha 2.5 — `thinking_budget`

| Modelo | Faixa | Desliga? |
|---|---|---|
| `gemini-2.5-pro` | **128 – 32768** | **não** |
| `gemini-2.5-flash` | **0 – 24576** | sim (`0`) |
| `gemini-2.5-flash-lite` | **512 – 24576** | não pensa por padrão |

Se o plano era "desligar o thinking do Pro", não existe esse plano — a única forma é
trocar de modelo.

### Linha 3.x — `thinking_level`

Valores: **`MINIMAL`**, **`LOW`**, **`HIGH`**. Default **`HIGH`**.

- **Pro da linha 3.x não aceita `MINIMAL`.**
- **`MINIMAL` exige *thought signatures*.**

### Regra que vale para as duas

**Nunca envie `thinking_budget` e `thinking_level` na mesma request — erro 400.** São a
API antiga e a nova.

## maxOutputTokens e a armadilha do thinking

**Tokens de thinking contam contra `maxOutputTokens`.**

Com `responseSchema`, estourar o limite devolve:

```
response.text   -> None
response.parsed -> None
finishReason    -> MAX_TOKENS
```

**Sem exceção lançada.** Código que faz `json.loads(response.text)` quebra a jusante com
`TypeError`, e o log registra "erro de parsing" — diagnóstico que manda o investigador
para o schema em vez do orçamento de saída.

Padrão correto:

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
de thinking antes de escolher o número, em vez de estimar.

## responseSchema

Nos perfis de avaliação e extração, o schema deve exigir **evidência**, não só o
resultado. Um campo booleano não é conferível; um campo que obriga a citar o trecho de
origem permite que o código valide a saída contra o documento.

Isso é configuração de qualidade, não de segurança — mas serve às duas.

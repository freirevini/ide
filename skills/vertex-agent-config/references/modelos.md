# Modelos e ciclo de vida

## Linha 3.x (preferencial)

Modelos flash confirmados nesta skill: **`gemini-3.5-flash-lite`**, **`gemini-3.6-flash`**
e **`gemini-3.7-flash`** — sendo o **3.7-flash o mais recente**.

Existe Pro na linha 3.x (o próprio comportamento de `thinking_level` documenta que "Pro
não aceita `MINIMAL`"). **Confirme o id exato liberado no seu deploy** antes de fixá-lo
em configuração — esta skill não presume o identificador.

### Controle de raciocínio

`thinking_level`: **`MINIMAL`**, **`LOW`**, **`HIGH`**. Default **`HIGH`**.

- Pro 3.x **não aceita `MINIMAL`**.
- `MINIMAL` **exige *thought signatures***.

### Parâmetros de amostragem

Mantenha `temperature` em **1.0**. Baixá-la pode causar loops e degradar raciocínio.

Em `gemini-3.5-flash-lite`, `gemini-3.6-flash` e `gemini-3.7-flash`, `temperature`,
`topK` e `topP` são **depreciados e ignorados** — determinismo se obtém por *system
instruction*.

## Linha 2.5 (legado)

| Modelo | Thinking | Desliga? |
|---|---|---|
| `gemini-2.5-pro` | **128 – 32768** | **não** |
| `gemini-2.5-flash` | **0 – 24576** | sim (`0`) |
| `gemini-2.5-flash-lite` | **512 – 24576** | não pensa por padrão |

Aqui `temperature` é alavanca real. Comece em `1.0`.

Use `thinking_budget`, **nunca** junto de `thinking_level` (erro 400).

## Ciclo de vida

**`gemini-2.5-pro`, `gemini-2.5-flash` e `gemini-2.5-flash-lite`: aposentadoria anunciada
para não antes de 2026-10-16.** A página de lifecycle da Vertex mostra **2026-10-20**.

### O que fazer com isso

1. **Mantenha o model id parametrizado** — env var ou settings, nunca literal espalhado
   pelo código. Um projeto com o id em sete arquivos migra em sete lugares, e esquece um.
2. **Registre a data em comentário** junto ao parâmetro, para que a migração apareça na
   leitura do código.
3. **Trate a migração como mudança de configuração, não de código** — se o id está
   parametrizado, migrar é trocar um valor e revalidar a qualidade.

### Ao migrar 2.5 → 3.x

Não é troca de string. Muda a API de raciocínio (`thinking_budget` → `thinking_level`) e,
nos flash recentes, `temperature`/`topP`/`topK` deixam de ter efeito. Configuração que
dependia de `temperature` baixa precisa ser reescrita como *system instruction*.

Revalide a qualidade depois de migrar: mesmo prompt, modelo diferente, resultado
diferente.

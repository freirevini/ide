# Context caching no Vertex AI

Maior ganho de custo do pipeline com risco de precisão **zero**: o modelo recebe
exatamente o mesmo prefixo, cacheado ou não. Comece por aqui.

## Números que decidem

| Item | Valor |
|---|---|
| Mínimo de tokens para cache — linha 3.x | **4.096** (fonte alternativa cita **32.768** para cache explícito no `gemini-3.1-pro` — **confirme na doc oficial**) |
| Máximo por blob/texto | 10 MB |
| TTL padrão | 60 min |
| Leitura de cache — `gemini-3.1-pro` | **$0,50 / 1M** (75% de desconto sobre $2,00) |
| Escrita de cache — `gemini-3.1-pro` | **$2,00 / 1M** |
| Armazenamento — `gemini-3.1-pro` | **$4,50 / 1M por hora** |

O mínimo é o portão: um prefixo abaixo dele **não cacheia**, nem implícito nem
explícito, e nenhum ajuste muda isso. Se o prefixo estável estiver abaixo do mínimo,
a decisão é entre trazer mais conteúdo estável para o prefixo (as regras de compliance
do RAG são candidatas naturais) ou aceitar que esta alavanca não se aplica.

## Implícito vs explícito

**Implícito** é o comportamento padrão — não requer chamada de API. Acerta quando:
- o prefixo é **byte a byte idêntico** entre requests, e
- as requests estão **próximas no tempo**.

Não há garantia contratual de acerto. É grátis de implementar e frágil de manter.

**Explícito** (`CachedContent`) dá controle: você cria o cache, recebe um handle e o
referencia nas requests. Custa armazenamento pelo TTL e garante o acerto. Vale quando
o mesmo conjunto de regras é usado por muitas peças em sequência — o caso deste
pipeline, se as regras parametrizadas mudam raramente.

Regra prática: **comece pelo implícito** (só reordenar o request), meça o acerto, e
migre para explícito só se o acerto medido for baixo e o volume justificar.

## Como montar o prefixo estável

A ordem do conteúdo é o trabalho todo. Cache é **prefixo**: tudo que varia precisa vir
depois de tudo que é estável.

```
[ system instruction ................ estável ]  ─┐
[ regras de compliance do RAG ....... estável ]   ├─ candidato a cache
[ exemplos few-shot ................. estável ]  ─┘
[ metadados da peça ................. variável ]
[ conteúdo da peça de marketing ..... variável ]
```

Isso coincide com a ordem exigida pela defesa contra injeção de prompt
(ver `prompts.md`): conteúdo não confiável por último. As duas necessidades apontam
para o mesmo layout — não há trade-off aqui.

## O que quebra o acerto silenciosamente

Todos estes produzem prefixo diferente sem parecer diferentes:

- timestamp, `request_id`, `session_id` ou nome de usuário embutidos na system instruction;
- regras vindas do RAG concatenadas em **ordem não determinística** (resultado de
  `set`, ordem de retorno do índice, `dict` montado por iteração concorrente) —
  **ordene explicitamente** antes de serializar;
- `json.dumps` sem `sort_keys=True` sobre dicionário montado dinamicamente;
- espaço em branco / quebra de linha variável em template de f-string;
- número de regras recuperadas variando por peça, quando o `top_k` do RAG é dinâmico.

Se as regras recuperadas variam por peça, elas **não pertencem ao prefixo cacheável**.
Nesse caso, cacheie apenas system instruction + exemplos, e injete as regras variáveis
depois — ou fixe um conjunto-base de regras sempre presente e trate o restante como
complemento variável.

## Medir o acerto

O acerto vem em `usageMetadata` da resposta:

- `cachedContentTokenCount` — tokens que bateram no cache;
- `promptTokenCount` — total de entrada.

Taxa de acerto = `cachedContentTokenCount / promptTokenCount`. Registre isso por
request desde a primeira medição (`scripts/medir_latencia.py` já tem o campo). Sem
esse número, "ativamos caching" é uma afirmação sem evidência — e, com prefixo
instável, o acerto pode ser 0% enquanto o código parece correto.

## Depois de mexer em prompt

Qualquer edição em system instruction, exemplos ou formato de regra **invalida o
cache**. Após alterar prompt, reconfira a taxa de acerto antes de concluir que a
mudança foi neutra em custo.

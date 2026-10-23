# Ciclos — ler a cadeia de handoffs

Uma task passa por várias IAs/IDEs várias vezes. Cada passagem é um **ciclo** gravado por
`context-out`. Ler só o último é o erro mais caro: decisão do ciclo 1 e correção recusada no ciclo 4
mudam o trabalho de agora tanto quanto o ciclo mais recente.

## Anatomia da entrada de ciclo

```markdown
### Ciclo 4 · 2026-09-09 · antigravity / gemini-3-pro · correção
chat: agy-sess-8f21c04 · Agent Manager > "oauth callback fix"
doc: .doc/auth-oauth-google.md

| Arquivo | Mudança | Por quê |
...
Correções aplicadas: C3.1, C3.2. Recusada: C3.4.

#### Verificação
#### Para o revisor validar
```

| Campo | Como usar |
|---|---|
| número + data | posição na cadeia; o que veio depois pode ter revertido o que veio antes |
| ferramenta / modelo | calibra a leitura: ciclo de planejamento tende a decisão densa e verificação rasa; de implementação, o inverso |
| ação | `planejamento`, `implementação`, `revisão`, `correção`, `teste`, `refatoração` |
| `chat:` | conversa de origem daquela etapa — para quando o resumo não bastar |
| `doc:` | caminho do próprio documento; confirma vínculo quando o conteúdo foi colado em outro chat |
| `#### Verificação` | o que foi **de fato** executado. "não testado" ali é risco real |
| `#### Para o revisor validar` | escopo da revisão seguinte, incluindo o que **não** precisa ser revisado de novo |

## Papéis e o que executar

`proximo_papel` no frontmatter diz o que a cadeia espera de você agora.

| Papel | Fila |
|---|---|
| `corrigir` | itens `C<n>.<n>` `aberta`/`reaberta`, por severidade |
| `revisar` | escopo de `#### Para o revisor validar` do último ciclo + conferir se as correções aplicadas resolveram |
| `implementar` | pendências gerais `[implementar]` |
| `planejar` / `testar` | pendências do papel |
| `nenhum` | task fechada; confirme com o usuário antes de abrir trabalho novo |

## Itens de correção

```markdown
- [ ] **C3.1** `api/auth/callback.ts:42-51` · severidade: alta · status: aberta
  - **Problema**: ...
  - **Trecho**: ...
  - **Correção**: ...
  - **Aceite**: ...
  - **Origem**: ciclo 3 · revisão · cursor / composer-2.5
```

- O ID é estável para sempre. Reporte por ele — a rastreabilidade da cadeia depende disso.
- **Correção é instrução, não sugestão.** Arquivo, trecho, correção e aceite já estão prontos:
  aplique como está, sem reinterpretar. Ausência de detalhe é exceção, não o normal.
- Discordância técnica de um item: **não ignore em silêncio**. Diga ao usuário o motivo e proponha
  recusar — a recusa fica registrada no próximo ciclo com o motivo, e o revisor seguinte vê.
- Status manda:

| Status | O que fazer |
|---|---|
| `aberta` | aplicar |
| `reaberta no ciclo N` | aplicar; a revisão constatou que a tentativa anterior não resolveu — leia o que faltou |
| `aplicada no ciclo N` | não refazer. Se você é o revisor, confira se resolveu mesmo |
| `recusada (motivo)` | não reaplicar. Reabra só se o usuário pedir ou se o motivo não se sustentar mais |

Na revisão: problema que já tem ID vira **reabertura daquele ID**, não achado novo. Achado novo com
ID novo para o mesmo problema faz a cadeia perder o rastro e entrar em loop.

## Rastreabilidade — quando abrir o chat de origem

O documento é resumo. O `chat:` de cada ciclo aponta para a conversa completa daquela etapa.
Recorra a ele quando, e só quando:

- o motivo de uma decisão não está no documento e muda o que você vai fazer;
- um ciclo antigo foi compactado em uma linha e você precisa do detalhe;
- documento e código divergem e nem `git log` nem as decisões explicam.

Como reabrir, por ferramenta:

| Ferramenta | Reabrir |
|---|---|
| Claude Code | `claude --resume <id>`; transcrição em `~/.claude/projects/<projeto>/<id>.jsonl` |
| Cursor | link de Share, se gravado; senão procurar pelo título + data na lista de chats do workspace |
| Antigravity | Agent Manager, pelo nome/id da sessão; artefatos daquela sessão em `artefatos:` |
| Gemini CLI / Copilot | pelo id, se gravado; senão título + data |

`chat: nao-disponivel · <ferramenta> · "<título>" · <data>` significa que o identificador não existia
— use ferramenta, título e data para achar na mão. **Nunca afirme ter lido uma conversa que você não
abriu**, e não invente id ausente.

## Documento compactado

A partir de ~6 ciclos, `context-out` compacta ciclos antigos em uma linha cada, preservando
decisões, correções abertas, pendências e todas as linhas `chat:`. Linha compactada é resumo por
construção: o detalhe está no chat citado. Trate a ausência de detalhe como "está em outro lugar",
não como "não aconteceu".

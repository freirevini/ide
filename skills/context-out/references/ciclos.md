# Ciclos — handoff em cadeia

Uma task atravessa várias IAs/IDEs várias vezes: planejada no Cursor → implementada no
Antigravity → revisada no Cursor → corrigida no Antigravity → revisada de novo. Cada passagem é
um **ciclo**. Cada execução de `context-out` grava **um ciclo novo**, nunca sobrescreve os anteriores.

## Numeração

Inteiro monotônico começando em 1. Nunca reutilizado, nunca renumerado — IDs de correção e
referências de decisão apontam para o número do ciclo e precisam continuar válidos para sempre.

Antes de gravar, releia o documento: se `ciclo` no frontmatter já é maior que o seu (outro agente
gravou em paralelo), pegue o próximo livre e funda o trabalho dele antes.

## Tipos de ação

| Ação | Grava | Entrega para |
|---|---|---|
| `planejamento` | objetivo, decisões, plano em pendências | `implementar` |
| `implementação` | arquivos alterados, verificação, pontos a validar | `revisar` |
| `revisão` | achados, correções estruturadas, o que foi aprovado | `corrigir` (ou `nenhum` se aprovado) |
| `correção` | correções aplicadas por ID, o que foi recusado e por quê | `revisar` (re-revisão) |
| `teste` | o que foi executado, resultado, falhas reproduzíveis | conforme o resultado |
| `refatoração` | o que mudou de forma, invariante preservada | `revisar` |
| `checkpoint` | feito até aqui, tentado e falhou, próximo passo exato; bastão fica com quem grava | o mesmo papel (ou quem assumir, se a sessão cair) |

`proximo_papel` do frontmatter: `planejar`, `implementar`, `revisar`, `corrigir`, `testar`, `nenhum`.

Toda entrada de ciclo, de qualquer tipo, leva a linha `Tentado e falhou:` (ou `nenhum`), logo
depois da tabela de arquivos: abordagem, por que não serviu, o que o experimento provou.

## Entrada de ciclo em `## Mudanças realizadas`

Mais recente no topo. Formato fixo:

```markdown
### Ciclo 4 · 2026-09-09 · antigravity / gemini-3-pro · correção
chat: agy-sess-8f21c04 · Agent Manager > "oauth callback fix" · retomar pelo Agent Manager
doc: .doc/auth-oauth-google.md

| Arquivo | Mudança | Por quê |
|---|---|---|
| `api/auth/callback.ts` | trocado `res.json` por cookie httpOnly | correção C3.1 |

Correções aplicadas: C3.1, C3.2. Recusada: C3.4 (motivo em Pendências).
Tentado e falhou: `Set-Cookie` em middleware global — quebrava rotas públicas; voltou ao handler.

#### Verificação
- `npm test -- auth` → 18 passed, 0 failed.
- Fluxo end-to-end: não testado (falta client_id de dev).

#### Para o revisor validar
- C3.1: cookie sai com `httpOnly`, `SameSite=Lax`, `Secure` em produção.
- C3.2: `error=access_denied` retorna 400 com mensagem tratada, não 500.
- **Não precisa revisar de novo**: `src/auth/oauth.ts` — aprovado no ciclo 3 e não tocado depois.
```

`#### Para o revisor validar` é **obrigatório** quando `proximo_papel` é `revisar`. Sem ele o
revisor re-revisa tudo e o ciclo se perde em ruído.

## Ciclo de revisão

Ao gravar um ciclo `revisão`, o documento precisa conter, ao fim:

1. **Escopo revisado** — quais arquivos e qual ciclo de implementação foram olhados.
2. **O que foi implementado** — já está nas entradas anteriores; confira que está legível sozinho
   e complete o que ficou vago, sem reescrever o histórico.
3. **Critérios validados** — o que foi checado e passou. Vira `aprovado no ciclo N` e sai da fila
   de revisão futura.
4. **Critérios não validados** — o que não deu para checar e por quê (falta credencial, ambiente,
   dado). Vira pendência de teste, não achado.
5. **Achados** — cada um vira item de correção estruturado (abaixo). Achado sem item de correção
   é feedback vago; não grave assim.
6. **Observações sem ação** — o que não vira correção mas o próximo deve saber. Vai para
   `## Contexto adicional`.

## Itens de correção

Ficam em `## Pendências`, sob `### Correções do ciclo N (revisão · <ferramenta / modelo>)`.
Formato fixo — é o que permite aplicar sem reinterpretar:

```markdown
- [ ] **C3.1** `api/auth/callback.ts:42-51` · severidade: alta · status: aberta
  - **Problema**: token devolvido no corpo da resposta; qualquer XSS lê o token.
  - **Trecho**: `res.json({ token })`
  - **Correção**: setar cookie httpOnly (`Set-Cookie: session=...; HttpOnly; SameSite=Lax`) e
    responder `204`. Segue D3.
  - **Aceite**: `npm test -- auth/callback` verde e resposta sem `token` no body.
  - **Origem**: ciclo 3 · revisão · cursor / composer-2.5
```

Regras:

- **ID** `C<ciclo-da-revisão>.<n>`, estável para sempre. É por ele que o ciclo de correção reporta.
- **Severidade**: `alta` (quebra, risco de segurança, dado errado) · `média` (comportamento errado
  em caso não central) · `baixa` (clareza, consistência). Ordene por severidade dentro do bloco.
- **Problema** descreve o que está errado e o efeito observável — nunca "melhorar", "ajustar",
  "revisar isso".
- **Correção** é acionável e específica: o que fazer, onde, seguindo qual decisão.
- **Aceite** é verificável por comando ou observação, não por opinião.
- Sem arquivo e sem linha/trecho, o item não está pronto. Complete antes de gravar.

### Ciclo de vida

| Status | Quando | Onde fica |
|---|---|---|
| `aberta` | criada pela revisão | Pendências |
| `aplicada no ciclo N` | corrigida | sai de Pendências, citada na entrada do ciclo N |
| `recusada (motivo)` | o corretor discorda ou o usuário decidiu não fazer | fica em Pendências com o motivo, até a próxima revisão fechar |
| `reaberta no ciclo N` | a re-revisão constatou que não resolveu | volta a `aberta`, com o que faltou |

Correção nunca é apagada em silêncio. Item que some sem status faz o revisor seguinte reencontrar
o mesmo problema e o ciclo entra em loop.

## Bastão de uso único e sessão cortada

`bastao:` no frontmatter diz quem segura a task agora. Uma sessão por vez:

| Momento | Valor |
|---|---|
| ciclo que entrega para outro papel (`proximo_papel` muda de mão) | `livre` |
| checkpoint no meio de um papel | `<ferramenta / modelo> · chat <id> · desde <data-hora ISO>` |
| `context-in` assume task livre | grava o próprio nome nessa linha (única escrita dele) |
| `status: concluida` | `livre` |

**Checkpoint** é para task longa: antes de passo que pode estourar cota, travar ou derrubar a
sessão (migração grande, suíte lenta, refatoração em muitos arquivos), grave um ciclo
`checkpoint` com o feito até aqui, o `Tentado e falhou:` e o próximo passo exato. Custa um
minuto; sem ele, a sessão que cai leva o estado junto.

**Sessão cortada** (cota, crash, terminal fechado) não grava ciclo. A sessão seguinte encontra
`bastao` com outro chat e o repositório adiante do documento (commits depois de `atualizado_em`,
`git status` sujo nos arquivos da task). `context-in` reconstrói o não gravado pelo git, com
confirmação do usuário; o `context-out` que vier depois grava:

```markdown
### Ciclo 6 · 2026-09-12 · claude-code / opus-5 · implementação · assumido de antigravity / gemini-3-pro
chat: <id>
doc: .doc/auth-oauth-google.md
recuperado: 3 arquivos alterados depois do ciclo 5 sem ciclo gravado (`src/auth/refresh.ts`,
`src/auth/session.ts`, `tests/auth/refresh.test.ts`); motivos desconhecidos; tratados como estado.
```

O que a sessão cortada fez é **estado**, não decisão: a mudança é fato, o motivo é desconhecido
até alguém dizer. Decisão inferida do diff vai como `suposição:`.

## Rastreabilidade da conversa de origem

Cada entrada de ciclo grava, sempre:

- `chat:` identificador do chat/sessão onde a etapa aconteceu, mais como reabrir.
- `doc:` o caminho do próprio documento (`.doc/<slug>.md`) — serve quando o conteúdo é colado em
  outro chat e perde o vínculo com o arquivo.

O mesmo par vai para o frontmatter, em `ciclos:`, que é a lista legível por máquina.

Como obter o identificador, por ferramenta:

| Ferramenta | Identificador | Como obter / reabrir |
|---|---|---|
| Claude Code | UUID da sessão | `ls -t ~/.claude/projects/*/*.jsonl \| head -1` — o nome do arquivo é o id; reabrir com `claude --resume <id>`. Se o ambiente expõe URL de sessão, grave a URL. |
| Cursor | link de compartilhamento, se houver; senão título + data do chat | Share do chat gera link. Sem link: `titulo · data · workspace`. Histórico local em `~/Library/Application Support/Cursor/User/workspaceStorage/<hash>/state.vscdb` (macOS). |
| Antigravity | id ou nome da sessão no Agent Manager | Nome exibido no Agent Manager + data; cite também os artefatos da sessão em `artefatos:`. |
| Gemini CLI / Copilot | id de sessão se exposto; senão título + data | Grave o que a ferramenta mostrar. |

**Nunca invente identificador.** Não conseguiu obter:

```
chat: nao-disponivel · cursor · "OAuth callback" · 2026-09-09 · workspace lab/ide
```

Título + ferramenta + data já permitem achar a conversa na mão. ID inventado manda a IA seguinte
procurar o que não existe.

## Compactação (documento longo)

A partir de ~6 ciclos ou ~400 linhas, compacte **só** entradas de ciclo antigas:

- Ciclos anteriores aos 3 últimos viram uma linha cada:
  `### Ciclo 2 · 2026-09-07 · cursor / composer-2.5 · implementação — 4 arquivos, ver D2/D3, correções C2.1–C2.3 aplicadas no ciclo 3. chat: <id>`
- **Nunca compacte**: `## Decisões técnicas`, correções abertas ou recusadas, `## Pendências`,
  `## Contexto adicional`, e as linhas `chat:` de nenhum ciclo.
- Registre a compactação: `compactado no ciclo N — histórico detalhado dos ciclos 1–3 nos chats
  citados`.

Rastreabilidade é o que torna a compactação segura: o resumo perde detalhe, o `chat:` devolve.

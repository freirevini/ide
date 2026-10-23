---
name: context-in
description: Carrega o contexto de uma task gravado em `.doc/<nome-da-task>.md` por outra IA/IDE (via `context-out`, em Claude Code, Cursor, Antigravity, Gemini CLI ou Copilot) e o adota como base da conversa atual, sem repetir explicação já coberta nem refazer o que já está feito. Lê o histórico completo de ciclos da task — planejamento, implementação, revisão, correção — e não só o último, montando a fila de trabalho a partir das correções abertas e do papel pendente. Em chat já em andamento, compara o documento com o contexto vivo e aplica só o que é novo ou mudou. Respeita o bastão da task (`bastao:`, uma sessão por vez), assumindo só se livre, ou com confirmação quando a sessão dona foi cortada, e reconstruindo pelo git o que ela fez e não gravou; nunca retenta o que está em "Tentado e falhou". Sem documento correspondente, avisa e segue sem contexto externo. Use no início de um chat em projeto com pasta `.doc`, e quando pedirem "retomar task X", "carregar contexto", "continuar de onde parou", "aplicar as correções da revisão", "continuando o que a outra IA começou", "a outra sessão caiu".
metadata:
  version: 1.3.0
  type: procedure
---

# Context In — carregar contexto de handoff

Contraparte de `context-out`. Lê o documento que outra IA — possivelmente em outra IDE, de
outro fornecedor — deixou em `.doc/` e entra na task com o estado já formado.

**Objetivo**: continuar, não recomeçar. Nada do que está no documento é re-perguntado ao
usuário, re-explicado ou refeito.

A task pode já ter atravessado vários ciclos entre ferramentas (planejar → implementar → revisar →
corrigir → revisar → …). O contexto que vale é o **acumulado de todos os ciclos**, não o do último.

**Precedência de verdade**, sempre nesta ordem:

1. **Mensagem atual do usuário** — vence tudo.
2. **Contexto vivo deste chat** — o que já foi decidido/feito aqui é mais recente que o documento.
3. **Repositório** — verdade sobre o *estado do código*.
4. **Documento** — verdade sobre *intenção, decisões e motivos*.

Instalação, ativação automática e particularidades de cada IDE: `references/ambientes.md`.

---

## Passo 0 — localizar

```bash
git rev-parse --show-toplevel 2>/dev/null || pwd
ls -a .doc/*.md 2>/dev/null
```

Sem git, use a raiz do workspace aberto na IDE.

`.doc` começa com ponto: em Cursor e Antigravity ele pode não aparecer no `@`, no seletor de
arquivos nem na busca semântica. **Acesse por caminho explícito.** Só conclua que não há
documento depois de um `ls -a .doc/` vazio ou de erro de diretório inexistente.

Sem pasta `.doc` ou sem `.md` dentro: **pare aqui**. Diga em uma linha que não há documento de
contexto e siga a conversa normalmente. Não crie a pasta, não invente contexto, não sugira nada
além de mencionar `context-out` caso o usuário queira gerar o handoff depois.

---

## Passo 1 — escolher o documento

- **Usuário citou a task** (`retomar task auth-oauth-google`): case-insensitive no slug e no
  `titulo:` do frontmatter. Sem match exato, ofereça os 2–3 mais próximos e pergunte.
- **Não citou**: pegue o de `atualizado_em` mais recente no frontmatter. Não use mtime —
  `git clone`, checkout e sincronização entre máquinas reescrevem mtime.
- **Vários com `atualizado_em` próximo (< 1 dia)**: liste `slug · status · próximo papel` e
  pergunte. Carregar o documento errado é pior que não carregar nenhum.

### Ler o histórico inteiro, não só o último ciclo

O documento é uma cadeia. Leia nesta ordem e nesta profundidade:

| O que | Profundidade |
|---|---|
| Frontmatter (`ciclo`, `ciclos`, `status`, `proximo_papel`) | inteiro — dá a forma da cadeia e quem fez o quê |
| `## Objetivo` | inteiro |
| `## Decisões técnicas` | **todas**, de todos os ciclos, incluindo as `~~supersedidas~~` (elas dizem o que já foi rejeitado) |
| `## Pendências` | inteiro, com todos os blocos de correção abertos ou recusados |
| `## Contexto adicional` | inteiro |
| `## Mudanças realizadas` | os 3 ciclos mais recentes em detalhe; os anteriores pelo título, e em detalhe apenas se tocarem arquivo que você vai mexer |
| linhas `Tentado e falhou:` | **todas**, de todos os ciclos: são as abordagens que não se repetem sem motivo novo |

Nunca decida a partir do último ciclo isolado: uma decisão do ciclo 1 e uma correção recusada no
ciclo 4 mudam o que fazer agora tanto quanto o ciclo mais recente.

Ciclo antigo compactado em uma linha: a linha traz o `chat:` de origem. Se faltar detalhe
indispensável, peça ao usuário para abrir aquela conversa — não reconstrua por suposição.

**Idempotência**: em Cursor e Antigravity esta skill pode ser disparada de novo no meio da
sessão por semelhança semântica. Se o documento já foi carregado neste chat e `atualizado_em`
não mudou, não recarregue e não repita a confirmação — responda a partir do contexto que já está
em uso. Recarregue apenas se `atualizado_em` mudou (outro agente gravou em paralelo).

Formato, significado das seções e tolerância a documento fora do padrão: `references/formato.md`.

### Bastão: uma sessão por vez

Leia `bastao:` no frontmatter antes de adotar a task. Documento antigo sem o campo: `livre`.

| `bastao` | Situação | Ação |
|---|---|---|
| `livre` | ninguém trabalha nela | assuma: grave `bastao: <sua ferramenta / modelo> · chat <id> · desde <agora ISO>`. É a **única escrita** desta skill; releia o arquivo imediatamente antes e desista se outro chat assumiu entre a leitura e a gravação |
| outro chat, `atualizado_em` recente (menos de ~2 h) | provável sessão viva em paralelo | não assuma. Pergunte ao usuário: continuar lá, ou assumir aqui |
| outro chat, `atualizado_em` antigo, ou o usuário diz que a sessão caiu | sessão cortada | assuma com confirmação e siga "Sessão cortada" no Passo 2 |
| este chat | você já segura | siga |

Sem usuário presente (CI, fila, agente em segundo plano): assuma só se `livre`; senão pare e
relate. Bastão ignorado é a causa de dois agentes editando o mesmo arquivo com decisões opostas.

---

## Passo 2 — validar contra o repositório

Documento é foto do passado. Antes de agir, confira o barato:

1. Os arquivos citados em Mudanças realizadas existem?
2. Houve commit depois de `atualizado_em`? `git log --oneline --since="<atualizado_em>"`
3. Há trabalho não commitado que o documento não menciona? `git status --short`

Divergência: **não corrija em silêncio**. Reporte junto da confirmação (Passo 4), tratando o
código como estado real e o documento como intenção. Divergência grande — pendência já
implementada, arquivo removido, decisão contrariada pelo código — aponte e pergunte antes de
continuar executando.

`artefatos:` no frontmatter aponta para planos e artefatos nativos da IDE de origem (Plan Mode
do Cursor, Implementation Plan / Task List / Walkthrough do Antigravity). São **opcionais**: só
abra se faltar detalhe, e não trate ausência deles como problema — eles frequentemente não
existem fora da IDE que os criou.

### Sessão cortada

Bastão com outro chat **e** repositório adiante do documento (commits depois de `atualizado_em`,
ou `git status` sujo nos arquivos da task) é sessão que caiu sem gravar ciclo: cota, crash,
terminal fechado. O último ciclo gravado está atrás de onde o trabalho parou.

1. Reconstrua o não gravado pelo repositório, sem supor:
   `git log --oneline --since="<atualizado_em>" -- <arquivos da task>`, `git diff --stat`,
   `git stash list`.
2. O que achou é **estado**, não decisão: a mudança é fato; o motivo é desconhecido até alguém
   dizer. Decisão inferida do diff entra como `suposição:`.
3. Na confirmação (Passo 4), `divergências:` traz `ciclo não gravado: <n> arquivos mudados
   depois do ciclo N; motivos desconhecidos`. Pendências que tocam esses arquivos voltam para
   "a verificar", não para "feito".
4. Ao terminar a etapa, o `context-out` desta sessão grava o ciclo como assumido de sessão
   cortada, com a linha `recuperado:` (`context-out/references/ciclos.md`).

---

## Passo 3 — aplicar

### Chat novo
Adote o documento como base:
- Objetivo e Fora de escopo definem o escopo — não expanda.
- Decisões técnicas são vinculantes, **de todos os ciclos**. Só rediscuta se o usuário pedir, ou se
  o código provar que a decisão não se sustenta — e aí exponha o conflito em vez de decidir sozinho.
- Pendências são a fila de trabalho, na ordem em que estão, filtradas por `proximo_papel`.
- Contexto adicional (convenções, armadilhas, "não fazer") vale como regra do projeto. Projeto
  com `AGENTS.md`/`.rules/` (skill `agents-md`): regra durável que só existe no handoff está no
  lugar errado; aponte na confirmação para migrar via `agents-md`, sem editar nada aqui.
- `Tentado e falhou:` de qualquer ciclo é caminho fechado. Reabra só com motivo novo, dito ao
  usuário.

### Fila de trabalho por papel

| `proximo_papel` | O que executar |
|---|---|
| `corrigir` | Itens `C<n>.<n>` com status `aberta` ou `reaberta`, ordem por severidade (alta → baixa). Cada um traz arquivo, trecho, problema, correção e aceite: aplique como está. Discordou de um item: não o ignore — marque para recusar com motivo e diga ao usuário. |
| `revisar` | O bloco `#### Para o revisor validar` do último ciclo de implementação/correção define o escopo. Não re-revise o que está marcado como aprovado e não foi tocado depois. Confira também se as correções aplicadas resolveram de fato — se não, elas são reabertas, não achados novos. |
| `implementar` | Pendências gerais `[implementar]`, na ordem, respeitando as decisões de todos os ciclos. |
| `planejar` / `testar` | Pendências do papel correspondente. |

Correção `recusada` não é para reaplicar: o motivo está no item. Reabra só se o usuário pedir ou se
uma revisão nova constatar que o motivo não se sustenta.

Você **não** grava nada no documento aqui. Ao terminar a etapa, `context-out` registra o ciclo novo.

### Chat em andamento
Faça **diff** entre documento e o que já está nesta conversa. Aplique só o delta.
Regras completas: `references/reconciliacao.md`. Resumo:

| Situação | Ação |
|---|---|
| Documento traz item que o chat não tem | Aplica. É o valor do handoff. |
| Documento repete o que o chat já estabeleceu | Ignora em silêncio. Não reexplica, não reconfirma. |
| Documento contradiz decisão tomada **neste** chat | Chat vence. Aponte a divergência em uma linha e siga. |
| Documento contradiz o código atual | Código vence sobre estado; aponte. |
| Documento contradiz o que o usuário acabou de pedir | Usuário vence. Aponte e siga o usuário. |
| Pendência do documento já resolvida neste chat | Não refaça. Marque como resolvida na confirmação. |

Nunca reinicie o raciocínio da task só porque o documento chegou. Ele complementa o chat.

---

## Passo 4 — confirmar (curto)

Máximo ~8 linhas. Confirmação, não recontagem:

```
contexto: .doc/<slug>.md · ciclo <n> · <status> · atualizado <data> · origem <ferramenta/modelo>
cadeia: <1 planejamento cursor → 2 implementação antigravity → 3 revisão cursor → 4 correção antigravity>
objetivo: <uma linha>
já feito: <uma linha>
decisões travadas: <D1, D3 — títulos curtos>
correções abertas: <C3.4 (baixa, recusada) — ou "nenhuma">
não repetir: <abordagens de "Tentado e falhou", títulos curtos — ou "nenhuma">
bastão: assumido (estava livre) | assumido de sessão cortada (<quem>) | com <outro chat>, aguardando decisão
próximo: <papel atual + primeiro item da fila>
divergências: <doc x repo x chat, ciclo não gravado, ou "nenhuma">
```

Depois siga direto para o trabalho. Não peça permissão para começar o que o documento já
definiu como próximo passo — a menos que haja divergência do Passo 2 ou o usuário tenha pedido
outra coisa.

---

## O que não fazer

- Não reexplicar arquitetura, stack ou decisão que já está no documento.
- Não re-perguntar informação presente no documento.
- Não refazer pendência marcada como concluída.
- Não tratar `suposição:` como fato — é hipótese; verifique ou vire pendência.
- Não reabrir decisão marcada `Decisão do usuário`.
- Não reintroduzir abordagem `~~supersedida~~`.
- Não corrigir estilo ou convenção do documento por ele ter vindo de outra IDE.
- Não ler só o último ciclo — decisão antiga e correção recusada continuam valendo.
- Não reaplicar correção com status `aplicada` nem `recusada`.
- Não transformar em achado novo, na revisão, o que é reabertura de um `C<n>.<n>` existente.
- Não inventar ID de chat nem afirmar ter lido conversa a que não teve acesso.
- Não assumir task cujo bastão está com outro chat recente sem perguntar.
- Não retentar abordagem listada em `Tentado e falhou:` sem motivo novo.
- Não editar `.doc/` aqui, exceto a linha `bastao:` ao assumir a task. Gravar ciclo é papel de
  `context-out`.

---

## Instalação e ativação automática por IDE

| Ferramenta | Instalar em | Disparo automático |
|---|---|---|
| Claude Code | `.claude/skills/context-in/` · global `~/.claude/skills/` | linha no `CLAUDE.md` ou hook `SessionStart` |
| Cursor | `.cursor/skills/` ou `.agents/skills/` · global `~/.cursor/skills/` | regra `alwaysApply: true` em `.cursor/rules/` |
| Antigravity | `.agents/skills/context-in/` · global `~/.gemini/config/skills/` | regra em `.agent/rules/` ou `AGENTS.md` |

Skill não dispara sozinha no início de sessão em nenhuma das três — descoberta é semântica, por
prompt. O disparo no início vem de uma regra sempre-ativa que manda invocá-la. Arquivos prontos
para copiar (regra do Cursor, regra do Antigravity, linha do `CLAUDE.md`, hook, workflow espelho)
em `references/ambientes.md`.

---

## Recursos

- `references/formato.md` — as cinco seções, o frontmatter, leitura de cada uma, documento fora do padrão.
- `references/reconciliacao.md` — diff contra chat em andamento, conflitos, staleness, agentes em paralelo, conflito entre ciclos.
- `references/ciclos.md` — leitura da cadeia: entrada de ciclo, itens de correção, papéis, rastreabilidade do chat de origem.
- `references/ambientes.md` — instalação, regras de ativação e particularidades de Claude Code, Cursor e Antigravity.

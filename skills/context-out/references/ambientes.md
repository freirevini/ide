# Ambientes — instalação e particularidades por IDE

O documento em `.doc/` é Markdown puro e funciona em qualquer ferramenta. O que muda por IDE
é **onde a skill mora**, **como é chamada** e **quais armadilhas locais existem**.

## Instalação

| Ferramenta | Projeto | Global | Invocação manual |
|---|---|---|---|
| Claude Code | `.claude/skills/context-out/` | `~/.claude/skills/` | `/context-out` |
| Cursor | `.cursor/skills/` ou `.agents/skills/` | `~/.cursor/skills/` ou `~/.agents/skills/` | `/` e busca pelo nome |
| Antigravity (IDE) | `.agents/skills/context-out/` | `~/.gemini/config/skills/` | `/` (via workflow espelho) |
| Antigravity CLI | `.agents/skills/context-out/` | `~/.gemini/antigravity-cli/skills/` | `/` |

Cursor também lê `.claude/skills/` e `.codex/skills/` por compatibilidade. Antigravity guarda
regras e workflows em `.agent/` (singular) e skills em `.agents/` (plural) — não confunda.

### Uma cópia, três ferramentas (recomendado)

```bash
# fonte única no projeto
mkdir -p .agents/skills
cp -R /caminho/para/context-out .agents/skills/

# Claude Code aponta para a mesma pasta
mkdir -p .claude/skills
ln -s ../../.agents/skills/context-out .claude/skills/context-out
```

Global, equivalente:

```bash
mkdir -p ~/.gemini/config/skills ~/.claude/skills ~/.cursor/skills
cp -R context-out ~/.gemini/config/skills/
ln -s ~/.gemini/config/skills/context-out ~/.claude/skills/context-out
ln -s ~/.gemini/config/skills/context-out ~/.cursor/skills/context-out
```

Conferir se a IDE enxergou: digite `/` no chat e procure `context-out`. Não aparecendo,
o caminho está errado para aquela versão — teste a outra pasta da tabela.

## Frontmatter portável

`name` e `description` são o mínimo comum às três. `name` em minúsculas com hífen e **igual ao
nome da pasta** (Cursor exige). `metadata` é aceito no Claude Code e no Cursor e ignorado nas
demais — não coloque nada essencial lá. Campos exclusivos de uma ferramenta
(`paths`, `disable-model-invocation`, `icon`, `color` no Cursor) são ignorados pelas outras;
usar não quebra, depender quebra.

## Cursor

- **Plan Mode**: o plano vira um artefato do chat. Extraia decisões e pendências para o
  documento e registre o caminho em `artefatos:` — o plano não atravessa para outra IDE.
- **Pasta com ponto**: `.doc` pode não aparecer no `@` nem no índice. Leia por caminho
  explícito. `.cursorignore` e `.gitignore` também podem esconder — confira `ls -a .doc/`.
- **Abas paralelas / worktrees**: dois agentes podem escrever no mesmo documento. Aplique a
  regra de concorrência (releia `atualizado_em` antes de gravar).
- **Auto-chamada**: a descrição da skill é o gatilho semântico. Frase que dispara bem:
  "salvar contexto", "gerar handoff", "documentar a task", "registrar a revisão".
- **Identificador do chat**: use o link de Share, se houver. Sem link, grave título + data +
  workspace — dá para reabrir na lista de chats.

## Antigravity

- **Artefatos** (Implementation Plan, Task List, Walkthrough): são a fonte mais rica de
  contexto na sessão e a menos portável. Traduza decisão e pendência para o documento; cite
  o artefato em `artefatos:` como leitura opcional. Não cole o conteúdo inteiro.
- **Agent Manager**: vários agentes em paralelo no mesmo repositório. Concorrência de escrita é
  cenário normal, não exceção — releia antes de gravar, sempre.
- **Regras** em `.agent/rules/*.md`, limite de ~12.000 caracteres por arquivo. Não use regra
  para carregar o procedimento; a regra só aponta para a skill.
- **Workflow espelho** para garantir o `/` mesmo se a descoberta de skills falhar —
  `.agent/workflows/context-out.md`:

  ```markdown
  ---
  description: Grava o contexto da task atual em .doc/<task>.md para handoff entre IAs/IDEs.
  ---

  Execute a skill `context-out` (`.agents/skills/context-out/SKILL.md`): leia o SKILL.md e siga
  os passos 0 a 5. Se a skill não estiver instalada neste projeto, aplique o procedimento:
  crie `.doc/` na raiz se faltar, identifique o slug da task, e escreva/atualize
  `.doc/<slug>.md` com frontmatter (task, titulo, status, atualizado_em, proximo_papel, origem,
  sessoes) e exatamente as seções `## Objetivo`, `## Mudanças realizadas`,
  `## Decisões técnicas`, `## Pendências`, `## Contexto adicional`.
  ```

- **Identificador do chat**: nome e id da sessão no Agent Manager, mais a data. Cite os artefatos
  da sessão em `artefatos:` — são o complemento natural do `chat:` quando alguém volta a investigar.
- **Gemini CLI** lê skills de `~/.gemini/config/skills/` — a mesma instalação global serve.

## Claude Code

- `/context-out` ou chamada automática pela descrição.
- Hook `Stop` em `.claude/settings.json` para lembrar de gravar ao fim de sessão longa é
  opcional; a chamada manual cobre o caso normal.

## Campos de identificação entre ferramentas

Em `origem` e em cada entrada de `ciclos`, escreva **ferramenta / modelo**, sempre nessa ordem:

```
claude-code / opus-5
cursor / composer-2.5
antigravity / gemini-3-pro
gemini-cli / gemini-3-flash
copilot / gpt-5
```

Serve para o leitor seguinte calibrar: ciclo escrito por modelo de planejamento costuma ter decisão
densa e verificação rasa; por modelo de implementação, o inverso.

Cada ciclo grava também o `chat:` — identificador da conversa onde a etapa aconteceu e como
reabri-la. A tabela de captura por ferramenta (Claude Code, Cursor, Antigravity, Gemini CLI) está
em `ciclos.md`. Sem acesso ao identificador, grave `nao-disponivel` com ferramenta, título e data;
nunca invente.

# Ambientes — instalação e ativação por IDE

O documento em `.doc/` é Markdown puro e funciona em qualquer ferramenta. O que muda é **onde a
skill mora**, **o que a faz disparar no início da sessão** e **as armadilhas locais**.

## Instalação

| Ferramenta | Projeto | Global | Invocação manual |
|---|---|---|---|
| Claude Code | `.claude/skills/context-in/` | `~/.claude/skills/` | `/context-in` |
| Cursor | `.cursor/skills/` ou `.agents/skills/` | `~/.cursor/skills/` ou `~/.agents/skills/` | `/` e busca pelo nome |
| Antigravity (IDE) | `.agents/skills/context-in/` | `~/.gemini/config/skills/` | `/` (via workflow espelho) |
| Antigravity CLI | `.agents/skills/context-in/` | `~/.gemini/antigravity-cli/skills/` | `/` |

Cursor também lê `.claude/skills/` e `.codex/skills/` por compatibilidade. Antigravity usa
`.agent/` (singular) para regras e workflows e `.agents/` (plural) para skills.

### Uma cópia, três ferramentas

```bash
mkdir -p .agents/skills
cp -R /caminho/para/context-in .agents/skills/
mkdir -p .claude/skills
ln -s ../../.agents/skills/context-in .claude/skills/context-in
```

Confira digitando `/` no chat: `context-in` tem que aparecer. Não aparecendo, o caminho está
errado para aquela versão — teste a outra pasta da tabela.

## Ativação no início da sessão

Descoberta de skill é semântica: sem prompt que case com a descrição, nada dispara. Para carregar
o contexto logo na abertura, use uma regra sempre-ativa que **manda invocar a skill** — a regra
fica curta, o procedimento continua na skill.

### Cursor — `.cursor/rules/000-context-in.mdc`

```mdc
---
description: Carrega o contexto de handoff da pasta .doc no início da sessão
alwaysApply: true
---

Se existir a pasta `.doc/` na raiz do projeto, invoque a skill `context-in` antes da primeira
ação da sessão e antes de responder qualquer pergunta sobre a task. A pasta começa com ponto:
verifique com `ls -a .doc/`, não pelo seletor de arquivos. Sem `.doc/`, siga normalmente sem
mencionar nada.
```

### Antigravity — `.agent/rules/000-context-in.md`

```markdown
# Contexto de handoff

Se existir a pasta `.doc/` na raiz do workspace, invoque a skill `context-in`
(`.agents/skills/context-in/SKILL.md`) antes da primeira ação da sessão. Verifique com
`ls -a .doc/` — a pasta começa com ponto e pode não aparecer na busca de arquivos.
Sem `.doc/`, siga normalmente. Não grave nada em `.doc/` aqui: gravar é papel de `context-out`.
```

Limite de ~12.000 caracteres por arquivo de regra no Antigravity. A regra acima é curta de
propósito — não copie o procedimento para dentro dela. Serve igual em `AGENTS.md` ou `GEMINI.md`
na raiz, se preferir um arquivo só.

### Claude Code

Linha no `CLAUDE.md` do projeto:

```
Se existir pasta .doc na raiz, invoque a skill context-in antes da primeira ação da sessão.
```

`CLAUDE.md` grande demais e a linha se perde: use hook `SessionStart` em `.claude/settings.json`
injetando o mesmo lembrete.

### Antigravity — workflow espelho (opcional)

`.agent/workflows/context-in.md`, para garantir o `/` mesmo se a descoberta de skills falhar:

```markdown
---
description: Carrega o contexto da task de .doc/<task>.md gravado por outra IA/IDE.
---

Execute a skill `context-in` (`.agents/skills/context-in/SKILL.md`): leia o SKILL.md e siga os
passos 0 a 4. Se a skill não estiver instalada, aplique o procedimento: liste `ls -a .doc/*.md`,
escolha pelo slug citado ou pelo `atualizado_em` mais recente do frontmatter, leia o documento
inteiro, valide contra `git status`/`git log`, adote as decisões como vinculantes e confirme em
até 8 linhas. Sem `.doc/`, avise e siga sem contexto externo.
```

## Particularidades

### Cursor
- **Pasta com ponto**: `.doc` pode estar fora do índice e do `@`. Leia por caminho explícito.
  `.cursorignore`/`.gitignore` também escondem — confirme com `ls -a .doc/`.
- **Plan Mode**: se o documento citar um plano em `artefatos:`, ele é do chat que o gerou e
  provavelmente não existe aqui. Ausência não é erro; o documento se sustenta sozinho.
- **Re-disparo**: a skill pode ser chamada de novo no meio da sessão por semelhança semântica.
  Vale a regra de idempotência do Passo 1 — não recarregue nem repita a confirmação.

### Antigravity
- **Agent Manager**: vários agentes em paralelo. O documento pode mudar **durante** a sessão.
  Antes de executar uma pendência longa, confira se `atualizado_em` ou `ciclo` mudaram; se mudaram,
  releia — pode ter entrado um ciclo de revisão com correções.
- **Artefatos**: Implementation Plan e Task List do agente são internos da sessão. Use o
  documento como fonte principal e o artefato como aprofundamento opcional.
- **Modelos Gemini 3.x**: sem particularidade de leitura — o documento é Markdown plano de
  propósito, sem depender de formatação exótica.

### Claude Code
- `/context-in` ou disparo automático pela descrição.
- Com a linha no `CLAUDE.md`, a skill entra antes da primeira ação da sessão.

## Diagnóstico rápido

| Sintoma | Causa provável | Ação |
|---|---|---|
| Skill não aparece no `/` | pasta de instalação errada para a versão | teste a outra pasta da tabela |
| "Não encontrei `.doc`" com a pasta existindo | busca pelo índice/`@` em vez do caminho | `ls -a .doc/` e leitura por caminho |
| Contexto carregado duas vezes na mesma sessão | re-disparo semântico | regra de idempotência (Passo 1) |
| Correção aplicada volta a aparecer na revisão seguinte | status não atualizado no ciclo de correção | conferir status dos `C<n>.<n>`; reabrir pelo mesmo ID, não criar ID novo |
| Só o último ciclo foi considerado | leitura parcial do documento | ler decisões e correções de todos os ciclos (`ciclos.md`) |
| Documento diferente do esperado | escolha por mtime | ordenar por `atualizado_em` do frontmatter |
| Contexto some ao trocar de IDE | skill instalada só numa | instalar nas duas, ou `.agents/skills/` + symlink |

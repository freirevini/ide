# Ambientes — como cada IA encontra `AGENTS.md` e `.rules/`

Verificado em 2026-10 em documentação oficial e relatos; versões mudam. O Passo 5 da skill
(perguntar ao agente em sessão nova) é a confirmação que vale.

## Princípio

`AGENTS.md` é padrão aberto (formato em https://agents.md, governado pela Agentic AI
Foundation, da Linux Foundation), lido nativamente pela maioria das ferramentas. `.rules/` não é padrão de ninguém: é lido
porque o `AGENTS.md` manda ler. Ferramenta com arquivo próprio recebe um ponteiro de uma
linha. Nunca cópia: cópia diverge.

Linha-ponteiro, igual em toda ferramenta:

```
Leia AGENTS.md na raiz e todos os arquivos de .rules/ antes da primeira ação. São vinculantes.
```

## Tabela

| Ferramenta | Lê `AGENTS.md`? | Arquivo próprio | O que fazer |
|---|---|---|---|
| Claude Code ≥ 2.1.277 | sim, **só se não houver `CLAUDE.md`** no mesmo diretório | `CLAUDE.md`; `.claude/rules/*.md` (carregados sozinhos; `paths:` no frontmatter restringe a globs) | `CLAUDE.md` com `@AGENTS.md` na linha 1. Opcional: `ln -s ../.rules .claude/rules` carrega `.rules/` toda sessão; confirmar com `/memory` |
| Claude Code < 2.1.277 | não | idem | `CLAUDE.md` com `@AGENTS.md` |
| Cursor | sim; aninhado por subpasta | `.cursor/rules/*.mdc` (globs, `alwaysApply`) | nada. Reforço opcional abaixo |
| GitHub Copilot (VS Code agent mode, coding agent) | sim | `.github/copilot-instructions.md` (sempre); `.github/instructions/*.instructions.md` (`applyTo`) | nada. Se `copilot-instructions.md` existir com regras, migrar e deixar o ponteiro |
| OpenAI Codex | sim (origem do padrão) | — | nada |
| Gemini CLI | via configuração | `GEMINI.md` | `GEMINI.md` com a linha-ponteiro, ou `.gemini/settings.json` com `"contextFileName": ["AGENTS.md"]` |
| Antigravity IDE ≥ 1.20 | sim | `GEMINI.md`; `.agents/rules/` (novo) ou `.agent/rules/` (legado); limite ~12.000 caracteres por regra | nada |
| Antigravity CLI / managed agents | lê `.agents/AGENTS.md` | — | `mkdir -p .agents && ln -s ../AGENTS.md .agents/AGENTS.md` |
| Windsurf | sim (versões recentes) | `.windsurf/rules/*.md`; `.windsurfrules` (legado) | nada. Não carregou: `.windsurf/rules/agents.md` com a linha-ponteiro |
| Cline | versões recentes | `.clinerules` (arquivo ou pasta) | não carregou: `.clinerules` com a linha-ponteiro |
| Zed | sim | arquivo `.rules` (primeiro da lista: `.rules`, `.cursorrules`, `.windsurfrules`, `.clinerules`, `copilot-instructions.md`, `AGENT.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) | nada. **Atenção**: Zed procura um *arquivo* chamado `.rules` antes do `AGENTS.md`; a pasta `.rules/` não é esse arquivo. Confirmar no Passo 5 |
| Aider | não | `CONVENTIONS.md` via `.aider.conf.yml` | `.aider.conf.yml` com `read:` listando `AGENTS.md` e `.rules/*.md` |
| Jules, Devin, Amp, Factory, OpenCode, Roo Code, Kilo | sim | — | nada |
| JetBrains Junie | verificar | `.junie/guidelines.md` | linha-ponteiro |
| Kiro | verificar | `.kiro/steering/*.md` | `.kiro/steering/agents.md` com a linha-ponteiro |
| Qualquer outra | verificar na doc | o arquivo que a doc indicar | linha-ponteiro; nunca cópia |

## Ponteiros prontos

`CLAUDE.md`:

```markdown
@AGENTS.md

Leia também todos os arquivos de .rules/ antes da primeira ação. São vinculantes.
<!-- abaixo só o que é exclusivo do Claude Code: hooks, skills, permissões -->
```

`GEMINI.md`, `.clinerules`, `.junie/guidelines.md`, `.kiro/steering/agents.md`,
`.windsurf/rules/agents.md`, `.github/copilot-instructions.md`: só a linha-ponteiro.

`.aider.conf.yml`:

```yaml
read:
  - AGENTS.md
  - .rules/escopo.md
  - .rules/testes.md
  - .rules/erros.md
  - .rules/decisoes.md
```

`.gemini/settings.json` (alternativa ao `GEMINI.md`):

```json
{ "contextFileName": ["AGENTS.md"] }
```

## Precedência quando há mais de um arquivo

- **Claude Code**: `CLAUDE.md` vence `AGENTS.md` no mesmo diretório; o mais próximo do arquivo
  em edição soma ao da raiz. `/doctor` aponta contradição.
- **Cursor**: `AGENTS.md` aninhado entra só quando o agente trabalha naquela subárvore; regras
  de time vencem regras de projeto. Workspace multi-raiz vaza `AGENTS.md` entre raízes (bug
  conhecido): um repositório por janela, ou regras com `globs` em `.mdc`.
- **Zed**: carrega **um** arquivo, o primeiro da lista acima.
- **Antigravity**: `AGENTS.md`, `GEMINI.md` e regras são somados, sem ordem documentada.

Regra da skill: uma diretiva vive em um arquivo só. Os outros apontam.

## Monorepo

- Raiz: `AGENTS.md` completo e `.rules/` únicos.
- Cada pacote: `AGENTS.md` só com Projeto e Comandos do pacote e "regras em `.rules/` na raiz".
- Claude Code: `CLAUDE.md` do pacote com `@AGENTS.md` também, se o pacote tiver `CLAUDE.md`.

## Reforço mecânico (opcional)

`AGENTS.md` é instrução; nenhuma ferramenta obriga o agente a cumpri-la. Onde for crítico,
existe reforço que não depende de o agente lembrar:

- **Claude Code**: hook `Stop` em `.claude/settings.json` que roda a suíte rápida e bloqueia o
  encerramento com saída vermelha; hook `PreToolUse` que nega escrita fora de uma lista de
  caminhos. Configurar via skill `update-config` quando disponível.
- **Cursor**: `.cursor/rules/000-agents.mdc` com `alwaysApply: true` e três linhas: abrir
  `.rules/` antes da primeira ação; rodar `<comando rápido>` antes de "pronto"; registrar em
  `.rules/erros.md` após correção. Curta; o procedimento continua nos arquivos.
- **Antigravity**: `.agent/workflows/pronto.md` acionável por `/pronto`, com o checklist de
  "Definição de pronto" e "Após cada ajuste".
- **Copilot**: `.github/instructions/testes.instructions.md` com `applyTo: "**"` e as mesmas
  três linhas.
- **Qualquer ferramenta, pelo git**: `.githooks/commit-msg` chama `bash .rules/check.sh
  --commit-msg`; commit `fix` sem entrada nova em `erros.md` e sem teste é recusado. Vale para
  qualquer IA que commite pelo git local. `core.hooksPath` é configuração por clone: cada
  clone roda `git config core.hooksPath .githooks` uma vez (está em Comandos do `AGENTS.md`).
  `--no-verify` burla; por isso está em "Não fazer".
- **Qualquer ferramenta, pelo CI**: o mesmo script com `--range`. Pega o que o hook não
  pegou (clone sem hook, agente em segundo plano, `--no-verify`). GitHub Actions:

  ```yaml
  # .github/workflows/rules.yml
  name: rules
  on: [pull_request]
  jobs:
    check:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
          with: { fetch-depth: 0 }
        - run: bash .rules/check.sh --range "${{ github.event.pull_request.base.sha }}..HEAD"
  ```

  GitLab CI: `bash .rules/check.sh --range "$CI_MERGE_REQUEST_DIFF_BASE_SHA..HEAD"`. Outro
  CI: intervalo da base do PR até `HEAD`, com histórico completo no checkout.

## Diagnóstico

| Sintoma | Causa provável | Ação |
|---|---|---|
| Agente não sabe o comando de teste | arquivo não carregado | Claude: `/memory`; Cursor: painel de regras; Antigravity: conversa nova; outras: perguntar na sessão |
| Claude Code ignora `AGENTS.md` | existe `CLAUDE.md` sem `@AGENTS.md`, ou versão antiga | `@AGENTS.md` na linha 1 |
| Agente não abriu `.rules/` | mandou ler mas não listou os arquivos | índice com caminho exato de cada arquivo no `AGENTS.md`; Claude Code: symlink em `.claude/rules` |
| Agente repetiu erro que está em `erros.md` | entrada sem `Área` exata ou sem regra executável; ou `.rules/` não lido | corrigir a entrada; Passo 5 |
| Agente alterou arquivo fora do pedido | `escopo.md` não lido ou mínimo inline enfraquecido | item 1 do mínimo no topo; reforço mecânico |
| Regras conflitantes entre sessões | diretiva duplicada em `CLAUDE.md`/`GEMINI.md`/`.mdc`/README | manter em um lugar; ponteiro nos outros |
| Antigravity trunca arquivo | acima de ~12.000 caracteres | mover para `.rules/` ou `docs/` |
| Cursor aplica regra de outro repositório | workspace multi-raiz | um repositório por janela ou `.mdc` com `globs` |
| Zed não carrega nada | pasta `.rules/` confundida com arquivo `.rules` | confirmar com teste; se confirmado, relatar ao usuário e decidir juntos |
| Comando do arquivo falha na máquina | arquivo desatualizado | Passo 2 de novo; comando errado é pior que ausente |
| Hook não dispara | `core.hooksPath` não configurado neste clone, ou hook sem `chmod +x` | `git config core.hooksPath .githooks && chmod +x .githooks/commit-msg` |
| Hook recusa commit que não é correção | primeira linha da mensagem começa com `fix`/`corrig` por engano | reescrever a mensagem (`feat:`, `docs:`, `chore:`) |
| CI falha em commit antigo | histórico anterior à adoção da regra | `--range` a partir do commit de adoção, ou registrar retroativamente |

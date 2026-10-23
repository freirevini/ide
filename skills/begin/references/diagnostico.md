# Diagnóstico — o que detectar antes de criar qualquer coisa

O script `scripts/bootstrap.sh` faz a detecção abaixo sozinho. Esta página explica o que ele
olha, para você conferir o resultado e corrigir com flag quando a detecção errar.

## Raiz

`git rev-parse --show-toplevel`; sem git, a pasta aberta na IDE. Monorepo: a raiz do
repositório, nunca um pacote. O contrato (`AGENTS.md`, `.rules/`, `.doc/`) vive na raiz;
pacote recebe `AGENTS.md` só com o que difere (`agents-md/references/estrutura.md`,
"Monorepo").

## Stack pelo manifesto

| Arquivo encontrado | `--stack` | Bloco de ignore | Runner de teste padrão (`agents-md/references/testes.md`) |
|---|---|---|---|
| `pyproject.toml`, `requirements*.txt`, `setup.py`, `Pipfile` | `python` | `templates/gitignore/python` | pytest |
| `package.json` | `node` | `templates/gitignore/node` | vitest ou jest; o que `package.json` já cita |
| `go.mod` | `go` | `templates/gitignore/go` | `go test ./...` |
| `Cargo.toml` | `rust` | `templates/gitignore/rust` | `cargo test` |
| `pom.xml`, `build.gradle*` | `java` | `templates/gitignore/java` | JUnit via maven/gradle |
| `*.csproj`, `*.sln` | `dotnet` | `templates/gitignore/dotnet` | `dotnet test` |
| nenhum | `none` | só `base` | `a definir` |

Mais de um manifesto (ex.: `package.json` e `pyproject.toml`): a detecção pega o primeiro da
tabela; passe `--stack` com o principal e rode de novo com o segundo (`bootstrap.sh --stack
node` depois `--stack python`): o merge do `.gitignore` acumula sem repetir linha.

Stack fora da tabela (Ruby, PHP, Elixir, Swift, Kotlin, Dart...): `--stack none` e depois

```bash
gh api /gitignore/templates/<Nome> --jq .source >> .gitignore     # Nome: Ruby, Swift, Dart...
# sem gh:
curl -fsSL https://raw.githubusercontent.com/github/gitignore/main/<Nome>.gitignore >> .gitignore
```

Confira o que entrou: `git diff .gitignore`. Nada ali pode ignorar `AGENTS.md`, `.rules/`,
`.doc/`, `.githooks/` ou `.github/`.

## Remoto

| `git remote get-url origin` | Modo |
|---|---|
| contém `github.com` | GitHub: `.rules/git.md` + `.github/` |
| outro host (gitlab, bitbucket, dev.azure.com, servidor próprio) | `.rules/git.md`; `.github/` não; CI pelo snippet de `references/github.md` |
| vazio | só git local; `.rules/git.md` só se o usuário pedir (`--github` força) |

Repositório clonado com remoto GitHub mas sem acesso (`gh auth status` falha): o modo GitHub
vale do mesmo jeito; proteção de branch e segredos ficam como comando oferecido.

## Ferramentas de IA presentes

| Sinal no repositório | `--tools` | Ponteiro gerado |
|---|---|---|
| `.claude/` ou `CLAUDE.md` | `claude` | `CLAUDE.md` com `@AGENTS.md` |
| `.cursor/` | `cursor` | nenhum (lê `AGENTS.md`) |
| `.agents/` ou `.agent/` | `antigravity` | `.agents/AGENTS.md` symlink |
| `.gemini/` ou `GEMINI.md` | `gemini` | `GEMINI.md` |
| `.github/copilot-instructions.md` | `copilot` | mantém o arquivo; você acrescenta a linha-ponteiro |
| `.windsurf/` ou `.windsurfrules` | `windsurf` | `.windsurf/rules/agents.md` |
| `.clinerules` | `cline` | mantém; acrescente a linha-ponteiro |
| `.aider.conf.yml` | `aider` | mantém; acrescente `read:` |

Projeto vazio não tem sinal nenhum. A ferramenta que está executando esta skill entra sempre
(`--tools claude` se é o Claude Code, etc.), mais as que o usuário citou no Passo 2.
Ponteiro é uma linha; regra de projeto que estiver em arquivo de ferramenta migra para
`.rules/` (`agents-md`, modo Migrar).

## Arquivos de instrução já existentes

Leia inteiros antes de decidir o modo (SKILL.md, Passo 1). O que procurar:

```bash
ls AGENTS.md agents.md agent.md AGENT.md Agents.md CLAUDE.md GEMINI.md CONVENTIONS.md \
   .cursorrules .windsurfrules .clinerules .github/copilot-instructions.md 2>/dev/null
ls -a .rules .cursor/rules .claude/rules .agents/rules .agent/rules .github/instructions 2>/dev/null
```

`.rules` como **arquivo** (não pasta) é o formato do Zed; não é a pasta desta skill. Se existir,
Pergunta Aberta: o Zed carrega o primeiro da lista dele, e a pasta `.rules/` não é esse arquivo.

## Skills irmãs

| Skill | Papel aqui | Obrigatória | Onde o script procura |
|---|---|---|---|
| `agents-md` | templates de `AGENTS.md`, `.rules/` base, `check.sh`, hook; auditoria; atualização após ajuste | sim | pasta irmã desta skill; `~/.claude/skills/`; `~/.agents/skills/`; `~/.cursor/skills/`; `~/.gemini/config/skills/`; `.agents/skills/`, `.claude/skills/`, `.cursor/skills/` do projeto |
| `context-out` | grava `.doc/<task>.md` ao pausar ou trocar de ferramenta | não; `contexto.md` §4 descreve o formato manual | — |
| `context-in` | lê `.doc/<task>.md` ao entrar | não; `contexto.md` §2 descreve a leitura manual | — |
| `rules-default` | auditoria de `.cursor/rules/*.mdc` quando o projeto usa regras com globs | não | — |

`agents-md` ausente: o script sai com código 2 e diz onde instalar. Instale (um symlink da
pasta basta: `ln -s <repo-de-skills>/agents-md ~/.claude/skills/agents-md`) e rode de novo.
Não há fallback que copie o conteúdo: cópia diverge.

## Sinais de projeto que já tem contrato

| Sinal | Ação |
|---|---|
| `AGENTS.md` com as dez seções e sem `{{` | só completar o que falta (`contexto.md`, `git.md`, `.doc/`, ignore, ponteiros) |
| `AGENTS.md` com `{{` sobrando ou comando que falha | `agents-md` Passo A antes de seguir |
| `.rules/` com nomes diferentes (`rules/`, `docs/rules/`, `.ai/`) | não renomeie; Pergunta Aberta: migrar para `.rules/` ou apontar |
| `.doc/` com documentos | `context-in` antes de qualquer coisa; há task em andamento |
| hook em `.husky/`, `.pre-commit-config.yaml` ou `core.hooksPath` já configurado | não troque `core.hooksPath`; adicione a chamada `bash .rules/check.sh --commit-msg "$1"` ao hook `commit-msg` existente e avise |

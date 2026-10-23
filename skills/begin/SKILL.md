---
name: begin
description: Inicia qualquer projeto — pasta vazia, repositório recém-clonado ou código em andamento sem contrato de IA — com o mínimo para que qualquer IA de código (Claude Code, Cursor, Antigravity, Gemini CLI, Copilot, Codex, Aider ou outra) entenda o que foi feito e trabalhe sem quebrar o resto. Cria `AGENTS.md` na raiz, a pasta `.rules/` (escopo, testes, erros, decisões, contexto, permissões em três colunas e, com remoto git, git), a pasta `.doc/` para handoff entre IAs, `bin/setup` idempotente, `.gitignore`, `.editorconfig`, README mínimo, hook de commit, ponteiro para cada ferramenta (com lista de permissões para Claude Code) e, quando o repositório está no GitHub, `.github/` com template de PR e CI das regras. Idempotente, nunca sobrescreve o que existe, completa o que falta. Delega o conteúdo de `AGENTS.md` e das quatro regras base à skill `agents-md`, e o handoff de task às skills `context-out`/`context-in`. Use quando pedirem "começar projeto", "iniciar projeto", "novo projeto", "preparar o repositório para IA", "setup inicial", "bootstrap", "kickoff", "primeiro commit", ao criar pasta nova, ao clonar repositório sem `AGENTS.md`, ou ao abrir pela primeira vez um projeto em qualquer IDE com IA.
metadata:
  version: 1.1.0
  type: procedure
  requires: "agents-md (templates de AGENTS.md, .rules/ base, check.sh e hook); context-out e context-in opcionais (handoff)"
---

# Begin — início de projeto para qualquer IA

Projeto começa sem memória. A primeira IA que entra decide convenções que a segunda não vê;
a terceira refaz o que a primeira fez. O que evita isso não é modelo nem ferramenta: é um
conjunto pequeno de arquivos na raiz que toda IA lê antes de agir, criados no **primeiro dia**
e não quando o problema aparece.

Esta skill cria esse conjunto. Para o contrato (`AGENTS.md` + `.rules/` base) usa os
templates e o procedimento da skill `agents-md`; acrescenta o que ela não cobre: regras de
contexto (`.rules/contexto.md`), permissões em três colunas (`.rules/permissoes.md`: o que o
agente faz sozinho, o que pergunta, o que nunca faz), regras de git para repositório com
remoto (`.rules/git.md`), pasta de handoff `.doc/`, `bin/setup` idempotente, `.gitignore`,
`.editorconfig`, README mínimo, `.github/` e o primeiro commit.

**Governa**: existência e coerência dos arquivos de contrato e da infraestrutura mínima do
repositório (git, ignore, hook, CI das regras, ponteiros de ferramenta).

**Não toca**: linguagem, framework, arquitetura, gerenciador de pacotes, estrutura de pastas
do código, tamanho ou técnica do projeto. Não cria scaffold de código (`src/`, `main.py`,
rota, modelo): isso é do usuário ou do gerador do framework. Não cria conta, repositório
remoto, proteção de branch nem faz push sem pedido explícito; mostra o comando e espera.

**Invariantes**:
- Arquivo que existe é mantido. A skill completa o que falta e audita o que há
  (`agents-md`, Passo A); nunca sobrescreve.
- Uma diretiva vive em um arquivo só. Os outros apontam.
- Comando só entra no `AGENTS.md` depois de rodar com sucesso nesta máquina. Projeto sem
  código ainda: `a definir: <o que precisa existir>`; nunca slot `{{...}}` sobrando.
- Uma rodada de perguntas, no máximo. O que já veio no pedido não é perguntado.
- O nome do arquivo é `AGENTS.md` (formato aberto agents.md). `agent.md`, `agents.md` e
  `AGENT.md` são variantes e viram `AGENTS.md` por `git mv`.

---

## Passo 0 — Diagnóstico

```bash
cd "${RAIZ:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
ls -a
git rev-parse --is-inside-work-tree 2>/dev/null && git remote -v && git log --oneline -5
ls AGENTS.md agents.md agent.md AGENT.md CLAUDE.md GEMINI.md .cursorrules .clinerules \
   .github/copilot-instructions.md .aider.conf.yml 2>/dev/null
ls -a .rules .doc .githooks .github .claude .cursor .agents .agent .gemini .windsurf 2>/dev/null
ls pyproject.toml requirements.txt package.json go.mod Cargo.toml pom.xml build.gradle* \
   *.csproj *.sln Gemfile composer.json 2>/dev/null
```

Anote em tabela curta: raiz; git (sim/não); remoto (GitHub/outro/nenhum); stack pelo
manifesto (ou "vazio"); arquivos de instrução encontrados, lidos inteiros; ferramentas de IA
presentes; skills irmãs instaladas (`agents-md` obrigatória; `context-out`, `context-in`).
Tabelas de detecção em `references/diagnostico.md`.

---

## Passo 1 — Gate: qual modo

| Situação | Modo |
|---|---|
| Pasta vazia ou só README/LICENSE | **Novo**: Passos 2 a 8, tudo |
| Código sem `AGENTS.md` nem `.rules/` | **Completar**: Passos 2 a 8; comandos verificados pelo `agents-md` Passo 2 |
| Existe `AGENTS.md` e `.rules/` | **Auditar e completar**: `agents-md` Passo A no que existe; Passos 4 a 8 só para o que falta (`contexto.md`, `git.md`, `.doc/`, `.github/`, ignore, ponteiros) |
| Variante de nome (`agent.md`, `agents.md`, `AGENT.md`) | `git mv <variante> AGENTS.md`; depois **Auditar e completar** |
| Só `CLAUDE.md`, `GEMINI.md`, `.cursorrules` ou `copilot-instructions.md` com regras | **Migrar** pelo `agents-md` (conteúdo neutro vai para `AGENTS.md`/`.rules/`; fica o ponteiro); depois **Completar** |
| `agents-md` não instalada | pare; diga onde instalar (`references/diagnostico.md`, "skills irmãs"). Sem ela, não há template de contrato nem `check.sh` |

---

## Passo 2 — Perguntas de abertura (uma rodada)

Pergunte **só o que não está no pedido nem no repositório**, tudo de uma vez. Lista completa,
defaults e como derivar cada resposta: `references/perguntas.md`. Mínimo:

| Pergunta | Default se não respondida |
|---|---|
| Nome e uma frase: o que faz, para quem | nome da pasta; frase `a definir` |
| Stack (linguagem, framework, banco) | o que o manifesto diz; vazio: `a definir` |
| GitHub: já existe remoto, criar agora, ou não usar | o que `git remote -v` diz; sem remoto: não usar, e oferecer o comando de criação |
| Ferramentas de IA que vão trabalhar aqui | as detectadas no Passo 0 mais a que está executando esta skill |
| Idioma dos arquivos de contrato | o idioma do pedido |

Pedido já respondeu tudo: não pergunte nada; declare as suposições em uma linha e siga.

---

## Passo 3 — Git local e GitHub

- Sem `.git`: `git init -b main`. Reversível, sem efeito fora da pasta; faça e relate.
- Com `.git`: nada. Branch padrão é a que existe.
- Remoto GitHub detectado (`git remote get-url origin` contém `github.com`): modo GitHub ligado.
  Entram `.rules/git.md` e `.github/`.
- Usuário quer GitHub e não há remoto: **mostre** o comando e espere confirmação; criar
  repositório é ação fora da máquina.

  ```bash
  gh repo create <dono>/<nome> --private --source=. --remote=origin
  ```

  Confirmado e executado: modo GitHub ligado. Proteção de branch, Actions e segredos ficam em
  `references/github.md`, sempre como comando oferecido, nunca executado sem pedido.
- Remoto em outro host (GitLab, Bitbucket, Azure DevOps): `.rules/git.md` entra do mesmo
  jeito (as regras de branch, commit e PR são de git, não do GitHub); `.github/` não. Adapte
  o CI com o snippet correspondente de `references/github.md`.

---

## Passo 4 — Esqueleto

O script copia o que falta, nunca sobrescreve, e imprime o que criou e o que manteve.

```bash
SKILL=<pasta desta skill>
bash "$SKILL/scripts/bootstrap.sh" --dry-run            # mostra o plano
bash "$SKILL/scripts/bootstrap.sh" \
  [--github | --no-github] [--stack python|node|go|rust|java|dotnet|none] \
  [--tools claude,cursor,antigravity,gemini,copilot,windsurf,cline,aider] [--root DIR]
```

Sem flags, o script detecta stack, remoto e ferramentas. Flags vencem a detecção.

| Arquivo | Origem | Quando |
|---|---|---|
| `AGENTS.md` | `agents-md/templates/AGENTS.md` | sempre |
| `.rules/escopo.md`, `testes.md`, `erros.md`, `decisoes.md`, `check.sh` | `agents-md/templates/rules/` | sempre |
| `.githooks/commit-msg` + `git config core.hooksPath .githooks` | `agents-md/templates/githooks/` | sempre |
| `.rules/contexto.md` | `templates/rules/contexto.md` | sempre |
| `.rules/permissoes.md` | `templates/rules/permissoes.md` | sempre; três colunas: sozinho, pergunta, nunca |
| `.rules/git.md` | `templates/rules/git.md` | remoto git (GitHub ou outro) |
| `bin/setup` | `templates/bin/setup` | sempre; slots preenchidos no Passo 5; `chmod +x` |
| `.claude/settings.json` | `templates/permissions/claude.json` | ferramenta `claude`; cópia derivada de `permissoes.md`; só se não existe |
| `.doc/.gitkeep` | criado | sempre; é a pasta de handoff de `context-out`/`context-in` |
| `.gitignore` | `templates/gitignore/base` + `templates/gitignore/<stack>` | sempre; **merge** linha a linha, nunca substitui |
| `.editorconfig` | `templates/editorconfig` | sempre |
| `README.md` | `templates/README.md` | se não existe |
| `.env.example` | `templates/env.example` | se a stack usa variáveis de ambiente ou o usuário pediu |
| `.github/pull_request_template.md`, `.github/workflows/rules.yml` | `templates/github/` | GitHub |
| ponteiro por ferramenta | gerado | ferramentas de `--tools` ou detectadas (Passo 6) |

O script também insere no índice de regras do `AGENTS.md` as linhas de `contexto.md`,
`permissoes.md` e `git.md`, a linha `bash bin/setup` em "Comandos", e acrescenta
`ls -a .doc/` à linha "Início de sessão". Stack sem template de ignore:
`gh api /gitignore/templates/<Nome>` ou `references/diagnostico.md`.

---

## Passo 5 — Preencher

Siga `agents-md` Passo 2 (verificar comandos) e Passo 3 (preencher `AGENTS.md` e `.rules/`).
Regras adicionais desta skill:

- **Projeto vazio**: todo comando vira `a definir: quando existir <manifesto/teste/build>`.
  Seção "Código e estilo": `a definir no primeiro módulo`. "Ambientes": `dev local; sem
  staging; sem produção ainda`. Nada de inventar comando que não rodou.
- **Projeto com código**: nenhum `a definir` onde um comando rodou. Suíte de teste existe:
  rode e registre. Não existe: `agents-md` Passo 2 propõe o runner e cria um teste trivial com
  confirmação.
- `.rules/contexto.md`: preencha os slots (ferramentas, idioma, caminho do documento de
  arquitetura se houver). O resto é fixo.
- `.rules/git.md`: preencha convenção de branch, formato de commit, política de merge e quem
  revisa. Não contradiga a seção "Git e PR" do `AGENTS.md`: ela traz o mínimo e aponta para
  `git.md`; o procedimento mora em `git.md`.
- `.rules/permissoes.md`: preencha os slots com os comandos verificados (teste, lint, build e
  instalação na coluna "sozinho"; deploy, serviços e APIs pagas em "pergunta"; credencial e
  host de produção em "nunca"). As três colunas valem para qualquer ferramenta; a cópia por
  ferramenta (`.claude/settings.json`) é derivada, nunca a fonte. Projeto que já tem
  `.claude/settings.json`: compare com a lista e ajuste à mão; o script não toca.
- `bin/setup`: preencha ferramenta da stack, instalação, teste rápido e comando de rodar com
  o que já rodou nesta máquina. Rode duas vezes seguidas: a segunda termina sem erro e sem
  refazer trabalho. Stack com formatador padrão (`gofmt`, `cargo fmt`, `ruff format`,
  `prettier`): ele entra em "Lint / typecheck" do `AGENTS.md`; estilo não se discute depois.
  Projeto vazio: cada slot vira `a definir` em comentário e o script sai com aviso.
- `README.md` (se a skill criou): nome, frase, como rodar apontando para `AGENTS.md`. Dez
  linhas. Não duplique comandos: o `AGENTS.md` é a fonte.
- Idioma: o escolhido no Passo 2; nomes de arquivo e comandos ficam como estão.
- `grep -rn '{{' AGENTS.md .rules/ bin/setup README.md .github/ 2>/dev/null` vazio antes de
  seguir.

---

## Passo 6 — Ligar cada ferramenta

O script gera o ponteiro de cada ferramenta em `--tools`. Tabela completa e precedência em
`agents-md/references/ambientes.md`. Resumo do que o script faz:

| Ferramenta | Ponteiro |
|---|---|
| Claude Code | `CLAUDE.md` com `@AGENTS.md` na linha 1; `.claude/settings.json` com `permissions.allow/ask/deny` derivado de `.rules/permissoes.md` (só se não existe) |
| Cursor, Antigravity IDE, Copilot, Codex, Zed, Windsurf | nada; leem `AGENTS.md`. Permissões: copie as três colunas de `permissoes.md` no painel ou arquivo da ferramenta |
| Antigravity CLI | `.agents/AGENTS.md` como symlink para `../AGENTS.md` |
| Gemini CLI | `GEMINI.md` com a linha-ponteiro |
| Copilot (reforço) | `.github/copilot-instructions.md` com a linha-ponteiro |
| Cline / Windsurf (reforço) | `.clinerules` / `.windsurf/rules/agents.md` com a linha-ponteiro |
| Aider | `.aider.conf.yml` com `read:` listando `AGENTS.md` e `.rules/*.md` |

Ferramenta com arquivo próprio já existente: o script não toca; você acrescenta a
linha-ponteiro no topo à mão e move regra neutra para `.rules/` (`agents-md`, modo Migrar).

---

## Passo 7 — Primeiro teste e primeiro commit

1. Stack conhecida e sem teste: `agents-md` Passo 2, teste trivial que passa, com confirmação.
   Stack `a definir`: pule; `.rules/testes.md` fica com `a definir` nos comandos e a
   entrada "primeiro commit de código: definir runner" vai para "Manutenção" abaixo.
2. `bash .rules/check.sh` imprime `check.sh: ok`.
3. Commit local, sempre `chore:` (nunca `fix:`, que o hook exige registro):

   ```bash
   git add -A && git status --short      # confira: nada de .env, dado ou segredo
   git commit -m "chore: iniciar projeto com AGENTS.md, .rules/ e handoff"
   ```

4. `git push` só se o usuário pediu. Repositório recém-criado no Passo 3 com `--source=.`
   ainda não tem push: ofereça `git push -u origin main` e espere.
5. GitHub: ofereça proteção de `main` e CI (`references/github.md`); execute só com pedido.

---

## Passo 8 — Verificar

1. `ls -a` mostra `AGENTS.md`, `.rules/`, `.doc/`, `.githooks/`, `.gitignore`,
   `.editorconfig` e os ponteiros esperados.
2. `.gitignore` não ignora `AGENTS.md`, `.rules/`, `.doc/`, `.githooks/`, `.github/`
   (`git check-ignore -v AGENTS.md .rules .doc .githooks` não imprime nada).
3. `bash .rules/check.sh` ok; `git config core.hooksPath` responde `.githooks`.
4. Hook funciona: commit de teste `fix: x` sem entrada em `erros.md` é recusado; reverta.
5. Sessão nova na ferramenta principal: pergunte *"qual o comando de teste, o que você lê ao
   entrar no projeto e onde grava o contexto ao sair?"*. A resposta tem que bater com
   `AGENTS.md` e `.rules/contexto.md` (`agents-md` Passo 5).
6. `bash bin/setup` duas vezes seguidas: a segunda termina com `setup: ok` sem reinstalar
   nem falhar. Stack `a definir`: pule e registre em "Manutenção".
7. Permissões: peça ao agente `git push` de teste em branch descartável; ele tem que pedir
   confirmação, não executar. Peça `sudo ls`; tem que recusar.

---

## Passo 9 — Relatório

```
modo: novo | completar | auditar-e-completar | migrar
raiz: <caminho> · git: iniciado | existente · remoto: github <url> | outro | nenhum
stack: <detectada ou "a definir"> · ferramentas: <lista>
criados: <lista> · mantidos: <lista>
AGENTS.md: <n> linhas · slots restantes: 0 · "a definir": <n> (<quais>)
.rules/: escopo testes erros decisoes contexto permissoes [git] · check.sh: ok · hook: instalado
bin/setup: ok (2x) | a definir · permissões: .claude/settings.json criado | existia | n/a
ponteiros: <ferramenta: arquivo> ...
testes: <runner · n · verde> | a definir
commit: <hash curto> "chore: ..." | não feito (<motivo>) · push: não | <branch>
github: <pr template, rules.yml> | n/a · proteção de branch: oferecida | aplicada | n/a
perguntas abertas: <lista numerada ou "nenhuma">
```

---

## Manutenção

- Primeiro código em projeto que nasceu vazio: `agents-md` Passo 2 e substitua cada
  `a definir` por comando verificado. `.gitignore` ganha o bloco da stack
  (`bootstrap.sh --stack <x>` faz o merge sem tocar no resto).
- Remoto GitHub adicionado depois: `bootstrap.sh --github` acrescenta `git.md` e `.github/`.
- Ferramenta nova no time: `bootstrap.sh --tools <nome>` gera só o ponteiro que falta.
- Rodar `begin` de novo é seguro: mantém tudo que existe e relata o que faltava.
- Conteúdo de `AGENTS.md` e `.rules/` desatualizado: é `agents-md` (Passo A, Passo U).
- Task pausada ou trocando de ferramenta: `context-out` grava em `.doc/`; `context-in` lê.

## Referências

- `scripts/bootstrap.sh` — esqueleto idempotente; `--dry-run` mostra o plano.
- `templates/rules/contexto.md` — regras de contexto: onde o contexto vive, o que ler ao
  entrar, o que gravar ao sair, leitor frio.
- `templates/rules/git.md` — branch, commit, PR, push, o que nunca entra no repositório.
- `templates/rules/permissoes.md` — três colunas (sozinho, pergunta, nunca), modo autônomo,
  sessão arriscada, como aplicar por ferramenta.
- `templates/permissions/claude.json` — cópia derivada para `.claude/settings.json`.
- `templates/bin/setup` — máquina limpa até os testes rodarem; idempotente.
- `templates/gitignore/`, `templates/editorconfig`, `templates/README.md`,
  `templates/env.example`, `templates/github/` — arquivos de infraestrutura mínima.
- `references/diagnostico.md` — detecção de stack, remoto e ferramentas; skills irmãs.
- `references/perguntas.md` — a rodada única de perguntas e os defaults.
- `references/github.md` — proteção de branch, CI, segredos, Dependabot, CODEOWNERS: comandos
  oferecidos, nunca executados sem pedido.
- Skill `agents-md` — templates de `AGENTS.md`, `.rules/` base, `check.sh`, hook, auditoria,
  atualização após ajuste, ponteiros por ferramenta.
- Skills `context-out` / `context-in` — handoff de task em `.doc/`.
- Formato público: https://agents.md

---
name: agents-md
description: Cria, audita e mantém o contrato de qualquer projeto com qualquer IA de código — um `AGENTS.md` na raiz mais a pasta `.rules/` (escopo, testes, erros, decisões) — para o agente entender o contexto, não repetir erro já corrigido e não alterar nada fora do que foi pedido. Sem `AGENTS.md`, cria arquivo e pasta com comandos verificados na máquina. Com `AGENTS.md` (ou variante `agent.md`, `CLAUDE.md`, `GEMINI.md`, `.cursorrules`), audita nome, formato, tamanho, contradições e comandos quebrados e corrige. Aplica o orçamento de atenção, em que cada linha do `AGENTS.md` passa no teste "remover isto faria o agente errar?"; o que não passa vai para `.rules/` ou `docs/`. Após qualquer correção ou ajuste, registra o erro em `.rules/erros.md`, exige o teste de regressão e prova que nenhum outro comportamento mudou. Liga Claude Code, Cursor, Antigravity, Copilot, Gemini CLI, Windsurf, Cline, Zed, Aider, Codex e qualquer outra ferramenta ao mesmo arquivo por ponteiro, nunca por cópia. Use quando pedirem "cria o AGENTS.md", "configura o projeto para IA", "regras para o agente", "pasta .rules", "revisa o AGENTS.md", "o agente repetiu o erro", "mudou o que eu não pedi", "toda correção gera teste", ou ao abrir projeto novo em qualquer IDE com IA.
metadata:
  version: 2.1.0
  type: procedure
  source: "técnica discutida no Flow #663 (Fábio Akita, youtube.com/watch?v=N3eU-2VIByQ), generalizada para qualquer ambiente e qualquer IA; seções alinhadas ao formato aberto agents.md e à skill create-agentsmd (awesome-copilot)"
---

# `AGENTS.md` + `.rules/` — contrato do projeto com qualquer IA

Todo agente de código esquece entre sessões, conserta um ponto e quebra outro, e "melhora" o
que ninguém pediu. A resposta não depende de modelo nem de ferramenta: um arquivo de entrada
que toda IA lê (`AGENTS.md`, na raiz), regras em arquivos pequenos que ela abre antes de agir
(`.rules/`), regra que importa escrita como **teste**, e um **registro de erros** que cresce a
cada correção para o mesmo erro não voltar.

Esta skill cria esse conjunto quando não existe, audita quando existe e o atualiza depois de
cada ajuste. Serve para qualquer linguagem, qualquer tamanho de projeto e qualquer IA que leia
arquivos do repositório (`references/ambientes.md`). O `AGENTS.md` segue o formato aberto de
agents.md; a estrutura de seções incorpora a skill `create-agentsmd` (awesome-copilot) e
acrescenta o que ela não cobre: escopo cirúrgico, registro de erros, atualização após ajuste e
verificação mecânica (hook de commit e CI) que não depende de a IA lembrar.

**Governa**: existência, formato, veracidade e atualização de `AGENTS.md` e `.rules/`, e o
ponteiro de cada ferramenta até eles.

**Não toca**: tamanho, arquitetura, linguagem, framework de teste ou cobertura numérica do
projeto. Descreve o projeto como ele é. Sem runner de teste, propõe o padrão da linguagem e
**pergunta**; não decide.

**Invariantes**:
- Comando que não rodou com sucesso nesta máquina não entra em arquivo nenhum.
- Uma diretiva vive em um arquivo só. Os outros apontam; nunca copiam.
- Conflito entre instruções existentes vira **Pergunta Aberta** no relatório, nunca escolha
  silenciosa.
- A skill não altera código do projeto, salvo o esqueleto de teste do Passo 2, e só com
  confirmação.

---

## Passo 0 — Diagnóstico

```bash
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
ls -a
ls AGENTS.md agents.md agent.md AGENT.md Agents.md CLAUDE.md GEMINI.md CONVENTIONS.md \
   .cursorrules .windsurfrules .clinerules .rules .github/copilot-instructions.md 2>/dev/null
ls -a .rules .cursor/rules .claude/rules .agents/rules .agent/rules .windsurf/rules \
   .github/instructions .kiro/steering .github/workflows 2>/dev/null
find . -maxdepth 3 \( -name AGENTS.md -o -name CLAUDE.md \) -not -path '*/node_modules/*'
```

Anote em tabela curta: stack (manifesto), runner e quantidade de testes (zero é dado
importante), CI, ambientes (`.env.example`, compose, scripts de deploy) e **cada arquivo de
instrução encontrado, lido inteiro**.

---

## Passo 1 — Gate: qual modo

| Situação | Modo |
|---|---|
| Nenhum arquivo de instrução | **Criar**: Passos 2 a 6 |
| Existe `AGENTS.md` | **Auditar** (Passo A); depois só o que faltar dos Passos 2 a 6 |
| Existe variante (`agent.md`, `agents.md`, `AGENT.md`) | `git mv <variante> AGENTS.md`; depois **Auditar** |
| Só `CLAUDE.md`, `GEMINI.md`, `.cursorrules` ou `copilot-instructions.md` com regras de projeto | **Migrar**: conteúdo neutro vai para `AGENTS.md` e `.rules/`; no original fica o ponteiro e o que é exclusivo da ferramenta |
| Skill chamada logo após correção/ajuste, ou "registra esse erro" | **Atualizar após ajuste** (Passo U) |
| Regras com globs (`.cursor/rules/*.mdc`, `.claude/rules/` com `paths`, `.github/instructions/`) | ficam onde estão; `AGENTS.md` referencia. Auditoria delas é da skill `rules-default` |
| Duas fontes dizem coisas diferentes | Pergunta Aberta; seguir o que CI e manifesto comprovam |

---

## Passo 2 — Verificar comandos; garantir que "rodar os testes" executa algo

Execute cada comando que vai entrar no arquivo (instalar, rodar, testar, lint, build) e anote
a última linha da saída. Comando que falha entra como `a definir` com Pergunta Aberta.

Projeto **sem teste**: proponha o runner padrão da linguagem (`references/testes.md`, tabela
por stack), crie **um teste trivial que passa** e confirme com o usuário antes de fixar.
Projeto **com testes**: rode a suíte completa uma vez; registre tempo e resultado. Suíte
vermelha antes de começar é Pergunta Aberta, não ponto de partida.

---

## Passo 3 — Escrever `AGENTS.md` e `.rules/`

Copie os templates e preencha. `references/estrutura.md` explica cada arquivo e o formato das
entradas; `references/exemplo.md` calibra tamanho e tom.

```bash
SKILL=<pasta desta skill>
cp "$SKILL/templates/AGENTS.md" AGENTS.md
mkdir -p .rules .githooks
cp "$SKILL"/templates/rules/* .rules/
cp "$SKILL/templates/githooks/commit-msg" .githooks/
chmod +x .rules/check.sh .githooks/commit-msg
git config core.hooksPath .githooks
```

| Arquivo | Conteúdo | Muda quando |
|---|---|---|
| `AGENTS.md` | projeto, comandos verificados, índice de `.rules/` com o mínimo inline, código e estilo, ambientes, dados, git e PR, "após cada ajuste", pronto, não fazer | comando, caminho ou convenção muda |
| `.rules/escopo.md` | pedido em quatro partes, escopo cirúrgico, prova de não-regressão, relatório | raro |
| `.rules/testes.md` | bug vira teste, regra vira teste, estado pelo caminho curto, duas velocidades, proibições | raro |
| `.rules/erros.md` | registro: ID, data, área, sintoma, causa, regra, teste | **a cada correção** |
| `.rules/decisoes.md` | decisões com motivo; gotchas de ambiente | a cada decisão |
| `.rules/check.sh` | verificação mecânica: nome, tamanho, slot `{{...}}` sobrando, ID duplicado, segredo, caminhos; commit `fix` sem entrada em `erros.md` e sem teste é recusado | nunca; script fixo |
| `.githooks/commit-msg` | chama o `check.sh` em todo commit; `core.hooksPath` é por clone | nunca |

Escrita: imperativo, verificável, uma ideia por linha; nome exato de arquivo, comando e pasta;
nada de "geralmente", "preferencialmente", "código bom". Preencha todo slot `{{...}}` e apague
os comentários `<!-- -->`; `bash .rules/check.sh` acusa o que sobrou. Seção que não se aplica
fica com uma linha dizendo isso ("sem staging; produção faz esse papel"). Idioma: o do time;
os templates estão em português e a IA lê qualquer idioma. Time internacional traduz ao
preencher, mantendo nomes de arquivo e comandos.

Orçamento: `AGENTS.md` entre 60 e 150 linhas; cada arquivo de `.rules/` abaixo de **12.000
caracteres** (limite de regra do Antigravity; acima há truncamento silencioso). Monorepo:
`AGENTS.md` por pacote só com o que difere; `.rules/` só na raiz.

O orçamento é de atenção, não só de bytes. Acima de ~200 linhas de instrução sempre carregadas
a aderência cai para todas as regras, inclusive as que importam; `@import` e ponteiro não
aliviam (carregam na inicialização do mesmo jeito). Por isso cada linha do `AGENTS.md` passa
no teste **"remover isto faria o agente errar?"**. Dois níveis:

| Nível | Onde | Entra o quê | Teste |
|---|---|---|---|
| Regra governada | `AGENTS.md`, mínimo inline | invariante amplo, imperativo, durável, 1–2 linhas | esquecer causa erro em muitas tarefas |
| Conhecimento de recuperação | `.rules/decisoes.md`, `.rules/erros.md`, `docs/` | decisão com contexto, gotcha pontual, histórico, pesquisa | só importa quando a tarefa toca aquilo |

Promover para `AGENTS.md` é subtrativo: linha nova disputa atenção com as existentes, e regra
que precisa de parágrafo de contexto é conhecimento de recuperação, não regra. Procedimento
que muda com frequência (CI, deploy, integração): aponte para um **exemplo vivo** (arquivo ou
repositório que funciona hoje) em vez de descrever passo a passo.

---

## Passo 4 — Ligar cada ferramenta

Ferramenta que lê `AGENTS.md` nativamente não precisa de nada. Ferramenta com arquivo próprio
recebe **um ponteiro de uma linha**, nunca cópia. Tabela completa, snippets e reforço
mecânico em `references/ambientes.md`. Mínimo:

| Ferramenta | Ponteiro |
|---|---|
| Claude Code | `CLAUDE.md` com `@AGENTS.md` na linha 1; opcional `ln -s ../.rules .claude/rules` para carregar `.rules/` toda sessão (confirmar com `/memory`) |
| Cursor, Antigravity IDE, Copilot, Codex, Zed, Windsurf, Jules, Devin, Amp | nada; leem `AGENTS.md` |
| Gemini CLI | `GEMINI.md` com a linha-ponteiro, ou `"contextFileName": ["AGENTS.md"]` em `.gemini/settings.json` |
| Antigravity CLI | `mkdir -p .agents && ln -s ../AGENTS.md .agents/AGENTS.md` |
| Cline, Aider, Kiro, Junie, qualquer outra | arquivo próprio da ferramenta com a linha-ponteiro |

Linha-ponteiro, igual em toda ferramenta:
`Leia AGENTS.md na raiz e todos os arquivos de .rules/ antes da primeira ação. São vinculantes.`

Reforço que não depende da IA: o hook de commit instalado no Passo 3 recusa correção sem
registro e sem teste; o mesmo script roda em CI com `--range` (`references/ambientes.md`).
IA em segundo plano (Copilot coding agent, Codex, Jules) só entra pelo CI.

---

## Passo 5 — Verificar que a IA leu

1. Sessão nova na ferramenta. Pergunte: *"Qual o comando de teste deste projeto, o que você
   faz antes de declarar pronto, e qual o último erro registrado em `.rules/erros.md`?"*
   A resposta tem que bater com os arquivos.
2. Claude Code: `/memory`. Cursor: painel de regras. Antigravity: conversa nova após salvar.
3. Smoke: peça para corrigir um bug trivial conhecido. Observe se o agente listou o escopo
   antes, escreveu o teste antes da correção, registrou em `erros.md` no fim e não tocou em
   mais nada. Falhou algum item: a regra está longe do topo ou genérica demais.
4. Mecânico: `bash .rules/check.sh` imprime `check.sh: ok`. Depois, commit de teste
   `fix: x` sem entrada em `erros.md`: o hook tem que recusar. Reverta o commit de teste.

---

## Passo A — Auditar `AGENTS.md` existente

Checklist completo em `references/auditoria.md`. Saída: tabela `verificação · achado · ação ·
automática | pergunta`. A skill corrige sozinha: nome do arquivo, codificação, comando quebrado
(re-executa e substitui), placeholder sobrando, seção ausente (acrescenta do template),
arquivo acima do limite (move detalhe para `.rules/` ou `docs/`), diretiva duplicada (mantém
uma, aponta nas outras), regra vaga que tem forma verificável óbvia. Vira Pergunta Aberta:
contradição de conteúdo, regra que parece errada, comando que falha sem causa clara. Nunca
reescreva o que está certo; diff pequeno.

---

## Passo U — Atualizar após ajuste

Dispara após qualquer correção, ajuste ou "mudança pequena", feita pelo agente ou à mão. A
mesma lista está no `AGENTS.md` ("Após cada ajuste") para o agente cumprir sozinho.

1. **Teste**: existe teste que reproduzia o problema e agora passa? Não existe: escreva, veja
   falhar contra o código anterior (`git stash` ou `git checkout <sha> -- <arquivo>`), veja
   passar.
2. **Registro**: entrada nova no fim de `.rules/erros.md` (próximo ID, data, área, sintoma,
   causa, regra, teste, commit, origem). Uma linha por campo. Correção vinda de handoff
   (`.doc/`, item `C<n>.<n>`) cita o item em `Origem`. Dois agentes em paralelo geraram o
   mesmo ID: renumere o mais novo.
3. **Generalizar**: a lição vale para mais de um lugar? A regra vai para `.rules/testes.md`,
   `.rules/escopo.md` ou "Não fazer" do `AGENTS.md`; a entrada em `erros.md` aponta para lá.
4. **Comandos e caminhos**: algo citado no `AGENTS.md` mudou? Atualize e re-execute.
5. **Prova de escopo**: suíte completa verde; `git diff --stat` só com os arquivos previstos;
   nenhum teste existente alterado; `bash .rules/check.sh` ok. Arquivo a mais: ou justificado
   no relatório, ou revertido. Teste, registro e correção vão no **mesmo commit** (o hook
   exige).
6. **Compactar** quando `erros.md` passar de ~40 entradas ou 10.000 caracteres: entradas
   antigas viram uma linha com ID; ID nunca some.

---

## Passo 6 — Relatório

```
modo: criar | auditar | migrar | atualizar-após-ajuste
arquivos: AGENTS.md (<n> linhas, <n> chars) · .rules/{escopo,testes,erros,decisoes}.md
ponteiros: <ferramenta: ação> ...
comandos verificados: <comando · última linha> ...
testes: <runner> · <n> testes · <tempo> · verde|vermelho
auditoria: <n> achados · <n> corrigidos · <n> perguntas
erros.md: <ID novo ou "sem alteração">
check.sh: ok | <n> falhas · hook: instalado | não · CI: sim | não
migrado de: <arquivo> | nada
perguntas abertas: <lista numerada ou "nenhuma">
```

---

## Manutenção

- Comando mudou: atualize e re-execute. Comando errado é pior que ausente.
- Trocou de ferramenta ou de versão: Passo 5 de novo.
- `AGENTS.md` acima de 150 linhas ou `.rules/*.md` acima de 12.000 caracteres: Passo A.
- Agente repetiu erro que está em `erros.md`: a entrada está vaga (sem área ou sem regra
  executável) ou a ferramenta não carregou `.rules/`. Corrija a entrada; Passo 5.
- Agente alterou o que não foi pedido: `escopo.md` não foi lido ou o mínimo inline do
  `AGENTS.md` perdeu o item 1. Passo 5; considere reforço mecânico (`ambientes.md`).
- Agente ignora regra que está no `AGENTS.md`: o arquivo passou do orçamento de atenção.
  Passo A com o teste por linha; remova antes de acrescentar.

## Referências

- `templates/AGENTS.md`, `templates/rules/*.md` — arquivos para copiar e preencher; slot é
  `{{...}}`.
- `templates/rules/check.sh`, `templates/githooks/commit-msg` — verificação mecânica e hook.
- `references/estrutura.md` — por que entrada mais `.rules/`, formato de cada arquivo e de
  cada entrada, crescimento, compactação e correspondência com agents.md / `create-agentsmd`.
- `references/auditoria.md` — checklist do Passo A.
- `references/testes.md` — a disciplina de testes em detalhe e runner por stack.
- `references/protocolo.md` — pedido em quatro partes, escopo cirúrgico, prova de
  não-regressão, ambientes, dados, git, decisões: o que escrever e por quê.
- `references/ambientes.md` — como cada IA encontra os arquivos, ponteiros prontos, reforço
  mecânico, diagnóstico.
- `references/exemplo.md` — conjunto preenchido para um projeto pequeno, como calibre.
- Skill `begin` — início de projeto: usa estes templates e acrescenta `.rules/contexto.md`,
  `.rules/git.md`, `.doc/`, `.gitignore`, `.editorconfig`, README, `.github/` e o primeiro commit.
- Formato público: https://agents.md · skill de referência:
  https://www.skills.sh/github/awesome-copilot/create-agentsmd

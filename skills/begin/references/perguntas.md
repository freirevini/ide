# Perguntas de abertura — uma rodada, só o que falta

Regra: pergunte tudo de uma vez, só o que o pedido e o repositório não respondem, com default
explícito em cada item. Pedido completo: zero perguntas; uma linha de suposições e segue.
Nunca pergunte o que o manifesto, o `git remote` ou a pasta já dizem.

## As perguntas

| # | Pergunta | Como derivar antes de perguntar | Default | Vai para |
|---|---|---|---|---|
| 1 | Nome do projeto e uma frase: o que faz, para quem | nome da pasta; `name` do manifesto; `description` do `package.json`/`pyproject.toml`; primeira linha do README | nome da pasta; frase `a definir` | `AGENTS.md` Projeto; `README.md` |
| 2 | Stack: linguagem e versão, framework, banco, infra | manifesto; `.python-version`, `.nvmrc`, `engines`; `Dockerfile`, `compose.yml` | o que foi detectado; vazio: `a definir` | `AGENTS.md` Projeto; `.gitignore`; `.rules/testes.md` |
| 3 | GitHub: já existe remoto, criar agora, ou não usar | `git remote -v`; `gh repo view` | remoto existente; sem remoto: não usar, oferecendo o comando | modo GitHub; `.rules/git.md`; `.github/` |
| 4 | Ferramentas de IA que vão trabalhar aqui | sinais no repositório (`references/diagnostico.md`); a ferramenta atual | detectadas + atual | ponteiros; `contexto.md` §cabeçalho |
| 5 | Idioma dos arquivos de contrato | idioma do pedido | idioma do pedido | todos os templates (traduzir ao preencher; nomes de arquivo e comandos ficam) |
| 6 | Convenção de branch e integração (squash, merge, rebase) | `git log --merges`; branch protection via `gh api repos/<o>/<r>/branches/main/protection` | `feat/<slug>`; squash | `.rules/git.md` §1 |
| 7 | Há staging ou produção já? | `.env.example`, pastas `deploy/`, `infra/`, workflows de deploy | "sem staging; sem produção ainda" | `AGENTS.md` Ambientes |
| 8 | Dados de terceiros ou dado pessoal no projeto? | modelos, migrações, fixtures | "nenhum ainda" | `AGENTS.md` Dados e segurança |

Perguntas 6 a 8 só quando há código ou o usuário tocou no assunto. Projeto vazio: 1 a 5, e
só as que o pedido não cobriu.

## Formato da rodada

```
Antes de criar, três coisas que o pedido não diz (default entre colchetes; responda só o que quer mudar):
1. Stack? [a definir — pasta vazia, nenhum manifesto]
2. GitHub: criar repositório agora (`gh repo create freire/<nome> --private`) ou seguir só local? [só local]
3. Ferramentas além do Claude Code? [só Claude Code]
```

Uma mensagem. Sem resposta em modo autônomo: aplique os defaults, liste-os no relatório como
suposições e siga. Nenhuma das perguntas bloqueia a criação do esqueleto; elas mudam o
preenchimento.

## O que não perguntar

- Nome do arquivo de contrato: é `AGENTS.md`, sempre.
- Se quer `.rules/`, `.doc/`, hook, `.editorconfig`: são o mínimo; a skill cria. O usuário
  que não quiser apaga e registra em `.rules/decisoes.md`.
- Arquitetura, estrutura de pastas, framework de teste quando a stack é `a definir`: não é
  decisão de kickoff; nasce com o primeiro código (`agents-md` Passo 2).
- Licença: slot no README com `a definir`; não é bloqueante.
- Permissão para `git init` ou para o commit local `chore:`: reversíveis, dentro da máquina.
  Push, criação de repositório, proteção de branch: sempre perguntar, nunca executar sozinho.

# Git — branch, commit, PR, push; o que entra e o que nunca entra

Vinculante para qualquer agente que commite neste repositório, em qualquer ferramenta.
Remoto: {{github.com/<dono>/<repo>}}. O mínimo está em `AGENTS.md`, seção "Git e PR"; o
procedimento é este arquivo. Conflito entre os dois: este arquivo está errado, corrija aqui.

## 1. Branches

- Padrão: `{{main}}`. Ninguém commita direto nela{{; exceção: nenhuma | o dono, em `chore:`}}.
- Trabalho: `{{feat|fix|chore|docs}}/<slug-curto>` a partir de `{{main}}` atualizada
  (`git pull --rebase origin {{main}}` antes de criar).
- Uma branch por pedido. Pedido novo, branch nova. Branch viva por mais de {{5}} dias úteis é
  sinal de escopo grande demais: divida.
- Integração: {{squash merge pelo PR | merge commit | rebase e fast-forward}}. Branch apagada
  após merge.

## 2. Commits

- Formato: `<tipo>(<escopo opcional>): <o que mudou, imperativo, minúscula, sem ponto>`.
  Tipos: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`, `ci`, `build`.
  Corpo (opcional) diz **por quê**, não o quê; o diff já mostra o quê.
- Um assunto por commit. Correção e refatoração não dividem commit.
- `fix:` leva no mesmo commit a entrada nova em `.rules/erros.md` e o teste que reproduz o
  erro. O hook `.githooks/commit-msg` recusa sem isso; `[sem-teste: motivo]` na mensagem
  dispensa só o teste.
- Antes de `git commit`: suíte rápida verde (última linha no relatório), `bash .rules/check.sh`
  ok, `git diff --stat` só com os arquivos do escopo, `git status --short` sem arquivo
  inesperado.
- Mudou comando, caminho, convenção ou ambiente: `AGENTS.md` atualizado no mesmo commit.
- Nunca: `--no-verify`, `--amend` em commit já publicado, commit com teste vermelho, commit
  com segredo (mesmo que apagado no commit seguinte: fica no histórico).

## 3. Pull request

- Um PR por branch; título no formato de commit; descrição responde: o que mudou, como foi
  verificado (comando e última linha), o que ficou de fora, suposições, perguntas abertas.
  Template em `.github/pull_request_template.md`.
- Linka a issue quando existe (`Closes #n`).
- Antes de abrir: `{{lint}}`, `{{comando completo}}` e `bash .rules/check.sh` verdes; branch
  rebased em `{{main}}`; CI verde.
- Revisão: {{quem revisa | "o dono aprova; sem segundo revisor por enquanto"}}. Comentário de
  revisão que vira correção segue "Após cada ajuste" do `AGENTS.md`.
- Agente sem humano no chat (CI, agente em segundo plano): abre **PR draft** com as perguntas
  numeradas em "Suposições". Nunca faz merge.
- PR grande demais para ler em uma sentada: dividir, não pedir desculpa na descrição.

## 4. Push e histórico

- `push` só quando o usuário pede ou quando o pedido inclui abrir PR.
- `--force` nunca em `{{main}}` nem em branch que outra pessoa ou outro agente tocou.
  Em branch própria, só `--force-with-lease`.
- Histórico publicado não é reescrito. Erro publicado se corrige com commit novo (`revert`).
- Tag `v<major>.<minor>.<patch>` quando o projeto lança versão; {{"sem versão por enquanto"}}.

## 5. Sincronizar e resolver conflito

- Começo de sessão: `git fetch --all --prune`; `git status` diz se a branch está atrás.
- Conflito: resolva arquivo a arquivo, rode a suíte completa antes de concluir o rebase ou o
  merge. Conflito em `.rules/erros.md` ou `decisoes.md`: mantenha as duas entradas e renumere
  a mais nova (`check.sh` acusa ID duplicado).
- Conflito em `.doc/<task>.md`: mantenha os dois ciclos; o mais novo recebe o próximo número.

## 6. O que nunca entra no repositório

- `.env` e qualquer arquivo com credencial, token, chave privada, senha, string de conexão.
- Dado pessoal, dado de cliente, dump ou export de banco, planilha de produção.
- Artefato de build, dependência instalada, cache, log, arquivo da IDE do usuário.
- Binário grande (> {{10}} MB) sem LFS e sem decisão em `.rules/decisoes.md`.

Entrou por engano: avise o usuário na hora. Remover do histórico (`git filter-repo`) e
rotacionar o segredo são decisões dele; não execute sem pedido.

## 7. O que sempre entra

`AGENTS.md`, `.rules/`, `.doc/`, `.githooks/`, `.github/`, `.gitignore`, `.editorconfig`,
`.env.example` (sem valor real), lockfile do gerenciador de pacotes, testes.

## 8. Hooks e CI

- Hook local: `git config core.hooksPath .githooks` uma vez por clone (está em Comandos do
  `AGENTS.md`). Hook não disparou: esse comando faltou, ou `chmod +x .githooks/commit-msg`.
- CI: `.github/workflows/rules.yml` roda `bash .rules/check.sh --range` em todo PR. Pega o que
  o hook não pegou (clone sem hook, agente em segundo plano, `--no-verify`). Suíte de testes
  no CI: {{job em `.github/workflows/<nome>.yml` | "a definir: quando houver comando de teste"}}.
- Proteção de `{{main}}` no GitHub (PR obrigatório, CI verde, sem force push): {{"aplicada em
  <data>" | "não aplicada; comandos em references/github.md da skill begin"}}.

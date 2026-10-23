#!/usr/bin/env bash
# begin/scripts/bootstrap.sh — esqueleto mínimo de projeto para qualquer IA. Idempotente.
#
# Uso:
#   bash bootstrap.sh [--dry-run] [--root DIR] [--github | --no-github]
#                     [--stack python|node|go|rust|java|dotnet|none]
#                     [--tools claude,cursor,antigravity,gemini,copilot,windsurf,cline,aider]
#
# Nunca sobrescreve arquivo existente. Copia o que falta, faz merge linha a linha no
# .gitignore, insere no AGENTS.md as linhas de contexto.md e git.md (se ausentes) e gera o
# ponteiro de cada ferramenta. Sem flag, detecta stack, remoto e ferramentas.
# Templates de AGENTS.md, .rules/ base, check.sh e hook vêm da skill agents-md (obrigatória).
# Compatível com bash 3.2 (macOS). Saída: 0 ok; 2 pré-requisito ausente.

set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd -P)"
TPL="$SKILL_DIR/templates"
DRY=0; ROOT=""; GITHUB=""; STACK=""; TOOLS=""
criados=""; mantidos=""; avisos=""

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    --root) ROOT="$2"; shift ;;
    --github) GITHUB=1 ;;
    --no-github) GITHUB=0 ;;
    --stack) STACK="$2"; shift ;;
    --tools) TOOLS="$2"; shift ;;
    -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
    *) echo "opção desconhecida: $1" >&2; exit 1 ;;
  esac
  shift
done

log()   { printf '%s\n' "$*"; }
aviso() { avisos="$avisos
  - $*"; }
executa() { [ "$DRY" -eq 1 ] && { log "  [dry-run] $*"; return 0; }; "$@"; }

# ---------- skill irmã agents-md ----------
AGENTS_MD=""
for cand in "$SKILL_DIR/../agents-md" "$HOME/.claude/skills/agents-md" "$HOME/.agents/skills/agents-md" \
            "$HOME/.cursor/skills/agents-md" "$HOME/.gemini/config/skills/agents-md" \
            ; do  # só caminhos da skill ou do usuário; nunca pastas do próprio repositório (não confiável)
  if [ -f "$cand/templates/AGENTS.md" ] && [ -f "$cand/templates/rules/check.sh" ]; then
    AGENTS_MD="$(cd "$cand" && pwd -P)"; break
  fi
done
if [ -z "$AGENTS_MD" ]; then
  cat >&2 <<'EOF'
FALHA: skill agents-md não encontrada (templates/AGENTS.md e templates/rules/check.sh).
Instale ao lado desta skill ou em ~/.claude/skills/agents-md, ~/.agents/skills/agents-md,
~/.cursor/skills/agents-md ou ~/.gemini/config/skills/agents-md e rode de novo.
EOF
  exit 2
fi

# ---------- raiz ----------
if [ -n "$ROOT" ]; then
  cd "$ROOT" || { echo "raiz inexistente: $ROOT" >&2; exit 1; }
else
  cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
fi
RAIZ="$(pwd -P)"

# ---------- git ----------
git_iniciado=0
if [ ! -d .git ] && ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  executa git init -q -b main . && git_iniciado=1
fi
remoto="$(git remote get-url origin 2>/dev/null || true)"
tem_remoto=0; [ -n "$remoto" ] && tem_remoto=1
if [ -z "$GITHUB" ]; then
  case "$remoto" in *github.com*) GITHUB=1 ;; *) GITHUB=0 ;; esac
fi

# ---------- stack ----------
algum() { for f in "$@"; do [ -e "$f" ] && return 0; done; return 1; }  # glob sem match fica literal
if [ -z "$STACK" ]; then
  if   algum pyproject.toml requirements*.txt setup.py setup.cfg Pipfile; then STACK=python
  elif [ -f package.json ]; then STACK=node
  elif [ -f go.mod ]; then STACK=go
  elif [ -f Cargo.toml ]; then STACK=rust
  elif algum pom.xml build.gradle build.gradle.kts; then STACK=java
  elif algum ./*.csproj ./*.sln; then STACK=dotnet
  else STACK=none; fi
fi

# ---------- ferramentas ----------
if [ -z "$TOOLS" ]; then
  { [ -d .claude ] || [ -f CLAUDE.md ]; }            && TOOLS="$TOOLS,claude"
  [ -d .cursor ]                                      && TOOLS="$TOOLS,cursor"
  { [ -d .agents ] || [ -d .agent ]; }                && TOOLS="$TOOLS,antigravity"
  { [ -d .gemini ] || [ -f GEMINI.md ]; }             && TOOLS="$TOOLS,gemini"
  [ -f .github/copilot-instructions.md ]              && TOOLS="$TOOLS,copilot"
  { [ -d .windsurf ] || [ -f .windsurfrules ]; }      && TOOLS="$TOOLS,windsurf"
  [ -e .clinerules ]                                  && TOOLS="$TOOLS,cline"
  [ -f .aider.conf.yml ]                              && TOOLS="$TOOLS,aider"
fi
TOOLS="$(printf '%s' "$TOOLS" | tr ',' '\n' | sed '/^$/d' | sort -u | tr '\n' ',' | sed 's/,$//')"
tem_tool() { printf ',%s,' "$TOOLS" | grep -q ",$1,"; }

# ---------- helpers ----------
instala() {  # instala ORIGEM DESTINO : copia só se DESTINO não existe
  src="$1"; dst="$2"
  if [ -e "$dst" ]; then mantidos="$mantidos $dst"; return 0; fi
  [ "$DRY" -eq 1 ] && { log "  [dry-run] criar $dst"; criados="$criados $dst"; return 0; }
  mkdir -p "$(dirname "$dst")" && cp "$src" "$dst" && criados="$criados $dst"
}
escreve() {  # escreve DESTINO <<conteúdo : grava só se não existe
  dst="$1"
  if [ -e "$dst" ]; then mantidos="$mantidos $dst"; cat >/dev/null; return 0; fi
  [ "$DRY" -eq 1 ] && { log "  [dry-run] criar $dst"; criados="$criados $dst"; cat >/dev/null; return 0; }
  mkdir -p "$(dirname "$dst")" && cat > "$dst" && criados="$criados $dst"
}
merge_ignore() {  # merge_ignore ARQUIVO_TEMPLATE : acrescenta ao .gitignore as linhas ausentes
  [ -f "$1" ] || return 0
  [ -f .gitignore ] || { [ "$DRY" -eq 1 ] || : > .gitignore; criados="$criados .gitignore"; }
  novas=""
  while IFS= read -r linha || [ -n "$linha" ]; do
    [ -z "$linha" ] && continue
    case "$linha" in "#"*) ;; *) grep -qxF -- "$linha" .gitignore 2>/dev/null && continue ;; esac
    novas="$novas
$linha"
  done < "$1"
  novas="${novas#?}"   # tira a quebra de linha inicial
  # só o cabeçalho ("# --- begin: x ---") sem linha útil: nada a fazer
  [ "$(printf '%s\n' "$novas" | grep -vc '^#')" -gt 0 ] || return 0
  [ "$DRY" -eq 1 ] && { log "  [dry-run] .gitignore += bloco $(basename "$1")"; return 0; }
  [ -s .gitignore ] && printf '\n' >> .gitignore
  printf '%s\n' "$novas" >> .gitignore
}
insere_apos() {  # insere_apos ARQUIVO PADRAO_ANCORA LINHA_NOVA : uma vez; aviso se âncora não existe
  f="$1"; ancora="$2"; nova="$3"
  grep -qF -- "$nova" "$f" && return 0
  if ! grep -qF -- "$ancora" "$f"; then aviso "âncora não encontrada em $f: '$ancora'; insira à mão: $nova"; return 0; fi
  [ "$DRY" -eq 1 ] && { log "  [dry-run] $f: inserir linha após '$ancora'"; return 0; }
  awk -v a="$ancora" -v n="$nova" 'BEGIN{d=0} {print} !d && index($0,a){print n; d=1}' "$f" > "$f.tmp" \
    && mv "$f.tmp" "$f"
}

PONTEIRO='Leia AGENTS.md na raiz e todos os arquivos de .rules/ antes da primeira ação. São vinculantes.'

log "raiz: $RAIZ"
log "git: $([ "$git_iniciado" -eq 0 ] && echo existente || { [ "$DRY" -eq 1 ] && echo "a iniciar" || echo iniciado; }) · remoto: ${remoto:-nenhum} · github: $GITHUB · stack: $STACK · tools: ${TOOLS:-nenhuma}"
log "agents-md: $AGENTS_MD"
[ "$DRY" -eq 1 ] && log "--- dry-run: nada será escrito ---"

# ---------- 1. contrato (agents-md) ----------
instala "$AGENTS_MD/templates/AGENTS.md" AGENTS.md
for f in escopo testes erros decisoes; do instala "$AGENTS_MD/templates/rules/$f.md" ".rules/$f.md"; done
instala "$AGENTS_MD/templates/rules/check.sh" .rules/check.sh
instala "$AGENTS_MD/templates/githooks/commit-msg" .githooks/commit-msg
if [ "$DRY" -eq 0 ]; then
  case " $criados " in
    *" .githooks/commit-msg "*)
      chmod +x .githooks/commit-msg
      [ "$(git config core.hooksPath 2>/dev/null)" = ".githooks" ] || git config core.hooksPath .githooks ;;
    *) aviso ".githooks/commit-msg já existia: hook NÃO ativado por este script. Leia-o e, se confiar, rode: git config core.hooksPath .githooks" ;;
  esac
  case " $criados " in *" .rules/check.sh "*) chmod +x .rules/check.sh ;; esac
fi

# ---------- 2. regras desta skill ----------
instala "$TPL/rules/contexto.md" .rules/contexto.md
instala "$TPL/rules/permissoes.md" .rules/permissoes.md
if [ "$GITHUB" -eq 1 ] || [ "$tem_remoto" -eq 1 ]; then
  instala "$TPL/rules/git.md" .rules/git.md
fi
instala "$TPL/bin/setup" bin/setup
[ "$DRY" -eq 0 ] && [ -f bin/setup ] && chmod +x bin/setup

# ---------- 3. índice e início de sessão no AGENTS.md ----------
if [ -f AGENTS.md ]; then
  insere_apos AGENTS.md '`.rules/decisoes.md`' \
    '- `.rules/contexto.md` — onde o contexto vive, o que ler ao entrar, o que gravar ao sair. Outra IA continua sem o seu chat.'
  insere_apos AGENTS.md '`.rules/contexto.md`' \
    '- `.rules/permissoes.md` — o que o agente faz sozinho, o que pergunta antes, o que nunca faz.'
  insere_apos AGENTS.md '- Instalar:' \
    '- Máquina limpa: `bash bin/setup` (idempotente: ferramentas, dependências, `.env`, hook, testes rápidos)'
  if [ -f .rules/git.md ] || { [ "$DRY" -eq 1 ] && { [ "$GITHUB" -eq 1 ] || [ "$tem_remoto" -eq 1 ]; }; }; then
    insere_apos AGENTS.md '`.rules/contexto.md`' \
      '- `.rules/git.md` — branch, commit, PR, push e o que nunca entra no repositório.'
  fi
  if grep -qF 'últimas 5 entradas de `.rules/erros.md`.' AGENTS.md && ! grep -qF 'ls -a .doc/' AGENTS.md; then
    [ "$DRY" -eq 1 ] && log "  [dry-run] AGENTS.md: acrescentar 'ls -a .doc/' à linha Início de sessão" || {
      sed 's/últimas 5 entradas de `.rules\/erros.md`\./últimas 5 entradas de `.rules\/erros.md`, `ls -a .doc\/` (task em andamento: carregue-a)./' \
        AGENTS.md > AGENTS.md.tmp && mv AGENTS.md.tmp AGENTS.md; }
  fi
fi

# ---------- 4. handoff, ignore, editorconfig, readme, env ----------
escreve .doc/.gitkeep </dev/null
merge_ignore "$TPL/gitignore/base"
[ "$STACK" != none ] && merge_ignore "$TPL/gitignore/$STACK"
[ "$STACK" != none ] && [ ! -f "$TPL/gitignore/$STACK" ] && aviso "sem template de ignore para '$STACK'; use gh api /gitignore/templates/<Nome>"
instala "$TPL/editorconfig" .editorconfig
instala "$TPL/README.md" README.md
case "$STACK" in python|node|go|rust|java|dotnet) instala "$TPL/env.example" .env.example ;; esac

# ---------- 5. github ----------
if [ "$GITHUB" -eq 1 ]; then
  instala "$TPL/github/pull_request_template.md" .github/pull_request_template.md
  instala "$TPL/github/workflows/rules.yml" .github/workflows/rules.yml
fi

# ---------- 6. ponteiros por ferramenta ----------
tem_tool claude && escreve CLAUDE.md <<EOF
@AGENTS.md

Leia também todos os arquivos de .rules/ antes da primeira ação. São vinculantes.
EOF
tem_tool claude && instala "$TPL/permissions/claude.json" .claude/settings.json
tem_tool gemini && escreve GEMINI.md <<EOF
$PONTEIRO
EOF
tem_tool copilot && escreve .github/copilot-instructions.md <<EOF
$PONTEIRO
EOF
tem_tool cline && escreve .clinerules <<EOF
$PONTEIRO
EOF
tem_tool windsurf && escreve .windsurf/rules/agents.md <<EOF
$PONTEIRO
EOF
tem_tool aider && escreve .aider.conf.yml <<'EOF'
read:
  - AGENTS.md
  - .rules/escopo.md
  - .rules/testes.md
  - .rules/erros.md
  - .rules/decisoes.md
  - .rules/contexto.md
  - .rules/permissoes.md
EOF
if tem_tool antigravity; then
  if [ -e .agents/AGENTS.md ]; then mantidos="$mantidos .agents/AGENTS.md"
  elif [ "$DRY" -eq 1 ]; then log "  [dry-run] criar symlink .agents/AGENTS.md -> ../AGENTS.md"; criados="$criados .agents/AGENTS.md"
  else mkdir -p .agents && ln -s ../AGENTS.md .agents/AGENTS.md && criados="$criados .agents/AGENTS.md"; fi
fi

# ---------- 7. checagens ----------
for p in AGENTS.md .rules .doc .githooks .github; do
  [ -e "$p" ] || continue
  if git check-ignore -q "$p" 2>/dev/null; then aviso "$p está ignorado pelo .gitignore; remova a regra (contexto.md §7)"; fi
done
for v in agents.md agent.md AGENT.md Agents.md; do
  [ -e "$v" ] && [ "$v" != AGENTS.md ] && ! ls -1 | grep -qx AGENTS.md && aviso "variante '$v' encontrada; git mv $v AGENTS.md"
done
case " $criados " in
  *" .rules/check.sh "*) [ "$DRY" -eq 0 ] && { bash .rules/check.sh >/dev/null 2>&1 || aviso "bash .rules/check.sh falhou: slots {{...}} a preencher (esperado em projeto recém-criado)"; } ;;
  *) [ -f .rules/check.sh ] && aviso ".rules/check.sh já existia: não executado por este script. Leia-o antes de rodar." ;;
esac

# ---------- relatório ----------
log ""
log "criados:";  for x in $criados;  do log "  $x"; done
log "mantidos:"; for x in $mantidos; do log "  $x"; done
[ -n "$avisos" ] && log "avisos:$avisos"
log ""
log "próximo: preencher slots -> grep -rn '{{' AGENTS.md .rules/ bin/setup README.md 2>/dev/null"
log "depois:  bash .rules/check.sh   (precisa imprimir 'check.sh: ok')"
exit 0

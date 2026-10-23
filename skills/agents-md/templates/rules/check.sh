#!/usr/bin/env bash
# .rules/check.sh — verificação mecânica de AGENTS.md e .rules/. Não depende de IA.
#
# Uso:
#   bash .rules/check.sh                        estático: nome, presença, tamanho, slots {{...}},
#                                               comentários, IDs duplicados, segredo, caminhos
#   bash .rules/check.sh --commit-msg ARQUIVO   estático + regra de correção no commit em curso
#                                               (chamado pelo hook .githooks/commit-msg)
#   bash .rules/check.sh --range A..B           estático + regra de correção em cada commit do
#                                               intervalo (CI)
#
# Regra de correção: commit cuja primeira linha começa com fix, hotfix, bugfix, corrig ou
# correção precisa, no mesmo commit, de (1) linha nova "### E-nnn" em .rules/erros.md e
# (2) arquivo de teste adicionado ou alterado. "[sem-teste: motivo]" na mensagem dispensa (2).
# Nada dispensa (1).
#
# Saída: 0 ok; 1 falha. "FALHA:" bloqueia; "aviso:" não. Compatível com bash 3.2 (macOS).

set -u
# raiz do projeto = pasta acima de .rules/, pela localização do próprio script (não pelo cwd)
cd "$(cd "$(dirname "$0")/.." && pwd)" || exit 1

LIMITE_CHARS=12000
LIMITE_LINHAS=150
falhas=0
falha() { printf 'FALHA: %s\n' "$*" >&2; falhas=$((falhas + 1)); }
aviso() { printf 'aviso: %s\n' "$*" >&2; }

# linhas fora de blocos ```, prefixadas com arquivo:linha
fora_de_fence() { awk '/^```/ { f = !f; next } !f { print FILENAME ":" NR ": " $0 }' "$1"; }

# ---------- 1. nome e presença ----------
# compara com a listagem real: em disco sem distinção de maiúsculas (macOS, Windows),
# "-f AGENTS.md" passaria mesmo com o arquivo chamado agents.md
if ! ls -1 2>/dev/null | grep -qx 'AGENTS.md'; then
  variante=$(ls -1 2>/dev/null | grep -iE '^agents?\.md$' | head -1)
  if [ -n "$variante" ]; then
    falha "arquivo chama '$variante'; renomeie: git mv '$variante' AGENTS.md"
  else
    falha "AGENTS.md não existe na raiz"
  fi
fi
for f in escopo testes erros decisoes; do
  [ -f ".rules/$f.md" ] || falha ".rules/$f.md não existe"
done

# ---------- 2. tamanho ----------
for f in AGENTS.md .rules/*.md; do
  [ -f "$f" ] || continue
  c=$(wc -c < "$f" | tr -d ' ')
  [ "$c" -le "$LIMITE_CHARS" ] || falha "$f tem $c caracteres (limite $LIMITE_CHARS); mova detalhe ou compacte"
done
if [ -f AGENTS.md ]; then
  l=$(wc -l < AGENTS.md | tr -d ' ')
  [ "$l" -le "$LIMITE_LINHAS" ] || aviso "AGENTS.md tem $l linhas (alvo até $LIMITE_LINHAS)"
fi

# ---------- 3. slots {{...}} e comentários <!-- --> sobrando ----------
for f in AGENTS.md .rules/*.md; do
  [ -f "$f" ] || continue
  sobras=$(fora_de_fence "$f" | grep -E '\{\{|<!--' || true)
  if [ -n "$sobras" ]; then
    printf '%s\n' "$sobras" | sed 's/^/FALHA: slot ou comentário sobrando: /' >&2
    falhas=$((falhas + $(printf '%s\n' "$sobras" | wc -l | tr -d ' ')))
  fi
done

# ---------- 4. palavras vagas (aviso) ----------
for f in AGENTS.md .rules/*.md; do
  [ -f "$f" ] || continue
  fora_de_fence "$f" | grep -iwE 'geralmente|preferencialmente|se possível|tente|idealmente' \
    | sed 's/^/aviso: palavra vaga: /' >&2 || true
done

# ---------- 5. segredo ----------
for f in AGENTS.md .rules/*.md; do
  [ -f "$f" ] || continue
  achados=$(grep -niE '(key|token|secret|senha|password|bearer)[a-z_]*[[:space:]]*[:=][[:space:]]*[^[:space:]]{6,}' "$f" || true)
  if [ -n "$achados" ]; then
    printf '%s\n' "$achados" | sed "s|^|FALHA: possível segredo em $f:|" >&2
    falhas=$((falhas + 1))
  fi
done

# ---------- 6. IDs duplicados (merge de agentes em paralelo) ----------
for par in "erros:E" "decisoes:D"; do
  f=".rules/${par%%:*}.md"; p="${par##*:}"
  [ -f "$f" ] || continue
  dups=$(grep -oE "^### $p-[0-9]+" "$f" | sort | uniq -d || true)
  [ -z "$dups" ] || falha "$f: ID duplicado ($(printf '%s' "$dups" | tr '\n' ' ')); renumere a entrada mais nova"
done

# ---------- 7. caminhos citados no AGENTS.md (aviso) ----------
if [ -f AGENTS.md ]; then
  grep -oE '`[^`]+`' AGENTS.md | tr -d '`' | sort -u | while IFS= read -r tok; do
    case "$tok" in
      *" "*|*"{{"*|*"<"*|*"*"*|*":"*|*"\$"*|-*|http*|.env) continue ;;
    esac
    printf '%s' "$tok" | grep -qE '^\.?[A-Za-z0-9_./-]+$' || continue
    case "$tok" in */*|.*) ;; *) continue ;; esac
    [ -e "$tok" ] || aviso "caminho citado em AGENTS.md não existe: $tok"
  done
fi

# ---------- 8. regra de correção ----------
eh_correcao() {
  printf '%s\n' "$1" | grep -v '^#' | sed -n '1p' \
    | grep -qiE '^(fix|hotfix|bugfix)(\(|:|!| |$)|^corrig|^correção'
}
tem_teste() {
  printf '%s\n' "$1" | grep -qE '(^|/)(tests?|specs?|__tests__|e2e)/|_test\.[A-Za-z]+$|\.(test|spec)\.[A-Za-z]+$|Tests?\.(java|kt|cs|swift)$|_spec\.rb$|(^|/)test_[^/]+\.py$'
}
verifica_correcao() {  # $1 rótulo, $2 mensagem, $3 arquivos (um por linha), $4 diff de erros.md
  eh_correcao "$2" || return 0
  printf '%s\n' "$4" | grep -qE '^\+### E-[0-9]+' \
    || falha "$1: commit de correção sem entrada nova (### E-nnn) em .rules/erros.md"
  if printf '%s\n' "$2" | grep -qiE '\[sem-teste:'; then
    aviso "$1: correção sem teste, dispensada por [sem-teste: ...]"
  else
    tem_teste "$3" || falha "$1: commit de correção sem arquivo de teste adicionado ou alterado ([sem-teste: motivo] na mensagem dispensa)"
  fi
}

modo="${1:-}"
case "$modo" in
  --commit-msg)
    if [ -f "${2:-}" ]; then
      verifica_correcao "commit em curso" "$(cat "$2")" \
        "$(git diff --cached --name-only)" "$(git diff --cached -U0 -- .rules/erros.md)"
    else
      falha "--commit-msg precisa do arquivo da mensagem"
    fi
    ;;
  --range)
    if [ -n "${2:-}" ]; then
      for sha in $(git rev-list --reverse --no-merges "$2" 2>/dev/null); do
        verifica_correcao "$(git log -1 --format='%h %s' "$sha")" \
          "$(git log -1 --format=%B "$sha")" \
          "$(git diff-tree --no-commit-id --name-only -r "$sha")" \
          "$(git show --format= -U0 "$sha" -- .rules/erros.md)"
      done
    else
      falha "--range precisa de A..B"
    fi
    ;;
  "") ;;
  *) falha "opção desconhecida: $modo" ;;
esac

if [ "$falhas" -eq 0 ]; then
  echo "check.sh: ok"
  exit 0
fi
printf 'check.sh: %s falha(s)\n' "$falhas" >&2
exit 1

# GitHub — o que configurar no remoto, sempre como comando oferecido

Tudo aqui age fora da máquina (cria repositório, muda proteção, grava segredo). A skill mostra
o comando, explica o efeito em uma linha e espera o pedido. Nunca executa por conta própria,
nem em modo autônomo. `gh` precisa estar autenticado (`gh auth status`).

## Criar o repositório

```bash
gh repo create <dono>/<nome> --private --source=. --remote=origin --description "<frase>"
git push -u origin main
```

`--public` só com pedido explícito. Repositório criado: `.rules/git.md` §cabeçalho recebe a
URL; `bootstrap.sh --github` acrescenta `.github/` se ainda não existe.

## Proteger `main`

Efeito: PR obrigatório, CI `rules` verde antes do merge, sem force push, sem apagar a branch.
Conta pessoal no plano gratuito: proteção só em repositório **público**; privado exige plano
pago ou organização. Se o comando falhar com 403/404, é isso; registre em `.rules/git.md` §8.

```bash
gh api -X PUT "repos/<dono>/<nome>/branches/main/protection" \
  -H "Accept: application/vnd.github+json" \
  --input - <<'JSON'
{
  "required_status_checks": { "strict": true, "contexts": ["check"] },
  "enforce_admins": false,
  "required_pull_request_reviews": { "required_approving_review_count": 0 },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
```

`contexts: ["check"]` é o nome do job em `.github/workflows/rules.yml`. Suíte de testes no CI:
acrescente o nome do job. Projeto solo: `required_approving_review_count: 0` (ninguém para
aprovar); time: 1.

Alternativa mais nova (rulesets), mesma ideia:

```bash
gh api -X POST "repos/<dono>/<nome>/rulesets" --input - <<'JSON'
{ "name": "main", "target": "branch", "enforcement": "active",
  "conditions": { "ref_name": { "include": ["refs/heads/main"], "exclude": [] } },
  "rules": [ { "type": "pull_request", "parameters": { "required_approving_review_count": 0,
               "dismiss_stale_reviews_on_push": true, "require_code_owner_review": false,
               "require_last_push_approval": false, "required_review_thread_resolution": false } },
             { "type": "non_fast_forward" }, { "type": "deletion" } ] }
JSON
```

## Política de merge do repositório

Alinhe com `.rules/git.md` §1. Squash (default da skill):

```bash
gh repo edit <dono>/<nome> --enable-squash-merge --enable-merge-commit=false \
  --enable-rebase-merge=false --delete-branch-on-merge
```

## CI

`.github/workflows/rules.yml` já roda `bash .rules/check.sh --range` em todo PR. Suíte de
testes: job separado, só quando o comando foi verificado (`agents-md` Passo 2). Esqueleto:

```yaml
# .github/workflows/tests.yml
name: tests
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # - uses: actions/setup-python@v5   # ou setup-node, setup-go, setup-java, setup-dotnet
      #   with: { python-version: "3.12" }
      - run: <comando de instalar verificado>
      - run: <comando completo de teste verificado>
```

Outro host, mesmo `check.sh`:

| Host | Comando no pipeline |
|---|---|
| GitLab CI | `bash .rules/check.sh --range "$CI_MERGE_REQUEST_DIFF_BASE_SHA..HEAD"` |
| Azure DevOps | `bash .rules/check.sh --range "origin/$(System.PullRequest.TargetBranch)..HEAD"` |
| Bitbucket | `bash .rules/check.sh --range "origin/$BITBUCKET_PR_DESTINATION_BRANCH..HEAD"` |

Checkout com histórico completo (`fetch-depth: 0` ou equivalente), senão `--range` não acha a
base.

## Segredos

Nunca em arquivo. No GitHub:

```bash
gh secret set NOME --body "<valor>"        # ou: gh secret set NOME < arquivo
gh secret list
```

No workflow: `${{ secrets.NOME }}`. `.env.example` lista o nome; `.rules/git.md` §6 proíbe o
valor no repositório. Segredo que entrou por engano: rotacionar é mais urgente que apagar do
histórico; as duas decisões são do usuário.

## Varredura e dependências (opcionais; ofereça, não aplique)

```bash
# secret scanning + push protection (repositório público, ou privado com GitHub Advanced Security)
gh api -X PATCH "repos/<dono>/<nome>" --input - <<'JSON'
{ "security_and_analysis": { "secret_scanning": { "status": "enabled" },
                             "secret_scanning_push_protection": { "status": "enabled" } } }
JSON
```

Dependabot (atualização de dependências por PR), uma vez por stack:

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "<pip | npm | gomod | cargo | maven | nuget | github-actions>"
    directory: "/"
    schedule: { interval: "weekly" }
```

`CODEOWNERS` só quando há mais de uma pessoa: `.github/CODEOWNERS` com `* @<dono>`.

## Issues e PR

- Issue por pedido que não cabe em uma sessão; o slug da issue vira o slug da branch e da task
  em `.doc/`.
- PR usa `.github/pull_request_template.md`; agente sem humano abre draft: `gh pr create --draft`.
- Depois do merge: `git checkout main && git pull --rebase && git branch -d <branch>`.

## Registrar o que foi aplicado

Cada item aplicado vira uma linha em `.rules/git.md` §8 ("proteção aplicada em <data>",
"merge: squash", "CI: rules + tests") e, se houve alternativa descartada, uma entrada em
`.rules/decisoes.md`.

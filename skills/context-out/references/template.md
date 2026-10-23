# Template canônico do documento de handoff

Arquivo: `.doc/<slug>.md`. Estrutura fixa — outras IAs dependem dela para localizar informação
sem ler tudo. Cinco seções H2, sempre presentes, sempre nesta ordem. O histórico cresce **dentro**
delas, por ciclo.

## Frontmatter

```yaml
---
task: auth-oauth-google              # slug, igual ao nome do arquivo
titulo: Login com OAuth Google       # legível
caminho: .doc/auth-oauth-google.md   # o próprio caminho — sobrevive a copiar/colar em outro chat
status: em-andamento                 # planejamento | em-andamento | pronto-para-implementar | em-revisao | em-correcao | concluida
ciclo: 4                             # número do último ciclo gravado
atualizado_em: 2026-09-09T15:40:00-03:00
proximo_papel: revisar               # planejar | implementar | revisar | corrigir | testar | nenhum
bastao: livre                        # livre | <ferramenta / modelo> · chat <id> · desde <ISO>; quem segura a task agora, uma sessão por vez
origem: antigravity / gemini-3-pro   # ferramenta / modelo que gravou o último ciclo
ciclos:
  - n: 1
    data: 2026-09-06
    por: cursor / composer-2.5
    acao: planejamento
    chat: "cursor · 'Plano OAuth' · 2026-09-06 · workspace lab/ide"
  - n: 2
    data: 2026-09-07
    por: antigravity / gemini-3-pro
    acao: implementação
    chat: agy-sess-3b90f11 · Agent Manager > "oauth base"
  - n: 3
    data: 2026-09-08
    por: cursor / composer-2.5
    acao: revisão
    chat: "https://cursor.com/share/<id>"
  - n: 4
    data: 2026-09-09
    por: antigravity / gemini-3-pro
    acao: correção
    chat: agy-sess-8f21c04 · Agent Manager > "oauth callback fix"
artefatos:                           # opcional — artefatos nativos da IDE, leitura extra
  - .agent/artifacts/plan-oauth.md · antigravity · Implementation Plan · ciclo 2
---
```

- `ciclo` + `ciclos` são a espinha do handoff em cadeia: quem fez o quê, quando, e de qual conversa.
- `bastao` é o uso único: `livre` quando o ciclo entrega para outro papel; o nome de quem trabalha
  em checkpoint. `context-in` só assume task com bastão livre, ou sessão cortada confirmada, e
  essa linha é a única coisa que ele escreve.
- `chat` grava identificador **ou** ferramenta + título + data. Nunca inventado.
- `caminho` existe para o caso do conteúdo ser colado em outro chat e perder o vínculo com o arquivo.
- `atualizado_em` é a chave de ordenação entre documentos — mtime não serve, `git clone` reescreve.
- `artefatos` é opcional e sempre secundário: plano do Plan Mode do Cursor, Implementation Plan /
  Task List / Walkthrough do Antigravity. Podem não existir na outra IDE — o documento tem que se
  sustentar sozinho sem abrir nenhum deles.

## Corpo

````markdown
> Documento de handoff de contexto. Leia por completo antes de agir.
> Cinco seções fixas, histórico por ciclo. O código no repositório é a verdade sobre o estado
> atual; este documento é a verdade sobre intenção e decisões.

# Login com OAuth Google

## Objetivo

Permitir login com conta Google no app web, emitindo sessão própria do backend.

**Fora de escopo**: outros providers, migração dos usuários existentes, tela de conta.

## Mudanças realizadas

### Ciclo 4 · 2026-09-09 · antigravity / gemini-3-pro · correção
chat: agy-sess-8f21c04 · Agent Manager > "oauth callback fix"
doc: .doc/auth-oauth-google.md

| Arquivo | Mudança | Por quê |
|---|---|---|
| `api/auth/callback.ts` | cookie httpOnly no lugar de token no body | correção C3.1 (D3) |
| `src/auth/oauth.ts` | trata `error=access_denied` | correção C3.2 |

Correções aplicadas: C3.1, C3.2. Recusada: C3.4 — ver Pendências.
Tentado e falhou: `Set-Cookie` em middleware global — quebrava rotas públicas sem sessão; voltou
para o handler do callback.

#### Verificação
- `npm test -- auth` → 18 passed, 0 failed.
- Fluxo end-to-end: **não testado** — falta client_id de dev.

#### Para o revisor validar
- C3.1: resposta sem `token` no body; cookie com `HttpOnly`, `SameSite=Lax`, `Secure` em produção.
- C3.2: `access_denied` retorna 400 tratado, não 500.
- **Não revisar de novo**: `src/config/providers.ts` — aprovado no ciclo 3, não tocado depois.

### Ciclo 3 · 2026-09-08 · cursor / composer-2.5 · revisão
chat: https://cursor.com/share/<id>

- **Escopo revisado**: ciclo 2 inteiro — `src/auth/oauth.ts`, `src/auth/session.ts`, `api/auth/callback.ts`.
- **Aprovado**: fluxo PKCE em `oauth.ts`; config em `providers.ts`.
- **Não validado**: fluxo end-to-end (sem credencial de dev) → pendência de teste, não achado.
- **Achados**: C3.1 (alta), C3.2 (média), C3.4 (baixa). Detalhe em Pendências.

### Ciclo 2 · 2026-09-07 · antigravity / gemini-3-pro · implementação
chat: agy-sess-3b90f11 · Agent Manager > "oauth base"

| Arquivo | Mudança | Por quê |
|---|---|---|
| `src/auth/oauth.ts` | criado — authorization code + PKCE | D1 |
| `src/auth/session.ts` | `createSession()` recebe `provider` | multi-provider |

Tentado e falhou: nenhum.

#### Verificação
- `npm test -- auth` → 14 passed, 0 failed.

### Ciclo 1 · 2026-09-06 · cursor / composer-2.5 · planejamento
chat: cursor · "Plano OAuth" · 2026-09-06 · workspace lab/ide

Plano fechado em D1–D2, sem código escrito.

## Decisões técnicas

### D1 (ciclo 1) — PKCE em vez de client_secret no front
- **Decisão**: authorization code + PKCE, sem secret no cliente.
- **Motivo**: SPA não guarda secret com segurança.
- **Alternativas descartadas**: implicit flow (descontinuado); BFF com secret (serviço novo, fora do escopo).
- **Afeta**: `src/auth/oauth.ts`, `src/config/providers.ts`.

### ~~D2 (ciclo 1) — token em localStorage~~ (supersedida por D3 no ciclo 3)
- Revertida: exposição a XSS.

### D3 (ciclo 3) — token em cookie httpOnly
- **Decisão**: cookie httpOnly + `SameSite=Lax`, emitido pelo backend.
- **Motivo**: substitui D2; XSS não alcança o token.
- **Afeta**: `src/auth/session.ts`, `api/auth/callback.ts`.

## Pendências

### Correções do ciclo 3 (revisão · cursor / composer-2.5)

- [x] **C3.1** `api/auth/callback.ts:42-51` · severidade: alta · status: aplicada no ciclo 4
  - **Problema**: token devolvido no corpo da resposta; qualquer XSS lê o token.
  - **Trecho**: `res.json({ token })`
  - **Correção**: setar cookie httpOnly e responder `204`. Segue D3.
  - **Aceite**: `npm test -- auth/callback` verde e body sem `token`.
  - **Origem**: ciclo 3 · revisão · cursor / composer-2.5

- [x] **C3.2** `src/auth/oauth.ts:88` · severidade: média · status: aplicada no ciclo 4
  - **Problema**: `error=access_denied` do provider cai no caminho de sucesso e estoura 500.
  - **Correção**: tratar antes da troca de code, retornar 400 via `toAuthError()`.
  - **Aceite**: teste de `access_denied` retornando 400.
  - **Origem**: ciclo 3 · revisão · cursor / composer-2.5

- [ ] **C3.4** `src/auth/session.ts:30` · severidade: baixa · status: recusada (ciclo 4)
  - **Problema**: nome `createSession` não distingue criação de renovação.
  - **Correção sugerida**: renomear para `issueSession`.
  - **Motivo da recusa**: rename toca 11 call sites fora do escopo desta task; virou item para o backlog.
  - **Origem**: ciclo 3 · revisão · cursor / composer-2.5

### Pendências gerais

- [ ] `[testar]` Fluxo end-to-end com client_id real. Bloqueado: falta credencial de dev (pedir ao usuário).
- [ ] `[revisar]` Re-revisar C3.1 e C3.2 no próximo ciclo.

## Contexto adicional

- **Stack**: TypeScript, Next.js 15 App Router, Vitest.
- **Comandos**: testes `npm test`; dev `npm run dev` (porta 3000).
- **Ler primeiro**: `src/auth/oauth.ts`, depois `src/config/providers.ts`.
- **Convenção do repo**: erro de auth nunca sobe cru para a UI, passa por `toAuthError()` em `src/auth/errors.ts`.
- **Armadilha**: `providers.ts` tem config duplicada para staging; mexer só no bloco `production` quebra staging em silêncio.
- **Não fazer**: não adicionar biblioteca OAuth pronta — decisão do usuário, o fluxo é manual de propósito.
- **Observação do ciclo 3 (sem ação)**: cobertura de teste do `session.ts` está rasa; não bloqueia, mas o próximo revisor deve olhar.
- **Suposição não verificada**: o provider aceita `redirect_uri` com porta local — não confirmado na doc deles.
- **Links**: <issue/ticket/PR, se houver>
````

## Regras de escrita

- Caminho de arquivo sempre relativo à raiz, em crase.
- Pendência começa com verbo, tem local e critério de aceite. `[papel]` indica quem continua.
- Item de correção usa ID `C<ciclo>.<n>`, estável para sempre, com status explícito.
- Decisão sem motivo é ruído — a próxima IA rediscute. Motivo e alternativa descartada evitam retrabalho.
- `Tentado e falhou:` em todo ciclo, mesmo que `nenhum`. Abordagem queimada sem registro é a
  primeira coisa que a próxima IA tenta.
- Regra durável do projeto e decisão que vale além da task moram em `AGENTS.md`/`.rules/`
  (skill `agents-md`); o documento aponta (`ver .rules/decisoes.md D-012`), não duplica.
- Suposição marcada como suposição.
- Sem transcrição de chat, sem tutorial de linguagem, sem elogio a si mesmo.
- Sem segredo (token, senha, `.env`, dado de cliente).
- **Portável**: nada que dependa de recurso de uma IDE só — memória do agente, artefato interno,
  aba aberta, índice semântico, `@arquivo`. Caminho relativo e comando de terminal funcionam em
  Claude Code, Cursor e Antigravity igualmente.

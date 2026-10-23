# Pesquisa: workflow e skills do Akita (AI Lair + GitHub) — 2026-10-23

Objetivo: levantar técnicas de uso de LLM em desenvolvimento, aplicáveis a qualquer
projeto e qualquer IA, que possam virar skills novas ou ampliar as existentes neste
repositório. Nada foi criado como skill; esta nota é insumo para decisão do usuário.

Fontes e cópias de referência: `inbox/akita/SOURCES.md`, `inbox/akita/my-skills/`
(16 skills do repo `akitaonrails/my-skills`), `inbox/akita/examples/` (AGENTS.md do
ai-memory, apêndices do livro, skill de avaliação por rubrica).

Nota sobre a página `/workflow/#company`: não existe seção "company" com conteúdo
próprio; a âncora aponta para o bloco "Versão para gestores" (quatro hábitos
adaptados a empresa: tarefa reversível, dados não sensíveis primeiro, teste de
aceitação + prazo + orçamento antes do piloto, medir qualidade/tempo/falhas antes
de ampliar).

---

## 1. O workflow (ailair.akitaonrails.com/pt-br/workflow)

### 1.1 A menor versão (vale para qualquer pessoa, qualquer IA)
1. Tarefa limitada: fim claro e resultado verificável.
2. Restrições escritas: o que deve continuar verdadeiro, quais comandos verificam
   o trabalho, o que não tocar.
3. Revisão humana: ler o diff, questionar suposições, rodar as verificações.
   Uma pessoa aceita a mudança.
4. Guardar a lição: cada falha vira teste de regressão ou regra escrita.

### 1.2 Setup diário
- Um agente por projeto (uma janela tmux por projeto), uma linha de instrução por
  manhã, revisão do resultado.
- Três prompts-padrão: dia normal = `pr-audit` + `iss-audit` depois
  `github-resolution`; com volume = acrescenta `release`; só bots = `pr-bump` +
  `release`.
- `--yolo` / `--dangerously-skip-permissions` só dentro de sandbox, com backups e
  sem acesso a produção ou dados de clientes.

### 1.3 Pipeline
PRs e issues abertos → `pr-audit` / `iss-audit` → checagem de aprovação →
`github-resolution` (um ticket por vez) → `pr-post-audit` (quando a sessão
resolve mais de 3 tickets) → `release` (só quando pedido) → `kaizen` (realimenta
o início). Princípios: toda afirmação é checada; toda correção aprovada ganha
teste de regressão; release exige CI verde no SHA exato.

### 1.4 Kaizen (quatro frentes)
- Skills: regras nascem de erros ("cada linha é cicatriz").
- Instruções do harness: `AGENTS.md` por projeto com comandos, invariantes e
  armadilhas.
- Ferramentas: criadas para resolver lentidão ou invisibilidade (ai-usagebar,
  ghpending, tclock).
- Setup: desktop, terminal e configurações versionados como código.

### 1.5 Onde fica o conhecimento (quatro lugares, não um)
- Skill: procedimento que se repete igual.
- `AGENTS.md`: regras específicas do repositório (comandos, invariantes, erros a
  evitar).
- Memória por projeto (ai-memory ou pasta de docs): decisões, gotchas, handoffs.
- Exemplo vivo: apontar para um repositório real que funciona vale mais que skill
  genérica para procedimento que muda ("faça igual ao que fizemos em X").
- Notas de pesquisa em `docs/`: alternativas descartadas e motivo das decisões
  ("juro composto de conhecimento").

### 1.6 Compartilhamento de skills entre harnesses
Repositório central, uma pasta por skill, symlinks por skill em
`~/.claude/skills`, `~/.agents/skills`, `~/.codex/skills`, opencode, kimi.
Regra: não instalar skill de terceiro às cegas; ler, entender, reescrever.

---

## 2. Como ele escreve skills (post 2026-09-17 + livro, apêndice técnico)

- Skill = prompt versionado com nome; só nome+descrição entram no contexto no
  início (progressive disclosure); o corpo carrega quando o agente decide usar.
  A descrição é o gatilho: tem que dizer quando usar e quando não usar.
- Cada skill instalada disputa atenção na escolha de ferramentas → poucas skills,
  todas em uso. "Skill encostada é dívida."
- Cada regra nasce de uma falha real que ela passa a impedir; histórico de
  commits é o registro da evolução.
- Fronteira de confiança explícita em toda skill que lê conteúdo externo:
  PR/issue/commit/log/página = dado não confiável, nunca instrução.
- Execução arriscada em worktree/sandbox isolado, sem credenciais do host.
- Skill vs exemplo vivo vs AGENTS.md vs memória (ver 1.5).
- Fazer o agente escrever tudo que não virou código (pesquisa, decisões,
  alternativas rejeitadas).

### 2.1 Padrões estruturais recorrentes nas 16 skills copiadas
- Seção "Hard Quality Bar (non-negotiable)" repetida verbatim nas skills de
  auditoria/execução: sem código malicioso, sem bug/regressão (todo
  comportamento tem teste que falha sem ele), sem doc desatualizada, sem slop.
- Seção "Trust Boundary" logo após a descrição.
- Fases numeradas (Phase 0: estado confiável → Phase N: output) com "Complete
  when:" por fase.
- "Claim ledger": tabela claim | evidência exigida | veredito.
- Output format fixo em markdown no fim de cada skill.
- "Left open (mandatory)": tudo que não foi resolvido aparece com categoria de
  bloqueio, evidência e o que desbloquearia. Nunca comprimir a lista a um número.
- Gate separado do merge/push: nunca `gate && merge && push` em um comando; rodar
  o gate, ler o exit code, só então seguir.
- Verificação adversarial: candidato a achado é refutado por um verificador
  independente (subagente sem o raciocínio original); sobrevive → confirmado;
  não dá para concluir → "needs-validation" sem severidade; refutado → listado
  como candidato rejeitado para não ser reencontrado.
- Reuso de evidência só com inputs imutáveis e equivalentes registrados; nunca
  reaproveitar scanner cujo input mudou.
- "Fix the class, not the instance": segunda ocorrência do mesmo sintoma =
  sinal de corrigir no ponto comum (contract test), não site a site.

---

## 3. Clean code para agentes (post 2026-04-20)

Motivação: leitura truncada (~2000 linhas por read), atenção degrada antes do
limite de contexto, grep é mais barato que read, cada tool call custa.

Princípios em ordem de relevância (números do autor, usar como heurística
relativa, não como gate — ver memória `skill-nao-limita-projeto`):
1. Funções e arquivos pequenos (funções 4–20 linhas; arquivos < 500, ideal
   200–300).
2. Responsabilidade única por módulo.
3. Nomes grepáveis e únicos: nome bom tem < 5 ocorrências; evitar `data`,
   `process`, `handler`, `Manager`, `Service`.
4. Comentários com WHY e proveniência (issue, SHA); não apagar comentários do
   agente em refactor; docstring com intenção + exemplo.
5. Tipos explícitos em tudo.
6. DRY rigoroso (agente atualiza uma cópia e esquece as outras).
7. Testes que o agente roda sozinho: um comando, documentado, saída parseável,
   sem setup manual; F.I.R.S.T; todo código novo e todo bug ganham teste.
8. Estrutura de diretório previsível (convenção do framework).
9. Injeção de dependência + fakes nomeados (`FakeEmailSender`) + wrapper fino
   sobre libs externas + config centralizada.
10. Aninhamento máximo 2 níveis (early return, guard clause).
11. Erros com o valor problemático e o formato esperado.
12. Formatador padrão da linguagem em pre-commit; não discutir estilo.
13. Sem comentário óbvio.

O que o agente NÃO faz sozinho e precisa estar escrito no arquivo de regras:
DI, DRY rigoroso, tipos em todo lugar, nomes únicos, código defensivo (rate
limit, retry com backoff, circuit breaker, timeout, fallback).

Meta-documentação: `AGENTS.md`/`CLAUDE.md` curto, imperativo, bullets, sem prosa;
template proposto < 100 linhas (~500 tokens) em seis áreas: code style, comments,
tests, dependencies, structure/formatting, logging (JSON estruturado). README com
arquitetura em ASCII/Mermaid; comandos de validação previsíveis; `bin/setup`
idempotente.

---

## 4. Orçamento do AGENTS.md (ai-memory/docs/design-rules-promotion.md)

- Modelos seguem com confiança ~150–200 instruções; o system prompt do harness
  já gasta ~50; sobra ~100 linhas de instrução para regras do projeto.
- Acima de ~200 linhas a aderência cai > 30% e derruba também as regras fortes.
- `@import` não economiza contexto: carrega na inicialização do mesmo jeito.
- Teste para cada linha: "remover isto faria o agente errar?" Se não, não entra.
- Dois níveis: regra governada (AGENTS.md, sempre carregada: invariantes amplos,
  imperativos, duráveis, compactos) vs conhecimento de recuperação (docs/wiki,
  sob demanda: decisões com contexto, gotchas pontuais, histórico).
- Promoção para AGENTS.md é subtrativa: admitir uma regra significa remover
  outra. Candidata só se: ampla, imperativa/falsificável, durável sem
  contradição, uma ou duas linhas.
- `CLAUDE.md` deve ser só `@AGENTS.md` (import real); "leia AGENTS.md" em prosa
  não carrega nada.

Exemplo de AGENTS.md maduro: `inbox/akita/examples/ai-memory.AGENTS.md`
(overview, stack, layout com responsabilidade por pasta, dois loops de teste
(rápido / gate completo), notas por plataforma, invariantes).

---

## 5. Segurança operacional (post 2026-07-11 + livro apêndice B)

Sete peças, cada uma cobre o buraco da anterior:
1. Jaula (sandbox): só a pasta do projeto é gravável; `~/.ssh`, `~/.gnupg`,
   `~/.aws`, perfis de browser ficam fora; rede desligada ou filtrada; nada de
   atalho para root (Docker socket = chave da casa).
2. Snapshots automáticos (BTRFS/APFS) + um manual antes de sessão arriscada.
3. Backup externo automático, versionado, criptografado, testado por restore.
4. Lista de permissões em três colunas:
   - pode sem perguntar: só leitura ou fácil de desfazer (status, diff, log,
     listar, grep, rodar testes, commit local);
   - pergunta antes: sai da máquina ou apaga (push, rm, docker run);
   - nunca: sudo, chmod 777, `git push --force`, descartar mudanças locais sem
     volta, reescrever histórico remoto.
   Push fica na coluna do meio: agente comita à vontade, humano publica.
5. Agente não entra em produção. Staging sim, mas escrevendo receitas
   versionadas (Ansible/Terraform/K8s/migrations), nunca comando avulso. Humano
   promove.
6. Notas que sobrevivem à sessão, em três gavetas: regras do projeto
   (AGENTS.md), decisões e pesquisas (docs/ versionado), meio do caminho
   (handoff: o que foi feito, o que falhou, o que ficou aberto).
7. Medidor de uso à vista para trocar de agente antes de estourar cota.

Segredos: `git status` + `git diff --cached` antes do commit; revisar todos os
commits locais antes do push; chave vazada = trocar a chave, não só limpar
histórico.

Git como rede: commits pequenos e frequentes, cópia remota, push sempre manual.

---

## 6. Limites das LLMs e o que fazer (ailair /limits + Flow #663)

- LLM copia bem o que é público e documentado; onde não há referência, cai em
  tentativa e erro.
- Fornecer oráculo (testes, verificação objetiva): no benchmark do autor, dar
  testes a modelos fracos mudou mais o resultado que a escolha de linguagem.
- Fornecer referência (spec, fonte, comportamento de referência).
- Orçar tokens para trabalho pesado em ferramentas.
- Engenheiro no controle; revisar tudo; o trabalho que cresce é julgamento.
- Harness importa tanto quanto modelo: mesmo modelo, Tier A em um harness e
  Tier C em outro; plugin de usuário deslocou nota em 106 pontos.
- Multi-agente forçado não melhorou qualidade em tarefa coesa; só custou mais.

---

## 7. Debug e investigação longa (livro, apêndice técnico)

- Antes de investigar: garantir reprodução em 100% das tentativas; sem isso é
  caça-fantasma.
- Técnica da espingarda: alterar uma categoria inteira de uma vez para
  descartar a família toda em um experimento; usar para conhecer o terreno.
- Rodízio de agentes quando um entra em círculo (mesmas hipóteses sem novidade);
  sessão longa entulha o contexto; matar e recomeçar quando o agente repete a
  mesma "solução".
- Registrar hipóteses e descartes em documentos (50 docs, 7 mil linhas, para
  um bug de um inteiro).

---

## 8. Testes com LLM dentro do sistema (livro, apêndice técnico)

- Bateria por commit: estilo → auditoria de deps → SAST → suíte completa (~22 s).
- Chamar o modelo duas vezes não devolve o mesmo; cada chamada custa. Guardar as
  respostas do modelo durante o desenvolvimento e só pagar de novo com flag
  explícita.
- Checagem estrutural da saída (arquivo existe, mínimo de itens, marcações
  obrigatórias) porque o modelo erra de formas criativas.
- Quando o mesmo modelo escreve o código e o dublê do teste, o teste pode
  certificar o erro (hallucinated API + mock da alucinação = verde falso).

---

## 9. Avaliação por rubrica (llm-coding-benchmark)

- Rubrica 0–100 em dimensões ponderadas; cada nota justificada com `file:line`;
  "never invent scores"; status != completed não desqualifica, penaliza.
- v3: testes ocultos (held-out) adversariais; os testes que o modelo escreve
  não contam; gate de causa raiz (variante do bug também tem que ser corrigida);
  gate de regressão; gate de performance; "honestidade" (status declarado vs
  realidade dos testes ocultos).
- Cópia: `inbox/akita/examples/benchmark-audit/`.

---

## 10. Mapeamento para este repositório

**Status (2026-10-23, mesma data):** aplicado. As 12 candidatas da tabela 10.1 que não eram
"extensão" viraram skills (`ticket-audit`, `ticket-resolution`, `post-merge-audit`,
`dependency-bump`, `release`, `verification-planning`, `reflect`, `worktrees`, `eval-rubric`,
`llm-in-tests`, `debug-ledger`, `codemap`); `clean-code-for-agents`, `agent-permissions`,
`task-brief` e `skill-hygiene` entraram como extensões de `forever-clean`, `begin`,
`prompt-default` e `reflect`. Extensões de 10.2 aplicadas em `agents-md`, `begin`,
`prompt-default`, `forever-clean`; depois, na mesma data, `context-in`/`context-out` (bastão de uso
único, `Tentado e falhou`, checkpoint e sessão cortada, três gavetas), `clean-code-review`
(legibilidade para agente) e `security-gemini-prompt` (verificação adversarial, relatório com
fronteiras sem achado, a validar, rejeitados, risco residual). Nada pendente de 10.2.

### 10.1 Candidatas a skill nova (sem equivalente local)

| Candidata | Fonte | Técnica macro | Observação |
|---|---|---|---|
| `ticket-audit` (pr-audit + iss-audit) | my-skills | Evidência sobre narrativa; claim ledger; hostile-change gate; trust boundary; um por vez | Generalizar para qualquer forge (GitHub, GitLab, Azure DevOps); trocar `gh` por abstração |
| `ticket-resolution` (github-resolution) | my-skills | Executa só o aprovado; teste de regressão antes do fix; slop é defeito; fecha ao pousar; "left open" obrigatório | Par da anterior |
| `post-merge-audit` (pr-post-audit) | my-skills | Auditar a árvore combinada após lote de merges; composição é superfície nova | Gatilho: > 3 tickets ou pré-release |
| `dependency-bump` (pr-bump) | my-skills | Caminho rápido para PR de bot com piso de supply chain (registry público, nome, versão, checksum; git/path/hook novo = auditoria completa) | |
| `release` | my-skills | Versão derivada do changelog (fix→patch, aditivo→minor, breaking→major); CI verde no SHA exato; tag anotada; nunca reescrever tag; limpeza pós-release | |
| `verification-planning` | my-skills | Caminho de evidência ANTES de implementar: claim → como o sistema revela a verdade → affordance mínima → orçamento → fechar | Complementa `verification-before-completion` (global, pós) |
| `reflect` / kaizen | my-skills + workflow | Após sessão: fricção repetida → menor forma útil (regra < skill < comando < agente); "criar nada" é resultado válido; inventariar o que existe antes | Fecha o loop com `agents-md` (regra por erro) |
| `clean-code-for-agents` | post 04/20 | Nomes grepáveis, WHY+proveniência, tipos, DI com fakes nomeados, um comando de teste, erros com valor+esperado, formatador, JSON logs | Conflito parcial com memória `skill-nao-limita-projeto`: números do autor viram heurística relativa, nunca gate. Talvez melhor estender `forever-clean` e `clean-code-review` |
| `agent-permissions` / `safe-autonomy` | post 07/11 + livro apB | Lista três colunas (pode / pergunta / nunca); push manual; agente fora de produção; snapshot antes de sessão arriscada; hábitos de segredo | Pode ser template em `begin` ou `agents-md` em vez de skill própria; relaciona com memória `skill-seguranca-delecao-no-repo` |
| `task-brief` | workflow 1.1 | Bloco de restrições: o que deve continuar verdadeiro, comandos que verificam, o que não tocar; resultado verificável | Provável extensão de `prompt-default` em vez de skill nova |
| `codemap` | my-skills | `codemap.md` por pasta (responsabilidade, design, fluxo, integração) + atlas raiz + registro em AGENTS.md; detecção de mudança por hash | Overlap com `acquire-codebase-knowledge`/`codebase-onboarding` (globais) |
| `worktrees` | my-skills | Lanes isoladas para trabalho arriscado/paralelo, confirmação antes de toda mutação git, manifesto local | Overlap com `EnterWorktree` do Claude Code; útil para IAs sem isso |
| `debug-ledger` | livro aptecnico | Reproduzir 100% antes; espingarda por categoria; registrar hipóteses e descartes; rodízio de agente quando entra em círculo | Overlap com `systematic-debugging` (global) |
| `llm-in-tests` | livro aptecnico | Cache de respostas do modelo em testes de integração com flag para pagar de novo; checagem estrutural; não deixar o mesmo modelo escrever código e dublê | Relevante para LLMOps Gemini (`gemini-vertex-tuning` golden set) |
| `eval-rubric` | llm-coding-benchmark | Rubrica ponderada com prova `file:line`; testes ocultos; testes do próprio modelo não contam; gates de causa raiz/regressão/honestidade | Relevante para avaliação de agentes Gemini |
| `skill-hygiene` | post 09/17 | Auditar skills: descrição como gatilho, poucas e em uso, última modificação, sobreposição, origem de cada regra | Pode entrar em `reflect` |

### 10.2 Extensões de skills existentes

- `agents-md`: orçamento (~100 linhas de instrução; teste "remover isto causaria
  erro?"); dois níveis (regra governada vs conhecimento de recuperação);
  critérios de promoção (ampla, imperativa, durável, compacta); `CLAUDE.md` =
  `@AGENTS.md`; seções comandos / invariantes / armadilhas / mapa do repositório;
  "exemplo vivo" como alternativa a regra longa.
- `context-out` / `context-in`: handoff de uso único com dono (claim-once);
  conteúdo mínimo = feito, falhou, aberto; regra para sessão cortada (handoff
  antigo pode preceder onde parou); as três gavetas (regras / decisões+pesquisa /
  meio do caminho) e onde cada uma mora.
- `begin`: template de permissões três colunas; um comando de teste documentado;
  `bin/setup` idempotente; formatador em pre-commit; lista do que o agente não
  faz sozinho (DI, DRY, tipos, nomes únicos, código defensivo).
- `prompt-default`: bloco de restrições do item 1.1 (deve continuar verdadeiro /
  verifica com / não tocar) quando a tarefa é de mudança de código.
- `forever-clean` / `clean-code-review`: heurísticas voltadas ao agente (nome
  com < N ocorrências medido contra o projeto, WHY+proveniência, não apagar
  comentários em refactor).
- `security-gemini-prompt`: fase de verificação adversarial (refutar cada achado
  com verificador independente; "needs-validation" sem severidade; candidatos
  rejeitados listados) e seção "Reviewed boundaries with no finding" com
  evidência concreta.

### 10.3 Já coberto por skills globais (não precisa cópia local)
`security-audit`, `simplify`, `verification-before-completion`,
`systematic-debugging`, `continuous-learning`, `acquire-codebase-knowledge`,
`code-review`, `conventional-commit`, `git-workflow`, `autonomous-loops`,
`agent-eval`, `eval-harness`, `skill-authoring`. Vale decidir se este repo quer
versões próprias (independentes de plugin) ou só referência.

### 10.4 Não aplicável / não copiado
`blog-cost-charts` (pessoal), `effect` (lib específica), `agent-browser`
(vendor npm), `humanizer` (terceiro, licença própria), `fact-check` (pessoal,
depende de CLIs locais), `release-smoke-test` (opencode), `loop-engineering`
(runtime OMO).

---

## 11. Alinhamento com as memórias do repo

- `skills-de-video-sao-macro`: tudo acima deve virar técnica genérica; fonte só
  em `metadata.source`; exemplos com projeto neutro.
- `skill-nao-limita-projeto`: os números do Akita (500 linhas, 20 linhas por
  função, < 5 ocorrências) entram como "olhar mais de perto", medidos contra o
  próprio projeto, nunca como gate.
- `skill-seguranca-delecao-no-repo`: a lista três colunas e "nada fora do root
  de trabalho" convergem; a jaula do Akita é a versão em sistema operacional da
  mesma guarda.
- `transcricao-flow-663-akita`: o processo de 4 itens do vídeo é o item 1.1 do
  site; o site e o post de skills dão a versão escrita e mais recente.

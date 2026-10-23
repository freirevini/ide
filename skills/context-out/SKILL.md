---
name: context-out
description: Grava o contexto de uma task em `.doc/<nome-da-task>.md` para handoff em cadeia entre IAs/IDEs diferentes (Claude Code, Cursor, Antigravity, Gemini CLI, Copilot) — objetivo, mudanças realizadas, decisões técnicas, pendências e contexto adicional em cinco seções fixas, escritas para outro modelo ler sem acesso ao histórico do chat. Cada execução acrescenta um ciclo novo ao documento (planejamento, implementação, revisão, correção), preservando o histórico anterior, com achados de revisão e itens de correção estruturados por arquivo/trecho/problema/correção, e com o ID do chat de origem para rastrear a conversa completa. Marca quem segura o bastão da task (`bastao:`, uma sessão por vez), grava em todo ciclo o que foi tentado e falhou para a próxima sessão não repetir, e aceita checkpoint em task longa para sessão cortada por cota ou falha não perder o estado. Use ao encerrar ou pausar uma etapa, ao trocar de ferramenta/modelo, antes de passo longo que pode estourar cota, e quando pedirem "salvar contexto", "gerar handoff", "documentar essa task", "registrar a revisão", "checkpoint", "salva onde parei", "vou continuar no Cursor/Antigravity/outra IDE".
metadata:
  version: 1.3.0
  type: procedure
---

# Context Out — gravar contexto para handoff

Escreve o documento que a skill `context-in` (ou qualquer outra IA, mesmo sem skill
instalada) vai ler para continuar a task em outra ferramenta.

**Invariante**: o documento é escrito para um **leitor frio** — modelo com zero histórico
deste chat, em outra IDE, de outro fornecedor, com outro conjunto de ferramentas. Nada pode
depender de algo "que já foi falado antes" nem de recurso exclusivo de uma IDE.

**Não é log de conversa.** É estado + intenção + decisão. Transcrição, raciocínio passo a
passo e explicação genérica de linguagem/framework ficam de fora.

**Cada execução grava um ciclo novo**, nunca sobrescreve os anteriores. A task atravessa a cadeia
quantas vezes for preciso (planejar → implementar → revisar → corrigir → revisar → …) e o
documento guarda a ordem cronológica completa, com quem fez cada etapa e de qual chat.
Formato do ciclo, revisão, itens de correção e rastreabilidade: `references/ciclos.md`.

**Bastão de uso único.** O frontmatter diz quem segura a task agora (`bastao:`). Ciclo que
entrega para outro papel deixa `bastao: livre`; checkpoint no meio de um papel mantém o bastão
com quem está trabalhando. `context-in` só assume task com bastão livre, ou com confirmação do
usuário quando a sessão dona parou de responder (sessão cortada). Exatamente uma sessão por vez.

**Handoff carrega o meio do caminho**, não a memória do projeto. Regra durável ("sempre",
"nunca") mora em `AGENTS.md`/`.rules/`; decisão que vale além desta task mora em
`.rules/decisoes.md` quando o projeto tem a skill `agents-md`, e o documento cita o `D-nnn`;
pesquisa e alternativas comparadas vão para `docs/`. Aqui fica o que foi feito, o que foi
tentado e falhou, e o que está aberto.

Instalação, invocação e particularidades de cada IDE: `references/ambientes.md`.

---

## Passo 0 — raiz do projeto e pasta `.doc`

```bash
git rev-parse --show-toplevel 2>/dev/null || pwd
```

Sem git, use a raiz do workspace aberto na IDE. Verifique `.doc` lá:

- Não existe: crie `.doc/`. Avise que criou.
- Existe: siga. Nunca crie `.doc` aninhado em subpasta — sempre na raiz.

`.doc` começa com ponto: em Cursor e Antigravity ele pode não aparecer no seletor de arquivos
nem no índice de busca semântica. **Sempre acesse por caminho explícito** (`cat .doc/x.md`,
leitura direta do path). Não conclua que o documento não existe só porque o `@`/busca não
achou — confirme com `ls -a .doc/`.

Se houver `.gitignore` sem menção a `.doc`, **não mexa**. Informe uma vez que handoff entre
máquinas e ferramentas exige `.doc` versionado, e deixe a decisão com o usuário.

---

## Passo 1 — identificar a task e o arquivo alvo

1. Liste: `ls -a .doc/*.md`.
2. Leia o frontmatter (`task:`, `titulo:`, `status:`, `atualizado_em:`) de cada um.
3. Decida:
   - **Task já tem documento** (mesmo slug, ou objetivo claramente equivalente): atualize.
     Regras de merge no Passo 3.
   - **Task nova**: crie `.doc/<slug>.md`.
   - **Ambíguo**: pergunte antes de criar. Documento duplicado da mesma task quebra o
     handoff — o próximo modelo lê um dos dois e perde metade do estado.

**Slug**: kebab-case, ASCII sem acento, 2–5 palavras, derivado do objetivo e não da ação
(`auth-oauth-google`, não `implementar-login`). Estável entre sessões e ferramentas.

**Escrita concorrente** (Antigravity roda vários agentes em paralelo no Agent Manager; Cursor
roda várias abas/worktrees): releia o arquivo imediatamente antes de gravar. Se
`atualizado_em` ou `ciclo` mudaram desde a leitura do passo 1, outro agente escreveu — releia,
funda o que ele acrescentou, pegue o próximo número de ciclo livre e só então grave. Nunca
sobrescreva cego.

### Ciclo e tipo de ação

4. Determine o **número do ciclo**: `ciclo` do frontmatter + 1. Documento novo começa em 1.
   Numeração monotônica, nunca reutilizada — IDs de correção apontam para ela.
5. Determine o **tipo de ação** desta passagem: `planejamento`, `implementação`, `revisão`,
   `correção`, `teste`, `refatoração`, `checkpoint` (o mesmo papel continua; use em task longa,
   antes de passo que pode estourar cota ou derrubar a sessão). Define o que é obrigatório
   gravar (Passo 3) e qual é o `proximo_papel`.

---

## Passo 2 — coletar o que entra

Junte e **confira contra o repositório**, não contra a memória do chat:

- Arquivos tocados: `git status --short`, `git diff --stat`, `git log --oneline` se houve commit.
- O que foi de fato executado nesta sessão (build, teste, lint) e o resultado real.
- Decisões com alternativa descartada — inclusive as revertidas.
- O que foi **tentado e falhou** nesta sessão: abordagem, por que não serviu, o que o
  experimento provou. Sem isso a próxima sessão começa pela mesma tentativa.
- Pendências, com **onde** (arquivo, função, linha).

**Artefatos nativos da IDE** (plano do Plan Mode do Cursor, Implementation Plan / Task List /
Walkthrough do Antigravity, TODO list do agente): não copie o conteúdo inteiro. Extraia
decisão e pendência para as seções próprias e registre o caminho no frontmatter (`artefatos:`).
Esses arquivos costumam não existir ou não ser legíveis na outra IDE — o documento em `.doc/`
precisa se sustentar sozinho, com o artefato valendo só como leitura extra opcional.

Marque como fato só o que foi verificado. O resto vai explicitamente como `suposição:`.
Suposição escrita como fato é a falha que mais custa no handoff — o próximo modelo constrói em cima.

### Rastreabilidade (obrigatório em todo ciclo)

Capture o identificador do chat/sessão em que esta etapa aconteceu e como reabri-lo, mais o
caminho do próprio documento. Vão na entrada do ciclo e no frontmatter (`ciclos:`). Como obter em
cada IDE: tabela em `references/ciclos.md`. **Nunca invente identificador** — sem acesso a ele,
grave `nao-disponivel` seguido de ferramenta, título do chat e data, que já bastam para achar a
conversa na mão.

### Se este ciclo é de revisão ou correção

- **Revisão**: colete escopo revisado, critérios validados (aprovados), critérios que não deu para
  validar e por quê, achados com severidade, e observações sem ação. Todo achado vira item de
  correção estruturado — arquivo, trecho, problema, correção, aceite. Achado vago não entra.
- **Correção**: colete quais IDs de correção foram aplicados, quais foram recusados e o motivo, e
  o que a correção mudou de fato no código.

---

## Passo 3 — escrever ou atualizar

Estrutura **fixa e obrigatória**, sempre nesta ordem, sempre presente (seção vazia recebe
`Nenhuma.` — nunca some):

```
## Objetivo
## Mudanças realizadas
## Decisões técnicas
## Pendências
## Contexto adicional
```

Template completo, frontmatter e exemplo preenchido: `references/template.md`.
Merge quando o documento já existe: `references/atualizacao.md`.

Resumo do merge:

| Seção | Regra |
|---|---|
| Objetivo | Preserva. Só muda se o escopo mudou — e aí registra a mudança. |
| Mudanças realizadas | **Acumula por ciclo**, mais recente no topo. Nunca reescreve ciclo anterior. |
| Decisões técnicas | **Acumula**, cada uma marcada com o ciclo que a tomou. Decisão revertida vira `~~supersedida~~` com o motivo, nunca some. |
| Pendências | **Reescreve** com o estado atual, incluindo os blocos de correção por ciclo de revisão. Concluída sai e aparece em Mudanças. |
| Contexto adicional | Funde. Remove só o que ficou comprovadamente falso. |

Sempre atualize `ciclo`, `atualizado_em`, `status`, `proximo_papel`, `caminho`, `bastao`
(`livre` ao entregar para outro papel; `<ferramenta / modelo> · chat <id> · desde <data-hora>`
em checkpoint) e acrescente uma entrada em `ciclos:` com número, data, **ferramenta / modelo**
(`cursor / composer-2.5`, `antigravity / gemini-3-pro`, `claude-code / opus-5`), tipo de ação e
identificador do chat.

### Obrigatório por tipo de ciclo

| Ciclo | Além do comum, grave |
|---|---|
| implementação | `#### Para o revisor validar` — critérios, riscos e o que **não** precisa ser revisado de novo |
| revisão | escopo revisado, critérios aprovados, critérios não validados com motivo, e um item `C<ciclo>.<n>` estruturado por achado |
| correção | IDs aplicados, IDs recusados com motivo, e o status atualizado de cada correção |
| checkpoint | feito até aqui, próximo passo exato (arquivo, comando), `status: em-andamento`, `bastao` com você |
| assumido de sessão cortada | título do ciclo com `· assumido de <ferramenta / modelo>` e linha `recuperado:` com o que o git mostrou que a sessão caída fez e não gravou |

Todo ciclo, de qualquer tipo, leva a linha `Tentado e falhou:` (ou `nenhum`): abordagem, por
que não serviu, o que provou. É a parte do handoff que mais evita retrabalho.

Formato exato da entrada de ciclo, do bloco de revisão e do item de correção: `references/ciclos.md`.

**Nunca escreva no documento**: credenciais, tokens, valores de `.env`, URL interna com
segredo, dado de cliente. `.doc` costuma ir para o git.

---

## Passo 4 — checagem antes de fechar

1. Cinco seções presentes, na ordem, nenhuma vazia sem `Nenhuma.`.
2. **Teste do leitor frio**: cada pendência é executável por outro modelo, em outra IDE, sem
   perguntar nada? Se não, falta caminho de arquivo, critério de aceite ou decisão.
3. Nada de "como conversamos", "conforme acima", "o arquivo de antes".
4. Nada que dependa de recurso de uma IDE só (memória do agente, artefato interno, aba aberta,
   índice semântico). Caminho de arquivo e comando de terminal funcionam em todas.
5. Sem segredo (Passo 3).
6. Até ~250 linhas. Passou muito disso, entrou transcrição ou explicação genérica — corte.
7. Caminhos conferidos contra o repositório real.
8. **Ciclo**: número novo, ciclos anteriores intactos, entrada com data, ferramenta/modelo, ação,
   `chat:` e `doc:`.
9. **Se entrega para revisão**: `#### Para o revisor validar` presente e específico.
10. **Se este ciclo é revisão**: todo achado virou item `C<n>.<n>` com arquivo, trecho, problema,
    correção e aceite. Nenhum achado solto em prosa.
11. **Se este ciclo é correção**: todo ID citado pela revisão tem status — aplicada, recusada com
    motivo, ou continua aberta.
12. Documento com mais de ~6 ciclos ou ~400 linhas: compacte os ciclos antigos conforme
    `references/ciclos.md`, sem tocar em decisões, correções abertas nem linhas `chat:`.
13. `Tentado e falhou:` presente no ciclo novo (ou `nenhum`).
14. `bastao` coerente: `livre` quando `proximo_papel` muda de mão; seu nome em checkpoint.
15. Regra durável ("sempre", "nunca") ou decisão que vale além desta task apareceu nesta
    sessão: foi para `AGENTS.md`/`.rules/` (projeto com `agents-md`) e o documento só aponta.
    Sem `agents-md`, fica em Contexto adicional com a marca `regra do projeto:`.

---

## Passo 5 — relatório

```
doc: .doc/<slug>.md · ciclo <n> (<ação>) registrado
status: <status> · próximo papel: <planejar|implementar|revisar|corrigir|testar|nenhum>
correções: <abertas> abertas, <aplicadas> aplicadas neste ciclo
pendências: <n> (<a mais importante>)
falhou: <n> abordagens registradas em "Tentado e falhou" | nenhuma
bastão: livre | <ferramenta / modelo> (checkpoint) · assumido de sessão cortada: sim | não
chat: <id ou "nao-disponivel · ferramenta · título · data">
```

Se a próxima etapa é em outra ferramenta, diga a frase de retomada de lá: `retomar task <slug>`
— é o que `context-in` procura, em qualquer IDE.

---

## Compatibilidade entre IDEs

| Ferramenta | Instalar em | Invocação |
|---|---|---|
| Claude Code | `.claude/skills/context-out/` · global `~/.claude/skills/` | `/context-out` ou automática por descrição |
| Cursor | `.cursor/skills/` ou `.agents/skills/` · global `~/.cursor/skills/` | `/context-out` ou automática |
| Antigravity | `.agents/skills/context-out/` · global `~/.gemini/config/skills/` | automática; workflow espelho em `.agent/workflows/` para o `/` |

Uma cópia em `.agents/skills/` atende Cursor e Antigravity; um symlink cobre o Claude Code.
Comandos, workflow espelho e checagem de instalação: `references/ambientes.md`.

---

## Recursos

- `references/template.md` — template canônico, frontmatter e exemplo preenchido.
- `references/ciclos.md` — ciclos em cadeia: numeração, tipos de ação, entrada de ciclo, checklist de revisão, itens de correção, rastreabilidade do chat, compactação.
- `references/atualizacao.md` — merge seção a seção, supersedência, mudança de escopo, concorrência.
- `references/ambientes.md` — instalação e particularidades de Claude Code, Cursor e Antigravity.

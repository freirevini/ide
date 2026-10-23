# Formato do documento — lado da leitura

Documento gerado por `context-out`. Cinco seções H2 fixas, nesta ordem, mais frontmatter YAML.

## Frontmatter — o que cada campo decide

| Campo | Uso na leitura |
|---|---|
| `task` | slug; casa com o que o usuário disser em "retomar task X". |
| `titulo` | segundo alvo de busca quando o usuário cita a task por nome legível. |
| `caminho` | caminho do próprio documento. Confirma o vínculo quando o conteúdo chegou colado em outro chat. |
| `status` | `planejamento` / `em-andamento` / `pronto-para-implementar` / `em-revisao` / `em-correcao` / `concluida`. Define se há trabalho aberto. |
| `ciclo` | número do último ciclo gravado. Muda durante a sessão se outro agente gravar em paralelo. |
| `atualizado_em` | **chave de ordenação** para "documento mais recente". Nunca use mtime de arquivo. |
| `proximo_papel` | define a fila de trabalho agora: `planejar` / `implementar` / `revisar` / `corrigir` / `testar` / `nenhum`. |
| `bastao` | quem segura a task agora: `livre` ou `<ferramenta / modelo> · chat <id> · desde <data-hora>`. Uma sessão por vez; assumir é a única escrita que `context-in` faz. Ausente em documento antigo: `livre`. Com outro chat e repositório adiante do documento: sessão cortada (Passo 2 da skill). |
| `origem` | ferramenta/modelo que gravou o último ciclo. Calibra a leitura, não a confiança. |
| `ciclos` | a cadeia inteira: `n`, `data`, `por` (ferramenta / modelo), `acao`, `chat`. Leia antes do corpo — dá a forma do handoff e onde está cada conversa de origem. |
| `artefatos` | opcional. Planos e artefatos nativos da IDE de origem (Plan Mode do Cursor, Implementation Plan / Task List / Walkthrough do Antigravity). Leitura extra, nunca obrigatória — costumam não existir fora da IDE que os criou. |

`status: concluida` + `proximo_papel: nenhum` e o usuário pedindo continuação: confirme o que
ele quer antes de abrir trabalho novo — provavelmente é task nova relacionada.

Cadeia longa (`ciclo` alto) com alternância `revisão` → `correção` → `revisão` no mesmo ponto:
sinal de correção que não resolve. Leia os IDs reabertos antes de repetir a tentativa anterior.

## As cinco seções

### `## Objetivo`
Escopo da task. Inclui **Fora de escopo** — trate como proibição, não como sugestão.
Se o usuário pedir algo do "fora de escopo", ele mudou de ideia: siga o usuário e avise que
isso contraria o documento (para atualizar depois via `context-out`).

### `## Mudanças realizadas`
Subseções **por ciclo**, mais recente no topo: `### Ciclo N · data · ferramenta / modelo · ação`,
com `chat:` e `doc:` logo abaixo, tabela `arquivo | mudança | por quê`, `#### Verificação` e —
quando o ciclo entrega para revisão — `#### Para o revisor validar`.

Profundidade de leitura: os 3 ciclos mais recentes inteiros; os anteriores pelo título, e inteiros
só se tocarem arquivo que você vai mexer. Ciclo compactado em uma linha traz o `chat:` para buscar
o detalhe. Anatomia completa e uso do `chat:`: `ciclos.md`.

Leia a Verificação com atenção: "não testado" ali significa risco real, não formalidade.
Falta de verificação vira item a checar antes de construir em cima.

Cada ciclo traz `Tentado e falhou:` (ou `nenhum`): abordagens já queimadas, com o motivo. Leia
todas, de todos os ciclos, antes de propor caminho. Ciclo `checkpoint` ou título com
`· assumido de <quem>` e linha `recuperado:` indicam task longa ou sessão cortada; o que está em
`recuperado:` é estado reconstruído do git, sem motivo conhecido.

### `## Decisões técnicas`
Blocos `D<n> (ciclo N)` com decisão, motivo, alternativas descartadas, arquivos afetados.
Valem **todas**, de todos os ciclos — não só as do último.

- **Vinculantes.** Não rediscuta por preferência de estilo.
- `~~D<n>~~ (supersedida por ...)` — abordagem já testada e rejeitada. Não reintroduza.
- `**Decisão do usuário**` — não rediscuta sem ele levantar.
- Só reabra decisão se o código provar que ela não se sustenta. Aí exponha o conflito ao
  usuário; não decida sozinho.

### `## Pendências`
Dois tipos de bloco.

**`### Correções do ciclo N (revisão · ferramenta / modelo)`** — itens `C<n>.<n>` com arquivo,
trecho, problema, correção, aceite, severidade e status. São instrução pronta para aplicar, não
sugestão. Semântica de status e regra de reabertura: `ciclos.md`.

**`### Pendências gerais`** — checkboxes com papel, local e critério de aceite:
`- [ ] [implementar] <ação> em <arquivo>. Aceite: <critério>.`

Ordem = prioridade; dentro de correções, severidade manda. `Bloqueado:` significa dependência
externa — não tente contornar sem avisar. Filtre por `proximo_papel`, mas leia tudo: uma correção
recusada explica por que o código está "errado" de propósito.

### `## Contexto adicional`
Stack, comandos, arquivos para ler primeiro, convenções, armadilhas, "não fazer", suposições,
relacionados, links.

- `suposição:` — hipótese, não fato. Verifique antes de depender.
- `descartado:` — já tentado/decidido contra.
- `divergência <data>:` — documento e repositório já discordaram antes; provável ponto frágil.
- `relacionada: .doc/<outro>.md` — leia se a task atual encostar nela.

## Documento fora do padrão

Documento escrito por IA sem esta skill, ou versão antiga do formato. Seja tolerante:

- **Falta seção**: trate como vazia. Não reclame do formato, não reescreva o documento.
- **Nomes diferentes** (`## Goal`, `## O que foi feito`, `## Next steps`): mapeie por
  significado para as cinco seções e siga.
- **Sem frontmatter**: pegue título do primeiro H1, use a data do último commit que tocou o
  arquivo como `atualizado_em` aproximado (`git log -1 --format=%cI -- .doc/<arquivo>.md`).
- **Texto corrido sem estrutura**: extraia o que der (objetivo, arquivos citados, próximos
  passos), diga ao usuário que o documento está fora do padrão e siga. O conteúdo vale mais
  que o formato.
- **Documento vazio ou só com título**: trate como inexistente — avise e siga sem contexto externo.
- **Escrito por outra IDE** (`origem: cursor / ...`, `antigravity / ...`): normal, é o objetivo do
  formato. Não corrija estilo, não reescreva, não desconfie do conteúdo por causa da origem.
  Modelo de planejamento tende a decisão densa e verificação rasa; modelo de implementação, o
  inverso — calibre a leitura por isso, não a confiança.

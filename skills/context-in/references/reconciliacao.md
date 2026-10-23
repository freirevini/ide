# Reconciliação — documento x chat em andamento x repositório

Aplicável quando a conversa já tem contexto próprio e o documento chega depois. O erro a
evitar é o modelo "resetar" para o documento e perder o que já foi construído no chat.

## Precedência

1. Mensagem atual do usuário.
2. Contexto vivo deste chat.
3. Repositório — estado do código.
4. Documento — intenção, decisão, motivo.

Regra geral: **recência vence sobre estado; documento vence sobre intenção.** O código de
hoje diz o que existe; o documento diz por que existe daquele jeito.

## Diff, item a item

Para cada informação do documento, classifique antes de aplicar:

| Classe | Teste | Ação |
|---|---|---|
| **Nova** | Não aparece no chat nem no código já visto aqui | Aplica. Sem cerimônia. |
| **Idêntica** | Já estabelecida no chat, mesmo teor | Ignora. Não repete, não confirma, não reexplica. |
| **Refinada** | Chat tem versão vaga, documento tem versão precisa (caminho exato, critério de aceite, motivo) | Aplica a versão do documento como detalhamento. |
| **Desatualizada** | Chat ou código já avançou além | Mantém o do chat. Nota mental para atualizar via `context-out` no fim. |
| **Conflitante** | Contradição direta e as duas são plausíveis | Não escolha em silêncio. Uma linha ao usuário com as duas versões e a que você vai seguir por padrão (chat). |

Aplicar significa usar daqui pra frente. Não significa anunciar item por item — a confirmação
final é de ~8 linhas.

## Conflitos típicos

**Decisão técnica divergente.** Documento diz cookie httpOnly; o chat decidiu localStorage.
Chat vence (mais recente), mas o documento pode carregar o motivo que o chat não tinha — se o
bloco `D<n>` traz risco concreto (XSS, breaking change, custo), traga esse motivo ao usuário
em uma linha antes de seguir. Ele pode não ter tido a informação.

**Pendência já feita.** Documento lista pendência que este chat já resolveu. Não refaça.
Confirme pelo código (`git status`, `git diff`), não pela memória. Marque como resolvida na
confirmação.

**Arquivo citado não existe.** Renomeado, movido ou nunca criado. Procure pelo nome antigo
(`git log --diff-filter=D --name-only`, busca por símbolos). Achou o sucessor: use e registre
a divergência. Não achou: vira pendência de verificação, não suposição.

**Documento mais novo que o chat.** Outra ferramenta trabalhou em paralelo e gravou depois do
início desta conversa (`atualizado_em` > início do chat, ou commits novos). Aí o documento é o
lado recente: adote-o para o que ele cobre e avise o usuário que houve trabalho paralelo.

**Dois documentos para a mesma task.** Duplicata de handoff. Leia os dois, siga o de
`atualizado_em` maior, e avise: convém unificar via `context-out` para não bifurcar de novo.

## Staleness — quando desconfiar

Indicadores de documento velho, em ordem de peso:

1. Commits depois de `atualizado_em` tocando os arquivos citados.
2. `git status` com trabalho não commitado que o documento não menciona.
3. Arquivo citado inexistente.
4. Dependência/comando descrito que não existe mais (`package.json`, scripts).

Um indicador: siga com atenção. Dois ou mais: pare, reporte o que está fora de sincronia e
pergunte se continua pelo documento ou reconstrói pelo código.

Indicador 1 ou 2 **junto com `bastao:` de outro chat** não é só documento velho: é sessão
cortada. Procedimento próprio no Passo 2 da skill (reconstruir pelo git, tratar como estado,
registrar `ciclo não gravado` na confirmação).

## Conflito entre ciclos do próprio documento

A cadeia pode se contradizer sozinha — é normal em task longa, e a regra é simples: **ciclo mais
recente vence sobre ciclo antigo**, com três exceções.

| Situação | Resolução |
|---|---|
| D2 (ciclo 1) contradiz D5 (ciclo 4) | vale D5. D2 deveria estar `~~supersedida~~`; se não estiver, siga D5 e aponte a inconsistência. |
| Correção `aplicada no ciclo 4` e a revisão do ciclo 5 reabre | vale a reabertura: a tentativa não resolveu. Leia o que faltou antes de repetir a mesma abordagem. |
| Correção `recusada` num ciclo e cobrada de novo em outro | **exceção**: não reaplique por conta própria. O motivo da recusa continua valendo até alguém derrubá-lo. Traga ao usuário. |
| Decisão marcada `**Decisão do usuário**` num ciclo antigo, contrariada por ciclo técnico posterior | **exceção**: a decisão do usuário vence. Aponte o conflito. |
| Pendência antiga que nenhum ciclo posterior menciona | **exceção**: continua aberta. Silêncio não fecha pendência. |

Ciclo posterior que simplesmente ignora uma decisão anterior — sem supersedê-la — não é
revogação: é provável esquecimento. Aponte, não replique.

## Agentes em paralelo (Antigravity Agent Manager, abas do Cursor)

Vários agentes trabalhando no mesmo repositório ao mesmo tempo: o documento pode mudar **durante**
esta sessão, sem aviso.

- Antes de começar uma pendência longa, confira `atualizado_em` e `ciclo`. Mudaram: releia antes de
  executar — pode ter entrado um ciclo de revisão com correções que mudam o que você ia fazer.
- Pendência que some do documento entre duas leituras: outro agente concluiu. Confirme pelo código
  antes de assumir; não refaça.
- Decisão nova aparecendo no meio da sessão: se contradiz o que você já implementou aqui, pare e
  reporte ao usuário — dois agentes divergindo no mesmo arquivo é problema dele resolver, não seu.
- Nunca grave em `.doc/` para "resolver" a divergência. Gravar é papel de `context-out`.

## Encerramento

Terminada a etapa, lembre o usuário, em uma linha, de rodar `context-out` — é o que fecha o ciclo e
mantém a cadeia. Vale sempre que houve trabalho: pendência resolvida, decisão nova, correção
aplicada ou recusada, achado de revisão, divergência encontrada.

Diga também o que o próximo ciclo espera: `próximo: revisar C4.1 e C4.2 (Cursor)`. Sem isso, quem
abrir o próximo chat não sabe qual papel assumir.

Não grave o documento por conta própria: gravar é papel de `context-out`.

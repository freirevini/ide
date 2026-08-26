# Tuning de recuperação (RAG)

**Antes de qualquer coisa: identifique o backend.** Os parâmetros abaixo pertencem a
produtos diferentes e não são intercambiáveis. Aplicar `tree_depth` em quem usa Vertex
AI Vector Search não é aproximação — é parâmetro inexistente.

Descubra pelo import e pelo tipo do objeto de configuração, não pelo nome da variável:

| Backend | Pista no código |
|---|---|
| `RagManagedDb` | `vertexai.preview.rag`, `RagCorpus`, `RagManagedDbConfig` |
| Vertex AI Vector Search | `MatchingEngineIndex`, `IndexEndpoint`, `aiplatform.MatchingEngine*` |
| Vertex AI Search | `discoveryengine`, `SearchServiceClient` |
| Outro (pgvector, Qdrant, Elastic...) | client próprio; nada abaixo se aplica |

Só otimize recuperação se a medição do Passo 2 mostrar que ela pesa no p95. Em
pipelines de avaliação de compliance, o agente 2 costuma dominar — e nesse caso todo
o conteúdo desta página é irrelevante para a latência total.

---

## RagManagedDb

**KNN é o padrão** e é busca **exata**: qualidade máxima de recuperação, custo que
cresce com o número de documentos. Para corpora pequenos (regras de compliance
tipicamente são poucas centenas ou poucos milhares de itens), KNN geralmente já é
rápido o bastante — trocar por ANN aí é otimização negativa, porque troca precisão de
recuperação por latência que você não estava pagando.

**ANN** é a busca aproximada. Parâmetros:

- **`tree_depth`** — aceita **somente 2 ou 3**. Use `2` para a ordem de 10 mil
  arquivos, `3` acima disso. Default `2`.
- **`leaf_count`** — default `500`. Recomendação: `10 * sqrt(nº de RagFiles)`.
  Com 10.000 arquivos: `10 * 100 = 1000`.

Requisitos operacionais do ANN, cada um já causou "o RAG parou de achar as regras":

1. `rebuild_ann_index=true` na configuração;
2. **um rebuild precisa rodar antes da primeira consulta** — índice recém-criado e
   ainda não reconstruído devolve resultado vazio ou degradado, sem erro claro;
3. **apenas 1 rebuild concorrente por projeto/região** — dois deployments simultâneos
   se atropelam;
4. após ingestão significativa de novos `RagFile`s, é preciso reconstruir de novo.

Consequência prática: ANN é decisão operacional, não flag. Se a superfície editável é
só o repositório, o rebuild precisa ser uma chamada explícita no código de setup/
migração, e alguém precisa saber que ela existe.

---

## Vertex AI Vector Search

Backend diferente, vocabulário diferente:

- **`leafNodeEmbeddingCount`** — default `1000`. Quantos embeddings por nó folha.
- **`leafNodesToSearchPercent`** — default `10`. Percentual de folhas visitadas por
  consulta. **Comece entre 5% e 10%.**

`leafNodesToSearchPercent` é o dial direto de latência × recall: reduzir acelera e
perde recall; aumentar faz o inverso. Ajuste **um** valor por vez e meça recall contra
o golden set de recuperação — não contra a impressão de que "as respostas parecem boas".

---

## Medir recuperação separado do veredito

Erro comum: avaliar mudança de RAG pelo veredito final. O veredito depende do agente 2,
então uma regressão de recuperação pode ser mascarada por um agente 2 que acertou por
outro caminho — e o contrário também.

Meça os dois níveis:

1. **Recall de recuperação** — para um conjunto de peças com as regras relevantes
   anotadas à mão, quantas das regras corretas apareceram no top-k?
2. **Acurácia do veredito** — o golden set completo (`scripts/golden_set.py`).

Um ganho de latência que derruba (1) mas ainda passa em (2) é uma bomba-relógio: a
próxima peça de fronteira é a que vai falhar.

## Outras alavancas antes de mexer no índice

Costumam pagar mais e arriscar menos:

- **`top_k` menor** — menos regras injetadas significa menos tokens de entrada no
  agente 2, que é onde o custo está. Mas cuidado: `top_k` variável quebra o prefixo
  cacheável (ver `caching.md`).
- **Filtro por metadado** antes da busca vetorial (categoria de peça, canal, produto),
  quando as regras são parametrizadas por essas dimensões. Reduz o espaço de busca sem
  tocar em parâmetro de índice.
- **Cachear a recuperação** para peças da mesma categoria — se as mesmas regras saem
  para todas as peças de um tipo, a consulta vetorial por peça é trabalho repetido.

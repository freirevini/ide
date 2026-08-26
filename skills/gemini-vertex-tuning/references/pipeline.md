# Orquestração dos dois agentes

Alavancas de latência que não tocam no modelo nem no prompt — portanto, sem risco de
precisão. Aplique antes de qualquer coisa que mexa em thinking ou em model id.

## Paralelizar o que é independente

Encadeamento típico e desnecessário:

```
extrair texto → agente 1 (classifica) → consulta RAG → agente 2 (avalia)
```

A consulta ao RAG normalmente **não depende** da classificação do agente 1 — depende da
categoria da peça, do canal ou do produto, que vêm dos metadados. Quando for esse o
caso, o agente 1 e a recuperação rodam em paralelo e o p95 cai pelo tempo do menor dos
dois, de graça.

```python
import asyncio

async def avaliar(peca):
    tipo, regras = await asyncio.gather(
        classificar(peca),          # agente 1
        recuperar_regras(peca.meta) # RAG
    )
    return await julgar(peca, tipo, regras)  # agente 2
```

**Verifique a dependência antes de aplicar.** Se a consulta ao RAG usa o tipo de
arquivo devolvido pelo agente 1 para filtrar regras, a paralelização muda o
comportamento — e aí não é otimização, é bug.

Lote de peças: `asyncio.gather` com `Semaphore` para respeitar a cota. Sem semáforo, um
lote grande vira 429 e o retry destrói o ganho.

```python
sem = asyncio.Semaphore(8)  # calibre contra a cota real do projeto

async def limitado(peca):
    async with sem:
        return await avaliar(peca)

resultados = await asyncio.gather(*(limitado(p) for p in pecas))
```

## Cliente síncrono num caminho async

Erro comum: código `async def` chamando SDK síncrono. O event loop bloqueia e a
paralelização é ilusória — as chamadas serializam e a medição mostra ganho zero, o que
costuma ser diagnosticado como "o modelo é lento".

Use o cliente assíncrono do SDK. Se não houver, `asyncio.to_thread` como ponte:

```python
resp = await asyncio.to_thread(client.models.generate_content, **kwargs)
```

Confirme qual dos dois o repositório usa no Passo 0, item 5 — antes de propor
paralelização.

## Saída antecipada

Nem toda peça precisa do pipeline completo:

- extensão não suportada, arquivo corrompido, tamanho zero → rejeita antes de qualquer
  chamada ao modelo;
- classificação de altíssima confiança por extensão + magic bytes → o agente 1 pode ser
  dispensado para a maioria dos casos, sobrando só para o ambíguo;
- resultado idêntico já avaliado (hash do conteúdo) → cache de resultado.

Um cache de resultado por hash da peça + versão do conjunto de regras é o ganho mais
barato disponível quando há reenvio de peças, e é exato: mesma entrada, mesma saída.
A **versão das regras precisa entrar na chave**, senão mudança de regra não reavalia.

## Retry que não piora o p95

Retry cego multiplica a cauda. Regras:

- backoff exponencial **com jitter**;
- **só** para 429 e 5xx — 400 (schema, `thinking_level` conflitante) nunca melhora com
  repetição, só consome tempo;
- teto de tentativas e **deadline global** por peça: melhor devolver
  `revisao_humana` em tempo previsível do que travar a fila;
- `MAX_TOKENS` não é caso de retry — é caso de `maxOutputTokens` mal dimensionado
  (ver `modelos.md`). Repetir a mesma request dá o mesmo resultado.

## Streaming

Reduz **latência percebida**, não latência total, e só se o front consumir
incrementalmente. Com `responseSchema`, o JSON só é útil completo — streaming não ajuda
o veredito estruturado.

Onde ajuda: mostrar progresso por estágio na UI ("classificando", "recuperando regras",
"avaliando"). Isso é trabalho de BFF/front, não de tuning de modelo — mas costuma valer
mais para o usuário do que 300 ms a menos.

## Instrumentação

Sem isso, tudo acima é opinião. Emita por peça e por estágio:

| Campo | Por quê |
|---|---|
| `stage`, `duration_ms` | achar quem domina o p95 |
| `model` | comparar roteamento |
| `prompt_token_count` | custo de entrada |
| `candidates_token_count` | custo de saída |
| `thoughts_token_count` | dimensionar `maxOutputTokens` |
| `cached_content_token_count` | taxa de acerto de cache |
| `finish_reason` | pegar `MAX_TOKENS` silencioso |
| `retry_count` | separar latência de modelo de latência de retry |

`scripts/medir_latencia.py` fornece o context manager que emite esses eventos em JSONL
e o CLI que agrega em p50/p95/p99 e custo por estágio.

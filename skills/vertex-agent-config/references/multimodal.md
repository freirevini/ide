# Multimodal — entrada e geração

## `media_resolution` — a alavanca de qualidade da geração 3.x

A geração 3.x traz **`media_resolution`** com valores **`low`**, **`medium`** e **`high`**,
ajustável **por parte de mídia individual**. É o controle mais direto de qualidade de
percepção que esta skill tem.

Como usar sob o princípio "qualidade acima de custo":

- **`high` quando a regra depende de ler detalhe** — letra miúda, rodapé, disclaimer,
  número em tabela densa, assinatura.
- **`low` ou `medium` nas partes de contexto** que só situam a tarefa.
- Por parte significa que **não é decisão global**: a página com o rodapé crítico vai em
  `high` e as outras 40 páginas de anexo vão em `low`, na mesma request.

Reduzir resolução para economizar é exatamente o erro que essa granularidade evita:
economize nas partes que não carregam a regra, não na que carrega.

## O que a Vertex aceita como documento

**Document understanding aceita SOMENTE `application/pdf` e `text/plain`.**

`.docx`, `.pptx`, `.xlsx` **não são tipos de entrada** — precisam ser convertidos.

Outros MIME entram **como texto puro**, e aí **gráficos, diagramas e formatação se
perdem**. É perda silenciosa: a chamada funciona, a resposta vem, e o que sumiu não
aparece em lugar nenhum.

**Regra dura**: Office → PDF. **Nunca** Office → texto puro quando houver regra posicional
ou visual — a conversão para texto destrói exatamente a informação que a regra usa.

## PDF

| Item | Valor |
|---|---|
| Custo por página | **258 tokens** (fontes citam **~560 tokens/página** conforme a resolução) |
| Página grande | reduzida a no máximo **3072×3072**, preservando proporção |
| Página pequena | ampliada a **768×768** |
| Páginas por arquivo | **1.000** (confirme: material da geração anterior citava 3.000) |
| Tamanho por arquivo (GCS) | **50 MB** |
| Tamanho no console | **7 MB** |
| Documentos por prompt | até **3.000** |

**"OCR for scanned PDFs: Not used by default"** na Vertex. PDF escaneado é lido como
imagem, sem camada de texto. Prefira **PDF com texto renderizado como texto**. Se só
houver escaneado, faça OCR antes ou aceite explicitamente a perda — e registre a decisão,
porque ela explica erros futuros.

Onde as fontes divergem (tokens por página, páginas por arquivo), **confirme na
documentação oficial** antes de dimensionar custo ou fatiamento.

## Imagens de entrada

| Item | Valor |
|---|---|
| Imagens por prompt | até **3.000** |
| Inline | **7 MB** |
| Via GCS | **30 MB** |

Qualidade da imagem:

- **Gire** para a orientação correta antes de enviar.
- **Evite borrão.**
- **Use `media_resolution=high`** quando a regra depende de ler letra miúda. É preferível a
  aumentar o arquivo: o controle é o parâmetro, não o upload.

## Ordem das partes

**Mídia ANTES do texto** quando há **uma** mídia (uma página, uma imagem, um vídeo).

Com **múltiplas imagens**, **rotule cada uma** e **referencie pelos rótulos**:

```
imagem 1: <bytes>   media_resolution=high
imagem 2: <bytes>   media_resolution=low
imagem 3: <bytes>   media_resolution=high

Compare o rodapé da imagem 1 com o da imagem 3. A imagem 2 é a versão anterior.
```

Sem rótulos, "a segunda imagem" é ambíguo para o modelo e para quem lê o prompt depois.

## Vídeo

- **Vídeo antes do texto.**
- Áudio em blocos de **1s a 32 tokens**.
- **Referencie momentos em `MM:SS`.**

Para transcrição dedicada existe **`gemini-3.5-transcribe`** (GA) — não force um modelo de
raciocínio a fazer trabalho de transcrição.

---

## Geração de imagem — linha Nano Banana

| Model id | Nome | Resoluções | Tokens de saída |
|---|---|---|---|
| `gemini-3-pro-image` | **Nano Banana Pro** | 512px, 1K (default), 2K, 4K | **1120** (1K e 2K), **2000** (4K) |
| `gemini-3.1-flash-image` | **Nano Banana 2** | 512px, 1K (default), 2K, 4K | **747** (512px), **1120** (1K), **1680** (2K), **2520** (4K) |
| `gemini-3.1-flash-lite-image` | — | **somente 1K** | — |

Preço do **`gemini-3-pro-image`** na Vertex: **$3,00 / $15,00 por 1M tokens**, ou
**$0,134 por imagem 1K/2K** e **$0,24 por imagem 4K**. Em batch/flex (entrega
assíncrona): **$0,067 por imagem 2K** — metade.

### Como escolher

- **`gemini-3.1-flash-image` (Nano Banana 2)** é o **generalista** — default para a
  maioria das tarefas de geração e edição.
- **`gemini-3-pro-image` (Nano Banana Pro)** quando a qualidade de renderização for o
  critério, em especial **texto dentro da imagem**, onde é o mais forte da linha.
- **`gemini-3.1-flash-lite-image`** só entrega 1K — não sirva a ele tarefa que precise de
  2K ou 4K.

### SynthID

Toda imagem gerada ou editada carrega **marca d'água invisível SynthID** identificando-a
como gerada por IA. No `gemini-3.1-flash-lite-image` é *always on*.

Não é opcional, não é removível, e **não deve ser tratada como obstáculo** — é
proveniência. Se o caso de uso depende de a imagem não ser identificável como gerada por
IA, o caso de uso é o problema, não a marca d'água.

### Escolha de resolução

1K é o default. Suba para 2K ou 4K quando a imagem for ser ampliada, impressa ou
inspecionada em detalhe — o custo por imagem sobe de $0,134 para $0,24, e no Nano Banana 2
os tokens vão de 1120 para 2520.

## Limitações documentadas

Características do modelo, não bug a contornar com prompt:

- **Raciocínio espacial impreciso** — contagens saem aproximadas. Não construa regra que
  dependa de contagem exata de elementos visuais.
- **Alucinação em manuscrito** — texto à mão gera invenção com aparência de leitura.
- **Recusa por moderação** — conteúdo legítimo pode ser recusado; tenha fallback.
- **Não serve para identificar pessoas não-públicas.**
- **Não serve para imagens médicas.**

## Diagnóstico quando o multimodal falha

Antes de mexer no prompt de tarefa, **peça ao modelo que DESCREVA a mídia**.

Separa **falha de percepção** (o modelo não está vendo o que você acha) de **falha de
raciocínio** (vê certo e conclui errado). Correções diferentes:

- não viu → `media_resolution=high`, orientação, conversão, OCR;
- viu e errou → instrução, `thinking_level`, modelo.

Pular esse passo leva a semanas ajustando prompt de raciocínio para um problema de
resolução.

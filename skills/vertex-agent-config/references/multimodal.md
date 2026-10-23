# Multimodal — entrada e geração

Verificado em 2026-10-23 nas páginas "Document understanding", "Image understanding", "Get
started with Gemini 3" e nas páginas de modelo da Vertex. Modelos de imagem: tabela única em
`modelos.md`.

## `media_resolution` — a alavanca de qualidade da geração 3.x e 4

Valores: **`LOW`**, **`MEDIUM`**, **`HIGH`** e **`ULTRA_HIGH`**. Os três primeiros valem no
`generation_config` (todas as mídias da request) ou **por parte**; `ULTRA_HIGH` só por parte.
A configuração da parte **sobrescreve** a global.

| Mídia | LOW | MEDIUM | HIGH | ULTRA_HIGH |
|---|---|---|---|---|
| Imagem | 280 tokens | 560 | 1.120 | 2.240 |
| PDF (por página, mais o texto) | 280 | **560 (default)** | 1.120 | — |
| Vídeo (por frame) | 70 | 70 | 280 | — |

Forma no SDK: `types.Part(file_data=..., media_resolution=types.PartMediaResolution(level="MEDIA_RESOLUTION_HIGH"))`.

Como usar sob o princípio "qualidade acima de custo":

- **`HIGH`** (ou `ULTRA_HIGH` na parte) quando a regra depende de ler detalhe: letra miúda,
  rodapé, disclaimer, número em tabela densa, assinatura.
- **`LOW` ou `MEDIUM`** nas partes de contexto que só situam a tarefa.
- Por parte significa que **não é decisão global**: a página com o rodapé crítico vai em `HIGH`
  e as outras 40 páginas de anexo vão em `LOW`, na mesma request.
- Entrada muito longa pode exigir `LOW` para caber na janela; nesse caso diga qual regra
  perdeu fidelidade.

Reduzir resolução para economizar é exatamente o erro que essa granularidade evita: economize
nas partes que não carregam a regra, não na que carrega.

## O que a Vertex aceita como documento

**Document understanding aceita SOMENTE `application/pdf` e `text/plain`** (confirmado
2026-10-23; nenhuma menção a DOCX, XLSX ou PPTX).

`.docx`, `.pptx`, `.xlsx` **não são tipos de entrada** — precisam ser convertidos. Outros MIME
entram **como texto puro**, e aí **gráficos, diagramas e formatação se perdem**. É perda
silenciosa: a chamada funciona, a resposta vem, e o que sumiu não aparece em lugar nenhum.

**Regra dura**: Office → PDF. **Nunca** Office → texto puro quando houver regra posicional ou
visual — a conversão para texto destrói exatamente a informação que a regra usa.

## PDF

| Item | Valor (4 Argon, 3.8, 3.7, 3.6, 3.5, 3.5-lite, 3.1-lite, 3.1 Pro preview) |
|---|---|
| Tokens por página | **280 / 560 / 1.120** conforme `media_resolution` (default MEDIUM = 560), mais o texto |
| Páginas por arquivo | **3.000** |
| Arquivos por prompt | **3.000** (até 100 URIs) |
| Tamanho por arquivo (API ou GCS) | **50 MB** para PDF; **7 MB** para texto |
| Upload pelo console | **7 MB** |
| Divergência registrada | a seção REST da mesma página diz "documentos não podem exceder 15 MB" |

Modelos de imagem (Nano Banana) aceitam PDF limitado pelo próprio contexto (131.072 ou 65.536).

**OCR**: a nota "OCR for scanned PDFs: Not used by default" aparece nas linhas do 3.1 Pro
preview e do 3 Flash preview; para os demais a página não afirma nada. Trate como **sem
garantia de OCR em nenhum modelo**: PDF escaneado é lido como imagem. Prefira PDF com texto
renderizado como texto. Se só houver escaneado, faça OCR antes ou aceite explicitamente a
perda — e registre a decisão, porque ela explica erros futuros.

## Imagens de entrada

| Item | Valor |
|---|---|
| Imagens por prompt | até **3.000** (até 100 URIs) |
| Inline ou console | **7 MB** |
| Via GCS | **30 MB** |
| Formatos | PNG, JPEG, WebP, HEIC, HEIF |

Qualidade: **gire** para a orientação correta antes de enviar; **evite borrão**; use
`media_resolution=HIGH` (ou `ULTRA_HIGH` na parte) quando a regra depende de ler letra miúda.
O controle é o parâmetro, não o upload.

## Vídeo e áudio

- Vídeo: até **10 por prompt**; cerca de **45 min com áudio** ou **1 h sem**. Vídeo antes do
  texto; referencie momentos em `MM:SS`. Tokens por frame conforme `media_resolution`.
- Áudio: **1 arquivo por prompt**, até cerca de **8,4 h** (1M tokens).
- Transcrição dedicada: **`gemini-3.5-transcribe`** (GA). Não force um modelo de raciocínio a
  fazer trabalho de transcrição.
- 4 Argon: "agentic video understanding" GA, **desligado por padrão** (`media_processing="static"`).

## Ordem das partes

**Mídia ANTES do texto** quando há **uma** mídia (uma página, uma imagem, um vídeo).

Com **múltiplas imagens**, **rotule cada uma** e **referencie pelos rótulos**:

```
imagem 1: <bytes>   media_resolution=HIGH
imagem 2: <bytes>   media_resolution=LOW
imagem 3: <bytes>   media_resolution=HIGH

Compare o rodapé da imagem 1 com o da imagem 3. A imagem 2 é a versão anterior.
```

Sem rótulos, "a segunda imagem" é ambíguo para o modelo e para quem lê o prompt depois.

---

## Geração de imagem — linha Nano Banana

Ids, estágio, resoluções, tokens por imagem, proveniência e parâmetros rejeitados: tabela em
`modelos.md`. Resumo de escolha:

- **`gemini-nano-banana-2.1`** é o **generalista** (GA 2026-10-06): 1K default, 2K, 4K; até 14
  imagens de entrada por prompt; só endpoint `global`; rejeita `seed`, `temperature`, `topP`,
  `topK` com erro.
- **`gemini-3-pro-image`** (Nano Banana Pro) quando o 2.1 não bastar em texto dentro da imagem.
- **`gemini-3.1-flash-image`** (Nano Banana 2) está depreciado na Gemini API; não use em
  projeto novo.
- **`gemini-3.1-flash-lite-image`** só entrega 1K.

### Proveniência

Toda imagem gerada ou editada carrega marca de proveniência: **C2PA Content Credentials** na
página do 2.1; **SynthID** nas páginas anteriores do Pro e do Lite. Não é opcional, não é
removível e **não deve ser tratada como obstáculo**. Se o caso de uso depende de a imagem não
ser identificável como gerada por IA, o caso de uso é o problema, não a marca.

### Escolha de resolução

1K é o default. Suba para 2K ou 4K quando a imagem for ampliada, impressa ou inspecionada em
detalhe. O custo por imagem sobe de $0,134 para $0,24 (linha mantida da versão anterior; vale
para o `gemini-3-pro-image`); no 2.1 os tokens vão de 1.120 (1K) para 3.780 (4K).

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

- não viu → `media_resolution` mais alta na parte, orientação, conversão, OCR;
- viu e errou → instrução, `thinking_level`, modelo.

Pular esse passo leva a semanas ajustando prompt de raciocínio para um problema de resolução.

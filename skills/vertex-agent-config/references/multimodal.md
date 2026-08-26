# Entrada multimodal

## O que a Vertex aceita como documento

**Document understanding aceita SOMENTE `application/pdf` e `text/plain`.**

`.docx`, `.pptx`, `.xlsx` **não são tipos de entrada** — precisam ser convertidos.

Outros MIME types entram **como texto puro**, e aí **gráficos, diagramas e formatação se
perdem**. É uma perda silenciosa: a chamada funciona, a resposta vem, e o que sumiu não
aparece em lugar nenhum.

**Regra dura**: Office → PDF. **Nunca** Office → texto puro quando houver regra
posicional ou visual — a conversão para texto destrói exatamente a informação que a
regra usa.

## PDF

| Item | Valor |
|---|---|
| Custo por página | **258 tokens** |
| Página grande | reduzida a no máximo **3072×3072** |
| Página pequena | ampliada a **768×768** |
| Resolução maior | **sem ganho de qualidade** |
| Resolução menor | **sem desconto** |
| Arquivos por prompt (Vertex 2.5) | até **3.000** |
| Páginas por arquivo | até **3.000** |
| Tamanho por arquivo (API/GCS) | **50 MB** |
| Tamanho no console | **7 MB** |
| Resolução padrão | **560 tokens** |

**"OCR for scanned PDFs: Not used by default"** na Vertex. Consequência: PDF escaneado é
lido como imagem, sem camada de texto. Prefira **PDF com texto renderizado como texto**.
Se só houver escaneado, faça OCR antes ou aceite explicitamente a perda — e registre essa
decisão, porque ela explica erros futuros.

Como não há desconto por resolução menor nem ganho por resolução maior, **não faça
downscale para economizar**: só perde informação.

## Imagens

| Item | Valor |
|---|---|
| Imagens por prompt (Vertex 2.5) | até **3.000** |
| Inline | **7 MB** |
| Via GCS | **30 MB** |
| Resolução padrão | **1120 tokens** |
| Ambas dimensões ≤ 384px | **258 tokens** |
| Acima disso | tiles de **768×768** a **258 tokens** cada |

### Qualidade da imagem

- **Gire** páginas e imagens para a orientação correta antes de enviar.
- **Evite borrão.**
- **Use resolução alta.** Quando a regra depende de ler letra miúda — rodapé,
  disclaimer, nota de rodapé —, reduzir a imagem quebra a leitura. E, de novo: não há
  desconto por reduzir.

## Ordem das partes

**Mídia ANTES do texto** quando há **uma** mídia (uma página, uma imagem, um vídeo).

Com **múltiplas imagens**, **rotule cada uma** e **referencie pelos rótulos** na
instrução:

```
imagem 1: <bytes>
imagem 2: <bytes>
imagem 3: <bytes>

Compare o rodapé da imagem 1 com o da imagem 3. A imagem 2 é a versão anterior.
```

Sem rótulos, "a segunda imagem" é ambíguo para o modelo e para quem lê o prompt depois.

## Vídeo

- **Vídeo antes do texto.**
- Áudio em blocos de **1s a 32 tokens**.
- **Referencie momentos em `MM:SS`.**

## Limitações documentadas

Trate como características do modelo, não como bug a contornar com prompt:

- **Raciocínio espacial impreciso** — contagens saem aproximadas. Não construa regra que
  dependa de contagem exata de elementos visuais.
- **Alucinação em manuscrito** — texto à mão gera invenção com aparência de leitura.
- **Recusa por moderação** — conteúdo legítimo pode ser recusado; tenha caminho de
  fallback.
- **Não serve para identificar pessoas não-públicas.**
- **Não serve para imagens médicas.**

## Diagnóstico quando o multimodal falha

Antes de mexer no prompt de tarefa, **peça ao modelo que DESCREVA a mídia**.

Isso separa **falha de percepção** (o modelo não está vendo o que você acha que está)
de **falha de raciocínio** (ele vê corretamente e conclui errado). São problemas
diferentes com correções diferentes:

- não viu → resolução, orientação, conversão, OCR;
- viu e errou → instrução, thinking, modelo.

Pular esse passo leva a semanas ajustando prompt de raciocínio para um problema de
resolução de imagem.

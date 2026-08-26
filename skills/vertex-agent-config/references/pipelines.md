# Pipelines de múltiplos agentes

## Uma responsabilidade por agente

Um agente que **classifica** não julga. Um agente que **julga** não reclassifica.

Teste prático: se a descrição da função do agente precisa de um "e" para caber, são dois
agentes. "Classifica o tipo de arquivo **e** avalia contra as regras" são duas
responsabilidades, com perfis, modelos e thinking diferentes.

Caso de referência:

| Agente | Função | Perfil | Recebe | Entrega |
|---|---|---|---|---|
| 1 | classificar o arquivo | `classificacao` | arquivo bruto | tipo + metadados + texto extraído |
| 2 | avaliar contra regras | `avaliacao-regras` | saída estruturada do 1 (+ mídia, se a regra for visual) | veredito + evidências |

## Contrato de comunicação

**JSON com schema explícito, versionado.** O agente seguinte valida o que recebe.

```json
{
  "contrato_versao": "1.2.0",
  "tipo_arquivo": "pdf_texto",
  "paginas": 12,
  "texto_extraido": "...",
  "observacoes": [
    {"pagina": 12, "regiao": "inferior_direita", "descricao": "texto de ~6pt"}
  ],
  "midia_original_uri": "gs://bucket/doc.pdf"
}
```

Por que versionar: contrato implícito quebra em silêncio quando um dos lados muda. Com
`contrato_versao`, o agente 2 recusa explicitamente o que não sabe ler, em vez de
interpretar campo faltante como ausência de achado.

## Regra antirredundância

**O agente N+1 nunca refaz extração ou OCR já feita pelo agente N.** Recebe o resultado
estruturado.

Refazer custa latência e — pior — produz **duas leituras divergentes do mesmo documento**
sem ninguém decidir qual vale. Quando as duas discordam, o sistema não tem critério de
desempate e escolhe a última por acidente de implementação.

## Exceção crítica: regra posicional ou visual

Quando a regra a avaliar depende de **posição, layout ou aparência** — letra miúda,
rodapé, disclaimer próximo ao preço, proporção entre elementos, cor —, o agente avaliador
precisa da **mídia original além do texto extraído**.

Passar só o resumo do agente anterior **perde fidelidade exatamente onde a regra mora**.
O texto extraído diz *o que* está escrito; a regra pergunta *como* e *onde* está escrito.

Decida isso na Etapa 2 do framework, com a pergunta sobre dependência de posição/layout.
Na prática, o contrato leva os dois: `texto_extraido` **e** `midia_original_uri`.

Custo dessa exceção: o agente 2 volta a pagar os 258 tokens por página. É o preço de
poder avaliar a regra — e cai no princípio norteador da skill: qualidade acima de custo.

## Nunca passar interpretação como fato

O agente N+1 recebe **observações e evidências**, não **conclusões**.

| Passar | Não passar |
|---|---|
| "rodapé com texto de ~6pt na região inferior direita da página 12" | "disclaimer inadequado" |
| "não foi encontrado texto contendo 'prazo' nas páginas 1–12" | "peça sem informação de prazo" |
| "valor 'R$ 18.500,00' aparece na página 3, linha 7" | "valor compatível com a faixa" |

Motivo: conclusão que entra como fato de entrada **não pode ser contestada** pelo agente
seguinte — ele só herda o erro, e o erro ganha a autoridade de ter vindo "do sistema".
Observação pode ser reavaliada; conclusão, não.

Isso vale inclusive quando o agente 1 está quase sempre certo. O ponto não é a taxa de
acerto: é preservar a possibilidade de revisão.

## Escalonamento

Cada agente precisa de um **critério explícito de escalonamento** — quando passa o caso
adiante ou para uma pessoa. Sem isso, o agente força uma resposta em caso ambíguo, e
ambiguidade forçada é onde os erros caros aparecem.

Defina na Etapa 3 da configuração, e deixe o critério no schema de saída (um valor de
resultado do tipo "indeterminado" / "revisão humana"), não só no código.

## Chunking

Fatiar documento longo gera **um veredito por fatia**. Regra que depende do documento
inteiro — "existe disclaimer em algum lugar", "o total confere com a soma das páginas" —
vira N respostas parciais, cada uma olhando um pedaço, nenhuma podendo responder a
pergunta.

**Decida a estratégia de agregação antes de fatiar**, e verifique se cada regra é
respondível por fatia. As que não forem precisam de outra abordagem: documento inteiro
num modelo de contexto grande, ou uma passada de agregação sobre os resultados parciais.

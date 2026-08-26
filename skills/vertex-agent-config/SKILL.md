---
name: vertex-agent-config
description: Configura agentes Gemini na Vertex AI priorizando assertividade e qualidade da avaliação acima de custo — escolhe modelo, thinking, temperature, responseSchema, ordem das partes multimodais, tratamento por tipo de arquivo e estratégia de cache, e desenha pipelines de múltiplos agentes com contrato explícito entre eles. Entende o projeto antes de sugerir, pergunta o que faltar e segue a decisão final do usuário sobre modelo. Use quando pedirem "configurar agente Vertex", "qual modelo Gemini usar", "melhorar a precisão do agente", "criar novo agente", "desenhar pipeline de agentes", "ajustar temperature", "ajustar thinking", "o agente está errando na leitura do PDF" ou "como passar imagem/planilha para o Gemini".
---

# Vertex Agent Config — configurar para acertar

## Princípio norteador

**Qualidade e assertividade da avaliação acima de custo.** Custo entra como
*informação* ao lado da recomendação, nunca como critério de decisão.

A única exceção é o usuário pedir explicitamente para otimizar custo. Aí sim, apresente
o trade-off — e diga o que se perde, não só o que se economiza.

Corolário: **nunca proponha reduzir qualidade para economizar**. E, do outro lado,
**nunca discuta depois que o usuário escolher o modelo** — adapte a configuração ao que
ele escolheu e siga.

---

## Passo 0 — entender antes de sugerir (obrigatório)

Não emita configuração nenhuma antes de completar isto:

1. **Arquitetura de agentes existente** — quantos agentes, a função de cada um, como se
   comunicam, onde está a orquestração.
2. **Model ids já configurados** — quais são e em que arquivo/env var.
3. **Tipos de arquivo realmente processados** — e **onde acontece a conversão/extração**
   de cada um.
4. **O que já existe** — cache de contexto, `responseSchema`, configuração de thinking.
5. Qualquer um desses pontos que não puder ser determinado: **PERGUNTE ao usuário**.
   Não assuma.

`python scripts/inspecionar_agentes.py <raiz_do_projeto>` faz o primeiro passe e imprime
model ids, locations, tipos de arquivo tratados e presença de schema/thinking/cache. É
heurístico — confirme lendo o código.

Configuração sugerida sem o Passo 0 completo é chute com aparência de recomendação. Não
faça.

### Se o usuário não quiser responder

Ele pode ter pressa, ou não saber. Não insista e não trave: **assuma explicitamente e
marque a suposição**.

> Assumindo PDF com texto renderizado e saída para revisão humana. Se algum desses dois
> for diferente, a configuração muda — me avise e eu ajusto.

Suposição declarada é revisável; suposição silenciosa vira erro de produção que ninguém
consegue rastrear até a decisão que o causou.

---

## Framework de decisão

### Etapa 1 — classificar o objetivo

Encaixe o que o usuário descreveu em **um** perfil:

| Perfil | O que caracteriza |
|---|---|
| `triagem` | rotear/decidir o próximo passo; erro é recuperável a jusante |
| `classificacao` | atribuir rótulo de um conjunto fechado |
| `extracao` | tirar campos estruturados de um documento |
| `avaliacao-regras` | julgar conteúdo contra regras multicamada, com justificativa |
| `alto-risco` | decisão com consequência difícil de reverter |
| `documento-longo` | contexto grande domina a tarefa |
| `criativo` | geração aberta, sem resposta única correta |

Se dois perfis parecerem caber, **é sinal de que são dois agentes** — veja "Desenho de
múltiplos agentes".

### Etapa 2 — perguntar só o que muda a configuração

**Perguntas abertas, no máximo três por vez.** Só as lacunas que efetivamente alteram a
saída da Etapa 3. Não pergunte o que o Passo 0 já respondeu.

O repertório (escolha as que importam para o caso):

- Qual tipo de arquivo predomina, e ele chega como PDF com texto ou escaneado?
- O resultado vai para uma pessoa decidir ou dispara uma ação automática?
- Qual erro custa mais: aprovar indevidamente ou reprovar indevidamente?
- Qual a tolerância a latência por item?
- O conjunto de regras é fechado e finito, ou aberto e crescente?
- Qual o volume esperado por dia?
- Alguma regra depende de **posição, layout ou aparência** (letra miúda, rodapé,
  proximidade entre elementos)?

A última é a que mais gente esquece e a que mais muda a configuração — decide se o
avaliador precisa da mídia original ou basta o texto extraído.

### Etapa 3 — emitir a configuração completa

Entregue tudo, não só o modelo:

1. **Modelo** — com a linha 3.x como preferencial e o equivalente 2.5 quando o deploy
   só liberar essa família.
2. **Thinking** — `thinking_level` (3.x) ou `thinking_budget` (2.5). Nunca os dois.
3. **Temperature** — marcando explicitamente quando o modelo **ignora** o parâmetro.
4. **`responseSchema`** — exigindo evidência, não só o resultado.
5. **`maxOutputTokens`** — dimensionado como thinking + resposta.
6. **`seed`** — quando a avaliação precisa ser auditável/reprodutível.
7. **Ordem das partes multimodais** — mídia antes do texto; rótulos quando há várias.
8. **Tratamento por tipo de arquivo** — onde converte, para quê, e o que se perde.
9. **Cache de contexto** — o que é prefixo estável.
10. **Critério de escalonamento** — quando este agente passa o caso adiante ou para uma
    pessoa.

`python scripts/gerar_config.py --perfil <perfil> --modelo <model_id>` imprime o bloco
`GenerateContentConfig` e marca o que o modelo escolhido ignora.

**Encerre sempre com esta linha** (ou equivalente):

> Se preferir outro modelo, digo qual configuração equivalente usar — a escolha é sua.

E, quando o usuário escolher, **adapte e siga**. Não reargumente.

---

## Determinismo por system instruction

Nos flash 3.5-lite / 3.6 / 3.7, `temperature`, `topP` e `topK` são ignorados — o controle
de variabilidade migra inteiro para a *system instruction*. Não é o mesmo trabalho com
outro nome: parâmetro estreitava a amostragem, instrução precisa **descrever o
comportamento**.

O que colocar, em ordem de efeito:

1. **Formato exato da saída** — junto com `responseSchema`, não no lugar dele.
2. **Critério de decisão**, explícito e ordenado. "Se A e B, então X; se só A, então Y."
   Critério implícito é onde a variabilidade entra.
3. **O que fazer em caso de ambiguidade** — nomeie o valor de saída para o caso
   indeterminado. Sem isso o modelo escolhe, e escolhe diferente a cada vez.
4. **O que NÃO inferir** — "não deduza informação ausente; devolva campo nulo com o
   motivo". Cobre a maior fonte de variação em extração.

Um agente configurado assim varia menos entre execuções do que um com `temperature` baixa
— e continua raciocinando, que é o que a temperature baixa quebrava.

---

## Cache de contexto

Item 9 da Etapa 3. A regra é estrutural: **o que é estável vem primeiro, o que varia vem
depois**.

```
system instruction ......... estável  ─┐
regras / parâmetros ........ estável   ├─ prefixo candidato a cache
exemplos ................... estável  ─┘
──────────────────────────────
metadados do item .......... variável
conteúdo do item ........... variável
```

O que quebra o cache sem parecer que quebra: timestamp ou id de sessão no prefixo, regras
concatenadas em ordem não determinística (ordene antes de serializar), `json.dumps` sem
`sort_keys=True`.

**Confirme na documentação da Vertex** os mínimos de token, o TTL e o desconto vigentes
antes de dimensionar — esta skill não fixa esses números.

Feliz coincidência: essa mesma ordem é a que isola conteúdo não confiável do prompt do
sistema. Cache e segurança pedem o mesmo layout.

---

## Tabela objetivo → modelo → thinking

| Perfil | Linha 3.x (preferencial) | Linha 2.5 (legado) | Thinking | Temperature |
|---|---|---|---|---|
| `triagem` | `gemini-3.7-flash` | `gemini-2.5-flash` | `LOW` / budget `0` | 3.7-flash: **ignorada** · 2.5: `1.0` |
| `classificacao` | `gemini-3.7-flash` | `gemini-2.5-flash` | `LOW` a `HIGH` / `2048–8192` | idem |
| `extracao` | `gemini-3.7-flash` ou Pro 3.x | `gemini-2.5-pro` | `HIGH` / `8192+` | idem · use `seed` |
| `avaliacao-regras` | Pro 3.x | `gemini-2.5-pro` | `HIGH` / `16384+` | `1.0` |
| `alto-risco` | Pro 3.x | `gemini-2.5-pro` | `HIGH` / `32768` | `1.0` · use `seed` |
| `documento-longo` | Pro 3.x | `gemini-2.5-pro` | `HIGH` / `16384+` | `1.0` |
| `criativo` | Pro 3.x ou `gemini-3.7-flash` | `gemini-2.5-pro` | `HIGH` | `1.0` (default) |

Notas que mudam a decisão:

- **Temperature é alavanca só na linha 2.5.** Na 3.x, mantenha `1.0` — baixá-la pode
  causar loops e degradar raciocínio. Em `gemini-3.5-flash-lite`, `gemini-3.6-flash` e
  `gemini-3.7-flash`, `temperature`, `topK` e `topP` são **depreciados e ignorados**;
  determinismo se obtém por *system instruction*, não por parâmetro.
- **`gemini-2.5-pro` não desliga thinking** (faixa 128–32768). Só o Flash aceita `0`
  (faixa 0–24576). Flash-Lite não pensa por padrão (faixa 512–24576).
- **Pro da linha 3.x não aceita `MINIMAL`**; `MINIMAL` exige *thought signatures*.
- Confirme o id exato do Pro 3.x liberado no seu deploy antes de fixá-lo — não presuma.

Detalhes e faixas completas em `references/modelos.md` e `references/parametros.md`.

---

## Desenho de múltiplos agentes

### Uma responsabilidade por agente

Um agente que **classifica** não julga. Um agente que **julga** não reclassifica. Se a
Etapa 1 encaixou em dois perfis, são dois agentes.

### Contrato de comunicação

JSON com schema **explícito e versionado** entre agentes. O agente seguinte valida o que
recebe contra o schema; contrato implícito quebra em silêncio quando um dos lados muda.

### Regra antirredundância

O agente N+1 **nunca refaz** extração ou OCR já feita pelo agente N — recebe o resultado
estruturado. Refazer custa latência e, pior, produz duas leituras divergentes do mesmo
documento sem ninguém decidir qual vale.

### Exceção crítica à regra antirredundância

Quando a regra a avaliar for **posicional ou visual** — letra miúda, rodapé, disclaimer
próximo ao preço, proporção entre elementos —, o agente avaliador precisa da **mídia
original** além do texto extraído. Passar só o resumo do agente anterior perde
fidelidade exatamente onde a regra mora.

Decida isso na Etapa 2, com a pergunta sobre dependência de posição/layout.

### Nunca passar interpretação como fato

O agente N+1 recebe **observações e evidências**, não conclusões do agente N. "Rodapé
contém texto de 6pt na região inferior direita" é observação. "Disclaimer inadequado" é
conclusão — e, se entrar como fato de entrada, o agente seguinte não tem como
contestá-la; só herda o erro.

Mais em `references/pipelines.md`.

---

## Tratamento por tipo de arquivo

| Entrada | O que fazer | Por quê |
|---|---|---|
| `.pdf` (texto renderizado) | enviar direto | é um dos dois MIME aceitos |
| `.pdf` (escaneado) | OCR **antes**, ou aceitar perda | "OCR for scanned PDFs: Not used by default" |
| `.docx` `.pptx` `.xlsx` | **converter para PDF** | não são tipos de entrada aceitos |
| `.csv` / texto | `text/plain` | aceito |
| `.jpeg` `.png` | enviar direto, resolução alta | ver limites em `references/multimodal.md` |

**Document understanding na Vertex aceita SOMENTE `application/pdf` e `text/plain`.**
Outros MIME entram como texto puro — e aí **gráficos, diagramas e formatação se perdem**.

**Regra dura**: Office → PDF. **Nunca** Office → texto puro quando houver regra
posicional ou visual, porque a conversão para texto destrói justamente a informação que
a regra usa.

Números (páginas, tokens, limites de tamanho, ordem das partes) em
`references/multimodal.md`.

---

## Exemplo completo — pipeline de dois agentes

Pedido: *"tenho um sistema que recebe peças de marketing em vários formatos, classifica e
avalia contra regras de compliance. Quero melhorar a precisão."*

**Passo 0** revela: dois agentes, `gemini-2.5-flash` e `gemini-2.5-pro` (ids em
`app/agentes.py:4` e `:5`), formatos `.pdf .docx .pptx .xlsx .csv .jpeg .png`, sem sinal
de conversão, sem thinking configurado, sem cache. `temperature=0.0` no agente 1.

**Etapa 1**: dois perfis — `classificacao` (agente 1) e `avaliacao-regras` (agente 2).
Confirma que são dois agentes.

**Etapa 2**, três perguntas abertas:
1. Alguma regra depende de posição ou aparência — letra miúda, rodapé, proximidade entre
   elementos?
2. O veredito dispara uma ação automática ou vai para uma pessoa decidir?
3. Onde os `.docx` e `.xlsx` são convertidos hoje?

Respostas: sim, várias regras são de rodapé e letra miúda; vai para uma pessoa; a
conversão não existe — os Office vão como texto puro.

**Etapa 3**:

- **Achado que muda tudo antes de qualquer parâmetro**: Office indo como texto puro
  destrói posição e formatação, que é onde as regras moram. Converter para PDF é a
  correção de maior efeito neste caso — maior que qualquer ajuste de modelo.
- Agente 1 `gemini-2.5-flash`, `thinking_budget=4096`, `temperature=1.0` (o `0.0` atual
  não está ajudando), `responseSchema` devolvendo tipo + texto extraído + observações
  posicionais + URI da mídia original.
- Agente 2 `gemini-2.5-pro`, `thinking_budget=16384`, `max_output_tokens=32768`,
  `seed` fixo, `responseSchema` exigindo `regra_id` + trecho citado.
- **Agente 2 recebe a mídia original além do texto** — exceção à regra antirredundância,
  porque as regras são posicionais.
- Cache: system instruction + regras no prefixo estável; a peça por último.
- Escalonamento: `revisao_humana` quando a regra depender de julgamento de grau.
- Ids parametrizados, com a data de aposentadoria da 2.5 em comentário.

> Se preferir a linha 3.x, digo a configuração equivalente — a escolha é sua.

---

## Armadilhas

1. **`temperature=0` na linha 3.x.** Pode causar loop e degradar raciocínio. Mantenha
   `1.0`. Nos flash 3.5-lite/3.6/3.7 o parâmetro é simplesmente ignorado — quem "fixou"
   temperature ali acha que controlou algo e não controlou.
2. **Thinking conta contra `maxOutputTokens`.** Com `responseSchema`, estourar devolve
   `text=None` e `parsed=None` com `finishReason=MAX_TOKENS` — **sem exceção lançada**.
   Vira `TypeError` a jusante e é diagnosticado como "erro de schema".
3. **`thinking_budget` + `thinking_level` na mesma request = erro 400.** São a API 2.5 e
   a 3.x.
4. **PDF escaneado sem OCR por padrão.** O modelo não avisa que está lendo pixel; a
   resposta vem confiante e errada.
5. **Reduzir resolução de imagem quebra leitura de letra miúda.** Não há desconto por
   resolução menor — reduzir só perde informação.
6. **Chunking de documento gera veredito por fatia.** Regra que depende do documento
   inteiro (ex.: "existe disclaimer em algum lugar") vira N vereditos parciais, cada um
   olhando um pedaço. Decida a estratégia de agregação **antes** de fatiar.
7. **Geração infinita**: se o modelo entrar em loop, **aumentar** temperature para `>= 0.1`
   pode ajudar (aplicável onde o parâmetro não é ignorado).

---

## Ciclo de vida

`gemini-2.5-pro`, `gemini-2.5-flash` e `gemini-2.5-flash-lite` têm aposentadoria
anunciada para **não antes de 2026-10-16** (a página de lifecycle da Vertex mostra
**2026-10-20**).

Consequência prática: **mantenha o model id parametrizado** (env var ou settings), nunca
literal espalhado pelo código. Registre a data em comentário junto ao parâmetro, para
que a migração apareça na leitura do código e não numa falha de produção.

---

## Referências

- `references/parametros.md` — temperature, topP/topK, thinking, seed, maxOutputTokens.
- `references/multimodal.md` — PDF, imagem, vídeo: limites, tokens, ordem das partes.
- `references/modelos.md` — famílias, faixas de thinking, ciclo de vida.
- `references/pipelines.md` — múltiplos agentes, contratos, antirredundância.

## Scripts

- `scripts/inspecionar_agentes.py` — varre o projeto: model ids, locations, tipos de
  arquivo tratados, presença de `responseSchema`/thinking/cache.
- `scripts/gerar_config.py` — recebe perfil + modelo e imprime o `GenerateContentConfig`
  recomendado, marcando o que o modelo ignora.

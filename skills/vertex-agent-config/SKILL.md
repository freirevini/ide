---
name: vertex-agent-config
description: Configura agentes Gemini da geração 3.x na Vertex AI priorizando assertividade e qualidade da avaliação acima de custo — escolhe modelo (incluindo a linha de imagem Nano Banana), thinking_level, media_resolution, responseSchema, ordem das partes multimodais, tratamento por tipo de arquivo e estratégia de cache, e desenha pipelines de múltiplos agentes com contrato explícito entre eles. Entende o projeto antes de sugerir, pergunta o que faltar e segue a decisão final do usuário sobre modelo. Use quando pedirem "configurar agente Vertex", "qual modelo Gemini usar", "melhorar a precisão do agente", "criar novo agente", "desenhar pipeline de agentes", "ajustar thinking_level", "gerar imagem com Nano Banana", "o agente está errando na leitura do PDF" ou "como passar imagem/planilha para o Gemini".
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

1. **Modelo** — da geração 3.x. Para geração de imagem, a linha Nano Banana.
2. **Thinking** — `thinking_level`: `MINIMAL`, `LOW`, `MEDIUM` ou `HIGH`.
3. **Temperature** — marcando explicitamente quando o modelo **ignora** o parâmetro.
4. **`responseSchema`** — exigindo evidência, não só o resultado.
5. **`maxOutputTokens`** — dimensionado como thinking + resposta.
6. **`seed`** — quando a avaliação precisa ser auditável/reprodutível.
7. **Ordem das partes multimodais** — mídia antes do texto; rótulos quando há várias; e
   `media_resolution` por parte (`high` onde a regra mora, `low` no resto).
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

Em `gemini-3.5-flash-lite`, `gemini-3.6-flash` e `gemini-3.7-flash`, `temperature`,
`topP` e `topK` são ignorados — o controle
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

Preços de cache do `gemini-3.1-pro`: escrita **$2,00/1M**, leitura **$0,50/1M** (75% de
desconto), armazenamento **$4,50/1M por hora**.

**O mínimo de tokens diverge entre fontes** (4.096 para a linha 3.x vs 32.768 para cache
explícito no Pro) — **confirme na documentação oficial** antes de dimensionar.

Feliz coincidência: essa mesma ordem é a que isola conteúdo não confiável do prompt do
sistema. Cache e segurança pedem o mesmo layout.

---

## Tabela objetivo → modelo → thinking

Somente geração 3.x. A geração 2.5 não é recomendada para projeto novo.

| Perfil | Modelo | `thinking_level` | Amostragem |
|---|---|---|---|
| `triagem` | `gemini-3.5-flash-lite` | `LOW` | ignorada neste modelo |
| `classificacao` | `gemini-3.7-flash` | `LOW` a `MEDIUM` | ignorada neste modelo |
| `extracao` | `gemini-3.7-flash` ou `gemini-3.1-pro` | `HIGH` | ignorada no flash · `1.0` no Pro |
| `avaliacao-regras` | `gemini-3.1-pro` | `HIGH` | `temperature=1.0` |
| `alto-risco` | `gemini-3.1-pro` | `HIGH` | `temperature=1.0` · use `seed` |
| `documento-longo` | `gemini-3.1-pro` | `HIGH` | `temperature=1.0` |
| `criativo` | `gemini-3.1-pro` ou `gemini-3.7-flash` | `HIGH` | `1.0` (default) |
| geração de imagem | `gemini-3.1-flash-image` (generalista) ou `gemini-3-pro-image` (texto na imagem) | — | — |

Notas que mudam a decisão:

- **`MEDIUM` existe desde a linha 3.1.** Quando `LOW` erra e `HIGH` custa demais, é aqui
  que se resolve — **antes** de trocar de modelo.
- **Default de `thinking_level` é `HIGH`.** Toda chamada sem o parâmetro usa raciocínio
  máximo e paga por ele. É o default certo para qualidade; saiba que é escolha ativa.
- **Pro não aceita `MINIMAL`**; `MINIMAL` exige *thought signatures*.
- **`temperature`, `topP` e `topK` são depreciados e ignorados** em `gemini-3.7-flash`,
  `gemini-3.6-flash` e `gemini-3.5-flash-lite`. Determinismo ali é *system instruction*.
- **`maxOutputTokens` default do `gemini-3.1-pro` é 8.192** — baixo para `HIGH`.
  Dimensione explicitamente.
- **Preço do Pro dobra a entrada acima de 200K tokens de contexto** ($2,00→$4,00) e a
  saída sobe para $18,00. Documento longo cruza isso sem aviso.

Ids, preços e modelos de imagem em `references/modelos.md`.

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
- **Migrar os dois para a geração 3.x** — não é troca de string: `thinking_budget` vira
  `thinking_level`, e no flash a `temperature` deixa de ter efeito.
- Agente 1 `gemini-3.7-flash`, `thinking_level="MEDIUM"`. O `temperature=0.0` atual é
  **ignorado** neste modelo — o determinismo que ele tentava obter vai para a *system
  instruction*. `responseSchema` devolvendo tipo + texto extraído + observações
  posicionais + URI da mídia original.
- Agente 2 `gemini-3.1-pro`, `thinking_level="HIGH"`, `temperature=1.0`,
  `max_output_tokens=32768` (o default de 8.192 não cabe com `HIGH`), `seed` fixo,
  `responseSchema` exigindo `regra_id` + trecho citado.
- **Agente 2 recebe a mídia original além do texto** — exceção à regra antirredundância,
  porque as regras são posicionais. Nas páginas com rodapé crítico, `media_resolution=high`;
  no restante, `low`.
- Cache: system instruction + regras no prefixo estável; a peça por último.
- Escalonamento: `revisao_humana` quando a regra depender de julgamento de grau.
- Ids parametrizados em env var, nunca literais espalhados.
- Atenção ao degrau de 200K do Pro se as peças forem longas.

> Se preferir outro modelo da linha, digo a configuração equivalente — a escolha é sua.

---

## Armadilhas

1. **`temperature=0` na geração 3.x.** Pode causar loop e degradar raciocínio. Mantenha
   `1.0`. Em `gemini-3.7-flash`, `gemini-3.6-flash` e `gemini-3.5-flash-lite` o parâmetro
   é **ignorado** — quem "fixou" temperature ali acha que controlou algo e não controlou.
2. **Thinking conta contra `maxOutputTokens`.** Com `responseSchema`, estourar devolve
   `text=None` e `parsed=None` com `finishReason=MAX_TOKENS` — **sem exceção lançada**.
   Vira `TypeError` a jusante e é diagnosticado como "erro de schema". No `gemini-3.1-pro`
   o default de `maxOutputTokens` é **8.192**, baixo para `thinking_level=HIGH`.
3. **`thinking_level` + `thinking_budget` na mesma request = erro.** `thinking_budget` é a
   API da geração 2.5; na 3.x só existe `thinking_level`.
4. **Default `HIGH` cobra sem avisar.** Chamada sem `thinking_level` usa raciocínio máximo,
   e thinking é cobrado como saída ($12,00/1M no Pro).
5. **Degrau de 200K no Pro.** Acima de 200K de contexto a entrada dobra e a saída sobe.
   Documento longo cruza sem aviso.
6. **PDF escaneado sem OCR por padrão.** O modelo não avisa que está lendo pixel; a
   resposta vem confiante e errada.
7. **`media_resolution` baixa quebra leitura de letra miúda.** Na 3.x o controle é por
   parte: use `high` na página que carrega a regra, `low` no resto — não um valor global.
8. **Chunking gera veredito por fatia.** Regra que depende do documento inteiro vira N
   respostas parciais. Decida a agregação **antes** de fatiar.
9. **Geração infinita**: aumentar temperature para `>= 0.1` pode ajudar, onde o parâmetro
   não é ignorado.
10. **SynthID nas imagens geradas é sempre presente.** Não trate como removível; é
    proveniência.

---

## Ciclo de vida

Modelos entram, saem e mudam de tier — a geração 3.x já acumula `gemini-3-flash`,
`3.5-flash`, `3.6-flash` e `3.7-flash` na mesma linha.

1. **Mantenha o model id parametrizado** — env var ou settings, nunca literal espalhado
   pelo código. Projeto com o id em sete arquivos migra em sete lugares, e esquece um.
2. **Confirme o id e a disponibilidade na sua região** antes de fixar.
3. **Revalide a qualidade a cada troca de id.** Mesmo prompt, modelo diferente, resultado
   diferente — inclusive dentro da mesma geração.

Esta skill não recomenda a geração 2.5 para projeto novo. Se encontrar `gemini-2.5-*`
configurado no Passo 0, trate como migração pendente: a mudança 2.5 → 3.x não é troca de
string, porque `thinking_budget` vira `thinking_level` e, nos flash recentes, a
`temperature` deixa de ter efeito — configuração que dependia de temperature baixa precisa
ser reescrita como *system instruction*.

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

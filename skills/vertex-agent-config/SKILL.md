---
name: vertex-agent-config
description: Configura agentes Gemini das gerações 3.x e 4 na Vertex AI priorizando assertividade e qualidade da avaliação acima de custo — escolhe modelo (Gemini 4 Argon, 3.8 Flash, 3.5 Flash-Lite, 3.1 Pro preview e a linha de imagem Nano Banana 2.1 / Pro), thinking_level com o default real de cada modelo, media_resolution por parte, responseSchema, ordem das partes multimodais, tratamento por tipo de arquivo e estratégia de cache (explícito ou implícito conforme o modelo), e desenha pipelines de múltiplos agentes com contrato explícito entre eles. Entende o projeto antes de sugerir, pergunta o que faltar e segue a decisão final do usuário sobre modelo e número de agentes. Marca id depreciado, preview ou retirado e parâmetro ignorado pelo modelo. Use quando pedirem "configurar agente Vertex", "qual modelo Gemini usar", "melhorar a precisão do agente", "criar novo agente", "desenhar pipeline de agentes", "ajustar thinking_level", "migrar para Gemini 4", "gerar imagem com Nano Banana", "o agente está errando na leitura do PDF" ou "como passar imagem/planilha para o Gemini".
metadata:
  version: 2.0.0
  type: procedure
  verified: 2026-10-23
  source: "documentação oficial da Vertex AI lida em 2026-10-23: páginas de modelo (4 Argon, 3.8 Flash, 3.7 Flash, 3.1 Pro preview, Nano Banana 2.1), Thinking, Model versions and lifecycle, Document understanding, Image understanding, Context caching, Gemini API changelog"
---

# Vertex Agent Config — configurar para acertar

## Princípio norteador

**Qualidade e assertividade da avaliação acima de custo.** Custo entra como *informação* ao
lado da recomendação, nunca como critério de decisão.

A única exceção é o usuário pedir explicitamente para otimizar custo. Aí sim, apresente o
trade-off — e diga o que se perde, não só o que se economiza.

Corolário: **nunca proponha reduzir qualidade para economizar**. E, do outro lado, **nunca
discuta depois que o usuário escolher o modelo ou o número de agentes** — adapte a
configuração ao que ele escolheu e siga.

Fatos por modelo (níveis de thinking e default, o que é ignorado, estágio, data de retirada,
cache, endpoints) vivem em **`references/modelos.md`**, verificado em 2026-10-23. Esta skill
não repete esses fatos; aponta. Modelo muda em semanas: antes de fixar um id, confira lá e na
página do modelo.

---

## Passo 0 — entender antes de sugerir (obrigatório)

Não emita configuração nenhuma antes de completar isto:

1. **Arquitetura de agentes existente** — quantos agentes, a função de cada um, como se
   comunicam, onde está a orquestração.
2. **Model ids já configurados** — quais são e em que arquivo/env var. Id depreciado, retirado,
   preview ou inexistente (`gemini-2.5-*`, `gemini-3.7-flash`, `gemini-3.6-flash`,
   `gemini-3.1-pro` sem `-preview`) é **migração pendente**, dita antes de qualquer parâmetro.
3. **Tipos de arquivo realmente processados** — e **onde acontece a conversão/extração** de
   cada um.
4. **O que já existe** — cache de contexto, `responseSchema`, configuração de thinking,
   `temperature`/`top_p` enviados a modelo que os ignora.
5. Qualquer um desses pontos que não puder ser determinado: **PERGUNTE ao usuário**. Não assuma.

`python scripts/inspecionar_agentes.py <raiz_do_projeto>` faz o primeiro passe: model ids
(literais, env vars, config), locations, tipos de arquivo, presença de schema/thinking/cache,
ids legados e amostragem enviada a modelo que a ignora. É heurístico — confirme lendo o código.

Configuração sugerida sem o Passo 0 completo é chute com aparência de recomendação. Não faça.

### Se o usuário não quiser responder

Ele pode ter pressa, ou não saber. Não insista e não trave: **assuma explicitamente e marque
a suposição**.

> Assumindo PDF com texto renderizado e saída para revisão humana. Se algum desses dois for
> diferente, a configuração muda — me avise e eu ajusto.

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

Dois perfis parecem caber? É sinal de duas responsabilidades. **Pergunte** se o usuário quer
dois agentes, dizendo o que ganha (modelo e thinking certos para cada um, contrato explícito)
e o que perde (latência, um ponto a mais de falha). Ele decide; a skill não separa por conta
própria. Ver "Desenho de múltiplos agentes".

### Etapa 2 — perguntar só o que muda a configuração

**Perguntas abertas, no máximo três por vez.** Só as lacunas que efetivamente alteram a saída
da Etapa 3. Não pergunte o que o Passo 0 já respondeu.

O repertório (escolha as que importam para o caso):

- Qual tipo de arquivo predomina, e ele chega como PDF com texto ou escaneado?
- O resultado vai para uma pessoa decidir ou dispara uma ação automática?
- Qual erro custa mais: aprovar indevidamente ou reprovar indevidamente?
- Qual a tolerância a latência por item?
- O conjunto de regras é fechado e finito, ou aberto e crescente?
- Qual o volume esperado por dia?
- Alguma regra depende de **posição, layout ou aparência** (letra miúda, rodapé, proximidade
  entre elementos)?
- Modelo preview em produção é aceitável? (só se a resposta da Etapa 3 cair no 3.1 Pro preview)

A de posição/layout é a que mais gente esquece e a que mais muda a configuração — decide se o
avaliador precisa da mídia original ou basta o texto extraído.

### Etapa 3 — emitir a configuração completa

Entregue tudo, não só o modelo:

1. **Modelo** — da tabela abaixo, com estágio (GA, preview, depreciado) e data de retirada.
   Para geração de imagem, a linha Nano Banana.
2. **Thinking** — `thinking_level`, dizendo qual é o **default do modelo** e se o valor
   escolhido é igual a ele. `MINIMAL` só onde o modelo aceita.
3. **Amostragem** — em modelo que ignora `temperature`/`topP`/`topK`, **remover**, não
   comentar; onde funciona (3.1 Pro preview), `temperature=1.0`.
4. **`responseSchema`** — exigindo evidência, não só o resultado.
5. **`maxOutputTokens`** — thinking + resposta; no 4 Argon, dentro da janela unificada.
6. **Reprodutibilidade** — registro de entrada, system instruction, `thinking_level`, schema e
   model id; `seed` só onde confirmado.
7. **Ordem das partes multimodais** — mídia antes do texto; rótulos quando há várias; e
   `media_resolution` por parte (`HIGH`/`ULTRA_HIGH` onde a regra mora, `LOW` no resto).
8. **Tratamento por tipo de arquivo** — onde converte, para quê, e o que se perde.
9. **Cache de contexto** — o que é prefixo estável; explícito ou implícito conforme o modelo.
10. **Critério de escalonamento** — quando este agente passa o caso adiante ou para uma pessoa.

`python scripts/gerar_config.py --perfil <perfil> --modelo <model_id>` imprime o bloco
`GenerateContentConfig`, o default de thinking do modelo e o que ele ignora ou rejeita.

**Encerre sempre com esta linha** (ou equivalente):

> Se preferir outro modelo, digo qual configuração equivalente usar — a escolha é sua.

E, quando o usuário escolher, **adapte e siga**. Não reargumente.

---

## Tabela objetivo → modelo → thinking

Gerações 3.x e 4. Linha 2.5 retirada da Vertex em 2026-10-20; não aparece.

| Perfil | Modelo | `thinking_level` (default do modelo) | Amostragem |
|---|---|---|---|
| `triagem` | `gemini-3.5-flash-lite` | `LOW` (default `MINIMAL`) | ignorada |
| `classificacao` | `gemini-3.8-flash` | `LOW` a `MEDIUM` (default `MEDIUM`) | ignorada |
| `extracao` | `gemini-3.8-flash`; `gemini-4-argon` se exigir raciocínio sobre o documento inteiro | `HIGH` (default `MEDIUM`) | ignorada |
| `avaliacao-regras` | `gemini-4-argon` | `HIGH` (default `MEDIUM`) | ignorada |
| `alto-risco` | `gemini-4-argon` | `HIGH` (default `MEDIUM`) | ignorada |
| `documento-longo` | `gemini-4-argon` (janela unificada de 1M) | `HIGH` (default `MEDIUM`) | ignorada |
| `criativo` | `gemini-4-argon` ou `gemini-3.8-flash` | `MEDIUM` a `HIGH` | ignorada |
| geração de imagem | `gemini-nano-banana-2.1` (generalista); `gemini-3-pro-image` quando o 2.1 não bastar em texto na imagem | — | 2.1 **rejeita** `seed`/`temperature`/`topP`/`topK` |

Alternativa ao 4 Argon quando o projeto precisa de `temperature`/`seed` funcionando ou de
cache explícito: `gemini-3.1-pro-preview` — **preview**, só endpoint `global`, sem data de
retirada; decisão do usuário, registrada.

Notas que mudam a decisão:

- **Default de `thinking_level` é por modelo.** `MEDIUM` em 4 Argon e Flash 3.5 a 3.8; `HIGH`
  só no 3.1 Pro preview; `MINIMAL` nos Flash-Lite. Chamada sem o parâmetro usa o default do
  modelo. "Default é HIGH" era verdade de uma geração, não da plataforma.
- **`MINIMAL` só existe em 3.6, 3.5, 3.5-lite, 3.1-lite e 3 Flash.** Em 4 Argon, 3.8, 3.7 e
  3.1 Pro devolve erro. Onde existe, exige *thought signatures* em multi-turn.
- **`MEDIUM`** entrou com o 3.1 Pro e hoje é o default da maioria. Quando `LOW` erra e `HIGH`
  custa demais, é aqui que se resolve — **antes** de trocar de modelo.
- **`temperature`, `topP` e `topK` são ignorados** em 4 Argon, 3.8, 3.7, 3.6 e 3.5 Flash-Lite.
  O guia oficial manda remover; gerações futuras devolvem HTTP 400 (no 4 Argon,
  `candidate_count`/`frequency_penalty`/`presence_penalty` já devolvem). Determinismo ali é
  `thinking_level` + `response_schema` + *system instruction*.
- **`gemini-4-argon`: janela unificada** — entrada + thinking + resposta ≤ 1.048.576;
  `max_output_tokens` até a janela menos a entrada; default por request 65.536 (32.768 em
  HTTP sem streaming). Cache **só implícito**.
- **`gemini-3.1-pro` sem `-preview` não existe na Vertex.** O id é `gemini-3.1-pro-preview`.
- **`maxOutputTokens`**: 3.8 Flash e 3.1 Pro preview têm saída máxima 65.536; o default de
  8.192 citado em versões anteriores desta skill não consta na página atual. Dimensione
  explicitamente.
- **Preço do Pro dobra a entrada acima de 200K tokens de contexto** ($2,00→$4,00) e a saída
  sobe para $18,00. Documento longo cruza isso sem aviso.

Ids, estágios, datas, cache e endpoints: `references/modelos.md`. Comportamento de cada
parâmetro: `references/parametros.md`.

---

## Determinismo

Orientação oficial para os modelos que ignoram amostragem: profundidade por `thinking_level`,
formato por `response_schema`. Depois, a *system instruction* descreve o comportamento: formato
exato da saída, critério de decisão ordenado, o que fazer na ambiguidade, o que não inferir.
Detalhe e ordem de efeito em `references/parametros.md`, "Determinismo".

Um agente configurado assim varia menos entre execuções do que um com `temperature` baixa, e
continua raciocinando, que é o que a temperature baixa quebrava.

## Cache de contexto

Item 9 da Etapa 3. Regra estrutural: **o que é estável vem primeiro, o que varia vem depois**.
Vale para explícito e implícito. 4 Argon só tem implícito (durável por padrão); 3.8 Flash tem
os dois. Mínimos, o que quebra o cache sem parecer e TTL em `references/parametros.md`, "Cache
de contexto".

Feliz coincidência: essa mesma ordem é a que isola conteúdo não confiável do prompt do sistema.
Cache e segurança pedem o mesmo layout.

---

## Desenho de múltiplos agentes

### Uma responsabilidade por agente

Um agente que **classifica** não julga. Um agente que **julga** não reclassifica. Se a Etapa 1
encaixou em dois perfis, proponha dois agentes e pergunte; a decisão é do usuário.

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
original** além do texto extraído. Passar só o resumo do agente anterior perde fidelidade
exatamente onde a regra mora.

Decida isso na Etapa 2, com a pergunta sobre dependência de posição/layout.

### Nunca passar interpretação como fato

O agente N+1 recebe **observações e evidências**, não conclusões do agente N. "Rodapé contém
texto de 6pt na região inferior direita" é observação. "Disclaimer inadequado" é conclusão —
e, se entrar como fato de entrada, o agente seguinte não tem como contestá-la; só herda o erro.

Mais em `references/pipelines.md`.

---

## Tratamento por tipo de arquivo

| Entrada | O que fazer | Por quê |
|---|---|---|
| `.pdf` (texto renderizado) | enviar direto | é um dos dois MIME aceitos |
| `.pdf` (escaneado) | OCR **antes**, ou aceitar perda | OCR não é garantido em nenhum modelo |
| `.docx` `.pptx` `.xlsx` | **converter para PDF** | não são tipos de entrada aceitos |
| `.csv` / texto | `text/plain` | aceito |
| `.jpeg` `.png` `.webp` `.heic` | enviar direto, `media_resolution` alta na parte | ver limites em `references/multimodal.md` |

**Document understanding na Vertex aceita SOMENTE `application/pdf` e `text/plain`**
(confirmado 2026-10-23). Outros MIME entram como texto puro — e aí **gráficos, diagramas e
formatação se perdem**.

**Regra dura**: Office → PDF. **Nunca** Office → texto puro quando houver regra posicional ou
visual, porque a conversão para texto destrói justamente a informação que a regra usa.

PDF custa **280, 560 ou 1.120 tokens por página** conforme `media_resolution` (default
`MEDIUM` = 560), até 3.000 páginas por arquivo. Números, limites e ordem das partes em
`references/multimodal.md`.

---

## Exemplo completo — pipeline de dois agentes

Pedido: *"tenho um sistema que recebe peças de marketing em vários formatos, classifica e
avalia contra regras de compliance. Quero melhorar a precisão."*

**Passo 0** revela: dois agentes, `gemini-3.7-flash` e `gemini-3.1-pro` (ids em
`app/agentes.py:4` e `:5`), formatos `.pdf .docx .pptx .xlsx .csv .jpeg .png`, sem sinal de
conversão, `thinking_budget=1024` e `temperature=0.0` no agente 1, sem cache. Duas migrações
pendentes antes de qualquer parâmetro: 3.7 Flash está depreciado (retira 2027-01-28) e
`gemini-3.1-pro` não existe na Vertex (o id é `gemini-3.1-pro-preview`, preview).

**Etapa 1**: dois perfis — `classificacao` (agente 1) e `avaliacao-regras` (agente 2). O
projeto já tem dois agentes; confirma a separação.

**Etapa 2**, três perguntas abertas:
1. Alguma regra depende de posição ou aparência — letra miúda, rodapé, proximidade entre
   elementos?
2. O veredito dispara uma ação automática ou vai para uma pessoa decidir?
3. Onde os `.docx` e `.xlsx` são convertidos hoje?

Respostas: sim, várias regras são de rodapé e letra miúda; vai para uma pessoa; a conversão
não existe — os Office vão como texto puro.

**Etapa 3**:

- **Achado que muda tudo antes de qualquer parâmetro**: Office indo como texto puro destrói
  posição e formatação, que é onde as regras moram. Converter para PDF é a correção de maior
  efeito neste caso — maior que qualquer ajuste de modelo.
- **Agente 1 → `gemini-3.8-flash`**, `thinking_level="MEDIUM"` (igual ao default; explícito
  por clareza). `thinking_budget` vira `thinking_level`; `temperature=0.0` **sai** (ignorado
  hoje, 400 amanhã); o determinismo que ele tentava obter vai para `response_schema` e
  *system instruction*. Schema devolvendo tipo + texto extraído + observações posicionais +
  URI da mídia original.
- **Agente 2 → `gemini-4-argon`**, `thinking_level="HIGH"` (default é `MEDIUM`; a regra é
  multicamada), `max_output_tokens=32768` dentro da janela unificada (peça de ~40 páginas em
  `MEDIUM` ≈ 22k tokens de entrada; sobra folga), `response_schema` exigindo `regra_id` +
  trecho citado. Sem `seed` (efeito não documentado); reprodutibilidade por registro de
  entrada + model id. Alternativa se o time exigir `seed`/`temperature`: `gemini-3.1-pro-preview`,
  com aviso de preview e só `global`.
- **Agente 2 recebe a mídia original além do texto** — exceção à regra antirredundância,
  porque as regras são posicionais. Nas páginas com rodapé crítico, `media_resolution=HIGH`
  (ou `ULTRA_HIGH` na parte); no restante, `LOW`.
- Cache: system instruction + regras no prefixo estável; a peça por último. No 4 Argon o cache
  é implícito (sem `CachedContent`); no 3.8 Flash pode ser explícito ou implícito.
- Escalonamento: `revisao_humana` quando a regra depender de julgamento de grau.
- Ids parametrizados em env var, nunca literais espalhados; data de verificação registrada.

> Se preferir outro modelo da linha, digo a configuração equivalente — a escolha é sua.

---

## Armadilhas

1. **`temperature`, `topP`, `topK` em 4 Argon, 3.8, 3.7, 3.6 e 3.5 Flash-Lite são
   ignorados.** Quem "fixou" temperature ali acha que controlou algo e não controlou. O guia
   oficial manda remover; gerações futuras devolvem 400. Onde funcionam (3.1 Pro preview),
   `temperature=0` pode causar loop e degradar raciocínio: mantenha `1.0`.
2. **Thinking conta contra `maxOutputTokens`.** Com `responseSchema`, estourar devolve
   `text=None` e `parsed=None` com `finishReason=MAX_TOKENS` — **sem exceção lançada**. Vira
   `TypeError` a jusante e é diagnosticado como "erro de schema". No 4 Argon a janela é
   unificada: documento grande come o espaço da resposta.
3. **`thinking_level` + `thinking_budget` na mesma request = erro.** `thinking_budget` é a
   API da geração 2.5; no 4 Argon devolve 400 mesmo sozinho e não é mapeado para um nível.
4. **Default de thinking é por modelo, e na maioria é `MEDIUM`.** Chamada sem o parâmetro usa
   o default do modelo, e thinking é cobrado como saída ($12,00/1M no Pro). `HIGH` é escolha
   ativa em todo modelo exceto o 3.1 Pro preview.
5. **Degrau de 200K no Pro.** Acima de 200K de contexto a entrada dobra e a saída sobe.
   Documento longo cruza sem aviso.
6. **PDF escaneado sem OCR garantido.** O modelo não avisa que está lendo pixel; a resposta
   vem confiante e errada.
7. **`media_resolution` baixa quebra leitura de letra miúda.** O controle é por parte: `HIGH`
   ou `ULTRA_HIGH` na página que carrega a regra, `LOW` no resto — não um valor global.
8. **Chunking gera veredito por fatia.** Regra que depende do documento inteiro vira N
   respostas parciais. Decida a agregação **antes** de fatiar.
9. **Geração infinita**: aumentar temperature para `>= 0.1` pode ajudar, só onde o parâmetro
   funciona (3.1 Pro preview).
10. **Marca de proveniência nas imagens geradas é sempre presente** (C2PA no Nano Banana 2.1;
    SynthID nas páginas anteriores do Pro e do Lite). Não trate como removível.
11. **Long decode do 4 Argon** (saída acima de 65.536, só `v1beta1`) não é para classificação,
    chat nem turnos curtos de agente.
12. **Modelo preview em produção** (`gemini-3.1-pro-preview`, `gemini-3-flash`): sem data de
    retirada e sem garantia de GA. É decisão do usuário, registrada; a skill avisa toda vez.
13. **Id inexistente**: `gemini-3.1-pro` sem `-preview` falha na Vertex. `gemini-3.5-flash`
    e `gemini-3.1-flash-lite`: amostragem "a confirmar" — não presuma pelo vizinho.

---

## Ciclo de vida

Modelos entram, saem e mudam de tier em semanas: o 3.6 Flash viveu de 2026-07-21 a
2026-11-19. Datas e estágios vêm de **duas plataformas que não andam juntas**: a Gemini API
deprecia antes e roteia automaticamente (3.7 Flash → 3.8 em 2026-10-08); a Vertex mantém
até a data de retirada (3.7 Flash até 2027-01-28). Diga de qual plataforma vem cada data.

1. **Mantenha o model id parametrizado** — env var ou settings, nunca literal espalhado pelo
   código. Projeto com o id em sete arquivos migra em sete lugares, e esquece um.
2. **Confirme o id, o estágio e a disponibilidade na sua região** antes de fixar
   (`references/modelos.md`, depois a página do modelo).
3. **Revalide a qualidade a cada troca de id.** Mesmo prompt, modelo diferente, resultado
   diferente — inclusive dentro da mesma geração.
4. **Registre** o id escolhido com a data de verificação (`.rules/decisoes.md`, se o projeto tiver).

Migração pendente quando o Passo 0 encontrar: `gemini-2.5-*` (retirado da Vertex em
2026-10-20); `gemini-3.7-flash` (depreciado, retira 2027-01-28); `gemini-3.6-flash` (retira
2026-11-19); `gemini-3.1-flash-image` (depreciado → `gemini-nano-banana-2.1`);
`gemini-omni-flash-preview` (→ `gemini-omni-1.1-flash`). A mudança não é troca de string:
`thinking_budget` vira `thinking_level`, `MINIMAL` some nos modelos novos, amostragem deixa
de ter efeito, e no 4 Argon o cache explícito sai e a janela passa a ser unificada.

## Referências

- `references/modelos.md` — **fonte única** de fatos por modelo: ids, estágio, datas, níveis
  de thinking e default, amostragem, cache, endpoints; linha de imagem.
- `references/parametros.md` — thinking_level, amostragem, determinismo, seed,
  maxOutputTokens, regras próprias do 4 Argon, cache de contexto, responseSchema.
- `references/multimodal.md` — media_resolution por parte, PDF, imagem, vídeo, áudio, ordem
  das partes, geração de imagem, diagnóstico.
- `references/pipelines.md` — múltiplos agentes, contratos, antirredundância, escalonamento.

## Scripts

- `scripts/inspecionar_agentes.py` — varre o projeto: model ids (literais, env, config),
  locations, tipos de arquivo, presença de `responseSchema`/thinking/cache, ids legados,
  amostragem enviada a modelo que a ignora.
- `scripts/gerar_config.py` — recebe perfil + modelo e imprime o `GenerateContentConfig`
  recomendado com o default de thinking do modelo e o que ele ignora ou rejeita;
  `--listar` mostra a tabela de modelos.
- `tests/test_scripts.py` — `python -m pytest tests/ -q`: tabela de modelos bate com
  `modelos.md`, defaults por modelo, `MINIMAL` nunca inferido, `.env` varrido, Nano Banana
  sem `seed`.

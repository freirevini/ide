# Model Armor no Vertex AI

Classificador gerenciado do Google Cloud para prompt injection/jailbreak, URI malicioso e
dado sensível. Cobre qualquer LLM via REST, não só Gemini.

**Limites verificados em 2026-10-23** na documentação oficial (overview, "Sanitize prompts
and responses", quotas, release notes). Preço, latência e quota: linhas mantidas da versão
anterior desta skill, não reverificadas.

## Números operacionais

| Item | Valor |
|---|---|
| Preço | **2M tokens/mês grátis**, depois **US$ 0,10 por 1M de tokens** |
| Limite do filtro de prompt injection/jailbreak | **65.536 tokens** (≈ 262.144 caracteres) desde 2026-08-25, para injeção/jailbreak, Responsible AI e CSAM; a página de quotas ainda lista **10.000**. Histórico: 2.000 (2025) → 10.000 (2025-07-28) → 65.536 |
| Acima do limite | filtros de injeção, RAI e URI: `MATCH_FOUND` se acharam algo, **`SKIP_DETECTION`** se não; Sensitive Data Protection: sempre `SKIP_DETECTION` |
| Streaming | modo *real-time streaming* sem limite de tokens; modo *buffered* sujeito ao limite |
| Token | ≈ 4 caracteres; a mesma contagem vale para preço e para o limite |
| Latência adicional | **~50–300 ms** por chamada, no caminho da request |
| Quota padrão | **1.200 QPM por projeto** (ajustável 0–1.200) |
| Modos de enforcement | `INSPECT_ONLY` (default), `INSPECT_AND_BLOCK` |
| Níveis de confiança | `LOW_AND_ABOVE`, `MEDIUM_AND_ABOVE` |

## As três restrições que mudam o desenho

**1. `SKIP_DETECTION` não é "limpo".** Texto acima do limite devolve `SKIP_DETECTION`
quando não encontrou nada — o que inclui o caso em que o payload estava na parte não lida.
Trate `SKIP_DETECTION` como **não classificado**, igual a indisponibilidade. Documento
maior que o limite: fatiar o texto extraído em **janelas sobrepostas** (payload cortado na
fronteira escapa das duas metades) e agregar; uma janela suspeita marca o documento. Com
65.536 tokens a maior parte dos documentos cabe inteira; o fatiamento vira exceção, não
regra — mas o tratamento de `SKIP_DETECTION` continua obrigatório.

**2. Documento entra só pela API REST, com tipo explícito.** Model Armor sanitiza PDF, CSV,
TXT, Word (DOCX, DOCM, DOTX, DOTM), PowerPoint (PPTX, PPTM, POTX, POTM, POT) e Excel (XLSX,
XLSM, XLTX, XLTM), em base64, **com `byteDataType` informado pelo chamador** — não há
detecção automática de tipo. As integrações por **Agent Gateway** e por **políticas do
Apigee** **não aceitam documento**: por elas, só texto. Nunca presuma que enviar o arquivo
pela integração aciona o filtro; confirme por qual caminho o documento chega e, se não for a
API direta, extraia o texto na aplicação e submeta texto.

**3. O que a aplicação extrai e o que o filtro lê precisam ser o mesmo texto.** Se a
extração para o modelo e a extração para o Model Armor divergem (OCR diferente, versão
diferente do documento), o filtro classifica um texto e o modelo lê outro.

## Configuração: template vs floor setting

| | Template por request | Floor setting |
|---|---|---|
| Escopo | chamada individual | todo o projeto |
| Como | `modelArmorConfig` com `promptTemplateName` / `responseTemplateName` no `generateContent` | configuração do projeto |
| Exige acesso ao projeto | não (só código) | **sim** |
| Aplica quando `modelArmorConfig` é omitido | não | sim |

**Se a superfície editável for apenas arquivos versionados do repositório, use template
por request.** Floor setting é configuração de projeto e estará fora de alcance — propor
floor setting nesse ambiente é recomendação inaplicável.

Cuidado adicional: a request **falha** se o template não existir na região de roteamento.
Confirme a região antes.

## Comportamento em indisponibilidade

A integração pode **pular a sanitização** se o Model Armor estiver indisponível;
`INSPECT_AND_BLOCK` reporta erro de configuração. Trate no código: ausência de resposta do
classificador, erro e `SKIP_DETECTION` **não** são sinal verde. Registre e trate como não
classificado, aplicando as camadas determinísticas normalmente.

## Filtros disponíveis

- Prompt injection e jailbreak (com nível de confiança)
- URI malicioso
- Sensitive Data Protection — de-identificação por masking, redaction ou hashing
- Responsible AI: hate speech, harassment, dangerous, sexually explicit
- CSAM
- Varredura de vírus em documento (`VirusScanFilterResult`)

## Eficácia

**Não há taxa de detecção publicada para Model Armor.** Não cite número. Para a classe de
classificador + verificação de alinhamento, LlamaFirewall reporta ASR de **17,6% → 1,75%**
— e mesmo esse é evadível por atacante adaptativo.

Trate Model Armor como camada probabilística de redução de ruído, nunca como portão.

## Fontes

- docs.cloud.google.com/model-armor/overview
- docs.cloud.google.com/model-armor/sanitize-prompts-responses
- docs.cloud.google.com/model-armor/quotas
- docs.cloud.google.com/model-armor/release-notes
- docs.cloud.google.com/model-armor/model-armor-agent-gateway-integration
- docs.cloud.google.com/security-command-center/docs/model-armor-vertex-integration
- cloud.google.com/security/products/model-armor

# Model Armor no Vertex AI

Classificador gerenciado do Google Cloud para prompt injection/jailbreak, URI malicioso e
dado sensível. Cobre qualquer LLM via REST, não só Gemini.

## Números operacionais

| Item | Valor |
|---|---|
| Preço | **2M tokens/mês grátis**, depois **US$ 0,10 por 1M de tokens** |
| Limite do filtro de prompt injection/jailbreak | **512 tokens** |
| Latência adicional | **~50–300 ms** por chamada, no caminho da request |
| Quota padrão | **1.200 QPM por projeto** (ajustável 0–1.200) |
| Modos de enforcement | `INSPECT_ONLY` (default), `INSPECT_AND_BLOCK` |
| Níveis de confiança | `LOW_AND_ABOVE`, `MEDIUM_AND_ABOVE` |

## As duas restrições que mudam o desenho

**1. O filtro aceita 512 tokens.** Um documento avaliado inteiro não cabe. É obrigatório
fatiar o texto extraído em janelas e classificar janela a janela. Consequências:

- custo e latência escalam com o tamanho do documento, não são constantes;
- **use janelas sobrepostas** — payload cortado exatamente na fronteira entre janelas
  escapa das duas metades;
- decida a política de agregação: uma janela suspeita basta para marcar o documento
  (recomendado), ou exige N janelas.

**2. Sanitização de documento não é suportada.** Para `.pdf`, `.docx`, `.pptx`, `.xlsx` é
preciso **extrair o texto na aplicação e submeter texto**. Nunca presuma que enviar o
arquivo aciona o filtro.

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
classificador **não** é sinal verde. Registre e trate como não classificado, aplicando as
camadas determinísticas normalmente.

## Filtros disponíveis

- Prompt injection e jailbreak (com nível de confiança)
- URI malicioso
- Sensitive Data Protection — de-identificação por masking, redaction ou hashing
- Responsible AI: hate speech, harassment, dangerous, sexually explicit

## Eficácia

**Não há taxa de detecção publicada para Model Armor.** Não cite número. Para a classe de
classificador + verificação de alinhamento, LlamaFirewall reporta ASR de **17,6% → 1,75%**
— e mesmo esse é evadível por atacante adaptativo.

Trate Model Armor como camada probabilística de redução de ruído, nunca como portão.

## Fontes

- docs.cloud.google.com/security-command-center/docs/model-armor-vertex-integration
- docs.cloud.google.com/model-armor/quotas
- cloud.google.com/security/products/model-armor

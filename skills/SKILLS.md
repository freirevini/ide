# Índice das skills (pt-BR)

Versão em português, organizada por área, do índice gerado `SKILLS.txt`.
Fonte de cada linha: o frontmatter (`name`, `description`, `metadata.version`) do
`SKILL.md` de cada pasta. A coluna **Origem** diz de onde a skill veio: `própria`
(escrita neste repositório) ou o repositório GitHub de onde foi instalada via
`npx skills add` (registrado em `skills-lock.json`).

Este arquivo é mantido à mão. `SKILLS.txt` continua sendo a fonte gerada e
verificada (`python3 skills/scripts/skills-index.py --check`); ao criar, mudar
ou remover uma skill, atualize os dois.

**Total: 66 skills** (25 próprias, 41 de terceiros). Atualizado em 2026-10-26.

## Sumário

1. [Fluxo de trabalho com IA](#1-fluxo-de-trabalho-com-ia)
2. [Qualidade, verificação e depuração](#2-qualidade-verificação-e-depuração)
3. [Tickets, releases e manutenção](#3-tickets-releases-e-manutenção)
4. [Python](#4-python)
5. [Dados e engenharia de dados](#5-dados-e-engenharia-de-dados)
6. [Google Cloud e Gemini](#6-google-cloud-e-gemini)
7. [Front-end e visualização](#7-front-end-e-visualização)
8. [Navegador e automação web](#8-navegador-e-automação-web)
9. [Criação de skills](#9-criação-de-skills)

---

## 1. Fluxo de trabalho com IA

Contrato do projeto, prompts, contexto entre sessões e organização do trabalho
com qualquer IA de código.

| Skill (versão) | Origem | Objetivo | Quando usar |
|---|---|---|---|
| `begin` (1.1.0) | própria | Inicia qualquer projeto (pasta vazia, repositório recém-clonado ou código sem contrato de IA) com o mínimo para que qualquer IA de código entenda o contexto. | "começar projeto", "novo projeto", "preparar o repositório para IA", "setup inicial", "bootstrap", "primeiro commit"; ao clonar repositório sem `AGENTS.md` ou abrir projeto pela primeira vez em IDE com IA. |
| `agents-md` (2.1.0) | própria | Cria, audita e mantém o contrato do projeto com a IA: `AGENTS.md` na raiz mais a pasta `.rules/` (escopo, testes, erros, decisões). Aplica orçamento de atenção e liga todas as ferramentas ao mesmo arquivo por ponteiro. | "cria o AGENTS.md", "configura o projeto para IA", "regras para o agente", "revisa o AGENTS.md", "o agente repetiu o erro", "mudou o que eu não pedi", "toda correção gera teste". |
| `prompt-default` (2.1.0) | própria | Portão de pré-execução para qualquer prompt: verifica arquivos citados, contradições, verbos vagos e pedidos de risco antes de agir. | Em toda tarefa antes de executar, em especial quando o prompt cita arquivos ou funções que podem não existir, mistura instruções contraditórias, usa "melhora", "arruma isso", ou pede apagar, reescrever, migrar ou trocar a stack. |
| `rules-default` | própria | Audita, corrige e cria regras do Cursor (`.cursor/rules/*.mdc`). Lê todas as regras existentes antes; se a regra pedida já existe ou está espalhada, levanta uma questão em vez de duplicar. | Revisar formatação de regras, padronizar regras ou criar uma regra nova. |
| `context-out` (1.3.0) | própria | Grava o contexto de uma task em `.doc/<task>.md` para handoff em cadeia entre IAs/IDEs: objetivo, mudanças, decisões, pendências, o que foi tentado e falhou. | Ao encerrar ou pausar uma etapa, trocar de ferramenta ou modelo, antes de passo longo que pode estourar cota; "salvar contexto", "gerar handoff", "checkpoint", "salva onde parei", "vou continuar no Cursor". |
| `context-in` (1.3.0) | própria | Carrega o contexto gravado em `.doc/<task>.md` por outra IA/IDE e o adota como base da conversa atual, reconciliando com o chat e o repositório. | No início de um chat em projeto com pasta `.doc`; "retomar task X", "carregar contexto", "continuar de onde parou", "aplicar as correções da revisão", "a outra sessão caiu". |
| `reflect` (1.0.0) | própria | Aprende com trabalho repetido e o transforma no menor ativo útil (regra, skill, script ou nada). | Após um lote de trabalho ou fim de sprint; "o que vira regra?", "revisa as skills", "aprende com essa sessão", "melhoria contínua", "kaizen". Não é para implementação comum nem depuração pontual. |
| `codemap` (1.0.0) | própria | Constrói e atualiza um mapa hierárquico de um repositório desconhecido, para qualquer IA e stack. Só sob pedido explícito, porque é caro. | "mapear o repositório", "cria o codemap", "atualiza o mapa do código", onboarding em repositório grande. Não é para trabalho rotineiro nem repositórios pequenos. |
| `worktrees` (1.0.0) | própria | Gerencia git worktrees como pistas isoladas para trabalho arriscado, paralelo ou exploratório. | Refatoração que pode quebrar o checkout ativo, tarefas ou agentes em paralelo, spikes descartáveis, upgrade de dependências; "cria uma worktree", "isola essa mudança", "roda em paralelo". |

## 2. Qualidade, verificação e depuração

Disciplina de código, provas de funcionamento, testes e investigação de bugs.

| Skill (versão) | Origem | Objetivo | Quando usar |
|---|---|---|---|
| `forever-clean` (2.1.0) | própria | Disciplina de editar antes de criar e de forma do código para qualquer base: localiza o conceito, decide criar ou editar, audita tamanho e complexidade, refatora só se compensar. | Ao adicionar ou mudar código, sempre que o agente for criar um arquivo novo; "simplifica o repo", "esse arquivo está grande demais", "arquivos demais", "não cria arquivo novo". |
| `clean-code-review` (1.1.0) | própria | Revisão de clean code em duas fases: primeiro reduz o número de arquivos (fundindo), depois enxuga o código dentro deles, mantendo legibilidade para o próximo agente. Nunca muda comportamento externo. | "revisa o clean code", "enxuga o código", "reduz os arquivos". Escala de projeto simples a base grande (leitura em lotes com "continuar"). |
| `verification-planning` (1.0.0) | própria | Monta o caminho de evidência antes de uma implementação não trivial: como saber que funcionou. | Antes de feature, correção, refatoração, migração ou mudança de comportamento; "como vamos testar isso?", "como provar que funcionou?", "planeja a verificação". |
| `verification-before-completion` | obra/superpowers | Antes de declarar trabalho pronto, corrigido ou passando, exige rodar os comandos de verificação e confirmar a saída. Evidência antes de afirmação. | Sempre que estiver prestes a dizer "está pronto", antes de commit ou PR. |
| `test-driven-development` | obra/superpowers | Protocolo de TDD: teste falhando primeiro, implementação mínima, refatoração. | Ao implementar qualquer feature ou correção, antes de escrever código de produção. |
| `systematic-debugging` | obra/superpowers | Depuração sistemática: reproduzir, isolar, formular hipótese, provar, antes de propor correção. Inclui script de bisseção para achar teste que polui estado. | Ao encontrar qualquer bug, teste falhando ou comportamento inesperado, antes de propor correções. |
| `debug-ledger` (1.0.0) | própria | Protocolo de investigação para bugs difíceis, intermitentes ou longos, com registro persistente de hipóteses e tentativas. | Quando o bug resiste à primeira correção, reproduz só às vezes, atravessa vários componentes, ou o agente insiste na mesma mudança; "investigar esse bug", "não reproduz sempre", "já tentamos isso". |
| `eval-rubric` (1.0.0) | própria | Pontua um entregável produzido por IA (código gerado, PR, documento, saída de pipeline, execução de agente) contra uma rubrica ponderada em que cada ponto traz prova (arquivo:linha ou saída de comando). | "avalie o resultado", "dê uma nota", "pontue o projeto gerado", "qual modelo foi melhor", A/B de prompts ou modelos. Não é para revisar código escrito por humano. |
| `llm-in-tests` (1.0.0) | própria | Torna testável e barato de testar um sistema que chama LLM (classificação, extração, geração, agentes, RAG), para qualquer provedor e linguagem. | "testar o pipeline com LLM", "como testar a chamada do modelo", "teste intermitente por causa da IA", "mockar o Gemini/OpenAI", "montar um golden set", "o prompt mudou, o que quebrou". |
| `calculos-python` | própria | Revisa cálculos numéricos quanto à integridade de arredondamento decimal entre Python, PySpark/Databricks, BigQuery e Excel. | Revisar, validar ou depurar cálculos (divisão, tendência, médias simples e ponderadas, médias aparadas, derivação subtrativa, multiplicação percentual) em que diferenças de arredondamento entre etapas mudam o resultado. |

## 3. Tickets, releases e manutenção

Ciclo de PRs e issues, auditoria pós-merge, dependências, versões e sistemas legados.

| Skill (versão) | Origem | Objetivo | Quando usar |
|---|---|---|---|
| `ticket-audit` (1.0.0) | própria | Audita pull requests e issues antes de qualquer código ser escrito ou mergeado, em qualquer forge (GitHub, GitLab, Bitbucket, Azure DevOps). | "audita os PRs", "revisa as issues abertas", "pode fazer merge?", "faz triagem do backlog", decidir se um PR é seguro. |
| `ticket-resolution` (1.0.0) | própria | Executa os resultados aprovados de uma auditoria de tickets (correções, ajustes, features, fechamentos), um ticket por vez. | Após a auditoria, quando o usuário manda prosseguir; "pode corrigir", "resolve o que foi aprovado", "implementa o que a auditoria pediu". Não julga tickets (isso é `ticket-audit`). |
| `post-merge-audit` (1.0.0) | própria | Audita o estado combinado da branch padrão após um lote de merges ou antes de deploy ou release. | Quando vários tickets entraram na mesma sessão, antes de tag, deploy ou publicação; "o main está pronto pra release?", "audita o lote que entrou", "revisa o que foi mergeado". |
| `dependency-bump` (1.0.0) | própria | Caminho rápido e seguro para PRs de bot só de dependência (Dependabot, Renovate e similares), em qualquer gerenciador de pacotes. | "atualiza as dependências do dependabot", "fecha os PRs de bump", "mergeia os bumps". Não é para PRs que tocam código de aplicação, migrações, containers ou CI. |
| `release` (1.0.0) | própria | Corta e publica uma versão de qualquer projeto: changelog, tag, publicação. | "lança a versão", "corta uma release", "publica a 1.4", "fecha o changelog". Não é para mergear tickets nem auditar o lote. |
| `legacy-modernizer` (1.1.0) | jeffallan/claude-skills | Desenha estratégias de migração incremental, identifica fronteiras de serviço, produz mapas de dependência, roteiros de migração e fachadas de API para bases antigas. | Modernizar sistemas legados, aplicar strangler fig ou branch by abstraction, decompor monólitos, atualizar frameworks ou linguagens, reduzir dívida técnica sem parar o negócio. |

## 4. Python

Estrutura de bibliotecas, qualidade, testes, segurança, desempenho, CLIs e recursos modernos da linguagem.

| Skill (versão) | Origem | Objetivo | Quando usar |
|---|---|---|---|
| `setting-up-python-libraries` | wdm0006/python-skills | Monta projetos de biblioteca Python com ferramental moderno: `pyproject.toml`, uv, ruff, pytest, pre-commit, GitHub Actions. Inclui script gerador de projeto. | Criar biblioteca nova, modernizar projeto para `pyproject.toml`, configurar lint/testes/CI, Makefile e pre-commit. |
| `improving-python-code-quality` | wdm0006/python-skills | Melhora a qualidade do código Python com ruff, mypy, idiomas pythônicos e refatoração. | Revisar código por qualidade, adicionar type hints, configurar análise estática, refatorar biblioteca. |
| `testing-python-libraries` | wdm0006/python-skills | Projeta e implementa suítes pytest com fixtures, parametrização, mocks, testes baseados em propriedades (Hypothesis) e CI. | Criar testes, aumentar cobertura, montar infraestrutura de testes, testes de propriedade. |
| `auditing-python-security` | wdm0006/python-skills | Audita bibliotecas Python quanto a vulnerabilidades com Bandit, pip-audit, Semgrep e detect-secrets. Inclui script que roda os quatro. | Revisar segurança de biblioteca, configurar varredura de segurança no CI, aplicar padrões de código seguro. |
| `optimizing-python-performance` | wdm0006/python-skills | Otimiza desempenho de Python com profiling (cProfile, PyInstrument), análise de memória (memray, tracemalloc), benchmarks (pytest-benchmark). | Analisar gargalos, achar vazamento de memória, montar teste de regressão de desempenho. |
| `building-python-clis` | wdm0006/python-skills | Constrói interfaces de linha de comando para bibliotecas Python com Click ou Typer. | Adicionar CLI a uma biblioteca ou criar ferramenta de linha de comando. |
| `python-modern-python` | martinffx/python-skills | Recursos e tipagem do Python 3.12 a 3.14: parâmetros de tipo, aliases, protocolos, dataclasses, pattern matching, asyncio. | Escolher sintaxe para as versões suportadas, tipagem avançada, concorrência e cancelamento com asyncio. |
| `python-sqlalchemy` | martinffx/python-skills | Padrões estáveis de ORM e Core do SQLAlchemy 2.0. | Mapeamentos tipados, `select()`, sessões e transações, relacionamentos e carregamento, engines sync ou async, JSON, upserts por dialeto, migrações Alembic. |

## 5. Dados e engenharia de dados

DataFrames, Spark, dbt, Databricks, Airflow e BigQuery.

| Skill (versão) | Origem | Objetivo | Quando usar |
|---|---|---|---|
| `pandas-pro` (1.1.0) | jeffallan/claude-skills | Operações com DataFrames pandas para análise, manipulação e transformação. | Limpeza, agregação, merge, séries temporais, joins com várias chaves, pivot, resample, NaN com interpolação ou forward-fill, groupby, conversão de tipos. |
| `polars` | davila7/claude-code-templates | Biblioteca de DataFrames rápida sobre Apache Arrow. | Select, filter, group_by, joins, avaliação lazy, leitura e escrita CSV/Parquet, API de expressões, análise de alto desempenho. |
| `spark-engineer` (1.1.0) | jeffallan/claude-skills | Escrita de jobs Spark, depuração de desempenho e configuração de cluster para processamento distribuído. | Transformações de DataFrame, otimizar Spark SQL, pipelines RDD, tuning de shuffle, configuração de cluster, cargas de big data. |
| `using-dbt-for-analytics-engineering` | dbt-labs/dbt-agent-skills | Cria e altera modelos dbt, escreve transformações SQL com `ref()` e `source()`, cria testes e valida com `dbt show`. | Qualquer trabalho dbt: construir ou alterar modelos, depurar erros, explorar fontes, escrever testes, avaliar impacto de mudanças. |
| `running-dbt-commands` | dbt-labs/dbt-agent-skills | Formata e executa comandos da CLI dbt, escolhe o executável correto e estrutura parâmetros. | Rodar models, tests, builds, compiles ou show via CLI; dúvida sobre qual executável ou como formatar parâmetros. |
| `adding-dbt-unit-test` | dbt-labs/dbt-agent-skills | Cria definições YAML de testes unitários que simulam entradas dos modelos upstream e validam a saída esperada. | Adicionar testes unitários a um modelo dbt ou praticar TDD em dbt. Referências por warehouse (BigQuery, Snowflake, Redshift, Postgres, Spark). |
| `databricks-core` (0.1.0) | databricks/databricks-agent-skills | Operações da CLI Databricks e skill de entrada: autenticação, seleção de perfil e bundles (DABs). | Carregar primeiro em tarefas de CLI, auth, perfil e bundle; depois carregar a skill do produto correspondente. |
| `databricks-pipelines` (0.3.0) | databricks/databricks-agent-skills | Desenvolve Lakeflow Spark Declarative Pipelines (antigo Delta Live Tables) no Databricks. | Pipelines batch ou streaming em Python ou SQL, incluindo Auto CDC a partir de streams de eventos ou snapshots completos. Invocar antes de começar a implementação. |
| `databricks-jobs` (0.3.0) | databricks/databricks-agent-skills | Desenvolve e implanta Lakeflow Jobs no Databricks via DABs, SDK Python ou CLI. | Jobs de engenharia de dados com notebooks, wheels Python, SQL, dbt ou pipelines. Invocar antes de começar a implementação. |
| `lab-ui` | própria | Revisão de boas práticas para arquitetura de UI com ipywidgets em notebooks Databricks: notebook fino sobre fachada, allowlist de controles nativos, padrão factory+chrome, mount idempotente, separação estado/render. | Revisar, refinar ou estender código de UI de notebook que segue essa arquitetura. |
| `managed-airflow-dag-authoring` (1.0.1) | google/skills | Orientação para escrever DAGs do Apache Airflow no Managed Service for Apache Airflow (antigo Cloud Composer). | Criar ou estender um DAG do Airflow. Não é para Python sem relação com DAGs. |
| `bigquery-basics` (1.0.2) | google/skills | Gerencia datasets, tabelas e jobs no BigQuery (CLI, bibliotecas cliente, IaC, MCP, IAM). | Interagir com BigQuery, rodar SQL, gerenciar recursos (datasets, tabelas, views), ingestão e análise básicas. |
| `bigquery-bigframes` (2.0.1) | google/skills | Gera código Python com BigQuery DataFrames (BigFrames). | Padrão para qualquer tarefa de dados em Python envolvendo BigQuery: processamento, análise e machine learning. Não é para fluxos SQL-first nem para a biblioteca `google-cloud-bigquery` (use `bigquery-basics`). |
| `bigquery-optimization` (1.1.1) | google/skills | Fluxos para otimizar ambientes BigQuery: capacidade e editions, armazenamento (particionamento, clustering, ciclo de vida, modelos de cobrança) e consultas SQL. | Otimizar custo, migrar de edition, dimensionar reservas, armazenamento lógico vs. físico, desenhar particionamento/clustering, migrar tabelas, otimizar consultas, avaliar BI Engine e índices de busca. |

## 6. Google Cloud e Gemini

Gemini API, Vertex AI, agentes ADK, IAM, Cloud Run e Cloud Storage.

| Skill (versão) | Origem | Objetivo | Quando usar |
|---|---|---|---|
| `gemini-api` (1.0.1) | google/skills | Uso da Gemini API na Agent Platform (Vertex AI) com o Google Gen AI SDK: Python, JS/TS, Go, Java, C#; entradas multimodais, tools, mídia. | Gemini em ambiente corporativo, ou quando o usuário cita Vertex AI, Google Cloud ou Agent Platform. |
| `vertex-agent-config` (2.0.0) | própria | Configura agentes Gemini (gerações 3.x e 4) na Vertex AI priorizando assertividade e qualidade de avaliação acima de custo: escolha de modelo, `thinking_level`, pipeline de agentes, entrada de imagem e planilha. | "configurar agente Vertex", "qual modelo Gemini usar", "melhorar a precisão do agente", "desenhar pipeline de agentes", "migrar para Gemini 4", "o agente está errando na leitura do PDF". |
| `gemini-vertex-tuning` | própria | Otimiza latência e custo de pipelines de agentes Gemini/Vertex AI (classificação de arquivos + avaliação com RAG) sem degradar a precisão: context caching, thinking budget, roteamento de modelo. | "otimizar latência do agente", "a avaliação está lenta", "reduzir custo Vertex", "ajustar o RAG"; quando aparecer `finishReason=MAX_TOKENS` ou `parsed=None` em saída estruturada. |
| `security-gemini-prompt` (2.1.0) | própria | Audita um projeto que usa Gemini/Vertex AI, identifica fragilidades contra prompt injection direta e indireta e as corrige, com verificação adversarial e relatório estruturado. | "auditar segurança do projeto Gemini", "achar fragilidades de prompt injection", "hardening do RAG", "configurar Model Armor"; quando conteúdo de entrada consegue dobrar o comportamento do sistema. |
| `google-agents-cli-adk-code` (1.11.0) | google/agents-cli | Referência rápida de padrões de API do ADK (Agent Development Kit): tipos de agente, tools, orquestração, callbacks, estado, Workflow API em grafo. | "escrever código do agente", "construir agente com ADK", "adicionar uma tool", "criar callback", "gerenciar estado". Não é para scaffolding nem deploy. |
| `google-cloud-recipe-auth` (1.0.2) | google/skills | Orientação sobre IAM e autenticação/autorização em serviços e APIs do Google Cloud: usuários humanos, identidades de serviço, Application Default Credentials. | Configurar ou depurar acesso a serviços Google Cloud, escolher identidade e credenciais, boas práticas de acesso seguro. |
| `cloud-run-basics` (1.0.1) | google/skills | Gerencia serviços, jobs e worker pools do Cloud Run. | Implantar aplicação que responde HTTP (serviço), tarefa por evento ou agendada (job), ou processamento contínuo em background (worker pool). |
| `google-cloud-storage-basics` (1.1.2) | google/skills | Armazena, recupera e gerencia objetos em buckets do Cloud Storage (GCS). | Criar e configurar buckets, upload/download/stream/transferência, pastas, URLs assinadas, IAM e ACLs, classes de armazenamento, gcsfuse, MCP server de Storage. |

## 7. Front-end e visualização

Angular, gráficos, apps Streamlit e design de interface.

| Skill (versão) | Origem | Objetivo | Quando usar |
|---|---|---|---|
| `angular-developer` (1.0) | angular/skills | Gera código Angular e dá orientação arquitetural, com referências por tema (signals, DI, roteamento, formulários, SSR, acessibilidade, testes). | Criar projetos, componentes, serviços, HTTP; dúvidas sobre reatividade, content projection, formulários, injeção de dependência, roteamento, renderização híbrida, ARIA. |
| `angular-new-app` (1.0) | angular/skills | Cria uma aplicação Angular nova com a Angular CLI seguindo as diretrizes modernas. | Sempre que o usuário quiser criar uma aplicação Angular do zero. |
| `angular-material` (2026.1.31) | angular-sanctuary/angular-agent-skills | Biblioteca de componentes Angular Material baseada em Material Design 3, com referência por componente. | Usar, configurar ou tematizar componentes do Angular Material. |
| `apexcharts` (4.0.2) | apexcharts/apexcharts-skill | Construção de gráficos e visualizações com ApexCharts.js (v8), com um documento de referência por tipo de gráfico. | Criar, configurar ou corrigir qualquer gráfico ApexCharts: linha, área, barra, pizza, donut, radial, scatter, heatmap, candlestick, boxplot, radar, treemap, funil, gauge, sunburst, waterfall e outros. |
| `plotly` | davila7/claude-code-templates | Visualização científica e estatística interativa em Python (Plotly Express e graph objects). | Gráficos de dispersão, linha, barra, heatmap, 3D, mapas, distribuições, gráficos financeiros e dashboards interativos. |
| `developing-with-streamlit` | streamlit/agent-skills | Todas as tarefas Streamlit: criar, editar, depurar, estilizar, tematizar, otimizar ou implantar apps; componentes customizados e `st.components.v2`. Descobre e carrega a documentação da versão instalada (>= 1.57). | Qualquer menção a Streamlit ou `st.`. |
| `frontend-design` | anthropics/skills | Orientação para design visual distinto e intencional ao construir ou remodelar interfaces: direção estética, tipografia, escolhas que não pareçam template. | Criar UI nova ou reformular existente quando o resultado precisa ter identidade, não o padrão genérico. |
| `ui-ux-pro-max` | nextlevelbuilder/ui-ux-pro-max-skill | Inteligência de design UI/UX para web, mobile e desktop com base local pesquisável: estilos, paletas por produto, pares de fontes, diretrizes de UX, ícones, presets GSAP, tipos de gráfico e stacks. | Desenhar, construir, revisar ou corrigir interfaces: páginas, componentes, design systems, acessibilidade, interação, layout responsivo, tipografia, cor, gráficos, implementação por stack. |

## 8. Navegador e automação web

| Skill (versão) | Origem | Objetivo | Quando usar |
|---|---|---|---|
| `browser-use` | browser-use/browser-use | Controle direto do navegador via CDP: automação, scraping, testes, screenshots. Cobre também navegadores em nuvem (biblioteca `browser-use`, Playwright, Puppeteer ou qualquer cliente CDP). | Interagir com sites ou apps web por protocolo, com ou sem navegador hospedado. |
| `agent-browser` | vercel-labs/agent-browser | CLI de automação de navegador para agentes de IA; cobre também apps Electron (VS Code, Slack, Discord, Figma, Notion), Vercel Sandbox e AWS Bedrock AgentCore. | "abrir um site", "preencher formulário", "clicar botão", "tirar screenshot", "extrair dados", "testar esse app", "login no site"; testes exploratórios, QA, caça a bugs. |

## 9. Criação de skills

| Skill (versão) | Origem | Objetivo | Quando usar |
|---|---|---|---|
| `skill-creator` | anthropics/skills | Cria skills novas, modifica e melhora skills existentes, e mede desempenho com evals, benchmark com análise de variância e otimização da `description` para melhorar o gatilho. Inclui visualizador local de resultados de eval. | Criar skill do zero, editar ou otimizar uma existente, rodar evals, medir variância, melhorar precisão de acionamento. |

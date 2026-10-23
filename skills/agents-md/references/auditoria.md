# Auditoria — `AGENTS.md` já existente

Objetivo: a IA ler e entender o contexto com o mínimo de ambiguidade. Rode todas as
verificações; registre em tabela `verificação · achado · ação · automática | pergunta`.
Diff pequeno: corrija o que está errado, não reescreva o que está certo.

Legenda da coluna **Modo**: `auto` a skill corrige sem perguntar; `pergunta` vira Pergunta
Aberta no relatório; `auto/pergunta` corrige quando a resposta certa é evidente.

## 1. Nome e localização

| Verificação | Como | Correção | Modo |
|---|---|---|---|
| Nome exato `AGENTS.md` | `ls` na raiz; variantes `agent.md`, `agents.md`, `AGENT.md`, `Agents.md` | `git mv <variante> AGENTS.md`. Ferramentas procuram o nome exato; Linux e CI diferenciam maiúsculas | auto |
| Na raiz do repositório | `git rev-parse --show-toplevel` | mover para a raiz; subpasta só em monorepo | auto |
| Um por raiz; aninhados só com conteúdo próprio | `find . -name AGENTS.md -not -path '*/node_modules/*'` | fundir duplicados; aninhado só com o que difere | pergunta se divergem |
| UTF-8, LF, sem BOM | `file AGENTS.md` | converter | auto |

## 2. Tamanho

| Verificação | Como | Correção | Modo |
|---|---|---|---|
| `AGENTS.md` até 150 linhas e 12.000 caracteres | `wc -l -c AGENTS.md` | mover regras para `.rules/`, detalhe para `docs/` | auto |
| Cada `.rules/*.md` até 12.000 caracteres | `wc -c .rules/*.md` | compactar `erros.md`; dividir o resto | auto |
| Nenhuma seção acima de ~40 linhas | leitura | mover ou dividir | auto |
| Instruções sempre carregadas (`AGENTS.md` + `CLAUDE.md` + regras `alwaysApply` + imports) somam até ~200 linhas | `wc -l` de cada arquivo sempre carregado | aplicar o teste por linha (§5); mover o que sobrar para `.rules/` ou `docs/`; remover antes de acrescentar | auto/pergunta |

## 3. Estrutura

| Verificação | Como | Correção | Modo |
|---|---|---|---|
| Projeto e Comandos no topo | leitura | reordenar sem mudar texto | auto |
| Índice de `.rules/` e mínimo inline presentes | `grep -n '.rules/' AGENTS.md` | acrescentar do template; criar `.rules/` se não existir | auto |
| Seções presentes: Testes, Código e estilo, Após cada ajuste, Definição de pronto, Não fazer | leitura | acrescentar do template, preenchendo com o que o projeto já tem | auto; conteúdo específico: pergunta |
| Títulos `##` curtos; lista em vez de parágrafo | leitura | reformatar sem mudar sentido | auto |
| Sem slot `{{...}}` nem `<!-- -->` sobrando | `bash .rules/check.sh` | preencher ou remover | pergunta se o valor não for conhecido |

## 4. Veracidade

| Verificação | Como | Correção | Modo |
|---|---|---|---|
| Todo comando executa | rodar cada um e guardar a última linha | substituir pelo que funciona; sem solução: `a definir` | auto/pergunta |
| Todo caminho citado existe | `ls` em cada pasta e arquivo citado | corrigir ou remover | auto |
| Versões batem com manifesto e lockfile | comparar | corrigir | auto |
| Teste citado existe | `grep -rn "<nome>" <pasta de testes>` | corrigir | auto |
| Ambiente citado existe | `.env.example`, compose, scripts de deploy | remover ou marcar "não existe ainda" | pergunta |

## 5. Legibilidade para IA

| Verificação | Como | Correção | Modo |
|---|---|---|---|
| Toda regra é verificável (tem comando, arquivo ou critério) | leitura | concretizar ou remover ("escreva código limpo" não executa) | pergunta |
| Sem "geralmente", "preferencialmente", "se possível", "tente", "idealmente" | `grep -inwE 'geralmente\|preferencialmente\|se possível\|tente\|idealmente' AGENTS.md .rules/*.md` (`-w`: palavra inteira, senão "existente" casa) | imperativo | auto |
| Sem condicional ambígua ("em alguns casos") | leitura | separar em casos nomeados | pergunta |
| "Não fazer" cobre o que o projeto já sofreu | cruzar com `.rules/erros.md` e `git log --oneline \| grep -i fix` | acrescentar | auto |
| Uma ideia por linha | leitura | quebrar | auto |
| Cada linha passa no teste "remover isto faria o agente errar?" | leitura, linha a linha | linha que não passa vai para `.rules/decisoes.md`, `docs/` ou é removida; regra que precisa de parágrafo de contexto é conhecimento de recuperação, não regra governada | pergunta |
| Procedimento que muda com frequência está descrito passo a passo | leitura; `git log` do trecho | trocar por ponteiro para exemplo vivo (arquivo ou repositório que funciona hoje) | pergunta |

## 6. Contradição e duplicação

| Verificação | Como | Correção | Modo |
|---|---|---|---|
| Mesma diretiva em dois arquivos (`CLAUDE.md`, `GEMINI.md`, `.cursorrules`, `.mdc`, README, CI) | ler todos; comparar comandos e regras | manter em um; ponteiro nos outros | auto se igual; pergunta se diverge |
| CI roda comando diferente do `AGENTS.md` | ler `.github/workflows/*`, `.gitlab-ci.yml` | alinhar ao CI | pergunta |
| README diz outra coisa | leitura | README aponta para `AGENTS.md` ou alinha | pergunta |
| `AGENTS.md` contradiz `.rules/` | leitura cruzada | `.rules/` manda em regra; `AGENTS.md` manda em comando | auto |

## 7. Segurança

| Verificação | Como | Correção | Modo |
|---|---|---|---|
| Sem segredo, token, URL interna sensível, dado pessoal | `grep -inE '(key\|token\|secret\|senha\|password\|bearer)[a-z_]*[[:space:]]*[:=][[:space:]]*[^[:space:]]{6,}' AGENTS.md .rules/*.md` (pega atribuição com valor, não a palavra solta) e leitura | remover; avisar para rotacionar se já foi commitado | auto, com aviso |
| Seção Dados diz o que o projeto guarda, ou "nenhum" | leitura | perguntar | pergunta |

## 8. Ponteiros

| Verificação | Como | Correção | Modo |
|---|---|---|---|
| Cada ferramenta usada no projeto chega ao arquivo | `references/ambientes.md`; `ls` dos arquivos de cada ferramenta | criar ponteiro | auto |
| Nenhuma cópia divergente | `diff` | substituir cópia por ponteiro | auto |

## 9. Vivo

| Verificação | Como | Correção | Modo |
|---|---|---|---|
| `erros.md` tem entrada para os últimos bugs corrigidos | `git log --oneline -30 \| grep -iE 'fix\|corrig\|bug'` versus entradas | registrar retroativamente? | pergunta |
| `AGENTS.md` não ficou para trás do código | `git log -1 --format=%cd -- AGENTS.md` versus último commit | re-executar Passo 2 da skill | auto |

## 10. Mecânico

| Verificação | Como | Correção | Modo |
|---|---|---|---|
| `.rules/check.sh` existe e passa | `bash .rules/check.sh` | copiar do template; corrigir cada `FALHA:` | auto |
| Hook instalado neste clone | `git config --get core.hooksPath` imprime `.githooks` e `.githooks/commit-msg` é executável | `git config core.hooksPath .githooks`; `chmod +x` | auto |
| CI roda o check com `--range` | ler workflow | acrescentar passo (`references/ambientes.md`) | pergunta |
| Últimos commits `fix` cumprem a regra | `bash .rules/check.sh --range origin/main..HEAD` (ou últimos 20: `HEAD~20..HEAD`) | registrar retroativamente ou aceitar o histórico | pergunta |

## Relatório da auditoria

```
auditoria: <n> verificações · <n> achados · <n> corrigidos · <n> perguntas
arquivo: AGENTS.md <antes: n linhas/n chars> → <depois>
renomeado de: <variante> | não
criado: .rules/ [sim|já existia] · <arquivos>
achados corrigidos: <lista: verificação → ação>
check.sh: ok | <n> falhas · hook: instalado | não · CI: sim | não
perguntas abertas: <lista numerada>
```

# Contexto — outra IA continua este projeto sem o seu chat

Vinculante para qualquer agente, em qualquer ferramenta. Ferramentas usadas aqui: {{lista:
Claude Code, Cursor, Antigravity, Gemini CLI, Copilot...}}. Idioma dos arquivos de contrato:
{{português}}. Nenhuma ferramenta compartilha memória com outra; o que não está em arquivo
versionado não existe para a próxima sessão.

## 1. Onde cada tipo de contexto vive (um lugar só)

| Pergunta de quem chega | Arquivo | Quem escreve |
|---|---|---|
| O que é o projeto, como rodar, o que não fazer | `AGENTS.md` | skill `agents-md`; qualquer agente quando comando ou caminho muda |
| Por que está assim | `.rules/decisoes.md` | quem decide, na hora |
| O que já quebrou e a regra que ficou | `.rules/erros.md` | quem corrige, no mesmo commit |
| Em que ponto está cada task, o que falta, o que foi revisado | `.doc/<task>.md` | skill `context-out` ao pausar, encerrar ou trocar de ferramenta; `context-in` lê |
| O que mudou, quando, por quem | `git log` | commits pequenos com mensagem que diz o porquê (`.rules/git.md`) |
| Como o código é organizado | {{`docs/arquitetura.md` ou "a definir: criar quando houver mais de um módulo"}} | quem muda a estrutura |
| Para humano de fora: o que é e como começar | `README.md` | humano; aponta para `AGENTS.md`, não repete |

Informação fora desta tabela (comentário de código, issue, mensagem de chat, memória da IDE)
não conta como contexto do projeto. Vale, vai para o arquivo certo.

## 2. Ao entrar (toda sessão, antes da primeira ação)

1. `git status --short` e `git log --oneline -10`: o que está em andamento e o que acabou de mudar.
2. `AGENTS.md` inteiro; depois cada arquivo de `.rules/`.
3. `ls -a .doc/`: há documento com `status` diferente de `concluida`? Carregue-o
   (`context-in`, ou leia inteiro: objetivo, decisões de todos os ciclos, pendências) antes
   de propor qualquer coisa. Pedido do usuário cita uma task: carregue aquela.
4. Confira o que o documento afirma contra o repositório. Divergência vai para o usuário,
   não é corrigida em silêncio.

Precedência quando duas fontes discordam: pedido do usuário > esta conversa > código no
repositório > documentos. Código diz o estado; documento diz a intenção e o motivo.

## 3. Durante

- Decisão com alternativa descartada: entrada em `.rules/decisoes.md` **no momento**, não no
  fim. Fim de sessão esquece.
- O que não foi verificado é `suposição:` e assim fica escrito. Suposição escrita como fato
  é o erro mais caro do handoff: o próximo agente constrói em cima.
- Pergunta sem resposta neste chat vira pendência em `.doc/<task>.md`, com onde (arquivo,
  função) e o que falta decidir.
- Não dependa de plano, artefato, memória ou aba da sua ferramenta. Extraia decisão e
  pendência para os arquivos acima; o artefato nativo é leitura extra opcional.

## 4. Ao sair (pausa, fim de etapa, troca de ferramenta ou de modelo)

1. `.doc/<task>.md` atualizado com ciclo novo (`context-out`): objetivo, mudanças realizadas,
   decisões técnicas, pendências, contexto adicional. Sem a skill, escreva as cinco seções
   nessa ordem, com data, ferramenta/modelo e identificador do chat quando houver.
2. `AGENTS.md` conferido: comando, caminho ou convenção mudou? Atualize no mesmo commit.
3. Correção feita: "Após cada ajuste" do `AGENTS.md` cumprido (`erros.md`, teste, `check.sh`).
4. Commit do trabalho e do contexto juntos. Trabalho não commitado só existe nesta máquina.
5. Última linha da resposta: a frase de retomada para a próxima ferramenta
   (`retomar task <slug>`).

## 5. Escrever para leitor frio

O leitor é um modelo sem este chat, em outra ferramenta, de outro fornecedor, talvez em outra
máquina. Então:

- Caminho de arquivo completo e comando exato. "O arquivo de antes" não existe para ele.
- Nada de "como conversamos", "conforme combinado", "o de sempre".
- Fato verificado separado de suposição; pendência com critério de aceite.
- Uma ideia por linha. Lista, não parágrafo.
- Sem transcrição de conversa e sem explicação genérica de linguagem ou framework.
- Documento de task até ~250 linhas; passou, há transcrição dentro. Corte.

## 6. O que nunca entra em arquivo de contexto

Credencial, token, valor de `.env`, URL com segredo, dado pessoal, dado de cliente, dump de
banco. `.rules/`, `.doc/` e `AGENTS.md` são versionados e saem desta máquina.

## 7. Pastas de contexto são versionadas

`AGENTS.md`, `.rules/`, `.doc/`, `.githooks/` e `.github/` nunca vão para `.gitignore`.
Handoff entre máquinas e ferramentas depende disso. `git check-ignore -v .rules .doc` tem que
voltar vazio.

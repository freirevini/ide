# Testes automatizados — a disciplina em detalhe

Problema que resolve: o agente conserta um ponto e quebra outro, porque nada o avisa. Com
teste, o bug corrigido **não volta**, e cada regra do produto vira manual de instruções em
código, que qualquer IA executa sem precisar lembrar. Independe de linguagem e de ferramenta:
a IA só precisa saber rodar um comando e ler a saída.

Template pronto para o projeto: `templates/rules/testes.md`. Este arquivo explica cada item.

## 1. Todo bug vira teste de regressão

Ordem obrigatória:

1. Reproduzir o bug em um teste: mesmas condições, mesmo resultado errado.
2. Rodar: o teste **tem que falhar**. Se passa, não captura o bug; reescrever.
3. Corrigir o código.
4. Rodar: o teste passa, e o resto da suíte continua verde.
5. Nomear pelo comportamento, não pelo ticket: `test_cupom_e_promocao_nao_acumulam`, não
   `test_bug_42`. A IA busca pelo nome quando o sintoma reaparece.
6. Registrar em `.rules/erros.md` (Passo U da skill).

Bug corrigido sem teste é o mesmo bug adiado. O agente da próxima sessão não sabe que aquilo
já quebrou uma vez.

## 2. Toda regra vira teste

Regra de negócio, cálculo, validação, permissão, fluxo: se tem resultado determinável a partir
de uma entrada, tem teste. Regra sem teste é sugestão; o agente a quebra sem saber.

Ao criar a suíte, listar as regras e apontar o teste de cada uma. Linha sem teste é pendência.

| Regra | Entrada | Esperado | Teste |
|---|---|---|---|
| desconto nunca leva o total abaixo do mínimo | total 100, desconto 95%, mínimo 10 | 10 | `tests/test_pricing.py::test_desconto_respeita_minimo` |
| usuário sem papel `admin` não lista outros usuários | token de usuário comum | 403 | `tests/test_users.py::test_lista_exige_admin` |

## 3. Chegar ao estado pelo caminho curto

Para testar o ponto onde o bug acontece, não se percorre o fluxo inteiro. O ponto é um
**estado**; o teste constrói o estado direto (fixture, factory, snapshot, seed de banco) e
exercita só o pedaço em questão.

Efeito: teste em milissegundos, suíte roda a cada mudança, não "de madrugada". O fluxo
completo continua existindo como teste de integração (item 4), não como único jeito de testar.

## 4. Duas velocidades

| Camada | O que é | Quando roda |
|---|---|---|
| Rápida (unitária) | estado construído direto; sem rede, disco ou UI; segundos | **sempre**: antes de declarar qualquer tarefa pronta, a cada correção |
| Lenta (integração, ponta a ponta) | fluxo completo, banco real, navegador, serviços | antes de build, deploy e PR; em CI |

## 5. Suíte inicial para projeto sem testes

Pedir ao agente que crie **personas** que conhecem as regras (usuário típico, usuário que
explora limites, usuário que preenche tudo errado, operador) e enumere os casos de cada uma. O
agente escreve os testes; o humano revisa quais são regra de verdade e quais são suposição.
Suposição vira Pergunta Aberta, não teste.

Feito **uma vez**. Depois a suíte cresce pelo item 1 (bug) e pelo item 2 (regra nova).

## 6. Rotina de execução

- Suíte rápida: antes de "pronto", "corrigido", "implementado". Última linha no relatório.
- Suíte completa: antes de build, deploy e PR. Falhou, não sobe.
- CI roda no push; verde libera, vermelho devolve relatório e o agente corrige a partir dele.
  Qualquer agente sabe configurar CI da plataforma do projeto; basta pedir.
- Agente que pode rodar testes **roda sem ser mandado** quando toca em código coberto.

## 7. Proibições

- Não apagar, comentar, marcar `skip`/`xfail`/`todo` ou afrouxar asserção para fazer passar.
  Skip só com motivo no próprio teste e issue aberta.
- Não mudar o valor esperado sem confirmar com o usuário que **a regra mudou**. Teste que
  falha pode estar certo e o código errado.
- Não mockar a unidade sob teste. Mock é para fronteira: rede, relógio, banco, disco.
- Não escrever teste que passa sempre (sem asserção, tautologia, `assert True`).
- Não declarar "testado" sem ter rodado. "Deveria passar" não é resultado.
- Não editar teste existente dentro de uma tarefa que não é sobre aquele teste
  (`.rules/escopo.md`, item 3).

## 8. Quando um teste falha

1. Ler a mensagem inteira; não adivinhar.
2. Reproduzir isolado (`-k nome`, `-t nome`, `--filter`, `-run`).
3. Corrigir a **causa**; se a correção é "ajustar o teste", voltar ao item 7.
4. Rodar a suíte inteira de novo. Verde parcial não existe.

## 9. Teste como oráculo e como confirmação

No pedido em quatro partes (`protocolo.md`), o teste é o oráculo (antes) e a confirmação
(depois) ao mesmo tempo. Para operação fora de código (migração, cópia de dados, script
destrutivo) o equivalente é **dry-run** antes e **contagem ou hash** depois: "saíram N
registros com M bytes; têm que chegar exatamente N com M".

## 10. Runner padrão por stack

Usar o que o projeto já tem. Sem nada, propor o da tabela e **perguntar** antes de fixar.

| Stack | Runner | Comando rápido | Um teste só | Onde ficam |
|---|---|---|---|---|
| Python | pytest | `pytest -q` | `pytest -q -k nome` | `tests/` |
| Node/TypeScript | vitest (ou jest se já houver) | `npx vitest run` | `npx vitest run -t nome` | `*.test.ts`, `__tests__/` |
| Go | testing | `go test ./...` | `go test ./... -run Nome` | `*_test.go` ao lado do código |
| Rust | cargo | `cargo test` | `cargo test nome` | `#[cfg(test)]`, `tests/` |
| Java/Kotlin | JUnit via Gradle/Maven | `./gradlew test` / `mvn -q test` | `./gradlew test --tests Classe` | `src/test/` |
| .NET | xunit/nunit | `dotnet test` | `dotnet test --filter Nome` | projeto `*.Tests` |
| Ruby | rspec / minitest | `bundle exec rspec` / `rake test` | `bundle exec rspec -e nome` | `spec/` / `test/` |
| PHP | phpunit / pest | `vendor/bin/phpunit` | `vendor/bin/phpunit --filter nome` | `tests/` |
| Flutter/Dart | flutter test | `flutter test` | `flutter test --name nome` | `test/` |
| Swift | XCTest | `swift test` | `swift test --filter nome` | `Tests/` |
| Web ponta a ponta | Playwright | `npx playwright test` | `npx playwright test -g nome` | `e2e/` |

Esqueleto mínimo quando não há nada: um arquivo com um teste que passa, na pasta da tabela, e
o comando registrado em `AGENTS.md`. Sem isso, "rode os testes" não executa nada.

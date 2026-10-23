# Atualização de documento existente

Documento da task já existe em `.doc/`. Atualizar ≠ reescrever. Histórico de decisão é a
parte mais cara de reconstruir — nunca some.

## Antes de qualquer edição

1. Leia o documento inteiro. Não edite às cegas.
2. Confira o frontmatter: `ciclo`, `status`, `proximo_papel`, `atualizado_em`, `ciclos`, `artefatos`.
3. Se `origem` for outra ferramenta/modelo, o documento veio de handoff. Respeite o que
   está lá: você complementa, não corrige estilo nem reescreve seção que continua válida.
   Convenção de outra IDE não é erro a consertar.
4. Toda gravação é um **ciclo novo** (`ciclo` + 1), com data, ferramenta/modelo, tipo de ação e
   `chat:`. Ciclo anterior nunca é editado nem renumerado — formato em `ciclos.md`.

## Seção a seção

### Objetivo — preserva
Reescreve só se o escopo realmente mudou. Nesse caso registre a mudança, não a esconda:

```markdown
## Objetivo
<novo objetivo>

**Escopo alterado em 2026-09-08**: <antes> → <depois>. Motivo: <motivo>.
```

Item que saiu do escopo vai para **Fora de escopo**.

### Mudanças realizadas — acumula por ciclo
Nova subseção `### Ciclo N · <data> · <ferramenta / modelo> · <ação>` no topo, acima das anteriores,
com `chat:` e `doc:` logo abaixo do título. Ciclos antigos ficam intactos, mesmo que o código tenha
mudado depois — eles explicam por que o arquivo está como está e de qual conversa saiu.

Cada ciclo carrega seu próprio `#### Verificação` com o que foi **de fato** executado e o resultado
real. "Deve funcionar" não é verificação. Ciclo que entrega para revisão carrega também
`#### Para o revisor validar`.

Documento muito longo: compacte só ciclos antigos, conforme `ciclos.md`. Decisões, correções
abertas e linhas `chat:` nunca entram na compactação.

### Decisões técnicas — acumula, nunca apaga
Numeração contínua (`D4`, `D5`…), cada decisão marcada com o ciclo que a tomou: `### D5 (ciclo 4) — <título>`.
Decisão anterior invalidada:

```markdown
### ~~D2 — <título>~~ (supersedida por D5 em 2026-09-08)
- Revertida: <motivo em uma linha>.
```

Corpo original encurtado, título e motivo permanecem. Sem isso a próxima IA reintroduz a
abordagem descartada — é o modo de falha mais comum do handoff entre modelos.

Decisão tomada por **escolha do usuário** (não por análise técnica) marca-se assim:
`- **Decisão do usuário** — não rediscutir sem ele pedir.`

### Pendências — reescreve inteira
Dois blocos: `### Correções do ciclo N (revisão · <ferramenta / modelo>)`, um por ciclo de revisão
que ainda tenha item não fechado, e `### Pendências gerais`.

Item de correção segue o ciclo de vida de `ciclos.md` (`aberta` → `aplicada no ciclo N` /
`recusada (motivo)` / `reaberta no ciclo N`). Correção nunca é apagada em silêncio: sem status, o
revisor seguinte reencontra o mesmo problema e a cadeia entra em loop. Bloco cujos itens estejam
todos aplicados sai de Pendências — os IDs continuam citados na entrada do ciclo que os aplicou.

Lista reflete só o estado atual:
- Concluída: sai da lista, entra em Mudanças realizadas do ciclo atual.
- Cancelada: sai da lista, vira linha em Contexto adicional (`descartado: <o quê> — <por quê>`).
- Nova: entra com papel, local e critério de aceite.
- Bloqueada: fica, com `Bloqueado: <o que falta e de quem depende>`.

### Contexto adicional — funde
Acrescenta o novo. Remove só o que ficou comprovadamente falso (comando que mudou, armadilha
resolvida). Suposição confirmada vira fato e perde o rótulo `suposição:`; suposição derrubada
vira `descartado:` com o motivo.

## Frontmatter

- `atualizado_em`: sempre.
- `status` / `proximo_papel`: sempre reavaliados. `proximo_papel: nenhum` quando concluída.
- `origem`: ferramenta/modelo desta sessão.
- `ciclo`: incrementa.
- `ciclos`: acrescenta uma entrada com `n`, `data`, `por` (ferramenta / modelo), `acao` e `chat`.
  Nunca reescreve as anteriores.
- `bastao`: `livre` quando o ciclo entrega para outro papel; seu nome em checkpoint. Assumiu de
  sessão cortada: o título do ciclo diz de quem, e a entrada traz `recuperado:` (`ciclos.md`).
- `caminho`: confirme que bate com o arquivo real.

## Task nova x mesma task

Mesma task se o objetivo é o mesmo, mesmo que o slug pareça diferente. Sinais de mesma task:
mesmos arquivos-alvo, pendência do documento antigo descreve o que você acabou de fazer,
usuário disse "continuando".

Nova task se o objetivo é outro, ainda que no mesmo módulo. Aí cria documento novo e cruza
os dois: uma linha em Contexto adicional de cada um (`relacionada: .doc/<outro-slug>.md — <como>`).

Na dúvida, pergunte. Documento duplicado da mesma task quebra o handoff: a IA seguinte lê um
dos dois e perde metade do estado.

## Escrita concorrente (vários agentes no mesmo repositório)

Antigravity roda agentes em paralelo pelo Agent Manager; Cursor roda várias abas e worktrees.
Dois agentes gravando o mesmo `.doc/<slug>.md` é cenário normal.

Protocolo, obrigatório em toda gravação:

1. Guarde o `atualizado_em` e o `ciclo` lidos no início.
2. **Imediatamente antes de gravar**, releia o arquivo.
3. Iguais: grave com `ciclo` + 1.
4. Diferentes: outro agente escreveu. Releia inteiro, pegue o próximo número de ciclo livre e funda
   o que ele acrescentou (Mudanças ganham o ciclo dele **e** o seu; Decisões mantêm as duas
   numerações, renumerando as suas em seguida; Pendências viram a união menos as concluídas;
   correções mantêm os IDs originais, sempre)
   e só então grave.
5. Conflito real de decisão entre os dois agentes: não escolha sozinho. Registre as duas em
   Decisões técnicas com `**conflito aberto**` e avise o usuário.

Nunca sobrescreva sem reler. Contexto perdido aqui não volta — a outra sessão já fechou.

## Conflito entre documento e repositório

O documento diz uma coisa, o código diz outra (alguém editou fora da IA, ou outra ferramenta
mexeu sem gravar contexto). Nesse caso:

1. O repositório vence sobre **estado do código**.
2. O documento vence sobre **intenção e decisão** — a menos que o usuário diga o contrário.
3. Registre a divergência em Contexto adicional:
   `divergência 2026-09-08: doc dizia <X>, repo está <Y>; adotado <Z> porque <motivo>.`

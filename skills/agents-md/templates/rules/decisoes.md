# Decisões — tomadas com motivo; não reabra sem pedido

Leia antes de propor mudança estrutural. Decisão registrada aqui não é re-perguntada nem
revertida por "melhoria". Para mudar, o usuário pede e a entrada ganha uma linha "Revista em".
Pedido do usuário que contraria uma regra de `.rules/` e é mantido após aviso também entra aqui.

## Formato

```markdown
### D-<nnn> · <AAAA-MM-DD> · <decisão em uma frase>
- Contexto: <situação que exigiu decidir>
- Alternativas: <o que foi descartado>
- Motivo: <por que esta>
- Afeta: `<pastas/arquivos>`
- Commit: <hash curto, se houver>
- Revisar quando: <condição concreta>
```

Gotcha de ambiente (armadilha que não é bug de código: ferramenta, infra, dependência) é uma
linha com data na seção do fim: `- <AAAA-MM-DD> · <armadilha> · <como contornar>`.

IDs colidiram por trabalho em paralelo: quem faz o merge renumera a mais nova.

## Decisões

## Gotchas de ambiente

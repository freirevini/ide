# Erros — já cometidos e corrigidos aqui; não repita

Leia antes de tocar em qualquer área citada: `grep -n "<arquivo>" .rules/erros.md`.
Cada entrada nasce no fim de uma correção (`AGENTS.md`, "Após cada ajuste"). ID é estável;
entrada nunca é apagada, só compactada. O hook de commit recusa correção sem entrada nova.

## Formato

```markdown
### E-<nnn> · <AAAA-MM-DD> · <comportamento errado, em uma frase; não o número do ticket>
- Área: `<arquivo ou módulo>`, `<teste>`
- Sintoma: <o que apareceu, como foi notado>
- Causa: <raiz, uma linha>
- Regra: <verbo, "nunca" ou "sempre": o que fazer daqui em diante>
- Teste: `<caminho::nome>` ou "sem teste possível: <motivo>"
- Commit: <hash curto>, ou "este" quando a entrada vai no mesmo commit da correção
- Origem: <data · ferramenta/IA ou humano · pedido do usuário | handoff C<n>.<n> de .doc/<task>.md | CI>
```

## Como manter

- Entrada nova sempre no fim, com o próximo ID.
- `Área` é o campo de busca: nome exato de arquivo ou módulo.
- `Regra` é executável. "Cuidado com datas" não é regra; "converta para UTC na borda da API;
  nunca compare datetime naive com aware" é.
- Regra que vale para mais de um lugar vai para `testes.md`, `escopo.md` ou "Não fazer" do
  `AGENTS.md`; a entrada passa a apontar para lá.
- Acima de ~40 entradas ou 10.000 caracteres: entradas antigas viram uma linha
  (`E-003 · 2026-07-02 · <título> · regra em testes.md §5`). ID fica.
- IDs colidiram (dois agentes em paralelo: worktrees, Agent Manager, branches): quem faz o
  merge renumera a entrada mais nova para o próximo ID livre e corrige as referências.
  `bash .rules/check.sh` acusa ID duplicado.
- Correção vinda de handoff entre IAs (`.doc/`, item `C<n>.<n>` do `context-out`): a entrada
  cita o item em `Origem`; o documento de handoff cita o `E-nnn`.

## Entradas

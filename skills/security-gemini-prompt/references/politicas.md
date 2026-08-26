# Políticas de resposta à manipulação detectada

Duas políticas configuráveis. Padrão recomendado: `sinalizar`.

## Comparação

| | `sinalizar` | `ignorar` |
|---|---|---|
| Comportamento visível | reporta a tentativa no resultado, com trecho e família | desconsidera a instrução, avalia só o conteúdo legítimo |
| Auditabilidade na interface | alta | nenhuma |
| Realimenta o atacante | **sim** — revela qual detector disparou | não |
| Ruído com falso positivo | alto — cada falso positivo vira alarme visível | nenhum |
| Efeito colateral útil | nomear a tentativa reduz a chance de o modelo obedecê-la | — |
| Risco principal | fadiga de alerta; atacante itera contra o feedback | ataque bem-sucedido fica indistinguível de avaliação normal |

## Invariante que vale nas duas

**`ignorar` afeta apenas o que é exibido ao usuário final. O log interno registra sempre.**

Silêncio na interface nunca pode virar silêncio na auditoria. Sem isso, `ignorar` não é
uma política de apresentação — é perda de sinal de segurança, e torna impossível saber se
a taxa de tentativas está subindo.

Implemente como dois caminhos distintos a partir do mesmo evento:

```python
evento = {"documento_id": ..., "familia": ..., "trecho": ..., "camada": ...}
log_seguranca.registrar(evento)          # SEMPRE, nas duas políticas

if politica == "sinalizar":
    resultado["tentativa_de_manipulacao"] = {
        "detectada": True,
        "familia": evento["familia"],
        "trecho": evento["trecho"],
    }
# politica == "ignorar": resultado não menciona; o log já tem
```

## Critério de escolha

Escolha `sinalizar` quando:

- o resultado vai para um time interno de revisão (o alerta tem dono);
- há trilha de auditoria obrigatória por regulação ou processo;
- o autor do documento **não** é o destinatário do resultado — sem realimentação direta.

Escolha `ignorar` quando:

- o resultado volta para quem enviou o documento — aí `sinalizar` é um canal de
  feedback para o atacante iterar;
- o volume de falso positivo tornaria o alerta ruído e treinaria o revisor a ignorá-lo.

Caso híbrido, geralmente o mais defensável: **`ignorar` na resposta ao remetente,
`sinalizar` no painel interno**. Mesma detecção, dois públicos. É a configuração a propor
quando o sistema tem os dois destinos.

## O que nenhuma das políticas faz

Nenhuma decide o resultado. Manipulação detectada **nunca** produz decisão favorável
automática — isso é regra da camada 6 (`references/camadas.md`), determinística, e roda
independentemente da política escolhida. A política governa apenas a **apresentação**.

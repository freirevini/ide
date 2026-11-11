# Exemplos de envio silencioso de e-mail HTML em Python (Microsoft Graph e SMTP), com testes e verificação

## Papel e objetivo
Você é um engenheiro Python trabalhando em um ambiente corporativo Windows restritivo. Construa, teste e verifique três exemplos independentes e executáveis que enviam um e-mail HTML de forma silenciosa (sem abrir nenhuma janela de e-mail), tendo como remetente uma caixa departamental (caixa compartilhada) e preservando a formatação do HTML: tabela, CSS inline, acentos e um logo embutido. Ao final, entregue o relatório no formato fixo da seção "Relatório final". Você executa sozinho, sem ter a quem perguntar: onde algo não bater com as suposições, pare aquela rota e relate, em vez de improvisar.

## Contexto
**Situação.** O projeto do usuário enviava e-mails automatizando o Outlook clássico (COM, via `win32com`). Agora a máquina só tem o Outlook novo (versão 1.2026.1026.100), que não oferece COM, VBA nem MAPI. Essa automação não funciona mais e não deve ser tentada. O envio passa a ser feito direto no servidor, sem o aplicativo Outlook.

**Ambiente.** Windows corporativo, Python 3.11, `pip` possivelmente limitado a um repositório interno, possível proxy e inspeção TLS.

**Dados do ambiente** (preenchidos pelo usuário; `NÃO INFORMADO` significa que o dado ainda não existe):
```
DESTINATARIO_TESTE   = <e-mail do próprio usuário>
CAIXA_DEPARTAMENTAL  = <endereço da caixa departamental>
GRAPH_CLIENT_ID      = NÃO INFORMADO
GRAPH_TENANT_ID      = NÃO INFORMADO
GRAPH_ESCOPO         = Mail.Send.Shared
GRAPH_USAR_BROKER    = sim
SMTP_HOST            = NÃO INFORMADO
SMTP_PORTA           = 25
SMTP_STARTTLS        = não
```

**Os três exemplos.**
- **B1, Graph por `/me`**: `POST https://graph.microsoft.com/v1.0/me/sendMail`, com `message.from` igual à caixa. A cópia fica nos Itens Enviados do usuário logado.
- **B2, Graph pela caixa**: `POST https://graph.microsoft.com/v1.0/users/{CAIXA_DEPARTAMENTAL}/sendMail`, também com `message.from` igual à caixa. A cópia fica nos Itens Enviados da caixa. Exige que o usuário tenha, além da permissão de envio, acesso total à caixa.
- **C, SMTP por relay interno**: `smtplib` conectando em `SMTP_HOST:SMTP_PORTA`, com o cabeçalho `From` igual à caixa. O relay não guarda cópia em Itens Enviados.

**Fatos técnicos a respeitar.**
- O Graph é usado com permissão delegada (o script age em nome do usuário logado). Para enviar por outra caixa, o escopo é `Mail.Send.Shared` e o usuário precisa ter, na caixa, "Enviar como" (Send As) ou "Enviar em nome de" (Send on Behalf). Sem isso o Graph responde 403 com o código `ErrorSendAsDenied`.
- Sucesso no Graph é HTTP 202 sem corpo. Isso significa "aceito para envio", não "entregue".
- Imagem embutida no Graph: anexo `fileAttachment` com `isInline: true` e `contentId`; o HTML referencia `cid:<contentId>`. No MIME: parte `image/png` com `Content-ID: <logo>` dentro de `multipart/related`.
- Login com a biblioteca `msal`, classe `PublicClientApplication` (cliente público, sem segredo). Com broker (`enable_broker_on_windows=True`, requer `pip install "msal[broker]"`), o login reaproveita a sessão do Windows e o URI de redirecionamento registrado é `ms-appx-web://microsoft.aad.brokerplugin/<client-id>`. Sem broker, o login abre o navegador e o URI é `http://localhost`.
- `smtplib.SMTP.send_message()` devolve um dicionário de destinatários recusados; vazio significa que todos foram aceitos.

**Referência técnica** (trechos já validados; adapte, não reinvente):
```python
# Logo de teste (PNG de cor sólida) e mensagem MIME para a rota C
import struct, zlib
from email.message import EmailMessage
from email.utils import make_msgid

def png_cor_solida(largura, altura, rgb):
    def bloco(tipo, dados):
        corpo = tipo + dados
        return struct.pack(">I", len(dados)) + corpo + struct.pack(">I", zlib.crc32(corpo))
    linha = b"\x00" + bytes(rgb) * largura
    return (b"\x89PNG\r\n\x1a\n"
            + bloco(b"IHDR", struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0))
            + bloco(b"IDAT", zlib.compress(linha * altura))
            + bloco(b"IEND", b""))

def montar_mime(remetente, destinatario, assunto, html, logo_png):
    msg = EmailMessage()
    msg["Message-ID"] = make_msgid(domain=remetente.split("@")[-1])
    msg["From"] = remetente
    msg["To"] = destinatario
    msg["Subject"] = assunto
    msg.set_content("Versão em texto puro.")
    msg.add_alternative(html, subtype="html")        # html contém <img src="cid:logo">
    msg.get_payload()[1].add_related(logo_png, "image", "png", cid="<logo>")
    return msg
```
```python
# Corpo da requisição ao Graph (B1 e B2 usam o mesmo corpo; muda só a URL)
mensagem = {
    "subject": assunto,
    "body": {"contentType": "HTML", "content": html},
    "toRecipients": [{"emailAddress": {"address": destinatario}}],
    "from": {"emailAddress": {"address": caixa}},
    "attachments": [{
        "@odata.type": "#microsoft.graph.fileAttachment",
        "name": "logo.png", "contentType": "image/png",
        "contentBytes": base64.b64encode(logo_png).decode(),
        "contentId": "logo", "isInline": True}],
}
corpo = {"message": mensagem, "saveToSentItems": True}
# requests.post(url, headers={"Authorization": f"Bearer {token}"}, json=corpo, timeout=60)
```
```python
# Token: silencioso primeiro, login só se necessário
app = msal.PublicClientApplication(
    client_id, authority=f"https://login.microsoftonline.com/{tenant_id}",
    enable_broker_on_windows=usar_broker, token_cache=cache)   # cache=None com broker
contas = app.get_accounts()
resultado = app.acquire_token_silent([escopo], account=contas[0]) if contas else None
origem = "silencioso (cache)"
if not resultado:
    resultado = app.acquire_token_interactive(
        [escopo], parent_window_handle=app.CONSOLE_WINDOW_HANDLE, timeout=180)
    origem = "interativo ou broker"
# sucesso: "access_token" em resultado. Falha: resultado["error"] e resultado["error_description"]
# Sem broker, cache cifrado em disco (pacote msal-extensions):
#   from msal_extensions import build_encrypted_persistence, PersistedTokenCache
#   cache = PersistedTokenCache(build_encrypted_persistence(caminho_do_arquivo))
```

## Etapas da tarefa
1. Execute as "Etapas de descoberta" e registre os resultados. Defina, para cada rota, se ela está LIBERADA ou BLOQUEADA para envio real.
2. Crie a pasta `exemplos_envio_email/` na raiz do workspace e, dentro dela, somente estes arquivos:
   - `config.exemplo.ini` e `config.ini` (este com os valores de "Dados do ambiente"), lidos com `configparser`;
   - `comum.py`: leitura da configuração, HTML de teste, logo de teste, assunto com marcador único e a função que imprime a linha `RESULTADO`;
   - `envio_smtp.py` e `exemplo_rota_c.py`;
   - `envio_graph.py`, `exemplo_rota_b1.py` e `exemplo_rota_b2.py`;
   - `tests/test_offline.py` (somente `unittest` e `unittest.mock`, sem rede);
   - `rodar_tudo.py` e `README.md`;
   - `.gitignore` contendo `config.ini` e `.cache/`.
3. Implemente `comum.py`. O HTML de teste deve ter, tudo com CSS inline: `<img src="cid:logo" width="160" height="40">` (logo azul `#1F4E79` gerado por `png_cor_solida(160, 40, (31, 78, 121))`), um título colorido, um parágrafo com as palavras "formatação", "atenção" e "retângulo", e uma tabela com bordas, cabeçalho de fundo `#1F4E79` com texto branco, uma célula de fundo `#C6EFCE` e outra de fundo `#FFC7CE`. O assunto segue o padrão `[TESTE ROTA <B1|B2|C> <8 caracteres hex aleatórios>] Envio silencioso`.
4. Escreva e rode os testes offline de `comum.py`. Só avance com todos passando.
5. Implemente `envio_smtp.py` e `exemplo_rota_c.py`, escreva os testes offline correspondentes e rode.
6. Implemente `envio_graph.py` (obtenção de token e envio nas variantes `me` e `caixa`), os exemplos B1 e B2 e os testes offline correspondentes, e rode.
7. Faça os envios reais, somente nas rotas LIBERADAS, nesta ordem: C, B1, B2. Antes do B1, avise o usuário no chat que uma janela de login da Microsoft pode aparecer uma única vez, e aguarde a conclusão.
8. Teste de controle: se um envio real falhar por permissão de remetente (ver tabela de erros), faça **um** envio adicional na mesma rota com o próprio usuário como remetente (no Graph, via `/me/sendMail` sem `message.from`; no SMTP, `From = DESTINATARIO_TESTE`). Isso separa "a rota funciona, falta permissão na caixa" de "a rota não funciona".
9. Implemente `rodar_tudo.py` (roda os testes offline, depois os exemplos liberados chamando suas funções `main()`, e imprime o relatório) e o `README.md` (pré-requisitos, como preencher `config.ini`, como rodar cada exemplo, como interpretar os resultados).
10. Imprima o "Relatório final".

Cada exemplo deve rodar sozinho com `python exemplo_rota_<x>.py`, expor `main() -> int`, imprimir exatamente uma linha `RESULTADO` e terminar com código de saída 0 (ACEITO), 1 (FALHOU) ou 2 (BLOQUEADO por configuração ausente).

## Restrições
- **Modo oculto (regra principal).** O e-mail é enviado pelo código do início ao fim. É proibido qualquer fluxo em que uma janela de composição, um rascunho ou o Outlook seja aberto para o usuário clicar em Enviar. Não use, em nenhum arquivo: `os.startfile`, `webbrowser`, `subprocess`, arquivos `.eml`, o cabeçalho `X-Unsent`, `mailto:`, `olk.exe`, `win32com`/`pywin32`, nem automação de tela (`pyautogui`, `pywinauto`, Playwright, Selenium).
- A única interface que pode aparecer é a janela de login da Microsoft, e só quando não houver token válido (tipicamente na primeira execução da rota B).
- **Tecnologias proibidas**: EWS/`exchangelib` (em desativação no Exchange Online); `smtp.office365.com` com usuário e senha (autenticação básica será desativada por padrão no fim de dezembro de 2026); Power Automate; qualquer serviço externo de envio.
- **Escopo**: crie e altere arquivos somente dentro de `exemplos_envio_email/`. Não toque em nenhum outro arquivo do workspace nem em configurações do sistema, do proxy, do `pip` ou do Git.
- **Segurança**: nenhuma senha, segredo ou token em código, arquivo ou log; nunca imprima o `access_token`, nem em parte. Nunca desative a verificação TLS (`verify=False` é proibido). Não leia caixas de e-mail e não peça o escopo `Mail.Read`. Cache de token em disco só cifrado, em `exemplos_envio_email/.cache/`; se `msal-extensions` não estiver disponível, use cache apenas em memória.
- **Limite de envios**: destinatário sempre e somente `DESTINATARIO_TESTE`. No máximo 2 envios reais por rota nesta execução (1 normal e 1 de controle). Sem laços de repetição nem novas tentativas automáticas de envio.
- **Dependências**: rota C só com a biblioteca padrão. Rota B: `msal` (ou `msal[broker]` se `GRAPH_USAR_BROKER = sim`), `requests` e, sem broker, `msal-extensions`. Nada além disso.
- Código compatível com Python 3.11, com `encoding="utf-8"` explícito ao ler e escrever arquivos de texto e `sys.stdout.reconfigure(encoding="utf-8")` antes de imprimir.

## Etapas de descoberta
- **D1.** Rode `python --version` e `python -m pip --version`. Se o Python não for 3.11.x, registre e continue.
- **D2.** Leia o bloco "Dados do ambiente". A rota C fica BLOQUEADA se `SMTP_HOST` for `NÃO INFORMADO`. B1 e B2 ficam BLOQUEADAS se `GRAPH_CLIENT_ID` ou `GRAPH_TENANT_ID` for `NÃO INFORMADO`. Todas ficam BLOQUEADAS se `DESTINATARIO_TESTE` ou `CAIXA_DEPARTAMENTAL` não forem endereços de e-mail. Rota bloqueada ainda deve ser implementada e testada offline; só o envio real é pulado. Nunca invente valores.
- **D3.** (Rota B) Verifique se `msal` e `requests` estão instalados; se não, tente `python -m pip install` uma única vez. Se falhar, marque B1 e B2 como BLOQUEADAS por dependência, copie o erro para o relatório e não tente contornar.
- **D4.** (Rota C, se liberada) Sem enviar e-mail, conecte com `smtplib.SMTP(host, porta, timeout=15)`, chame `ehlo()` e registre a saudação e as extensões anunciadas (`STARTTLS`, `AUTH`).
- **D5.** (Rota B, se liberada) Sem autenticar, faça `GET https://login.microsoftonline.com/<GRAPH_TENANT_ID>/v2.0/.well-known/openid-configuration` (esperado: 200) e `GET https://graph.microsoft.com/v1.0/me` sem cabeçalho de autorização (esperado: 401). Isso só detecta bloqueio de rede, proxy, erro de certificado ou tenant inválido.

**Suposições.** Se alguma falhar, pare a rota afetada e relate a mensagem exata:
- `ASSUMPTION A1`: o usuário tem "Enviar como" ou "Enviar em nome de" na caixa. Se falhar, execute o teste de controle e relate; não tente outros remetentes.
- `ASSUMPTION A2`: existe um App Registration com `GRAPH_ESCOPO` consentido e URI de redirecionamento compatível com `GRAPH_USAR_BROKER`. Se o login falhar, relate o código `AADSTS`; não troque de client id e não use ids de aplicativos de terceiros.
- `ASSUMPTION A3`: o relay aceita conexão sem autenticação a partir desta máquina. Se exigir autenticação, pare a rota C; não peça nem use senha.
- `ASSUMPTION A4`: no B2, o endereço da caixa é aceito como identificador em `/users/{...}`. Se vier 404, relate que é preciso o UPN ou o Object ID da caixa.
- `ASSUMPTION A5`: "modo oculto" refere-se ao envio; a janela de login na primeira execução é aceitável.

**Tabela de erros** (interpretação provável, para o campo `detalhe`):
- Graph 401: token ausente, expirado ou inválido.
- Graph 403 `ErrorSendAsDenied`: falta permissão de envio na caixa (A1).
- Graph 403 `ErrorAccessDenied`: token sem o escopo necessário, ou falta acesso total à caixa (B2).
- Graph 404 em `/users/{caixa}`: identificador não resolvido (A4) ou caixa inacessível.
- `AADSTS65001`: consentimento não concedido. `AADSTS50011`: URI de redirecionamento não confere. `AADSTS700016`: client id não existe no tenant. `AADSTS50076`, `AADSTS50079` ou `AADSTS53003`: MFA ou Acesso Condicional barrou.
- `SSLError` / `CERTIFICATE_VERIFY_FAILED`: inspeção TLS corporativa. Não aplique correção; cite no relatório `truststore` e `REQUESTS_CA_BUNDLE` como caminhos a validar com a TI.
- `ProxyError` ou timeout: rede ou proxy.
- SMTP `ConnectionRefusedError` ou timeout: host, porta ou firewall. 530 ou 535: exige autenticação (A3). 550 5.7.1 com "relay": máquina não autorizada no relay. 550 5.7.60 ou texto "send as": remetente não permitido (A1).

## Verificação
**Nível 1, offline (obrigatório, sempre).** `python -m unittest discover -s tests -v` deve terminar com 0 falhas, cobrindo:
1. O logo de teste começa com a assinatura PNG `b"\x89PNG\r\n\x1a\n"`.
2. MIME da rota C: existem partes `text/plain` e `text/html`; a parte `image/png` tem `Content-ID` igual a `<logo>` e o HTML contém `cid:logo`; `From` é a caixa; `To` é o destinatário; o assunto contém o marcador; não existe cabeçalho `X-Unsent`; após `as_bytes()` e novo parse, os acentos do HTML continuam iguais.
3. SMTP com `smtplib.SMTP` substituído por mock: `send_message` é chamado exatamente uma vez; `starttls` só é chamado quando configurado; retorno `{}` vira ACEITO; `SMTPSenderRefused` vira FALHOU com o código no detalhe.
4. Corpo da requisição ao Graph: `message.from.emailAddress.address` é a caixa; `body.contentType` é `HTML`; o anexo tem `isInline` verdadeiro, `contentId` igual a `logo` e `contentBytes` que decodifica para o PNG; `json.dumps` funciona; a URL termina em `/me/sendMail` no B1 e em `/users/<caixa>/sendMail` no B2.
5. Graph com `requests.post` e a obtenção de token substituídos por mock: 202 vira ACEITO; 403 com `{"error": {"code": "ErrorSendAsDenied"}}` vira FALHOU com o código no detalhe; o token nunca aparece na saída impressa.
6. Configuração com `NÃO INFORMADO` faz o exemplo terminar como BLOQUEADO, com código de saída 2 e sem tocar na rede.
7. Modo oculto: varrer todos os `.py` da pasta (exceto `tests/`) e falhar se algum contiver `os.startfile`, `webbrowser`, `subprocess`, `win32com`, `X-Unsent`, `mailto:`, `.eml`, `olk.exe`, `pyautogui`, `pywinauto`, `selenium`, `playwright` ou `verify=False`.

**Nível 2, envio real (rotas liberadas).**
- C: nenhuma exceção e `send_message` devolveu `{}`.
- B1 e B2: HTTP 202.
- Registre a origem do token em cada execução. Se o B2 exigir novo login depois do B1, anote como observação (cache não persistiu), não como falha.
- ACEITO significa aceito pelo servidor. Não declare "entregue".

**Nível 3, confirmação visual (feita pelo usuário).** Para cada envio ACEITO, liste o assunto com o marcador e este checklist: chegou na caixa de entrada de `DESTINATARIO_TESTE`; o remetente exibido é a caixa departamental (anotar se aparece "em nome de"); o retângulo azul do logo aparece sem clicar em "baixar imagens"; a tabela tem cabeçalho escuro, uma célula verde e uma rosa; os acentos estão corretos; nenhuma janela de e-mail abriu durante a execução; onde ficou a cópia em Itens Enviados (B1: do usuário; B2: da caixa; C: nenhuma).

## Relatório final
Imprima exatamente neste formato, sem tokens nem senhas, copiando códigos e mensagens de erro literalmente:
```
=== RELATÓRIO FINAL ===
Ambiente: Python <versão> | msal <versão ou ausente> | requests <versão ou ausente> | broker: <sim/não>
Descoberta: D1 <...> | D2 <...> | D3 <...> | D4 <...> | D5 <...>
Testes offline: <N> executados, <N> falhas (listar as falhas)
RESULTADO | rota=C  | status=<ACEITO|FALHOU|BLOQUEADO> | codigo=<...> | remetente=<...> | marcador=<...> | detalhe=<...>
RESULTADO | rota=B1 | status=<...> | codigo=<...> | remetente=<...> | marcador=<...> | detalhe=<...>
RESULTADO | rota=B2 | status=<...> | codigo=<...> | remetente=<...> | marcador=<...> | detalhe=<...>
Controle (se houve): rota=<...> | remetente=<próprio usuário> | status=<...> | detalhe=<...>
Origem do token: B1=<...> | B2=<...>
Modo oculto: <OK | violação: ...>
Suposições que falharam: <A1..A5 ou nenhuma>, com a mensagem exata
Pendências para a TI: <lista objetiva>
Arquivos criados: <lista>
Checklist para o usuário: <itens do Nível 3, por marcador>
=== FIM ===
```

## Notas por modelo
- **composer-2.5**: siga as etapas na ordem; crie somente os arquivos listados; não refatore nem melhore nada fora da pasta. Ao encontrar uma condição de parada (suposição falhou, dependência indisponível, erro de TLS), pare aquela rota imediatamente e vá para o relatório, sem tentar alternativas.
- **Grok 4.5 High**: antes de codar, escreva um plano curto ligando cada critério da seção "Verificação" a um teste. Priorize os casos de borda (configuração ausente, respostas de erro, acentos) e a prova de que nenhuma janela é aberta.

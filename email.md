"""
Teste de envio de e-mail HTML sem o Outlook classico (Python 3.11+).

Rotas A e C usam somente a biblioteca padrao.
Rota B precisa de:  pip install "msal[broker]" requests
"""
import base64
import os
import smtplib
import tempfile
import uuid
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path

# ============================== CONFIGURACAO ==============================
ROTA = "A"   # "A" = rascunho .eml | "B" = Microsoft Graph | "C" = SMTP (relay)

DESTINATARIO = "voce@suaempresa.com.br"   # mande o teste para voce mesmo
CAIXA = ""   # "" = sai do seu e-mail. Depois teste com "departamento@suaempresa.com.br"

# --- Rota B: dados que a TI fornece ao criar o App Registration ---
CLIENT_ID = "cole-aqui-o-client-id"
TENANT_ID = "cole-aqui-o-tenant-id"
ESCOPO = "Mail.Send.Shared"   # troque por "Mail.Send" se a TI liberou so essa
USAR_BROKER = True            # False = login pelo navegador (redirect http://localhost)

# --- Rota C: dados que a TI fornece ---
SMTP_HOST = "relay.suaempresa.com.br"
SMTP_PORT = 25
SMTP_STARTTLS = False
# ==========================================================================

ASSUNTO = f"Teste de envio - rota {ROTA.upper()}"

# PNG de 1 pixel azul. O HTML estica para 160x40 so para provar que imagem
# embutida funciona. Para testar o logo real, troque por:
#   LOGO = Path(r"C:\pasta\logo.png").read_bytes()
LOGO = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR42mOQ96sEAAF2AOeIcoD6"
    "AAAAAElFTkSuQmCC")

BORDA = "border:1px solid #999999"
HTML = f"""\
<html><body style="font-family:Segoe UI,Arial,sans-serif;font-size:14px;color:#222222">
<img src="cid:logo" width="160" height="40" alt="logo de teste">
<h2 style="color:#1F4E79">Teste de formatação</h2>
<p>Se você vê o retângulo azul acima, a tabela colorida abaixo e este trecho em
<b>negrito</b>, com os acentos corretos, o HTML chegou inteiro.</p>
<table cellpadding="6" cellspacing="0" style="border-collapse:collapse;{BORDA}">
<tr style="background:#1F4E79;color:#ffffff"><th>Indicador</th><th>Valor</th><th>Status</th></tr>
<tr><td style="{BORDA}">Linha 1</td><td style="{BORDA}" align="right">1.234,56</td>
    <td style="{BORDA};background:#C6EFCE">OK</td></tr>
<tr><td style="{BORDA}">Linha 2</td><td style="{BORDA}" align="right">78,90</td>
    <td style="{BORDA};background:#FFC7CE">Atenção</td></tr>
</table>
</body></html>
"""


def montar_mime(rascunho=False):
    """Mensagem completa: texto puro + HTML + imagem embutida (cid:logo)."""
    msg = EmailMessage()
    if rascunho:
        msg["X-Unsent"] = "1"          # faz o Outlook novo abrir como rascunho
    msg["Message-ID"] = make_msgid(domain=DESTINATARIO.split("@")[-1])
    if CAIXA or not rascunho:
        msg["From"] = CAIXA or DESTINATARIO
    msg["To"] = DESTINATARIO
    msg["Subject"] = ASSUNTO
    msg.set_content("Versao em texto puro do teste.")
    msg.add_alternative(HTML, subtype="html")
    msg.get_payload()[1].add_related(LOGO, "image", "png", cid="<logo>")
    return msg


def rota_a():
    """Gera um .eml e abre no Outlook novo como rascunho (voce clica em Enviar)."""
    eml = Path(tempfile.gettempdir()) / f"teste_{uuid.uuid4().hex}.eml"
    eml.write_bytes(montar_mime(rascunho=True).as_bytes())
    os.startfile(str(eml))
    print(f"Arquivo gerado: {eml}")
    print("Deve abrir no Outlook novo como rascunho editavel.")
    print("Confira: formatacao, campo 'De' e se o botao Enviar funciona.")


def rota_b():
    """Envia direto pelo Microsoft Graph, sem abrir o Outlook."""
    import msal        # importados aqui para as rotas A e C rodarem sem eles
    import requests

    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        enable_broker_on_windows=USAR_BROKER)
    token = app.acquire_token_interactive(
        [ESCOPO], parent_window_handle=app.CONSOLE_WINDOW_HANDLE)
    if "access_token" not in token:
        print("Falha no login:", token.get("error"), "-", token.get("error_description"))
        return

    mensagem = {
        "subject": ASSUNTO,
        "body": {"contentType": "HTML", "content": HTML},
        "toRecipients": [{"emailAddress": {"address": DESTINATARIO}}],
        "attachments": [{
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": "logo.png",
            "contentType": "image/png",
            "contentBytes": base64.b64encode(LOGO).decode(),
            "contentId": "logo",
            "isInline": True,
        }],
    }
    if CAIXA:
        mensagem["from"] = {"emailAddress": {"address": CAIXA}}

    resposta = requests.post(
        "https://graph.microsoft.com/v1.0/me/sendMail",
        headers={"Authorization": f"Bearer {token['access_token']}"},
        json={"message": mensagem},
        timeout=60)
    if resposta.status_code == 202:
        print("Enviado (202). Confira a caixa de entrada.")
    else:
        print(f"Erro {resposta.status_code}: {resposta.text}")


def rota_c():
    """Envia direto pelo servidor SMTP interno (relay)."""
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as servidor:
        if SMTP_STARTTLS:
            servidor.starttls()
        servidor.send_message(montar_mime())
    print("Entregue ao relay sem erro. Confira a caixa de entrada.")


if __name__ == "__main__":
    print(f"Rota {ROTA.upper()} | remetente: {CAIXA or 'seu proprio e-mail'} | para: {DESTINATARIO}")
    try:
        {"A": rota_a, "B": rota_b, "C": rota_c}[ROTA.upper()]()
    except Exception as erro:
        print(f"FALHOU -> {type(erro).__name__}: {erro}")

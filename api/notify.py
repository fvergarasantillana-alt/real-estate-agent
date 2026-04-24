"""
Lead notification system.
Sends an email (Gmail SMTP) and a WhatsApp message (Meta Cloud API) to the agent
whenever a new lead is captured — either from the contact form or the WhatsApp bot.
"""

import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from tools.copy import AGENT_NAME


def _send_email(lead: dict) -> None:
    gmail_user    = os.environ['GMAIL_USER']
    gmail_pass    = os.environ['GMAIL_APP_PASSWORD']
    agent_email   = os.environ['AGENT_EMAIL']

    subject = f"🏠 New Lead: {lead.get('name', 'Unknown')} — {lead.get('intent', 'General inquiry')}"

    html = f"""
    <h2 style="color:#1a4f7a;">New Real Estate Lead</h2>
    <table style="border-collapse:collapse;width:100%;max-width:480px;">
      <tr><td style="padding:8px;font-weight:bold;">Name</td>    <td style="padding:8px;">{lead.get('name', '—')}</td></tr>
      <tr style="background:#f8f9fa;"><td style="padding:8px;font-weight:bold;">Email</td>   <td style="padding:8px;">{lead.get('email', '—')}</td></tr>
      <tr><td style="padding:8px;font-weight:bold;">Phone</td>   <td style="padding:8px;">{lead.get('phone', '—')}</td></tr>
      <tr style="background:#f8f9fa;"><td style="padding:8px;font-weight:bold;">Looking for</td><td style="padding:8px;">{lead.get('intent', lead.get('message', '—'))}</td></tr>
      <tr><td style="padding:8px;font-weight:bold;">Source</td>  <td style="padding:8px;">{lead.get('source', '—')}</td></tr>
    </table>
    <p style="margin-top:20px;color:#6b7280;font-size:0.85rem;">Sent by {AGENT_NAME}'s automated lead system.</p>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = gmail_user
    msg['To']      = agent_email
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(gmail_user, gmail_pass)
        server.sendmail(gmail_user, agent_email, msg.as_string())


def _send_whatsapp(lead: dict) -> None:
    token    = os.environ['META_WHATSAPP_TOKEN']
    phone_id = os.environ['META_PHONE_NUMBER_ID']
    to       = os.environ['AGENT_WHATSAPP_NUMBER'].replace('+', '').replace(' ', '')

    text = (
        f"🏠 *Nuevo Lead / New Lead*\n\n"
        f"*Nombre:* {lead.get('name', '—')}\n"
        f"*Email:* {lead.get('email', '—')}\n"
        f"*Teléfono:* {lead.get('phone', '—')}\n"
        f"*Busca:* {lead.get('intent', lead.get('message', '—'))}\n"
        f"*Fuente:* {lead.get('source', '—')}"
    )

    httpx.post(
        f"https://graph.facebook.com/v19.0/{phone_id}/messages",
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type':  'application/json',
        },
        json={
            'messaging_product': 'whatsapp',
            'to': to,
            'type': 'text',
            'text': {'body': text},
        },
        timeout=10,
    ).raise_for_status()


def notify_lead(lead: dict) -> dict[str, bool]:
    """
    Send email + WhatsApp notifications to the agent.
    Returns {"email": bool, "whatsapp": bool} indicating what succeeded.
    """
    results = {"email": False, "whatsapp": False}
    try:
        _send_email(lead)
        results["email"] = True
    except Exception as exc:
        print(f"[notify] email failed: {exc}")

    try:
        _send_whatsapp(lead)
        results["whatsapp"] = True
    except Exception as exc:
        print(f"[notify] whatsapp failed: {exc}")

    return results

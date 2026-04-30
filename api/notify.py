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


def _summary_line(lead: dict) -> str:
    parts = []
    name = lead.get('name', '')
    intent_map = {'buy': 'quiere comprar', 'sell': 'quiere vender', 'rent': 'quiere rentar'}
    intent = intent_map.get(lead.get('intent', '').lower(), lead.get('intent', ''))
    prop = lead.get('property_type', '')
    location = lead.get('location', '')
    budget = lead.get('budget', '')
    timeline = lead.get('timeline', '')

    if name:
        parts.append(name)
    if intent:
        parts.append(intent)
    if prop and prop != 'unknown':
        parts.append(f"una {prop}")
    if location and location != 'unknown':
        parts.append(f"en {location}")
    if budget and budget != 'unknown':
        parts.append(f"presupuesto {budget}")
    if timeline and timeline != 'unknown':
        parts.append(f"— {timeline}")

    return ', '.join(parts) if parts else 'Nuevo lead'


def _row(label: str, value: str, alt: bool = False) -> str:
    bg = ' style="background:#f8f9fa;"' if alt else ''
    return f'<tr{bg}><td style="padding:8px;font-weight:bold;">{label}</td><td style="padding:8px;">{value or "—"}</td></tr>'


def _send_email(lead: dict) -> None:
    gmail_user  = os.environ['GMAIL_USER']
    gmail_pass  = os.environ['GMAIL_APP_PASSWORD']
    agent_email = os.environ['AGENT_EMAIL']

    name   = lead.get('name', 'Desconocido')
    intent = lead.get('intent', 'Consulta general')
    subject = f"🏠 Nuevo Lead: {name} — {intent}"

    listings_shown = lead.get('listings_shown', [])
    listings_html = ''
    if listings_shown:
        items = ''.join(f'<li>{a}</li>' for a in listings_shown)
        listings_html = f'<p style="margin-top:16px;font-weight:bold;">Propiedades mostradas al cliente:</p><ul>{items}</ul>'

    rows = ''.join([
        _row('Nombre',             lead.get('name', '')),
        _row('Email',              lead.get('email', ''),         alt=True),
        _row('Teléfono',           lead.get('phone', '')),
        _row('Intención',          lead.get('intent', ''),        alt=True),
        _row('Tipo de propiedad',  lead.get('property_type', '')),
        _row('Ubicación',          lead.get('location', ''),      alt=True),
        _row('Presupuesto',        lead.get('budget', '')),
        _row('Timeline',           lead.get('timeline', ''),      alt=True),
        _row('Notas',              lead.get('notes', lead.get('message', ''))),
        _row('Fuente',             lead.get('source', ''),        alt=True),
    ])

    html = f"""
    <h2 style="color:#1a4f7a;">Nuevo Lead de Bienes Raíces</h2>
    <p style="color:#374151;font-size:1rem;margin-bottom:16px;"><strong>{_summary_line(lead)}</strong></p>
    <table style="border-collapse:collapse;width:100%;max-width:520px;">
      {rows}
    </table>
    {listings_html}
    <p style="margin-top:20px;color:#6b7280;font-size:0.85rem;">Enviado por el sistema automático de leads de {AGENT_NAME}.</p>
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

    listings_shown = lead.get('listings_shown', [])
    listings_part = ''
    if listings_shown:
        listings_part = '\n*Listings shown:*\n' + '\n'.join(f'  • {a}' for a in listings_shown)

    text = (
        f"🏠 *Nuevo Lead / New Lead*\n"
        f"_{_summary_line(lead)}_\n\n"
        f"*Nombre:* {lead.get('name', '—')}\n"
        f"*Email:* {lead.get('email', '—')}\n"
        f"*Teléfono:* {lead.get('phone', '—')}\n"
        f"*Intención:* {lead.get('intent', '—')}\n"
        f"*Tipo de propiedad:* {lead.get('property_type', '—')}\n"
        f"*Ubicación:* {lead.get('location', '—')}\n"
        f"*Presupuesto:* {lead.get('budget', '—')}\n"
        f"*Timeline:* {lead.get('timeline', '—')}\n"
        f"*Notas:* {lead.get('notes', lead.get('message', '—'))}\n"
        f"*Fuente:* {lead.get('source', '—')}"
        f"{listings_part}"
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


def notify_handoff(wa_number: str, message: str) -> None:
    """Alert the agent that a non-real-estate message needs their personal reply."""
    try:
        token    = os.environ['META_WHATSAPP_TOKEN']
        phone_id = os.environ['META_PHONE_NUMBER_ID']
        to       = os.environ['AGENT_WHATSAPP_NUMBER'].replace('+', '').replace(' ', '')
        text     = f"📩 Mensaje directo de +{wa_number}:\n\"{message}\"\n\nEsto no es sobre bienes raíces — responde tú directamente."
        httpx.post(
            f"https://graph.facebook.com/v19.0/{phone_id}/messages",
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json={'messaging_product': 'whatsapp', 'to': to, 'type': 'text', 'text': {'body': text}},
            timeout=10,
        ).raise_for_status()
    except Exception as exc:
        print(f"[notify] handoff whatsapp failed: {exc}")

    try:
        gmail_user  = os.environ['GMAIL_USER']
        gmail_pass  = os.environ['GMAIL_APP_PASSWORD']
        agent_email = os.environ['AGENT_EMAIL']
        subject     = f"📩 Mensaje directo de +{wa_number} (no es real estate)"
        html        = f"<p><strong>De:</strong> +{wa_number}</p><p><strong>Mensaje:</strong> {message}</p><p>Este mensaje no es sobre bienes raíces. Responde directamente.</p>"
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = gmail_user
        msg['To']      = agent_email
        msg.attach(MIMEText(html, 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, agent_email, msg.as_string())
    except Exception as exc:
        print(f"[notify] handoff email failed: {exc}")


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

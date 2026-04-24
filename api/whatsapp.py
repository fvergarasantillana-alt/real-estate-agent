"""
Vercel serverless function — POST /api/whatsapp
Meta WhatsApp Cloud API webhook handler.

GET  /api/whatsapp  → webhook verification (Meta sends this once during setup)
POST /api/whatsapp  → incoming messages
"""

import hashlib
import hmac
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import api.claude_chat as chat
import api.notify as notify


def _verify_signature(body: bytes, signature: str) -> bool:
    """Validate that the request came from Meta."""
    app_secret = os.environ.get('META_APP_SECRET', '')
    if not app_secret:
        return True  # skip in dev / sandbox
    expected = 'sha256=' + hmac.new(
        app_secret.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def handler(request, response):
    # ── Webhook verification (GET) ─────────────────────────────────────
    if request.method == 'GET':
        params = request.query or {}
        mode      = params.get('hub.mode')
        token     = params.get('hub.verify_token')
        challenge = params.get('hub.challenge')
        if mode == 'subscribe' and token == os.environ.get('META_VERIFY_TOKEN'):
            response.status_code = 200
            response.body = challenge
        else:
            response.status_code = 403
            response.body = 'Forbidden'
        return

    # ── Incoming message (POST) ────────────────────────────────────────
    if request.method != 'POST':
        response.status_code = 405
        response.body = 'Method Not Allowed'
        return

    body_bytes = request.body if isinstance(request.body, bytes) else request.body.encode()
    sig = request.headers.get('x-hub-signature-256', '')
    if not _verify_signature(body_bytes, sig):
        response.status_code = 401
        response.body = 'Unauthorized'
        return

    try:
        data = json.loads(body_bytes)
    except json.JSONDecodeError:
        response.status_code = 400
        response.body = 'Bad Request'
        return

    # Meta sends nested structure; dig out the message
    try:
        entry   = data['entry'][0]
        changes = entry['changes'][0]
        value   = changes['value']
        message = value['messages'][0]
    except (KeyError, IndexError):
        # Not a message event (e.g. status update) — acknowledge and ignore
        response.status_code = 200
        response.body = 'ok'
        return

    wa_number    = message['from']          # e.g. "13055551234"
    message_type = message.get('type', '')

    if message_type != 'text':
        # Ignore non-text messages (images, audio, etc.)
        response.status_code = 200
        response.body = 'ok'
        return

    user_text = message['text']['body']

    # Generate reply via Claude
    result = chat.reply(wa_number, user_text)
    reply_text   = result.get('message', 'Sorry, something went wrong.')
    lead_captured = result.get('lead_captured')

    # Send reply back to the user
    _send_whatsapp_reply(wa_number, reply_text)

    # If Claude captured a lead, notify the agent
    if lead_captured:
        lead_captured['source'] = 'whatsapp_bot'
        lead_captured['phone'] = lead_captured.get('phone') or f'+{wa_number}'
        notify.notify_lead(lead_captured)

    response.status_code = 200
    response.body = 'ok'


def _send_whatsapp_reply(to: str, text: str) -> None:
    import httpx
    token    = os.environ['META_WHATSAPP_TOKEN']
    phone_id = os.environ['META_PHONE_NUMBER_ID']
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

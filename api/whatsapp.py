from http.server import BaseHTTPRequestHandler
import hashlib
import hmac
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import api.claude_chat as chat
import api.notify as notify


def _verify_signature(body: bytes, signature: str) -> bool:
    app_secret = os.environ.get('META_APP_SECRET', '')
    if not app_secret:
        return True
    expected = 'sha256=' + hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _send_reply(to: str, text: str) -> None:
    import httpx
    token    = os.environ['META_WHATSAPP_TOKEN']
    phone_id = os.environ['META_PHONE_NUMBER_ID']
    httpx.post(
        f"https://graph.facebook.com/v19.0/{phone_id}/messages",
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json={'messaging_product': 'whatsapp', 'to': to, 'type': 'text', 'text': {'body': text}},
        timeout=10,
    ).raise_for_status()


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        params    = parse_qs(urlparse(self.path).query)
        mode      = params.get('hub.mode', [''])[0]
        token     = params.get('hub.verify_token', [''])[0]
        challenge = params.get('hub.challenge', [''])[0]
        if mode == 'subscribe' and token == os.environ.get('META_VERIFY_TOKEN', ''):
            self._text(200, challenge)
        else:
            self._text(403, 'Forbidden')

    def do_POST(self):
        length     = int(self.headers.get('Content-Length', 0))
        body_bytes = self.rfile.read(length)
        sig        = self.headers.get('x-hub-signature-256', '')

        if not _verify_signature(body_bytes, sig):
            self._text(401, 'Unauthorized')
            return

        try:
            data = json.loads(body_bytes)
        except json.JSONDecodeError:
            self._text(400, 'Bad Request')
            return

        try:
            message = data['entry'][0]['changes'][0]['value']['messages'][0]
        except (KeyError, IndexError):
            self._text(200, 'ok')
            return

        if message.get('type') != 'text':
            self._text(200, 'ok')
            return

        wa_number = message['from']
        user_text = message['text']['body']

        result        = chat.reply(wa_number, user_text)
        reply_text    = result.get('message', 'Sorry, something went wrong.')
        lead_captured = result.get('lead_captured')

        _send_reply(wa_number, reply_text)

        if lead_captured:
            lead_captured['source'] = 'whatsapp_bot'
            lead_captured.setdefault('phone', f'+{wa_number}')
            notify.notify_lead(lead_captured)

        self._text(200, 'ok')

    def _text(self, status, text):
        body = text.encode()
        self.send_response(status)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass

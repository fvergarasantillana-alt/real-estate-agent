from flask import Flask, request, jsonify, send_from_directory, Response
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__, static_folder='../public/static', static_url_path='/static')

PUBLIC_DIR = Path(__file__).parent.parent / 'public'


@app.route('/')
def index():
    wa_number = os.environ.get('AGENT_WHATSAPP_NUMBER', '')
    html = (PUBLIC_DIR / 'index.html').read_text(encoding='utf-8')
    config_script = f'<script>window.AGENT_WA_NUMBER = "{wa_number}";</script>'
    html = html.replace('<script>', config_script + '\n<script>', 1)
    return Response(html, mimetype='text/html')


@app.route('/api/config')
def config():
    return jsonify({'whatsapp_number': os.environ.get('AGENT_WHATSAPP_NUMBER', '')})


@app.route('/api/listings')
def listings():
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON', '')
        sheet_id   = os.environ.get('GOOGLE_SHEET_ID', '')

        if not creds_json or not sheet_id:
            return jsonify({'listings': []})

        creds   = Credentials.from_service_account_info(json.loads(creds_json),
                    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
        service = build('sheets', 'v4', credentials=creds)
        result  = service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range='Sheet1!A1:J200'
        ).execute()

        rows = result.get('values', [])
        if len(rows) < 2:
            return jsonify({'listings': []})

        headers  = [h.strip().lower().replace(' ', '_') for h in rows[0]]
        listings = []
        for row in rows[1:]:
            if not any(row):
                continue
            item = {headers[i]: row[i].strip() if i < len(row) else '' for i in range(len(headers))}
            listings.append(item)

        resp = jsonify({'listings': listings})
        resp.headers['Cache-Control'] = 'public, s-maxage=600'
        return resp
    except Exception as exc:
        return jsonify({'listings': [], 'error': str(exc)})


@app.route('/api/contact', methods=['POST'])
def contact():
    import api.notify as notify
    data = request.get_json(silent=True) or {}
    lead = {
        'name':    data.get('name', '').strip(),
        'email':   data.get('email', '').strip(),
        'phone':   data.get('phone', '').strip(),
        'intent':  data.get('message', '').strip(),
        'source':  'contact_form',
    }
    if not lead['name'] or not lead['email']:
        return jsonify({'error': 'name and email required'}), 400
    results = notify.notify_lead(lead)
    return jsonify({'ok': True, 'notifications': results})


@app.route('/api/whatsapp', methods=['GET', 'POST'])
def whatsapp():
    if request.method == 'GET':
        mode      = request.args.get('hub.mode')
        token     = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if mode == 'subscribe' and token == os.environ.get('META_VERIFY_TOKEN', ''):
            return Response(challenge, mimetype='text/plain')
        return Response('Forbidden', status=403)

    import api.claude_chat as chat
    import api.notify as notify
    import httpx

    body_bytes = request.get_data()
    data = request.get_json(silent=True) or {}

    try:
        message   = data['entry'][0]['changes'][0]['value']['messages'][0]
    except (KeyError, IndexError):
        return Response('ok')

    if message.get('type') != 'text':
        return Response('ok')

    wa_number     = message['from']
    user_text     = message['text']['body']
    result        = chat.reply(wa_number, user_text)
    reply_text    = result.get('message', 'Sorry, something went wrong.')
    lead_captured = result.get('lead_captured')

    token    = os.environ.get('META_WHATSAPP_TOKEN', '')
    phone_id = os.environ.get('META_PHONE_NUMBER_ID', '')
    if token and phone_id:
        httpx.post(
            f"https://graph.facebook.com/v19.0/{phone_id}/messages",
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json={'messaging_product': 'whatsapp', 'to': wa_number, 'type': 'text', 'text': {'body': reply_text}},
            timeout=10,
        )

    if lead_captured:
        lead_captured['source'] = 'whatsapp_bot'
        lead_captured.setdefault('phone', f'+{wa_number}')
        notify.notify_lead(lead_captured)

    return Response('ok')


if __name__ == '__main__':
    app.run(debug=True)

"""
Vercel serverless function — GET /
Serves the landing page HTML, injecting the agent's WhatsApp number
as a JS config variable so the frontend can build the wa.me link.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.copy import AGENT_NAME

TEMPLATE_PATH = Path(__file__).parent.parent / 'tools' / 'templates' / 'index.html'


def handler(request, response):
    wa_number = os.environ.get('AGENT_WHATSAPP_NUMBER', '')
    html = TEMPLATE_PATH.read_text(encoding='utf-8')

    config_script = f'<script>window.AGENT_WA_NUMBER = "{wa_number}";</script>'
    html = html.replace('<script>', config_script + '\n<script>', 1)

    response.status_code = 200
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.body = html

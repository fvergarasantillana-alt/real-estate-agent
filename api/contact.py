"""
Vercel serverless function — POST /api/contact
Handles contact form submissions from the landing page.
Sends lead notifications to the agent.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import api.notify as notify


def handler(request, response):
    if request.method != 'POST':
        response.status_code = 405
        response.body = 'Method Not Allowed'
        return

    try:
        body = request.body
        data = json.loads(body if isinstance(body, str) else body.decode())
    except (json.JSONDecodeError, Exception):
        response.status_code = 400
        response.body = json.dumps({'error': 'Invalid JSON'})
        return

    lead = {
        'name':    data.get('name', '').strip(),
        'email':   data.get('email', '').strip(),
        'phone':   data.get('phone', '').strip(),
        'message': data.get('message', '').strip(),
        'intent':  data.get('message', '').strip(),
        'source':  'contact_form',
    }

    if not lead['name'] or not lead['email']:
        response.status_code = 400
        response.headers['Content-Type'] = 'application/json'
        response.body = json.dumps({'error': 'name and email are required'})
        return

    results = notify.notify_lead(lead)

    response.status_code = 200
    response.headers['Content-Type'] = 'application/json'
    response.body = json.dumps({'ok': True, 'notifications': results})

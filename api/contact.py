from http.server import BaseHTTPRequestHandler
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import api.notify as notify


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body   = self.rfile.read(length)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, {'error': 'Invalid JSON'})
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
            self._respond(400, {'error': 'name and email are required'})
            return

        results = notify.notify_lead(lead)
        self._respond(200, {'ok': True, 'notifications': results})

    def _respond(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass

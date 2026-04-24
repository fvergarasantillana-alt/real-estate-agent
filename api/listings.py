from http.server import BaseHTTPRequestHandler
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES   = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '')
RANGE    = 'Sheet1!A1:J200'


def _get_listings():
    creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON', '')
    if not creds_json or not SHEET_ID:
        return []
    creds   = Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    result  = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=RANGE
    ).execute()
    rows = result.get('values', [])
    if len(rows) < 2:
        return []
    headers = [h.strip().lower().replace(' ', '_') for h in rows[0]]
    listings = []
    for row in rows[1:]:
        if not any(row):
            continue
        item = {headers[i]: row[i].strip() if i < len(row) else '' for i in range(len(headers))}
        listings.append(item)
    return listings


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            listings = _get_listings()
            body = json.dumps({'listings': listings}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'public, s-maxage=600')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            body = json.dumps({'error': str(exc), 'listings': []}).encode()
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, format, *args):
        pass

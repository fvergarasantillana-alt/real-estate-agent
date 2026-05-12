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

RAPIDAPI_KEY  = os.environ.get('RAPIDAPI_KEY', '')
RAPIDAPI_HOST = 'us-housing-market-data1.p.rapidapi.com'

_HOME_TYPE_MAP = {
    'house':      'Houses',
    'condo':      'Condos',
    'apartment':  'Apartments_Condos_Co-ops',
    'commercial': 'MultiFamily',
}


def search_listings(criteria: dict) -> list[dict]:
    if not RAPIDAPI_KEY:
        return _get_listings()

    params = {'location': criteria.get('location', 'Miami-Dade County, FL')}
    params['status_type'] = 'ForRent' if criteria.get('intent', '').lower() == 'rent' else 'ForSale'

    prop = criteria.get('property_type', '').lower()
    if prop in _HOME_TYPE_MAP:
        params['home_type'] = _HOME_TYPE_MAP[prop]
    if criteria.get('budget_max'):
        params['price_max'] = int(criteria['budget_max'])
    if criteria.get('budget_min'):
        params['price_min'] = int(criteria['budget_min'])
    if criteria.get('bedrooms'):
        params['beds_min'] = int(criteria['bedrooms'])

    try:
        import httpx
        resp = httpx.get(
            f'https://{RAPIDAPI_HOST}/propertyExtendedSearch',
            params=params,
            headers={'x-rapidapi-key': RAPIDAPI_KEY, 'x-rapidapi-host': RAPIDAPI_HOST},
            timeout=8,
        )
        resp.raise_for_status()
        props = resp.json().get('props', [])[:5]
    except Exception:
        return _get_listings()

    results = []
    for p in props:
        price = str(p.get('price', ''))
        try:
            price = str(int(float(price.replace(',', ''))))
        except (ValueError, TypeError):
            pass
        url = p.get('detailUrl', '')
        if url and not url.startswith('http'):
            url = 'https://www.zillow.com' + url
        results.append({
            'address':        p.get('address', ''),
            'price':          price,
            'bedrooms':       str(p.get('bedrooms', '')),
            'bathrooms':      str(p.get('bathrooms', '')),
            'sqft':           str(p.get('livingArea', '')),
            'description_en': '',
            'description_es': '',
            'image_url':      p.get('imgSrc', ''),
            'zillow_url':     url,
        })

    return results if results else _get_listings()


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

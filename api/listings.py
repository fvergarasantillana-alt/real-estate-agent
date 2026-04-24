"""
Vercel serverless function — GET /api/listings
Reads from a Google Sheet and returns listings as JSON.
Cached for 10 minutes via Vercel's Cache-Control header.

Google Sheet columns (row 1 = headers):
  address | price | bedrooms | bathrooms | sqft | type |
  zillow_url | image_url | description_en | description_es
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SHEET_ID = os.environ['GOOGLE_SHEET_ID']
RANGE    = 'Sheet1!A1:J200'


def _get_listings():
    creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    if not creds_json:
        raise RuntimeError('GOOGLE_SERVICE_ACCOUNT_JSON env var not set')

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


def handler(request, response):
    try:
        listings = _get_listings()
        body = json.dumps({'listings': listings})
        response.status_code = 200
        response.headers['Content-Type']  = 'application/json'
        response.headers['Cache-Control'] = 'public, s-maxage=600, stale-while-revalidate=60'
        response.body = body
    except Exception as exc:
        response.status_code = 500
        response.headers['Content-Type'] = 'application/json'
        response.body = json.dumps({'error': str(exc), 'listings': []})

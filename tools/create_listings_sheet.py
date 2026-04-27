"""
Creates a new Google Sheet for a client's listings with the correct headers
and sample data. Shares it with the service account automatically.

Usage:
    python tools/create_listings_sheet.py

Requires in .env:
    GOOGLE_SERVICE_ACCOUNT_JSON   — service account key JSON string
    AGENT_NAME                    — used to name the sheet

Outputs:
    - Sheet URL (open in browser to view/edit)
    - GOOGLE_SHEET_ID value to paste into Vercel env vars
"""

import json
import os
import sys
from pathlib import Path

# Remove tools/ from path so tools/copy.py doesn't shadow stdlib's copy module
_tools_dir = str(Path(__file__).parent)
if _tools_dir in sys.path:
    sys.path.remove(_tools_dir)

# Load .env manually (avoid dotenv which also triggers google imports)
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]

HEADERS = [
    'address', 'price', 'bedrooms', 'bathrooms', 'sqft',
    'description_en', 'description_es', 'image_url', 'zillow_url'
]

SAMPLE_ROWS = [
    [
        '123 Ocean Drive, Miami Beach, FL 33139',
        '850000', '3', '2', '1800',
        'Beautiful oceanfront condo with stunning views and modern finishes.',
        'Hermoso condominio frente al mar con vistas impresionantes y acabados modernos.',
        '', ''
    ],
    [
        '456 Brickell Ave #1201, Miami, FL 33131',
        '620000', '2', '2', '1200',
        'Luxury high-rise unit in the heart of Brickell with city and bay views.',
        'Lujoso piso alto en el corazón de Brickell con vistas a la ciudad y la bahía.',
        '', ''
    ],
    [
        '789 SW 8th St, Coral Gables, FL 33130',
        '1150000', '4', '3', '2800',
        'Spacious single-family home in a quiet Coral Gables neighborhood.',
        'Amplia casa unifamiliar en un tranquilo vecindario de Coral Gables.',
        '', ''
    ],
]


def main():
    creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON', '')
    sheet_id   = os.environ.get('GOOGLE_SHEET_ID', '')
    agent_name = os.environ.get('AGENT_NAME', 'Agent')

    if not creds_json:
        print("ERROR: GOOGLE_SERVICE_ACCOUNT_JSON not set in .env")
        sys.exit(1)
    if not sheet_id:
        print("ERROR: GOOGLE_SHEET_ID not set in .env")
        sys.exit(1)

    creds_info = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)

    sheets = build('sheets', 'v4', credentials=creds)

    # Write headers + sample data
    values = [HEADERS] + SAMPLE_ROWS
    sheets.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range='Sheet1!A1',
        valueInputOption='RAW',
        body={'values': values},
    ).execute()

    # Bold the header row
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={'requests': [{
            'repeatCell': {
                'range': {'sheetId': 0, 'startRowIndex': 0, 'endRowIndex': 1},
                'cell': {'userEnteredFormat': {'textFormat': {'bold': True}}},
                'fields': 'userEnteredFormat.textFormat.bold',
            }
        }]}
    ).execute()

    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
    print(f"\nSheet populated: {agent_name} — Listings")
    print(f"\nSheet URL:\n   {sheet_url}")
    print(f"\nGOOGLE_SHEET_ID = {sheet_id}")


if __name__ == '__main__':
    main()

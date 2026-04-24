# Workflow: Update Listings

## Objective
Add, update, or remove featured listings shown on the landing page without touching any code.

## Tool
Google Sheets (browser — no software needed)

## Steps

### Add a listing
1. Open the Google Sheet (bookmark it for easy access)
2. Go to the last empty row
3. Fill in each column:
   - **address** — e.g. `1234 Brickell Ave #501, Miami, FL 33131`
   - **price** — number only, no $ or commas → e.g. `450000`
   - **bedrooms** — number → e.g. `3`
   - **bathrooms** — number → e.g. `2`
   - **sqft** — number → e.g. `1400`
   - **type** — `buy`, `sell`, or `rent`
   - **zillow_url** — paste the full Zillow listing URL (optional but recommended)
   - **image_url** — direct link to a property photo (optional; leave blank for no image)
   - **description_en** — 1–2 sentence description in English
   - **description_es** — same description in Spanish
4. Save (Cmd+S or auto-saves)
5. Changes appear on the website within 10 minutes

### Remove a listing
Delete the entire row for that listing.

### Update a listing
Edit any cell in the row — price, description, Zillow link, etc.

## Tips
- Leave `image_url` blank if you don't have a photo — a placeholder will show instead
- You can get a Zillow listing URL from your Zillow profile page
- Keep descriptions short (1–2 sentences) — they're truncated on the card anyway
- The sheet is read-only from the website's perspective, so only you can edit it

## Update Log
- 2026-04-23: Initial workflow created

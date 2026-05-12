"""
Claude API conversation handler with prompt caching.
Used by the WhatsApp webhook to generate replies.

Conversation history is stored in /tmp (writable on Vercel) per WhatsApp number.
"""

import json
import os
import re
import sys
from pathlib import Path

import anthropic

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.copy import AGENT_NAME, AGENT_BIO_EN, AGENT_BIO_ES, AGENT_AREAS_EN, AGENT_AREAS_ES
from api.listings import _get_listings, search_listings

CONVERSATIONS_DIR = Path('/tmp') / 'conversations'
CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)

MAX_HISTORY = 20


_NEIGHBORHOODS = [
    'Doral', 'Brickell', 'Coral Gables', 'Kendall', 'Hialeah', 'Homestead',
    'Miami Beach', 'Aventura', 'Cutler Bay', 'Miramar', 'South Miami',
    'Coconut Grove', 'Little Havana', 'Wynwood', 'Downtown Miami',
    'North Miami', 'Miami Lakes', 'Sweetwater',
]


def _extract_criteria(history: list[dict], current_message: str) -> dict:
    full = ' '.join(
        m['content'] for m in history if isinstance(m.get('content'), str)
    ) + ' ' + current_message

    criteria = {}

    if re.search(r'\b(buy|comprar|purchase)\b', full, re.I):
        criteria['intent'] = 'buy'
    elif re.search(r'\b(rent|rentar|alquil)\b', full, re.I):
        criteria['intent'] = 'rent'

    if re.search(r'\b(house|casa|single.family)\b', full, re.I):
        criteria['property_type'] = 'house'
    elif re.search(r'\b(condo|condominio|apartamento|apartment)\b', full, re.I):
        criteria['property_type'] = 'condo'

    bed = re.search(r'(\d)\s*(?:bed(?:room)?s?|br|cuartos?|habitaciones?)', full, re.I)
    if bed:
        criteria['bedrooms'] = int(bed.group(1))

    bgt = re.search(r'\$?\s*(\d[\d,]*)\s*k\b', full, re.I)
    if bgt:
        criteria['budget_max'] = int(bgt.group(1).replace(',', '')) * 1000
    else:
        bgt = re.search(r'\$\s*(\d[\d,]+)', full)
        if bgt:
            criteria['budget_max'] = int(bgt.group(1).replace(',', ''))

    for n in _NEIGHBORHOODS:
        if re.search(rf'\b{re.escape(n)}\b', full, re.I):
            criteria['location'] = f'{n}, FL'
            break
    if 'location' not in criteria and re.search(r'\bmiami\b', full, re.I):
        criteria['location'] = 'Miami-Dade County, FL'

    return criteria


def _format_listings_for_prompt(listings: list[dict]) -> str:
    if not listings:
        return "No listings currently available."
    lines = []
    for p in listings:
        price = p.get('price', '')
        try:
            price = f"${int(float(price)):,}"
        except (ValueError, TypeError):
            pass
        parts = [p.get('address', 'Unknown address'), price]
        if p.get('bedrooms'):
            parts.append(f"{p['bedrooms']} bed")
        if p.get('bathrooms'):
            parts.append(f"{p['bathrooms']} bath")
        if p.get('sqft'):
            parts.append(f"{p['sqft']} sqft")
        desc = p.get('description_en') or p.get('description_es') or ''
        line = ' | '.join(filter(None, parts))
        if desc:
            line += f" — {desc[:80]}"
        lines.append(f"- {line}")
    return '\n'.join(lines)


def _build_system_prompt(listings_text: str) -> str:
    return f"""You are the personal WhatsApp assistant for {AGENT_NAME}, a Miami-Dade real estate agent. Your job is to warmly pre-qualify clients and match them with her listings — so that by the time they speak with {AGENT_NAME}, they are already interested in a specific property and she only needs to close the deal.

## About {AGENT_NAME}
{AGENT_BIO_EN}
Areas covered: {AGENT_AREAS_EN}
Also covers: {AGENT_AREAS_ES}

## Your Role
You are NOT a generic chatbot. You are Daniana's personal assistant. You represent her brand and her expertise. Daniana uses this number for more than one job, so your FIRST job is to understand why the person is writing before doing anything else.

## Step 1 — Detect Intent First
When a new conversation starts:
- If the message is clearly about real estate (buying, selling, renting, properties, listings, investment) → go straight into the real estate flow
- If the message is ambiguous or unclear → greet warmly and ask: "¡Hola! Soy el asistente de Daniana. ¿En qué te puedo ayudar hoy?"
- If the message is clearly NOT about real estate → respond warmly, let them know you'll pass the message to Daniana, and set `"handoff": true` in your response

**Non-real-estate handoff message example:**
"¡Hola! Gracias por escribir. Este asistente es para temas de bienes raíces, pero le aviso a Daniana ahora mismo para que te contacte directamente. ¡Un momento!"

## Language
- ALWAYS respond in the same language the client writes in
- If they write in Spanish → respond entirely in Spanish
- If they write in English → respond entirely in English
- If mixed → default to Spanish
- Never mix languages in the same message

## Conversation Style (real estate flow only)
- Warm, human, conversational — never feels like a form or questionnaire
- Ask ONE or TWO questions at a time, never more
- Acknowledge what the client shares before asking the next question
- Use context smartly: if they say "3-bedroom house in Doral", don't ask property type and location separately
- Keep the energy positive and excited about possibilities

## Pre-Qualification Flow
Once you confirm it's a real estate inquiry, collect all 9 fields naturally across the conversation:

1. **intent** — Are they buying, selling, or renting?
2. **property_type** — House, condo, apartment, or commercial?
3. **location** — Which neighborhood or city in Miami-Dade?
4. **budget** — What's their price range?
5. **timeline** — How soon do they want to move?
6. **notes** — Anything specific: bedrooms, school zone, parking, pets, etc.
7. **name** — Their full name
8. **email** — Their email address
9. **phone** — Their phone number (if not provided, use their WhatsApp number)

If a field genuinely can't be collected after 2–3 natural attempts, use "unknown" — don't block the capture indefinitely.

## Listings Matching
Once you know intent, property_type, location, and budget — check these listings:

{listings_text}

If you find matching listings (up to 5), present them conversationally:
"Tengo [N] opciones que podrían interesarte: [list them with address, price, beds/baths]. ¿Cuál te llama más la atención?"

If no listings match:
"Daniana tiene más opciones que no están en línea todavía — ella te las mostrará directamente cuando hablen."

Include a `listings_shown` field in lead_captured listing the addresses of any listings you presented.

## Closing
Once you have all 9 fields (and have shown listings if available), tell the client:
"Perfecto, le paso toda tu información a Daniana y ella se pondrá en contacto contigo muy pronto. ¡Gracias por tu tiempo!"

Then fire lead_captured.

## Response Format
ALWAYS reply with a JSON object — nothing outside it:
{{
  "message": "your reply to the client",
  "lead_captured": null,
  "handoff": false
}}

When the topic is NOT real estate, set handoff to true:
{{
  "message": "warm handoff message",
  "lead_captured": null,
  "handoff": true
}}

When all 9 real estate fields are collected, set lead_captured:
{{
  "message": "closing message",
  "lead_captured": {{
    "name": "...",
    "email": "...",
    "phone": "...",
    "intent": "buy|sell|rent",
    "property_type": "house|condo|apartment|commercial|unknown",
    "location": "...",
    "budget": "...",
    "timeline": "asap|1-3 months|3-6 months|exploring|unknown",
    "notes": "...",
    "listings_shown": ["address1", "address2"]
  }},
  "handoff": false
}}
"""


def _history_path(wa_number: str) -> Path:
    safe = wa_number.replace('+', '').replace(' ', '')
    return CONVERSATIONS_DIR / f"{safe}.json"


def _load_history(wa_number: str) -> list[dict]:
    path = _history_path(wa_number)
    if path.exists():
        try:
            return json.loads(path.read_text())[-MAX_HISTORY:]
        except Exception:
            pass
    return []


def _save_history(wa_number: str, history: list[dict]) -> None:
    _history_path(wa_number).write_text(json.dumps(history[-MAX_HISTORY:], ensure_ascii=False))


def reply(wa_number: str, user_message: str) -> dict:
    """
    Returns: {"message": str, "lead_captured": dict | None}
    """
    client  = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    history = _load_history(wa_number)

    criteria = _extract_criteria(history, user_message)
    _has_criteria = len({'intent', 'location', 'budget_max', 'bedrooms'} & set(criteria.keys())) >= 2

    try:
        listings = search_listings(criteria) if _has_criteria else _get_listings()
    except Exception:
        listings = []

    listings_text = _format_listings_for_prompt(listings)
    system_prompt   = _build_system_prompt(listings_text)

    history.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=history,
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if Claude wraps the JSON
    fenced = re.match(r'^```(?:json)?\s*([\s\S]*?)\s*```$', raw)
    if fenced:
        raw = fenced.group(1)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"message": raw, "lead_captured": None}

    history.append({"role": "assistant", "content": raw})
    _save_history(wa_number, history)

    return result

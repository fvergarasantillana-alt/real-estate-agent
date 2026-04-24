"""
Claude API conversation handler with prompt caching.
Used by the WhatsApp webhook to generate replies.

Conversation history is stored as JSON files under .tmp/conversations/.
"""

import json
import os
import sys
from pathlib import Path

import anthropic

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.copy import AGENT_NAME, AGENT_BIO_EN, AGENT_BIO_ES, AGENT_AREAS_EN

CONVERSATIONS_DIR = Path(__file__).parent.parent / '.tmp' / 'conversations'
CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)

MAX_HISTORY = 20  # messages kept per conversation

SYSTEM_PROMPT = f"""You are a friendly, professional real estate assistant for {AGENT_NAME}, a Miami-Dade real estate agent.

## About {AGENT_NAME}
{AGENT_BIO_EN}
Areas covered: {AGENT_AREAS_EN}

## Your Role
You help potential clients via WhatsApp. You answer questions about:
- Buying, selling, or renting property in Miami-Dade
- The Miami real estate market (prices, neighborhoods, trends)
- {AGENT_NAME}'s services and availability
- Scheduling property viewings (collect their info and pass it on)

## Language
Always respond in the same language the user writes in.
If Spanish → respond in Spanish. If English → respond in English.
Be warm, concise, and professional. Use natural conversational tone, not formal corporate language.

## Lead Capture
When a user expresses clear interest in buying, selling, or renting:
1. Confirm their intent (e.g. "¿Estás buscando comprar en Miami?")
2. Ask for: their name, email address, phone number, and what they're looking for
3. Once you have all four pieces of info, say you'll pass it along and that {AGENT_NAME} will contact them directly
4. In your reply JSON field "lead_captured", include their collected info

## Format
Reply ONLY with a JSON object:
{{
  "message": "your reply to the user",
  "lead_captured": null  // or {{ "name": ..., "email": ..., "phone": ..., "intent": ... }}
}}

Do not include anything outside the JSON object.
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

    history.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=history,
    )

    raw = response.content[0].text.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"message": raw, "lead_captured": None}

    history.append({"role": "assistant", "content": raw})
    _save_history(wa_number, history)

    return result

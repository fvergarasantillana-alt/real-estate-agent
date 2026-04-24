# Workflow: WhatsApp Lead Capture

## Objective
Respond to incoming WhatsApp messages, answer real estate questions in the user's language, and capture lead information (name, email, phone, intent) when a potential buyer/seller/renter shows interest.

## Trigger
Any incoming WhatsApp message to the bot number.

## Tools
- `api/whatsapp.py` — receives the message from Meta Cloud API
- `api/claude_chat.py` — generates the reply using Claude
- `api/notify.py` — sends lead notification to the agent

## Flow

```
1. User sends a message
2. whatsapp.py receives it → calls claude_chat.reply(wa_number, user_text)
3. claude_chat.py:
   - Loads conversation history for this number (.tmp/conversations/{number}.json)
   - Appends user message
   - Calls Claude API with the system prompt (cached) + full history
   - Parses the JSON response: { "message": str, "lead_captured": dict|null }
   - Appends assistant reply to history and saves
4. whatsapp.py sends the reply back to the user via Meta API
5. If lead_captured is not null → notify.notify_lead(lead) → email + WhatsApp to agent
```

## Lead Capture Trigger
Claude captures a lead when it has collected all four fields:
- `name` — user's full name
- `email` — valid email address
- `phone` — phone number (falls back to their WhatsApp number if not provided)
- `intent` — what they're looking for (buy/sell/rent + details)

## Conversation History
Stored as JSON at `.tmp/conversations/{number}.json`.
Last 20 messages kept. Cleared automatically when the file is regenerated.

## Edge Cases

| Situation | Handling |
|---|---|
| User sends image/audio/video | Ignored; only text messages are processed |
| Meta sends a delivery receipt | No `messages` key in payload → acknowledged and ignored |
| Claude returns malformed JSON | Raw text used as the reply; lead_captured = null |
| Notification fails (email/WA) | Logged to console; does not affect the reply to the user |
| User writes mix of EN/ES | Claude defaults to Spanish if ambiguous |

## Rate Limits / Costs
- Meta Cloud API: free for first 1,000 conversations/month. One conversation = 24-hour window per user.
- Claude API: ~$0.003–0.01 per typical conversation. Prompt caching reduces this ~80%.
- Conversations reset every 24 hours per Meta's definition.

## Testing
1. Join the Meta WhatsApp sandbox (test number from Meta Developer Console)
2. Text the sandbox number
3. Check `.tmp/conversations/` for saved history
4. Check agent email + WhatsApp for notification on lead capture

## Update Log
- 2026-04-23: Initial workflow created

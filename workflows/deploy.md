# Workflow: Deploy to Vercel

## One-Time Setup

### 1. GitHub repository
```bash
git init
git add .
git commit -m "Initial commit"
# Create a repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/real-estate-agent.git
git push -u origin main
```

### 2. Vercel account + project
1. Go to vercel.com → Sign up free with GitHub
2. Click "Add New Project" → import the GitHub repo
3. Framework preset: **Other**
4. Root directory: leave as `/`
5. Click Deploy (first deploy will fail — that's okay, we need env vars next)

### 3. Environment variables
In Vercel → Project → Settings → Environment Variables, add each key from `.env`:

| Key | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys |
| `META_WHATSAPP_TOKEN` | Meta Developer Console → App → WhatsApp → API Setup |
| `META_PHONE_NUMBER_ID` | Same page as above |
| `META_VERIFY_TOKEN` | Choose any secret string (e.g. `my-verify-token-2024`) |
| `META_APP_SECRET` | Meta Developer Console → App → Settings → Basic |
| `AGENT_WHATSAPP_NUMBER` | Her personal WhatsApp number with country code (e.g. `13055551234`) |
| `AGENT_EMAIL` | Her email address |
| `GMAIL_USER` | Gmail address used to send notifications |
| `GMAIL_APP_PASSWORD` | Gmail → Account Settings → Security → App Passwords → generate one |
| `GOOGLE_SHEET_ID` | From the Google Sheet URL: `docs.google.com/spreadsheets/d/**THIS_PART**/edit` |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | See step 4 below |

### 4. Google Sheets service account
1. Go to console.cloud.google.com → Create a new project
2. Enable the **Google Sheets API**
3. Create a Service Account → download the JSON key file
4. Open the JSON file → copy its entire contents
5. Paste as the value of `GOOGLE_SERVICE_ACCOUNT_JSON` in Vercel (it's a long JSON string)
6. In Google Sheets → Share the sheet with the service account email (found in the JSON as `"client_email"`) with **Viewer** access

### 5. Meta WhatsApp webhook
1. In Meta Developer Console → App → WhatsApp → Configuration
2. Set webhook URL: `https://your-vercel-app.vercel.app/api/whatsapp`
3. Set verify token: the same string you set in `META_VERIFY_TOKEN`
4. Subscribe to: `messages`
5. Click Verify and Save

### 6. Redeploy
In Vercel → Deployments → click the latest → Redeploy. The site is now live.

## Ongoing Deployments
Every `git push` to `main` triggers an automatic redeploy on Vercel. No manual action needed.

## Custom Domain (Optional, ~$10-15/year)
1. Buy a domain at namecheap.com or porkbun.com
2. Vercel → Project → Settings → Domains → Add domain
3. Follow the DNS instructions Vercel provides

## Update Log
- 2026-04-23: Initial workflow created

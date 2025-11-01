# WhatsApp Webhook Relay (Serverless)

A tiny Node.js relay to receive WhatsApp Cloud API webhooks and let the desktop app pull inbound messages.

## Endpoints
- GET `/` health check
- GET `/webhook` verification (Meta will call with hub.challenge)
- POST `/webhook` inbound events (Meta will POST here)
- GET `/pull?secret=...` desktop pulls queued messages

## Environment variables
- `VERIFY_TOKEN` (required): a secret you set in Meta webhook verification
- `PULL_SECRET` (optional): secret required by `/pull` (defaults to VERIFY_TOKEN)
- `PORT` (optional): default 3000

## Quick local run
```bash
npm install
VERIFY_TOKEN=changeme PULL_SECRET=changeme node server.js
```
Then expose it via a tunnel (optional):
```bash
npx ngrok http 3000
```
Use the HTTPS URL for your Meta webhook.

## Deploy to Vercel (recommended free tier)
1. Install Vercel CLI: `npm i -g vercel`
2. In this folder run: `vercel` and follow prompts (or `vercel --prod`)
3. Set env vars:
   ```bash
   vercel env add VERIFY_TOKEN
   vercel env add PULL_SECRET
   ```
4. Re-deploy: `vercel --prod`
5. Note the deployed URL, e.g., `https://your-relay.vercel.app`

Vercel notes: Webhook must be a serverless function. This simple server works on Vercel as a Node serverless with `vercel.json` or Node Serverless Function. If you prefer, deploy to Render/Railway/Glitch.

## Deploy to Render (alternative)
1. Create new Web Service from this folder repo
2. Build command: `npm install`
3. Start command: `node server.js`
4. Set `VERIFY_TOKEN` and `PULL_SECRET` in environment settings

## Connect Meta (WhatsApp Cloud API)
1. Go to Meta Developers > WhatsApp > Configuration
2. Set Webhook URL to: `https://YOUR-RELAY/webhook`
3. Set Verify Token to exactly your `VERIFY_TOKEN`
4. Subscribe to `messages` events

## Configure desktop app
In `config.json` of the desktop app:
```json
{
  "relay_url": "https://YOUR-RELAY",
  "relay_secret": "PULL_SECRET"
}
```
The desktop app will poll `/pull` every ~3 seconds and show inbound messages in Logs tab.

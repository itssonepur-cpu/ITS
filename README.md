# WhatsApp Marketing Pack – Desktop (.exe)

A lightweight Windows desktop tool to manage WhatsApp templates, contacts, and campaigns. Works offline in export-only mode (generates click-to-chat links and QR codes). Optionally sends via WhatsApp Cloud API when credentials are provided.

## Features (MVP)
- Contacts: Import CSV (name, phone, tags). Basic validator.
- Templates: Text with placeholders like {{name}}; optional media URL.
- Campaigns: Select contacts by tag, bind template, preview, export links.
- Sending: 
  - Export-only mode: wa.me links and optional QR image files.
  - API mode: WhatsApp Cloud API (requires token + phone_number_id).
- Logs: Result table + CSV export.

## Requirements
- Windows 10/11
- No Python install required for the packaged .exe
- For development/build: Python 3.10+ and pip

## Quick Start (run from source)
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `config.example.json` to `config.json` and edit values (optional for API mode).
3. Run the app:
   ```bash
   python -m src.app
   ```

## Build a single EXE
- PowerShell:
  ```powershell
  ./build.ps1
  ```
- Output will be at `dist/WhatsAppPack.exe`

## CSV format
contacts.csv (UTF-8):
```
name,phone,tags
Rohit,919876543210,student;gaming
Anita,911234567890,office
```
- `phone` must be in international format without plus.

## Templates
Example:
```
Title: Diwali Offer
Body: Hi {{name}}, festive deals are live! Get up to 10% off on laptops. Reply DEAL to know more.
Media URL (optional): https://example.com/banner.jpg
```

## API mode (optional)
- Create `config.json`:
```
{
  "mode": "api", 
  "cloud_api_token": "EAAG...",
  "phone_number_id": "1234567890",
  "business_id": "",
  "default_country_code": "91",
  "relay_url": "https://your-relay-url",
  "relay_secret": "your-pull-secret"
}
```
- Only use approved templates per WhatsApp policy. This tool sends text/media messages using your inputs.

## Notes
- Respect local regulations and WhatsApp policies.
- Include unsubscribe instructions in campaigns and honor suppression lists.

## License
MIT

---

# Inbound Replies via Relay (Serverless)

To receive incoming WhatsApp messages into the desktop app, deploy the tiny relay in `relay/` and add its URL to `config.json`.

## Deploy Relay
- Go to `relay/` folder and read `relay/README.md` for options (Vercel/Render/local+ngrok).
- Key env vars:
  - `VERIFY_TOKEN` used in Meta webhook verification.
  - `PULL_SECRET` used by the desktop app `/pull` endpoint.

## Connect Meta (Cloud API)
1. Set webhook URL to `https://YOUR-RELAY/webhook` and verify with `VERIFY_TOKEN`.
2. Subscribe to `messages` field.
3. In `config.json` set:
   - `relay_url`: `https://YOUR-RELAY`
   - `relay_secret`: your `PULL_SECRET`

The desktop app will poll the relay every ~3 seconds and list inbound messages under the Logs tab.

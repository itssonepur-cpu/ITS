// Simple WhatsApp Cloud API webhook relay
// Stores inbound messages in memory and lets the desktop app pull them periodically.
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(bodyParser.json());

const PORT = process.env.PORT || 3000;
const VERIFY_TOKEN = process.env.VERIFY_TOKEN || 'changeme';
const PULL_SECRET = process.env.PULL_SECRET || VERIFY_TOKEN;

let queue = [];

app.get('/', (req, res) => {
  res.json({ status: 'ok' });
});

// Webhook verification
app.get('/webhook', (req, res) => {
  const mode = req.query['hub.mode'];
  const token = req.query['hub.verify_token'];
  const challenge = req.query['hub.challenge'];
  if (mode === 'subscribe' && token === VERIFY_TOKEN) {
    return res.status(200).send(challenge);
  }
  return res.sendStatus(403);
});

// Webhook receiver (WhatsApp will POST here)
app.post('/webhook', (req, res) => {
  try {
    const body = req.body;
    // Extract messages from Cloud API payload shape
    if (body && body.entry) {
      body.entry.forEach(entry => {
        (entry.changes || []).forEach(change => {
          const value = change.value || {};
          const messages = value.messages || [];
          messages.forEach(msg => {
            if (!msg.from) return;
            const item = {
              id: msg.id,
              phone: msg.from,
              timestamp: msg.timestamp,
              type: msg.type,
              text: msg.text ? msg.text.body : undefined,
              interactive: msg.interactive || undefined,
              raw: msg
            };
            queue.push(item);
          });
        });
      });
    }
  } catch (e) {
    console.error('Webhook parse error', e);
  }
  res.sendStatus(200);
});

// Desktop app pulls messages
app.get('/pull', (req, res) => {
  const secret = req.query.secret;
  if (secret !== PULL_SECRET) {
    return res.sendStatus(403);
  }
  const out = queue;
  queue = [];
  res.json(out);
});

app.listen(PORT, () => {
  console.log(`Relay running on port ${PORT}`);
});

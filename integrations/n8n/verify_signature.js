// Code node (mode: Run Once for All Items) for the Anna events workflow.
// Source of truth for the jsCode embedded in anna_events_workflow.example.json.
// Mirrors receiver_example.py: same headers, same signed bytes, same 300 s tolerance.
//
// Needs: NODE_FUNCTION_ALLOW_BUILTIN=crypto (built-in module access in Code node)
//        and access to $env.ANNA_EVENTS_SIGNING_SECRET (see integrations/n8n/README.md).

const crypto = require('crypto');
const TOLERANCE_S = 300;

const item = $input.first();
const headers = item.json.headers || {};
const eventIdHeader = headers['x-anna-event-id'];
const timestamp = headers['x-anna-timestamp'];
const signature = headers['x-anna-signature'];
const secret = $env.ANNA_EVENTS_SIGNING_SECRET;

// RAW bytes are required: the signature covers the body exactly as it arrived.
// Webhook node option "Raw Body" must be enabled. Where the raw body lands depends on
// the n8n version: binary property "data" (base64) or json.rawBody (string). Check yours.
let raw = null;
if (item.binary && item.binary.data && item.binary.data.data) {
  raw = Buffer.from(item.binary.data.data, 'base64');
} else if (typeof item.json.rawBody === 'string') {
  raw = Buffer.from(item.json.rawBody, 'utf8');
}

function verdict() {
  if (!secret) return 'missing_secret';
  if (!timestamp || !signature || raw === null) return 'missing_headers';
  if (!/^[0-9]{1,12}$/.test(timestamp)) return 'bad_timestamp';
  const nowS = Math.floor(Date.now() / 1000);
  if (Math.abs(nowS - Number(timestamp)) > TOLERANCE_S) return 'stale_timestamp';

  const mac = crypto
    .createHmac('sha256', secret)
    .update(Buffer.concat([Buffer.from(timestamp + '.', 'ascii'), raw]))
    .digest('hex');
  const expected = Buffer.from('sha256=' + mac, 'utf8');
  const given = Buffer.from(String(signature), 'utf8');
  if (expected.length !== given.length || !crypto.timingSafeEqual(expected, given)) return 'bad_signature';
  return 'ok';
}

const reason = verdict();
let event = null;
let finalReason = reason;

if (reason === 'ok') {
  try {
    event = JSON.parse(raw.toString('utf8'));
  } catch (err) {
    event = null;
    finalReason = 'invalid_json';
  }
  if (event && event.event_id !== eventIdHeader) {
    event = null;
    finalReason = 'event_id_mismatch';
  }
}

const authorized = finalReason === 'ok';
return [
  {
    json: {
      authorized: authorized,
      reason: finalReason,
      eventId: eventIdHeader || null,
      eventType: authorized ? event.event_type : null,
      event: authorized ? event : null,
    },
  },
];

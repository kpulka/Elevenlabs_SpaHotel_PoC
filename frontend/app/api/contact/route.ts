import { NextRequest, NextResponse } from 'next/server'

import { validateContactPayload } from '@/lib/contact/validation'
import { logger } from '@/lib/logger'
import { createRateLimiter } from '@/lib/rate-limit'
import { checkRequestOrigin, clientIp } from '@/lib/request-guard'

/** Upper bound for the raw body; the longest valid form is well below this. */
const MAX_BODY_BYTES = 8 * 1024
const RATE_LIMIT = 5
const RATE_WINDOW_MS = 10 * 60_000
const limiter = createRateLimiter({ limit: RATE_LIMIT, windowMs: RATE_WINDOW_MS })

const encoder = new TextEncoder()

/**
 * Contact form endpoint. Validates the message and answers `ok`, but does NOT deliver it anywhere:
 * this is a demonstration build. The response says so (`delivered: false`), and nothing is stored.
 *
 * Logs contain event names, the field that failed validation and counts. They never contain the
 * name, e-mail, phone or message text.
 */
export async function POST(req: NextRequest) {
  const origin = checkRequestOrigin(req)
  if (!origin.allowed) {
    logger.warn('contact.origin_rejected', { reason: origin.reason })
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  const ip = clientIp(req)
  const decision = limiter.check(ip)
  if (!decision.allowed) {
    logger.warn('contact.rate_limited', { retryAfterSec: decision.retryAfterSec })
    return NextResponse.json(
      { error: 'Too many requests' },
      { status: 429, headers: { 'Retry-After': String(decision.retryAfterSec) } },
    )
  }

  const declaredLength = Number(req.headers.get('content-length') ?? '0')
  if (Number.isFinite(declaredLength) && declaredLength > MAX_BODY_BYTES) {
    logger.warn('contact.body_too_large', { declaredLength })
    return NextResponse.json({ error: 'Payload too large' }, { status: 413 })
  }

  let raw: string
  try {
    raw = await req.text()
  } catch {
    logger.warn('contact.body_unreadable')
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 })
  }
  const bodyBytes = encoder.encode(raw).length
  if (bodyBytes > MAX_BODY_BYTES) {
    logger.warn('contact.body_too_large', { bodyBytes })
    return NextResponse.json({ error: 'Payload too large' }, { status: 413 })
  }

  let body: unknown
  try {
    body = JSON.parse(raw)
  } catch {
    logger.warn('contact.invalid_json')
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 })
  }

  const result = validateContactPayload(body)
  if (result.kind === 'honeypot') {
    // Answer like a success so that the bot learns nothing. No content is logged.
    logger.info('contact.honeypot')
    return NextResponse.json({ ok: true, delivered: false })
  }
  if (result.kind === 'invalid') {
    logger.info('contact.invalid', { field: result.field })
    return NextResponse.json({ error: 'Invalid form data', field: result.field }, { status: 400 })
  }

  // topic is free text on the wire (the form sends a select value), so only its length is logged.
  logger.info('contact.accepted', {
    topicLength: result.value.topic.length,
    hasPhone: result.value.phone !== '',
    messageLength: result.value.message.length,
  })
  return NextResponse.json({ ok: true, delivered: false })
}

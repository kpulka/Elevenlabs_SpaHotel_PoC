import { NextRequest, NextResponse } from 'next/server'

import { getServerAgentId, getServerApiKey } from '@/lib/env'
import { logger, errorFields } from '@/lib/logger'
import { createRateLimiter } from '@/lib/rate-limit'
import { checkRequestOrigin, clientIp } from '@/lib/request-guard'

const RATE_LIMIT = 10
const RATE_WINDOW_MS = 60_000
const limiter = createRateLimiter({ limit: RATE_LIMIT, windowMs: RATE_WINDOW_MS })

// Returns a signed URL for the Anna agent without exposing the API key to the browser.
// The signed URL carries signed access to the conversation (agent_id + conversation_signature).
export async function GET(req: NextRequest) {
  const origin = checkRequestOrigin(req)
  if (!origin.allowed) {
    logger.warn('signed_url.origin_rejected', { reason: origin.reason })
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }
  if (origin.reason === 'no-origin') {
    logger.info('signed_url.no_origin', { note: 'no Origin/Referer header, non-browser client' })
  }

  const ip = clientIp(req)
  const decision = limiter.check(ip)
  if (!decision.allowed) {
    logger.warn('signed_url.rate_limited', { retryAfterSec: decision.retryAfterSec })
    return NextResponse.json(
      { error: 'Too many requests' },
      { status: 429, headers: { 'Retry-After': String(decision.retryAfterSec) } },
    )
  }

  let agentId: string
  let apiKey: string
  try {
    agentId = getServerAgentId()
    apiKey = getServerApiKey()
  } catch (err) {
    // Only the variable name reaches the log; EnvConfigError never contains values.
    logger.error('signed_url.misconfigured', errorFields(err))
    return NextResponse.json({ error: 'Voice assistant is not configured' }, { status: 500 })
  }

  const { searchParams } = req.nextUrl
  // Only known languages are echoed back; anything else falls back to Polish.
  const lang = searchParams.get('lang') === 'en' ? 'en' : 'pl'

  const url = `https://api.elevenlabs.io/v1/convai/conversation/get-signed-url?agent_id=${encodeURIComponent(agentId)}`
  try {
    const res = await fetch(url, {
      headers: { 'xi-api-key': apiKey },
      cache: 'no-store',
    })
    if (!res.ok) {
      // Upstream body is not logged: it may echo request details. Status is enough for operators.
      logger.error('signed_url.upstream_failed', { upstreamStatus: res.status })
      return NextResponse.json({ error: 'Voice assistant is temporarily unavailable' }, { status: 502 })
    }
    const data = (await res.json()) as { signed_url?: string }
    if (!data.signed_url) {
      logger.error('signed_url.missing_field')
      return NextResponse.json({ error: 'No signed_url in response' }, { status: 502 })
    }
    return NextResponse.json({
      signed_url: data.signed_url,
      language: lang,
    })
  } catch (err) {
    logger.error('signed_url.request_failed', errorFields(err))
    return NextResponse.json({ error: 'Voice assistant is temporarily unavailable' }, { status: 502 })
  }
}

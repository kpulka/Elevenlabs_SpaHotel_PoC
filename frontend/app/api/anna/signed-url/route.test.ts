// @vitest-environment node
import { NextRequest } from 'next/server'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { GET } from './route'

const TEST_AGENT_ID = 'agent_testagent0001'
const SITE_ORIGIN = 'http://localhost'

let ipCounter = 0

/** Each call gets its own client IP by default, so the shared in-memory rate limit does not leak between tests. */
function request(query = '', options: { ip?: string; headers?: Record<string, string> } = {}) {
  ipCounter += 1
  return new NextRequest(`${SITE_ORIGIN}/api/anna/signed-url${query}`, {
    headers: {
      'x-forwarded-for': options.ip ?? `10.1.0.${ipCounter}`,
      ...options.headers,
    },
  })
}

function stubSignedUrlFetch() {
  const fetchMock = vi.fn(async () => Response.json({ signed_url: 'wss://example.test/signed' }))
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

beforeEach(() => {
  vi.stubEnv('ELEVENLABS_API_KEY', 'test-key')
  vi.stubEnv('ELEVENLABS_AGENT_ID', TEST_AGENT_ID)
  vi.stubEnv('NEXT_PUBLIC_ELEVENLABS_AGENT_ID', '')
  vi.stubEnv('ALLOWED_ORIGINS', '')
  vi.spyOn(console, 'error').mockImplementation(() => {})
  vi.spyOn(console, 'info').mockImplementation(() => {})
  vi.spyOn(console, 'warn').mockImplementation(() => {})
})

afterEach(() => {
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('GET /api/anna/signed-url', () => {
  it.each([
    ['', 'pl'],
    ['?lang=pl', 'pl'],
    ['?lang=en', 'en'],
    ['?lang=de', 'pl'],
    ['?lang=EN', 'pl'],
    ['?lang=%3Cscript%3Ealert(1)%3C%2Fscript%3E', 'pl'],
  ])('query "%s" returns language "%s"', async (query, expected) => {
    stubSignedUrlFetch()

    const res = await GET(request(query, { headers: { origin: SITE_ORIGIN } }))

    expect(res.status).toBe(200)
    expect(await res.json()).toEqual({ signed_url: 'wss://example.test/signed', language: expected })
  })

  it('sends the configured agent id to ElevenLabs', async () => {
    const fetchMock = stubSignedUrlFetch()

    await GET(request('', { headers: { origin: SITE_ORIGIN } }))

    const calls = fetchMock.mock.calls as unknown as unknown[][]
    expect(String(calls[0][0])).toContain(`agent_id=${TEST_AGENT_ID}`)
  })

  it('returns 500 without calling ElevenLabs when the API key is missing', async () => {
    vi.stubEnv('ELEVENLABS_API_KEY', '')
    const fetchMock = stubSignedUrlFetch()

    const res = await GET(request())

    expect(res.status).toBe(500)
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('returns 500 and names only the variable when the agent id is missing (no hardcoded fallback)', async () => {
    vi.stubEnv('ELEVENLABS_AGENT_ID', '')
    const fetchMock = stubSignedUrlFetch()

    const res = await GET(request('', { headers: { origin: SITE_ORIGIN } }))
    const body = JSON.stringify(await res.json())

    expect(res.status).toBe(500)
    expect(fetchMock).not.toHaveBeenCalled()
    expect(body).not.toContain('agent_8401')
    expect(console.error).toHaveBeenCalledWith(expect.stringContaining('ELEVENLABS_AGENT_ID is not set'))
  })

  it('rejects a malformed agent id without echoing it', async () => {
    vi.stubEnv('ELEVENLABS_AGENT_ID', 'agent_bad&evil=1')
    const fetchMock = stubSignedUrlFetch()

    const res = await GET(request('', { headers: { origin: SITE_ORIGIN } }))

    expect(res.status).toBe(500)
    expect(fetchMock).not.toHaveBeenCalled()
    expect(console.error).not.toHaveBeenCalledWith(expect.stringContaining('evil'))
  })

  it('returns a generic 502 and hides upstream details when ElevenLabs fails', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('secret upstream detail', { status: 401 })))

    const res = await GET(request('?lang=en', { headers: { origin: SITE_ORIGIN } }))

    expect(res.status).toBe(502)
    expect(JSON.stringify(await res.json())).not.toContain('secret upstream detail')
  })

  it('returns 429 with Retry-After after 10 requests from the same IP within a minute', async () => {
    stubSignedUrlFetch()
    const ip = '203.0.113.7'

    for (let i = 0; i < 10; i += 1) {
      const ok = await GET(request('', { ip, headers: { origin: SITE_ORIGIN } }))
      expect(ok.status).toBe(200)
    }
    const limited = await GET(request('', { ip, headers: { origin: SITE_ORIGIN } }))

    expect(limited.status).toBe(429)
    const retryAfter = Number(limited.headers.get('Retry-After'))
    expect(retryAfter).toBeGreaterThanOrEqual(1)
    expect(retryAfter).toBeLessThanOrEqual(60)
  })

  it('rate limits per client IP, so another IP is still served', async () => {
    stubSignedUrlFetch()
    for (let i = 0; i < 10; i += 1) {
      await GET(request('', { ip: '198.51.100.1', headers: { origin: SITE_ORIGIN } }))
    }

    const other = await GET(request('', { ip: '198.51.100.2', headers: { origin: SITE_ORIGIN } }))

    expect(other.status).toBe(200)
  })

  it('returns 403 for a foreign Origin and does not call ElevenLabs', async () => {
    const fetchMock = stubSignedUrlFetch()

    const res = await GET(request('', { headers: { origin: 'https://evil.example' } }))

    expect(res.status).toBe(403)
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('returns 403 for a foreign Referer when no Origin header is sent', async () => {
    const fetchMock = stubSignedUrlFetch()

    const res = await GET(request('', { headers: { referer: 'https://evil.example/page' } }))

    expect(res.status).toBe(403)
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('returns 403 for a malformed Origin header', async () => {
    const res = await GET(request('', { headers: { origin: 'not a url' } }))

    expect(res.status).toBe(403)
  })

  it('allows localhost and origins listed in ALLOWED_ORIGINS', async () => {
    vi.stubEnv('ALLOWED_ORIGINS', 'https://bukowydwor.example, https://staging.example.test/')
    stubSignedUrlFetch()

    const local = await GET(request('', { headers: { origin: 'http://localhost:3000' } }))
    const listed = await GET(request('', { headers: { origin: 'https://staging.example.test' } }))

    expect(local.status).toBe(200)
    expect(listed.status).toBe(200)
  })

  it('allows a request without Origin or Referer (non-browser client) and logs it', async () => {
    stubSignedUrlFetch()

    const res = await GET(request())

    expect(res.status).toBe(200)
    expect(console.info).toHaveBeenCalledWith(expect.stringContaining('signed_url.no_origin'))
  })
})

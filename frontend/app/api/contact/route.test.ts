// @vitest-environment node
import { NextRequest } from 'next/server'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { POST } from './route'

const SITE_ORIGIN = 'http://localhost'
const SECRET_NAME = 'Zofia Testowa'
const SECRET_EMAIL = 'zofia.testowa@example.test'
const SECRET_MESSAGE = 'Proszę o pokój z łóżkiem dla osoby z dietą bezglutenową'

let ipCounter = 0

function validBody(overrides: Record<string, unknown> = {}) {
  return {
    name: SECRET_NAME,
    email: SECRET_EMAIL,
    phone: '+48 600 123 456',
    topic: 'Rezerwacja pokoju',
    message: SECRET_MESSAGE,
    website: '',
    ...overrides,
  }
}

/** Each request gets its own client IP by default, so the shared in-memory rate limit does not leak between tests. */
function post(body: unknown, options: { ip?: string; origin?: string | null; raw?: string } = {}) {
  ipCounter += 1
  const headers: Record<string, string> = {
    'content-type': 'application/json',
    'x-forwarded-for': options.ip ?? `10.2.0.${ipCounter}`,
  }
  if (options.origin !== null) headers.origin = options.origin ?? SITE_ORIGIN
  return new NextRequest(`${SITE_ORIGIN}/api/contact`, {
    method: 'POST',
    headers,
    body: options.raw ?? JSON.stringify(body),
  })
}

function loggedText(spy: { mock: { calls: unknown[][] } }): string {
  return spy.mock.calls.map((call) => call.map(String).join(' ')).join('\n')
}

beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation(() => {})
  vi.spyOn(console, 'info').mockImplementation(() => {})
  vi.spyOn(console, 'warn').mockImplementation(() => {})
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('POST /api/contact', () => {
  it('accepts a valid message and says it was not delivered (demo build)', async () => {
    const res = await POST(post(validBody()))

    expect(res.status).toBe(200)
    expect(await res.json()).toEqual({ ok: true, delivered: false })
  })

  it('accepts a message without a phone number', async () => {
    const res = await POST(post(validBody({ phone: '' })))

    expect(res.status).toBe(200)
  })

  it.each([
    ['email', { email: 'not-an-email' }],
    ['email', { email: 'a b@example.test' }],
    ['email', { email: 'x'.repeat(250) + '@example.test' }],
    ['name', { name: '   ' }],
    ['name', { name: 'n'.repeat(101) }],
    ['message', { message: '' }],
    ['message', { message: 'm'.repeat(2001) }],
    ['phone', { phone: 'call me' }],
    ['topic', { topic: 't'.repeat(81) }],
  ])('rejects an invalid %s with 400 and names only the field', async (field, override) => {
    const res = await POST(post(validBody(override)))

    expect(res.status).toBe(400)
    expect(await res.json()).toEqual({ error: 'Invalid form data', field })
  })

  it('rejects a body that is not JSON', async () => {
    const res = await POST(post(null, { raw: '{not json' }))

    expect(res.status).toBe(400)
  })

  it('rejects a JSON value that is not an object', async () => {
    const res = await POST(post(null, { raw: '["a"]' }))

    expect(res.status).toBe(400)
    expect(await res.json()).toEqual({ error: 'Invalid form data', field: 'body' })
  })

  it('rejects a body larger than 8 KB', async () => {
    const res = await POST(post(validBody({ message: 'a'.repeat(9000) })))

    expect(res.status).toBe(413)
  })

  it('returns 403 for a foreign Origin', async () => {
    const res = await POST(post(validBody(), { origin: 'https://evil.example' }))

    expect(res.status).toBe(403)
  })

  it('answers like a success for the honeypot without processing the message', async () => {
    const res = await POST(post(validBody({ website: 'http://spam.example' })))

    expect(res.status).toBe(200)
    expect(await res.json()).toEqual({ ok: true, delivered: false })
    expect(console.info).toHaveBeenCalledWith(expect.stringContaining('contact.honeypot'))
  })

  it('limits each client IP to 5 submissions per window', async () => {
    const ip = '203.0.113.50'
    for (let i = 0; i < 5; i += 1) {
      const ok = await POST(post(validBody(), { ip }))
      expect(ok.status).toBe(200)
    }

    const limited = await POST(post(validBody(), { ip }))

    expect(limited.status).toBe(429)
    expect(Number(limited.headers.get('Retry-After'))).toBeGreaterThanOrEqual(1)
  })

  it('never writes the name, e-mail, phone or message to the logs', async () => {
    await POST(post(validBody()))
    await POST(post(validBody({ message: '' })))
    await POST(post(validBody({ website: 'http://spam.example' })))

    const logs = [loggedText(vi.mocked(console.info)), loggedText(vi.mocked(console.warn)), loggedText(vi.mocked(console.error))].join('\n')
    expect(logs).toContain('contact.accepted')
    expect(logs).not.toContain(SECRET_NAME)
    expect(logs).not.toContain(SECRET_EMAIL)
    expect(logs).not.toContain('600 123 456')
    expect(logs).not.toContain(SECRET_MESSAGE)
  })
})

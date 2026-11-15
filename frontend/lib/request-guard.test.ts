// @vitest-environment node
import { describe, expect, it } from 'vitest'

import { checkRequestOrigin, clientIp, parseAllowedOrigins, parseTrustProxy } from '@/lib/request-guard'

const URL_SELF = 'https://site.example/api/anna/signed-url'

function req(headers: Record<string, string> = {}) {
  return new Request(URL_SELF, { headers })
}

describe('parseAllowedOrigins', () => {
  it('normalises entries and ignores malformed ones', () => {
    expect(parseAllowedOrigins(' https://a.example/ , not-a-url, https://b.example:8443 ')).toEqual([
      'https://a.example',
      'https://b.example:8443',
    ])
  })

  it('returns an empty list for undefined or empty input', () => {
    expect(parseAllowedOrigins(undefined)).toEqual([])
    expect(parseAllowedOrigins('')).toEqual([])
  })
})

describe('checkRequestOrigin', () => {
  it('allows the same origin as the request URL', () => {
    expect(checkRequestOrigin(req({ origin: 'https://site.example' }), '')).toEqual({
      allowed: true,
      reason: 'same-origin',
    })
  })

  it('allows localhost and 127.0.0.1 on any port', () => {
    expect(checkRequestOrigin(req({ origin: 'http://localhost:3000' }), '').allowed).toBe(true)
    expect(checkRequestOrigin(req({ origin: 'http://127.0.0.1:5173' }), '').allowed).toBe(true)
  })

  it('allows origins from ALLOWED_ORIGINS and rejects everything else', () => {
    const env = 'https://partner.example'
    expect(checkRequestOrigin(req({ origin: 'https://partner.example' }), env)).toEqual({
      allowed: true,
      reason: 'allow-list',
    })
    expect(checkRequestOrigin(req({ origin: 'https://partner.example.evil.test' }), env)).toEqual({
      allowed: false,
      reason: 'origin-not-allowed',
    })
  })

  it('prefers Origin over Referer', () => {
    const decision = checkRequestOrigin(
      req({ origin: 'https://evil.example', referer: 'https://site.example/page' }),
      '',
    )
    expect(decision.allowed).toBe(false)
  })

  it('uses Referer when Origin is absent', () => {
    expect(checkRequestOrigin(req({ referer: 'https://site.example/kontakt' }), '').allowed).toBe(true)
    expect(checkRequestOrigin(req({ referer: 'https://evil.example/x' }), '').allowed).toBe(false)
  })

  it('allows requests without Origin or Referer', () => {
    expect(checkRequestOrigin(req(), '')).toEqual({ allowed: true, reason: 'no-origin' })
  })

  it('rejects a malformed Origin', () => {
    expect(checkRequestOrigin(req({ origin: 'nope' }), '')).toEqual({
      allowed: false,
      reason: 'origin-malformed',
    })
  })
})

describe('clientIp', () => {
  it('uses the first X-Forwarded-For entry', () => {
    expect(clientIp(req({ 'x-forwarded-for': '1.2.3.4, 10.0.0.1' }))).toBe('1.2.3.4')
  })

  it('falls back to X-Real-IP and then to "unknown"', () => {
    expect(clientIp(req({ 'x-real-ip': '5.6.7.8' }))).toBe('5.6.7.8')
    expect(clientIp(req())).toBe('unknown')
  })
})

describe('clientIp trust model', () => {
  it('reads the forwarding headers by default', () => {
    expect(clientIp(req({ 'x-forwarded-for': '9.9.9.9' }), true)).toBe('9.9.9.9')
  })

  it('ignores forwarding headers when the proxy is not trusted and uses one shared key', () => {
    expect(clientIp(req({ 'x-forwarded-for': '9.9.9.9', 'x-real-ip': '8.8.8.8' }), false)).toBe('direct')
  })

  it('parses TRUST_PROXY: only the literal "false" turns trust off', () => {
    expect(parseTrustProxy(undefined)).toBe(true)
    expect(parseTrustProxy('')).toBe(true)
    expect(parseTrustProxy('true')).toBe(true)
    expect(parseTrustProxy(' FALSE ')).toBe(false)
  })
})

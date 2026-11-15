import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { errorFields, log, sanitizeFields } from '@/lib/logger'

beforeEach(() => {
  vi.spyOn(console, 'warn').mockImplementation(() => {})
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('logger', () => {
  it('writes one JSON line with level and event', () => {
    log('warn', 'test.event', { count: 2 })

    const line = vi.mocked(console.warn).mock.calls[0][0] as string
    const parsed = JSON.parse(line)
    expect(parsed).toMatchObject({ level: 'warn', event: 'test.event', count: 2 })
    expect(typeof parsed.ts).toBe('string')
  })

  it('drops fields whose names look like credentials', () => {
    expect(
      sanitizeFields({ apiKey: 'x', xiApiKey: 'y', authorization: 'z', token: 't', status: 401 }),
    ).toEqual({ status: 401 })
  })

  it('serialises errors as name and message only', () => {
    expect(errorFields(new TypeError('boom'))).toEqual({ errorName: 'TypeError', errorMessage: 'boom' })
    expect(errorFields('plain')).toEqual({ errorMessage: 'plain' })
  })
})

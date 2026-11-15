import { describe, expect, it } from 'vitest'

import { createRateLimiter } from '@/lib/rate-limit'

function clock(start = 1_000_000) {
  let t = start
  return {
    now: () => t,
    advance: (ms: number) => {
      t += ms
    },
  }
}

describe('createRateLimiter', () => {
  it('allows up to the limit and then blocks', () => {
    const c = clock()
    const limiter = createRateLimiter({ limit: 3, windowMs: 60_000, now: c.now })

    expect(limiter.check('a')).toEqual({ allowed: true, remaining: 2, retryAfterSec: 0 })
    expect(limiter.check('a').allowed).toBe(true)
    expect(limiter.check('a')).toEqual({ allowed: true, remaining: 0, retryAfterSec: 0 })

    const blocked = limiter.check('a')
    expect(blocked.allowed).toBe(false)
    expect(blocked.remaining).toBe(0)
  })

  it('reports retry-after in whole seconds until the oldest hit leaves the window', () => {
    const c = clock()
    const limiter = createRateLimiter({ limit: 1, windowMs: 60_000, now: c.now })
    limiter.check('a')
    c.advance(15_500)

    const blocked = limiter.check('a')

    expect(blocked.allowed).toBe(false)
    expect(blocked.retryAfterSec).toBe(45) // 44.5s left, rounded up
  })

  it('frees capacity once the window has passed (sliding window)', () => {
    const c = clock()
    const limiter = createRateLimiter({ limit: 2, windowMs: 1_000, now: c.now })
    limiter.check('a')
    c.advance(600)
    limiter.check('a')
    expect(limiter.check('a').allowed).toBe(false)

    c.advance(500) // first hit is now 1100ms old
    expect(limiter.check('a').allowed).toBe(true)
    expect(limiter.check('a').allowed).toBe(false)
  })

  it('tracks keys independently', () => {
    const limiter = createRateLimiter({ limit: 1, windowMs: 60_000, now: clock().now })
    expect(limiter.check('a').allowed).toBe(true)
    expect(limiter.check('b').allowed).toBe(true)
    expect(limiter.check('a').allowed).toBe(false)
  })

  it('bounds memory by evicting the oldest keys beyond maxKeys', () => {
    const c = clock()
    const limiter = createRateLimiter({ limit: 5, windowMs: 60_000, maxKeys: 3, now: c.now })
    for (let i = 0; i < 10; i += 1) {
      limiter.check(`ip-${i}`)
      c.advance(1)
    }

    expect(limiter.size()).toBeLessThanOrEqual(3)
  })

  it('drops expired keys when pruning', () => {
    const c = clock()
    const limiter = createRateLimiter({ limit: 5, windowMs: 1_000, maxKeys: 2, now: c.now })
    limiter.check('old-1')
    limiter.check('old-2')
    c.advance(5_000)
    limiter.check('new-1')
    limiter.check('new-2')
    limiter.check('new-3')

    expect(limiter.size()).toBeLessThanOrEqual(2)
    expect(limiter.check('old-1').remaining).toBe(4) // starts fresh
  })
})

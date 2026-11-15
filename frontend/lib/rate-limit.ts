/**
 * In-memory sliding-window rate limiter.
 *
 * Good enough for a single Node process (demo / single instance). State is per process and
 * lost on restart; with several instances each one keeps its own counters. For a real
 * deployment use a shared store (e.g. Redis or the platform's rate limiting).
 */

export type RateLimitDecision = {
  allowed: boolean
  remaining: number
  /** Seconds the caller should wait before retrying; 0 when allowed. */
  retryAfterSec: number
}

export type RateLimiterOptions = {
  /** Maximum requests per key inside one window. */
  limit: number
  windowMs: number
  /** Upper bound on tracked keys, protects memory against many spoofed IPs. */
  maxKeys?: number
  now?: () => number
}

export type RateLimiter = {
  check(key: string): RateLimitDecision
  /** Number of keys currently tracked (for tests and diagnostics). */
  size(): number
}

export function createRateLimiter(options: RateLimiterOptions): RateLimiter {
  const { limit, windowMs } = options
  const maxKeys = options.maxKeys ?? 10_000
  const now = options.now ?? Date.now
  // Map keeps insertion order, which lets us evict the oldest key when full.
  const hits = new Map<string, number[]>()

  function prune(cutoff: number) {
    for (const [key, stamps] of hits) {
      if (stamps.length === 0 || stamps[stamps.length - 1] <= cutoff) {
        hits.delete(key)
      }
    }
    while (hits.size > maxKeys) {
      const oldest = hits.keys().next().value
      if (oldest === undefined) break
      hits.delete(oldest)
    }
  }

  return {
    check(key: string): RateLimitDecision {
      const t = now()
      const cutoff = t - windowMs
      const recent = (hits.get(key) ?? []).filter((ts) => ts > cutoff)

      if (recent.length >= limit) {
        hits.set(key, recent)
        const retryAfterMs = recent[0] + windowMs - t
        return {
          allowed: false,
          remaining: 0,
          retryAfterSec: Math.max(1, Math.ceil(retryAfterMs / 1000)),
        }
      }

      recent.push(t)
      hits.delete(key) // re-insert so the Map order reflects recency
      hits.set(key, recent)
      if (hits.size > maxKeys) prune(cutoff)

      return { allowed: true, remaining: limit - recent.length, retryAfterSec: 0 }
    },
    size: () => hits.size,
  }
}

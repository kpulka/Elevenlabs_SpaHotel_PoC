/**
 * Request helpers for public API routes: client IP and Origin/Referer allow-list.
 */

const LOCAL_ORIGINS = ['http://localhost', 'http://127.0.0.1']

/** Parses the comma-separated ALLOWED_ORIGINS env value into normalised origins. */
export function parseAllowedOrigins(raw: string | undefined): string[] {
  if (!raw) return []
  return raw
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
    .flatMap((item) => {
      try {
        return [new URL(item).origin]
      } catch {
        return [] // ignore malformed entries instead of failing the whole route
      }
    })
}

function originOf(value: string | null): string | null {
  if (!value) return null
  try {
    return new URL(value).origin
  } catch {
    return null
  }
}

export type OriginDecision =
  | { allowed: true; reason: 'same-origin' | 'allow-list' | 'local-dev' | 'no-origin' }
  | { allowed: false; reason: 'origin-not-allowed' | 'origin-malformed' }

/**
 * Decides whether a request may use the endpoint.
 *
 * - Origin header present: must be the site itself, localhost / 127.0.0.1, or in ALLOWED_ORIGINS.
 * - No Origin: fall back to Referer with the same rules.
 * - Neither header: allowed (non-browser clients such as curl, health checks). The caller logs it.
 *   Browsers always send Origin on cross-origin fetches, so this only lets non-browser clients in;
 *   the rate limit still applies to them.
 */
export function checkRequestOrigin(
  req: Request,
  allowedOriginsEnv: string | undefined = process.env.ALLOWED_ORIGINS,
): OriginDecision {
  const selfOrigin = new URL(req.url).origin
  const origin = req.headers.get('origin')
  const referer = req.headers.get('referer')
  const candidate = origin ?? referer

  if (!candidate) {
    return { allowed: true, reason: 'no-origin' }
  }
  const parsed = originOf(candidate)
  if (!parsed) {
    return { allowed: false, reason: 'origin-malformed' }
  }
  if (parsed === selfOrigin) {
    return { allowed: true, reason: 'same-origin' }
  }
  if (LOCAL_ORIGINS.some((local) => parsed === local || parsed.startsWith(`${local}:`))) {
    return { allowed: true, reason: 'local-dev' }
  }
  if (parseAllowedOrigins(allowedOriginsEnv).includes(parsed)) {
    return { allowed: true, reason: 'allow-list' }
  }
  return { allowed: false, reason: 'origin-not-allowed' }
}

/**
 * Whether X-Forwarded-For / X-Real-IP may be used to identify the client. Default: true (the app is
 * meant to run behind a proxy that sets them). Set TRUST_PROXY=false when the app is exposed directly:
 * then the headers are ignored, because clients could spoof them, and every request shares one
 * rate-limit key (spoof-proof, but coarse: all visitors share the same budget).
 */
export function parseTrustProxy(raw: string | undefined): boolean {
  return raw?.trim().toLowerCase() !== 'false'
}

/** Key used when the forwarding headers are not trusted. */
export const DIRECT_CLIENT_KEY = 'direct'

/**
 * Client IP for rate limiting: first entry of X-Forwarded-For, then X-Real-IP.
 * X-Forwarded-For is trusted by default because the app runs behind a proxy that sets it; if the app
 * is exposed directly, clients can spoof it: set TRUST_PROXY=false, or enforce the limit at the proxy.
 */
export function clientIp(
  req: Request,
  trustProxy: boolean = parseTrustProxy(process.env.TRUST_PROXY),
): string {
  if (!trustProxy) return DIRECT_CLIENT_KEY
  const forwarded = req.headers.get('x-forwarded-for')
  if (forwarded) {
    const first = forwarded.split(',')[0]?.trim()
    if (first) return first
  }
  return req.headers.get('x-real-ip')?.trim() || 'unknown'
}

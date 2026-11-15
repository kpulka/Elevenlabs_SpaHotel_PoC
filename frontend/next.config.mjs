const isDev = process.env.NODE_ENV !== 'production'

/**
 * Content-Security-Policy.
 *
 * Trade-offs:
 * - script-src 'unsafe-inline': Next.js injects inline bootstrap/hydration scripts and JSON-LD.
 *   A per-request nonce would need middleware, which turns the pages into dynamic renders and
 *   gives up static generation for a brochure site. We accept 'unsafe-inline' for scripts and
 *   compensate with a strict default-src, frame-ancestors 'none' and no third-party script hosts.
 * - 'unsafe-eval' is only added in development (React / Turbopack dev tooling needs it).
 * - style-src 'unsafe-inline': Next and the ElevenLabs widget inject style tags at runtime.
 *
 * ElevenLabs widget (public/widget/convai-widget-embed.js) needs:
 * - connect-src: api.elevenlabs.io (signed URL, REST), wss://*.elevenlabs.io (realtime signaling
 *   incl. livekit.rtc.elevenlabs.io), m1.openfpcdn.io (fingerprint telemetry of the widget).
 * - img-src: storage.googleapis.com (avatar/flag images), blob: and data: for generated images.
 * - style-src / font-src: fonts.googleapis.com (@import inside the widget), fonts.gstatic.com.
 * - frame-src: *.elevenlabs.io (the widget may render an iframe; the hook adds allow="microphone").
 * - media-src: blob: and data: for audio playback, *.elevenlabs.io for audio URLs.
 * - worker-src blob: for audio worklets / workers created from blob URLs.
 * Microphone access is governed by Permissions-Policy (not CSP), see below.
 */
const ELEVENLABS = 'https://*.elevenlabs.io wss://*.elevenlabs.io'

const contentSecurityPolicy = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ''}`,
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "font-src 'self' data: https://fonts.gstatic.com",
  "img-src 'self' data: blob: https://storage.googleapis.com",
  `connect-src 'self' ${ELEVENLABS} https://api.elevenlabs.io https://m1.openfpcdn.io`,
  `media-src 'self' blob: data: ${ELEVENLABS}`,
  `frame-src 'self' ${ELEVENLABS}`,
  "worker-src 'self' blob:",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join('; ')

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Do not advertise the framework in responses.
  poweredByHeader: false,
  images: {
    // next/image optimizer enabled: AVIF/WebP instead of raw PNG/JPEG.
    unoptimized: false,
    formats: ['image/avif', 'image/webp'],
  },
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'Content-Security-Policy', value: contentSecurityPolicy },
          // Clickjacking: the site must never be framed (CSP frame-ancestors is the modern control).
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Strict-Transport-Security', value: 'max-age=63072000' },
          {
            key: 'Permissions-Policy',
            // Note: the microphone must stay enabled, the ElevenLabs widget uses getUserMedia.
            // With no clause the microphone is allowed by default; camera and geolocation stay blocked.
            value: 'camera=(), geolocation=()',
          },
        ],
      },
    ]
  },
}

export default nextConfig

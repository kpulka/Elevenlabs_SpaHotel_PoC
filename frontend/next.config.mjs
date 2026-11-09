/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    // Optymalizator next/image włączony: AVIF/WebP zamiast surowych PNG/JPEG.
    unoptimized: false,
    formats: ['image/avif', 'image/webp'],
  },
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Strict-Transport-Security', value: 'max-age=63072000' },
          {
            key: 'Permissions-Policy',
            // Uwaga: mikrofon musi być włączony — widget ElevenLabs używa getUserMedia.
            // Domyślnie (bez klauzuli) mikrofon jest dozwolony; camerę/geo zostawiamy zablokowane.
            value: 'camera=(), geolocation=()',
          },
        ],
      },
    ]
  },
}

export default nextConfig

/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    unoptimized: true,
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
            // The microphone must stay enabled: the ElevenLabs widget uses getUserMedia.
            // Camera and geolocation are disabled because the site does not need them.
            value: 'camera=(), geolocation=()',
          },
        ],
      },
    ]
  },
}

export default nextConfig

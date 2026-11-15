/**
 * Shared SEO constants for the site.
 *
 * NEXT_PUBLIC_SITE_URL is set in production (e.g. https://bukowydwor.example).
 * The fallback is the example domain from the project docs: sitemap/robots/OG need
 * a valid absolute URL at build time, also in demo environments.
 */
export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL ?? 'https://bukowydwor.example').replace(
  /\/+$/,
  '',
)

export const SITE_NAME = 'Bukowy Dwór'

export const SITE_TITLE = 'Bukowy Dwór — Uzdrowisko Termalne w Krynicy-Zdroju'

export const SITE_DESCRIPTION =
  'Uzdrowisko Termalne Bukowy Dwór w Krynicy-Zdroju — pokoje bez barier, baseny termalne, zabiegi balneologiczne i restauracja z dietami leczniczymi.'

/** Shared Open Graph image (1200x630, screenshot of the Anna widget). */
export const OG_IMAGE = {
  url: '/og/anna-widget.jpg',
  width: 1200,
  height: 630,
  alt: 'Rozmowa z Anną — wirtualną recepcjonistką Uzdrowiska Bukowy Dwór',
} as const

/** Public site routes (no API routes), used by sitemap.ts. */
export const PUBLIC_ROUTES = ['/', '/pokoje', '/spa', '/restauracja', '/dojazd', '/kontakt', '/polityka'] as const

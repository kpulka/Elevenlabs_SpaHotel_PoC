/**
 * Wspólne stałe SEO dla serwisu.
 *
 * NEXT_PUBLIC_SITE_URL ustawiamy w środowisku produkcyjnym (np. https://bukowydwor.pl).
 * Fallback to domena przykładowa z dokumentacji projektu — sitemap/robots/OG muszą mieć
 * poprawny absolutny URL już w buildzie, także na środowiskach demo.
 */
export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL ?? 'https://bukowydwor.example').replace(
  /\/+$/,
  '',
)

export const SITE_NAME = 'Bukowy Dwór'

export const SITE_DESCRIPTION =
  'Uzdrowisko Termalne Bukowy Dwór w Krynicy-Zdroju — pokoje bez barier, baseny termalne, zabiegi balneologiczne i restauracja z dietami leczniczymi.'

/** Wspólny obraz Open Graph (1200x630, zrzut widgetu Anny). */
export const OG_IMAGE = {
  url: '/og/anna-widget.jpg',
  width: 1200,
  height: 630,
  alt: 'Rozmowa z Anną — wirtualną recepcjonistką Uzdrowiska Bukowy Dwór',
} as const

/** Publiczne trasy serwisu (bez stron API) — używane w sitemap.ts. */
export const PUBLIC_ROUTES = ['/', '/pokoje', '/spa', '/restauracja', '/dojazd', '/kontakt'] as const

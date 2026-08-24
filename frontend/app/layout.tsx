import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import { Inter, Playfair_Display } from 'next/font/google'

import { AnnaEmbedWidget } from '@/components/anna-embed-widget'
import { LanguageProvider } from '@/context/language-context'
import './globals.css'

const inter = Inter({
  subsets: ['latin', 'latin-ext'],
  variable: '--font-inter',
  display: 'swap',
})

const playfair = Playfair_Display({
  subsets: ['latin', 'latin-ext'],
  variable: '--font-playfair',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Bukowy Dwór — Uzdrowisko Termalne w Krynicy-Zdroju',
  description:
    'Uzdrowisko Termalne Bukowy Dwór w Krynicy-Zdroju — pokoje, baseny termalne, zabiegi balneologiczne i restauracja z dietami leczniczymi. Spokój, leczenie i regeneracja w górskim otoczeniu.',
  generator: 'v0.app',
  icons: {
    icon: [
      {
        url: '/icon-light-32x32.png',
        media: '(prefers-color-scheme: light)',
      },
      {
        url: '/icon-dark-32x32.png',
        media: '(prefers-color-scheme: dark)',
      },
      {
        url: '/icon.svg',
        type: 'image/svg+xml',
      },
    ],
    apple: '/apple-icon.png',
  },
}

export const viewport: Viewport = {
  colorScheme: 'light',
  themeColor: '#1b2a4a',
  userScalable: true,
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="pl" className={`${inter.variable} ${playfair.variable}`}>
      <body className="bg-background antialiased">
        <LanguageProvider>
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[2000] focus:rounded-md focus:bg-navy focus:px-5 focus:py-3 focus:text-base focus:font-medium focus:text-white focus:outline-2 focus:outline-offset-2 focus:outline-gold"
          >
            Przejdź do treści
          </a>
          {children}
          <AnnaEmbedWidget />
          {process.env.NODE_ENV === 'production' && <Analytics />}
        </LanguageProvider>
      </body>
    </html>
  )
}

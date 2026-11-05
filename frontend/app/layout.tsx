import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import { Inter, Playfair_Display } from 'next/font/google'

import { AnnaEmbedWidget } from '@/components/anna-embed-widget'
import { SkipLink } from '@/components/skip-link'
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
  title: 'Bukowy Dwór — Thermal Spa & Health Resort in Krynica-Zdrój',
  description:
    'Bukowy Dwór is a barrier-free thermal spa and balneological health resort in Krynica-Zdrój. Thermal pools, sulphur and peat-mud treatments, physiotherapy and diet-based dining, with a virtual receptionist available 24/7.',
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
    <html lang="en" className={`${inter.variable} ${playfair.variable}`}>
      <body className="bg-background antialiased">
        <LanguageProvider>
          <SkipLink />
          {children}
          <AnnaEmbedWidget />
          {process.env.NODE_ENV === 'production' && <Analytics />}
        </LanguageProvider>
      </body>
    </html>
  )
}

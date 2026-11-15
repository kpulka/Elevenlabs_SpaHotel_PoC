import type { Metadata } from 'next'
import type { ReactNode } from 'react'

import { SITE_NAME } from '@/lib/site'

const title = 'Polityka prywatności'
const description =
  'Polityka prywatności demonstracyjnego serwisu Uzdrowiska Bukowy Dwór: rozmowa głosowa z Anną (ElevenLabs), mikrofon, nagrania, okresy przechowywania, analityka i prawa osób, których dane dotyczą.'

export const metadata: Metadata = {
  title,
  description,
  alternates: { canonical: '/polityka' },
  openGraph: {
    type: 'website',
    locale: 'pl_PL',
    siteName: SITE_NAME,
    url: '/polityka',
    title: `${title} | ${SITE_NAME}`,
    description,
  },
}

export default function PolitykaLayout({ children }: { children: ReactNode }) {
  return <>{children}</>
}

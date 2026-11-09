import type { Metadata } from 'next'
import type { ReactNode } from 'react'

import { OG_IMAGE, SITE_NAME } from '@/lib/site'

const title = 'Kontakt i Recepcja 24/7'
const description =
  'Kontakt z Uzdrowiskiem Bukowy Dwór w Krynicy-Zdroju: recepcja czynna całodobowo, telefon +48 18 123 45 67, e-mail recepcja@bukowydwor.pl, formularz zapytania o rezerwację oraz rozmowa na żywo z Anną.'

export const metadata: Metadata = {
  title,
  description,
  alternates: { canonical: '/kontakt' },
  openGraph: {
    type: 'website',
    locale: 'pl_PL',
    siteName: SITE_NAME,
    url: '/kontakt',
    title: `${title} | ${SITE_NAME}`,
    description,
    images: [OG_IMAGE],
  },
}

export default function KontaktLayout({ children }: { children: ReactNode }) {
  return <>{children}</>
}

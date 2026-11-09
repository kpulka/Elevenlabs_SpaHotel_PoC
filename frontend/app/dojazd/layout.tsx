import type { Metadata } from 'next'
import type { ReactNode } from 'react'

import { OG_IMAGE, SITE_NAME } from '@/lib/site'

const title = 'Dojazd, Transfer i Dostępność'
const description =
  'Jak dojechać do Uzdrowiska Bukowy Dwór w Krynicy-Zdroju: samochodem, pociągiem PKP lub autobusem PKS, bezpłatny transfer meleksem z dworca oraz udogodnienia dla osób z niepełnosprawnościami.'

export const metadata: Metadata = {
  title,
  description,
  alternates: { canonical: '/dojazd' },
  openGraph: {
    type: 'website',
    locale: 'pl_PL',
    siteName: SITE_NAME,
    url: '/dojazd',
    title: `${title} | ${SITE_NAME}`,
    description,
    images: [OG_IMAGE],
  },
}

export default function DojazdLayout({ children }: { children: ReactNode }) {
  return <>{children}</>
}

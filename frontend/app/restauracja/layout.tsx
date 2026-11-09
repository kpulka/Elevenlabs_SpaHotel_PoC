import type { Metadata } from 'next'
import type { ReactNode } from 'react'

import { OG_IMAGE, SITE_NAME } from '@/lib/site'

const title = 'Restauracja „Bukowy Smak” i Diety Lecznicze'
const description =
  'Restauracja „Bukowy Smak” w Uzdrowisku Bukowy Dwór: lokalne produkty z Beskidu Sądeckiego, bufet szwedzki oraz diety lecznicze (cukrzycowa, lekkostrawna, bezglutenowa) bez dodatkowych opłat.'

export const metadata: Metadata = {
  title,
  description,
  alternates: { canonical: '/restauracja' },
  openGraph: {
    type: 'website',
    locale: 'pl_PL',
    siteName: SITE_NAME,
    url: '/restauracja',
    title: `${title} | ${SITE_NAME}`,
    description,
    images: [OG_IMAGE],
  },
}

export default function RestauracjaLayout({ children }: { children: ReactNode }) {
  return <>{children}</>
}

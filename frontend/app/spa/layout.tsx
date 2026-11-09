import type { Metadata } from 'next'
import type { ReactNode } from 'react'

import { OG_IMAGE, SITE_NAME } from '@/lib/site'

const title = 'Baseny Termalne i Zabiegi Lecznicze'
const description =
  'Baseny termalne z wodą siarczkową w cenie pobytu oraz płatne zabiegi balneologiczne: kąpiele siarczkowe i borowinowe, masaże i fizykoterapia w Krynicy-Zdroju, realizowane pod nadzorem wykwalifikowanego personelu medycznego.'

export const metadata: Metadata = {
  title,
  description,
  alternates: { canonical: '/spa' },
  openGraph: {
    type: 'website',
    locale: 'pl_PL',
    siteName: SITE_NAME,
    url: '/spa',
    title: `${title} | ${SITE_NAME}`,
    description,
    images: [OG_IMAGE],
  },
}

export default function SpaLayout({ children }: { children: ReactNode }) {
  return <>{children}</>
}

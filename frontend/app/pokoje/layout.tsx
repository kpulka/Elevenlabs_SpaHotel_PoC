import type { Metadata } from 'next'
import type { ReactNode } from 'react'

import { OG_IMAGE, SITE_NAME } from '@/lib/site'

const title = 'Pokoje i Apartamenty bez Barier'
const description =
  'Pokoje jedno- i dwuosobowe oraz apartamenty w Uzdrowisku Bukowy Dwór: łazienki bez progów, uchwyty i przyciski alarmowe przy łóżku, widok na beskidzki las. Sprawdź wyposażenie i ceny za dobę.'

export const metadata: Metadata = {
  title,
  description,
  alternates: { canonical: '/pokoje' },
  openGraph: {
    type: 'website',
    locale: 'pl_PL',
    siteName: SITE_NAME,
    url: '/pokoje',
    title: `${title} | ${SITE_NAME}`,
    description,
    images: [OG_IMAGE],
  },
}

export default function PokojeLayout({ children }: { children: ReactNode }) {
  return <>{children}</>
}

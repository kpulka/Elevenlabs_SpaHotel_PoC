'use client'

import { useLanguage } from '@/context/language-context'

export function SkipLink() {
  const { t } = useLanguage()

  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[2000] focus:rounded-md focus:bg-navy focus:px-5 focus:py-3 focus:text-base focus:font-medium focus:text-white focus:outline-2 focus:outline-offset-2 focus:outline-gold"
    >
      {t.nav.skipToContent}
    </a>
  )
}

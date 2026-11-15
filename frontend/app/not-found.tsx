'use client'

import { useEffect } from 'react'

import { HotelButton } from '@/components/hotel-button'
import { Section } from '@/components/section'
import { SiteFooter } from '@/components/site-footer'
import { SiteHeader } from '@/components/site-header'
import { useLanguage } from '@/context/language-context'
import { logger } from '@/lib/logger'

export default function NotFound() {
  const { t } = useLanguage()

  useEffect(() => {
    // Path is not logged: it can carry user-entered text. The event alone shows dead links in aggregate.
    logger.info('app.not_found')
  }, [])

  return (
    <>
      <SiteHeader />
      <main id="main-content">
        <Section tone="warm-white">
          <div className="mx-auto flex max-w-xl flex-col items-center gap-6 text-center">
            <h1 className="font-serif text-3xl font-bold text-navy md:text-4xl">{t.notFoundPage.title}</h1>
            <p className="text-lg leading-relaxed text-charcoal/85">{t.notFoundPage.text}</p>
            <HotelButton href="/" variant="primary">
              {t.notFoundPage.home}
            </HotelButton>
          </div>
        </Section>
      </main>
      <SiteFooter />
    </>
  )
}

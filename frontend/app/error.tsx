'use client'

import { useEffect } from 'react'

import { HotelButton } from '@/components/hotel-button'
import { Section } from '@/components/section'
import { SiteHeader } from '@/components/site-header'
import { useLanguage } from '@/context/language-context'
import { logger } from '@/lib/logger'

/**
 * Segment error boundary. Renders inside the root layout (so the language provider is available).
 * Logs the digest and error name only: the message can contain request-specific data.
 */
export default function AppError({
  error,
  retry,
}: {
  error: Error & { digest?: string }
  retry: () => void
}) {
  const { t } = useLanguage()

  useEffect(() => {
    logger.error('app.error_boundary', { digest: error.digest ?? null, errorName: error.name })
  }, [error])

  return (
    <>
      <SiteHeader />
      <main id="main-content">
        <Section tone="warm-white">
          <div className="mx-auto flex max-w-xl flex-col items-center gap-6 text-center">
            <h1 className="font-serif text-3xl font-bold text-navy md:text-4xl">{t.errorPage.title}</h1>
            <p className="text-lg leading-relaxed text-charcoal/85">{t.errorPage.text}</p>
            <div className="flex flex-col gap-4 sm:flex-row">
              <HotelButton variant="primary" onClick={() => retry()}>
                {t.errorPage.retry}
              </HotelButton>
              <HotelButton href="/" variant="secondary">
                {t.errorPage.home}
              </HotelButton>
            </div>
          </div>
        </Section>
      </main>
    </>
  )
}

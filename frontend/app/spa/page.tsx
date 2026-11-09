'use client'

import Image from 'next/image'

import { AnnaInlineBanner } from '@/components/anna-inline-banner'
import { HotelButton } from '@/components/hotel-button'
import { SiteFooter } from '@/components/site-footer'
import { SiteHeader } from '@/components/site-header'
import { TreatmentCard } from '@/components/treatment-card'
import { useLanguage } from '@/context/language-context'
import { getTreatments, type TreatmentCategory } from '@/lib/hotel-data'

export default function SpaPage() {
  const { language, t } = useLanguage()
  const currentTreatments = getTreatments(language)

  const categories: Array<{ key: TreatmentCategory; label: string }> = [
    { key: 'thermal', label: t.spaPage.categoryThermal },
    { key: 'balneo', label: t.spaPage.categoryBalneo },
    { key: 'physio', label: t.spaPage.categoryPhysio },
  ]

  return (
    <>
      <SiteHeader />
      <main id="main-content">
        <section className="relative flex min-h-[420px] items-center overflow-hidden">
          <Image
            src="/images/spa-pool.png"
            alt={t.images.spaHeroAlt}
            fill
            priority
            className="object-cover"
          />
          <div className="absolute inset-0 bg-navy/60" />
          <div className="relative z-10 mx-auto max-w-[1280px] px-4 md:px-8">
            <p className="text-sm font-semibold tracking-[0.2em] text-gold uppercase">
              {t.spaPage.tag}
            </p>
            <h1 className="mt-3 max-w-2xl text-balance font-serif text-4xl font-bold text-white md:text-5xl">
              {t.spaPage.title}
            </h1>
            <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/90">
              {t.spaPage.subtitle}
            </p>
          </div>
        </section>

        <AnnaInlineBanner />

        {categories.map((category) => (
          <section key={category.key} className="border-b border-gold/15 bg-warm-white py-16 md:py-20">
            <div className="mx-auto max-w-[1280px] px-4 md:px-8">
              <h2 className="font-serif text-3xl font-bold text-navy">{category.label}</h2>
              <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {currentTreatments
                  .filter((treatment) => treatment.category === category.key)
                  .map((treatment) => (
                    <TreatmentCard key={treatment.id} treatment={treatment} />
                  ))}
              </div>
            </div>
          </section>
        ))}

        <section className="bg-cream py-16 md:py-24">
          <div className="mx-auto grid max-w-[1280px] gap-10 px-4 md:grid-cols-2 md:items-center md:px-8">
            <div className="relative aspect-[4/3] w-full overflow-hidden rounded-2xl">
              <Image
                src="/images/treatment-room.png"
                alt={t.images.treatmentRoomAlt}
                fill
                className="object-cover"
              />
            </div>
            <div>
              <p className="text-sm font-semibold tracking-[0.15em] text-sage uppercase">
                {t.spaPage.supervisionEyebrow}
              </p>
              <h2 className="mt-3 font-serif text-3xl font-bold text-navy md:text-4xl">
                {t.spaPage.supervisionTitle}
              </h2>
              <p className="mt-4 text-lg leading-relaxed text-charcoal/85">
                {t.spaPage.supervisionText}
              </p>
              <HotelButton href="/kontakt" variant="secondary" className="mt-8">
                {t.spaPage.supervisionCta}
              </HotelButton>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  )
}

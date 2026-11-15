'use client'

import Image from 'next/image'

import { AnnaInlineBanner } from '@/components/anna-inline-banner'
import { HotelButton } from '@/components/hotel-button'
import { PageHero } from '@/components/page-hero'
import { Section } from '@/components/section'
import { SiteFooter } from '@/components/site-footer'
import { SiteHeader } from '@/components/site-header'
import { TreatmentCard } from '@/components/treatment-card'
import { useLanguage } from '@/context/language-context'
import { getTreatments, type TreatmentCategory } from '@/lib/hotel'

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
        <PageHero
          image="/images/spa-pool.webp"
          alt={t.images.spaHeroAlt}
          tag={t.spaPage.tag}
          title={t.spaPage.title}
          subtitle={t.spaPage.subtitle}
        />

        <AnnaInlineBanner />

        {categories.map((category) => (
          <Section key={category.key} tone="warm-white" className="border-b border-gold/15 md:py-20">
            <h2 className="font-serif text-3xl font-bold text-navy">{category.label}</h2>
            <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {currentTreatments
                .filter((treatment) => treatment.category === category.key)
                .map((treatment) => (
                  <TreatmentCard key={treatment.id} treatment={treatment} />
                ))}
            </div>
          </Section>
        ))}

        <Section tone="cream" containerClassName="grid gap-10 md:grid-cols-2 md:items-center">
          <div className="relative aspect-[4/3] w-full overflow-hidden rounded-2xl">
            <Image
              src="/images/treatment-room.webp"
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
        </Section>
      </main>
      <SiteFooter />
    </>
  )
}

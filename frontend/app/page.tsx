'use client'

import { Phone } from 'lucide-react'
import Image from 'next/image'
import Link from 'next/link'

import { AccessibilitySection } from '@/components/accessibility-section'
import { AnnaIntroSection } from '@/components/anna-intro-section'
import { HighlightsSection } from '@/components/highlights-section'
import { HotelButton } from '@/components/hotel-button'
import { PageHero } from '@/components/page-hero'
import { RoomCard } from '@/components/room-card'
import { Section } from '@/components/section'
import { SiteFooter } from '@/components/site-footer'
import { SiteHeader } from '@/components/site-header'
import { useLanguage } from '@/context/language-context'
import { contactInfo, getRooms } from '@/lib/hotel'

export default function HomePage() {
  const { language, t } = useLanguage()
  const currentRooms = getRooms(language)

  return (
    <>
      <SiteHeader />
      <main id="main-content">
        <PageHero
          variant="home"
          minHeight={640}
          image="/images/hero-pool.webp"
          alt={t.images.homeHeroAlt}
          tag={t.home.heroTag}
          title={t.home.heroTitle}
          subtitle={t.home.heroSubtitle}
        >
          <div className="mt-10 flex flex-col gap-4 sm:flex-row">
            <HotelButton href="/kontakt" variant="primary" className="bg-gold text-navy hover:bg-gold/90">
              {t.nav.bookStay}
            </HotelButton>
            <HotelButton href="/pokoje" variant="ghost">
              {t.home.seeAllRooms}
            </HotelButton>
          </div>
          <a
            href={contactInfo.phoneHref}
            className="mt-8 inline-flex items-center gap-2 text-lg font-semibold text-white outline-none hover:text-gold focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-gold"
          >
            <Phone className="size-5" aria-hidden="true" />
            {contactInfo.phone}
          </a>
        </PageHero>

        <AnnaIntroSection />

        <HighlightsSection />

        <Section tone="warm-white" aria-labelledby="rooms-heading">
          <div className="flex flex-col items-start justify-between gap-6 md:flex-row md:items-end">
            <div>
              <p className="text-sm font-semibold tracking-[0.15em] text-sage uppercase">
                {t.roomsPage.tag}
              </p>
              <h2 id="rooms-heading" className="mt-3 font-serif text-3xl font-bold text-navy md:text-4xl">
                {t.home.roomsTitle}
              </h2>
            </div>
            <Link
              href="/pokoje"
              className="text-base font-semibold text-navy underline-offset-4 outline-none hover:underline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-gold"
            >
              {t.home.seeAllRooms} →
            </Link>
          </div>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {currentRooms.map((room) => (
              <RoomCard key={room.id} room={room} />
            ))}
          </div>
        </Section>

        <Section tone="navy" className="relative overflow-hidden" containerClassName="grid gap-10 md:grid-cols-2 md:items-center">
          <div>
            <p className="text-sm font-semibold tracking-[0.15em] text-gold uppercase">
              {t.home.natureEyebrow}
            </p>
            <h2 className="mt-3 font-serif text-3xl font-bold text-white md:text-4xl">
              {t.home.natureTitle}
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-white/85">
              {t.home.natureText}
            </p>
            <HotelButton href="/dojazd" variant="secondary" className="mt-8 border-gold text-white hover:bg-gold hover:text-navy">
              {t.home.natureCta}
            </HotelButton>
          </div>
          <div className="relative aspect-[4/3] w-full overflow-hidden rounded-2xl">
            <Image
              src="/images/nature-path.webp"
              alt={t.images.natureAlt}
              fill
              className="object-cover"
            />
          </div>
        </Section>

        <AccessibilitySection />
      </main>
      <SiteFooter />
    </>
  )
}

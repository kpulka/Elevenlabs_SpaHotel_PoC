'use client'

import { HotelButton } from '@/components/hotel-button'
import { PageHero } from '@/components/page-hero'
import { RoomCard } from '@/components/room-card'
import { Section } from '@/components/section'
import { SiteFooter } from '@/components/site-footer'
import { SiteHeader } from '@/components/site-header'
import { useLanguage } from '@/context/language-context'
import { getRooms } from '@/lib/hotel'

export default function RoomsPage() {
  const { language, t } = useLanguage()
  const currentRooms = getRooms(language)

  return (
    <>
      <SiteHeader />
      <main id="main-content">
        <PageHero
          image="/images/hero-rooms.webp"
          alt={t.images.roomsHeroAlt}
          tag={t.roomsPage.tag}
          title={t.roomsPage.title}
          subtitle={t.roomsPage.subtitle}
        />

        <Section tone="warm-white">
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {currentRooms.map((room) => (
              <RoomCard key={room.id} room={room} />
            ))}
          </div>
        </Section>

        <Section tone="cream">
          <div className="grid gap-10 lg:grid-cols-2">
            {currentRooms.map((room) => (
              <div
                key={`${room.id}-detail`}
                id={room.slug}
                className="rounded-2xl border border-gold/20 bg-warm-white p-8"
              >
                <h2 className="font-serif text-2xl font-bold text-navy">{room.name}</h2>
                <p className="mt-3 text-base leading-relaxed text-charcoal/85">
                  {room.longDescription}
                </p>
                <ul className="mt-5 grid gap-2 sm:grid-cols-2">
                  {room.features.map((feature) => (
                    <li key={feature} className="text-sm leading-relaxed text-charcoal/80">
                      • {feature}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </Section>

        <section className="bg-navy py-16 text-center md:py-20">
          <div className="mx-auto max-w-2xl px-4 md:px-8">
            <h2 className="font-serif text-3xl font-bold text-white">
              {t.roomsPage.contactTitle}
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-white/85">
              {t.roomsPage.contactText}
            </p>
            <div className="mt-8 flex justify-center">
              <HotelButton href="/kontakt" variant="primary" className="bg-gold text-navy hover:bg-gold/90">
                {t.roomsPage.contactCta}
              </HotelButton>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  )
}

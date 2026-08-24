'use client'

import Image from 'next/image'

import { HotelButton } from '@/components/hotel-button'
import { RoomCard } from '@/components/room-card'
import { SiteFooter } from '@/components/site-footer'
import { SiteHeader } from '@/components/site-header'
import { useLanguage } from '@/context/language-context'
import { getRooms } from '@/lib/hotel-data'

export default function RoomsPage() {
  const { language, t } = useLanguage()
  const currentRooms = getRooms(language)

  return (
    <>
      <SiteHeader />
      <main id="main-content">
        <section className="relative flex min-h-[420px] items-center overflow-hidden">
          <Image
            src="/images/hero-rooms.png"
            alt="Pokoje i apartamenty — Bukowy Dwór"
            fill
            priority
            className="object-cover"
          />
          <div className="absolute inset-0 bg-navy/60" />
          <div className="relative z-10 mx-auto max-w-[1280px] px-4 md:px-8">
            <p className="text-sm font-semibold tracking-[0.2em] text-gold uppercase">
              {t.roomsPage.tag}
            </p>
            <h1 className="mt-3 max-w-2xl text-balance font-serif text-4xl font-bold text-white md:text-5xl">
              {t.roomsPage.title}
            </h1>
            <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/90">
              {t.roomsPage.subtitle}
            </p>
          </div>
        </section>

        <section className="bg-warm-white py-16 md:py-24">
          <div className="mx-auto max-w-[1280px] px-4 md:px-8">
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {currentRooms.map((room) => (
                <RoomCard key={room.id} room={room} />
              ))}
            </div>
          </div>
        </section>

        <section className="bg-cream py-16 md:py-24">
          <div className="mx-auto max-w-[1280px] px-4 md:px-8">
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
          </div>
        </section>

        <section className="bg-navy py-16 text-center md:py-20">
          <div className="mx-auto max-w-2xl px-4 md:px-8">
            <h2 className="font-serif text-3xl font-bold text-white">
              {language === 'pl' ? 'Masz pytania dotyczące pokoi?' : 'Have Questions About Our Rooms?'}
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-white/85">
              {language === 'pl'
                ? 'Zadzwoń do recepcji lub zapytaj wirtualną asystentkę Annę — pomożemy dobrać idealny pokój dla Ciebie.'
                : 'Call our front desk or chat live with Anna — we will help you choose the ideal room for your stay.'}
            </p>
            <div className="mt-8 flex justify-center">
              <HotelButton href="/kontakt" variant="primary" className="bg-gold text-navy hover:bg-gold/90">
                {language === 'pl' ? 'Skontaktuj się z nami' : 'Contact Front Desk'}
              </HotelButton>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  )
}

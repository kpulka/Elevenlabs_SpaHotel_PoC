'use client'

import { Flower2, Phone, UtensilsCrossed, Waves } from 'lucide-react'
import Image from 'next/image'
import Link from 'next/link'

import { AccessibilitySection } from '@/components/accessibility-section'
import { AnnaIntroSection } from '@/components/anna-intro-section'
import { HotelButton } from '@/components/hotel-button'
import { RoomCard } from '@/components/room-card'
import { SiteFooter } from '@/components/site-footer'
import { SiteHeader } from '@/components/site-header'
import { useLanguage } from '@/context/language-context'
import { contactInfo, getRooms } from '@/lib/hotel-data'

export default function HomePage() {
  const { language, t } = useLanguage()
  const currentRooms = getRooms(language)

  const highlights = [
    {
      icon: Waves,
      title: language === 'pl' ? 'Baseny termalne 32–34°C' : 'Thermal Pools 32–34°C',
      description:
        language === 'pl'
          ? 'Dwa baseny o kojących temperaturach, otoczone lasem bukowym.'
          : 'Two therapeutic mineral pools with soothing temperatures surrounded by mountain beech woods.',
    },
    {
      icon: Flower2,
      title: language === 'pl' ? 'Zabiegi balneologiczne' : 'Balneotherapy Treatments',
      description:
        language === 'pl'
          ? 'Kąpiele siarczkowe, borowinowe i fizykoterapia pod opieką specjalistów.'
          : 'Natural sulphur baths, peat mud therapy, and customized physiotherapy under clinical supervision.',
    },
    {
      icon: UtensilsCrossed,
      title: language === 'pl' ? 'Restauracja z dietami leczniczymi' : 'Restaurant & Clinical Diets',
      description:
        language === 'pl'
          ? 'Posiłki dostosowane do zaleceń dietetycznych i potrzeb zdrowotnych.'
          : 'Delicious regional dining paired with 5 specialized therapeutic diet options included.',
    },
  ]

  return (
    <>
      <SiteHeader />
      <main id="main-content">
        <section className="relative flex min-h-[640px] items-center overflow-hidden">
          <Image
            src="/images/hero-pool.png"
            alt="Basen termalny Bukowego Dworu"
            fill
            priority
            className="object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-navy/80 via-navy/40 to-navy/20" />
          <div className="relative z-10 mx-auto w-full max-w-[1280px] px-4 py-24 md:px-8">
            <div className="max-w-2xl">
              <p className="text-sm font-semibold tracking-[0.2em] text-gold uppercase">
                {t.home.heroTag}
              </p>
              <h1 className="mt-4 text-balance font-serif text-4xl font-bold leading-tight text-white md:text-6xl">
                {t.home.heroTitle}
              </h1>
              <p className="mt-6 max-w-xl text-lg leading-relaxed text-white/90 md:text-xl">
                {t.home.heroSubtitle}
              </p>
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
            </div>
          </div>
        </section>

        <AnnaIntroSection />

        <section aria-labelledby="highlights-heading" className="bg-cream py-16 md:py-24">
          <div className="mx-auto max-w-[1280px] px-4 md:px-8">
            <div className="mx-auto max-w-2xl text-center">
              <h2 id="highlights-heading" className="font-serif text-3xl font-bold text-navy md:text-4xl">
                {t.home.featuresTitle}
              </h2>
            </div>
            <div className="mt-12 grid gap-6 sm:grid-cols-3">
              {highlights.map((item) => {
                const Icon = item.icon
                return (
                  <div
                    key={item.title}
                    className="flex flex-col items-center gap-3 rounded-2xl border border-gold/20 bg-warm-white p-8 text-center"
                  >
                    <div className="flex size-14 items-center justify-center rounded-full bg-navy/5 text-navy">
                      <Icon className="size-7" aria-hidden="true" />
                    </div>
                    <h3 className="font-serif text-xl font-semibold text-navy">{item.title}</h3>
                    <p className="text-base leading-relaxed text-charcoal/80">
                      {item.description}
                    </p>
                  </div>
                )
              })}
            </div>
          </div>
        </section>

        <section aria-labelledby="rooms-heading" className="bg-warm-white py-16 md:py-24">
          <div className="mx-auto max-w-[1280px] px-4 md:px-8">
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
          </div>
        </section>

        <section className="relative overflow-hidden bg-navy py-16 md:py-24">
          <div className="mx-auto grid max-w-[1280px] gap-10 px-4 md:grid-cols-2 md:items-center md:px-8">
            <div>
              <p className="text-sm font-semibold tracking-[0.15em] text-gold uppercase">
                {language === 'pl' ? 'Otoczenie' : 'Natural Sanctuary'}
              </p>
              <h2 className="mt-3 font-serif text-3xl font-bold text-white md:text-4xl">
                {language === 'pl' ? 'Las bukowy tuż za oknem' : 'Beech Forest Right Outside Your Window'}
              </h2>
              <p className="mt-4 text-lg leading-relaxed text-white/85">
                {language === 'pl'
                  ? 'Spacerowe alejki, świeże górskie powietrze i cisza — naturalne otoczenie Bukowego Dworu wspiera regenerację ciała i umysłu równie skutecznie, jak zabiegi w naszym SPA.'
                  : 'Serene walking trails, fresh alpine air, and tranquil silence — Bukowy Dwór’s mountain surroundings rejuvenate body and spirit alongside our thermal spa treatments.'}
              </p>
              <HotelButton href="/dojazd" variant="secondary" className="mt-8 border-gold text-white hover:bg-gold hover:text-navy">
                {language === 'pl' ? 'Sprawdź dojazd i dostępność' : 'Check Directions & Shuttle'}
              </HotelButton>
            </div>
            <div className="relative aspect-[4/3] w-full overflow-hidden rounded-2xl">
              <Image
                src="/images/nature-path.png"
                alt="Ścieżka w lesie bukowym w okolicy Bukowego Dworu"
                fill
                className="object-cover"
              />
            </div>
          </div>
        </section>

        <AccessibilitySection />
      </main>
      <SiteFooter />
    </>
  )
}

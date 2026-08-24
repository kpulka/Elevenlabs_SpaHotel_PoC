'use client'

import { Bus, Car, TrainFront } from 'lucide-react'
import Image from 'next/image'

import { AccessibilitySection } from '@/components/accessibility-section'
import { HotelButton } from '@/components/hotel-button'
import { SiteFooter } from '@/components/site-footer'
import { SiteHeader } from '@/components/site-header'
import { useLanguage } from '@/context/language-context'
import { contactInfo } from '@/lib/hotel-data'

export default function DirectionsPage() {
  const { language, t } = useLanguage()

  const travelOptions = [
    {
      icon: Car,
      title: t.accessPage.carTitle,
      description:
        language === 'pl'
          ? 'Z Krakowa ok. 2 godziny (A4, następnie DK75 i DK98). Bezpłatny, oświetlony parking bezpośrednio przy wejściu głównym z miejscami dla osób z niepełnosprawnościami.'
          : 'Approx. 2 hours from Kraków (A4 highway, then DK75/DK98). Free, well-lit parking immediately next to main entrance with accessible spots.',
    },
    {
      icon: TrainFront,
      title: t.accessPage.trainTitle,
      description:
        language === 'pl'
          ? 'Stacja PKP Krynica-Zdrój znajduje się 5 minut jazdy od ośrodka. Zapewniamy bezpłatny odbiór naszym busem przystosowanym do przewozu wózków.'
          : 'Krynica-Zdrój train station is 5 minutes from the resort. We provide free scheduled pickup in our wheelchair-accessible electric resort bus.',
    },
    {
      icon: Bus,
      title: language === 'pl' ? 'Autobusem (PKS)' : 'By Regional Bus',
      description:
        language === 'pl'
          ? 'Regularne połączenia z Nowego Sącza i Krakowa. Przystanek "Krynica-Zdrój Centrum" jest 10 minut pieszo od ośrodka.'
          : 'Regular direct coaches from Kraków and Nowy Sącz. Central bus stop is 10 minutes away, or request our free shuttle.',
    },
  ]

  return (
    <>
      <SiteHeader />
      <main id="main-content">
        <section className="relative flex min-h-[380px] items-center overflow-hidden">
          <Image
            src="/images/entrance.png"
            alt="Wejście do Bukowego Dworu"
            fill
            priority
            className="object-cover"
          />
          <div className="absolute inset-0 bg-navy/60" />
          <div className="relative z-10 mx-auto max-w-[1280px] px-4 md:px-8">
            <p className="text-sm font-semibold tracking-[0.2em] text-gold uppercase">
              {t.accessPage.tag}
            </p>
            <h1 className="mt-3 max-w-2xl text-balance font-serif text-4xl font-bold text-white md:text-5xl">
              {t.accessPage.title}
            </h1>
            <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/90">
              {contactInfo.address}
            </p>
          </div>
        </section>

        <section className="bg-warm-white py-16 md:py-24">
          <div className="mx-auto max-w-[1280px] px-4 md:px-8">
            <div className="grid gap-10 lg:grid-cols-2 lg:items-start">
              <div>
                <h2 className="font-serif text-3xl font-bold text-navy">
                  {language === 'pl' ? 'Jak do nas dojechać' : 'Directions & Transport Options'}
                </h2>
                <div className="mt-8 flex flex-col gap-6">
                  {travelOptions.map((option) => {
                    const Icon = option.icon
                    return (
                      <div key={option.title} className="flex gap-4">
                        <div className="flex size-12 shrink-0 items-center justify-center rounded-full bg-navy/5 text-navy">
                          <Icon className="size-6" aria-hidden="true" />
                        </div>
                        <div>
                          <h3 className="font-serif text-lg font-semibold text-navy">
                            {option.title}
                          </h3>
                          <p className="mt-1 text-base leading-relaxed text-charcoal/80">
                            {option.description}
                          </p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
              <div className="overflow-hidden rounded-2xl border border-gold/20 shadow-md">
                <iframe
                  title="Mapa — lokalizacja Bukowego Dworu w Krynicy-Zdroju"
                  src="https://www.openstreetmap.org/export/embed.html?bbox=20.94%2C49.40%2C20.98%2C49.42&layer=mapnik"
                  className="h-[360px] w-full"
                  loading="lazy"
                />
              </div>
            </div>
          </div>
        </section>

        <AccessibilitySection />

        <section className="bg-navy py-16 text-center md:py-20">
          <div className="mx-auto max-w-2xl px-4 md:px-8">
            <h2 className="font-serif text-3xl font-bold text-white">
              {language === 'pl'
                ? 'Potrzebujesz dodatkowej pomocy w dostaniu się do ośrodka?'
                : 'Need Assistance With Transportation & Arrival?'}
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-white/85">
              {language === 'pl'
                ? 'Zadzwoń do recepcji lub poinformuj Annę — zorganizujemy bezpłatny transfer meleksem i wsparcie z bagażem.'
                : 'Call front desk or ask Anna — we will organize your free electric shuttle pickup and luggage assistance.'}
            </p>
            <div className="mt-8 flex justify-center">
              <HotelButton href={contactInfo.phoneHref} variant="primary" className="bg-gold text-navy hover:bg-gold/90">
                {language === 'pl' ? `Zadzwoń: ${contactInfo.phone}` : `Call Front Desk: ${contactInfo.phone}`}
              </HotelButton>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  )
}

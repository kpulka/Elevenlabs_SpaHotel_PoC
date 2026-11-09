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
  const { t } = useLanguage()

  const travelOptions = [
    {
      icon: Car,
      title: t.accessPage.carTitle,
      description: t.accessPage.carDesc,
    },
    {
      icon: TrainFront,
      title: t.accessPage.trainTitle,
      description: t.accessPage.trainDesc,
    },
    {
      icon: Bus,
      title: t.accessPage.busTitle,
      description: t.accessPage.busDesc,
    },
  ]

  return (
    <>
      <SiteHeader />
      <main id="main-content">
        <section className="relative flex min-h-[380px] items-center overflow-hidden">
          <Image
            src="/images/entrance.png"
            alt={t.images.accessHeroAlt}
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
                  {t.accessPage.directionsHeading}
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
                  title={t.images.mapTitle}
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
              {t.accessPage.helpTitle}
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-white/85">
              {t.accessPage.helpText}
            </p>
            <div className="mt-8 flex justify-center">
              <HotelButton href={contactInfo.phoneHref} variant="primary" className="bg-gold text-navy hover:bg-gold/90">
                {t.accessPage.callPrefix} {contactInfo.phone}
              </HotelButton>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  )
}

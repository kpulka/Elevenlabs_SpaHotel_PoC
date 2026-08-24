import { Clock, Mail, MapPin, Phone } from 'lucide-react'
import type { Metadata } from 'next'
import Image from 'next/image'

import { ContactForm } from '@/components/contact-form'
import { SiteFooter } from '@/components/site-footer'
import { SiteHeader } from '@/components/site-header'
import { contactInfo } from '@/lib/hotel-data'

export const metadata: Metadata = {
  title: 'Kontakt — Bukowy Dwór',
  description:
    'Skontaktuj się z Bukowym Dworem w Krynicy-Zdroju — zarezerwuj pobyt, zapytaj o pokoje lub zabiegi SPA. Recepcja dostępna całodobowo.',
}

export default function ContactPage() {
  return (
    <>
      <SiteHeader />
      <main id="main-content">
        <section className="relative flex min-h-[420px] items-center overflow-hidden">
          <Image
            src="/images/hero-contact.png"
            alt="Elegancka i przyjazna recepcja Bukowego Dworu"
            fill
            priority
            className="object-cover"
          />
          <div className="absolute inset-0 bg-navy/60" />
          <div className="relative z-10 mx-auto max-w-[1280px] px-4 md:px-8">
            <p className="text-sm font-semibold tracking-[0.2em] text-gold uppercase">Kontakt</p>
            <h1 className="mt-3 max-w-2xl text-balance font-serif text-4xl font-bold text-white md:text-5xl">
              Jesteśmy do Twojej dyspozycji
            </h1>
            <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/90">
              Zadzwoń, napisz lub wypełnij formularz — odpowiemy tak szybko, jak to możliwe.
            </p>
          </div>
        </section>

        <section className="bg-warm-white py-16 md:py-24">
          <div className="mx-auto grid max-w-[1280px] gap-12 px-4 md:px-8 lg:grid-cols-[1fr_1.2fr]">
            <div className="flex flex-col gap-6">
              <div className="rounded-2xl border border-gold/20 bg-cream p-6">
                <div className="flex items-center gap-3">
                  <Phone className="size-6 text-sage" aria-hidden="true" />
                  <h2 className="font-serif text-lg font-semibold text-navy">Telefon</h2>
                </div>
                <a
                  href={contactInfo.phoneHref}
                  className="mt-3 inline-block text-2xl font-bold text-navy outline-none hover:text-sage focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
                >
                  {contactInfo.phone}
                </a>
                <p className="mt-1 text-sm text-muted-grey">{contactInfo.receptionHours}</p>
              </div>

              <div className="rounded-2xl border border-gold/20 bg-cream p-6">
                <div className="flex items-center gap-3">
                  <Mail className="size-6 text-sage" aria-hidden="true" />
                  <h2 className="font-serif text-lg font-semibold text-navy">E-mail</h2>
                </div>
                <a
                  href={`mailto:${contactInfo.email}`}
                  className="mt-3 inline-block text-lg font-semibold text-navy outline-none hover:text-sage focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
                >
                  {contactInfo.email}
                </a>
              </div>

              <div className="rounded-2xl border border-gold/20 bg-cream p-6">
                <div className="flex items-center gap-3">
                  <MapPin className="size-6 text-sage" aria-hidden="true" />
                  <h2 className="font-serif text-lg font-semibold text-navy">Adres</h2>
                </div>
                <p className="mt-3 text-lg leading-relaxed text-charcoal/85">
                  {contactInfo.address}
                </p>
              </div>

              <div className="rounded-2xl border border-gold/20 bg-cream p-6">
                <div className="flex items-center gap-3">
                  <Clock className="size-6 text-sage" aria-hidden="true" />
                  <h2 className="font-serif text-lg font-semibold text-navy">Recepcja</h2>
                </div>
                <p className="mt-3 text-lg leading-relaxed text-charcoal/85">Całodobowo, 24/7</p>
              </div>
            </div>

            <div className="rounded-2xl border border-gold/20 bg-cream p-6 md:p-10">
              <h2 className="font-serif text-2xl font-bold text-navy">Wyślij zapytanie</h2>
              <p className="mt-2 text-base leading-relaxed text-charcoal/80">
                Wypełnij formularz — skontaktujemy się z Tobą w ciągu 24 godzin.
              </p>
              <ContactForm />
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  )
}

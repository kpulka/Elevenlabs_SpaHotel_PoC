'use client'

import { Clock, Mail, MapPin, Phone } from 'lucide-react'
import Image from 'next/image'

import { ContactForm } from '@/components/contact-form'
import { SiteFooter } from '@/components/site-footer'
import { SiteHeader } from '@/components/site-header'
import { useLanguage } from '@/context/language-context'
import { contactInfo } from '@/lib/hotel-data'

export default function ContactPage() {
  const { t } = useLanguage()

  return (
    <>
      <SiteHeader />
      <main id="main-content">
        <section className="relative flex min-h-[420px] items-center overflow-hidden">
          <Image
            src="/images/hero-contact.png"
            alt={t.images.contactHeroAlt}
            fill
            priority
            className="object-cover"
          />
          <div className="absolute inset-0 bg-navy/60" />
          <div className="relative z-10 mx-auto max-w-[1280px] px-4 md:px-8">
            <p className="text-sm font-semibold tracking-[0.2em] text-gold uppercase">
              {t.nav.contact}
            </p>
            <h1 className="mt-3 max-w-2xl text-balance font-serif text-4xl font-bold text-white md:text-5xl">
              {t.contactPage.title}
            </h1>
            <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/90">
              {t.contactPage.subtitle}
            </p>
          </div>
        </section>

        <section className="bg-warm-white py-16 md:py-24">
          <div className="mx-auto grid max-w-[1280px] gap-12 px-4 md:px-8 lg:grid-cols-[1fr_1.2fr]">
            <div className="flex flex-col gap-6">
              <div className="rounded-2xl border border-gold/20 bg-cream p-6">
                <div className="flex items-center gap-3">
                  <Phone className="size-6 text-sage" aria-hidden="true" />
                  <h2 className="font-serif text-lg font-semibold text-navy">
                    {t.contactPage.phoneCardTitle}
                  </h2>
                </div>
                <a
                  href={contactInfo.phoneHref}
                  className="mt-3 inline-block text-2xl font-bold text-navy outline-none hover:text-sage focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
                >
                  {contactInfo.phone}
                </a>
                <p className="mt-1 text-sm text-muted-grey">{t.footer.receptionHours}</p>
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
                  <h2 className="font-serif text-lg font-semibold text-navy">
                    {t.contactPage.addressCardTitle}
                  </h2>
                </div>
                <p className="mt-3 text-lg leading-relaxed text-charcoal/85">
                  {contactInfo.address}
                </p>
              </div>

              <div className="rounded-2xl border border-gold/20 bg-cream p-6">
                <div className="flex items-center gap-3">
                  <Clock className="size-6 text-sage" aria-hidden="true" />
                  <h2 className="font-serif text-lg font-semibold text-navy">
                    {t.contactPage.availabilityCardTitle}
                  </h2>
                </div>
                <p className="mt-3 text-lg leading-relaxed text-charcoal/85">
                  {t.contactPage.availabilityValue}
                </p>
              </div>
            </div>

            <div className="rounded-2xl border border-gold/20 bg-cream p-6 md:p-10">
              <h2 className="font-serif text-2xl font-bold text-navy">{t.contactPage.formTitle}</h2>
              <p className="mt-2 text-base leading-relaxed text-charcoal/80">
                {t.contactPage.formHint}
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

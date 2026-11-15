'use client'

import { Clock, Mail, MapPin, Phone } from 'lucide-react'

import { ContactCard } from '@/components/contact-card'
import { ContactForm } from '@/components/contact-form'
import { PageHero } from '@/components/page-hero'
import { Section } from '@/components/section'
import { SiteFooter } from '@/components/site-footer'
import { SiteHeader } from '@/components/site-header'
import { useLanguage } from '@/context/language-context'
import { contactInfo } from '@/lib/hotel'

export default function ContactPage() {
  const { t } = useLanguage()

  return (
    <>
      <SiteHeader />
      <main id="main-content">
        <PageHero
          image="/images/hero-contact.webp"
          alt={t.images.contactHeroAlt}
          tag={t.nav.contact}
          title={t.contactPage.title}
          subtitle={t.contactPage.subtitle}
        />

        <Section tone="warm-white" containerClassName="grid gap-12 lg:grid-cols-[1fr_1.2fr]">
          <div className="flex flex-col gap-6">
            <ContactCard icon={Phone} title={t.contactPage.phoneCardTitle}>
              <a
                href={contactInfo.phoneHref}
                className="mt-3 inline-block text-2xl font-bold text-navy outline-none hover:text-sage focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
              >
                {contactInfo.phone}
              </a>
              <p className="mt-1 text-sm text-muted-grey">{t.footer.receptionHours}</p>
            </ContactCard>

            <ContactCard icon={Mail} title="E-mail">
              <a
                href={`mailto:${contactInfo.email}`}
                className="mt-3 inline-block text-lg font-semibold text-navy outline-none hover:text-sage focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
              >
                {contactInfo.email}
              </a>
            </ContactCard>

            <ContactCard icon={MapPin} title={t.contactPage.addressCardTitle}>
              <p className="mt-3 text-lg leading-relaxed text-charcoal/85">
                {contactInfo.address}
              </p>
            </ContactCard>

            <ContactCard icon={Clock} title={t.contactPage.availabilityCardTitle}>
              <p className="mt-3 text-lg leading-relaxed text-charcoal/85">
                {t.contactPage.availabilityValue}
              </p>
            </ContactCard>
          </div>

          <div className="rounded-2xl border border-gold/20 bg-cream p-6 md:p-10">
            <h2 className="font-serif text-2xl font-bold text-navy">{t.contactPage.formTitle}</h2>
            <p className="mt-2 text-base leading-relaxed text-charcoal/80">
              {t.contactPage.formHint}
            </p>
            <ContactForm />
          </div>
        </Section>
      </main>
      <SiteFooter />
    </>
  )
}

'use client'

import { Mail, MapPin, Phone } from 'lucide-react'

import { PageHero } from '@/components/page-hero'
import { Section } from '@/components/section'
import { SiteFooter } from '@/components/site-footer'
import { SiteHeader } from '@/components/site-header'
import { useLanguage } from '@/context/language-context'
import { contactInfo } from '@/lib/hotel'

type PolicyBlock = { title: string; body: readonly string[]; items?: readonly string[] }

export default function PrivacyPolicyPage() {
  const { t } = useLanguage()
  const p = t.privacyPage

  // The section id doubles as the anchor (e.g. /polityka#rights from the footer).
  const sections: { id: string; block: PolicyBlock }[] = [
    { id: 'controller', block: p.controller },
    { id: 'voice', block: p.voice },
    { id: 'microphone', block: p.microphone },
    { id: 'purposes', block: p.purposes },
    { id: 'recordings', block: p.recordings },
    { id: 'retention', block: p.retention },
    { id: 'analytics', block: p.analytics },
    { id: 'cookies', block: p.cookies },
    { id: 'rights', block: p.rights },
    { id: 'contact', block: p.contact },
  ]

  return (
    <>
      <SiteHeader />
      <main id="main-content">
        <PageHero
          image="/images/hero-contact.webp"
          alt={t.images.contactHeroAlt}
          tag={p.tag}
          title={p.title}
          subtitle={p.subtitle}
        />

        <Section tone="warm-white">
          <div className="mx-auto max-w-3xl">
            <p role="note" className="rounded-xl border border-gold/50 bg-gold/10 p-4 text-sm leading-relaxed text-charcoal">
              {p.demoNotice}
            </p>

            {sections.map(({ id, block }) => (
              <section key={id} id={id} aria-labelledby={`${id}-heading`} className="mt-12 scroll-mt-24">
                <h2 id={`${id}-heading`} className="font-serif text-2xl font-bold text-navy">
                  {block.title}
                </h2>
                {block.body.map((paragraph) => (
                  <p key={paragraph} className="mt-4 text-base leading-relaxed text-charcoal/85">
                    {paragraph}
                  </p>
                ))}
                {block.items && (
                  <ul className="mt-4 list-disc space-y-2 pl-6 text-base leading-relaxed text-charcoal/85">
                    {block.items.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                )}
                {id === 'contact' && (
                  <ul className="mt-6 flex flex-col gap-3 text-base text-charcoal/85">
                    <li className="flex items-start gap-3">
                      <MapPin className="mt-1 size-5 shrink-0 text-sage" aria-hidden="true" />
                      <span>{contactInfo.address}</span>
                    </li>
                    <li className="flex items-center gap-3">
                      <Phone className="size-5 shrink-0 text-sage" aria-hidden="true" />
                      <a href={contactInfo.phoneHref} className="font-semibold text-navy underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold">
                        {contactInfo.phone}
                      </a>
                    </li>
                    <li className="flex items-center gap-3">
                      <Mail className="size-5 shrink-0 text-sage" aria-hidden="true" />
                      <a href={`mailto:${contactInfo.email}`} className="font-semibold text-navy underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold">
                        {contactInfo.email}
                      </a>
                    </li>
                  </ul>
                )}
              </section>
            ))}
          </div>
        </Section>
      </main>
      <SiteFooter />
    </>
  )
}

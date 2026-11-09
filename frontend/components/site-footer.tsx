'use client'

import { Globe, Mail, MapPin, Phone, Share2 } from 'lucide-react'
import Link from 'next/link'

import { useLanguage } from '@/context/language-context'
import { contactInfo } from '@/lib/hotel-data'

export function SiteFooter() {
  const { t } = useLanguage()

  const quickLinks = [
    { label: t.nav.rooms, href: '/pokoje' },
    { label: t.nav.spa, href: '/spa' },
    { label: t.nav.restaurant, href: '/restauracja' },
    { label: t.nav.access, href: '/dojazd' },
    { label: t.nav.contact, href: '/kontakt' },
  ]

  return (
    <footer className="bg-navy text-white">
      <div className="mx-auto grid max-w-[1280px] gap-10 px-4 py-16 md:grid-cols-2 md:px-8 lg:grid-cols-4">
        <div>
          <span className="font-serif text-2xl font-bold">Bukowy Dwór</span>
          <p className="mt-4 max-w-xs text-base leading-relaxed text-white/80">
            {t.footer.tagline}
          </p>
          <div className="mt-6 flex gap-3">
            <a
              href="#"
              aria-label="Bukowy Dwór Facebook"
              className="flex size-12 items-center justify-center rounded-full border border-white/20 outline-none transition-colors hover:border-gold hover:text-gold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
            >
              <Globe className="size-5" aria-hidden="true" />
            </a>
            <a
              href="#"
              aria-label="Bukowy Dwór Instagram"
              className="flex size-12 items-center justify-center rounded-full border border-white/20 outline-none transition-colors hover:border-gold hover:text-gold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
            >
              <Share2 className="size-5" aria-hidden="true" />
            </a>
          </div>
        </div>

        <div>
          <h2 className="font-serif text-lg font-semibold">{t.footer.sections}</h2>
          <ul className="mt-4 flex flex-col gap-3">
            {quickLinks.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className="text-base text-white/80 outline-none transition-colors hover:text-gold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h2 className="font-serif text-lg font-semibold">{t.footer.contactTitle}</h2>
          <ul className="mt-4 flex flex-col gap-4 text-base text-white/80">
            <li className="flex items-start gap-3">
              <MapPin className="mt-1 size-5 shrink-0 text-gold" aria-hidden="true" />
              <span>{contactInfo.address}</span>
            </li>
            <li className="flex items-center gap-3">
              <Phone className="size-5 shrink-0 text-gold" aria-hidden="true" />
              <a
                href={contactInfo.phoneHref}
                className="text-lg font-semibold text-white underline-offset-4 outline-none hover:text-gold hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
              >
                {contactInfo.phone}
              </a>
            </li>
            <li className="flex items-center gap-3">
              <Mail className="size-5 shrink-0 text-gold" aria-hidden="true" />
              <a
                href={`mailto:${contactInfo.email}`}
                className="outline-none hover:text-gold hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
              >
                {contactInfo.email}
              </a>
            </li>
            <li>{t.footer.receptionHours}</li>
          </ul>
        </div>

        <div>
          <h2 className="font-serif text-lg font-semibold">{t.footer.hoursTitle}</h2>
          <ul className="mt-4 flex flex-col gap-2 text-base text-white/80">
            <li>{t.footer.poolsHours}</li>
            <li>{t.footer.treatmentHours}</li>
            <li>{t.footer.mealsHours}</li>
          </ul>
          <div className="mt-4 rounded-lg border border-gold/30 bg-gold/10 p-3 text-xs text-gold">
            {t.footer.annaBadge}
          </div>
        </div>
      </div>

      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-[1280px] flex-col gap-2 px-4 py-6 text-sm text-white/60 md:flex-row md:items-center md:justify-between md:px-8">
          <p>&copy; 2026 Bukowy Dwór. {t.footer.rights}</p>
          <div className="flex gap-4">
            <Link href="#" className="outline-none hover:text-gold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold">
              {t.footer.privacyPolicy}
            </Link>
            <Link href="#" className="outline-none hover:text-gold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold">
              GDPR / RODO
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}

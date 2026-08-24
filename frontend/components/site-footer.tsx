import { Globe, Mail, MapPin, Phone, Share2 } from 'lucide-react'
import Link from 'next/link'

import { contactInfo } from '@/lib/hotel-data'

const quickLinks = [
  { label: 'Pokoje', href: '/pokoje' },
  { label: 'SPA & Zabiegi', href: '/spa' },
  { label: 'Restauracja', href: '/restauracja' },
  { label: 'Dojazd & Dostępność', href: '/dojazd' },
  { label: 'Kontakt', href: '/kontakt' },
]

export function SiteFooter() {
  return (
    <footer className="bg-navy text-white">
      <div className="mx-auto grid max-w-[1280px] gap-10 px-4 py-16 md:grid-cols-2 md:px-8 lg:grid-cols-4">
        <div>
          <span className="font-serif text-2xl font-bold">Bukowy Dwór</span>
          <p className="mt-4 max-w-xs text-base leading-relaxed text-white/80">
            Uzdrowisko termalne w Krynicy-Zdroju. Miejsce, gdzie ciało wraca do równowagi.
          </p>
          <div className="mt-6 flex gap-3">
            <a
              href="#"
              aria-label="Bukowy Dwór na Facebooku"
              className="flex size-12 items-center justify-center rounded-full border border-white/20 outline-none transition-colors hover:border-gold hover:text-gold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
            >
              <Globe className="size-5" aria-hidden="true" />
            </a>
            <a
              href="#"
              aria-label="Bukowy Dwór na Instagramie"
              className="flex size-12 items-center justify-center rounded-full border border-white/20 outline-none transition-colors hover:border-gold hover:text-gold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
            >
              <Share2 className="size-5" aria-hidden="true" />
            </a>
          </div>
        </div>

        <div>
          <h2 className="font-serif text-lg font-semibold">Szybkie linki</h2>
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
          <h2 className="font-serif text-lg font-semibold">Kontakt</h2>
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
            <li>{contactInfo.receptionHours}</li>
          </ul>
        </div>

        <div>
          <h2 className="font-serif text-lg font-semibold">Dojazd</h2>
          <p className="mt-4 text-base text-white/80">
            ul. Zdrojowa 15, 33-380 Krynica-Zdrój — 5 minut od centrum, bezpłatny parking dla gości.
          </p>
          <Link
            href="/dojazd"
            className="mt-4 inline-flex min-h-[44px] items-center rounded-md border border-white/20 px-4 text-sm text-white/90 outline-none transition-colors hover:border-gold hover:text-gold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
          >
            Zobacz mapę i wskazówki
          </Link>
        </div>
      </div>

      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-[1280px] flex-col gap-2 px-4 py-6 text-sm text-white/60 md:flex-row md:items-center md:justify-between md:px-8">
          <p>&copy; 2026 Bukowy Dwór</p>
          <div className="flex gap-4">
            <Link href="#" className="outline-none hover:text-gold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold">
              Polityka prywatności
            </Link>
            <Link href="#" className="outline-none hover:text-gold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold">
              RODO
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}

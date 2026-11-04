'use client'

import { Menu, Phone, X } from 'lucide-react'
import Link from 'next/link'
import { useState } from 'react'

import { HotelButton } from '@/components/hotel-button'
import { LanguageSwitcher } from '@/components/language-switcher'
import { useLanguage } from '@/context/language-context'
import { contactInfo } from '@/lib/hotel-data'

export function SiteHeader() {
  const [open, setOpen] = useState(false)
  const { t } = useLanguage()

  const navItems = [
    { label: t.nav.rooms, href: '/rooms' },
    { label: t.nav.spa, href: '/spa' },
    { label: t.nav.restaurant, href: '/restaurant' },
    { label: t.nav.access, href: '/directions' },
    { label: t.nav.contact, href: '/contact' },
  ]

  return (
    <header className="sticky top-0 z-50 bg-navy">
      <div className="mx-auto flex max-w-[1280px] items-center justify-between gap-4 px-4 py-3 md:px-8">
        <Link href="/" className="flex items-center gap-2" onClick={() => setOpen(false)}>
          <span className="font-serif text-2xl font-bold tracking-wide text-white">
            Bukowy Dwór
          </span>
        </Link>

        <nav aria-label={t.nav.mainNav} className="hidden items-center gap-6 lg:flex">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-base tracking-wide text-white/90 outline-none transition-colors hover:text-gold focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-gold"
              style={{ letterSpacing: '0.03em' }}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-3 lg:flex">
          <LanguageSwitcher />

          <a
            href={contactInfo.phoneHref}
            className="flex items-center gap-2 text-sm text-white/90 outline-none transition-colors hover:text-gold focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-gold"
          >
            <Phone className="size-4" aria-hidden="true" />
            {contactInfo.phone}
          </a>
          <HotelButton href="/contact" variant="secondary" className="border-gold text-white hover:bg-gold hover:text-navy">
            {t.nav.bookStay}
          </HotelButton>
        </div>

        <div className="flex items-center gap-2 lg:hidden">
          <LanguageSwitcher />

          <a
            href={contactInfo.phoneHref}
            aria-label={`${t.nav.callReception} ${contactInfo.phone}`}
            className="flex size-10 items-center justify-center rounded-full text-white outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
          >
            <Phone className="size-5" aria-hidden="true" />
          </a>
          <button
            type="button"
            aria-expanded={open}
            aria-controls="mobile-menu"
            aria-label={open ? t.nav.closeMenu : t.nav.openMenu}
            onClick={() => setOpen((v) => !v)}
            className="flex size-10 items-center justify-center rounded-full text-white outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
          >
            {open ? <X className="size-6" aria-hidden="true" /> : <Menu className="size-6" aria-hidden="true" />}
          </button>
        </div>
      </div>

      {open && (
        <div
          id="mobile-menu"
          className="fixed inset-x-0 top-[64px] bottom-0 z-40 flex flex-col bg-navy px-6 py-8 lg:hidden"
        >
          <nav aria-label={t.nav.mobileNav} className="flex flex-col gap-2">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className="flex min-h-[52px] items-center rounded-lg px-3 text-lg text-white outline-none transition-colors hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="mt-8">
            <HotelButton href="/contact" variant="secondary" fullWidth className="border-gold text-white hover:bg-gold hover:text-navy" onClick={() => setOpen(false)}>
              {t.nav.bookStay}
            </HotelButton>
          </div>
        </div>
      )}
    </header>
  )
}

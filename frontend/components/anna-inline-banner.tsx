'use client'

import { Mic } from 'lucide-react'

export function AnnaInlineBanner() {
  return (
    <aside
      aria-label="Pomoc głosowa w rezerwacji"
      className="border-y border-gold/30 bg-warm-white py-6"
    >
      <div className="mx-auto flex max-w-[1280px] flex-col items-center justify-between gap-4 px-4 sm:flex-row md:px-8">
        <div className="flex items-center gap-4 text-center sm:text-left">
          <span className="flex size-12 shrink-0 items-center justify-center rounded-full bg-gold/20 text-navy">
            <Mic className="size-6 text-gold" aria-hidden="true" />
          </span>
          <div>
            <p className="font-serif text-lg font-bold text-navy">
              Wolisz zapytać głosowo o zabiegi lub wolne terminy?
            </p>
            <p className="text-sm text-charcoal/80">
              Anna, nasza recepcjonistka, pomoże dobrać zabieg i sprawdzić dostępność.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => window.dispatchEvent(new CustomEvent('open-anna-widget'))}
          className="inline-flex min-h-[48px] shrink-0 items-center gap-2 rounded-full bg-navy px-6 text-sm font-semibold text-white outline-none transition-transform hover:scale-105 hover:bg-navy/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
        >
          <Mic className="size-4 text-gold" aria-hidden="true" />
          Porozmawiaj z Anną
        </button>
      </div>
    </aside>
  )
}

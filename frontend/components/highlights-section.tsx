'use client'

import { Flower2, UtensilsCrossed, Waves } from 'lucide-react'

import { useLanguage } from '@/context/language-context'

export function HighlightsSection() {
  const { t } = useLanguage()

  const highlights = [
    {
      icon: Waves,
      title: t.home.highlightPoolsTitle,
      description: t.home.highlightPoolsDesc,
    },
    {
      icon: Flower2,
      title: t.home.highlightBalneoTitle,
      description: t.home.highlightBalneoDesc,
    },
    {
      icon: UtensilsCrossed,
      title: t.home.highlightDiningTitle,
      description: t.home.highlightDiningDesc,
    },
  ]

  return (
    <section aria-labelledby="highlights-heading" className="bg-cream py-16 md:py-24">
      <div className="mx-auto max-w-[1280px] px-4 md:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 id="highlights-heading" className="font-serif text-3xl font-bold text-navy md:text-4xl">
            {t.home.featuresTitle}
          </h2>
        </div>
        <div className="mt-12 grid gap-6 sm:grid-cols-3">
          {highlights.map((item) => {
            const Icon = item.icon
            return (
              <div
                key={item.title}
                className="flex flex-col items-center gap-3 rounded-2xl border border-gold/20 bg-warm-white p-8 text-center"
              >
                <div className="flex size-14 items-center justify-center rounded-full bg-navy/5 text-navy">
                  <Icon className="size-7" aria-hidden="true" />
                </div>
                <h3 className="font-serif text-xl font-semibold text-navy">{item.title}</h3>
                <p className="text-base leading-relaxed text-charcoal/80">
                  {item.description}
                </p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

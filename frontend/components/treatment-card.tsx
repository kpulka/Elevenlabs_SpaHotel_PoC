'use client'

import Image from 'next/image'

import { useLanguage } from '@/context/language-context'
import type { Treatment } from '@/lib/hotel-data'

export function TreatmentCard({ treatment }: { treatment: Treatment }) {
  const { t } = useLanguage()

  return (
    <article className="flex flex-col overflow-hidden rounded-2xl border border-gold/20 bg-warm-white transition-transform hover:-translate-y-1 hover:shadow-lg">
      {treatment.image && (
        <div className="relative aspect-[16/10] w-full overflow-hidden bg-cream">
          <Image
            src={treatment.image}
            alt={treatment.name}
            fill
            className="object-cover transition-transform duration-300 hover:scale-105"
          />
        </div>
      )}
      <div className="flex flex-1 flex-col gap-3 p-6">
        <div className="flex items-start justify-between gap-4">
          <h3 className="font-serif text-xl font-semibold text-navy">{treatment.name}</h3>
          {/* Cena pochodzi z mock_backend/data/spa_schedule.json (pricePln) — nigdy z literału w JSX. */}
          <p className="shrink-0 font-serif text-xl font-bold text-navy">
            {treatment.includedInStay
              ? t.spaPage.priceIncluded
              : `${treatment.price} ${t.spaPage.currencyZloty}`}
          </p>
        </div>
        <p className="text-sm font-medium text-sage">{treatment.duration}</p>
        <p className="text-base leading-relaxed text-charcoal/80">{treatment.description}</p>
        {treatment.includedInStay && (
          <p className="text-sm font-medium text-sage">{t.spaPage.noBookingNote}</p>
        )}
      </div>
    </article>
  )
}

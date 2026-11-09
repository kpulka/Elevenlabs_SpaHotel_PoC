'use client'

import { Bath, Bus, Car, DoorOpen, Hand, MoveVertical } from 'lucide-react'

import { useLanguage } from '@/context/language-context'
import { getAccessibilityFeatures } from '@/lib/hotel-data'

const icons = {
  'door-open': DoorOpen,
  'move-vertical': MoveVertical,
  car: Car,
  hand: Hand,
  bath: Bath,
  bus: Bus,
}

export function AccessibilitySection() {
  const { language, t } = useLanguage()
  const features = getAccessibilityFeatures(language)

  return (
    <section aria-labelledby="accessibility-heading" className="bg-warm-white py-16 md:py-24">
      <div className="mx-auto max-w-[1280px] px-4 md:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold tracking-[0.15em] text-sage uppercase">
            {t.accessibilitySection.eyebrow}
          </p>
          <h2 id="accessibility-heading" className="mt-3 font-serif text-3xl font-bold text-navy md:text-4xl">
            {t.accessibilitySection.title}
          </h2>
          <p className="mt-4 text-lg leading-relaxed text-charcoal/80">
            {t.accessibilitySection.text}
          </p>
        </div>

        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => {
            const Icon = icons[feature.icon]
            return (
              <div
                key={feature.title}
                className="flex flex-col gap-3 rounded-2xl border border-gold/20 bg-cream p-6"
              >
                <div className="flex size-12 items-center justify-center rounded-full bg-sage/15 text-sage">
                  <Icon className="size-6" aria-hidden="true" />
                </div>
                <h3 className="font-serif text-lg font-semibold text-navy">{feature.title}</h3>
                <p className="text-base leading-relaxed text-charcoal/80">{feature.description}</p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

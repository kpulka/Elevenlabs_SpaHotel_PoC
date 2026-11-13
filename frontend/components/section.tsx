import type { ComponentProps } from 'react'

import { cn } from '@/lib/utils'

/**
 * Jedyne miejsce, w którym żyje szerokość treści strony (max 1280px + gutter 16/32px).
 * Zmiana szerokości lub paddingu wymaga edycji tylko tutaj.
 */
export function Container({ className, ...props }: ComponentProps<'div'>) {
  return <div className={cn('mx-auto max-w-[1280px] px-4 md:px-8', className)} {...props} />
}

const toneClass = {
  cream: 'bg-cream',
  'warm-white': 'bg-warm-white',
  navy: 'bg-navy',
} as const

export type SectionTone = keyof typeof toneClass

interface SectionProps extends ComponentProps<'section'> {
  tone: SectionTone
  /** Dodatkowe klasy wewnętrznego kontenera (np. grid), bez szerokości. */
  containerClassName?: string
}

/** Sekcja pełnej szerokości: tło wg tonu, wspólny pionowy odstęp i kontener `Container`. */
export function Section({ tone, className, containerClassName, children, ...props }: SectionProps) {
  return (
    <section {...props} className={cn(toneClass[tone], 'py-16 md:py-24', className)}>
      <Container className={containerClassName}>{children}</Container>
    </section>
  )
}

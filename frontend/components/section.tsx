import type { ComponentProps } from 'react'

import { cn } from '@/lib/utils'

/**
 * The single place that defines the page content width (max 1280px + 16/32px gutter).
 * Changing the width or padding only requires an edit here.
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
  /** Extra classes for the inner container (e.g. grid), excluding width. */
  containerClassName?: string
}

/** Full-width section: background by tone, shared vertical spacing and a `Container`. */
export function Section({ tone, className, containerClassName, children, ...props }: SectionProps) {
  return (
    <section {...props} className={cn(toneClass[tone], 'py-16 md:py-24', className)}>
      <Container className={containerClassName}>{children}</Container>
    </section>
  )
}

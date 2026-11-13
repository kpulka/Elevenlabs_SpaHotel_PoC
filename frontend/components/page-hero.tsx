import Image from 'next/image'
import type { ReactNode } from 'react'

import { Container } from '@/components/section'
import { cn } from '@/lib/utils'

const minHeightClass = {
  380: 'min-h-[380px]',
  420: 'min-h-[420px]',
  640: 'min-h-[640px]',
} as const

const typography = {
  page: {
    title: 'mt-3 max-w-2xl text-balance font-serif text-4xl font-bold text-white md:text-5xl',
    subtitle: 'mt-4 max-w-2xl text-lg leading-relaxed text-white/90',
  },
  home: {
    title: 'mt-4 text-balance font-serif text-4xl font-bold leading-tight text-white md:text-6xl',
    subtitle: 'mt-6 max-w-xl text-lg leading-relaxed text-white/90 md:text-xl',
  },
} as const

interface PageHeroProps {
  image: string
  alt: string
  tag: string
  title: string
  subtitle: string
  /** Treść pod podtytułem, np. przyciski CTA na stronie głównej. */
  children?: ReactNode
  minHeight?: keyof typeof minHeightClass
  /** `home`: wyższy hero z gradientem i większą typografią. */
  variant?: keyof typeof typography
}

/**
 * Hero podstrony: obraz tła (zawsze `priority`, bo to LCP), overlay, tag, jedyny h1 i podtytuł.
 */
export function PageHero({
  image,
  alt,
  tag,
  title,
  subtitle,
  children,
  minHeight = 420,
  variant = 'page',
}: PageHeroProps) {
  const isHome = variant === 'home'
  const text = typography[variant]

  const content = (
    <>
      <p className="text-sm font-semibold tracking-[0.2em] text-gold uppercase">{tag}</p>
      <h1 className={text.title}>{title}</h1>
      <p className={text.subtitle}>{subtitle}</p>
      {children}
    </>
  )

  return (
    <section className={cn('relative flex', minHeightClass[minHeight], 'items-center overflow-hidden')}>
      <Image src={image} alt={alt} fill priority className="object-cover" />
      <div
        className={cn(
          'absolute inset-0',
          isHome ? 'bg-gradient-to-t from-navy/80 via-navy/40 to-navy/20' : 'bg-navy/60',
        )}
      />
      <Container className={cn('relative z-10', isHome && 'w-full py-24')}>
        {isHome ? <div className="max-w-2xl">{content}</div> : content}
      </Container>
    </section>
  )
}

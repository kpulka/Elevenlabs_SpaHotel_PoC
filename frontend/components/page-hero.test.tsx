import { cleanup, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { PageHero } from '@/components/page-hero'

describe('PageHero', () => {
  // Vitest działa bez `globals`, więc RTL nie czyści DOM automatycznie między testami.
  afterEach(() => {
    cleanup()
  })

  it('renders the image with its alt text and exactly one h1', () => {
    const { container } = render(
      <PageHero
        image="/images/spa-pool.png"
        alt="Basen termalny"
        tag="Strefa SPA"
        title="Odnowa ciała"
        subtitle="Zabiegi lecznicze"
      />,
    )

    expect(screen.getByRole('img', { name: 'Basen termalny' })).toBeTruthy()
    const headings = screen.getAllByRole('heading', { level: 1 })
    expect(headings).toHaveLength(1)
    expect(headings[0].textContent).toBe('Odnowa ciała')
    expect(within(container).getByText('Strefa SPA')).toBeTruthy()
    expect(within(container).getByText('Zabiegi lecznicze')).toBeTruthy()
  })

  it('renders children (CTA) and keeps a single h1 in the home variant', () => {
    render(
      <PageHero
        variant="home"
        minHeight={640}
        image="/images/hero-pool.png"
        alt="Hotel"
        tag="Uzdrowisko"
        title="Witamy"
        subtitle="Podtytuł"
      >
        <button type="button">Zarezerwuj</button>
      </PageHero>,
    )

    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
    expect(screen.getByRole('button', { name: 'Zarezerwuj' })).toBeTruthy()
  })
})

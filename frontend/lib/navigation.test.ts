import { describe, expect, it } from 'vitest'

import { getNavItems } from '@/lib/navigation'
import { translations } from '@/lib/translations'

describe('getNavItems', () => {
  it('returns the site routes in a fixed order', () => {
    const hrefs = getNavItems(translations.pl).map((item) => item.href)

    expect(hrefs).toEqual(['/pokoje', '/spa', '/restauracja', '/dojazd', '/kontakt'])
  })

  it('takes labels from the dictionary of the given language', () => {
    const en = getNavItems(translations.en).map((item) => item.label)
    const pl = getNavItems(translations.pl).map((item) => item.label)

    expect(en).toEqual([
      translations.en.nav.rooms,
      translations.en.nav.spa,
      translations.en.nav.restaurant,
      translations.en.nav.access,
      translations.en.nav.contact,
    ])
    expect(en).not.toEqual(pl)
  })
})

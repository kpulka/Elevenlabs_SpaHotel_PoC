import type { Dictionary } from '@/lib/translations'

export type NavItem = {
  readonly label: string
  readonly href: string
}

/** Main site navigation items, shared by the header and the footer. */
export function getNavItems(t: Dictionary): readonly NavItem[] {
  return [
    { label: t.nav.rooms, href: '/pokoje' },
    { label: t.nav.spa, href: '/spa' },
    { label: t.nav.restaurant, href: '/restauracja' },
    { label: t.nav.access, href: '/dojazd' },
    { label: t.nav.contact, href: '/kontakt' },
  ] as const
}

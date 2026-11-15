import type { Language } from "./translations"

/** Bilingual value: one place for a PL/EN pair instead of two parallel arrays. */
export type L<T> = { pl: T; en: T }

/** Picks the language variant from a bilingual record. */
export function loc<T>(value: L<T>, lang: Language): T {
  return lang === "en" ? value.en : value.pl
}

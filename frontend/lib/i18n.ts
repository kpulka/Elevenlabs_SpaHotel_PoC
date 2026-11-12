import type { Language } from "./translations"

/** Dwujęzyczna wartość — jedno miejsce na parę PL/EN zamiast dwóch równoległych tablic. */
export type L<T> = { pl: T; en: T }

/** Wybór wariantu językowego z rekordu dwujęzycznego. */
export function loc<T>(value: L<T>, lang: Language): T {
  return lang === "en" ? value.en : value.pl
}

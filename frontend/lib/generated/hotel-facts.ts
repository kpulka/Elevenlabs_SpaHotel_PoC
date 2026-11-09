// @generated — run pnpm data:sync
//
// ŹRÓDŁO (tylko do odczytu): mock_backend/data/rooms.json, mock_backend/data/spa_schedule.json
// Plik generowany przez scripts/sync-data.mjs. NIE edytuj ręcznie.
// Bramka driftu: pnpm data:check (krok CI).
//
// Backend jest jedynym źródłem prawdy dla identyfikatorów pokoi i ich cen za dobę
// oraz dla listy zabiegów wraz z ceną (pricePln, zł) i czasem trwania (durationMin, min).
// Copy PL/EN żyje w lib/hotel-data.ts — ten plik go nie zawiera.
//
// Baseny (pole `_baseny` w spa_schedule.json) to udogodnienia strefy basenowej,
// nie zabiegi do rezerwacji — dlatego nie mają tu wpisu i nie są rezerwowalne.

export const ROOM_FACTS = [
  { id: "jednoosobowy", pricePerNight: 350, currency: "PLN", backendName: "Pokój Jednoosobowy 'Spokojny Sen'" },
  { id: "dwuosobowy", pricePerNight: 500, currency: "PLN", backendName: "Pokój Dwuosobowy 'Komfort Plus'" },
  { id: "apartament", pricePerNight: 750, currency: "PLN", backendName: "Apartament" },
] as const

/** Zabiegi z katalogu backendu, które mają copy PL/EN na stronie. */
export const SITE_TREATMENTS = [
  { id: "kapiel-siarczkowa", code: "kapiel_siarczkowa", backendName: "kąpiel siarczkowa Ukojenie Stawów", pricePln: 80, durationMin: 20 },
  { id: "masaz-leczniczy", code: "masaz_leczniczy", backendName: "masaż leczniczy pleców", pricePln: 120, durationMin: 30 },
  { id: "kapiel-borowinowa", code: "kapiel_borowinowa", backendName: "kąpiel borowinowa", pricePln: 100, durationMin: 25 },
  { id: "jonoforeza", code: "jonoforeza", backendName: "jonoforeza", pricePln: 70, durationMin: 20 },
  { id: "masaz-klasyczny", code: "masaz_klasyczny", backendName: "masaż klasyczny", pricePln: 160, durationMin: 50 },
  { id: "gimnastyka-lecznicza", code: "gimnastyka_lecznicza", backendName: "gimnastyka lecznicza (grupowa)", pricePln: 30, durationMin: 45 },
] as const

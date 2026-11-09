#!/usr/bin/env node
/**
 * Generator faktów hotelowych: backend (mock_backend/data/*.json) -> frontend.
 *
 *   node scripts/sync-data.mjs           # przegeneruj lib/generated/hotel-facts.ts
 *   node scripts/sync-data.mjs --check   # wyjdź kodem 1, jeśli plik jest nieaktualny
 *
 * Backend jest źródłem prawdy dla: identyfikatorów i cen pokoi, listy zabiegów
 * w katalogu głosowym oraz ich cen (price_pln) i czasów trwania (duration_min).
 * Frontend merge'uje te fakty z dwujęzycznym copy po `id`.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs"
import { dirname, join, resolve } from "node:path"
import { fileURLToPath } from "node:url"

const here = dirname(fileURLToPath(import.meta.url))
const frontendRoot = resolve(here, "..")
const backendDataDir = resolve(frontendRoot, "..", "mock_backend", "data")
const outPath = join(frontendRoot, "lib", "generated", "hotel-facts.ts")
const treatmentCopyPath = join(frontendRoot, "lib", "hotel-data.ts")

/**
 * Każdy kod z spa_schedule.json musi mieć copy PL/EN w lib/hotel-data.ts.
 * Generator sprawdza to sam, zanim wyemituje plik: nowy zabieg w JSON bez wpisu
 * w `treatmentCopy` zatrzymuje build z nazwą brakującego id, zamiast po cichu
 * wygenerować kartę bez treści.
 */

/** Kod backendu ("kapiel_siarczkowa") -> id używane na stronie ("kapiel-siarczkowa"). */
function idFromCode(code) {
  return code.replace(/_/g, "-")
}

function fail(message) {
  console.error(`[data:sync] BŁĄD: ${message}`)
  process.exit(1)
}

function readJson(name) {
  const path = join(backendDataDir, name)
  if (!existsSync(path)) fail(`nie znaleziono ${path}`)
  try {
    return JSON.parse(readFileSync(path, "utf8"))
  } catch (error) {
    fail(`${path} nie jest poprawnym JSON-em: ${error.message}`)
  }
}

/** Liczba skończona > 0 albo błąd — ceny i czasy muszą pochodzić z JSON-a, nie z kodu. */
function requirePositiveNumber(value, label) {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) {
    fail(`${label} musi być dodatnią liczbą (jest: ${JSON.stringify(value)})`)
  }
  return value
}

/** Czy `lib/hotel-data.ts` deklaruje klucz `id` w literale `treatmentCopy`? */
function hasTreatmentCopy(source, id) {
  const escaped = id.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
  const pattern = new RegExp(`(^|[^\\w-])["'\`]?${escaped}["'\`]?\\s*:`, "m")
  return pattern.test(source)
}

const roomsJson = readJson("rooms.json")
const spaJson = readJson("spa_schedule.json")

if (!existsSync(treatmentCopyPath)) {
  fail(`nie znaleziono ${treatmentCopyPath} — nie da się sprawdzić kompletności copy`)
}
const hotelDataSource = readFileSync(treatmentCopyPath, "utf8")

// --- pokoje -----------------------------------------------------------------
const typy = roomsJson.typy_pokoi
if (!typy || typeof typy !== "object" || Object.keys(typy).length === 0) {
  fail("rooms.json: brak obiektu typy_pokoi z wpisami")
}

const rooms = Object.entries(typy).map(([id, wpis]) => {
  if (typeof wpis?.cena_za_noc !== "number" || !Number.isFinite(wpis.cena_za_noc)) {
    fail(`rooms.json: typ_pokoi "${id}" nie ma liczbowej cena_za_noc`)
  }
  if (typeof wpis.waluta !== "string" || wpis.waluta.length === 0) {
    fail(`rooms.json: typ_pokoi "${id}" nie ma pola waluta`)
  }
  return {
    id,
    pricePerNight: wpis.cena_za_noc,
    currency: wpis.waluta,
    backendName: typeof wpis.nazwa === "string" ? wpis.nazwa : "",
  }
})

// --- zabiegi ----------------------------------------------------------------
const zabiegi = spaJson.zabiegi
if (!Array.isArray(zabiegi) || zabiegi.length === 0) {
  fail("spa_schedule.json: brak niepustej tablicy zabiegi")
}

const seenCodes = new Set()
const siteTreatments = []

for (const wpis of zabiegi) {
  const code = wpis?.kod
  if (typeof code !== "string" || code.length === 0) {
    fail("spa_schedule.json: wpis zabiegu bez pola kod")
  }
  if (seenCodes.has(code)) fail(`spa_schedule.json: zduplikowany kod "${code}"`)
  seenCodes.add(code)

  const id = idFromCode(code)
  if (!hasTreatmentCopy(hotelDataSource, id)) {
    fail(
      `zabieg "${code}" (id "${id}") nie ma copy PL/EN w lib/hotel-data.ts — ` +
        `dodaj wpis do treatmentCopy (kategoria, nazwa, opis), inaczej karta byłaby pusta`
    )
  }

  siteTreatments.push({
    id,
    code,
    backendName: typeof wpis.nazwa === "string" ? wpis.nazwa : "",
    pricePln: requirePositiveNumber(wpis.price_pln, `spa_schedule.json: "${code}".price_pln`),
    durationMin: requirePositiveNumber(
      wpis.duration_min,
      `spa_schedule.json: "${code}".duration_min`
    ),
  })
}

const ids = siteTreatments.map((t) => t.id)
const duplicateIds = ids.filter((id, index) => ids.indexOf(id) !== index)
if (duplicateIds.length > 0) {
  fail(`kolizja id po zamianie "_" na "-": ${[...new Set(duplicateIds)].join(", ")}`)
}

// --- emisja -----------------------------------------------------------------
const quote = (value) => JSON.stringify(value)
const lines = []

lines.push("// @generated — run pnpm data:sync")
lines.push("//")
lines.push("// ŹRÓDŁO (tylko do odczytu): mock_backend/data/rooms.json, mock_backend/data/spa_schedule.json")
lines.push("// Plik generowany przez scripts/sync-data.mjs. NIE edytuj ręcznie.")
lines.push("// Bramka driftu: pnpm data:check (krok CI).")
lines.push("//")
lines.push("// Backend jest jedynym źródłem prawdy dla identyfikatorów pokoi i ich cen za dobę")
lines.push("// oraz dla listy zabiegów wraz z ceną (pricePln, zł) i czasem trwania (durationMin, min).")
lines.push("// Copy PL/EN żyje w lib/hotel-data.ts — ten plik go nie zawiera.")
lines.push("//")
lines.push("// Baseny (pole `_baseny` w spa_schedule.json) to udogodnienia strefy basenowej,")
lines.push("// nie zabiegi do rezerwacji — dlatego nie mają tu wpisu i nie są rezerwowalne.")
lines.push("")
lines.push("export const ROOM_FACTS = [")
for (const room of rooms) {
  lines.push(
    `  { id: ${quote(room.id)}, pricePerNight: ${room.pricePerNight}, currency: ${quote(
      room.currency
    )}, backendName: ${quote(room.backendName)} },`
  )
}
lines.push("] as const")
lines.push("")
lines.push("/** Zabiegi z katalogu backendu, które mają copy PL/EN na stronie. */")
lines.push("export const SITE_TREATMENTS = [")
for (const treatment of siteTreatments) {
  lines.push(
    `  { id: ${quote(treatment.id)}, code: ${quote(treatment.code)}, backendName: ${quote(
      treatment.backendName
    )}, pricePln: ${treatment.pricePln}, durationMin: ${treatment.durationMin} },`
  )
}
lines.push("] as const")
lines.push("")

const content = lines.join("\n")

if (process.argv.includes("--check")) {
  if (!existsSync(outPath)) {
    fail(`brak ${outPath} — uruchom pnpm data:sync`)
  }
  const current = readFileSync(outPath, "utf8")
  if (current !== content) {
    const currentLines = current.split("\n")
    const expectedLines = content.split("\n")
    const index = expectedLines.findIndex((line, i) => line !== currentLines[i])
    console.error(
      `[data:check] ${outPath} jest nieaktualny względem mock_backend/data/*.json`
    )
    console.error(`  pierwsza różnica w linii ${index + 1}:`)
    console.error(`    jest:      ${JSON.stringify(currentLines[index] ?? "<brak>")}`)
    console.error(`    powinno:   ${JSON.stringify(expectedLines[index] ?? "<brak>")}`)
    console.error("  poprawka: pnpm data:sync")
    process.exit(1)
  }
  console.log(
    `[data:check] OK — ${rooms.length} pokoi, ${siteTreatments.length} zabiegów z ceną i czasem.`
  )
  process.exit(0)
}

mkdirSync(dirname(outPath), { recursive: true })
writeFileSync(outPath, content)
console.log(
  `[data:sync] zapisano ${outPath} — ${rooms.length} pokoi, ${siteTreatments.length} zabiegów z ceną i czasem.`
)

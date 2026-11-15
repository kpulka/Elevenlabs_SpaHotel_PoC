#!/usr/bin/env node
/**
 * Hotel facts generator: backend (mock_backend/data/*.json) -> frontend.
 *
 *   node scripts/sync-data.mjs           # regenerate lib/generated/hotel-facts.ts
 *   node scripts/sync-data.mjs --check   # exit with code 1 if the file is stale
 *
 * The backend is the source of truth for: room ids and prices, the list of treatments
 * in the voice catalogue, and their prices (price_pln) and durations (duration_min).
 * The frontend merges these facts with the bilingual copy by `id`.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs"
import { dirname, join, resolve } from "node:path"
import { fileURLToPath } from "node:url"

const here = dirname(fileURLToPath(import.meta.url))
const frontendRoot = resolve(here, "..")
const backendDataDir = resolve(frontendRoot, "..", "mock_backend", "data")
const outPath = join(frontendRoot, "lib", "generated", "hotel-facts.ts")
const treatmentCopyPath = join(frontendRoot, "lib", "hotel", "treatments.ts")

/**
 * Every code in spa_schedule.json must have PL/EN copy in lib/hotel/treatments.ts.
 * The generator checks this itself before emitting the file: a new treatment in the JSON
 * without a `treatmentCopy` entry stops the build and names the missing id, instead of
 * silently generating a card with no content.
 */

/** Backend code ("kapiel_siarczkowa") -> id used on the site ("kapiel-siarczkowa"). */
function idFromCode(code) {
  return code.replace(/_/g, "-")
}

function fail(message) {
  console.error(`[data:sync] ERROR: ${message}`)
  process.exit(1)
}

function readJson(name) {
  const path = join(backendDataDir, name)
  if (!existsSync(path)) fail(`${path} not found`)
  try {
    return JSON.parse(readFileSync(path, "utf8"))
  } catch (error) {
    fail(`${path} is not valid JSON: ${error.message}`)
  }
}

/** A finite number > 0 or an error: prices and durations must come from the JSON, not from code. */
function requirePositiveNumber(value, label) {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) {
    fail(`${label} must be a positive number (got: ${JSON.stringify(value)})`)
  }
  return value
}

/** Does `lib/hotel/treatments.ts` declare the key `id` in the `treatmentCopy` literal? */
function hasTreatmentCopy(source, id) {
  const escaped = id.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
  const pattern = new RegExp(`(^|[^\\w-])["'\`]?${escaped}["'\`]?\\s*:`, "m")
  return pattern.test(source)
}

const roomsJson = readJson("rooms.json")
const spaJson = readJson("spa_schedule.json")

if (!existsSync(treatmentCopyPath)) {
  fail(`${treatmentCopyPath} not found — cannot verify that the copy is complete`)
}
const hotelDataSource = readFileSync(treatmentCopyPath, "utf8")

// --- rooms ------------------------------------------------------------------
const typy = roomsJson.typy_pokoi
if (!typy || typeof typy !== "object" || Object.keys(typy).length === 0) {
  fail("rooms.json: missing typy_pokoi object with entries")
}

const rooms = Object.entries(typy).map(([id, wpis]) => {
  if (typeof wpis?.cena_za_noc !== "number" || !Number.isFinite(wpis.cena_za_noc)) {
    fail(`rooms.json: typy_pokoi "${id}" has no numeric cena_za_noc`)
  }
  if (typeof wpis.waluta !== "string" || wpis.waluta.length === 0) {
    fail(`rooms.json: typy_pokoi "${id}" has no waluta field`)
  }
  return {
    id,
    pricePerNight: wpis.cena_za_noc,
    currency: wpis.waluta,
    backendName: typeof wpis.nazwa === "string" ? wpis.nazwa : "",
  }
})

// --- treatments -------------------------------------------------------------
const zabiegi = spaJson.zabiegi
if (!Array.isArray(zabiegi) || zabiegi.length === 0) {
  fail("spa_schedule.json: missing non-empty zabiegi array")
}

const seenCodes = new Set()
const siteTreatments = []

for (const wpis of zabiegi) {
  const code = wpis?.kod
  if (typeof code !== "string" || code.length === 0) {
    fail("spa_schedule.json: treatment entry without a kod field")
  }
  if (seenCodes.has(code)) fail(`spa_schedule.json: duplicate kod "${code}"`)
  seenCodes.add(code)

  const id = idFromCode(code)
  if (!hasTreatmentCopy(hotelDataSource, id)) {
    fail(
      `treatment "${code}" (id "${id}") has no PL/EN copy in lib/hotel/treatments.ts — ` +
        `add an entry to treatmentCopy (category, name, description), otherwise the card would be empty`
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
  fail(`id collision after replacing "_" with "-": ${[...new Set(duplicateIds)].join(", ")}`)
}

// --- emit -------------------------------------------------------------------
const quote = (value) => JSON.stringify(value)
const lines = []

lines.push("// @generated — run pnpm data:sync")
lines.push("//")
lines.push("// SOURCE (read-only): mock_backend/data/rooms.json, mock_backend/data/spa_schedule.json")
lines.push("// Generated by scripts/sync-data.mjs. Do NOT edit by hand.")
lines.push("// Drift gate: pnpm data:check (CI step).")
lines.push("//")
lines.push("// The backend is the single source of truth for room ids and their nightly prices,")
lines.push("// and for the list of treatments with price (pricePln, PLN) and duration (durationMin, min).")
lines.push("// The PL/EN copy lives in lib/hotel/rooms.ts and lib/hotel/treatments.ts, not in this file.")
lines.push("//")
lines.push("// The pools (`_baseny` field in spa_schedule.json) are pool-area amenities,")
lines.push("// not bookable treatments, so they have no entry here and cannot be booked.")
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
lines.push("/** Treatments from the backend catalogue that have PL/EN copy on the site. */")
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
    fail(`${outPath} is missing — run pnpm data:sync`)
  }
  const current = readFileSync(outPath, "utf8")
  if (current !== content) {
    const currentLines = current.split("\n")
    const expectedLines = content.split("\n")
    const index = expectedLines.findIndex((line, i) => line !== currentLines[i])
    console.error(
      `[data:check] ${outPath} is out of date with mock_backend/data/*.json`
    )
    console.error(`  first difference at line ${index + 1}:`)
    console.error(`    actual:    ${JSON.stringify(currentLines[index] ?? "<missing>")}`)
    console.error(`    expected:  ${JSON.stringify(expectedLines[index] ?? "<missing>")}`)
    console.error("  fix: pnpm data:sync")
    process.exit(1)
  }
  console.log(
    `[data:check] OK — ${rooms.length} rooms, ${siteTreatments.length} treatments with price and duration.`
  )
  process.exit(0)
}

mkdirSync(dirname(outPath), { recursive: true })
writeFileSync(outPath, content)
console.log(
  `[data:sync] wrote ${outPath} — ${rooms.length} rooms, ${siteTreatments.length} treatments with price and duration.`
)

#!/usr/bin/env node
/**
 * Bramka parytetu tłumaczeń PL/EN.
 *
 *   node scripts/check-i18n.mjs
 *
 * Parsuje `lib/translations.ts` kompilatorem TypeScript (bez transpilacji,
 * bez nowych zależności) i porównuje zbiory kluczy obu słowników rekurencyjnie.
 * Kompilator pilnuje parytetu typów (`en: Dictionary`), a ta bramka wyłapuje to,
 * co typy przepuszczą: podmienione lub zduplikowane klucze w trakcie merge'y.
 *
 * Kod wyjścia 1 = jakakolwiek różnica.
 */

import { readFileSync } from "node:fs"
import { dirname, join, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { createRequire } from "node:module"

const require = createRequire(import.meta.url)
const ts = require("typescript")

const here = dirname(fileURLToPath(import.meta.url))
const sourcePath = resolve(here, "..", "lib", "translations.ts")

const source = readFileSync(sourcePath, "utf8")
const sourceFile = ts.createSourceFile(
  sourcePath,
  source,
  ts.ScriptTarget.Latest,
  true,
  ts.ScriptKind.TS
)

/** Wyciąga drzewo kluczy z literału obiektowego, np. { home: { a: "x" } } -> { "home.a": "string" }. */
function collect(node, prefix, out) {
  if (!ts.isObjectLiteralExpression(node)) {
    out.set(prefix, describe(node))
    return
  }
  for (const property of node.properties) {
    let name = null
    if (ts.isPropertyAssignment(property) || ts.isShorthandPropertyAssignment(property)) {
      if (ts.isIdentifier(property.name)) name = property.name.text
      else if (ts.isStringLiteralLike(property.name)) name = property.name.text
    }
    if (name === null) {
      out.set(`${prefix}.<nieobsługiwany wpis>`, "unsupported")
      continue
    }
    const path = prefix ? `${prefix}.${name}` : name
    if (ts.isPropertyAssignment(property)) {
      collect(property.initializer, path, out)
    } else {
      out.set(path, "shorthand")
    }
  }
}

function describe(node) {
  if (ts.isStringLiteralLike(node)) return "string"
  if (ts.isArrayLiteralExpression(node)) return `array(${node.elements.length})`
  if (ts.isNumericLiteral(node)) return "number"
  return ts.SyntaxKind[node.kind]
}

/** Znajduje `const <name> = { ... }` na najwyższym poziomie pliku. */
function findDictionaryObject(name) {
  let found = null
  for (const statement of sourceFile.statements) {
    if (!ts.isVariableStatement(statement)) continue
    for (const declaration of statement.declarationList.declarations) {
      if (!ts.isIdentifier(declaration.name) || declaration.name.text !== name) continue
      if (declaration.initializer && ts.isObjectLiteralExpression(declaration.initializer)) {
        found = declaration.initializer
      }
    }
  }
  return found
}

const problems = []

const plNode = findDictionaryObject("pl")
const enNode = findDictionaryObject("en")

if (!plNode) problems.push("nie znaleziono literału `const pl = {...}` w lib/translations.ts")
if (!enNode) problems.push("nie znaleziono literału `const en: Dictionary = {...}` w lib/translations.ts")

if (plNode && enNode) {
  const plKeys = new Map()
  const enKeys = new Map()
  collect(plNode, "", plKeys)
  collect(enNode, "", enKeys)

  for (const [key, kind] of plKeys) {
    if (!enKeys.has(key)) {
      problems.push(`MISSING en: ${key}`)
      continue
    }
    const enKind = enKeys.get(key)
    const plIsArray = kind.startsWith("array(")
    const enIsArray = enKind.startsWith("array(")
    if (plIsArray !== enIsArray) {
      problems.push(`TYPE  en: ${key} (pl: ${kind}, en: ${enKind})`)
      continue
    }
    if (plIsArray && kind !== enKind) {
      problems.push(`LENGTH en: ${key} (pl: ${kind}, en: ${enKind})`)
    }
    if (!plIsArray && kind !== enKind) {
      problems.push(`TYPE  en: ${key} (pl: ${kind}, en: ${enKind})`)
    }
  }

  for (const key of enKeys.keys()) {
    if (!plKeys.has(key)) problems.push(`EXTRA en: ${key}`)
  }

  if (problems.length === 0 && plKeys.size > 0) {
    console.log(`[i18n:check] OK — ${plKeys.size} kluczy w obu językach (pl / en).`)
  }
}

if (problems.length > 0) {
  for (const problem of problems) console.error(`[i18n:check] ${problem}`)
  console.error(`[i18n:check] ${problems.length} problem(ów) — słowniki PL i EN nie są zgodne.`)
  process.exit(1)
}

if (problems.length === 0 && (!plNode || !enNode)) {
  console.error("[i18n:check] nie udało się sparsować słowników.")
  process.exit(1)
}

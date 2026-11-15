#!/usr/bin/env node
/**
 * PL/EN translation parity gate.
 *
 *   node scripts/check-i18n.mjs
 *
 * Parses `lib/translations.ts` with the TypeScript compiler (no transpilation,
 * no new dependencies) and recursively compares the key sets of both dictionaries.
 * The compiler guards type parity (`en: Dictionary`); this gate catches what
 * types let through: keys swapped or duplicated during merges.
 *
 * Exit code 1 = any difference.
 */

import { readFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
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

/** Extracts the key tree from an object literal, e.g. { home: { a: "x" } } -> { "home.a": "string" }. */
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
      out.set(`${prefix}.<unsupported entry>`, "unsupported")
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

/** Finds `const <name> = { ... }` at the top level of the file. */
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

if (!plNode) problems.push("literal `const pl = {...}` not found in lib/translations.ts")
if (!enNode) problems.push("literal `const en: Dictionary = {...}` not found in lib/translations.ts")

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
    console.log(`[i18n:check] OK — ${plKeys.size} keys in both languages (pl / en).`)
  }
}

if (problems.length > 0) {
  for (const problem of problems) console.error(`[i18n:check] ${problem}`)
  console.error(`[i18n:check] ${problems.length} problem(s) — the PL and EN dictionaries do not match.`)
  process.exit(1)
}

if (problems.length === 0 && (!plNode || !enNode)) {
  console.error("[i18n:check] failed to parse the dictionaries.")
  process.exit(1)
}

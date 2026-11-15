#!/usr/bin/env node
/**
 * Converts photos to WebP for public/images. Kept as a documented tool.
 *
 *   node scripts/optimize-images.mjs --source=<dir>                  # convert every PNG in <dir> into public/images
 *   node scripts/optimize-images.mjs --source=<dir> --remove-source  # ...and delete each source PNG afterwards
 *   node scripts/optimize-images.mjs --check                         # exit 1 if a PNG in <dir> has no WebP in public/images
 *
 * The original PNGs were removed from public/images to keep the repo small. They remain in git history
 * (commits before this change). Export them to a folder outside the repo and pass it with --source.
 *
 * Rules:
 * - Max width 1600 px (no upscaling).
 * - Quality starts at 80 and drops in steps of 5 (not below 50) until the file is <= 300 KB.
 * - Social cards (public/og/*) are NOT converted: Open Graph and most crawlers need JPEG or PNG.
 * - Icons (public/*.png) are not converted: favicons and apple-touch-icon need PNG.
 *
 * Uses `sharp` (devDependency; Next.js uses it for image optimisation too).
 */

import { existsSync, readdirSync, statSync, unlinkSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import sharp from 'sharp'

const here = dirname(fileURLToPath(import.meta.url))
const outDir = resolve(here, '..', 'public', 'images')

const MAX_WIDTH = 1600
const MAX_BYTES = 300 * 1024
const START_QUALITY = 80
const MIN_QUALITY = 50
const STEP = 5

const args = process.argv.slice(2)
const sourceArg = args.find((arg) => arg.startsWith('--source='))
const sourceDir = sourceArg ? resolve(sourceArg.slice('--source='.length)) : null
const removeSource = args.includes('--remove-source')
const checkOnly = args.includes('--check')

function kb(bytes) {
  return `${(bytes / 1024).toFixed(0)} KB`
}

function listPngs(dir) {
  return readdirSync(dir)
    .filter((name) => name.toLowerCase().endsWith('.png'))
    .sort()
}

/** Encodes one PNG as WebP, lowering quality until the result fits in MAX_BYTES. */
async function encode(pngPath) {
  const image = sharp(pngPath, { failOn: 'error' }).rotate().resize({ width: MAX_WIDTH, withoutEnlargement: true })
  let quality = START_QUALITY
  let output = await image.clone().webp({ quality, effort: 6 }).toBuffer()
  while (output.length > MAX_BYTES && quality - STEP >= MIN_QUALITY) {
    quality -= STEP
    output = await image.clone().webp({ quality, effort: 6 }).toBuffer()
  }
  const meta = await sharp(output).metadata()
  return { buffer: output, quality, width: meta.width, height: meta.height }
}

async function main() {
  if (!existsSync(outDir)) {
    console.error(`[images] output directory not found: ${outDir}`)
    process.exit(1)
  }
  if (!sourceDir) {
    console.error('[images] pass --source=<dir> with the original PNG files (see the header of this script)')
    process.exit(1)
  }
  if (!existsSync(sourceDir)) {
    console.error(`[images] source directory not found: ${sourceDir}`)
    process.exit(1)
  }

  const pngs = listPngs(sourceDir)
  if (pngs.length === 0) {
    console.log('[images] no PNG files in the source directory')
    return
  }

  if (checkOnly) {
    const missing = pngs.filter((name) => !existsSync(join(outDir, name.replace(/\.png$/i, '.webp'))))
    if (missing.length > 0) {
      console.error(`[images] missing WebP for: ${missing.join(', ')}`)
      process.exit(1)
    }
    console.log(`[images] OK: ${pngs.length} source PNG file(s) have a WebP in public/images`)
    return
  }

  let totalBefore = 0
  let totalAfter = 0
  let failures = 0
  for (const name of pngs) {
    const source = join(sourceDir, name)
    const target = join(outDir, name.replace(/\.png$/i, '.webp'))
    const before = statSync(source).size
    try {
      const { buffer, quality, width, height } = await encode(source)
      writeFileSync(target, buffer)
      totalBefore += before
      totalAfter += buffer.length
      const flag = buffer.length > MAX_BYTES ? ' (above 300 KB even at minimum quality)' : ''
      console.log(`[images] ${name}: ${kb(before)} -> ${kb(buffer.length)} (${width}x${height}, q${quality})${flag}`)
      if (removeSource) unlinkSync(source)
    } catch (err) {
      failures += 1
      console.error(`[images] ${name}: failed: ${err instanceof Error ? err.message : String(err)}`)
    }
  }

  console.log(`[images] total ${kb(totalBefore)} -> ${kb(totalAfter)} across ${pngs.length} file(s)`)
  if (failures > 0) process.exit(1)
}

main()

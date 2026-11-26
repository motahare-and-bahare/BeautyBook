import { existsSync, readFileSync, statSync } from 'node:fs'
import { resolve } from 'node:path'

import { describe, expect, it } from 'vitest'

/**
 * F-023: the Vazir typeface must ship with the application.
 *
 * These are file-level assertions on purpose: a missing or mis-declared font is invisible to
 * component tests (jsdom never loads fonts), so the only cheap guard is checking the real asset.
 */

const srcRoot = resolve(process.cwd(), 'src') + '/'

function read(relativePath: string): string {
  return readFileSync(`${srcRoot}${relativePath}`, 'utf8')
}

describe('self-hosted Vazirmatn font', () => {
  it('declares the family from a local WOFF2 file with swap', () => {
    const css = read('assets/styles/fonts.css')

    expect(css).toContain('@font-face')
    expect(css).toMatch(/font-family:\s*["']?Vazirmatn["']?/)
    expect(css).toContain('format("woff2")')
    expect(css).toMatch(/font-display:\s*swap/)
    expect(css).toMatch(/font-weight:\s*100\s+900/)
    // A third-party host would leak every visitor's IP. Comments may cite the upstream project,
    // so only real loads (url() and @import) are checked.
    expect(css).not.toMatch(/url\(\s*["']?https?:/i)
    expect(css).not.toMatch(/@import\s+(url\()?["']?https?:/i)
  })

  it('ships a real WOFF2 file next to its license', () => {
    const fontPath = `${srcRoot}assets/fonts/Vazirmatn-Variable.woff2`

    expect(existsSync(fontPath)).toBe(true)
    expect(statSync(fontPath).size).toBeGreaterThan(20_000)

    const signature = readFileSync(fontPath).subarray(0, 4).toString('latin1')
    expect(signature).toBe('wOF2')
  })

  it('declares the font file that actually exists', () => {
    const css = read('assets/styles/fonts.css')
    const urls = [...css.matchAll(/url\(["']?([^"')]+)["']?\)/g)].map((match) => match[1]!)

    expect(urls.length).toBeGreaterThan(0)
    for (const url of urls) {
      expect(url).not.toMatch(/^https?:/)
      const resolved = url.replace('../fonts/', 'assets/fonts/')
      expect(existsSync(`${srcRoot}${resolved}`)).toBe(true)
    }
  })

  it('ships the SIL Open Font License text', () => {
    const license = read('assets/fonts/Vazirmatn-OFL.txt')

    expect(license).toContain('SIL OPEN FONT LICENSE')
    expect(license.toLowerCase()).toContain('version 1.1')
  })

  it('keeps the Persian-first fallback stack intact', () => {
    const tokens = read('assets/styles/tokens.css')
    const stack = tokens.match(/--font-sans:\s*([^;]+);/)?.[1] ?? ''

    expect(stack).toMatch(/"Vazirmatn"/)
    expect(stack).toMatch(/Tahoma/)
    expect(stack).toMatch(/sans-serif/)
    // The family served by @font-face must be the first fallback the browser tries.
    expect(stack.trimStart().startsWith('"Vazirmatn"')).toBe(true)
  })

  it('loads the font stylesheet from the application entry point', () => {
    const main = read('main.ts')
    const fontImport = main.indexOf("assets/styles/fonts.css")
    const tokenImport = main.indexOf("assets/styles/tokens.css")

    expect(fontImport).toBeGreaterThan(-1)
    expect(tokenImport).toBeGreaterThan(-1)
  })
})

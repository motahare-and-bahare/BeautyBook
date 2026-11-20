import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

import { describe, expect, it } from 'vitest'

function read(relativePath: string): string {
  return readFileSync(fileURLToPath(new URL(relativePath, import.meta.url)), 'utf8')
}

describe('Persian right-to-left document', () => {
  it('declares Persian as the document language and right-to-left direction', () => {
    const html = read('../../index.html')

    expect(html).toMatch(/<html[^>]*\blang="fa"/)
    expect(html).toMatch(/<html[^>]*\bdir="rtl"/)
  })

  it('uses a Persian-capable font stack', () => {
    const css = read('../../src/assets/styles/tokens.css')
    const declaration = css.match(/--font-sans:\s*([^;]+);/)

    expect(declaration).not.toBeNull()
    const stack = declaration?.[1] ?? ''
    expect(stack).toContain('Vazirmatn')
    expect(stack).toContain('Tahoma')
  })
})

import { describe, expect, it } from 'vitest'

import { safeRedirect } from '@/utils/redirect'

describe('safeRedirect', () => {
  it.each(['/admin', '/account?tab=1', '/owner/salon#hours', '/'])(
    'accepts the local absolute path %s',
    (path) => {
      expect(safeRedirect(path, '/fallback')).toBe(path)
    },
  )

  it.each([
    null,
    undefined,
    '',
    '   ',
    'admin',
    '//evil.example/admin',
    'https://evil.example',
    'http://evil.example',
    'javascript:alert(1)',
    '/\\evil.example',
    '/admin\nSet-Cookie: stolen=1',
  ])('rejects %s', (path) => {
    expect(safeRedirect(path as string | null | undefined, '/fallback')).toBe('/fallback')
  })

  it('uses the first value when the query parameter repeats', () => {
    expect(safeRedirect(['/admin', '/account'], '/fallback')).toBe('/admin')
  })

  it('returns the fallback when the first repeated value is unsafe', () => {
    expect(safeRedirect(['//evil.example', '/admin'], '/fallback')).toBe('/fallback')
  })
})

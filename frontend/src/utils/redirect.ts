/**
 * Redirect targets come from the URL (`?redirect=`), so they must never be trusted.
 *
 * Only a local absolute path is accepted: it has to start with a single `/` and must not carry
 * control characters (which could smuggle a header) or a protocol-relative `//host` form.
 */

export function safeRedirect(value: unknown, fallback: string): string {
  const candidate = Array.isArray(value) ? value[0] : value

  if (typeof candidate !== 'string') {
    return fallback
  }

  const trimmed = candidate.trim()

  if (!trimmed.startsWith('/')) {
    return fallback
  }
  if (trimmed.startsWith('//') || trimmed.startsWith('/\\')) {
    return fallback
  }
  // eslint-disable-next-line no-control-regex
  if (/[\u0000-\u001f\u007f]/.test(trimmed)) {
    return fallback
  }

  return trimmed
}

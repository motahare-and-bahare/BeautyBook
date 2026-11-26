/**
 * Pure access decision for the router guard.
 *
 * Keeping this free of Vue, Pinia, and the router makes the security-relevant matrix cheap to
 * test. The backend still enforces roles on every endpoint; this only decides what to render.
 */

export interface AccessInput {
  requiresAuth: boolean
  allowedRoles: readonly string[]
  /** `null` means "no usable session", not "empty role list". */
  currentRoles: readonly string[] | null
}

export type AccessDecision =
  | { kind: 'allow' }
  | { kind: 'login' }
  | { kind: 'forbidden'; requiredRoles: string[] }

export function resolveAccess({
  requiresAuth,
  allowedRoles,
  currentRoles,
}: AccessInput): AccessDecision {
  if (!requiresAuth) {
    return { kind: 'allow' }
  }

  if (currentRoles === null) {
    return { kind: 'login' }
  }

  if (allowedRoles.length === 0) {
    return { kind: 'allow' }
  }

  const allowed = allowedRoles.some((role) => currentRoles.includes(role))

  return allowed ? { kind: 'allow' } : { kind: 'forbidden', requiredRoles: [...allowedRoles] }
}

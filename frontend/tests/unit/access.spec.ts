import { describe, expect, it } from 'vitest'

import { resolveAccess } from '@/router/access'

describe('resolveAccess', () => {
  it('allows a public route for a guest', () => {
    expect(
      resolveAccess({ requiresAuth: false, allowedRoles: [], currentRoles: null }),
    ).toEqual({ kind: 'allow' })
  })

  it('sends a guest to the login page for a protected route', () => {
    expect(
      resolveAccess({ requiresAuth: true, allowedRoles: ['admin'], currentRoles: null }),
    ).toEqual({ kind: 'login' })
  })

  it('allows an administrator into the admin area', () => {
    expect(
      resolveAccess({
        requiresAuth: true,
        allowedRoles: ['admin'],
        currentRoles: ['admin'],
      }),
    ).toEqual({ kind: 'allow' })
  })

  it('allows a user who holds one of several accepted roles', () => {
    expect(
      resolveAccess({
        requiresAuth: true,
        allowedRoles: ['admin', 'support'],
        currentRoles: ['customer', 'support'],
      }),
    ).toEqual({ kind: 'allow' })
  })

  it('blocks a signed-in customer and names the required role', () => {
    expect(
      resolveAccess({
        requiresAuth: true,
        allowedRoles: ['admin'],
        currentRoles: ['customer'],
      }),
    ).toEqual({ kind: 'forbidden', requiredRoles: ['admin'] })
  })

  it('allows any signed-in user when no specific role is required', () => {
    expect(
      resolveAccess({ requiresAuth: true, allowedRoles: [], currentRoles: ['customer'] }),
    ).toEqual({ kind: 'allow' })
  })

  it('treats an unknown role as not allowed', () => {
    expect(
      resolveAccess({
        requiresAuth: true,
        allowedRoles: ['admin'],
        currentRoles: ['superuser'],
      }),
    ).toEqual({ kind: 'forbidden', requiredRoles: ['admin'] })
  })
})

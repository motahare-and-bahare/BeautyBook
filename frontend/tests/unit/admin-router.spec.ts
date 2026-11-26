import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { createAppRouter } from '@/router'
import { authApi } from '@/services/api/auth'
import { ApiError } from '@/services/api/client'

vi.mock('@/services/api/auth', () => ({
  authApi: {
    registerCustomer: vi.fn(),
    login: vi.fn(),
    me: vi.fn(),
  },
}))

const meMock = vi.mocked(authApi.me)

const ADMIN = {
  id: 'a'.repeat(8),
  full_name: 'Reza Admin',
  email: 'admin@example.com',
  roles: ['admin'],
  status: 'active',
  created_at: '2026-11-19T10:15:30Z',
}
const CUSTOMER = {
  ...ADMIN,
  id: 'c'.repeat(8),
  full_name: 'Sara Ahmadi',
  email: 'sara@example.com',
  roles: ['customer'],
}

beforeEach(() => {
  setActivePinia(createPinia())
  meMock.mockReset()
})

describe('admin route guard', () => {
  it('sends a guest to the auth page and remembers the target', async () => {
    meMock.mockRejectedValue(new ApiError(401, 'UNAUTHENTICATED', 'Not signed in.'))
    const router = createAppRouter()

    await router.push('/admin')

    expect(router.currentRoute.value.name).toBe('auth')
    expect(router.currentRoute.value.query.redirect).toBe('/admin')
  })

  it('keeps the full nested path in the redirect', async () => {
    meMock.mockRejectedValue(new ApiError(401, 'UNAUTHENTICATED', 'Not signed in.'))
    const router = createAppRouter()

    await router.push('/admin/users')

    expect(router.currentRoute.value.name).toBe('auth')
    expect(router.currentRoute.value.query.redirect).toBe('/admin/users')
  })

  it('shows the access-denied page to a signed-in customer', async () => {
    meMock.mockResolvedValue(CUSTOMER)
    const router = createAppRouter()

    await router.push('/admin')

    expect(router.currentRoute.value.name).toBe('forbidden')
    expect(router.currentRoute.value.query.required).toBe('admin')
    expect(router.currentRoute.value.query.from).toBe('/admin')
  })

  it('renders the admin area for an administrator', async () => {
    meMock.mockResolvedValue(ADMIN)
    const router = createAppRouter()

    await router.push('/admin')

    expect(router.currentRoute.value.name).toBe('admin-dashboard')
  })

  it('leaves public routes alone for a guest', async () => {
    meMock.mockRejectedValue(new ApiError(401, 'UNAUTHENTICATED', 'Not signed in.'))
    const router = createAppRouter()

    await router.push('/forbidden')

    expect(router.currentRoute.value.name).toBe('forbidden')
    expect(meMock).not.toHaveBeenCalled()
  })
})

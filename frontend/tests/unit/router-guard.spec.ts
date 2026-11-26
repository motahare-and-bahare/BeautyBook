import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import router from '@/router'
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
  id: '8f14e45f-ea2f-4c1b-9b7a-1f3c2d4e5f60',
  full_name: 'Mina Admin',
  email: 'admin@beautybook.com',
  roles: ['admin', 'customer'],
  status: 'active',
  created_at: '2026-11-25T10:15:30Z',
}

const CUSTOMER = {
  ...ADMIN,
  id: '3c59dc48-8f14-4c1b-9b7a-0f3c2d4e5f61',
  full_name: 'Sara Customer',
  email: 'sara@example.com',
  roles: ['customer'],
}

beforeEach(async () => {
  setActivePinia(createPinia())
  meMock.mockReset()
  await router.replace('/login')
})

describe('admin route guard', () => {
  it('marks the user list as an admin-only, authenticated route', () => {
    const route = router.resolve('/admin/users')

    expect(route.name).toBe('admin-users')
    expect(route.meta.requiresAuth).toBe(true)
    expect(route.meta.roles).toEqual(['admin'])
  })

  it('lets an administrator open the user list', async () => {
    meMock.mockResolvedValue(ADMIN)

    await router.push('/admin/users')

    expect(router.currentRoute.value.name).toBe('admin-users')
  })

  it('sends a signed-out visitor to login with a return path', async () => {
    meMock.mockRejectedValue(new ApiError(401, 'UNAUTHENTICATED', 'Authentication is required.', {}))

    await router.push('/admin/users')

    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/admin/users')
  })

  it('sends a signed-in customer to the 403 page instead of the user list', async () => {
    meMock.mockResolvedValue(CUSTOMER)

    await router.push('/admin/users')

    expect(router.currentRoute.value.name).toBe('forbidden')
  })

  it('still allows the public login page without calling the API', async () => {
    await router.push('/login')

    expect(router.currentRoute.value.name).toBe('login')
    expect(meMock).not.toHaveBeenCalled()
  })
})

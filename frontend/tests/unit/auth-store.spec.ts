import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/stores/auth'
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

beforeEach(() => {
  setActivePinia(createPinia())
  meMock.mockReset()
})

describe('auth store', () => {
  it('loads the current user once for concurrent callers', async () => {
    meMock.mockResolvedValue(ADMIN)
    const store = useAuthStore()

    await Promise.all([store.load(), store.load(), store.load()])

    expect(meMock).toHaveBeenCalledTimes(1)
    expect(store.user?.email).toBe('admin@example.com')
    expect(store.hasRole('admin')).toBe(true)
  })

  it('does not refetch after a successful load', async () => {
    meMock.mockResolvedValue(ADMIN)
    const store = useAuthStore()

    await store.load()
    await store.load()

    expect(meMock).toHaveBeenCalledTimes(1)
  })

  it('treats 401 as a guest and stays safe', async () => {
    meMock.mockRejectedValue(new ApiError(401, 'UNAUTHENTICATED', 'Not signed in.'))
    const store = useAuthStore()

    await store.load()

    expect(store.user).toBeNull()
    expect(store.isAuthenticated).toBe(false)
    expect(store.hasRole('admin')).toBe(false)
  })

  it('treats a 403 from /auth/me as a guest', async () => {
    meMock.mockRejectedValue(new ApiError(403, 'FORBIDDEN', 'Forbidden.'))
    const store = useAuthStore()

    await store.load()

    expect(store.user).toBeNull()
  })

  it('retries after an anonymous load when asked explicitly', async () => {
    meMock.mockRejectedValueOnce(new ApiError(401, 'UNAUTHENTICATED', 'Not signed in.'))
    const store = useAuthStore()
    await store.load()

    meMock.mockResolvedValueOnce(ADMIN)
    await store.reload()

    expect(store.user?.email).toBe('admin@example.com')
    expect(meMock).toHaveBeenCalledTimes(2)
  })
})

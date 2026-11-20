import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { authApi } from '@/services/api/auth'
import { ApiError, clearCsrfToken } from '@/services/api/client'

const fetchMock = vi.fn<typeof fetch>()

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const USER = {
  id: '8f14e45f-ea2f-4c1b-9b7a-1f3c2d4e5f60',
  full_name: 'Sara Ahmadi',
  email: 'sara@example.com',
  roles: ['customer'],
  status: 'active',
  created_at: '2026-11-19T10:15:30Z',
}

const REGISTER_INPUT = {
  full_name: 'Sara Ahmadi',
  email: 'sara@example.com',
  password: 'correct horse battery staple',
}

beforeEach(() => {
  clearCsrfToken()
  document.cookie = 'beautybook_csrf=; Max-Age=0; path=/'
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('API client', () => {
  it('fetches a CSRF token, then posts the registration with credentials and the header', async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'csrf-token' }))
      .mockResolvedValueOnce(jsonResponse(USER, 201))

    const user = await authApi.registerCustomer(REGISTER_INPUT)

    expect(user).toEqual(USER)
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(fetchMock.mock.calls[0]?.[0]).toBe('/api/v1/auth/csrf')

    const init = fetchMock.mock.calls[1]?.[1] as RequestInit
    const headers = init.headers as Record<string, string>
    expect(fetchMock.mock.calls[1]?.[0]).toBe('/api/v1/auth/register/customer')
    expect(init.method).toBe('POST')
    expect(init.credentials).toBe('include')
    expect(headers['X-CSRF-Token']).toBe('csrf-token')
    expect(JSON.parse(String(init.body))).toEqual(REGISTER_INPUT)
    expect(localStorage.length).toBe(0)
    expect(sessionStorage.length).toBe(0)
  })

  it('uses the documented login endpoint', async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'csrf-token' }))
      .mockResolvedValueOnce(jsonResponse(USER))

    await authApi.login({ email: 'sara@example.com', password: 'correct horse battery staple' })

    expect(fetchMock.mock.calls[1]?.[0]).toBe('/api/v1/auth/login')
  })

  it('maps the backend error envelope to ApiError', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ csrf_token: 'csrf-token' })).mockResolvedValueOnce(
      jsonResponse(
        {
          error: {
            code: 'EMAIL_ALREADY_REGISTERED',
            message: 'An account with this email already exists. Sign in instead.',
            fields: {},
            request_id: 'request-1',
          },
        },
        409,
      ),
    )

    await expect(authApi.registerCustomer(REGISTER_INPUT)).rejects.toMatchObject({
      status: 409,
      code: 'EMAIL_ALREADY_REGISTERED',
      requestId: 'request-1',
    })
  })

  it('refreshes the CSRF token and retries once after CSRF_INVALID', async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'old-token' }))
      .mockResolvedValueOnce(
        jsonResponse({ error: { code: 'CSRF_INVALID', message: 'Invalid token.', fields: {} } }, 403),
      )
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'new-token' }))
      .mockResolvedValueOnce(jsonResponse(USER, 201))

    await authApi.registerCustomer(REGISTER_INPUT)

    expect(fetchMock).toHaveBeenCalledTimes(4)
    const retried = fetchMock.mock.calls[3]?.[1] as RequestInit
    expect((retried.headers as Record<string, string>)['X-CSRF-Token']).toBe('new-token')
  })

  it('never retries a non-CSRF 403', async () => {
    const forbidden = new ApiError(403, 'FORBIDDEN', 'Not allowed.', {})
    fetchMock.mockResolvedValueOnce(jsonResponse({ csrf_token: 'csrf-token' })).mockResolvedValueOnce(
      jsonResponse({ error: { code: 'FORBIDDEN', message: 'Not allowed.', fields: {} } }, 403),
    )

    await expect(authApi.registerCustomer(REGISTER_INPUT)).rejects.toMatchObject({
      status: forbidden.status,
      code: forbidden.code,
    })
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
})

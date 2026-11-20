/**
 * Small typed HTTP client for the BeautyBook API.
 *
 * Responsibilities:
 * - always send cookies (`credentials: "include"`);
 * - bootstrap and refresh the CSRF token before state-changing requests;
 * - retry once after `CSRF_INVALID`;
 * - convert the backend error envelope into a typed `ApiError`.
 *
 * The CSRF token is kept in memory only. It is deliberately not written to localStorage or
 * sessionStorage, and the session cookie stays HttpOnly.
 */

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL
export const API_BASE_URL =
  typeof configuredBaseUrl === 'string' && configuredBaseUrl.length > 0
    ? configuredBaseUrl
    : '/api/v1'

const CSRF_COOKIE_NAME = 'beautybook_csrf'
const CSRF_HEADER_NAME = 'X-CSRF-Token'
const NETWORK_ERROR_MESSAGE = 'Could not reach the server. Check your connection and try again.'

export interface ApiErrorEnvelope {
  error: {
    code: string
    message: string
    fields?: Record<string, string>
    request_id?: string
  }
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly fields: Record<string, string>
  readonly requestId: string | undefined

  constructor(
    status: number,
    code: string,
    message: string,
    fields: Record<string, string> = {},
    requestId?: string,
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.fields = fields
    this.requestId = requestId
  }
}

let csrfToken: string | null = null
let csrfRequest: Promise<string> | null = null

/** Clear the in-memory token, for example after logout or in tests. */
export function clearCsrfToken(): void {
  csrfToken = null
}

function readCookie(name: string): string | null {
  const prefix = `${name}=`
  for (const part of document.cookie.split(';')) {
    const trimmed = part.trim()
    if (trimmed.startsWith(prefix)) {
      return decodeURIComponent(trimmed.slice(prefix.length))
    }
  }
  return null
}

async function toApiError(response: Response): Promise<ApiError> {
  let envelope: ApiErrorEnvelope | null = null
  try {
    envelope = (await response.json()) as ApiErrorEnvelope
  } catch {
    envelope = null
  }

  const error = envelope?.error
  return new ApiError(
    response.status,
    error?.code ?? 'HTTP_ERROR',
    error?.message ?? `The request failed (${response.status}).`,
    error?.fields ?? {},
    error?.request_id,
  )
}

async function fetchCsrfToken(force = false): Promise<string> {
  if (force) {
    csrfToken = null
  }
  if (csrfToken) {
    return csrfToken
  }
  if (csrfRequest) {
    return csrfRequest
  }

  csrfRequest = (async () => {
    let response: Response
    try {
      response = await fetch(`${API_BASE_URL}/auth/csrf`, {
        credentials: 'include',
        headers: { Accept: 'application/json' },
      })
    } catch {
      throw new ApiError(0, 'NETWORK_ERROR', NETWORK_ERROR_MESSAGE)
    }

    if (!response.ok) {
      throw await toApiError(response)
    }

    const body = (await response.json()) as { csrf_token?: unknown }
    if (typeof body.csrf_token !== 'string' || body.csrf_token.length === 0) {
      throw new ApiError(
        response.status,
        'INVALID_CSRF_RESPONSE',
        'The server did not return a usable security token.',
      )
    }

    csrfToken = body.csrf_token
    return body.csrf_token
  })().finally(() => {
    csrfRequest = null
  })

  return csrfRequest
}

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

interface RequestOptions {
  method?: HttpMethod
  body?: unknown
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method ?? 'GET'
  const isMutation = method !== 'GET'
  const headers: Record<string, string> = { Accept: 'application/json' }

  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }
  if (isMutation) {
    headers[CSRF_HEADER_NAME] = await fetchCsrfToken()
  }

  const send = (): Promise<Response> =>
    fetch(`${API_BASE_URL}${path}`, {
      method,
      credentials: 'include',
      headers: { ...headers },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    })

  let response: Response
  try {
    response = await send()
  } catch {
    throw new ApiError(0, 'NETWORK_ERROR', NETWORK_ERROR_MESSAGE)
  }

  if (isMutation && response.status === 403) {
    const error = await toApiError(response)
    if (error.code !== 'CSRF_INVALID') {
      throw error
    }

    headers[CSRF_HEADER_NAME] = await fetchCsrfToken(true)
    try {
      response = await send()
    } catch {
      throw new ApiError(0, 'NETWORK_ERROR', NETWORK_ERROR_MESSAGE)
    }
  }

  if (!response.ok) {
    throw await toApiError(response)
  }

  const rotatedToken = readCookie(CSRF_COOKIE_NAME)
  if (rotatedToken) {
    csrfToken = rotatedToken
  }

  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

export const api = {
  get<T>(path: string): Promise<T> {
    return request<T>(path)
  },
  post<T>(path: string, body: unknown): Promise<T> {
    return request<T>(path, { method: 'POST', body })
  },
}

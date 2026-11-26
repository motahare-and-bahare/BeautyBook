import { api } from './client'

export interface AuthUser {
  id: string
  full_name: string
  email: string
  roles: string[]
  status: string
  created_at: string
}

export interface RegisterCustomerPayload {
  full_name: string
  email: string
  password: string
}

export interface LoginPayload {
  email: string
  password: string
}

export const authApi = {
  registerCustomer(payload: RegisterCustomerPayload): Promise<AuthUser> {
    return api.post<AuthUser>('/auth/register/customer', payload)
  },

  login(payload: LoginPayload): Promise<AuthUser> {
    return api.post<AuthUser>('/auth/login', payload)
  },

  /** The signed-in user, resolved from the HttpOnly session cookie by the server. */
  me(): Promise<AuthUser> {
    return api.get<AuthUser>('/auth/me')
  },
}

import type { AuthUser } from './auth'
import { api } from './client'

/** The administrator list shows the same safe account shape as `/auth/me`. */
export type AdminUser = AuthUser

export interface AdminUserPage {
  items: AdminUser[]
  /** Opaque cursor for the next page; `null` means this is the last page. */
  next_cursor: string | null
}

export interface ListUsersOptions {
  limit?: number
  cursor?: string | null
}

export const DEFAULT_PAGE_SIZE = 20

export const adminApi = {
  /** Admin-only: the server answers 401 when signed out and 403 without the `admin` role. */
  listUsers({ limit = DEFAULT_PAGE_SIZE, cursor = null }: ListUsersOptions = {}): Promise<
    AdminUserPage
  > {
    const params = new URLSearchParams({ limit: String(limit) })
    if (cursor) {
      params.set('cursor', cursor)
    }
    return api.get<AdminUserPage>(`/admin/users?${params.toString()}`)
  },
}

/**
 * The signed-in user, shared by the router guard and the screens.
 *
 * The session itself lives in an HttpOnly cookie, so the only client state is the user the
 * server returns from `GET /auth/me`. Roles are re-read from the backend on every load; the
 * frontend never decides what the server would allow.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

import { authApi, type AuthUser } from '@/services/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const loaded = ref(false)

  let pending: Promise<void> | null = null

  async function load(): Promise<void> {
    try {
      user.value = await authApi.me()
    } catch {
      // A missing or rejected session means "not signed in"; the guard sends the user to login.
      user.value = null
    }
  }

  /** Load the current user once per page load, even if several guards ask for it at once. */
  async function ensureLoaded(): Promise<void> {
    if (loaded.value) {
      return
    }
    pending ??= load().finally(() => {
      loaded.value = true
      pending = null
    })
    return pending
  }

  function hasRole(role: string): boolean {
    return user.value?.roles.includes(role) ?? false
  }

  function setUser(next: AuthUser | null): void {
    user.value = next
    loaded.value = true
  }

  return { user, loaded, load, ensureLoaded, hasRole, setUser }
})

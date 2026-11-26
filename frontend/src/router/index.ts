import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import LoginPage from '@/modules/auth/pages/LoginPage.vue'
import RegisterCustomerPage from '@/modules/auth/pages/RegisterCustomerPage.vue'

const routes = [
  { path: '/', redirect: { name: 'login' } },
  { path: '/login', name: 'login', component: LoginPage },
  { path: '/register', name: 'register', component: RegisterCustomerPage },
  {
    path: '/admin/users',
    name: 'admin-users',
    component: () => import('@/modules/admin/pages/AdminUsersPage.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  { path: '/forbidden', name: 'forbidden', component: () => import('@/modules/auth/pages/ForbiddenPage.vue') },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

/**
 * Authentication and role gate for protected routes.
 *
 * The backend re-checks both the session and the role on every request, so this guard only
 * decides what to render: an unauthenticated visitor is sent to login with a safe return path,
 * and a signed-in user without the required role sees the 403 page.
 */
router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) {
    return true
  }

  const auth = useAuthStore()
  await auth.ensureLoaded()

  if (!auth.user) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  const requiredRoles = (to.meta.roles as string[] | undefined) ?? []
  if (requiredRoles.length > 0 && !requiredRoles.some((role) => auth.hasRole(role))) {
    return { name: 'forbidden' }
  }

  return true
})

export default router

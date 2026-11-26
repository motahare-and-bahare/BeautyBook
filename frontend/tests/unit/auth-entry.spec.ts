import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter, type Router } from 'vue-router'

import AuthPage from '@/modules/auth/pages/AuthPage.vue'
import { authApi } from '@/services/api/auth'

vi.mock('@/services/api/auth', () => ({
  authApi: {
    registerCustomer: vi.fn(),
    login: vi.fn(),
    me: vi.fn(),
  },
}))

const loginMock = vi.mocked(authApi.login)

const PASSWORD = 'correct horse battery staple'
const CUSTOMER = {
  id: '8f14e45f-ea2f-4c1b-9b7a-1f3c2d4e5f60',
  full_name: 'Sara Ahmadi',
  email: 'sara@example.com',
  roles: ['customer'],
  status: 'active',
  created_at: '2026-11-19T10:15:30Z',
}
const ADMIN = { ...CUSTOMER, id: 'a'.repeat(8), full_name: 'Reza Admin', roles: ['admin'] }

const Stub = { template: '<div />' }

function makeRouter(): Router {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', redirect: { name: 'auth' } },
      { path: '/auth', name: 'auth', component: AuthPage },
      { path: '/login', name: 'login', component: Stub },
      { path: '/register', name: 'register', component: Stub },
      { path: '/admin', name: 'admin', component: Stub },
      { path: '/account', name: 'account', component: Stub },
    ],
  })
}

async function mountAt(path: string): Promise<{ wrapper: VueWrapper; router: Router }> {
  const router = makeRouter()
  await router.push(path)
  await router.isReady()
  const wrapper = mount(AuthPage, { global: { plugins: [router] } })
  return { wrapper, router }
}

async function signIn(wrapper: VueWrapper): Promise<void> {
  await wrapper.get('#email').setValue(CUSTOMER.email)
  await wrapper.get('#password').setValue(PASSWORD)
  await wrapper.get('form').trigger('submit')
  await flushPromises()
}

beforeEach(() => {
  loginMock.mockReset()
})

describe('auth entry page', () => {
  it('shows the sign-in form by default', async () => {
    const { wrapper, router } = await mountAt('/auth')

    expect(router.currentRoute.value.path).toBe('/auth')
    expect(wrapper.find('#email').exists()).toBe(true)
    expect(wrapper.find('#password').exists()).toBe(true)
    expect(wrapper.find('#full-name').exists()).toBe(false)
  })

  it('shows the sign-up form for ?mode=register', async () => {
    const { wrapper } = await mountAt('/auth?mode=register')

    expect(wrapper.find('#full-name').exists()).toBe(true)
    expect(wrapper.find('#password').exists()).toBe(true)
  })

  it('falls back to sign-in for an unknown mode', async () => {
    const { wrapper } = await mountAt('/auth?mode=nonsense')

    expect(wrapper.find('#email').exists()).toBe(true)
    expect(wrapper.find('#full-name').exists()).toBe(false)
  })

  it('exposes the active tab through aria-current and real links', async () => {
    const { wrapper } = await mountAt('/auth?mode=register')

    const tabs = wrapper.findAll('[data-testid="auth-tab"]')
    expect(tabs).toHaveLength(2)

    const active = tabs.filter((tab) => tab.attributes('aria-current') === 'page')
    expect(active).toHaveLength(1)
    expect(active[0]!.text()).toContain('ثبت‌نام')

    const signInTab = tabs[0]!
    expect(signInTab.attributes('href')).toBe('/auth')
    expect(tabs[1]!.attributes('href')).toBe('/auth?mode=register')
  })

  it('sends normalised credentials through the shared sign-in form', async () => {
    loginMock.mockResolvedValue(CUSTOMER)
    const { wrapper } = await mountAt('/auth')

    await wrapper.get('#email').setValue('  Sara@Example.COM ')
    await wrapper.get('#password').setValue(PASSWORD)
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(loginMock).toHaveBeenCalledWith({ email: 'sara@example.com', password: PASSWORD })
    expect(wrapper.text()).toContain('Sara')
    expect(wrapper.text()).not.toContain('customer')
  })

  it('honours a safe redirect after sign-in', async () => {
    loginMock.mockResolvedValue(CUSTOMER)
    const { wrapper, router } = await mountAt('/auth?redirect=/account')

    await signIn(wrapper)

    expect(router.currentRoute.value.path).toBe('/account')
  })

  it('ignores an external redirect after sign-in', async () => {
    loginMock.mockResolvedValue(CUSTOMER)
    const { wrapper, router } = await mountAt('/auth?redirect=//evil.example/steal')

    await signIn(wrapper)

    expect(router.currentRoute.value.path).toBe('/auth')
  })

  it('sends an administrator to the admin panel when no redirect is given', async () => {
    loginMock.mockResolvedValue(ADMIN)
    const { wrapper, router } = await mountAt('/auth')

    await signIn(wrapper)

    expect(router.currentRoute.value.path).toBe('/admin')
  })

  it('keeps a customer on the entry page when no redirect is given', async () => {
    loginMock.mockResolvedValue(CUSTOMER)
    const { wrapper, router } = await mountAt('/auth')

    await signIn(wrapper)

    expect(router.currentRoute.value.path).toBe('/auth')
  })
})

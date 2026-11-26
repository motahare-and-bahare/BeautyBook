import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import AdminSidebar from '@/modules/admin/components/AdminSidebar.vue'
import AdminDashboardPage from '@/modules/admin/pages/AdminDashboardPage.vue'
import ForbiddenPage from '@/modules/auth/pages/ForbiddenPage.vue'

const Stub = { template: '<div />' }

async function mountSidebar(path: string, roles: string[]) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/admin', name: 'admin-dashboard', component: Stub },
      { path: '/admin/users', name: 'admin-users', component: Stub },
      { path: '/forbidden', name: 'forbidden', component: Stub },
    ],
  })
  await router.push(path)
  await router.isReady()

  return mount(AdminSidebar, {
    props: { roles },
    global: { plugins: [router] },
  })
}

describe('admin sidebar', () => {
  it('lists administration sections for an administrator', async () => {
    const wrapper = await mountSidebar('/admin', ['admin'])

    const items = wrapper.findAll('[data-testid="admin-nav-item"]')
    // Only the dashboard exists today; the rest are marked as coming soon, not linked.
    expect(items).toHaveLength(1)
    expect(wrapper.text()).toContain('داشبورد')
    expect(wrapper.text()).toContain('کاربران')
    expect(wrapper.text()).toContain('سالن‌ها')
    expect(wrapper.text()).toContain('تنظیمات')
  })

  it('marks only the active section with aria-current', async () => {
    const wrapper = await mountSidebar('/admin', ['admin'])

    const active = wrapper
      .findAll('[data-testid="admin-nav-item"]')
      .filter((item) => item.attributes('aria-current') === 'page')

    expect(active).toHaveLength(1)
    expect(active[0]!.text()).toContain('داشبورد')
  })

  it('does not expose sections to a non-administrator', async () => {
    const wrapper = await mountSidebar('/admin', ['customer'])

    expect(wrapper.findAll('[data-testid="admin-nav-item"]')).toHaveLength(0)
    expect(wrapper.text()).toContain('دسترسی')
  })

  it('marks not-yet-implemented sections as unavailable instead of linking nowhere', async () => {
    const wrapper = await mountSidebar('/admin', ['admin'])

    const soon = wrapper.findAll('[data-testid="admin-nav-soon"]')
    expect(soon.length).toBeGreaterThan(0)
    for (const item of soon) {
      expect(item.attributes('aria-disabled')).toBe('true')
      expect(item.attributes('href')).toBeUndefined()
    }
    expect(wrapper.text()).toContain('به‌زودی')
  })
})

describe('admin dashboard', () => {
  it('states honestly that administration features are not implemented', () => {
    const wrapper = mount(AdminDashboardPage)

    expect(wrapper.text()).toContain('پنل مدیریت')
    expect(wrapper.text()).toContain('هنوز')
    expect(wrapper.findAll('[data-testid="admin-stat"]')).toHaveLength(0)
  })
})

describe('forbidden page', () => {
  it('names the required role in Persian and offers a way back', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/forbidden', name: 'forbidden', component: ForbiddenPage },
        { path: '/auth', name: 'auth', component: Stub },
      ],
    })
    await router.push('/forbidden?required=admin')
    await router.isReady()

    const wrapper = mount(ForbiddenPage, { global: { plugins: [router] } })

    expect(wrapper.text()).toContain('دسترسی')
    expect(wrapper.text()).toContain('مدیر')
    expect(wrapper.get('[data-testid="forbidden-back"]').attributes('href')).toBe('/auth')
  })
})

import { flushPromises, mount, RouterLinkStub, type VueWrapper } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import AdminUsersPage from '@/modules/admin/pages/AdminUsersPage.vue'
import { adminApi, DEFAULT_PAGE_SIZE, type AdminUser } from '@/services/api/admin'
import { ApiError } from '@/services/api/client'

vi.mock('@/services/api/admin', async () => {
  const actual = await vi.importActual<typeof import('@/services/api/admin')>('@/services/api/admin')
  return { ...actual, adminApi: { listUsers: vi.fn() } }
})

const listUsersMock = vi.mocked(adminApi.listUsers)

const ADMIN: AdminUser = {
  id: '8f14e45f-ea2f-4c1b-9b7a-1f3c2d4e5f60',
  full_name: 'Mina Admin',
  email: 'admin@beautybook.com',
  roles: ['admin', 'customer'],
  status: 'active',
  created_at: '2026-11-25T10:15:30Z',
}

const OWNER: AdminUser = {
  id: '3c59dc48-8f14-4c1b-9b7a-0f3c2d4e5f61',
  full_name: 'Sara Owner',
  email: 'sara@example.com',
  roles: ['customer', 'salon_owner'],
  status: 'pending_approval',
  created_at: '2026-11-24T09:00:00Z',
}

function mountPage(): VueWrapper {
  return mount(AdminUsersPage, {
    global: { stubs: { RouterLink: RouterLinkStub } },
  })
}

async function mountLoaded(): Promise<VueWrapper> {
  const wrapper = mountPage()
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  listUsersMock.mockReset()
})

describe('admin user list page', () => {
  it('shows each account with Persian role and status labels', async () => {
    listUsersMock.mockResolvedValue({ items: [OWNER, ADMIN], next_cursor: null })

    const wrapper = await mountLoaded()

    expect(listUsersMock).toHaveBeenCalledWith({ limit: DEFAULT_PAGE_SIZE })
    const rows = wrapper.findAll('tbody tr')
    expect(rows).toHaveLength(2)
    expect(rows[0]?.text()).toContain('sara@example.com')
    expect(rows[0]?.text()).toContain('سالن‌دار')
    expect(rows[0]?.text()).toContain('در انتظار تأیید')
    expect(rows[1]?.text()).toContain('admin@beautybook.com')
    expect(rows[1]?.text()).toContain('مدیر')

    // Enum values stay in the API; the page renders Persian labels.
    expect(wrapper.text()).not.toContain('salon_owner')
    expect(wrapper.text()).not.toContain('pending_approval')
  })

  it('shows a Persian empty state when there are no accounts', async () => {
    listUsersMock.mockResolvedValue({ items: [], next_cursor: null })

    const wrapper = await mountLoaded()

    expect(wrapper.text()).toContain('هنوز هیچ کاربری ثبت نشده است.')
    expect(wrapper.find('table').exists()).toBe(false)
  })

  it('shows a Persian error state and can retry', async () => {
    listUsersMock.mockRejectedValueOnce(new ApiError(403, 'FORBIDDEN', 'Not allowed.', {}))
    const wrapper = await mountLoaded()

    expect(wrapper.get('[role="alert"]').text()).toContain(
      'دسترسی به فهرست کاربران فقط برای مدیران مجاز است.',
    )

    listUsersMock.mockResolvedValueOnce({ items: [ADMIN], next_cursor: null })
    await wrapper.get('.retry').trigger('click')
    await flushPromises()

    expect(listUsersMock).toHaveBeenCalledTimes(2)
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    expect(wrapper.findAll('tbody tr')).toHaveLength(1)
  })

  it('loads the next page with the cursor from the server', async () => {
    listUsersMock
      .mockResolvedValueOnce({ items: [OWNER], next_cursor: 'cursor-2' })
      .mockResolvedValueOnce({ items: [ADMIN], next_cursor: null })

    const wrapper = await mountLoaded()
    expect(wrapper.findAll('tbody tr')).toHaveLength(1)

    await wrapper.get('.more button').trigger('click')
    await flushPromises()

    expect(listUsersMock).toHaveBeenLastCalledWith({
      limit: DEFAULT_PAGE_SIZE,
      cursor: 'cursor-2',
    })
    expect(wrapper.findAll('tbody tr')).toHaveLength(2)
    expect(wrapper.find('.more').exists()).toBe(false)
  })

  it('does not offer a next page when the server says there is none', async () => {
    listUsersMock.mockResolvedValue({ items: [ADMIN], next_cursor: null })

    const wrapper = await mountLoaded()

    expect(wrapper.find('.more').exists()).toBe(false)
  })
})

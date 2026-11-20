import { flushPromises, mount, RouterLinkStub, type VueWrapper } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import LoginPage from '@/modules/auth/pages/LoginPage.vue'
import { authApi } from '@/services/api/auth'
import { ApiError } from '@/services/api/client'

vi.mock('@/services/api/auth', () => ({
  authApi: {
    registerCustomer: vi.fn(),
    login: vi.fn(),
  },
}))

const loginMock = vi.mocked(authApi.login)

const PASSWORD = 'correct horse battery staple'
const USER = {
  id: '8f14e45f-ea2f-4c1b-9b7a-1f3c2d4e5f60',
  full_name: 'Sara Ahmadi',
  email: 'sara@example.com',
  roles: ['customer'],
  status: 'active',
  created_at: '2026-11-19T10:15:30Z',
}

function mountPage(): VueWrapper {
  return mount(LoginPage, {
    global: { stubs: { RouterLink: RouterLinkStub } },
  })
}

async function submit(wrapper: VueWrapper): Promise<void> {
  await wrapper.get('form').trigger('submit')
  await flushPromises()
}

beforeEach(() => {
  loginMock.mockReset()
})

describe('login page', () => {
  it('sends normalized credentials to the login API and shows the user in Persian', async () => {
    loginMock.mockResolvedValue(USER)
    const wrapper = mountPage()

    await wrapper.get('#email').setValue('  Sara@Example.COM ')
    await wrapper.get('#password').setValue(PASSWORD)
    await submit(wrapper)

    expect(loginMock).toHaveBeenCalledWith({
      email: 'sara@example.com',
      password: PASSWORD,
    })
    expect(wrapper.text()).toContain('خوش آمدید، Sara')
    expect(wrapper.text()).toContain('sara@example.com')
    // Roles and status are shown through Persian labels, never as raw enum values.
    expect(wrapper.text()).toContain('مشتری')
    expect(wrapper.text()).toContain('فعال')
    expect(wrapper.text()).not.toContain('customer')
    expect(wrapper.text()).not.toContain('active')
  })

  it('renders Persian labels and keeps Latin input content left to right', () => {
    const wrapper = mountPage()

    expect(wrapper.text()).toContain('رمز عبور')
    expect(wrapper.get('#email').attributes('dir')).toBe('ltr')
    expect(wrapper.get('#password').attributes('dir')).toBe('ltr')
    expect(wrapper.get('#email').attributes('type')).toBe('email')
    expect(wrapper.findAll('label')).toHaveLength(2)
  })

  it('requires both fields with Persian messages', async () => {
    const wrapper = mountPage()

    await submit(wrapper)

    expect(loginMock).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('ایمیل خود را وارد کنید.')
    expect(wrapper.text()).toContain('رمز عبور را وارد کنید.')
  })

  it('shows the generic invalid-credentials message in Persian', async () => {
    loginMock.mockRejectedValue(
      new ApiError(401, 'INVALID_CREDENTIALS', 'Invalid email or password.', {}),
    )
    const wrapper = mountPage()

    await wrapper.get('#email').setValue('sara@example.com')
    await wrapper.get('#password').setValue(PASSWORD)
    await submit(wrapper)

    expect(wrapper.get('[role="alert"]').text()).toContain('ایمیل یا رمز عبور نادرست است.')
  })

  it.each([
    [
      'ACCOUNT_PENDING_APPROVAL',
      'درخواست سالن‌داری شما هنوز در حال بررسی است. پس از تأیید می‌توانید وارد شوید.',
    ],
    [
      'ACCOUNT_REJECTED',
      'این حساب تأیید نشده است. اگر فکر می‌کنید اشتباهی رخ داده با پشتیبانی تماس بگیرید.',
    ],
    ['ACCOUNT_SUSPENDED', 'این حساب تعلیق شده است. برای کمک با پشتیبانی تماس بگیرید.'],
  ])('explains the blocked account status %s in Persian', async (code, message) => {
    loginMock.mockRejectedValue(new ApiError(403, code, 'Blocked.', {}))
    const wrapper = mountPage()

    await wrapper.get('#email').setValue('sara@example.com')
    await wrapper.get('#password').setValue(PASSWORD)
    await submit(wrapper)

    expect(wrapper.get('[role="alert"]').text()).toContain(message)
  })

  it('translates a backend validation field error instead of showing English', async () => {
    loginMock.mockRejectedValue(
      new ApiError(422, 'VALIDATION_ERROR', 'The request contains invalid values.', {
        email: 'Enter a valid email address.',
      }),
    )
    const wrapper = mountPage()

    await wrapper.get('#email').setValue('not-an-email')
    await wrapper.get('#password').setValue(PASSWORD)
    await submit(wrapper)

    expect(wrapper.text()).toContain('ایمیل معتبر وارد کنید.')
    expect(wrapper.text()).not.toContain('Enter a valid email address.')
  })

  it('shows a Persian message when the server cannot be reached', async () => {
    loginMock.mockRejectedValue(new Error('network down'))
    const wrapper = mountPage()

    await wrapper.get('#email').setValue('sara@example.com')
    await wrapper.get('#password').setValue(PASSWORD)
    await submit(wrapper)

    expect(wrapper.get('[role="alert"]').text()).toContain(
      'ارتباط با سرور برقرار نشد. اتصال خود را بررسی کنید و دوباره تلاش کنید.',
    )
  })
})

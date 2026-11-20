import { flushPromises, mount, RouterLinkStub, type VueWrapper } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import RegisterCustomerPage from '@/modules/auth/pages/RegisterCustomerPage.vue'
import { authApi } from '@/services/api/auth'
import { ApiError } from '@/services/api/client'

vi.mock('@/services/api/auth', () => ({
  authApi: {
    registerCustomer: vi.fn(),
    login: vi.fn(),
  },
}))

const registerMock = vi.mocked(authApi.registerCustomer)

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
  return mount(RegisterCustomerPage, {
    global: { stubs: { RouterLink: RouterLinkStub } },
  })
}

async function fillForm(wrapper: VueWrapper, values: Record<string, string>): Promise<void> {
  if (values.full_name !== undefined) await wrapper.get('#full-name').setValue(values.full_name)
  if (values.email !== undefined) await wrapper.get('#email').setValue(values.email)
  if (values.password !== undefined) await wrapper.get('#password').setValue(values.password)
  if (values.confirmPassword !== undefined) {
    await wrapper.get('#confirm-password').setValue(values.confirmPassword)
  }
}

async function submit(wrapper: VueWrapper): Promise<void> {
  await wrapper.get('form').trigger('submit')
  await flushPromises()
}

beforeEach(() => {
  registerMock.mockReset()
})

describe('customer registration page', () => {
  it('sends the real payload and shows the signed-in customer in Persian', async () => {
    registerMock.mockResolvedValue(USER)
    const wrapper = mountPage()

    await fillForm(wrapper, {
      full_name: '  Sara Ahmadi  ',
      email: '  Sara@Example.COM ',
      password: PASSWORD,
      confirmPassword: PASSWORD,
    })
    await submit(wrapper)

    expect(registerMock).toHaveBeenCalledWith({
      full_name: 'Sara Ahmadi',
      email: 'sara@example.com',
      password: PASSWORD,
    })
    expect(wrapper.text()).toContain('خوش آمدید، Sara')
    expect(wrapper.text()).toContain('sara@example.com')
    expect(wrapper.text()).toContain('مشتری')
    expect(wrapper.text()).not.toContain('customer')
  })

  it('renders Persian labels and keeps Latin input content left to right', () => {
    const wrapper = mountPage()

    expect(wrapper.text()).toContain('نام کامل')
    expect(wrapper.text()).toContain('تکرار رمز عبور')
    expect(wrapper.get('#email').attributes('dir')).toBe('ltr')
    expect(wrapper.get('#password').attributes('dir')).toBe('ltr')
    expect(wrapper.get('#confirm-password').attributes('dir')).toBe('ltr')
    expect(wrapper.findAll('label')).toHaveLength(4)
  })

  it('offers no administrator or role choice', async () => {
    const wrapper = mountPage()

    expect(wrapper.findAll('option')).toHaveLength(0)
    expect(wrapper.find('[name="role"]').exists()).toBe(false)
    expect(wrapper.find('[name="status"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('حساب مدیر هرگز از اینجا ساخته نمی‌شود')
  })

  it('blocks an empty submit and explains each field in Persian', async () => {
    const wrapper = mountPage()

    await submit(wrapper)

    expect(registerMock).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('نام کامل خود را وارد کنید.')
    expect(wrapper.text()).toContain('ایمیل خود را وارد کنید.')
    expect(wrapper.text()).toContain('رمزی با حداقل ۱۲ کاراکتر وارد کنید.')
  })

  it('rejects a short password and a mismatched confirmation', async () => {
    const wrapper = mountPage()

    await fillForm(wrapper, {
      full_name: 'Sara Ahmadi',
      email: 'sara@example.com',
      password: 'short',
      confirmPassword: 'different',
    })
    await submit(wrapper)

    expect(registerMock).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('رمز عبور باید بین ۱۲ تا ۱۲۸ کاراکتر باشد.')
    expect(wrapper.text()).toContain('رمزهای عبور یکسان نیستند.')
  })

  it('shows the duplicate-email message from the backend in Persian', async () => {
    registerMock.mockRejectedValue(
      new ApiError(
        409,
        'EMAIL_ALREADY_REGISTERED',
        'An account with this email already exists. Sign in instead.',
        {},
      ),
    )
    const wrapper = mountPage()

    await fillForm(wrapper, {
      full_name: 'Sara Ahmadi',
      email: 'sara@example.com',
      password: PASSWORD,
      confirmPassword: PASSWORD,
    })
    await submit(wrapper)

    expect(wrapper.get('[role="alert"]').text()).toContain('حسابی با این ایمیل از قبل وجود دارد')
    expect(wrapper.text()).toContain('وارد شوید')
  })

  it('maps backend field errors onto the form in Persian', async () => {
    registerMock.mockRejectedValue(
      new ApiError(422, 'VALIDATION_ERROR', 'The request contains invalid values.', {
        email: 'Enter a valid email address.',
      }),
    )
    const wrapper = mountPage()

    await fillForm(wrapper, {
      full_name: 'Sara Ahmadi',
      email: 'sara@example.com',
      password: PASSWORD,
      confirmPassword: PASSWORD,
    })
    await submit(wrapper)

    expect(wrapper.text()).toContain('ایمیل معتبر وارد کنید.')
    expect(wrapper.text()).not.toContain('Enter a valid email address.')
  })
})

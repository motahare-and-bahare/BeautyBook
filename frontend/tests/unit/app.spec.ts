import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { describe, expect, it } from 'vitest'

import App from '@/app/App.vue'
import router from '@/router'

describe('application shell', () => {
  it('renders the login page for the login route', async () => {
    await router.push('/login')
    await router.isReady()

    const wrapper = mount(App, { global: { plugins: [createPinia(), router] } })

    expect(wrapper.get('h1').text()).toBe('ورود به بیوتی‌بوک')
  })

  it('redirects the root route to login', async () => {
    await router.push('/')
    await router.isReady()

    expect(router.currentRoute.value.name).toBe('login')
  })
})

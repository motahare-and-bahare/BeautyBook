<script setup lang="ts">
import { computed, watchEffect } from 'vue'
import { RouterLink, useRoute, useRouter, type RouteLocationRaw } from 'vue-router'

import AuthLayout from '@/modules/auth/components/AuthLayout.vue'
import LoginForm from '@/modules/auth/components/LoginForm.vue'
import RegisterCustomerForm from '@/modules/auth/components/RegisterCustomerForm.vue'
import type { AuthUser } from '@/services/api/auth'
import { safeRedirect } from '@/utils/redirect'

type Mode = 'login' | 'register'

const route = useRoute()
const router = useRouter()

function firstValue(value: unknown): string | undefined {
  return Array.isArray(value) ? (value[0] as string | undefined) : (value as string | undefined)
}

const mode = computed<Mode>(() =>
  firstValue(route.query.mode) === 'register' ? 'register' : 'login',
)

function tabTarget(target: Mode): RouteLocationRaw {
  const redirect = firstValue(route.query.redirect)

  return {
    name: 'auth',
    query: {
      ...(target === 'register' ? { mode: 'register' } : {}),
      ...(redirect ? { redirect } : {}),
    },
  }
}

const copy = computed(() =>
  mode.value === 'register'
    ? {
        eyebrow: 'ثبت‌نام مشتری',
        title: 'ساخت حساب مشتری',
        subtitle:
          'اطلاعات خود را یک‌بار ذخیره کنید، سپس سالن‌های معتبر را رزرو کنید و همهٔ نوبت‌ها را یک‌جا داشته باشید.',
      }
    : {
        eyebrow: 'خوش آمدید',
        title: 'ورود به بیوتی‌بوک',
        subtitle:
          'با همان ایمیل و رمزی وارد شوید که ثبت‌نام کردید. حساب‌های مشتری و سالن‌داران تأییدشده می‌توانند وارد شوند.',
      },
)

watchEffect(() => {
  document.title = `${copy.value.title} | BeautyBook`
})

function handleAuthenticated(user: AuthUser): void {
  const fallback = user.roles.includes('admin') ? '/admin' : ''
  const target = safeRedirect(firstValue(route.query.redirect), fallback)

  if (target) {
    void router.push(target)
  }
}
</script>

<template>
  <AuthLayout :eyebrow="copy.eyebrow" :title="copy.title" :subtitle="copy.subtitle">
    <nav class="auth-tabs" aria-label="ورود و ثبت‌نام">
      <RouterLink
        data-testid="auth-tab"
        class="auth-tab"
        :to="tabTarget('login')"
        :aria-current="mode === 'login' ? 'page' : undefined"
      >
        ورود
      </RouterLink>
      <RouterLink
        data-testid="auth-tab"
        class="auth-tab"
        :to="tabTarget('register')"
        :aria-current="mode === 'register' ? 'page' : undefined"
      >
        ثبت‌نام
      </RouterLink>
    </nav>

    <LoginForm v-if="mode === 'login'" @authenticated="handleAuthenticated" />
    <RegisterCustomerForm v-else @authenticated="handleAuthenticated" />

    <template #footer>
      <p>
        سالن‌دار هستید؟ درخواست سالن‌داری جداگانه بررسی و تأیید می‌شود.
      </p>
    </template>
  </AuthLayout>
</template>

<style scoped>
.auth-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-1);
  padding: var(--space-1);
  margin-top: var(--space-5);
  background: #f8f1f3;
  border-radius: var(--radius-md);
}

.auth-tab {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 2.5rem;
  color: var(--color-text-muted);
  border-radius: calc(var(--radius-md) - 2px);
  font-size: var(--text-sm);
  font-weight: 700;
  text-decoration: none;
}

.auth-tab:focus-visible {
  outline: 2px solid var(--color-primary-strong);
  outline-offset: 2px;
}

.auth-tab[aria-current='page'] {
  color: var(--color-primary-strong);
  background: #fff;
  box-shadow: 0 1px 3px rgb(15 23 42 / 12%);
}
</style>

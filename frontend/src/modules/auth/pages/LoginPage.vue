<script setup lang="ts">
import { computed, nextTick, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'

import AuthLayout from '@/modules/auth/components/AuthLayout.vue'
import FormField from '@/modules/auth/components/FormField.vue'
import { fieldErrorLabel, roleLabels, statusLabel } from '@/modules/auth/labels'
import { authApi, type AuthUser } from '@/services/api/auth'
import { ApiError } from '@/services/api/client'

type FieldName = 'email' | 'password'

const form = reactive({
  email: '',
  password: '',
})

const errors = reactive<Record<FieldName, string>>({
  email: '',
  password: '',
})

const formElement = ref<HTMLFormElement | null>(null)
const user = ref<AuthUser | null>(null)
const formError = ref('')
const submitting = ref(false)

const firstName = computed(() => user.value?.full_name.trim().split(/\s+/)[0] ?? '')

function clearErrors(): void {
  errors.email = ''
  errors.password = ''
}

function validate(): boolean {
  clearErrors()
  let valid = true

  const email = form.email.trim()
  if (!email) {
    errors.email = 'ایمیل خود را وارد کنید.'
    valid = false
  } else if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    errors.email = 'ایمیل معتبر وارد کنید.'
    valid = false
  }

  if (!form.password) {
    errors.password = 'رمز عبور را وارد کنید.'
    valid = false
  }

  return valid
}

async function focusFirstInvalid(): Promise<void> {
  await nextTick()
  formElement.value?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus()
}

function loginMessage(error: ApiError): string {
  switch (error.code) {
    case 'INVALID_CREDENTIALS':
      return 'ایمیل یا رمز عبور نادرست است.'
    case 'ACCOUNT_PENDING_APPROVAL':
      return 'درخواست سالن‌داری شما هنوز در حال بررسی است. پس از تأیید می‌توانید وارد شوید.'
    case 'ACCOUNT_REJECTED':
      return 'این حساب تأیید نشده است. اگر فکر می‌کنید اشتباهی رخ داده با پشتیبانی تماس بگیرید.'
    case 'ACCOUNT_SUSPENDED':
      return 'این حساب تعلیق شده است. برای کمک با پشتیبانی تماس بگیرید.'
    case 'CSRF_INVALID':
      return 'توکن امنیتی شما منقضی شده است. لطفاً دوباره تلاش کنید.'
    case 'VALIDATION_ERROR':
      return 'فیلدهای مشخص‌شده را بررسی کنید و دوباره تلاش کنید.'
    default:
      return 'خطایی رخ داد. لطفاً دوباره تلاش کنید.'
  }
}

function applyError(error: unknown): void {
  if (!(error instanceof ApiError)) {
    formError.value = 'ارتباط با سرور برقرار نشد. اتصال خود را بررسی کنید و دوباره تلاش کنید.'
    return
  }

  for (const [field, message] of Object.entries(error.fields)) {
    if (field === 'email' || field === 'password') {
      // Backend messages are English; render the Persian text for the known field instead.
      errors[field] = fieldErrorLabel(field, message)
    }
  }

  formError.value = loginMessage(error)
}

async function submit(): Promise<void> {
  formError.value = ''

  if (!validate()) {
    await focusFirstInvalid()
    return
  }

  submitting.value = true
  try {
    user.value = await authApi.login({
      email: form.email.trim().toLowerCase(),
      password: form.password,
    })
  } catch (error) {
    applyError(error)
    await focusFirstInvalid()
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AuthLayout
    eyebrow="خوش آمدید"
    title="ورود به بیوتی‌بوک"
    subtitle="با همان ایمیل و رمزی وارد شوید که ثبت‌نام کردید. حساب‌های مشتری و سالن‌داران تأییدشده می‌توانند وارد شوند."
  >
    <section v-if="user" class="success" role="status" aria-live="polite">
      <span class="success-icon" aria-hidden="true">✓</span>
      <h2>خوش آمدید، {{ firstName }}.</h2>
      <p>
        شما با <strong dir="ltr">{{ user.email }}</strong> وارد شده‌اید.
      </p>

      <dl class="status-list">
        <div>
          <dt>نقش‌ها</dt>
          <dd>{{ roleLabels(user.roles) }}</dd>
        </div>
        <div>
          <dt>وضعیت</dt>
          <dd>{{ statusLabel(user.status) }}</dd>
        </div>
      </dl>

      <p class="success-note">داشبورد حساب در مرحلهٔ بعدی فرانت‌اند اضافه می‌شود.</p>
    </section>

    <template v-else>
      <div v-if="formError" class="form-alert" role="alert">
        {{ formError }}
      </div>

      <form
        ref="formElement"
        class="form"
        novalidate
        :aria-busy="submitting"
        @submit.prevent="submit"
      >
        <FormField
          id="email"
          v-model="form.email"
          label="ایمیل"
          type="email"
          dir="ltr"
          autocomplete="email"
          :error="errors.email"
          required
        />

        <FormField
          id="password"
          v-model="form.password"
          label="رمز عبور"
          type="password"
          dir="ltr"
          autocomplete="current-password"
          :error="errors.password"
          required
        />

        <button class="submit" type="submit" :disabled="submitting">
          <span v-if="submitting" class="spinner" aria-hidden="true"></span>
          {{ submitting ? 'در حال ورود…' : 'ورود' }}
        </button>

        <p class="account-note">
          درخواست‌های سالن‌داری که در انتظار تأیید هستند، تا زمان تأیید مدیر نمی‌توانند وارد شوند.
        </p>
      </form>
    </template>

    <template #footer>
      <p v-if="!user">
        تازه به بیوتی‌بوک آمده‌اید؟
        <RouterLink to="/register">ساخت حساب مشتری</RouterLink>
      </p>
    </template>
  </AuthLayout>
</template>

<style scoped>
.form {
  display: grid;
  gap: var(--space-4);
  margin-top: var(--space-5);
}

.form-alert {
  padding: var(--space-3) var(--space-4);
  margin-top: var(--space-4);
  color: #7f1d1d;
  background: #fff1f0;
  border: 1px solid #f3c4c0;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  line-height: 1.8;
}

.submit {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  width: 100%;
  min-height: 3rem;
  margin-top: var(--space-1);
  padding: 0.75rem var(--space-4);
  color: #fff;
  background: linear-gradient(135deg, #96385a, #b44f70);
  border: 0;
  border-radius: var(--radius-md);
  box-shadow: 0 6px 16px rgb(150 56 90 / 24%);
  font-weight: 700;
  cursor: pointer;
  transition:
    transform 120ms ease,
    box-shadow 120ms ease,
    opacity 120ms ease;
}

.submit:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 9px 22px rgb(150 56 90 / 30%);
}

.submit:disabled {
  cursor: wait;
  opacity: 0.7;
}

.account-note {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  line-height: 1.8;
  text-align: center;
}

.spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid rgb(255 255 255 / 45%);
  border-top-color: #fff;
  border-radius: 999px;
  animation: spin 700ms linear infinite;
}

.success {
  margin-top: var(--space-5);
  text-align: center;
}

.success h2 {
  margin-bottom: var(--space-2);
  font-size: var(--text-xl);
}

.success p {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  line-height: 1.8;
}

.success-icon {
  display: grid;
  width: 3rem;
  height: 3rem;
  margin: 0 auto var(--space-4);
  place-items: center;
  color: #fff;
  background: var(--color-success);
  border-radius: 999px;
  font-size: var(--text-xl);
  font-weight: 800;
}

.status-list {
  display: grid;
  gap: var(--space-2);
  margin: var(--space-4) 0;
  padding: var(--space-4);
  text-align: start;
  background: #f8f1f3;
  border-radius: var(--radius-md);
}

.status-list div {
  display: flex;
  justify-content: space-between;
  gap: var(--space-4);
}

.status-list dt {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.status-list dd {
  margin: 0;
  font-weight: 700;
}

.success-note {
  margin: 0 !important;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .spinner {
    animation-duration: 1600ms;
  }
}
</style>

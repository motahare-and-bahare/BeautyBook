<script setup lang="ts">
import { computed, nextTick, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'

import FormField from '@/modules/auth/components/FormField.vue'
import { fieldErrorLabel, roleLabels, statusLabel } from '@/modules/auth/labels'
import { authApi, type AuthUser } from '@/services/api/auth'
import { ApiError } from '@/services/api/client'

type FieldName = 'full_name' | 'email' | 'password' | 'confirm_password'

const emit = defineEmits<{ authenticated: [user: AuthUser] }>()

const form = reactive({
  fullName: '',
  email: '',
  password: '',
  confirmPassword: '',
})

const errors = reactive<Record<FieldName, string>>({
  full_name: '',
  email: '',
  password: '',
  confirm_password: '',
})

const formElement = ref<HTMLFormElement | null>(null)
const user = ref<AuthUser | null>(null)
const formError = ref('')
const showLoginLink = ref(false)
const submitting = ref(false)

const firstName = computed(() => user.value?.full_name.trim().split(/\s+/)[0] ?? '')

function clearErrors(): void {
  errors.full_name = ''
  errors.email = ''
  errors.password = ''
  errors.confirm_password = ''
}

function isFieldName(value: string): value is FieldName {
  return (
    value === 'full_name' ||
    value === 'email' ||
    value === 'password' ||
    value === 'confirm_password'
  )
}

function validate(): boolean {
  clearErrors()
  let valid = true

  const name = form.fullName.trim()
  if (!name) {
    errors.full_name = 'نام کامل خود را وارد کنید.'
    valid = false
  } else if (name.length < 2 || name.length > 100) {
    errors.full_name = 'نام باید بین ۲ تا ۱۰۰ کاراکتر باشد.'
    valid = false
  } else if (/[\u0000-\u001f\u007f]/.test(name)) {
    errors.full_name = 'نام شامل کاراکترهای غیرمجاز است.'
    valid = false
  }

  const email = form.email.trim()
  if (!email) {
    errors.email = 'ایمیل خود را وارد کنید.'
    valid = false
  } else if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    errors.email = 'ایمیل معتبر وارد کنید.'
    valid = false
  }

  if (!form.password) {
    errors.password = 'رمزی با حداقل ۱۲ کاراکتر وارد کنید.'
    valid = false
  } else if (form.password.length < 12 || form.password.length > 128) {
    errors.password = 'رمز عبور باید بین ۱۲ تا ۱۲۸ کاراکتر باشد.'
    valid = false
  } else if (!form.password.trim()) {
    errors.password = 'رمز عبور نباید خالی باشد.'
    valid = false
  }

  if (!form.confirmPassword) {
    errors.confirm_password = 'رمز عبور را تکرار کنید.'
    valid = false
  } else if (form.password !== form.confirmPassword) {
    errors.confirm_password = 'رمزهای عبور یکسان نیستند.'
    valid = false
  }

  return valid
}

async function focusFirstInvalid(): Promise<void> {
  await nextTick()
  formElement.value?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus()
}

function registrationMessage(error: ApiError): string {
  switch (error.code) {
    case 'EMAIL_ALREADY_REGISTERED':
      return 'حسابی با این ایمیل از قبل وجود دارد. به جای ثبت‌نام وارد شوید.'
    case 'VALIDATION_ERROR':
      return 'فیلدهای مشخص‌شده را بررسی کنید و دوباره تلاش کنید.'
    case 'CSRF_INVALID':
      return 'توکن امنیتی شما منقضی شده است. لطفاً دوباره تلاش کنید.'
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
    if (isFieldName(field)) {
      // Backend messages are English; render the Persian text for the known field instead.
      errors[field] = fieldErrorLabel(field, message)
    }
  }

  showLoginLink.value = error.code === 'EMAIL_ALREADY_REGISTERED'
  formError.value = registrationMessage(error)
}

async function submit(): Promise<void> {
  formError.value = ''
  showLoginLink.value = false

  if (!validate()) {
    await focusFirstInvalid()
    return
  }

  submitting.value = true
  try {
    user.value = await authApi.registerCustomer({
      full_name: form.fullName.trim(),
      email: form.email.trim().toLowerCase(),
      password: form.password,
    })
    emit('authenticated', user.value)
  } catch (error) {
    applyError(error)
    await focusFirstInvalid()
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section v-if="user" class="success" role="status" aria-live="polite">
    <span class="success-icon" aria-hidden="true">✓</span>
    <h2>خوش آمدید، {{ firstName }}.</h2>
    <p>
      حساب مشتری شما آماده است و با
      <strong dir="ltr">{{ user.email }}</strong>
      وارد شده‌اید.
    </p>

    <dl class="status-list">
      <div>
        <dt>نقش</dt>
        <dd>{{ roleLabels(user.roles) }}</dd>
      </div>
      <div>
        <dt>وضعیت</dt>
        <dd>{{ statusLabel(user.status) }}</dd>
      </div>
    </dl>

    <p class="success-note">داشبورد حساب در مرحلهٔ بعدی فرانت‌اند اضافه می‌شود.</p>
    <RouterLink class="button-secondary" to="/login">بازگشت به ورود</RouterLink>
  </section>

  <template v-else>
    <div v-if="formError" class="form-alert" role="alert">
      <p>{{ formError }}</p>
      <p v-if="showLoginLink" class="form-alert-link">
        <RouterLink to="/login">وارد شوید</RouterLink> با این ایمیل، یا از ایمیل دیگری استفاده کنید.
      </p>
    </div>

    <form
      ref="formElement"
      class="form"
      novalidate
      :aria-busy="submitting"
      @submit.prevent="submit"
    >
      <FormField
        id="full-name"
        v-model="form.fullName"
        label="نام کامل"
        dir="auto"
        autocomplete="name"
        :error="errors.full_name"
        required
      />

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
        autocomplete="new-password"
        hint="حداقل ۱۲ کاراکتر. استفاده از عدد و نماد آزاد است."
        :error="errors.password"
        required
      />

      <FormField
        id="confirm-password"
        v-model="form.confirmPassword"
        label="تکرار رمز عبور"
        type="password"
        dir="ltr"
        autocomplete="new-password"
        :error="errors.confirm_password"
        required
      />

      <button class="submit" type="submit" :disabled="submitting">
        <span v-if="submitting" class="spinner" aria-hidden="true"></span>
        {{ submitting ? 'در حال ساخت حساب…' : 'ساخت حساب مشتری' }}
      </button>

      <p class="privacy-note">فقط حساب مشتری. حساب مدیر هرگز از اینجا ساخته نمی‌شود.</p>
    </form>
  </template>
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

.form-alert p {
  margin: 0;
}

.form-alert-link {
  margin-top: var(--space-2) !important;
}

.form-alert a {
  font-weight: 700;
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

.privacy-note {
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
  margin-bottom: var(--space-4) !important;
}

.button-secondary {
  display: inline-flex;
  min-height: 2.6rem;
  align-items: center;
  justify-content: center;
  padding: 0.6rem var(--space-4);
  color: var(--color-primary-strong);
  background: var(--color-primary-soft);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 700;
  text-decoration: none;
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

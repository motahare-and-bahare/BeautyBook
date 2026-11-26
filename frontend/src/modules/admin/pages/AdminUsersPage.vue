<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { roleLabels, statusLabel } from '@/modules/auth/labels'
import { adminApi, DEFAULT_PAGE_SIZE, type AdminUser } from '@/services/api/admin'
import { ApiError } from '@/services/api/client'

const users = ref<AdminUser[]>([])
const nextCursor = ref<string | null>(null)
const loading = ref(false)
const loadingMore = ref(false)
const failed = ref(false)
const errorText = ref('')
const loaded = ref(false)

const isEmpty = computed(() => loaded.value && users.value.length === 0)

const dateFormatter = new Intl.DateTimeFormat('fa-IR', {
  dateStyle: 'medium',
  timeStyle: 'short',
})

function formatDate(value: string): string {
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? value : dateFormatter.format(parsed)
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === 'FORBIDDEN') {
      return 'دسترسی به فهرست کاربران فقط برای مدیران مجاز است.'
    }
    if (error.code === 'UNAUTHENTICATED') {
      return 'نشست شما معتبر نیست. دوباره وارد شوید.'
    }
    return 'دریافت فهرست کاربران ناموفق بود. دوباره تلاش کنید.'
  }
  return 'ارتباط با سرور برقرار نشد. اتصال خود را بررسی کنید و دوباره تلاش کنید.'
}

async function load(): Promise<void> {
  loading.value = true
  failed.value = false
  try {
    const page = await adminApi.listUsers({ limit: DEFAULT_PAGE_SIZE })
    users.value = page.items
    nextCursor.value = page.next_cursor
    loaded.value = true
  } catch (error) {
    failed.value = true
    errorText.value = errorMessage(error)
  } finally {
    loading.value = false
  }
}

async function loadMore(): Promise<void> {
  if (!nextCursor.value || loadingMore.value) {
    return
  }
  loadingMore.value = true
  failed.value = false
  try {
    const page = await adminApi.listUsers({
      limit: DEFAULT_PAGE_SIZE,
      cursor: nextCursor.value,
    })
    users.value = [...users.value, ...page.items]
    nextCursor.value = page.next_cursor
  } catch (error) {
    failed.value = true
    errorText.value = errorMessage(error)
  } finally {
    loadingMore.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="admin-page">
    <header class="admin-header">
      <RouterLink class="brand" to="/">BeautyBook</RouterLink>
      <p class="eyebrow">پنل مدیریت</p>
      <h1>کاربران</h1>
      <p class="subtitle">
        همهٔ حساب‌های ثبت‌شده، همراه با نقش‌ها و وضعیتشان. این صفحه فقط برای کاربران با نقش مدیر
        در دسترس است.
      </p>
    </header>

    <section class="card" aria-live="polite">
      <div v-if="loading" class="state" role="status">
        <span class="spinner" aria-hidden="true"></span>
        در حال دریافت فهرست کاربران…
      </div>

      <div v-else-if="failed" class="alert" role="alert">
        <p>{{ errorText }}</p>
        <button class="retry" type="button" @click="load">تلاش دوباره</button>
      </div>

      <p v-else-if="isEmpty" class="state">هنوز هیچ کاربری ثبت نشده است.</p>

      <template v-else>
        <p class="count">{{ users.length }} کاربر نمایش داده شد.</p>

        <div class="table-scroll">
          <table>
            <caption class="visually-hidden">
              فهرست کاربران بیوتی‌بوک
            </caption>
            <thead>
              <tr>
                <th scope="col">نام</th>
                <th scope="col">ایمیل</th>
                <th scope="col">نقش‌ها</th>
                <th scope="col">وضعیت</th>
                <th scope="col">تاریخ عضویت</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id">
                <td data-label="نام">{{ user.full_name }}</td>
                <td data-label="ایمیل">
                  <span dir="ltr" class="email">{{ user.email }}</span>
                </td>
                <td data-label="نقش‌ها">{{ roleLabels(user.roles) }}</td>
                <td data-label="وضعیت">
                  <span class="badge">{{ statusLabel(user.status) }}</span>
                </td>
                <td data-label="تاریخ عضویت">{{ formatDate(user.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="nextCursor" class="more">
          <button type="button" :disabled="loadingMore" @click="loadMore">
            {{ loadingMore ? 'در حال بارگذاری…' : 'نمایش کاربران بیشتر' }}
          </button>
        </div>
      </template>
    </section>
  </main>
</template>

<style scoped>
.admin-page {
  width: min(100%, var(--content-max));
  margin-inline: auto;
  padding: clamp(1.5rem, 4vw, 3rem) var(--space-4) var(--space-8);
}

.brand {
  display: inline-block;
  margin-bottom: var(--space-5);
  color: var(--color-primary);
  font-size: var(--text-sm);
  font-weight: 800;
  letter-spacing: 0.14em;
  text-decoration: none;
  text-transform: uppercase;
}

.eyebrow {
  margin: 0 0 var(--space-2);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: 700;
}

.admin-header h1 {
  margin: 0 0 var(--space-3);
  font-size: clamp(1.6rem, 3vw, 2.1rem);
}

.subtitle {
  max-width: 60ch;
  margin: 0 0 var(--space-5);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  line-height: 1.9;
}

.card {
  padding: clamp(1rem, 3vw, 1.75rem);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.state {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin: 0;
  padding: var(--space-5);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.alert {
  padding: var(--space-4);
  color: #7f1d1d;
  background: #fff1f0;
  border: 1px solid #f3c4c0;
  border-radius: var(--radius-md);
}

.alert p {
  margin: 0 0 var(--space-3);
  font-size: var(--text-sm);
  line-height: 1.8;
}

.retry,
.more button {
  padding: 0.6rem var(--space-4);
  color: #fff;
  background: var(--color-primary);
  border: 0;
  border-radius: var(--radius-md);
  font-family: inherit;
  font-weight: 700;
  cursor: pointer;
}

.retry:disabled,
.more button:disabled {
  cursor: wait;
  opacity: 0.7;
}

.count {
  margin: 0 0 var(--space-3);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.table-scroll {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
  text-align: start;
}

th,
td {
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--color-border);
  text-align: start;
  vertical-align: top;
}

th {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: 700;
  white-space: nowrap;
}

tbody tr:last-child td {
  border-bottom: 0;
}

.email {
  display: inline-block;
  font-family: ui-monospace, 'Cascadia Code', monospace;
  white-space: nowrap;
}

.badge {
  padding: 0.15rem var(--space-2);
  color: var(--color-primary-strong);
  background: var(--color-primary-soft);
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 700;
}

.more {
  display: flex;
  justify-content: center;
  margin-top: var(--space-4);
}

/* On narrow screens the five columns become one stacked card per account. */
@media (max-width: 640px) {
  thead {
    display: none;
  }

  table,
  tbody,
  tr,
  td {
    display: block;
    width: 100%;
  }

  tr {
    padding-block: var(--space-3);
    border-bottom: 1px solid var(--color-border);
  }

  tbody tr:last-child {
    border-bottom: 0;
  }

  td {
    padding: 0.2rem 0;
    border-bottom: 0;
  }

  td::before {
    content: attr(data-label) ": ";
    color: var(--color-text-muted);
    font-size: var(--text-xs);
  }

  .email {
    white-space: normal;
    overflow-wrap: anywhere;
  }
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}

.spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 999px;
  animation: spin 700ms linear infinite;
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

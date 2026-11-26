<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const route = useRoute()

const sectionLabels: Readonly<Record<string, string>> = {
  users: 'کاربران',
  salons: 'سالن‌ها',
  settings: 'تنظیمات',
  'audit-logs': 'گزارش رخدادها',
}

const section = computed(() => String(route.params.section ?? ''))
const label = computed(() => sectionLabels[section.value] ?? 'این بخش')
</script>

<template>
  <section class="section-page">
    <p class="section-eyebrow">بخش مدیریتی</p>
    <h1>{{ label }}</h1>

    <p class="section-text">
      این بخش هنوز ساخته نشده است. مسیر آن از قبل محافظت می‌شود تا دسترسی غیرمجاز حتی به صفحهٔ
      نیمه‌کاره هم ممکن نباشد، اما هیچ داده یا عملیاتی برای نمایش وجود ندارد.
    </p>

    <p class="section-note">
      تعریف دقیق این صفحه در تسک F-014 انجام می‌شود.
    </p>

    <RouterLink class="section-back" to="/admin">بازگشت به داشبورد</RouterLink>
  </section>
</template>

<style scoped>
.section-page {
  max-width: 42rem;
}

.section-eyebrow {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--text-xs);
}

h1 {
  margin: var(--space-1) 0 var(--space-3);
  font-size: var(--text-xl);
}

.section-text {
  color: var(--color-text-muted);
  line-height: 1.9;
}

.section-note {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  line-height: 1.9;
}

.section-back {
  display: inline-flex;
  margin-top: var(--space-3);
  color: var(--color-primary-strong);
  font-weight: 700;
  text-decoration: none;
}

.section-back:focus-visible {
  outline: 2px solid var(--color-primary-strong);
  outline-offset: 2px;
}
</style>

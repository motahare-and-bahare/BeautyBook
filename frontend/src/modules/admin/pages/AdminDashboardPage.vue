<script setup lang="ts">
/**
 * Honest placeholder: the administration features are F-014 and are not specified or built yet.
 * Showing invented statistics here would mislead the operator, so nothing is rendered as data.
 */

const planned = [
  'مدیریت کاربران: جست‌وجو، تعلیق و بازگردانی حساب',
  'بررسی و تأیید سالن‌ها و درخواست‌های سالن‌داری',
  'تنظیمات پلتفرم: ساعات کاری، محدودیت‌ها و قوانین لغو',
  'گزارش رخدادهای حساس (audit log)',
]
</script>

<template>
  <section class="admin-page">
    <p class="admin-eyebrow">داشبورد</p>
    <h1>پنل مدیریت</h1>

    <p class="admin-lead">
      ساختار پنل آماده است، اما بخش‌های مدیریتی هنوز پیاده‌سازی نشده‌اند. این صفحه عمداً هیچ آمار یا
      عملیاتی را نمایش نمی‌دهد تا چیزی که وجود ندارد واقعی به نظر نرسد.
    </p>

    <ul class="admin-planned">
      <li v-for="item in planned" :key="item">{{ item }}</li>
    </ul>

    <p class="admin-note">
      این بخش‌ها در تسک F-014 تعریف و سپس ساخته می‌شوند. تا آن زمان، مسیرهای آن‌ها در منو با
      برچسب «به‌زودی» مشخص شده‌اند.
    </p>
  </section>
</template>

<style scoped>
.admin-page {
  max-width: 46rem;
}

.admin-eyebrow {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--text-xs);
}

h1 {
  margin: var(--space-1) 0 var(--space-3);
  font-size: var(--text-xl);
}

.admin-lead {
  color: var(--color-text-muted);
  line-height: 1.9;
}

.admin-planned {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-4) var(--space-4) var(--space-6);
  margin: var(--space-4) 0;
  background: #fff;
  border: 1px solid #f1e6ea;
  border-radius: var(--radius-md);
  line-height: 1.8;
}

.admin-note {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  line-height: 1.9;
}
</style>

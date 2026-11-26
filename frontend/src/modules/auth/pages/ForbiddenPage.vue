<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <main class="forbidden">
    <section class="card" role="alert">
      <p class="code">۴۰۳</p>
      <h1>دسترسی به این صفحه مجاز نیست</h1>
      <p class="text">
        این صفحه فقط برای کاربران با نقش مدیر در دسترس است. اگر فکر می‌کنید اشتباهی رخ داده، با
        پشتیبانی تماس بگیرید.
      </p>
      <RouterLink class="link" to="/login">بازگشت به صفحهٔ ورود</RouterLink>
    </section>
  </main>
</template>

<style scoped>
.forbidden {
  display: grid;
  min-height: 100vh;
  padding: var(--space-5);
  place-items: center;
  background: var(--color-bg);
}

.card {
  width: min(100%, 30rem);
  padding: clamp(1.5rem, 4vw, 2.5rem);
  text-align: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

.code {
  margin: 0 0 var(--space-2);
  color: var(--color-primary);
  font-size: var(--text-2xl);
  font-weight: 800;
}

h1 {
  margin: 0 0 var(--space-3);
  font-size: var(--text-xl);
}

.text {
  margin: 0 0 var(--space-5);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  line-height: 1.9;
}

.link {
  display: inline-block;
  padding: 0.65rem var(--space-4);
  color: #fff;
  background: var(--color-primary);
  border-radius: var(--radius-md);
  font-weight: 700;
  text-decoration: none;
}
</style>

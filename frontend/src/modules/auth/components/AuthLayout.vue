<script setup lang="ts">
import { RouterLink } from 'vue-router'

defineProps<{
  eyebrow: string
  title: string
  subtitle: string
}>()
</script>

<template>
  <main class="auth-page">
    <aside class="auth-brand">
      <RouterLink class="brand" to="/">BeautyBook</RouterLink>

      <div class="brand-copy">
        <p class="brand-eyebrow">نوبت بعدی شما از اینجا شروع می‌شود</p>
        <h2>زیبایی، با یک رزرو زیبا.</h2>
        <p class="brand-text">
          سالن‌های معتبر را پیدا کنید، قیمت‌های واقعی را مقایسه کنید و همهٔ نوبت‌هایتان را در یک جای
          آرام نگه دارید.
        </p>

        <ul class="benefits">
          <li>
            <span class="check" aria-hidden="true">✓</span>
            خدمات، مدت زمان و قیمت‌های واقعی
          </li>
          <li>
            <span class="check" aria-hidden="true">✓</span>
            همهٔ نوبت‌ها و سابقهٔ شما در یک حساب
          </li>
          <li>
            <span class="check" aria-hidden="true">✓</span>
            فقط حساب مشتری — ثبت‌نام عمومی مدیر وجود ندارد
          </li>
        </ul>
      </div>

      <p class="brand-foot">بیوتی‌بوک · حساب‌های مشتری</p>
    </aside>

    <section class="auth-panel">
      <div class="auth-card">
        <p class="auth-eyebrow">{{ eyebrow }}</p>
        <h1>{{ title }}</h1>
        <p class="auth-subtitle">{{ subtitle }}</p>
        <slot />
      </div>

      <div class="auth-footer">
        <slot name="footer" />
      </div>
    </section>
  </main>
</template>

<style scoped>
.auth-page {
  display: grid;
  grid-template-columns: minmax(0, 1.02fr) minmax(0, 0.98fr);
  min-height: 100vh;
  background: var(--color-bg);
}

.auth-brand {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: var(--space-7);
  overflow: hidden;
  padding: clamp(2rem, 5vw, 4.5rem);
  color: #fff;
  background:
    radial-gradient(circle at 12% 12%, rgb(255 255 255 / 18%) 0, transparent 34%),
    linear-gradient(150deg, #6f2341 0%, #96385a 48%, #c66c86 100%);
}

.auth-brand::before,
.auth-brand::after {
  position: absolute;
  content: '';
  border-radius: 999px;
  border: 1px solid rgb(255 255 255 / 18%);
  pointer-events: none;
}

.auth-brand::before {
  width: 22rem;
  height: 22rem;
  inset-inline-end: -8rem;
  bottom: -8rem;
}

.auth-brand::after {
  width: 13rem;
  height: 13rem;
  inset-inline-end: 2rem;
  bottom: 2rem;
  background: rgb(255 255 255 / 5%);
}

/* The wordmark stays Latin, so uppercase and wide tracking are intentional here. */
.brand {
  position: relative;
  z-index: 1;
  align-self: flex-start;
  color: #fff;
  font-size: var(--text-sm);
  font-weight: 800;
  letter-spacing: 0.14em;
  text-decoration: none;
  text-transform: uppercase;
}

.brand-copy {
  position: relative;
  z-index: 1;
  max-width: 34rem;
}

.brand-eyebrow {
  margin-bottom: var(--space-3);
  color: rgb(255 255 255 / 78%);
  font-size: var(--text-sm);
  font-weight: 700;
}

.brand-copy h2 {
  max-width: 18ch;
  margin-bottom: var(--space-4);
  font-size: clamp(2rem, 4vw, 3.2rem);
  line-height: 1.25;
}

.brand-text {
  max-width: 34ch;
  color: rgb(255 255 255 / 84%);
  font-size: var(--text-lg);
  line-height: 1.85;
}

.benefits {
  display: grid;
  gap: var(--space-3);
  margin: var(--space-6) 0 0;
  padding: 0;
  list-style: none;
}

.benefits li {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  color: rgb(255 255 255 / 92%);
  font-size: var(--text-sm);
  line-height: 1.7;
}

.check {
  display: grid;
  flex: 0 0 auto;
  width: 1.35rem;
  height: 1.35rem;
  margin-top: 0.15rem;
  place-items: center;
  border-radius: 999px;
  color: #7d2948;
  background: #fff;
  font-size: 0.72rem;
  font-weight: 900;
}

.brand-foot {
  position: relative;
  z-index: 1;
  margin: 0;
  color: rgb(255 255 255 / 68%);
  font-size: var(--text-sm);
}

.auth-panel {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: var(--space-5);
  padding: clamp(1.5rem, 4vw, 4rem);
}

.auth-card {
  width: min(100%, 28rem);
  margin-inline: auto;
  padding: clamp(1.5rem, 4vw, 2.5rem);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

.auth-eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-primary);
  font-size: var(--text-sm);
  font-weight: 800;
}

.auth-card h1 {
  margin-bottom: var(--space-3);
  font-size: clamp(1.6rem, 3vw, 2rem);
  line-height: 1.35;
}

.auth-subtitle {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  line-height: 1.8;
}

.auth-footer {
  width: min(100%, 28rem);
  margin-inline: auto;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  text-align: center;
}

.auth-footer :deep(p) {
  margin: 0;
  line-height: 1.8;
}

@media (max-width: 900px) {
  .auth-page {
    grid-template-columns: 1fr;
  }

  .auth-brand {
    gap: var(--space-4);
    padding: var(--space-6) var(--space-5);
  }

  .brand-copy h2 {
    max-width: none;
    margin-bottom: var(--space-2);
    font-size: clamp(1.6rem, 7vw, 2.1rem);
  }

  .brand-text,
  .benefits,
  .brand-foot,
  .brand-eyebrow {
    display: none;
  }

  .auth-panel {
    padding: var(--space-5) var(--space-4) var(--space-7);
  }
}
</style>

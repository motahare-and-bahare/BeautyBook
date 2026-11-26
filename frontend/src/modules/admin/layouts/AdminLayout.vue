<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

import AdminSidebar from '@/modules/admin/components/AdminSidebar.vue'
import { roleLabels } from '@/modules/auth/labels'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const displayName = computed(() => auth.user?.full_name ?? 'مدیر')
</script>

<template>
  <div class="admin-shell">
    <aside class="admin-aside">
      <RouterLink class="admin-brand" to="/">BeautyBook</RouterLink>
      <p class="admin-brand-note">پنل مدیریت</p>

      <AdminSidebar :roles="auth.roles" />
    </aside>

    <div class="admin-main">
      <header class="admin-header">
        <div>
          <p class="admin-kicker">حساب مدیر</p>
          <p class="admin-user">
            {{ displayName }}
            <span class="admin-roles">{{ roleLabels(auth.roles) }}</span>
          </p>
        </div>
      </header>

      <main class="admin-content">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin-shell {
  display: grid;
  grid-template-columns: 16rem minmax(0, 1fr);
  min-height: 100vh;
  background: var(--color-bg);
}

.admin-aside {
  padding: var(--space-5) var(--space-4);
  background: #fff;
  border-inline-end: 1px solid #f1e6ea;
}

.admin-brand {
  display: inline-block;
  color: var(--color-primary-strong);
  font-size: var(--text-lg);
  font-weight: 800;
  text-decoration: none;
}

.admin-brand-note {
  margin: var(--space-1) 0 var(--space-5);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
}

.admin-main {
  min-width: 0;
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  background: #fff;
  border-bottom: 1px solid #f1e6ea;
}

.admin-kicker {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--text-xs);
}

.admin-user {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin: 0;
  font-weight: 700;
}

.admin-roles {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: 600;
}

.admin-content {
  padding: var(--space-5);
}

@media (max-width: 900px) {
  .admin-shell {
    grid-template-columns: 1fr;
  }

  .admin-aside {
    border-inline-end: 0;
    border-bottom: 1px solid #f1e6ea;
  }
}
</style>

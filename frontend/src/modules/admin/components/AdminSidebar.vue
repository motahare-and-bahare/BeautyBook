<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

interface NavItem {
  to: string
  label: string
  available: boolean
}

const props = defineProps<{ roles: readonly string[] }>()

const route = useRoute()

/**
 * Only sections that exist are links. The rest are marked "به‌زودی" instead of pointing at a
 * route that would 404, so the shell never promises a feature that F-014 has not delivered.
 */
const items: readonly NavItem[] = [
  { to: '/admin', label: 'داشبورد', available: true },
  { to: '/admin/users', label: 'کاربران', available: false },
  { to: '/admin/salons', label: 'سالن‌ها', available: false },
  { to: '/admin/settings', label: 'تنظیمات', available: false },
  { to: '/admin/audit-logs', label: 'گزارش رخدادها', available: false },
]

const isAdmin = computed(() => props.roles.includes('admin'))
const visibleItems = computed(() => (isAdmin.value ? items : []))

function isActive(item: NavItem): boolean {
  return route.path === item.to
}
</script>

<template>
  <nav class="admin-nav" aria-label="منوی مدیریت">
    <p v-if="!isAdmin" class="admin-nav-empty" role="status">
      دسترسی به منوی مدیریت فقط برای حساب مدیر مجاز است.
    </p>

    <ul v-else class="admin-nav-list">
      <li v-for="item in visibleItems" :key="item.to">
        <RouterLink
          v-if="item.available"
          data-testid="admin-nav-item"
          class="admin-nav-link"
          :to="item.to"
          :aria-current="isActive(item) ? 'page' : undefined"
        >
          {{ item.label }}
        </RouterLink>

        <span
          v-else
          data-testid="admin-nav-soon"
          class="admin-nav-link is-soon"
          aria-disabled="true"
        >
          {{ item.label }}
          <span class="admin-nav-badge">به‌زودی</span>
        </span>
      </li>
    </ul>
  </nav>
</template>

<style scoped>
.admin-nav-list {
  display: grid;
  gap: var(--space-1);
  padding: 0;
  margin: 0;
  list-style: none;
}

.admin-nav-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  padding: 0.65rem var(--space-3);
  color: var(--color-text-muted);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 600;
  text-decoration: none;
}

.admin-nav-link:hover {
  background: #f8f1f3;
}

.admin-nav-link:focus-visible {
  outline: 2px solid var(--color-primary-strong);
  outline-offset: 2px;
}

.admin-nav-link[aria-current='page'] {
  color: var(--color-primary-strong);
  background: #f8f1f3;
  font-weight: 800;
}

.is-soon {
  cursor: not-allowed;
  opacity: 0.65;
}

.admin-nav-badge {
  padding: 0.1rem 0.45rem;
  color: var(--color-text-muted);
  background: #f1e6ea;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
}

.admin-nav-empty {
  padding: var(--space-3);
  margin: 0;
  color: var(--color-text-muted);
  background: #f8f1f3;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  line-height: 1.8;
}
</style>

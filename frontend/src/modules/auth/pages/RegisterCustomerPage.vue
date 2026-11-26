<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'

import AuthLayout from '@/modules/auth/components/AuthLayout.vue'
import RegisterCustomerForm from '@/modules/auth/components/RegisterCustomerForm.vue'
import type { AuthUser } from '@/services/api/auth'

const user = ref<AuthUser | null>(null)
</script>

<template>
  <AuthLayout
    eyebrow="ثبت‌نام مشتری"
    title="ساخت حساب مشتری"
    subtitle="اطلاعات خود را یک‌بار ذخیره کنید، سپس سالن‌های معتبر را رزرو کنید و همهٔ نوبت‌ها را یک‌جا داشته باشید."
  >
    <RegisterCustomerForm @authenticated="user = $event" />

    <template #footer>
      <p v-if="!user">
        حساب دارید؟
        <RouterLink to="/login">وارد شوید</RouterLink>
      </p>
    </template>
  </AuthLayout>
</template>

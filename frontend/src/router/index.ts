import { createRouter, createWebHistory } from 'vue-router'

import LoginPage from '@/modules/auth/pages/LoginPage.vue'
import RegisterCustomerPage from '@/modules/auth/pages/RegisterCustomerPage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: { name: 'login' } },
    { path: '/login', name: 'login', component: LoginPage },
    { path: '/register', name: 'register', component: RegisterCustomerPage },
  ],
})

export default router

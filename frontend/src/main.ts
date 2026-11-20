import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from '@/app/App.vue'
import router from '@/router'
import '@/assets/styles/tokens.css'
import '@/assets/styles/global.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.mount('#app')

import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    // The README documents http://127.0.0.1:5173. Node now resolves `localhost` to ::1 first,
    // which binds IPv6 only and makes the documented IPv4 URL unreachable. Binding loopback IPv4
    // explicitly also keeps the server off the LAN.
    host: '127.0.0.1',
    // Fail loudly instead of silently starting on 5174, so the documented port is the real port.
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})

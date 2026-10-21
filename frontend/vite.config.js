import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    // запросы /api/... уходят на бэкенд, поэтому CORS не нужен
    proxy: {
      '/api': process.env.API_URL || 'http://127.0.0.1:8000',
    },
  },
})

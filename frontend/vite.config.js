import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      // 开发环境代理：把以下路径转发到 Django 后端，避免跨域
      // 说明：当前 .env.development 使用直连（CORS）模式；
      // 若将 VITE_API_BASE 改为 /api 走代理，二者只能选其一。
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/login': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/logout': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})

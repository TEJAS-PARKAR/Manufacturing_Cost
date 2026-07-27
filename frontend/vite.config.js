import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const RENDER_BACKEND = 'https://manufacturing-cost.onrender.com'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    open: true,
    proxy: {
      '/supplier': {
        target: RENDER_BACKEND,
        changeOrigin: true,
        secure: true,
      },
      '/health': {
        target: RENDER_BACKEND,
        changeOrigin: true,
        secure: true,
      },
      '/estimate-cost': {
        target: RENDER_BACKEND,
        changeOrigin: true,
        secure: true,
      },
      '/chat-cost': {
        target: RENDER_BACKEND,
        changeOrigin: true,
        secure: true,
      },
    },
  },
})

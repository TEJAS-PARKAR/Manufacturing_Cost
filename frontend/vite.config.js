import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const LOCAL_BACKEND = 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    open: true,
    proxy: {
      '/login': {
        target: LOCAL_BACKEND,
        changeOrigin: true,
      },
      '/supplier': {
        target: LOCAL_BACKEND,
        changeOrigin: true,
      },
      '/health': {
        target: LOCAL_BACKEND,
        changeOrigin: true,
      },
      '/estimate-cost': {
        target: LOCAL_BACKEND,
        changeOrigin: true,
      },
      '/chat-cost': {
        target: LOCAL_BACKEND,
        changeOrigin: true,
      },
    },
  },
})

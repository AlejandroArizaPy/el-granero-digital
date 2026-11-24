import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // El proxy conserva las rutas para que Django reciba su URL original.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/usuarios': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/productos': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/ordenes': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})

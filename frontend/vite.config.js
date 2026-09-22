import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Em desenvolvimento o Vite (porta 5173) repassa para a API (porta 8000) tudo
// que não é tela do React. Em produção a própria API serve o frontend.
const API = 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': API,
      '/uploads': API,
      '/docs': API,
      '/redoc': API,
    },
  },
})

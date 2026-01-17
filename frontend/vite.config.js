import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath } from 'url'

const backendTarget =
  process.env.VITE_BACKEND_URL ||
  `http://127.0.0.1:${process.env.VITE_BACKEND_PORT || '8000'}`

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    // pnpm 会使用 symlink 结构；明确关闭 preserveSymlinks，避免 dev 依赖预构建阶段出现
    // "Outdated Optimize Dep" / "Could not resolve ..." 之类问题
    preserveSymlinks: false,
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  optimizeDeps: {
    esbuildOptions: {
      preserveSymlinks: false,
    },
  },
  server: {
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
      }
    }
  }
})

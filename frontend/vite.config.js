import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

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
      '@': path.resolve(__dirname, './src'),
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
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  }
})

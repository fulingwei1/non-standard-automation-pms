import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath } from 'url'

const backendTarget =
  process.env.VITE_BACKEND_URL ||
  `http://127.0.0.1:${process.env.VITE_BACKEND_PORT || '8002'}`

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
  build: {
    // vendor-antd 约 586KB，属于长期缓存的第三方依赖，提高阈值避免误报
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        // 将 700KB 主 bundle 按依赖拆分为独立 vendor chunk，利用浏览器缓存
        manualChunks(id) {
          if (!id.includes('node_modules')) return

          // React 核心 + scheduler（React 内部调度器）
          if (
            id.includes('/react/') ||
            id.includes('/react-dom/') ||
            id.includes('/react-router') ||
            id.includes('/scheduler/')
          ) {
            return 'vendor-react'
          }
          // 图表库（必须在 @ant-design 通配之前匹配 @ant-design/plots）
          if (
            id.includes('/@ant-design/plots/') ||
            id.includes('/recharts/') ||
            id.includes('/d3-') ||
            id.includes('/victory-')
          ) {
            return 'vendor-charts'
          }
          // Ant Design 生态（含 @rc-component、@ant-design 子包）
          if (
            id.includes('/antd/') ||
            id.includes('/@ant-design/') ||
            id.includes('/@rc-component/')
          ) {
            return 'vendor-antd'
          }
          // Radix UI + shadcn 工具链
          if (
            id.includes('/@radix-ui/') ||
            id.includes('/class-variance-authority/') ||
            id.includes('/clsx/') ||
            id.includes('/tailwind-merge/') ||
            id.includes('/lucide-react/')
          ) {
            return 'vendor-ui'
          }
          // 工具库
          if (
            id.includes('/framer-motion/') ||
            id.includes('/axios/') ||
            id.includes('/date-fns/') ||
            id.includes('/dayjs/') ||
            id.includes('/zod/')
          ) {
            return 'vendor-utils'
          }
        },
      },
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

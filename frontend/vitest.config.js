import { configDefaults, mergeConfig } from "vitest/config";
import { defineConfig } from "vite";
import viteConfig from "./vite.config.js";

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: ["./src/test/setupTests.js"],
      css: true,
      include: ["src/**/*.{test,spec}.{js,jsx,ts,tsx}"],
      // 支持.tsx文件中的JSX语法
      transformMode: {
        web: [/\.[jt]sx?$/],
      },
      exclude: [...configDefaults.exclude, "e2e/**"],
      // 开启文件级并行并限制 worker 数量，避免全量测试串行超时或内存溢出
      pool: "forks",
      fileParallelism: true,
      maxWorkers: 4,
      maxConcurrency: 5,
      sequence: {
        shuffle: false,
      },
      testTimeout: 10000,
      hookTimeout: 10000,
      coverage: {
        provider: "v8",
        reporter: ["text", "html", "lcov"],
        reportsDirectory: "./coverage",
        exclude: ["dist/**", "node_modules/**", "src/test/**"],
      },
    },
  }),
);

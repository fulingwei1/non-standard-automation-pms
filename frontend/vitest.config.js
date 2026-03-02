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
      // 限制并发，避免状态冲突
      pool: "forks",
      poolOptions: {
        forks: {
          singleFork: true,
        },
      },
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

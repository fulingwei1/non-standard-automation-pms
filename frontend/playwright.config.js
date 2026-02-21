import { defineConfig, devices } from "playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000, // 增加到 60 秒，适应复杂流程
  expect: { timeout: 10_000 },
  
  // 失败重试
  retries: process.env.CI ? 2 : 1,
  
  // 并行worker数量
  workers: process.env.CI ? 1 : undefined,
  
  // Reporter配置
  reporter: [
    ['html', { outputFolder: 'test-results/html' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['list']
  ],
  
  use: {
    baseURL: "http://127.0.0.1:4173",
    
    // 截图配置
    screenshot: 'only-on-failure',
    
    // 视频录制
    video: 'retain-on-failure',
    
    // 追踪
    trace: 'retain-on-failure',
    
    // 浏览器上下文
    viewport: { width: 1920, height: 1080 },
    
    // 导航超时
    navigationTimeout: 30_000,
    
    // 动作超时
    actionTimeout: 10_000,
  },
  
  webServer: {
    command: "pnpm preview --host 127.0.0.1 --port 4173 --strictPort",
    url: "http://127.0.0.1:4173",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
  
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    
    // 可选：添加更多浏览器
    // {
    //   name: "firefox",
    //   use: { ...devices["Desktop Firefox"] },
    // },
    // {
    //   name: "webkit",
    //   use: { ...devices["Desktop Safari"] },
    // },
  ],
});

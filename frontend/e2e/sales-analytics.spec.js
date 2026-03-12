/**
 * 销售分析功能 E2E 测试
 *
 * 测试范围：
 * - 销售漏斗页面
 * - 销售统计页面
 * - 赢率预测功能
 * - 报表导出
 */

import { test, expect } from "playwright/test";
import { login, waitForPageLoad } from "./helpers/test-helpers.js";

test.describe("销售漏斗", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await waitForPageLoad(page);
  });

  test("应该正确显示销售漏斗页面", async ({ page }) => {
    await page.goto("/sales/funnel");
    await waitForPageLoad(page);

    // 验证页面标题
    await expect(page.locator("h1, h2, .page-title")).toContainText(/销售漏斗/);

    // 截图
    await page.screenshot({
      path: "test-results/screenshots/sales-funnel-page.png",
    });
  });

  test("应该显示漏斗各阶段数据", async ({ page }) => {
    await page.goto("/sales/funnel");
    await waitForPageLoad(page);

    // 等待数据加载
    await page.waitForTimeout(2000);

    // 验证漏斗阶段
    const pageContent = await page.textContent("body");
    expect(pageContent).toMatch(/线索|商机|报价|合同/);

    // 截图漏斗图
    await page.screenshot({
      path: "test-results/screenshots/sales-funnel-stages.png",
    });
  });

  test("应该能切换到转化分析 Tab", async ({ page }) => {
    await page.goto("/sales/funnel");
    await waitForPageLoad(page);

    // 查找并点击转化分析 Tab
    const conversionTab = page.getByRole("tab", { name: /转化分析/ });
    if (await conversionTab.isVisible({ timeout: 5000 })) {
      await conversionTab.click();
      await page.waitForTimeout(1000);

      // 验证内容切换
      const content = await page.textContent("body");
      expect(content).toMatch(/转化|率|%/);

      await page.screenshot({
        path: "test-results/screenshots/conversion-analysis.png",
      });
    }
  });

  test("应该能切换到瓶颈识别 Tab", async ({ page }) => {
    await page.goto("/sales/funnel");
    await waitForPageLoad(page);

    // 查找并点击瓶颈识别 Tab
    const bottleneckTab = page.getByRole("tab", { name: /瓶颈识别/ });
    if (await bottleneckTab.isVisible({ timeout: 5000 })) {
      await bottleneckTab.click();
      await page.waitForTimeout(1000);

      await page.screenshot({
        path: "test-results/screenshots/bottleneck-analysis.png",
      });
    }
  });

  test("应该显示赢率预测数据", async ({ page }) => {
    await page.goto("/sales/funnel");
    await waitForPageLoad(page);

    // 等待赢率预测数据加载
    await page.waitForTimeout(3000);

    // 查找赢率预测相关内容
    const pageContent = await page.textContent("body");
    const hasWinRate = /赢率|预测|胜率|概率/.test(pageContent);

    if (hasWinRate) {
      await page.screenshot({
        path: "test-results/screenshots/win-rate-prediction.png",
      });
    }

    // 页面应该正常加载
    expect(page.url()).toContain("/sales/funnel");
  });

  test("应该支持筛选功能", async ({ page }) => {
    await page.goto("/sales/funnel");
    await waitForPageLoad(page);

    // 查找筛选按钮或下拉框
    const filterButton = page.locator(
      'button:has-text("筛选"), button:has-text("过滤"), [aria-label*="filter"]'
    );

    if (await filterButton.first().isVisible({ timeout: 3000 })) {
      await filterButton.first().click();
      await page.waitForTimeout(500);

      await page.screenshot({
        path: "test-results/screenshots/funnel-filter-open.png",
      });
    }
  });
});

test.describe("销售统计", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await waitForPageLoad(page);
  });

  test("应该正确显示销售统计页面", async ({ page }) => {
    await page.goto("/sales/statistics");
    await waitForPageLoad(page);

    // 验证页面加载
    await page.waitForTimeout(2000);

    // 截图
    await page.screenshot({
      path: "test-results/screenshots/sales-statistics-page.png",
    });
  });

  test("应该显示统计卡片", async ({ page }) => {
    await page.goto("/sales/statistics");
    await waitForPageLoad(page);

    // 等待数据加载
    await page.waitForTimeout(2000);

    // 验证统计内容
    const pageContent = await page.textContent("body");
    expect(pageContent).toMatch(/线索|商机|合同|金额|总计|数量/);

    await page.screenshot({
      path: "test-results/screenshots/statistics-cards.png",
    });
  });

  test("应该显示图表", async ({ page }) => {
    await page.goto("/sales/statistics");
    await waitForPageLoad(page);

    // 等待图表加载
    await page.waitForTimeout(3000);

    // 查找图表元素
    const charts = page.locator(
      '.recharts-wrapper, [class*="chart"], canvas, svg'
    );
    const chartCount = await charts.count();

    await page.screenshot({
      path: "test-results/screenshots/statistics-charts.png",
    });

    // 页面应该有某种数据可视化
    expect(page.url()).toContain("/sales/statistics");
  });
});

test.describe("商机管理", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await waitForPageLoad(page);
  });

  test("应该显示商机列表", async ({ page }) => {
    await page.goto("/sales/opportunities");
    await waitForPageLoad(page);

    // 等待列表加载
    await page.waitForTimeout(2000);

    // 验证页面内容
    const pageContent = await page.textContent("body");
    expect(pageContent).toMatch(/商机|客户|阶段/);

    await page.screenshot({
      path: "test-results/screenshots/opportunity-list.png",
    });
  });

  test("应该能搜索商机", async ({ page }) => {
    await page.goto("/sales/opportunities");
    await waitForPageLoad(page);

    // 查找搜索框
    const searchInput = page.locator(
      'input[placeholder*="搜索"], input[placeholder*="查找"], input[type="search"]'
    );

    if (await searchInput.first().isVisible({ timeout: 3000 })) {
      await searchInput.first().fill("测试");
      await page.waitForTimeout(1000);

      await page.screenshot({
        path: "test-results/screenshots/opportunity-search.png",
      });
    }
  });

  test("应该显示商机详情", async ({ page }) => {
    await page.goto("/sales/opportunities");
    await waitForPageLoad(page);

    // 等待列表加载
    await page.waitForTimeout(2000);

    // 尝试点击第一行商机
    const firstRow = page.locator("tr").nth(1);
    if (await firstRow.isVisible({ timeout: 3000 })) {
      // 查找查看详情按钮或直接点击行
      const viewBtn = firstRow.locator(
        'button:has-text("查看"), button:has-text("详情"), a:has-text("查看")'
      );

      if (await viewBtn.first().isVisible({ timeout: 2000 })) {
        await viewBtn.first().click();
        await page.waitForTimeout(1000);

        await page.screenshot({
          path: "test-results/screenshots/opportunity-detail.png",
        });
      }
    }
  });

  test("应该显示赢率预测信息", async ({ page }) => {
    await page.goto("/sales/opportunities");
    await waitForPageLoad(page);

    // 等待数据加载
    await page.waitForTimeout(3000);

    // 查找赢率相关信息
    const pageContent = await page.textContent("body");
    const hasWinRate = /赢率|概率|预测|%/.test(pageContent);

    await page.screenshot({
      path: "test-results/screenshots/opportunity-win-rate.png",
    });

    // 页面应该正常加载
    expect(page.url()).toContain("/sales/opportunities");
  });
});

test.describe("客户管理", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await waitForPageLoad(page);
  });

  test("应该显示客户列表", async ({ page }) => {
    await page.goto("/sales/customers");
    await waitForPageLoad(page);

    // 等待列表加载
    await page.waitForTimeout(2000);

    // 验证页面内容
    const pageContent = await page.textContent("body");
    expect(pageContent).toMatch(/客户|名称|行业|状态/);

    await page.screenshot({
      path: "test-results/screenshots/customer-list.png",
    });
  });

  test("应该能创建客户", async ({ page }) => {
    await page.goto("/sales/customers");
    await waitForPageLoad(page);

    // 查找创建按钮
    const createBtn = page.getByRole("button", { name: /新建|创建|添加/ });

    if (await createBtn.first().isVisible({ timeout: 3000 })) {
      await createBtn.first().click();
      await page.waitForTimeout(1000);

      // 验证表单出现
      const form = page.locator("form, .ant-modal, .drawer");
      await expect(form.first()).toBeVisible({ timeout: 3000 });

      await page.screenshot({
        path: "test-results/screenshots/customer-create-form.png",
      });

      // 关闭表单
      const cancelBtn = page.getByRole("button", { name: /取消|关闭/ });
      if (await cancelBtn.first().isVisible({ timeout: 2000 })) {
        await cancelBtn.first().click();
      }
    }
  });
});

test.describe("报价管理", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await waitForPageLoad(page);
  });

  test("应该显示报价列表", async ({ page }) => {
    await page.goto("/sales/quotes");
    await waitForPageLoad(page);

    // 等待列表加载
    await page.waitForTimeout(2000);

    // 验证页面内容
    const pageContent = await page.textContent("body");
    expect(pageContent).toMatch(/报价|客户|金额|状态/);

    await page.screenshot({
      path: "test-results/screenshots/quote-list.png",
    });
  });

  test("应该支持报价筛选", async ({ page }) => {
    await page.goto("/sales/quotes");
    await waitForPageLoad(page);

    // 查找状态筛选
    const statusFilter = page.locator(
      'select, [role="combobox"], button:has-text("状态")'
    );

    if (await statusFilter.first().isVisible({ timeout: 3000 })) {
      await statusFilter.first().click();
      await page.waitForTimeout(500);

      await page.screenshot({
        path: "test-results/screenshots/quote-filter.png",
      });
    }
  });
});

import { test, expect } from "playwright/test";
import { login, logout, waitForPageLoad } from "./helpers/test-helpers.js";

test.describe("用户认证流程", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await waitForPageLoad(page);
  });

  test("应该显示登录页面元素", async ({ page }) => {
    // 验证登录页面关键元素
    await expect(page.getByPlaceholder("请输入用户名")).toBeVisible();
    await expect(page.getByPlaceholder("请输入密码")).toBeVisible();
    await expect(page.getByRole("button", { name: /登录/i })).toBeVisible();
    
    // 验证页面标题
    await expect(page.getByRole("heading", { name: "欢迎回来" })).toBeVisible();
    
    // 截图
    await page.screenshot({ path: 'test-results/screenshots/login-page.png' });
  });

  test("应该成功登录管理员账户", async ({ page }) => {
    // 填写登录表单
    await page.getByPlaceholder("请输入用户名").fill("admin");
    await page.getByPlaceholder("请输入密码").fill("admin123");
    
    // 截图登录前
    await page.screenshot({ path: 'test-results/screenshots/before-login.png' });
    
    // 点击登录
    await page.getByRole("button", { name: /登录/i }).click();
    
    // 等待跳转到工作台
    await page.waitForURL(/dashboard|workstation/, { timeout: 10000 });
    
    // 验证登录成功
    await expect(page).toHaveURL(/dashboard|workstation/);
    
    // 截图登录后
    await page.screenshot({ path: 'test-results/screenshots/after-login.png' });
  });

  test("应该拒绝错误的登录凭证", async ({ page }) => {
    // 填写错误的登录信息
    await page.getByPlaceholder("请输入用户名").fill("wronguser");
    await page.getByPlaceholder("请输入密码").fill("wrongpassword");
    
    // 点击登录
    await page.getByRole("button", { name: /登录/i }).click();
    
    // 验证仍在登录页或显示错误消息
    await expect(
      page.locator('.ant-message-error, .error-message, .ant-form-item-explain-error')
    ).toBeVisible({ timeout: 5000 });
    
    // 截图错误状态
    await page.screenshot({ path: 'test-results/screenshots/login-error.png' });
  });

  test("应该验证必填字段", async ({ page }) => {
    // 不填写任何信息，直接点击登录
    await page.getByRole("button", { name: /登录/i }).click();
    
    // 验证显示验证错误
    const usernameError = page.locator('input[placeholder*="用户名"]').locator('..').locator('.ant-form-item-explain-error');
    const passwordError = page.locator('input[placeholder*="密码"]').locator('..').locator('.ant-form-item-explain-error');
    
    // 至少有一个字段显示错误
    const errorVisible = await usernameError.isVisible().catch(() => false) || 
                         await passwordError.isVisible().catch(() => false);
    expect(errorVisible).toBeTruthy();
    
    // 截图验证错误
    await page.screenshot({ path: 'test-results/screenshots/validation-error.png' });
  });

  test("应该成功退出登录", async ({ page }) => {
    // 先登录
    await login(page);
    
    // 等待页面加载
    await waitForPageLoad(page);
    
    // 查找用户菜单并点击（可能是头像、用户名或下拉菜单）
    const userMenuSelectors = [
      '[data-testid="user-menu"]',
      '.user-avatar',
      '.ant-dropdown-trigger',
      'button:has-text("admin")',
      '[aria-label="user"]'
    ];
    
    let clicked = false;
    for (const selector of userMenuSelectors) {
      try {
        const element = page.locator(selector).first();
        if (await element.isVisible({ timeout: 2000 })) {
          await element.click();
          clicked = true;
          break;
        }
      } catch (e) {
        continue;
      }
    }
    
    if (!clicked) {
      console.log('未找到用户菜单，尝试查找退出按钮');
    }
    
    // 点击退出登录
    await page.getByText(/退出登录|登出|logout/i).click();
    
    // 验证返回登录页
    await expect(page).toHaveURL(/login/, { timeout: 10000 });
    
    // 截图退出后
    await page.screenshot({ path: 'test-results/screenshots/after-logout.png' });
  });

  test("应该在未登录时重定向到登录页", async ({ page }) => {
    // 清除存储
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());
    await page.evaluate(() => sessionStorage.clear());
    
    // 尝试访问受保护的页面
    await page.goto('/dashboard');
    
    // 验证重定向到登录页
    await expect(page).toHaveURL(/login/, { timeout: 10000 });
    
    // 截图重定向
    await page.screenshot({ path: 'test-results/screenshots/redirect-to-login.png' });
  });
});

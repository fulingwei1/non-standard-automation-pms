import { expect } from "playwright/test";

/**
 * 登录辅助函数
 */
export async function login(page, username = 'admin', password = 'admin123') {
  await page.goto('/login');
  await page.getByPlaceholder('请输入用户名').fill(username);
  await page.getByPlaceholder('请输入密码').fill(password);
  await page.getByRole('button', { name: /登录|登錄|login/i }).click();
  
  // 等待导航完成
  await page.waitForURL(/dashboard|workstation/, { timeout: 10000 });
}

/**
 * 登出辅助函数
 */
export async function logout(page) {
  // 点击用户头像或菜单
  await page.locator('[data-testid="user-menu"], .user-avatar, .ant-dropdown-trigger').first().click();
  
  // 点击退出登录
  await page.getByText(/退出登录|登出|logout/i).click();
  
  // 验证返回登录页
  await expect(page).toHaveURL(/login/);
}

/**
 * 等待页面加载完成
 */
export async function waitForPageLoad(page) {
  await page.waitForLoadState('networkidle');
  await page.waitForLoadState('domcontentloaded');
}

/**
 * 填写表单字段
 */
export async function fillFormField(page, label, value) {
  const field = page.locator(`label:has-text("${label}")`).locator('..').locator('input, textarea').first();
  await field.fill(value);
}

/**
 * 点击提交按钮
 */
export async function clickSubmit(page, buttonText = '提交') {
  await page.getByRole('button', { name: new RegExp(buttonText, 'i') }).click();
}

/**
 * 等待成功提示
 */
export async function waitForSuccess(page, message = '成功') {
  await expect(page.locator('.ant-message-success, .success-message')).toContainText(message, { timeout: 5000 });
}

/**
 * 清理测试数据 - 删除项
 */
export async function cleanupItem(page, itemName) {
  try {
    // 查找包含删除按钮的行
    const row = page.locator(`tr:has-text("${itemName}")`);
    if (await row.count() > 0) {
      await row.locator('button:has-text("删除"), [aria-label="delete"]').first().click();
      
      // 确认删除
      await page.getByRole('button', { name: /确定|确认|OK/i }).click();
      
      // 等待删除成功
      await waitForSuccess(page, '删除');
    }
  } catch (error) {
    console.log(`清理项目 ${itemName} 时出错:`, error.message);
  }
}

/**
 * 生成唯一测试数据名称
 */
export function generateTestName(prefix) {
  const timestamp = Date.now();
  return `${prefix}_${timestamp}`;
}

/**
 * 截图辅助函数
 */
export async function takeScreenshot(page, name) {
  await page.screenshot({ 
    path: `test-results/screenshots/${name}.png`,
    fullPage: true 
  });
}

/**
 * 选择下拉选项
 */
export async function selectDropdownOption(page, label, optionText) {
  // 点击下拉框
  await page.locator(`label:has-text("${label}")`).locator('..').locator('.ant-select, select').first().click();
  
  // 选择选项
  await page.locator('.ant-select-item, option').filter({ hasText: optionText }).click();
}

/**
 * 等待表格加载
 */
export async function waitForTableLoad(page) {
  await page.waitForSelector('.ant-table, table', { timeout: 10000 });
  await page.waitForLoadState('networkidle');
}

/**
 * 验证表格包含数据
 */
export async function verifyTableContains(page, text) {
  await expect(page.locator('.ant-table, table')).toContainText(text);
}

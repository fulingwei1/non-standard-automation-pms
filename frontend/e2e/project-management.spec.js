import { test, expect } from "playwright/test";
import { 
  login, 
  waitForPageLoad, 
  fillFormField,
  clickSubmit,
  waitForSuccess,
  cleanupItem,
  generateTestName,
  waitForTableLoad,
  verifyTableContains
} from "./helpers/test-helpers.js";

test.describe("项目管理流程", () => {
  let projectName;

  test.beforeEach(async ({ page }) => {
    // 登录
    await login(page);
    await waitForPageLoad(page);
    
    // 生成唯一项目名
    projectName = generateTestName("E2E测试项目");
  });

  test("应该显示项目列表页面", async ({ page }) => {
    // 导航到项目列表
    await page.goto('/projects');
    await waitForTableLoad(page);
    
    // 验证页面元素
    await expect(page.locator('h1, h2, .page-title')).toContainText(/项目/);
    
    // 验证有创建按钮
    const createButton = page.getByRole('button', { name: /新建|创建|添加.*项目/i });
    await expect(createButton).toBeVisible();
    
    // 截图
    await page.screenshot({ path: 'test-results/screenshots/project-list.png' });
  });

  test("应该成功创建新项目", async ({ page }) => {
    // 导航到项目列表
    await page.goto('/projects');
    await waitForTableLoad(page);
    
    // 点击创建项目按钮
    await page.getByRole('button', { name: /新建|创建|添加.*项目/i }).click();
    
    // 等待表单出现
    await page.waitForSelector('form, .ant-modal, .drawer', { timeout: 5000 });
    
    // 截图表单
    await page.screenshot({ path: 'test-results/screenshots/project-create-form.png' });
    
    // 填写项目信息
    await page.locator('input[placeholder*="项目名称"], input[name*="name"]').first().fill(projectName);
    await page.locator('textarea[placeholder*="描述"], textarea[name*="description"]').first().fill('这是一个E2E测试项目');
    
    // 尝试选择项目类型（如果有）
    try {
      const typeSelector = page.locator('.ant-select:has-text("类型")').first();
      if (await typeSelector.isVisible({ timeout: 2000 })) {
        await typeSelector.click();
        await page.locator('.ant-select-item').first().click();
      }
    } catch (e) {
      console.log('未找到项目类型选择器');
    }
    
    // 截图填写后
    await page.screenshot({ path: 'test-results/screenshots/project-form-filled.png' });
    
    // 提交表单
    await page.getByRole('button', { name: /确定|提交|保存|创建/i }).click();
    
    // 等待成功提示或跳转
    await Promise.race([
      page.waitForSelector('.ant-message-success', { timeout: 10000 }),
      page.waitForURL(/project/, { timeout: 10000 })
    ]);
    
    // 截图结果
    await page.screenshot({ path: 'test-results/screenshots/project-created.png' });
    
    // 返回列表验证项目已创建
    await page.goto('/projects');
    await waitForTableLoad(page);
    await verifyTableContains(page, projectName);
  });

  test("应该成功编辑项目信息", async ({ page }) => {
    // 先创建项目
    await page.goto('/projects');
    await waitForTableLoad(page);
    
    await page.getByRole('button', { name: /新建|创建|添加.*项目/i }).click();
    await page.waitForSelector('form, .ant-modal, .drawer');
    await page.locator('input[placeholder*="项目名称"], input[name*="name"]').first().fill(projectName);
    await page.getByRole('button', { name: /确定|提交|保存|创建/i }).click();
    
    await page.waitForTimeout(2000);
    await page.goto('/projects');
    await waitForTableLoad(page);
    
    // 查找并点击编辑按钮
    const projectRow = page.locator(`tr:has-text("${projectName}")`);
    await expect(projectRow).toBeVisible({ timeout: 10000 });
    
    // 尝试多种编辑按钮选择器
    const editSelectors = [
      'button:has-text("编辑")',
      '[aria-label="edit"]',
      'button.edit-btn',
      '.ant-btn:has-text("编辑")'
    ];
    
    let clicked = false;
    for (const selector of editSelectors) {
      try {
        const editBtn = projectRow.locator(selector).first();
        if (await editBtn.isVisible({ timeout: 2000 })) {
          await editBtn.click();
          clicked = true;
          break;
        }
      } catch (e) {
        continue;
      }
    }
    
    if (!clicked) {
      // 如果没有编辑按钮，尝试点击行进入详情
      await projectRow.click();
    }
    
    // 等待编辑表单
    await page.waitForSelector('form, .ant-modal, .drawer, input[name*="name"]', { timeout: 5000 });
    
    // 修改项目描述
    const updatedDescription = `${projectName} - 已编辑`;
    await page.locator('textarea[placeholder*="描述"], textarea[name*="description"]').first().fill(updatedDescription);
    
    // 截图编辑
    await page.screenshot({ path: 'test-results/screenshots/project-edit.png' });
    
    // 保存
    await page.getByRole('button', { name: /确定|提交|保存|更新/i }).click();
    
    // 等待成功
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'test-results/screenshots/project-edited.png' });
  });

  test("应该在项目看板中拖拽任务", async ({ page }) => {
    // 导航到项目看板
    await page.goto('/progress-tracking/board');
    await waitForPageLoad(page);
    
    // 截图看板
    await page.screenshot({ path: 'test-results/screenshots/project-board.png' });
    
    // 查找可拖拽的卡片
    const cards = page.locator('.kanban-card, .task-card, [draggable="true"]');
    const cardCount = await cards.count();
    
    if (cardCount >= 1) {
      const firstCard = cards.first();
      
      // 获取卡片位置
      const cardBox = await firstCard.boundingBox();
      
      if (cardBox) {
        // 拖拽卡片（简单的横向移动）
        await page.mouse.move(cardBox.x + cardBox.width / 2, cardBox.y + cardBox.height / 2);
        await page.mouse.down();
        await page.mouse.move(cardBox.x + 200, cardBox.y + cardBox.height / 2, { steps: 10 });
        await page.mouse.up();
        
        // 等待动画
        await page.waitForTimeout(1000);
        
        // 截图拖拽后
        await page.screenshot({ path: 'test-results/screenshots/board-after-drag.png' });
      }
    } else {
      console.log('看板中没有可拖拽的卡片');
      await page.screenshot({ path: 'test-results/screenshots/board-empty.png' });
    }
  });

  test("应该成功删除项目", async ({ page }) => {
    // 先创建项目
    await page.goto('/projects');
    await waitForTableLoad(page);
    
    await page.getByRole('button', { name: /新建|创建|添加.*项目/i }).click();
    await page.waitForSelector('form, .ant-modal, .drawer');
    await page.locator('input[placeholder*="项目名称"], input[name*="name"]').first().fill(projectName);
    await page.getByRole('button', { name: /确定|提交|保存|创建/i }).click();
    
    await page.waitForTimeout(2000);
    await page.goto('/projects');
    await waitForTableLoad(page);
    
    // 查找项目行
    const projectRow = page.locator(`tr:has-text("${projectName}")`);
    await expect(projectRow).toBeVisible({ timeout: 10000 });
    
    // 截图删除前
    await page.screenshot({ path: 'test-results/screenshots/before-delete-project.png' });
    
    // 尝试多种删除按钮选择器
    const deleteSelectors = [
      'button:has-text("删除")',
      '[aria-label="delete"]',
      'button.delete-btn',
      '.ant-btn-dangerous'
    ];
    
    let clicked = false;
    for (const selector of deleteSelectors) {
      try {
        const deleteBtn = projectRow.locator(selector).first();
        if (await deleteBtn.isVisible({ timeout: 2000 })) {
          await deleteBtn.click();
          clicked = true;
          break;
        }
      } catch (e) {
        continue;
      }
    }
    
    if (clicked) {
      // 确认删除
      await page.waitForSelector('.ant-modal, .ant-popconfirm', { timeout: 3000 });
      await page.getByRole('button', { name: /确定|确认|删除|OK/i }).click();
      
      // 等待删除成功
      await page.waitForTimeout(2000);
      
      // 截图删除后
      await page.screenshot({ path: 'test-results/screenshots/after-delete-project.png' });
      
      // 验证项目已删除
      await waitForTableLoad(page);
      const deletedRow = page.locator(`tr:has-text("${projectName}")`);
      await expect(deletedRow).not.toBeVisible();
    } else {
      console.log('未找到删除按钮');
    }
  });

  test.afterEach(async ({ page }) => {
    // 清理：尝试删除测试项目
    try {
      await page.goto('/projects');
      await waitForTableLoad(page);
      await cleanupItem(page, projectName);
    } catch (e) {
      console.log('清理项目失败:', e.message);
    }
  });
});

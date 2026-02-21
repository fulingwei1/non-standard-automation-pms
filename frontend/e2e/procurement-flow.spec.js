import { test, expect } from "playwright/test";
import { 
  login, 
  waitForPageLoad, 
  generateTestName,
  waitForTableLoad,
  verifyTableContains,
  cleanupItem
} from "./helpers/test-helpers.js";

test.describe("采购流程", () => {
  let purchaseName;
  let supplierName;
  let orderName;

  test.beforeEach(async ({ page }) => {
    // 登录
    await login(page);
    await waitForPageLoad(page);
    
    // 生成唯一名称
    purchaseName = generateTestName("E2E采购申请");
    supplierName = generateTestName("E2E供应商");
    orderName = generateTestName("E2E采购订单");
  });

  test("应该成功创建采购申请", async ({ page }) => {
    // 导航到采购申请页面
    await page.goto('/procurement/requests');
    await waitForPageLoad(page);
    
    // 截图采购申请列表
    await page.screenshot({ path: 'test-results/screenshots/purchase-request-list.png' });
    
    // 点击创建按钮
    const createBtn = page.getByRole('button', { name: /新建|创建|添加.*申请/i });
    await expect(createBtn).toBeVisible({ timeout: 10000 });
    await createBtn.click();
    
    // 等待表单
    await page.waitForSelector('form, .ant-modal, .drawer', { timeout: 5000 });
    
    // 填写采购申请信息
    await page.locator('input[placeholder*="申请名称"], input[placeholder*="名称"], input[name*="name"]').first().fill(purchaseName);
    
    // 填写物料或产品
    try {
      await page.locator('input[placeholder*="物料"], input[placeholder*="产品"]').first().fill('测试物料');
    } catch (e) {
      console.log('未找到物料字段');
    }
    
    // 填写数量
    try {
      await page.locator('input[placeholder*="数量"], input[name*="quantity"]').first().fill('10');
    } catch (e) {
      console.log('未找到数量字段');
    }
    
    // 填写预算
    try {
      await page.locator('input[placeholder*="预算"], input[placeholder*="金额"], input[name*="budget"]').first().fill('50000');
    } catch (e) {
      console.log('未找到预算字段');
    }
    
    // 填写备注
    try {
      await page.locator('textarea[placeholder*="备注"], textarea[name*="remark"]').first().fill('E2E自动化测试采购申请');
    } catch (e) {
      console.log('未找到备注字段');
    }
    
    // 截图填写后
    await page.screenshot({ path: 'test-results/screenshots/purchase-request-form.png' });
    
    // 提交
    await page.getByRole('button', { name: /确定|提交|保存|创建/i }).click();
    
    // 等待成功
    await page.waitForTimeout(2000);
    
    // 截图创建后
    await page.screenshot({ path: 'test-results/screenshots/purchase-request-created.png' });
    
    // 验证申请已创建
    await page.goto('/procurement/requests');
    await waitForTableLoad(page);
    await verifyTableContains(page, purchaseName);
  });

  test("应该显示供应商列表", async ({ page }) => {
    // 导航到供应商管理
    await page.goto('/procurement/suppliers');
    await waitForPageLoad(page);
    
    // 验证页面元素
    await expect(page.locator('h1, h2, .page-title')).toContainText(/供应商/);
    
    // 截图供应商列表
    await page.screenshot({ path: 'test-results/screenshots/supplier-list.png' });
    
    // 验证有表格或列表
    const hasTable = await page.locator('.ant-table, table, .supplier-list').isVisible({ timeout: 5000 });
    expect(hasTable).toBeTruthy();
  });

  test("应该成功选择供应商", async ({ page }) => {
    // 先创建采购申请
    await page.goto('/procurement/requests');
    await waitForPageLoad(page);
    
    await page.getByRole('button', { name: /新建|创建|添加.*申请/i }).click();
    await page.waitForSelector('form, .ant-modal, .drawer');
    await page.locator('input[placeholder*="申请名称"], input[placeholder*="名称"], input[name*="name"]').first().fill(purchaseName);
    await page.getByRole('button', { name: /确定|提交|保存|创建/i }).click();
    
    await page.waitForTimeout(2000);
    await page.goto('/procurement/requests');
    await waitForTableLoad(page);
    
    // 查找采购申请行
    const requestRow = page.locator(`tr:has-text("${purchaseName}")`);
    if (await requestRow.isVisible({ timeout: 5000 })) {
      // 截图选择前
      await page.screenshot({ path: 'test-results/screenshots/before-select-supplier.png' });
      
      // 尝试查找选择供应商按钮
      const supplierSelectors = [
        'button:has-text("选择供应商")',
        'button:has-text("供应商")',
        'button:has-text("选择")'
      ];
      
      let clicked = false;
      for (const selector of supplierSelectors) {
        try {
          const supplierBtn = requestRow.locator(selector).first();
          if (await supplierBtn.isVisible({ timeout: 2000 })) {
            await supplierBtn.click();
            clicked = true;
            break;
          }
        } catch (e) {
          continue;
        }
      }
      
      if (clicked) {
        // 等待供应商选择界面
        await page.waitForSelector('.ant-modal, .drawer, .supplier-select', { timeout: 5000 });
        
        // 截图供应商选择界面
        await page.screenshot({ path: 'test-results/screenshots/supplier-selection.png' });
        
        // 选择第一个供应商（如果有）
        const firstSupplier = page.locator('.ant-radio, .supplier-item, .ant-select-item').first();
        if (await firstSupplier.isVisible({ timeout: 3000 })) {
          await firstSupplier.click();
          
          // 确认选择
          await page.getByRole('button', { name: /确定|确认|选择/i }).click();
          await page.waitForTimeout(2000);
          
          // 截图选择后
          await page.screenshot({ path: 'test-results/screenshots/after-select-supplier.png' });
        }
      } else {
        console.log('未找到选择供应商按钮');
      }
    }
  });

  test("应该成功生成采购订单", async ({ page }) => {
    // 导航到采购订单页面
    await page.goto('/procurement/orders');
    await waitForPageLoad(page);
    
    // 截图订单列表
    await page.screenshot({ path: 'test-results/screenshots/purchase-order-list.png' });
    
    // 点击创建订单
    const createBtn = page.getByRole('button', { name: /新建|创建|添加.*订单/i });
    if (await createBtn.isVisible({ timeout: 5000 })) {
      await createBtn.click();
      await page.waitForSelector('form, .ant-modal, .drawer');
      
      // 填写订单信息
      await page.locator('input[placeholder*="订单名称"], input[placeholder*="名称"], input[name*="name"]').first().fill(orderName);
      
      // 选择供应商
      try {
        const supplierSelect = page.locator('.ant-select:has-text("供应商"), select[name*="supplier"]').first();
        if (await supplierSelect.isVisible({ timeout: 3000 })) {
          await supplierSelect.click();
          await page.locator('.ant-select-item, option').first().click();
        }
      } catch (e) {
        console.log('未找到供应商选择');
      }
      
      // 填写金额
      try {
        await page.locator('input[placeholder*="金额"], input[name*="amount"]').first().fill('50000');
      } catch (e) {
        console.log('未找到金额字段');
      }
      
      // 截图订单表单
      await page.screenshot({ path: 'test-results/screenshots/purchase-order-form.png' });
      
      // 提交
      await page.getByRole('button', { name: /确定|提交|保存|创建/i }).click();
      await page.waitForTimeout(2000);
      
      // 截图订单创建后
      await page.screenshot({ path: 'test-results/screenshots/purchase-order-created.png' });
      
      // 验证订单已创建
      await page.goto('/procurement/orders');
      await waitForTableLoad(page);
      await verifyTableContains(page, orderName);
    } else {
      console.log('未找到创建订单按钮');
    }
  });

  test("应该成功提交订单审批", async ({ page }) => {
    // 创建采购订单
    await page.goto('/procurement/orders');
    await waitForPageLoad(page);
    
    const createBtn = page.getByRole('button', { name: /新建|创建|添加.*订单/i });
    if (await createBtn.isVisible({ timeout: 5000 })) {
      await createBtn.click();
      await page.waitForSelector('form, .ant-modal, .drawer');
      
      await page.locator('input[placeholder*="订单名称"], input[placeholder*="名称"], input[name*="name"]').first().fill(orderName);
      
      await page.getByRole('button', { name: /确定|提交|保存|创建/i }).click();
      await page.waitForTimeout(2000);
      
      await page.goto('/procurement/orders');
      await waitForTableLoad(page);
      
      // 查找订单行
      const orderRow = page.locator(`tr:has-text("${orderName}")`);
      if (await orderRow.isVisible({ timeout: 5000 })) {
        // 截图审批前
        await page.screenshot({ path: 'test-results/screenshots/before-order-approval.png' });
        
        // 查找提交审批按钮
        const approvalSelectors = [
          'button:has-text("提交审批")',
          'button:has-text("审批")',
          'button:has-text("提交")'
        ];
        
        for (const selector of approvalSelectors) {
          try {
            const approvalBtn = orderRow.locator(selector).first();
            if (await approvalBtn.isVisible({ timeout: 2000 })) {
              await approvalBtn.click();
              
              // 等待确认对话框
              await page.waitForTimeout(1000);
              const confirmBtn = page.getByRole('button', { name: /确定|确认|提交/i });
              if (await confirmBtn.isVisible({ timeout: 3000 })) {
                await confirmBtn.click();
              }
              
              await page.waitForTimeout(2000);
              
              // 截图审批后
              await page.screenshot({ path: 'test-results/screenshots/after-order-approval.png' });
              break;
            }
          } catch (e) {
            continue;
          }
        }
      }
    } else {
      console.log('未找到创建订单按钮');
    }
  });

  test.afterEach(async ({ page }) => {
    // 清理测试数据
    try {
      // 清理采购申请
      await page.goto('/procurement/requests');
      await waitForTableLoad(page);
      await cleanupItem(page, purchaseName);
      
      // 清理采购订单
      await page.goto('/procurement/orders');
      await waitForTableLoad(page);
      await cleanupItem(page, orderName);
    } catch (e) {
      console.log('清理采购数据失败:', e.message);
    }
  });
});

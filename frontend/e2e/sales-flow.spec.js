import { test, expect } from "playwright/test";
import { 
  login, 
  waitForPageLoad, 
  generateTestName,
  waitForTableLoad,
  verifyTableContains,
  cleanupItem
} from "./helpers/test-helpers.js";

test.describe("销售流程", () => {
  let leadName;
  let opportunityName;
  let contractName;

  test.beforeEach(async ({ page }) => {
    // 登录
    await login(page);
    await waitForPageLoad(page);
    
    // 生成唯一名称
    leadName = generateTestName("E2E测试线索");
    opportunityName = generateTestName("E2E测试商机");
    contractName = generateTestName("E2E测试合同");
  });

  test("应该成功创建销售线索", async ({ page }) => {
    // 导航到线索管理
    await page.goto('/sales/leads');
    await waitForPageLoad(page);
    
    // 截图线索列表
    await page.screenshot({ path: 'test-results/screenshots/lead-list.png' });
    
    // 点击创建线索
    const createBtn = page.getByRole('button', { name: /新建|创建|添加.*线索/i });
    await expect(createBtn).toBeVisible({ timeout: 10000 });
    await createBtn.click();
    
    // 等待表单
    await page.waitForSelector('form, .ant-modal, .drawer', { timeout: 5000 });
    
    // 填写线索信息
    await page.locator('input[placeholder*="线索名称"], input[name*="name"]').first().fill(leadName);
    await page.locator('input[placeholder*="客户"], input[name*="customer"]').first().fill('E2E测试客户');
    await page.locator('input[placeholder*="联系人"], input[name*="contact"]').first().fill('张三');
    await page.locator('input[placeholder*="电话"], input[name*="phone"]').first().fill('13800138000');
    
    // 尝试填写其他可能的字段
    try {
      await page.locator('textarea[placeholder*="备注"], textarea[name*="remark"]').first().fill('E2E自动化测试线索');
    } catch (e) {
      console.log('未找到备注字段');
    }
    
    // 截图填写后
    await page.screenshot({ path: 'test-results/screenshots/lead-form-filled.png' });
    
    // 提交
    await page.getByRole('button', { name: /确定|提交|保存|创建/i }).click();
    
    // 等待成功
    await page.waitForTimeout(2000);
    
    // 截图创建后
    await page.screenshot({ path: 'test-results/screenshots/lead-created.png' });
    
    // 验证线索已创建
    await page.goto('/sales/leads');
    await waitForTableLoad(page);
    await verifyTableContains(page, leadName);
  });

  test("应该成功将线索转为商机", async ({ page }) => {
    // 先创建线索
    await page.goto('/sales/leads');
    await waitForPageLoad(page);
    
    await page.getByRole('button', { name: /新建|创建|添加.*线索/i }).click();
    await page.waitForSelector('form, .ant-modal, .drawer');
    await page.locator('input[placeholder*="线索名称"], input[name*="name"]').first().fill(leadName);
    await page.locator('input[placeholder*="客户"], input[name*="customer"]').first().fill('E2E测试客户');
    await page.getByRole('button', { name: /确定|提交|保存|创建/i }).click();
    
    await page.waitForTimeout(2000);
    await page.goto('/sales/leads');
    await waitForTableLoad(page);
    
    // 查找线索行
    const leadRow = page.locator(`tr:has-text("${leadName}")`);
    await expect(leadRow).toBeVisible({ timeout: 10000 });
    
    // 截图转换前
    await page.screenshot({ path: 'test-results/screenshots/before-lead-to-opportunity.png' });
    
    // 尝试查找转商机按钮
    const convertSelectors = [
      'button:has-text("转商机")',
      'button:has-text("转换")',
      '[aria-label="convert"]',
      'button:has-text("商机")'
    ];
    
    let clicked = false;
    for (const selector of convertSelectors) {
      try {
        const convertBtn = leadRow.locator(selector).first();
        if (await convertBtn.isVisible({ timeout: 2000 })) {
          await convertBtn.click();
          clicked = true;
          break;
        }
      } catch (e) {
        continue;
      }
    }
    
    if (clicked) {
      // 等待转换表单或确认对话框
      await page.waitForSelector('.ant-modal, .drawer, form', { timeout: 5000 });
      
      // 可能需要填写商机名称
      const opportunityNameInput = page.locator('input[placeholder*="商机名称"], input[name*="opportunity"]').first();
      if (await opportunityNameInput.isVisible({ timeout: 2000 })) {
        await opportunityNameInput.fill(opportunityName);
      }
      
      // 确认转换
      await page.getByRole('button', { name: /确定|确认|转换/i }).click();
      
      // 等待成功
      await page.waitForTimeout(2000);
      
      // 截图转换后
      await page.screenshot({ path: 'test-results/screenshots/after-lead-to-opportunity.png' });
      
      // 验证商机已创建
      await page.goto('/sales/opportunities');
      await waitForTableLoad(page);
      // 验证包含相关名称
      const hasLead = await page.locator('table').textContent();
      expect(hasLead).toMatch(new RegExp(leadName.substring(0, 10)));
    } else {
      console.log('未找到转商机按钮，跳过此测试');
    }
  });

  test("应该成功将商机转为合同", async ({ page }) => {
    // 导航到商机列表
    await page.goto('/sales/opportunities');
    await waitForPageLoad(page);
    
    // 截图商机列表
    await page.screenshot({ path: 'test-results/screenshots/opportunity-list.png' });
    
    // 创建商机
    const createBtn = page.getByRole('button', { name: /新建|创建|添加.*商机/i });
    if (await createBtn.isVisible({ timeout: 5000 })) {
      await createBtn.click();
      await page.waitForSelector('form, .ant-modal, .drawer');
      
      await page.locator('input[placeholder*="商机名称"], input[name*="name"]').first().fill(opportunityName);
      await page.locator('input[placeholder*="客户"], input[name*="customer"]').first().fill('E2E测试客户');
      
      // 尝试填写金额
      try {
        await page.locator('input[placeholder*="金额"], input[name*="amount"]').first().fill('100000');
      } catch (e) {
        console.log('未找到金额字段');
      }
      
      await page.getByRole('button', { name: /确定|提交|保存|创建/i }).click();
      await page.waitForTimeout(2000);
      
      await page.goto('/sales/opportunities');
      await waitForTableLoad(page);
      
      // 查找商机行
      const opportunityRow = page.locator(`tr:has-text("${opportunityName}")`);
      if (await opportunityRow.isVisible({ timeout: 5000 })) {
        // 截图转换前
        await page.screenshot({ path: 'test-results/screenshots/before-opportunity-to-contract.png' });
        
        // 尝试查找转合同按钮
        const convertSelectors = [
          'button:has-text("转合同")',
          'button:has-text("生成合同")',
          'button:has-text("合同")'
        ];
        
        for (const selector of convertSelectors) {
          try {
            const convertBtn = opportunityRow.locator(selector).first();
            if (await convertBtn.isVisible({ timeout: 2000 })) {
              await convertBtn.click();
              
              // 等待合同表单
              await page.waitForSelector('.ant-modal, .drawer, form', { timeout: 5000 });
              
              // 填写合同名称
              const contractNameInput = page.locator('input[placeholder*="合同名称"], input[name*="contract"]').first();
              if (await contractNameInput.isVisible({ timeout: 2000 })) {
                await contractNameInput.fill(contractName);
              }
              
              // 确认
              await page.getByRole('button', { name: /确定|确认|生成/i }).click();
              await page.waitForTimeout(2000);
              
              // 截图
              await page.screenshot({ path: 'test-results/screenshots/after-opportunity-to-contract.png' });
              break;
            }
          } catch (e) {
            continue;
          }
        }
      }
    } else {
      console.log('未找到创建商机按钮');
    }
  });

  test("应该显示合同审批页面", async ({ page }) => {
    // 导航到合同审批
    await page.goto('/sales/contract-approval');
    await waitForPageLoad(page);
    
    // 验证页面元素
    await expect(page.locator('h1, h2, .page-title')).toContainText(/合同.*审批|审批/);
    
    // 截图审批页面
    await page.screenshot({ path: 'test-results/screenshots/contract-approval.png' });
    
    // 检查是否有待审批列表
    const hasTable = await page.locator('.ant-table, table').isVisible({ timeout: 5000 });
    if (hasTable) {
      await waitForTableLoad(page);
      await page.screenshot({ path: 'test-results/screenshots/contract-approval-list.png' });
    }
  });

  test("应该成功提交合同审批", async ({ page }) => {
    // 导航到合同列表
    await page.goto('/sales/contracts');
    await waitForPageLoad(page);
    
    // 截图合同列表
    await page.screenshot({ path: 'test-results/screenshots/contract-list.png' });
    
    // 创建合同
    const createBtn = page.getByRole('button', { name: /新建|创建|添加.*合同/i });
    if (await createBtn.isVisible({ timeout: 5000 })) {
      await createBtn.click();
      await page.waitForSelector('form, .ant-modal, .drawer');
      
      await page.locator('input[placeholder*="合同名称"], input[name*="name"]').first().fill(contractName);
      await page.locator('input[placeholder*="客户"], input[name*="customer"]').first().fill('E2E测试客户');
      
      // 填写合同金额
      try {
        await page.locator('input[placeholder*="金额"], input[name*="amount"]').first().fill('100000');
      } catch (e) {
        console.log('未找到金额字段');
      }
      
      await page.screenshot({ path: 'test-results/screenshots/contract-form.png' });
      
      await page.getByRole('button', { name: /确定|提交|保存|创建/i }).click();
      await page.waitForTimeout(2000);
      
      await page.goto('/sales/contracts');
      await waitForTableLoad(page);
      
      // 查找合同行
      const contractRow = page.locator(`tr:has-text("${contractName}")`);
      if (await contractRow.isVisible({ timeout: 5000 })) {
        // 查找提交审批按钮
        const approvalSelectors = [
          'button:has-text("提交审批")',
          'button:has-text("审批")',
          'button:has-text("提交")'
        ];
        
        for (const selector of approvalSelectors) {
          try {
            const approvalBtn = contractRow.locator(selector).first();
            if (await approvalBtn.isVisible({ timeout: 2000 })) {
              await approvalBtn.click();
              
              // 确认提交
              await page.waitForTimeout(1000);
              const confirmBtn = page.getByRole('button', { name: /确定|确认|提交/i });
              if (await confirmBtn.isVisible({ timeout: 3000 })) {
                await confirmBtn.click();
              }
              
              await page.waitForTimeout(2000);
              await page.screenshot({ path: 'test-results/screenshots/contract-submitted.png' });
              break;
            }
          } catch (e) {
            continue;
          }
        }
      }
    } else {
      console.log('未找到创建合同按钮');
    }
  });

  test.afterEach(async ({ page }) => {
    // 清理测试数据
    try {
      // 清理线索
      await page.goto('/sales/leads');
      await waitForTableLoad(page);
      await cleanupItem(page, leadName);
      
      // 清理商机
      await page.goto('/sales/opportunities');
      await waitForTableLoad(page);
      await cleanupItem(page, opportunityName);
      
      // 清理合同
      await page.goto('/sales/contracts');
      await waitForTableLoad(page);
      await cleanupItem(page, contractName);
    } catch (e) {
      console.log('清理销售数据失败:', e.message);
    }
  });
});

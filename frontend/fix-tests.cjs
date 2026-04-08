const fs = require('fs');
const path = require('path');

// 扫描测试文件目录
function scanTestFiles(dir, files = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      scanTestFiles(fullPath, files);
    } else if (entry.name.endsWith('.test.js')) {
      files.push(fullPath);
    }
  }
  return files;
}

// 检查文件是否有需要修复的 vi.mock
function needsFix(content) {
  // 检查是否有类似 adminApi as xxxApi 这样的导入
  const importPattern = /import\s+\{[^}]*\b(adminApi|settlementApi|projectApi|purchaseApi|productionApi|warehouseApi|timesheetApi)[^}]*\}\s+from\s+['"]\.\.\/\.\.\/\.\.\/services\/api['"]/;
  const hasApiImport = importPattern.test(content);
  // 检查是否有默认的 mock 但没有为具体 API 添加 mock
  const hasDefaultMock = content.includes('default: {') && content.includes('get: vi.fn()');
  // 检查是否有 .list.mockResolvedValue 调用
  const hasListMock = content.includes('.list.mockResolvedValue');
  
  return hasApiImport && hasDefaultMock && hasListMock;
}

// 修复测试文件
function fixTestFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf-8');
  
  // 找到导入的 API 名称
  const apiMatch = content.match(/import\s+\{[^}]*\b(adminApi|settlementApi|projectApi|purchaseApi|productionApi|warehouseApi|timesheetApi|supplierApi|bomApi|qualityApi|serviceApi|scheduleApi|contractApi|customerApi|salesApi|engineerApi|hrApi|departmentApi|workerApi|customerServiceApi|acceptanceApi|shortageApi|materialApi|technicalApi|productionPlanApi|productionExceptionApi|assemblyKitApi)[^}]*\}\s+from\s+['"]\.\.\/\.\.\/\.\.\/services\/api['"]/);
  
  if (!apiMatch) return false;
  
  // 提取导入的 API 名称
  const importPart = apiMatch[0];
  const apiNames = [];
  const namePattern = /\b(adminApi|settlementApi|projectApi|purchaseApi|productionApi|warehouseApi|timesheetApi|supplierApi|bomApi|qualityApi|serviceApi|scheduleApi|contractApi|customerApi|salesApi|engineerApi|hrApi|departmentApi|workerApi|customerServiceApi|acceptanceApi|shortageApi|materialApi|technicalApi|productionPlanApi|productionExceptionApi|assemblyKitApi)\b/g;
  let match;
  while ((match = namePattern.exec(importPart)) !== null) {
    apiNames.push(match[1]);
  }
  
  if (apiNames.length === 0) return false;
  
  // 检查是否已经有该 API 的 mock 定义
  for (const apiName of apiNames) {
    const hasApiMock = content.includes(`${apiName}: {`) || content.includes(`${apiName}:`);
    if (!hasApiMock) {
      // 添加 API mock
      const apiMock = `    ${apiName}: {\n      list: vi.fn(),\n      get: vi.fn(),\n      query: vi.fn(),\n      create: vi.fn(),\n      update: vi.fn(),\n      delete: vi.fn(),\n      aiMatch: vi.fn(),\n    },`;
      
      // 找到 return { 的位置，在 default 后面添加
      content = content.replace(
        /(\s+default:\s*\{[^}]+\},?\s*)\}/,
        `$1\n${apiMock}\n  }`
      );
    }
  }
  
  fs.writeFileSync(filePath, content);
  console.log(`Fixed: ${filePath}`);
  return true;
}

// 主程序
const testDir = path.join(__dirname, 'src/pages');
const files = scanTestFiles(testDir);

let fixedCount = 0;
for (const file of files) {
  const content = fs.readFileSync(file, 'utf-8');
  if (needsFix(content)) {
    if (fixTestFile(file)) {
      fixedCount++;
    }
  }
}

console.log(`Total files scanned: ${files.length}`);
console.log(`Files fixed: ${fixedCount}`);
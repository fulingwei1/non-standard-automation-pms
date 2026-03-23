/**
 * 修复 hook 测试文件中 API mock 不正确的问题
 *
 * 问题：vi.mock 使用 importOriginal + spread，导致真实的 API 对象被保留
 * 真实函数没有 mockResolvedValue 方法
 *
 * 修复：将 API 对象的所有方法替换为 vi.fn()
 */
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { resolve } from 'path';

const PROJECT_ROOT = '/Users/flw/non-standard-automation-pm/frontend';

// 获取所有失败的 hook 测试文件
const allFailing = readFileSync('/tmp/still_failing.txt', 'utf-8')
  .split('\n')
  .filter(Boolean);

// 只处理包含 "api.list.mockResolvedValue" 模式的 hook 测试
const hookTests = allFailing.filter(f => f.includes('hooks/__tests__/'));

let fixed = 0;

for (const testFile of hookTests) {
  const absPath = resolve(PROJECT_ROOT, testFile);
  if (!existsSync(absPath)) continue;

  const content = readFileSync(absPath, 'utf-8');

  // 检查是否包含有问题的 mock 模式
  if (!content.includes('async (importOriginal)') || !content.includes('mockResolvedValue')) {
    continue;
  }

  // 提取 import 的 API 对象名（例如 bomApi, alertApi）
  const apiImportMatch = content.match(/import\s*\{\s*(\w+)\s*\}\s*from\s*['"].*services\/api['"]/);
  if (!apiImportMatch) continue;

  const apiName = apiImportMatch[1];

  // 找到 API 模块路径
  const apiPathMatch = content.match(/vi\.mock\(['"]([^'"]+services\/api)['"]/);
  if (!apiPathMatch) continue;
  const apiPath = apiPathMatch[1];

  // 收集 beforeEach 中使用的方法名
  const methodNames = new Set();
  const methodRegex = new RegExp(`(?:api|${apiName})\\.(\w+)(?:\\.mock|\\s)`, 'g');
  let m;
  while ((m = methodRegex.exec(content)) !== null) {
    methodNames.add(m[1]);
  }
  // 添加常见方法作为默认
  ['list', 'get', 'create', 'update', 'delete', 'query'].forEach(n => methodNames.add(n));

  // 构建 mock 方法对象
  const mockMethods = Array.from(methodNames).map(n => `    ${n}: vi.fn()`).join(',\n');

  // 替换 vi.mock
  const oldMockRegex = /vi\.mock\(['"]([^'"]+services\/api)['"]\s*,\s*async\s*\(importOriginal\)\s*=>\s*\{[\s\S]*?\}\s*\);/;
  const oldMockMatch = content.match(oldMockRegex);

  if (!oldMockMatch) continue;

  const newMock = `vi.mock('${apiPath}', () => ({
  ${apiName}: {
${mockMethods},
  },
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn(),
    defaults: { baseURL: '/api' },
  },
}));`;

  const newContent = content.replace(oldMockMatch[0], newMock);

  if (newContent !== content) {
    writeFileSync(absPath, newContent, 'utf-8');

    // 验证
    const verify = readFileSync(absPath, 'utf-8');
    if (verify.includes(apiName + ': {')) {
      fixed++;
      console.log(`OK ${testFile}: mocked ${apiName} with methods [${Array.from(methodNames).join(', ')}]`);
    } else {
      console.log(`WRITE FAILED ${testFile}`);
    }
  }
}

console.log(`\nFixed ${fixed} hook test files`);

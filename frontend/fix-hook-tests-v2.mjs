/**
 * 修复 hook 测试文件中 API mock 不正确的问题 (v2)
 * 处理多 API 导入和别名情况
 */
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { resolve } from 'path';

const PROJECT_ROOT = '/Users/flw/non-standard-automation-pm/frontend';

const allFailing = readFileSync('/tmp/still_failing.txt', 'utf-8')
  .split('\n')
  .filter(Boolean);

const hookTests = allFailing.filter(f => f.includes('hooks/__tests__/'));

let fixed = 0;

for (const testFile of hookTests) {
  const absPath = resolve(PROJECT_ROOT, testFile);
  if (!existsSync(absPath)) continue;

  const content = readFileSync(absPath, 'utf-8');

  // 检查是否仍包含有问题的 mock 模式
  if (!content.includes('async (importOriginal)') || !content.includes('mockResolvedValue')) {
    continue;
  }

  // 提取所有 import 的 API 对象名（处理多个导入和别名）
  // 格式: import { apiA, apiB as aliasB } from '...services/api'
  const apiImportMatch = content.match(/import\s*\{([^}]+)\}\s*from\s*['"][^'"]*services\/api['"]/);
  if (!apiImportMatch) continue;

  // 解析导入的名字，提取原始导出名（不是别名）
  const importedNames = apiImportMatch[1].split(',').map(s => {
    const trimmed = s.trim();
    // 处理 "apiName as alias" 模式，需要原始名字用于 mock
    const parts = trimmed.split(/\s+as\s+/);
    return {
      original: parts[0].trim(),
      alias: parts.length > 1 ? parts[1].trim() : parts[0].trim(),
    };
  }).filter(n => n.original);

  // 找到 API 模块路径
  const apiPathMatch = content.match(/vi\.mock\(['"]([^'"]+services\/api)['"]/);
  if (!apiPathMatch) continue;
  const apiPath = apiPathMatch[1];

  // 收集 beforeEach 中使用的方法名（查找所有 api.xxx.mock 模式）
  const allMethodNames = new Set(['list', 'get', 'create', 'update', 'delete', 'query']);
  const methodRegex = /(?:api|Api)\.\s*(\w+)\s*(?:\.\s*mock|(?:&&|\|\|))/g;
  let m;
  while ((m = methodRegex.exec(content)) !== null) {
    allMethodNames.add(m[1]);
  }
  // 也查找 api.xxx.mockXxx 模式
  const mockMethodRegex = /\.\s*(\w+)\s*\.\s*mock(?:Resolved|Rejected|Implementation)/g;
  while ((m = mockMethodRegex.exec(content)) !== null) {
    allMethodNames.add(m[1]);
  }

  // 构建每个 API 对象的 mock
  const mockMethods = Array.from(allMethodNames).map(n => `      ${n}: vi.fn()`).join(',\n');

  const apiMocks = importedNames.map(({ original }) => {
    return `  ${original}: {\n${mockMethods},\n  }`;
  }).join(',\n');

  // 替换 vi.mock
  const oldMockRegex = /vi\.mock\(['"]([^'"]+services\/api)['"]\s*,\s*async\s*\(importOriginal\)\s*=>\s*\{[\s\S]*?\}\s*\);/;
  const oldMockMatch = content.match(oldMockRegex);

  if (!oldMockMatch) continue;

  const newMock = `vi.mock('${apiPath}', () => ({
${apiMocks},
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
    if (!verify.includes('async (importOriginal)')) {
      fixed++;
      console.log(`OK ${testFile}: mocked [${importedNames.map(n => n.original).join(', ')}]`);
    } else {
      console.log(`WRITE FAILED ${testFile}`);
    }
  }
}

console.log(`\nFixed ${fixed} additional hook test files`);

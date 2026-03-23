/**
 * 修复使用 PageHeader 但未导入的页面测试
 * 在测试文件的 vi.mock 区域添加 PageHeader 的全局定义
 */
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { resolve } from 'path';

const PROJECT_ROOT = '/Users/flw/non-standard-automation-pm/frontend';

const files = [
  'src/pages/__tests__/BOMManagement.test.jsx',
  'src/pages/__tests__/InventoryAnalysis.test.jsx',
  'src/pages/__tests__/MaterialTracking.test.jsx',
  'src/pages/__tests__/ProductionModuleSmoke.test.jsx',
  'src/pages/__tests__/QualificationManagement.test.jsx',
  'src/pages/__tests__/ServiceRecord.test.jsx',
  'src/pages/__tests__/WorkOrderManagement.test.jsx',
  'src/pages/__tests__/WorkshopManagement.test.jsx',
  'src/pages/SalesFunnel.test.jsx',
];

// PageHeader 和 Tag（来自 antd）mock
const globalSetup = `
// 全局定义缺失的组件（源文件中使用但未导入）
globalThis.PageHeader = ({ title, children, extra, ...props }) => (
  <div data-testid="page-header" {...props}>
    {title && <h1>{title}</h1>}
    {extra && <div>{extra}</div>}
    {children}
  </div>
);
globalThis.Tag = ({ children, color, ...props }) => (
  <span data-testid="tag" style={{ color }} {...props}>{children}</span>
);
`;

let fixed = 0;

for (const file of files) {
  const absPath = resolve(PROJECT_ROOT, file);
  if (!existsSync(absPath)) continue;

  const content = readFileSync(absPath, 'utf-8');

  // 检查是否已经有 PageHeader 定义
  if (content.includes('globalThis.PageHeader') || content.includes("global.PageHeader")) {
    continue;
  }

  // 找到第一个 describe 之前插入
  const describeIndex = content.indexOf('describe(');
  if (describeIndex === -1) continue;

  const newContent = content.slice(0, describeIndex) + globalSetup + '\n' + content.slice(describeIndex);
  writeFileSync(absPath, newContent, 'utf-8');

  const verify = readFileSync(absPath, 'utf-8');
  if (verify.includes('globalThis.PageHeader')) {
    fixed++;
    console.log(`OK ${file}`);
  }
}

console.log(`\nFixed ${fixed} files`);

/**
 * 自动修复测试文件中缺失的导入
 * 策略：读取每个失败的测试文件，分析 JSX 中使用但未导入的符号，添加正确的 import
 */
import { readFileSync, writeFileSync, existsSync, readdirSync } from 'fs';
import { dirname, basename, resolve, relative } from 'path';

const PROJECT_ROOT = '/Users/flw/non-standard-automation-pm/frontend';
const SRC = `${PROJECT_ROOT}/src`;

const failingTests = readFileSync('/tmp/still_failing.txt', 'utf-8')
  .split('\n')
  .filter(Boolean);

/**
 * 扫描目录，查找指定组件名的源文件
 */
function findSourceFile(testDir, componentName) {
  // testDir 是 __tests__ 目录的绝对路径
  const parentDir = dirname(testDir);

  // 尝试在父目录中查找各种形式的文件名
  const variants = [
    `${componentName}.jsx`,
    `${componentName}.tsx`,
    `${componentName}.js`,
    `${componentName}/index.jsx`,
    `${componentName}/index.tsx`,
    `${componentName}/index.js`,
    `${componentName}/${componentName}.jsx`,
    // 小写首字母
    `${componentName.charAt(0).toLowerCase() + componentName.slice(1)}.jsx`,
    `${componentName.charAt(0).toLowerCase() + componentName.slice(1)}.tsx`,
    `${componentName.charAt(0).toLowerCase() + componentName.slice(1)}.js`,
  ];

  for (const v of variants) {
    const fullPath = resolve(parentDir, v);
    if (existsSync(fullPath)) {
      // 获取实际文件名（处理大小写）
      const dir = dirname(fullPath);
      const base = basename(fullPath);
      try {
        const actualFiles = readdirSync(dir);
        const actualName = actualFiles.find(f => f.toLowerCase() === base.toLowerCase());
        if (actualName) {
          return resolve(dir, actualName);
        }
      } catch {
        return fullPath;
      }
    }
  }
  return null;
}

/**
 * 检查源文件的导出类型
 */
function getExportType(filePath, symbolName) {
  try {
    const content = readFileSync(filePath, 'utf-8');

    // 检查 export default
    if (/export\s+default\s+/.test(content)) {
      // 检查是否同时有命名导出
      const namedExportRegex = new RegExp(
        `export\\s+(?:function|const|class|let|var)\\s+${symbolName}\\b|` +
        `export\\s*\\{[^}]*\\b${symbolName}\\b`
      );
      if (namedExportRegex.test(content)) {
        return 'named';
      }
      return 'default';
    }

    // 只有命名导出
    return 'named';
  } catch {
    return 'named'; // 默认假设命名导出
  }
}

/**
 * 从源文件中获取所有命名导出
 */
function getNamedExports(filePath) {
  try {
    const content = readFileSync(filePath, 'utf-8');
    const exports = new Set();

    // export function Name
    const funcRegex = /export\s+(?:function|const|class|let|var)\s+(\w+)/g;
    let m;
    while ((m = funcRegex.exec(content)) !== null) {
      exports.add(m[1]);
    }

    // export { Name1, Name2 }
    const bracketRegex = /export\s*\{([^}]+)\}/g;
    while ((m = bracketRegex.exec(content)) !== null) {
      m[1].split(',').forEach(s => {
        const name = s.trim().split(/\s+as\s+/)[0].trim();
        if (name && /^[A-Z]/.test(name)) exports.add(name);
      });
    }

    return exports;
  } catch {
    return new Set();
  }
}

/**
 * 分析测试文件，找出 JSX 中使用但未导入的组件
 */
function findMissingImports(content) {
  // 收集所有已导入的符号
  const imported = new Set();

  // import { A, B } from '...'
  const namedImportRegex = /import\s*\{([^}]+)\}\s*from/g;
  let m;
  while ((m = namedImportRegex.exec(content)) !== null) {
    m[1].split(',').forEach(s => {
      const parts = s.trim().split(/\s+as\s+/);
      const name = parts.length > 1 ? parts[1].trim() : parts[0].trim();
      if (name) imported.add(name);
    });
  }

  // import Default from '...'
  const defaultImportRegex = /import\s+(\w+)\s+from/g;
  while ((m = defaultImportRegex.exec(content)) !== null) {
    imported.add(m[1]);
  }

  // import Default, { Named } from '...'
  const mixedImportRegex = /import\s+(\w+)\s*,\s*\{([^}]+)\}\s*from/g;
  while ((m = mixedImportRegex.exec(content)) !== null) {
    imported.add(m[1]);
    m[2].split(',').forEach(s => {
      const name = s.trim().split(/\s+as\s+/).pop().trim();
      if (name) imported.add(name);
    });
  }

  // 收集 JSX 中使用的组件（大写开头标签）
  const usedComponents = new Set();
  const jsxTagRegex = /<([A-Z]\w+)/g;
  while ((m = jsxTagRegex.exec(content)) !== null) {
    usedComponents.add(m[1]);
  }

  // 也检查函数调用中的组件引用
  const funcCallRegex = /(?:render|createElement|React\.createElement)\(\s*([A-Z]\w+)/g;
  while ((m = funcCallRegex.exec(content)) !== null) {
    usedComponents.add(m[1]);
  }

  // 检查变量声明（const X = ...）— 这些不需要导入
  const localDefs = new Set();
  const localDefRegex = /(?:const|let|var|function)\s+([A-Z]\w+)/g;
  while ((m = localDefRegex.exec(content)) !== null) {
    localDefs.add(m[1]);
  }

  // 找出未导入也未本地定义的组件
  const missing = [];
  for (const comp of usedComponents) {
    if (!imported.has(comp) && !localDefs.has(comp)) {
      missing.push(comp);
    }
  }

  return missing;
}

/**
 * 找到最后一个 import 语句的行号
 */
function findLastImportLine(lines) {
  let lastImport = -1;
  for (let i = 0; i < lines.length; i++) {
    if (/^import\s+/.test(lines[i].trim())) {
      lastImport = i;
    }
  }
  return lastImport;
}

// ==================== 主逻辑 ====================

let filesFixed = 0;
let importCount = 0;
const results = [];

for (const testFile of failingTests) {
  const absPath = resolve(PROJECT_ROOT, testFile);
  if (!existsSync(absPath)) {
    console.log(`SKIP (not found): ${testFile}`);
    continue;
  }

  let content = readFileSync(absPath, 'utf-8');
  const missing = findMissingImports(content);

  if (missing.length === 0) {
    results.push({ file: testFile, status: 'no-missing-imports' });
    continue;
  }

  const testDir = dirname(absPath);
  const importsToAdd = [];

  // 分组：react-router-dom 组件
  const routerComponents = missing.filter(c =>
    ['MemoryRouter', 'BrowserRouter', 'Routes', 'Route', 'Link', 'Navigate', 'Outlet'].includes(c)
  );
  if (routerComponents.length > 0) {
    importsToAdd.push(`import { ${routerComponents.join(', ')} } from 'react-router-dom';`);
  }

  // 分组：Ant Design 组件
  const antdComponents = missing.filter(c =>
    ['Tag', 'Table', 'Form', 'Modal', 'Select', 'DatePicker', 'Space', 'Spin', 'Empty',
     'Tooltip', 'Popconfirm', 'Dropdown', 'Menu', 'TreeSelect', 'Cascader', 'Switch',
     'Transfer', 'Upload', 'Steps', 'Collapse', 'Divider', 'Rate', 'Result',
     'Statistic', 'Timeline', 'Tree', 'Pagination', 'Alert', 'Drawer',
     'Descriptions', 'Image', 'List', 'Segmented', 'Typography', 'ConfigProvider',
     'Row', 'Col', 'Layout', 'Breadcrumb', 'PageHeader', 'Affix', 'AutoComplete',
     'BackTop', 'Calendar', 'Card', 'Carousel', 'Checkbox', 'Comment',
     'InputNumber', 'Mentions', 'Radio', 'Slider', 'TimePicker'].includes(c)
  );
  // Note: 不添加 antd 导入，因为这些可能是自定义组件或需要特殊处理

  // 分组：framer-motion 组件
  const motionComponents = missing.filter(c => c === 'AnimatePresence');

  // 其他组件：从本地源文件导入
  const otherComponents = missing.filter(c =>
    !routerComponents.includes(c) &&
    !antdComponents.includes(c) &&
    !motionComponents.includes(c)
  );

  // 按源文件分组
  const sourceGroups = {}; // { importPath: { default: name|null, named: [names] } }

  for (const comp of otherComponents) {
    const sourceFile = findSourceFile(testDir, comp);
    if (sourceFile) {
      const relPath = relative(testDir, sourceFile)
        .replace(/\\/g, '/')
        .replace(/\.(jsx|tsx|js|ts)$/, '')
        .replace(/\/index$/, ''); // 简化 /index 路径
      const importPath = relPath.startsWith('.') ? relPath : `./${relPath}`;

      const exportType = getExportType(sourceFile, comp);

      if (!sourceGroups[importPath]) {
        sourceGroups[importPath] = { default: null, named: [], sourceFile };
      }

      if (exportType === 'default') {
        sourceGroups[importPath].default = comp;
      } else {
        sourceGroups[importPath].named.push(comp);
      }
    } else {
      // 组件源文件未找到，记录但不处理
      results.push({ file: testFile, status: 'source-not-found', component: comp });
    }
  }

  // 对于同一个源文件中的多个命名导出，合并导入
  for (const [importPath, info] of Object.entries(sourceGroups)) {
    // 对于命名导出，检查源文件中是否真的有这些导出
    if (info.named.length > 0 && info.sourceFile) {
      const actualExports = getNamedExports(info.sourceFile);
      // 过滤出源文件中确实存在的导出
      info.named = info.named.filter(n => {
        // 如果源文件只有 default export，把第一个添加为 default
        if (!actualExports.has(n) && !info.default) {
          const content = readFileSync(info.sourceFile, 'utf-8');
          if (/export\s+default/.test(content)) {
            info.default = n;
            return false;
          }
        }
        return true; // 保留（即使不确定）
      });
    }

    let importStatement = '';
    if (info.default && info.named.length > 0) {
      importStatement = `import ${info.default}, { ${info.named.join(', ')} } from '${importPath}';`;
    } else if (info.default) {
      importStatement = `import ${info.default} from '${importPath}';`;
    } else if (info.named.length > 0) {
      importStatement = `import { ${info.named.join(', ')} } from '${importPath}';`;
    }

    if (importStatement) {
      importsToAdd.push(importStatement);
    }
  }

  if (importsToAdd.length === 0) {
    results.push({ file: testFile, status: 'no-imports-resolved', missing });
    continue;
  }

  // 插入 import 语句
  const lines = content.split('\n');
  const lastImportLine = findLastImportLine(lines);
  const insertAt = lastImportLine >= 0 ? lastImportLine + 1 : 0;

  const newLines = [
    ...lines.slice(0, insertAt),
    ...importsToAdd,
    ...lines.slice(insertAt),
  ];

  const newContent = newLines.join('\n');
  writeFileSync(absPath, newContent, 'utf-8');

  // 验证写入成功
  const verifyContent = readFileSync(absPath, 'utf-8');
  const verified = importsToAdd.every(imp => verifyContent.includes(imp));

  if (verified) {
    filesFixed++;
    importCount += importsToAdd.length;
    console.log(`OK ${testFile}: +${importsToAdd.length} imports`);
    for (const imp of importsToAdd) {
      console.log(`   ${imp}`);
    }
  } else {
    console.log(`WRITE FAILED ${testFile}`);
  }
}

console.log(`\n=== Summary ===`);
console.log(`Files fixed: ${filesFixed}`);
console.log(`Imports added: ${importCount}`);

// Show files that couldn't be fixed
const unfixed = results.filter(r => r.status !== 'no-missing-imports');
if (unfixed.length > 0) {
  console.log(`\nUnresolved files:`);
  for (const r of unfixed) {
    console.log(`  ${r.file}: ${r.status} ${r.component || ''} ${r.missing ? r.missing.join(',') : ''}`);
  }
}

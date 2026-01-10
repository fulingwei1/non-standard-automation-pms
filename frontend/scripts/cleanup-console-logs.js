/**
 * 前端 console.log 清理脚本
 * 用法: node frontend/scripts/cleanup-console-logs.js
 */

const fs = require('fs');
const path = require('path');

const srcDir = path.join(__dirname, '../src');

// 需要清理的 console 类型
const CONSOLE_PATTERNS = [
  // 调试用的 console.log
  { pattern: /console\.log\([^)]*\)/g, type: 'debug' },
  // 保留 console.error 和 console.warn，但可以格式化
];

// 统计
let totalFiles = 0;
let totalRemoved = 0;

function cleanFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let originalContent = content;
  let removed = 0;

  // 清理 console.log
  content = content.replace(/console\.log\([^)]*\)/g, () => {
    removed++;
    return '';
  });

  // 清理连续的空行
  content = content.replace(/\n\s*\n\s*\n/g, '\n\n');

  if (content !== originalContent) {
    fs.writeFileSync(filePath, content);
    console.log(`✓ ${path.relative(srcDir, filePath)}: 移除 ${removed} 个 console.log`);
    totalRemoved += removed;
    totalFiles++;
  }
}

function walkDir(dir) {
  const files = fs.readdirSync(dir);

  for (const file of files) {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);

    if (stat.isDirectory() && !filePath.includes('node_modules')) {
      walkDir(filePath);
    } else if (file.endsWith('.jsx') || file.endsWith('.js')) {
      cleanFile(filePath);
    }
  }
}

console.log('开始清理 console.log...\n');
walkDir(srcDir);
console.log(`\n完成! 共清理 ${totalFiles} 个文件，移除 ${totalRemoved} 个 console.log`);

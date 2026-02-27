#!/usr/bin/env node
/**
 * 检查启用严格 ESLint 配置后的影响
 * 
 * 使用方法：
 * node scripts/check-strict-eslint-impact.js
 */

import { execSync } from 'child_process'
import { readFileSync, writeFileSync, copyFileSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const frontendDir = join(__dirname, '..')

console.log('🔍 检查严格 ESLint 配置的影响...\n')

// 1. 备份当前配置
const currentConfig = join(frontendDir, 'eslint.config.js')
const strictConfig = join(frontendDir, 'eslint.config.strict.js')
const backupConfig = join(frontendDir, 'eslint.config.backup.js')

console.log('📋 步骤 1: 备份当前配置...')
try {
  copyFileSync(currentConfig, backupConfig)
  console.log('✅ 已备份到 eslint.config.backup.js\n')
} catch {
  console.log('⚠️  备份失败（可能已存在）\n')
}

// 2. 临时启用严格配置
console.log('📋 步骤 2: 临时启用严格配置...')
const currentConfigContent = readFileSync(currentConfig, 'utf-8')
const strictConfigContent = readFileSync(strictConfig, 'utf-8')
writeFileSync(currentConfig, strictConfigContent)
console.log('✅ 已临时启用严格配置\n')

// 3. 运行 ESLint 检查
console.log('📋 步骤 3: 运行 ESLint 检查...')
let lintOutput;
let errorCount = 0
let warningCount = 0

try {
  lintOutput = execSync('npm run lint', {
    cwd: frontendDir,
    encoding: 'utf-8',
    stdio: 'pipe'
  })
} catch (error) {
  lintOutput = error.stdout || error.stderr || ''
  
  // 统计错误和警告
  const errorMatches = lintOutput.match(/\s+(\d+)\s+error\(s\)/g)
  const warningMatches = lintOutput.match(/\s+(\d+)\s+warning\(s\)/g)
  
  if (errorMatches) {
    errorCount = errorMatches.reduce((sum, match) => {
      const count = parseInt(match.match(/(\d+)/)[1])
      return sum + count
    }, 0)
  }
  
  if (warningMatches) {
    warningMatches.forEach(match => {
      const count = parseInt(match.match(/(\d+)/)[1])
      warningCount += count
    })
  }
}

// 4. 恢复原配置
console.log('📋 步骤 4: 恢复原配置...')
writeFileSync(currentConfig, currentConfigContent)
console.log('✅ 已恢复原配置\n')

// 5. 输出统计结果
console.log('='.repeat(60))
console.log('📊 检查结果统计')
console.log('='.repeat(60))
console.log(`❌ 错误数量: ${errorCount}`)
console.log(`⚠️  警告数量: ${warningCount}`)
console.log(`📝 总计: ${errorCount + warningCount}`)
console.log('='.repeat(60))

// 6. 保存详细报告
const reportFile = join(frontendDir, 'eslint-strict-report.txt')
writeFileSync(reportFile, lintOutput)
console.log(`\n📄 详细报告已保存到: eslint-strict-report.txt`)

// 7. 给出建议
console.log('\n💡 建议：')
if (errorCount === 0 && warningCount === 0) {
  console.log('✅ 可以安全启用严格配置！')
  console.log('   运行: cp eslint.config.strict.js eslint.config.js')
} else if (errorCount < 50) {
  console.log('⚠️  发现少量问题，建议先修复后再启用')
  console.log('   1. 查看详细报告: cat eslint-strict-report.txt')
  console.log('   2. 运行自动修复: npm run lint -- --fix')
  console.log('   3. 手动修复剩余问题')
  console.log('   4. 启用严格配置: cp eslint.config.strict.js eslint.config.js')
} else if (errorCount < 200) {
  console.log('⚠️  发现较多问题，建议分阶段修复')
  console.log('   1. 先修复未使用的变量/导入（高优先级）')
  console.log('   2. 再修复 React Hooks 依赖问题（中优先级）')
  console.log('   3. 最后修复代码风格问题（低优先级）')
} else {
  console.log('❌ 发现大量问题，建议渐进式启用')
  console.log('   参考: frontend/ENABLE_STRICT_ESLINT.md')
  console.log('   或使用渐进式方案，逐步添加规则')
}

console.log('\n')

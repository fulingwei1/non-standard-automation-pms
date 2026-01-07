/**
 * 角色工作台跳转验证脚本 V2
 * 基于已知的角色配置进行验证
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const nodeProcess = globalThis.process;

const dashboardPath = path.join(__dirname, '../src/pages/Dashboard.jsx');
const appPath = path.join(__dirname, '../src/App.jsx');

const dashboardContent = fs.readFileSync(dashboardPath, 'utf-8');
const appContent = fs.readFileSync(appPath, 'utf-8');

// 已知的角色与工作台映射（从 roleConfig.js 和导航配置中提取）
const expectedMappings = {
  // 管理层
  chairman: '/chairman-dashboard',
  gm: '/gm-dashboard',
  
  // 销售/支持
  sales_director: '/sales-director-dashboard',
  sales_manager: '/sales-manager-dashboard',
  sales: '/sales-dashboard',
  business_support: '/business-support',
  presales: '/presales-dashboard',
  presales_manager: '/presales-manager-dashboard',
  
  // 工程师
  me_engineer: '/workstation',
  ee_engineer: '/workstation',
  sw_engineer: '/workstation',
  te_engineer: '/workstation',
  rd_engineer: '/workstation',
  
  // 装配
  assembler: '/assembly-tasks',
  assembler_mechanic: '/assembly-tasks',
  assembler_electrician: '/assembly-tasks',
  
  // 采购
  procurement_engineer: '/procurement-dashboard',
  
  // 生产
  production_manager: '/production-dashboard',
  
  // 其他角色使用默认 Dashboard (/)
  // 这些角色在 roleDashboardMap 中可能没有定义，或者应该使用 '/'
  admin: '/',
  super_admin: '/',
  dept_manager: '/',
  pm: '/',
  te: '/',
  me_leader: '/',
  ee_leader: '/',
  te_leader: '/',
  buyer: '/',
  warehouse: '/',
  qa: '/',
  pmc: '/',
  finance: '/',
  finance_manager: '/',
  hr_manager: '/',
  viewer: '/',
  project_dept_manager: '/',
  tech_dev_manager: '/',
  me_dept_manager: '/',
  te_dept_manager: '/',
  ee_dept_manager: '/',
  procurement_manager: '/',
  manufacturing_director: '/',
  customer_service_manager: '/',
  customer_service_engineer: '/',
};

// 提取 roleDashboardMap
const roleDashboardMap = {};
const mapMatch = dashboardContent.match(/const roleDashboardMap = \{([\s\S]*?)\n\}/);
if (mapMatch) {
  const mapContent = mapMatch[1];
  const mapMatches = mapContent.matchAll(/(\w+):\s*['"]([^'"]+)['"](?:\s*\/\/[^\n]*)?/g);
  for (const match of mapMatches) {
    roleDashboardMap[match[1]] = match[2];
  }
}

// 提取路由定义
const routes = new Set();
const routeMatches = appContent.matchAll(/path="([^"]+)"\s+element=\{<(\w+)\s*\/>/g);
for (const match of routeMatches) {
  routes.add(match[1]);
}

// 验证函数
function routeExists(path) {
  return routes.has(path);
}

// 执行验证
console.log('='.repeat(80));
console.log('角色工作台跳转配置验证报告');
console.log('='.repeat(80));
console.log('');

const results = [];
let passCount = 0;
let failCount = 0;
let missingCount = 0;
let extraCount = 0;

// 验证所有预期映射
for (const [roleCode, expectedPath] of Object.entries(expectedMappings)) {
  const actualPath = roleDashboardMap[roleCode];
  const routeExistsCheck = routeExists(expectedPath);
  
  let status = '✅';
  let issues = [];
  
  if (!actualPath) {
    if (expectedPath === '/') {
      // 使用默认 Dashboard 的角色，未定义是可以接受的
      status = '⚠️';
      issues.push('未定义（使用默认 Dashboard）');
      missingCount++;
    } else {
      status = '❌';
      issues.push(`未在 roleDashboardMap 中定义，应该跳转到 ${expectedPath}`);
      missingCount++;
    }
  } else if (actualPath !== expectedPath) {
    status = '❌';
    issues.push(`路径不匹配: 期望 ${expectedPath}, 实际 ${actualPath}`);
    failCount++;
  } else if (!routeExistsCheck) {
    status = '❌';
    issues.push(`路由不存在: ${expectedPath}`);
    failCount++;
  } else {
    passCount++;
  }
  
  results.push({
    roleCode,
    expectedPath,
    actualPath: actualPath || '(未定义)',
    routeExists: routeExistsCheck,
    status,
    issues
  });
}

// 检查 roleDashboardMap 中是否有额外的角色
const extraRoles = Object.keys(roleDashboardMap).filter(
  role => !Object.hasOwn(expectedMappings, role)
);
if (extraRoles.length > 0) {
  extraCount = extraRoles.length;
  console.log('⚠️  roleDashboardMap 中存在未预期的角色:');
  extraRoles.forEach(role => {
    console.log(`   ${role}: '${roleDashboardMap[role]}'`);
  });
  console.log('');
}

// 输出结果
console.log('验证结果汇总:');
console.log(`  ✅ 通过: ${passCount}`);
console.log(`  ❌ 失败: ${failCount}`);
console.log(`  ⚠️  缺失: ${missingCount}`);
if (extraCount > 0) {
  console.log(`  ⚠️  额外: ${extraCount}`);
}
console.log(`  总计: ${results.length}`);
console.log('');

// 按状态分组输出
const passed = results.filter(r => r.status === '✅');
const failed = results.filter(r => r.status === '❌');
const missing = results.filter(r => r.status === '⚠️' && r.expectedPath !== '/');

if (failed.length > 0) {
  console.log('❌ 失败的配置:');
  console.log('-'.repeat(80));
  failed.forEach(r => {
    console.log(`${r.status} ${r.roleCode}`);
    console.log(`   期望路径: ${r.expectedPath}`);
    console.log(`   实际路径: ${r.actualPath}`);
    console.log(`   路由存在: ${r.routeExists}`);
    r.issues.forEach(issue => console.log(`   问题: ${issue}`));
    console.log('');
  });
}

if (missing.length > 0) {
  console.log('⚠️  缺失的配置（需要添加）:');
  console.log('-'.repeat(80));
  missing.forEach(r => {
    console.log(`${r.status} ${r.roleCode}`);
    console.log(`   应该跳转到: ${r.expectedPath}`);
    console.log('');
  });
}

if (passed.length > 0 && failed.length === 0 && missing.length === 0) {
  console.log('✅ 所有角色配置正确！');
} else if (passed.length > 0) {
  console.log('');
  console.log('✅ 正确的配置:');
  console.log('-'.repeat(80));
  passed.slice(0, 10).forEach(r => {
    console.log(`  ${r.roleCode} -> ${r.actualPath}`);
  });
  if (passed.length > 10) {
    console.log(`  ... 还有 ${passed.length - 10} 个正确的配置`);
  }
}

console.log('');
console.log('='.repeat(80));

// 生成修复建议
if (failed.length > 0 || missing.length > 0) {
  console.log('');
  console.log('修复建议:');
  console.log('-'.repeat(80));
  console.log('在 Dashboard.jsx 的 roleDashboardMap 中修改以下配置:');
  console.log('');
  
  const needFix = [...failed, ...missing];
  needFix.forEach(r => {
    if (r.actualPath === '(未定义)') {
      console.log(`  ${r.roleCode}: '${r.expectedPath}', // 新增`);
    } else {
      console.log(`  ${r.roleCode}: '${r.expectedPath}', // 修复: ${r.actualPath} -> ${r.expectedPath}`);
    }
  });
}

// 退出码
nodeProcess?.exit(failed.length > 0 || missing.length > 0 ? 1 : 0);




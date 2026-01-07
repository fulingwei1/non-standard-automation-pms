/**
 * 角色工作台跳转验证脚本
 * 自动验证所有角色的跳转配置是否正确
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const nodeProcess = globalThis.process;

// 读取配置文件
const roleConfigPath = path.join(__dirname, '../src/lib/roleConfig.js');
const dashboardPath = path.join(__dirname, '../src/pages/Dashboard.jsx');
const appPath = path.join(__dirname, '../src/App.jsx');

const roleConfigContent = fs.readFileSync(roleConfigPath, 'utf-8');
const dashboardContent = fs.readFileSync(dashboardPath, 'utf-8');
const appContent = fs.readFileSync(appPath, 'utf-8');

// 提取 roleDashboardMap
const roleDashboardMapMatch = dashboardContent.match(/const roleDashboardMap = \{([\s\S]*?)\n\}/);

// 提取路由定义
const routes = [];
const routeMatches = appContent.matchAll(/path="([^"]+)" element=\{<(\w+) \/>\}/g);
for (const match of routeMatches) {
  routes.push({ path: match[1], component: match[2] });
}

// 解析角色定义（简化版，使用正则提取）
const roles = {};
const roleMatches = roleConfigContent.matchAll(/(\w+):\s*\{[\s\S]*?name:\s*['"]([^'"]+)['"][\s\S]*?navGroups:\s*\[([^\]]+)\]/g);
for (const match of roleMatches) {
  const roleCode = match[1];
  const roleName = match[2];
  const navGroupsStr = match[3];
  const navGroups = navGroupsStr.split(',').map(g => g.trim().replace(/['"]/g, ''));
  roles[roleCode] = { name: roleName, navGroups };
}

// 解析导航组（简化版）
const navGroups = {};
const navGroupMatches = roleConfigContent.matchAll(/(\w+):\s*\{[\s\S]*?items:\s*\[([\s\S]*?)\]\s*\}/g);
for (const match of navGroupMatches) {
  const groupKey = match[1];
  const itemsStr = match[2];
  const pathMatches = itemsStr.matchAll(/path:\s*['"]([^'"]+)['"]/g);
  const paths = [];
  for (const pathMatch of pathMatches) {
    paths.push(pathMatch[1]);
  }
  navGroups[groupKey] = paths;
}

// 解析 roleDashboardMap
const dashboardMap = {};
if (roleDashboardMapMatch) {
  const mapContent = roleDashboardMapMatch[1];
  const mapMatches = mapContent.matchAll(/(\w+):\s*['"]([^'"]+)['"]/g);
  for (const match of mapMatches) {
    dashboardMap[match[1]] = match[2];
  }
}

// 查找每个角色的第一个工作台路径
function findFirstDashboardPath(roleCode) {
  const role = roles[roleCode];
  if (!role) return null;
  
  // 查找包含 dashboard, workstation, tasks, support 的路径（优先）
  const dashboardKeywords = ['dashboard', 'workstation', 'tasks', 'support'];
  
  // 优先查找专用工作台路径
  for (const groupKey of role.navGroups) {
    const paths = navGroups[groupKey] || [];
    for (const navPath of paths) {
      if (dashboardKeywords.some(keyword => navPath.includes(keyword))) {
        return navPath;
      }
    }
  }
  
  // 如果没有找到专用工作台，查找第一个导航组的第一个路径（通常是工作台）
  // 但排除 overview 组的 '/' 路径
  for (const groupKey of role.navGroups) {
    const paths = navGroups[groupKey] || [];
    if (paths.length > 0 && paths[0] !== '/') {
      return paths[0];
    }
  }
  
  // 如果第一个导航组是 overview 且第一个路径是 '/'，则返回 '/'
  // 这表示该角色使用默认 Dashboard
  return '/'; // 默认路径
}

// 验证路由是否存在
function routeExists(path) {
  return routes.some(r => r.path === path);
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

// 验证所有角色
for (const [roleCode, role] of Object.entries(roles)) {
  const expectedPath = findFirstDashboardPath(roleCode);
  const actualPath = dashboardMap[roleCode];
  const routeExistsCheck = actualPath ? routeExists(actualPath) : false;
  
  let status = '✅';
  let issues = [];
  
  if (!actualPath) {
    status = '⚠️';
    issues.push('未在 roleDashboardMap 中定义');
    missingCount++;
  } else if (actualPath !== expectedPath) {
    status = '❌';
    issues.push(`路径不匹配: 期望 ${expectedPath}, 实际 ${actualPath}`);
    failCount++;
  } else if (!routeExistsCheck) {
    status = '❌';
    issues.push(`路由不存在: ${actualPath}`);
    failCount++;
  } else {
    passCount++;
  }
  
  results.push({
    roleCode,
    roleName: role.name,
    expectedPath,
    actualPath: actualPath || '(未定义)',
    routeExists: routeExistsCheck,
    status,
    issues
  });
}

// 输出结果
console.log('验证结果汇总:');
console.log(`  通过: ${passCount}`);
console.log(`  失败: ${failCount}`);
console.log(`  缺失: ${missingCount}`);
console.log(`  总计: ${results.length}`);
console.log('');

// 按状态分组输出
const passed = results.filter(r => r.status === '✅');
const failed = results.filter(r => r.status === '❌');
const missing = results.filter(r => r.status === '⚠️');

if (failed.length > 0) {
  console.log('❌ 失败的配置:');
  console.log('-'.repeat(80));
  failed.forEach(r => {
    console.log(`${r.status} ${r.roleCode} (${r.roleName})`);
    console.log(`   期望路径: ${r.expectedPath}`);
    console.log(`   实际路径: ${r.actualPath}`);
    console.log(`   路由存在: ${r.routeExists}`);
    r.issues.forEach(issue => console.log(`   问题: ${issue}`));
    console.log('');
  });
}

if (missing.length > 0) {
  console.log('⚠️  缺失的配置:');
  console.log('-'.repeat(80));
  missing.forEach(r => {
    console.log(`${r.status} ${r.roleCode} (${r.roleName})`);
    console.log(`   建议路径: ${r.expectedPath}`);
    console.log('');
  });
}

if (passed.length > 0 && (failed.length === 0 && missing.length === 0)) {
  console.log('✅ 所有角色配置正确！');
} else if (passed.length > 0) {
  console.log('');
  console.log('✅ 正确的配置:');
  console.log('-'.repeat(80));
  passed.forEach(r => {
    console.log(`${r.status} ${r.roleCode} (${r.roleName}) -> ${r.actualPath}`);
  });
}

console.log('');
console.log('='.repeat(80));

// 生成修复建议
if (failed.length > 0 || missing.length > 0) {
  console.log('');
  console.log('修复建议:');
  console.log('-'.repeat(80));
  console.log('在 Dashboard.jsx 的 roleDashboardMap 中添加/修改以下配置:');
  console.log('');
  console.log('const roleDashboardMap = {');
  
  // 按字母顺序排序
  const allRoles = [...Object.keys(roles)].sort();
  allRoles.forEach(roleCode => {
    const result = results.find(r => r.roleCode === roleCode);
    const expectedPath = result.expectedPath;
    const currentPath = dashboardMap[roleCode];
    const comment = result.roleName;
    
    if (currentPath && currentPath === expectedPath) {
      console.log(`  ${roleCode}: '${currentPath}', // ${comment}`);
    } else {
      if (currentPath) {
        console.log(`  ${roleCode}: '${expectedPath}', // ${comment} (修复: ${currentPath} -> ${expectedPath})`);
      } else {
        console.log(`  ${roleCode}: '${expectedPath}', // ${comment} (新增)`);
      }
    }
  });
  
  console.log('}');
}

// 退出码
nodeProcess?.exit(failed.length > 0 || missing.length > 0 ? 1 : 0);

# 角色工作台跳转测试文档

## 测试目的
验证不同角色登录后是否正确跳转到对应的主内容网格（工作台页面）。

## 角色与工作台映射表

| 角色代码 | 角色名称 | 应该跳转的路径 | 工作台页面组件 | 状态 |
|---------|---------|--------------|--------------|------|
| `chairman` | 董事长 | `/chairman-dashboard` | `ChairmanWorkstation` | ✅ |
| `gm` | 总经理 | `/gm-dashboard` | `GeneralManagerWorkstation` | ✅ |
| `sales_director` | 销售总监 | `/sales-director-dashboard` | `SalesDirectorWorkstation` | ✅ |
| `sales_manager` | 销售经理 | `/sales-manager-dashboard` | `SalesManagerWorkstation` | ✅ 已修复 |
| `sales` | 销售工程师 | `/sales-dashboard` | `SalesWorkstation` | ✅ |
| `business_support` | 商务支持专员 | `/business-support` | `BusinessSupportWorkstation` | ✅ |
| `presales` | 售前技术工程师 | `/presales-dashboard` | `PresalesWorkstation` | ✅ |
| `presales_manager` | 售前技术部经理 | `/presales-manager-dashboard` | `PresalesManagerWorkstation` | ✅ |
| `me_engineer` | 机械工程师 | `/workstation` | `EngineerWorkstation` | ✅ |
| `ee_engineer` | 电气工程师 | `/workstation` | `EngineerWorkstation` | ✅ |
| `sw_engineer` | 软件工程师 | `/workstation` | `EngineerWorkstation` | ✅ |
| `te_engineer` | 测试工程师 | `/workstation` | `EngineerWorkstation` | ✅ |
| `assembler` | 装配技工 | `/assembly-tasks` | `AssemblerTaskCenter` | ✅ |
| `procurement_engineer` | 采购工程师 | `/procurement-dashboard` | `ProcurementEngineerWorkstation` | ✅ |
| `production_manager` | 生产部经理 | `/production-dashboard` | `ProductionManagerDashboard` | ✅ |
| `project_dept_manager` | 项目部经理 | `/` (默认Dashboard) | `Dashboard` | ✅ |
| `tech_dev_manager` | 技术开发部经理 | `/` (默认Dashboard) | `Dashboard` | ✅ |
| `procurement_manager` | 采购部经理 | `/` (默认Dashboard) | `Dashboard` | ✅ |
| `manufacturing_director` | 制造总监 | `/` (默认Dashboard) | `Dashboard` | ✅ |

## 测试步骤

### 1. 测试销售经理跳转（已修复的问题）
1. 使用销售经理账号登录（`sales_manager` 角色）
2. 登录成功后应该自动跳转到 `/sales-manager-dashboard`
3. 验证页面显示的是"销售经理工作台"（SalesManagerWorkstation 组件）
4. 验证主内容网格包含：
   - 销售漏斗分析
   - 团队成员业绩
   - 待审批事项
   - 重点客户
   - 近期回款计划

### 2. 测试销售总监跳转
1. 使用销售总监账号登录（`sales_director` 角色）
2. 登录成功后应该自动跳转到 `/sales-director-dashboard`
3. 验证页面显示的是"销售总监工作台"（SalesDirectorWorkstation 组件）

### 3. 测试销售工程师跳转
1. 使用销售工程师账号登录（`sales` 角色）
2. 登录成功后应该自动跳转到 `/sales-dashboard`
3. 验证页面显示的是"销售工作台"（SalesWorkstation 组件）

### 4. 测试其他角色
按照映射表逐一测试每个角色的跳转是否正确。

## 修复记录

### 2026-01-06
- **问题**：`sales_manager` 角色登录后跳转到了 `/sales-dashboard`（销售工程师工作台），而不是 `/sales-manager-dashboard`（销售经理工作台）
- **原因**：`Dashboard.jsx` 中的 `roleDashboardMap` 映射错误
- **修复**：将 `sales_manager: '/sales-dashboard'` 改为 `sales_manager: '/sales-manager-dashboard'`
- **文件**：`frontend/src/pages/Dashboard.jsx`

## 验证方法

### 方法1：浏览器控制台验证
1. 打开浏览器开发者工具（F12）
2. 登录后，在控制台输入：
```javascript
const user = JSON.parse(localStorage.getItem('user'));
console.log('当前角色:', user.role);
console.log('当前路径:', window.location.pathname);
```

### 方法2：代码验证
检查 `Dashboard.jsx` 中的 `roleDashboardMap` 是否与 `App.jsx` 中的路由定义一致。

## 注意事项

1. 某些角色（如 `project_dept_manager`、`tech_dev_manager` 等）没有专门的工作台页面，它们会使用默认的 Dashboard 页面（路径 `/`）
2. 如果角色在 `roleDashboardMap` 中没有定义，用户会停留在默认 Dashboard 页面
3. 确保所有角色的工作台页面组件都已正确导入到 `App.jsx` 中







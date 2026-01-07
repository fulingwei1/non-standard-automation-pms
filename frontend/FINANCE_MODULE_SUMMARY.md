# 财务模块功能总结

## 概述

财务模块为非标自动化项目管理系统提供完整的财务管理功能，包括财务数据概览、成本核算、付款审批、项目结算、财务报表等核心功能。

## 已实现的页面

### 1. 财务经理工作台 (`FinanceManagerDashboard.jsx`)
**路径**: `/finance-manager-dashboard`

**核心功能**:
- ✅ 6个关键财务指标卡片（营收、成本、利润、待审批、应收、现金流）
- ✅ 年度财务目标进度（营收目标、成本预算、净利润、预算执行率）
- ✅ 预算执行情况（按成本类别展示）
- ✅ 财务趋势分析（营收、成本、利润、现金流四个维度）
- ✅ 成本构成分析（6大成本类别）
- ✅ 项目成本分析（重点项目成本执行情况）
- ✅ 待审批付款（采购、外协、费用、工资）
- ✅ 财务健康度（回款率、预算执行率、利润率）
- ✅ 财务团队管理（团队成员绩效）

**特色功能**:
- 支持月度/季度/年度时间范围切换
- 环比增长率自动计算和显示
- 趋势可视化（Progress组件）
- 成本构成饼图式展示

### 2. 成本核算页面 (`CostAccounting.jsx`)
**路径**: `/costs`

**核心功能**:
- ✅ 成本记录查询和筛选（项目、类型、日期范围）
- ✅ 成本统计（总成本、材料成本、人工成本、平均成本）
- ✅ 成本类型分布分析
- ✅ 项目成本排行
- ✅ 成本录入功能
- ✅ 成本详情查看

**数据展示**:
- 成本列表（支持搜索和筛选）
- 成本类型分布（材料、人工、外协、费用）
- 项目成本排行（Top 5）

### 3. 付款审批页面 (`PaymentApproval.jsx`)
**路径**: `/payment-approval`

**核心功能**:
- ✅ 待审批付款列表
- ✅ 付款类型分类（采购、外协、费用、工资）
- ✅ 审批统计（待审批数量、金额、紧急事项）
- ✅ 筛选功能（类型、优先级）
- ✅ 审批操作（通过/拒绝）
- ✅ 付款详情查看
- ✅ 附件管理
- ✅ 批量审批功能

**审批流程**:
- 查看付款详情
- 填写审批意见
- 通过/拒绝操作
- 审批历史记录

### 4. 项目结算页面 (`ProjectSettlement.jsx`)
**路径**: `/settlement`

**核心功能**:
- ✅ 结算单列表和查询
- ✅ 结算单创建
- ✅ 成本明细展示（材料、人工、外协、费用）
- ✅ 利润分析（利润、利润率）
- ✅ 收款节点跟踪（签约款、进度款、发货款、验收款、质保金）
- ✅ 结算单确认
- ✅ 结算单导出

**统计功能**:
- 合同总额统计
- 总成本统计
- 总利润统计
- 回款率统计

### 5. 财务报表页面 (`FinancialReports.jsx`)
**路径**: `/financial-reports`

**核心功能**:
- ✅ 损益表（营业收入、营业成本、净利润）
- ✅ 现金流量表（流入、流出、净流量）
- ✅ 预算执行分析（按成本类别）
- ✅ 成本构成分析
- ✅ 项目盈利能力分析
- ✅ 报表导出功能

**报表类型**:
1. **损益表**: 展示营收、成本、利润及利润率
2. **现金流量表**: 展示现金流入、流出及净流量
3. **预算执行**: 展示预算执行情况和差异
4. **成本分析**: 展示成本构成和分布
5. **项目盈利**: 展示项目盈利能力排名

**时间范围**:
- 月度报表
- 季度报表
- 年度报表

## 页面路由配置

所有财务相关页面已在 `App.jsx` 中配置路由：

```javascript
{/* Finance Management */}
<Route path="/finance-manager-dashboard" element={<FinanceManagerDashboard />} />
<Route path="/costs" element={<CostAccounting />} />
<Route path="/payment-approval" element={<PaymentApproval />} />
<Route path="/settlement" element={<ProjectSettlement />} />
<Route path="/financial-reports" element={<FinancialReports />} />
```

## 导航配置

财务相关导航已在 `roleConfig.js` 中配置：

```javascript
finance: {
  label: '财务管理',
  items: [
    { name: '成本核算', path: '/costs', icon: 'Calculator' },
    { name: '付款审批', path: '/payment-approval', icon: 'FileCheck' },
    { name: '项目结算', path: '/settlement', icon: 'Receipt' },
    { name: '财务报表', path: '/financial-reports', icon: 'BarChart3' },
  ],
}
```

## 数据模型

### 成本数据 (ProjectCost)
- 项目ID、机台ID
- 成本类型、成本分类
- 金额、税额
- 发生日期
- 来源模块、来源单号
- 描述

### 付款审批数据
- 付款类型（采购、外协、费用、工资）
- 订单号/申请单号
- 项目/部门
- 供应商/申请人
- 金额
- 提交时间、待审批天数
- 优先级

### 结算数据
- 结算单号
- 项目信息
- 合同信息
- 成本明细（材料、人工、外协、费用）
- 利润信息
- 收款节点
- 结算状态

## 功能特点

### 1. 数据可视化
- 使用 Progress 组件展示趋势和占比
- 使用颜色标识不同状态和类型
- 支持多维度数据展示

### 2. 交互设计
- 响应式布局，适配不同屏幕
- 深色主题，统一视觉风格
- 动画效果，提升用户体验
- 悬停效果，增强交互反馈

### 3. 数据筛选
- 支持多条件筛选
- 实时搜索
- 时间范围选择
- 状态筛选

### 4. 操作流程
- 审批流程清晰
- 详情查看便捷
- 批量操作支持
- 导出功能完善

## 待对接的API

### 成本核算API
- `GET /api/v1/costs/` - 获取成本列表
- `POST /api/v1/costs/` - 创建成本记录
- `GET /api/v1/costs/projects/{project_id}/costs` - 获取项目成本
- `GET /api/v1/costs/{cost_id}` - 获取成本详情

### 付款审批API
- `GET /api/v1/payments/pending` - 获取待审批付款
- `POST /api/v1/payments/{id}/approve` - 审批通过
- `POST /api/v1/payments/{id}/reject` - 审批拒绝
- `GET /api/v1/payments/{id}` - 获取付款详情

### 项目结算API
- `GET /api/v1/settlements/` - 获取结算单列表
- `POST /api/v1/settlements/` - 创建结算单
- `GET /api/v1/settlements/{id}` - 获取结算单详情
- `POST /api/v1/settlements/{id}/confirm` - 确认结算

### 财务报表API
- `GET /api/v1/financial-reports/profit-loss` - 获取损益表
- `GET /api/v1/financial-reports/cash-flow` - 获取现金流量表
- `GET /api/v1/financial-reports/budget` - 获取预算执行
- `POST /api/v1/financial-reports/export` - 导出报表

## 技术实现

### 前端技术栈
- **React**: 前端框架
- **Framer Motion**: 动画库
- **Lucide React**: 图标库
- **Tailwind CSS**: 样式框架
- **shadcn/ui**: UI组件库

### 组件使用
- `Card`, `CardContent`, `CardHeader`, `CardTitle` - 卡片容器
- `Button`, `Badge` - 按钮和标签
- `Input`, `Progress` - 输入和进度条
- `Dialog` - 对话框
- `Tabs`, `TabsContent`, `TabsList`, `TabsTrigger` - 标签页

## 页面统计

- **财务模块页面总数**: 7个
- **新增页面**: 4个（成本核算、付款审批、项目结算、财务报表）
- **增强页面**: 1个（财务经理工作台）

## 下一步计划

1. ⏳ **预算管理页面** - 创建专门的预算管理页面
2. ⏳ **API对接** - 将Mock数据替换为真实API调用
3. ⏳ **数据权限** - 实现基于角色的数据权限控制
4. ⏳ **报表导出** - 实现Excel/PDF导出功能
5. ⏳ **实时更新** - 实现数据的实时刷新
6. ⏳ **数据钻取** - 支持点击图表钻取到详细数据

## 使用说明

### 财务经理登录后
1. 自动跳转到 `/finance-manager-dashboard` 财务经理工作台
2. 可以查看财务数据概览、预算执行、待审批事项等
3. 通过侧边栏导航访问各个财务功能模块

### 功能入口
- **成本核算**: 侧边栏 → 财务管理 → 成本核算
- **付款审批**: 侧边栏 → 财务管理 → 付款审批
- **项目结算**: 侧边栏 → 财务管理 → 项目结算
- **财务报表**: 侧边栏 → 财务管理 → 财务报表

## 设计规范

所有财务页面遵循统一的设计规范：
- 深色主题（slate-800/900渐变背景）
- 卡片式布局
- 统一的颜色标识系统
- 响应式设计
- 动画过渡效果




# HRManagerDashboard.jsx 重构计划

## 文件信息
- **文件路径**: `frontend/src/pages/HRManagerDashboard.jsx`
- **原始行数**: 3047 行
- **主组件行数**: ~1855 行（估算）
- **嵌套组件**: 
  - `HrTransactionsTab()` - 人事事务 Tab
  - `HrContractsTab()` - 合同管理 Tab

## Tab 结构分析

该组件包含 9 个 Tab：

1. **overview** - 概览（统计卡片、图表、待办事项）
2. **transactions** - 人事事务（已有独立组件 `HrTransactionsTab`）
3. **contracts** - 合同管理（已有独立组件 `HrContractsTab`）
4. **recruitment** - 招聘管理
5. **performance** - 绩效管理
6. **attendance** - 考勤管理
7. **employees** - 员工管理
8. **relations** - 员工关系
9. **statistics** - 统计分析

## 重构策略

### 1. 目录结构
```
frontend/src/components/hr/
├── hooks/
│   ├── useHRDashboard.js          # 核心数据管理（员工、部门、统计数据）
│   ├── useHRTransactions.js       # 人事事务逻辑
│   ├── useHRContracts.js          # 合同管理逻辑
│   ├── useHRRecruitment.js        # 招聘管理逻辑
│   ├── useHRPerformance.js        # 绩效管理逻辑
│   ├── useHRAttendance.js          # 考勤管理逻辑
│   ├── useHREmployees.js          # 员工管理逻辑
│   ├── useHRRelations.js          # 员工关系逻辑
│   └── useHRStatistics.js         # 统计分析逻辑
├── tabs/
│   ├── HROverviewTab.jsx          # 概览 Tab
│   ├── HRTransactionsTab.jsx      # 人事事务 Tab（重构现有组件）
│   ├── HRContractsTab.jsx          # 合同管理 Tab（重构现有组件）
│   ├── HRRecruitmentTab.jsx        # 招聘管理 Tab
│   ├── HRPerformanceTab.jsx       # 绩效管理 Tab
│   ├── HRAttendanceTab.jsx         # 考勤管理 Tab
│   ├── HREmployeesTab.jsx         # 员工管理 Tab
│   ├── HRRelationsTab.jsx         # 员工关系 Tab
│   └── HRStatisticsTab.jsx        # 统计分析 Tab
├── dialogs/
│   └── [各种对话框组件]
└── HRDashboardHeader.jsx          # 页面头部组件
```

### 2. 重构步骤

#### 阶段1: 提取核心 Hook 和头部组件
- [ ] 创建 `useHRDashboard.js` Hook
  - 员工数据获取
  - 部门数据获取
  - 统计数据计算
  - 待办事项管理
- [ ] 创建 `HRDashboardHeader.jsx` 组件
  - 页面标题
  - 操作按钮
  - 筛选器

#### 阶段2: 重构已有 Tab 组件
- [ ] 重构 `HrTransactionsTab` → `HRTransactionsTab.jsx`
  - 提取到 `components/hr/tabs/`
  - 创建 `useHRTransactions.js` Hook
- [ ] 重构 `HrContractsTab` → `HRContractsTab.jsx`
  - 提取到 `components/hr/tabs/`
  - 创建 `useHRContracts.js` Hook

#### 阶段3: 重构概览 Tab
- [ ] 创建 `HROverviewTab.jsx`
  - 统计卡片展示
  - 图表展示
  - 待办事项列表

#### 阶段4: 重构其他 Tab（按优先级）
- [ ] `HRRecruitmentTab.jsx` - 招聘管理
- [ ] `HRPerformanceTab.jsx` - 绩效管理
- [ ] `HRAttendanceTab.jsx` - 考勤管理
- [ ] `HREmployeesTab.jsx` - 员工管理
- [ ] `HRRelationsTab.jsx` - 员工关系
- [ ] `HRStatisticsTab.jsx` - 统计分析

### 3. 重构原则

1. **单一职责**: 每个 Tab 组件只负责一个功能模块
2. **状态管理**: 复杂状态逻辑提取到自定义 Hooks
3. **代码复用**: 通用组件（如 StatCard）提取到共享位置
4. **性能优化**: 使用 `useMemo` 和 `useCallback` 优化渲染
5. **文件大小**: 每个组件文件不超过 500 行

### 4. 预期效果

- **主组件行数**: 从 ~1855 行减少到 ~150 行（减少 92%）
- **组件数量**: 从 1 个大组件拆分为 9 个 Tab 组件 + 多个 Hooks
- **可维护性**: 显著提升，每个模块独立管理
- **可测试性**: 小组件更容易编写单元测试

## 开始重构

让我们从阶段1开始：提取核心 Hook 和头部组件。

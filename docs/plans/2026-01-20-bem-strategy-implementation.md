# BEM 战略管理模块实施计划

## 实施概览

基于 `2026-01-20-bem-strategy-management-design.md` 设计文档，分阶段实施 BEM 战略管理模块。

---

## Phase 1: 数据模型层

### 1.1 创建模型文件

**文件**: `app/models/strategy.py`

- [ ] Strategy - 战略主表
- [ ] CSF - 关键成功要素
- [ ] KPI - 关键绩效指标
- [ ] KPIDataSource - KPI 数据源配置
- [ ] KPIHistory - KPI 历史快照
- [ ] AnnualKeyWork - 年度重点工作
- [ ] AnnualKeyWorkProjectLink - 重点工作与项目关联
- [ ] DepartmentObjective - 部门目标
- [ ] PersonalKPI - 个人 KPI
- [ ] StrategyReview - 战略审视
- [ ] StrategyCalendarEvent - 战略日历事件
- [ ] StrategyComparison - 战略年度对比

### 1.2 创建枚举定义

**文件**: `app/models/enums/strategy.py`

- [ ] StrategyStatus - 战略状态
- [ ] BSCDimension - BSC 四维度
- [ ] IPOOCType - IPOOC 指标类型
- [ ] VOCSource - VOC 声音来源
- [ ] CSFDerivationMethod - CSF 导出方法
- [ ] WorkStatus - 工作状态
- [ ] StrategyEventType - 战略事件类型
- [ ] DataSourceType - 数据源类型

### 1.3 数据库迁移

- [ ] 创建迁移文件 `migrations/20260120_strategy_sqlite.sql`
- [ ] 执行迁移并验证

---

## Phase 2: Schema 层

### 2.1 创建 Schema 目录结构

```
app/schemas/strategy/
├── __init__.py
├── strategy.py      # 战略 CRUD Schema
├── csf.py           # CSF Schema
├── kpi.py           # KPI Schema
├── annual_work.py   # 年度重点工作 Schema
├── decomposition.py # 目标分解 Schema
├── review.py        # 战略审视 Schema
└── dashboard.py     # 仪表板 Schema
```

### 2.2 各 Schema 实现

- [ ] StrategyCreate / StrategyUpdate / StrategyResponse
- [ ] CSFCreate / CSFUpdate / CSFResponse / CSFByDimension
- [ ] KPICreate / KPIUpdate / KPIResponse / KPIWithHistory
- [ ] AnnualKeyWorkCreate / AnnualKeyWorkUpdate / AnnualKeyWorkResponse
- [ ] DepartmentObjectiveCreate / DepartmentObjectiveResponse
- [ ] PersonalKPICreate / PersonalKPIResponse
- [ ] StrategyReviewCreate / StrategyReviewResponse
- [ ] StrategyMapResponse / MyStrategyResponse / StrategyComparisonResponse

---

## Phase 3: 服务层

### 3.1 创建服务目录结构

```
app/services/strategy/
├── __init__.py
├── strategy_service.py       # 战略 CRUD 服务
├── csf_service.py            # CSF 服务
├── kpi_service.py            # KPI 服务
├── kpi_collector.py          # KPI 数据采集器
├── annual_work_service.py    # 年度重点工作服务
├── decomposition_service.py  # 目标分解服务
├── review_service.py         # 战略审视服务
├── health_calculator.py      # 健康度计算器
└── comparison_service.py     # 同比分析服务
```

### 3.2 核心服务实现

#### strategy_service.py
- [ ] create_strategy()
- [ ] update_strategy()
- [ ] publish_strategy()
- [ ] get_strategy_map_data()
- [ ] archive_strategy()

#### kpi_collector.py
- [ ] collect_kpi_data() - 自动采集
- [ ] calculate_formula_kpi() - 公式计算（使用 simpleeval）
- [ ] update_kpi_value() - 手动更新
- [ ] create_kpi_snapshot() - 创建快照

#### health_calculator.py
- [ ] calculate_csf_health() - CSF 健康度
- [ ] calculate_dimension_health() - 维度健康度
- [ ] calculate_strategy_health() - 整体健康度
- [ ] get_health_trend() - 健康度趋势

#### decomposition_service.py
- [ ] decompose_to_department() - 分解到部门
- [ ] decompose_to_personal() - 分解到个人
- [ ] get_decomposition_tree() - 获取分解树
- [ ] trace_to_strategy() - 向上追溯到战略

---

## Phase 4: API 端点层

### 4.1 创建 API 目录结构

```
app/api/v1/endpoints/strategy/
├── __init__.py
├── strategies.py     # 战略 CRUD
├── csf.py            # CSF 管理
├── kpi.py            # KPI 管理
├── annual_works.py   # 年度重点工作
├── decomposition.py  # 目标分解
├── review.py         # 战略审视
├── comparison.py     # 同比分析
└── dashboard.py      # 仪表板
```

### 4.2 API 端点实现

#### strategies.py
- [ ] GET /strategies - 战略列表
- [ ] POST /strategies - 创建战略
- [ ] GET /strategies/{id} - 战略详情
- [ ] PUT /strategies/{id} - 更新战略
- [ ] POST /strategies/{id}/publish - 发布战略
- [ ] GET /strategies/{id}/map - 战略地图数据

#### csf.py
- [ ] GET /csf - CSF 列表
- [ ] POST /csf - 创建 CSF
- [ ] PUT /csf/{id} - 更新 CSF
- [ ] GET /csf/by-dimension - 按维度分组

#### kpi.py
- [ ] GET /kpi - KPI 列表
- [ ] POST /kpi - 创建 KPI
- [ ] PUT /kpi/{id} - 更新 KPI
- [ ] POST /kpi/{id}/collect - 采集数据
- [ ] PUT /kpi/{id}/value - 更新当前值
- [ ] GET /kpi/{id}/history - 历史数据

#### annual_works.py
- [ ] GET /annual-works - 工作列表
- [ ] POST /annual-works - 创建工作
- [ ] PUT /annual-works/{id} - 更新工作
- [ ] PUT /annual-works/{id}/progress - 更新进度
- [ ] POST /annual-works/{id}/link-project - 关联项目

#### decomposition.py
- [ ] GET /decomposition/department/{id} - 部门目标
- [ ] POST /decomposition/department - 创建部门目标
- [ ] GET /decomposition/personal/{id} - 个人 KPI
- [ ] POST /decomposition/personal - 分配个人 KPI

#### review.py
- [ ] GET /review - 审视记录列表
- [ ] POST /review - 创建审视记录
- [ ] GET /review/health-score - 健康度评分

#### comparison.py
- [ ] GET /comparison/{current}/{previous} - 年度对比
- [ ] GET /comparison/yoy-report/{year} - 同比报告

#### dashboard.py
- [ ] GET /dashboard/overview - 战略总览
- [ ] GET /dashboard/my-strategy - 我的战略关联
- [ ] GET /dashboard/execution-status - 执行状态

### 4.3 注册路由

- [ ] 更新 `app/api/v1/api.py` 注册战略模块路由

---

## Phase 5: 前端页面

### 5.1 创建页面目录结构

```
frontend/src/pages/Strategy/
├── index.jsx                 # 路由配置
├── StrategyOverview.jsx      # 战略总览
├── StrategyMap.jsx           # 战略地图
├── CSFManagement.jsx         # CSF 管理
├── KPIManagement.jsx         # KPI 管理
├── AnnualWorks.jsx           # 年度重点工作
├── Decomposition.jsx         # 目标分解
├── MyStrategy.jsx            # 我的战略
├── StrategyReview.jsx        # 战略审视
├── StrategyComparison.jsx    # 同比分析
└── components/
    ├── StrategyMapChart.jsx  # 战略地图图表组件
    ├── CSFCard.jsx           # CSF 卡片
    ├── KPITable.jsx          # KPI 表格
    ├── HealthGauge.jsx       # 健康度仪表
    └── DecompositionTree.jsx # 分解树组件
```

### 5.2 页面实现优先级

1. [ ] StrategyOverview - 战略总览（核心入口）
2. [ ] StrategyMap - 战略地图（核心可视化）
3. [ ] CSFManagement - CSF 管理
4. [ ] KPIManagement - KPI 管理
5. [ ] AnnualWorks - 年度重点工作
6. [ ] MyStrategy - 我的战略（全员视图）
7. [ ] Decomposition - 目标分解
8. [ ] StrategyReview - 战略审视
9. [ ] StrategyComparison - 同比分析

### 5.3 API 服务层

- [ ] 创建 `frontend/src/services/api/strategy.js`

### 5.4 路由配置

- [ ] 更新 `frontend/src/routes.jsx` 添加战略模块路由
- [ ] 更新侧边栏配置 `sidebarConfig.js`

---

## Phase 6: 集成与测试

### 6.1 模块集成

- [ ] 与项目管理模块集成（重点工作关联项目）
- [ ] 与绩效管理模块集成（个人 KPI 关联绩效）
- [ ] 与财务模块集成（财务维度数据采集）
- [ ] 与 HR 模块集成（学习成长维度数据采集）

### 6.2 测试用例

- [ ] 单元测试：services/strategy/
- [ ] API 测试：endpoints/strategy/
- [ ] 集成测试：数据采集流程

### 6.3 权限配置

- [ ] 添加战略模块权限定义
- [ ] 配置角色权限映射

---

## 实施顺序建议

```
Week 1: Phase 1 (数据模型) + Phase 2 (Schema)
Week 2: Phase 3 (服务层)
Week 3: Phase 4 (API 端点)
Week 4: Phase 5 (前端页面 - 核心)
Week 5: Phase 5 (前端页面 - 扩展) + Phase 6 (集成测试)
```

---

## 依赖项

- [ ] 安装 `simpleeval` 用于安全公式计算
- [ ] 确认 ECharts 已安装（战略地图可视化）

---

## 风险与注意事项

1. **数据源配置复杂度** - KPI 自动采集需要与多模块对接，建议先实现手动录入，再逐步添加自动采集
2. **健康度算法** - 权重配置需要灵活，建议支持管理员自定义
3. **权限粒度** - 部门级数据隔离需要仔细设计
4. **性能考虑** - 战略地图数据聚合可能涉及大量计算，建议添加缓存

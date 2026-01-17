# 项目四算体系差距分析报告

> 对比四算设计方案与现有系统的差距，识别需新增和修改的内容

---

## 1. 执行摘要

### 1.1 分析结论

| 维度 | 现有覆盖率 | 差距评估 |
|-----|----------|---------|
| **概算（估算利润）** | 30% | 有基础（报价成本模板），缺概算主表和审批 |
| **预算（成本控制）** | 60% | 有预算表和明细，缺控制机制和概算关联 |
| **核算（成本归集）** | 50% | 有成本记录，缺台账汇总和自动归集 |
| **决算（经验传承）** | 0% | 完全缺失，需从零构建 |

### 1.2 工作量估算

| 任务类型 | 数量 | 优先级 |
|---------|-----|-------|
| 新增数据表 | 8张 | 高 |
| 修改数据表 | 4张 | 高 |
| 新增API端点 | 35+ 个 | 高 |
| 新增前端页面 | 8个 | 中 |
| 新增服务类 | 6个 | 高 |

---

## 2. 现有系统资产分析

### 2.1 数据库模型现状

#### 已有的四算相关模型

| 模型 | 文件位置 | 四算关联 | 覆盖功能 |
|-----|---------|---------|---------|
| `Project` | `models/project.py` | 核心 | 项目基础+金额字段(contract_amount, budget_amount, actual_cost) |
| `ProjectCost` | `models/project.py` | 核算 | 成本记录(cost_type, cost_category, amount, source_*) |
| `FinancialProjectCost` | `models/project.py` | 核算 | 财务上传成本(更详细的字段，支持审核) |
| `ProjectPaymentPlan` | `models/project.py` | 核算 | 收款计划(planned_amount, actual_amount, status) |
| `ProjectBudget` | `models/budget.py` | 预算 | 预算主表(budget_no, version, status, approval) |
| `ProjectBudgetItem` | `models/budget.py` | 预算 | 预算明细(cost_category, cost_item, budget_amount) |
| `ProjectCostAllocationRule` | `models/budget.py` | 核算 | 成本分摊规则 |
| `QuoteCostTemplate` | `models/sales.py` | 概算 | 报价成本模板(cost_structure JSON) |
| `Quote` / `QuoteVersion` | `models/sales.py` | 概算 | 报价管理(total_price, cost_total, gross_margin) |

#### 模型评估

**Project 模型（部分满足）**
- ✅ 已有: `contract_amount`, `budget_amount`, `actual_cost`
- ❌ 缺失: `estimate_id`, `budget_id`, `settlement_id`, `four_estimate_status`

**ProjectBudget 模型（部分满足）**
- ✅ 已有: 预算编号、版本、审批流程、明细关联
- ❌ 缺失: `estimate_id`（概算关联）、`control_mode`、`warning_threshold`

**QuoteCostTemplate 模型（可复用）**
- ✅ 已有: 成本结构 JSON、设备类型、行业
- ❌ 缺失: 与项目/商机的关联、历史项目参考

### 2.2 API 端点现状

#### 已有的四算相关 API

| 端点模块 | 文件位置 | 功能覆盖 |
|---------|---------|---------|
| `/budgets` | `endpoints/budget.py` | 预算CRUD、审批、明细管理 |
| `/budgets/allocation-rules` | `endpoints/budget.py` | 成本分摊规则管理 |
| `/costs` | `endpoints/costs/basic.py` | 成本记录CRUD |
| `/costs/analysis` | `endpoints/costs/analysis.py` | 成本分析统计 |
| `/costs/allocation` | `endpoints/costs/allocation.py` | 成本分摊计算 |
| `/sales/cost-templates` | `endpoints/sales/cost_management.py` | 成本模板管理 |
| `/projects/{id}/payment-plans` | `endpoints/projects/payment_plans.py` | 收款计划管理 |
| `/timesheet/reports/finance` | `endpoints/timesheet/reports.py` | 工时→成本报表 |

---

## 3. 差距详细分析

### 3.1 概算模块差距 (缺失70%)

#### 需要新增的表

| 表名 | 用途 | 设计优先级 |
|-----|------|----------|
| `project_estimates` | 概算主表 | P0 |
| `project_estimate_items` | 概算明细 | P0 |

#### 需要新增的 API

| 端点 | 方法 | 功能 |
|-----|-----|------|
| `/estimates` | GET | 概算列表（支持按商机/项目筛选） |
| `/estimates` | POST | 创建概算 |
| `/estimates/{id}` | GET/PUT/DELETE | 概算详情/更新/删除 |
| `/estimates/{id}/items` | GET/POST | 概算明细列表/创建 |
| `/estimates/items/{id}` | PUT/DELETE | 概算明细更新/删除 |
| `/estimates/{id}/submit` | POST | 提交概算审批 |
| `/estimates/{id}/approve` | POST | 审批概算 |
| `/estimates/{id}/transfer-to-budget` | POST | 概算转预算 |
| `/estimates/templates` | GET | 获取概算模板（基于历史项目） |
| `/estimates/{id}/copy` | POST | 复制概算 |

#### 需要修改的现有功能

- **QuoteCostTemplate**: 增加 `reference_project_ids` 字段，支持参考历史项目
- **Quote/QuoteVersion**: 增加 `estimate_id` 关联字段

### 3.2 预算模块差距 (缺失40%)

#### 需要新增的表

| 表名 | 用途 | 设计优先级 |
|-----|------|----------|
| `project_budget_adjustments` | 预算调整记录 | P1 |

#### 需要扩展的现有表

**project_budgets 扩展字段**:
```sql
ALTER TABLE project_budgets ADD COLUMN estimate_id INT REFERENCES project_estimates(id);
ALTER TABLE project_budgets ADD COLUMN estimate_no VARCHAR(50);
ALTER TABLE project_budgets ADD COLUMN budget_source VARCHAR(20) DEFAULT 'MANUAL'; -- ESTIMATE/MANUAL/TEMPLATE
ALTER TABLE project_budgets ADD COLUMN budget_category VARCHAR(20) DEFAULT 'PROJECT'; -- PROJECT/PLATFORM/SHARED
ALTER TABLE project_budgets ADD COLUMN control_mode VARCHAR(20) DEFAULT 'SOFT'; -- HARD/SOFT/NONE
ALTER TABLE project_budgets ADD COLUMN warning_threshold DECIMAL(5,2) DEFAULT 0.80;
ALTER TABLE project_budgets ADD COLUMN original_amount DECIMAL(14,2);
ALTER TABLE project_budgets ADD COLUMN adjusted_amount DECIMAL(14,2);
ALTER TABLE project_budgets ADD COLUMN adjustment_count INT DEFAULT 0;
```

#### 需要新增的 API

| 端点 | 方法 | 功能 |
|-----|-----|------|
| `/budgets/{id}/adjustments` | GET/POST | 预算调整记录 |
| `/budgets/adjustments/{id}/approve` | POST | 审批预算调整 |
| `/budgets/{id}/check` | GET | 检查预算执行情况 |
| `/budgets/{id}/warnings` | GET | 获取预算预警列表 |
| `/budgets/from-estimate/{estimate_id}` | POST | 从概算生成预算 |

#### 需要修改的现有功能

- **采购模块**: 增加预算校验逻辑
  - `POST /purchase-orders` 增加预算检查
  - 返回预警信息或阻止提交
- **外协模块**: 增加预算校验逻辑
  - `POST /outsourcing/orders` 增加预算检查

### 3.3 核算模块差距 (缺失50%)

#### 需要新增的表

| 表名 | 用途 | 设计优先级 |
|-----|------|----------|
| `project_cost_ledgers` | 项目成本台账（按期间汇总） | P0 |
| `dept_financial_summaries` | 部门财务汇总 | P1 |
| `cost_aggregation_logs` | 成本归集日志 | P2 |

#### 需要新增的 API

| 端点 | 方法 | 功能 |
|-----|-----|------|
| `/cost-ledgers` | GET | 成本台账列表 |
| `/cost-ledgers/project/{project_id}` | GET | 项目成本台账 |
| `/cost-ledgers/project/{project_id}/period/{period}` | GET | 项目期间台账详情 |
| `/cost-ledgers/aggregate` | POST | 手动触发成本归集 |
| `/cost-ledgers/confirm` | POST | 确认月度核算 |
| `/cost-ledgers/lock` | POST | 锁定核算期间 |
| `/dept-summaries` | GET | 部门财务汇总列表 |
| `/dept-summaries/{dept_id}/period/{period}` | GET | 部门期间汇总 |
| `/cost-analysis/budget-variance` | GET | 预算偏差分析 |
| `/cost-analysis/estimate-variance` | GET | 概算偏差分析 |

#### 需要修改的现有功能

- **成本归集自动化**: 创建后台服务自动归集成本
  - 采购入库 → 物料成本
  - 外协验收 → 外协成本
  - 工时审批 → 人工成本（已有基础）
  - 费用报销 → 其他费用

### 3.4 决算模块差距 (缺失100%)

#### 需要新增的表

| 表名 | 用途 | 设计优先级 |
|-----|------|----------|
| `project_settlement_finals` | 决算主表 | P0 |
| `settlement_variance_analyses` | 决算偏差分析 | P0 |
| `project_lessons_learned` | 项目经验库 | P1 |

#### 需要新增的 API

| 端点 | 方法 | 功能 |
|-----|-----|------|
| `/settlements` | GET | 决算列表 |
| `/settlements` | POST | 创建决算 |
| `/settlements/{id}` | GET/PUT | 决算详情/更新 |
| `/settlements/{id}/submit` | POST | 提交决算审核 |
| `/settlements/{id}/review` | POST | 审核决算 |
| `/settlements/{id}/approve` | POST | 审批决算 |
| `/settlements/{id}/variance-analyses` | GET/POST | 偏差分析列表/创建 |
| `/settlements/variance-analyses/{id}` | PUT/DELETE | 偏差分析更新/删除 |
| `/lessons-learned` | GET | 经验库列表 |
| `/lessons-learned` | POST | 创建经验记录 |
| `/lessons-learned/{id}` | GET/PUT | 经验详情/更新 |
| `/lessons-learned/search` | POST | 搜索经验（用于概算参考） |
| `/lessons-learned/feedback-to-template` | POST | 反馈到概算模板 |

### 3.5 四算拉通与集成差距

#### 需要新增的表

| 表名 | 用途 | 设计优先级 |
|-----|------|----------|
| `four_estimate_checkpoints` | 四算检查点配置 | P1 |
| `four_estimate_checkpoint_logs` | 检查点执行日志 | P2 |

#### 需要新增的 API

| 端点 | 方法 | 功能 |
|-----|-----|------|
| `/four-estimate/checkpoints` | GET/POST | 检查点配置管理 |
| `/four-estimate/checkpoints/{id}` | PUT/DELETE | 检查点更新/删除 |
| `/four-estimate/project/{project_id}/status` | GET | 项目四算状态 |
| `/four-estimate/project/{project_id}/timeline` | GET | 项目四算时间线 |
| `/four-estimate/dashboard` | GET | 四算经营看板 |
| `/four-estimate/dept/{dept_id}/summary` | GET | 部门四算汇总 |

#### 需要扩展的现有表

**projects 扩展字段**:
```sql
ALTER TABLE projects ADD COLUMN estimate_id INT REFERENCES project_estimates(id);
ALTER TABLE projects ADD COLUMN four_estimate_status VARCHAR(50) DEFAULT 'ESTIMATE_PENDING';
ALTER TABLE projects ADD COLUMN settlement_id INT REFERENCES project_settlement_finals(id);
```

---

## 4. 数据库变更汇总

### 4.1 新增表 (8张)

| 序号 | 表名 | 模块 | 主要字段 |
|-----|------|-----|---------|
| 1 | `project_estimates` | 概算 | estimate_no, project_id, opportunity_id, target_margin_rate, allowed_cost, estimated_cost, status, version |
| 2 | `project_estimate_items` | 概算 | estimate_id, cost_category, cost_item, estimated_amount, reference_source, reference_project_id |
| 3 | `project_budget_adjustments` | 预算 | budget_id, adjustment_no, adjustment_type, before_amount, adjust_amount, reason_category, related_ecn_id, status |
| 4 | `project_cost_ledgers` | 核算 | project_id, machine_id, period_type, period_value, material_cost, labor_cost, outsource_cost, total_cost, budget_amount, variance_amount, status |
| 5 | `dept_financial_summaries` | 核算 | dept_id, period_type, period_value, project_count, total_estimate_revenue, total_actual_cost, budget_variance, estimate_accuracy |
| 6 | `project_settlement_finals` | 决算 | settlement_no, project_id, estimate_id, budget_id, final_revenue, total_cost, gross_profit, cost_variance, estimate_accuracy, status |
| 7 | `settlement_variance_analyses` | 决算 | settlement_id, variance_category, variance_type, estimated_amount, actual_amount, root_cause, lesson_learned, feedback_to_template |
| 8 | `project_lessons_learned` | 决算 | settlement_id, project_type, lesson_type, title, description, estimated_value, actual_value, recommendation, reference_count |

### 4.2 修改表 (4张)

| 序号 | 表名 | 修改内容 |
|-----|------|---------|
| 1 | `projects` | 新增: estimate_id, four_estimate_status, settlement_id |
| 2 | `project_budgets` | 新增: estimate_id, estimate_no, budget_source, budget_category, control_mode, warning_threshold, original_amount, adjusted_amount, adjustment_count |
| 3 | `quotes` / `quote_versions` | 新增: estimate_id |
| 4 | `quote_cost_templates` | 新增: reference_project_ids (JSON), source_settlement_ids (JSON) |

---

## 5. API 变更汇总

### 5.1 新增 API 端点 (35+)

#### 概算模块 (10个)
- `GET/POST /api/v1/estimates`
- `GET/PUT/DELETE /api/v1/estimates/{id}`
- `GET/POST /api/v1/estimates/{id}/items`
- `PUT/DELETE /api/v1/estimates/items/{id}`
- `POST /api/v1/estimates/{id}/submit`
- `POST /api/v1/estimates/{id}/approve`
- `POST /api/v1/estimates/{id}/transfer-to-budget`
- `GET /api/v1/estimates/templates`
- `POST /api/v1/estimates/{id}/copy`

#### 预算模块扩展 (5个)
- `GET/POST /api/v1/budgets/{id}/adjustments`
- `POST /api/v1/budgets/adjustments/{id}/approve`
- `GET /api/v1/budgets/{id}/check`
- `GET /api/v1/budgets/{id}/warnings`
- `POST /api/v1/budgets/from-estimate/{estimate_id}`

#### 核算模块 (10个)
- `GET /api/v1/cost-ledgers`
- `GET /api/v1/cost-ledgers/project/{project_id}`
- `GET /api/v1/cost-ledgers/project/{project_id}/period/{period}`
- `POST /api/v1/cost-ledgers/aggregate`
- `POST /api/v1/cost-ledgers/confirm`
- `POST /api/v1/cost-ledgers/lock`
- `GET /api/v1/dept-summaries`
- `GET /api/v1/dept-summaries/{dept_id}/period/{period}`
- `GET /api/v1/cost-analysis/budget-variance`
- `GET /api/v1/cost-analysis/estimate-variance`

#### 决算模块 (12个)
- `GET/POST /api/v1/settlements`
- `GET/PUT /api/v1/settlements/{id}`
- `POST /api/v1/settlements/{id}/submit`
- `POST /api/v1/settlements/{id}/review`
- `POST /api/v1/settlements/{id}/approve`
- `GET/POST /api/v1/settlements/{id}/variance-analyses`
- `PUT/DELETE /api/v1/settlements/variance-analyses/{id}`
- `GET/POST /api/v1/lessons-learned`
- `GET/PUT /api/v1/lessons-learned/{id}`
- `POST /api/v1/lessons-learned/search`
- `POST /api/v1/lessons-learned/feedback-to-template`

#### 四算集成 (6个)
- `GET/POST /api/v1/four-estimate/checkpoints`
- `PUT/DELETE /api/v1/four-estimate/checkpoints/{id}`
- `GET /api/v1/four-estimate/project/{project_id}/status`
- `GET /api/v1/four-estimate/project/{project_id}/timeline`
- `GET /api/v1/four-estimate/dashboard`
- `GET /api/v1/four-estimate/dept/{dept_id}/summary`

### 5.2 修改 API 端点

| 端点 | 修改内容 |
|-----|---------|
| `POST /purchase-orders` | 增加预算校验逻辑 |
| `POST /outsourcing/orders` | 增加预算校验逻辑 |
| `POST /quotes/{id}/submit` | 增加概算检查 |
| `POST /contracts` | 增加概算审批检查 |
| `POST /projects/{id}/complete` | 增加决算检查 |

---

## 6. 新增服务类

| 服务类 | 职责 | 位置 |
|-------|-----|------|
| `EstimateService` | 概算创建、审批、转预算 | `app/services/estimate/` |
| `BudgetControlService` | 预算控制、预警检查 | `app/services/budget/` |
| `CostLedgerService` | 成本台账归集、确认 | `app/services/cost/` |
| `SettlementService` | 决算创建、审批、偏差分析 | `app/services/settlement/` |
| `LessonsLearnedService` | 经验库管理、模板反馈 | `app/services/settlement/` |
| `FourEstimateIntegrationService` | 四算检查点、状态管理 | `app/services/four_estimate/` |

---

## 7. 数据库设计合理性评估

### 7.1 现有设计优点

1. **基础结构完善**: Project、ProjectCost、ProjectBudget 等核心模型设计良好
2. **关系清晰**: 使用 ForeignKey 关联，relationship 定义明确
3. **扩展性好**: 使用 JSON 字段存储复杂结构（如 cost_structure）
4. **审批流程**: 预算已有 status、submitted_by、approved_by 等审批字段
5. **时间戳**: 统一使用 TimestampMixin

### 7.2 需要改进的地方

1. **缺少概算层**: 从报价直接到预算，缺少目标利润设计环节
2. **预算控制弱**: 无强制/软性控制机制，无预警阈值
3. **核算不完整**: 有成本记录但无台账汇总视图
4. **无决算模块**: 完全缺失决算和经验库
5. **四算未拉通**: 项目状态与四算状态无关联

### 7.3 建议的改进

1. **新增概算层**: 在 Quote 和 Budget 之间插入 Estimate
2. **增强预算控制**: 添加 control_mode 和 warning_threshold
3. **构建成本台账**: 新增按期间汇总的成本视图
4. **完整决算流程**: 新增决算表和偏差分析
5. **四算状态机**: 在 Project 上增加四算状态字段

---

## 8. 实施优先级建议

### Phase 1: 基础闭环 (优先实施)

| 任务 | 工作量 | 优先级 |
|-----|-------|-------|
| 创建 project_estimates 表和 API | 3天 | P0 |
| 扩展 project_budgets 表（概算关联） | 1天 | P0 |
| 概算→预算转换 API | 1天 | P0 |
| 创建 project_settlement_finals 表和 API | 3天 | P0 |
| 项目四算状态字段 | 0.5天 | P0 |

### Phase 2: 控制机制 (次优先)

| 任务 | 工作量 | 优先级 |
|-----|-------|-------|
| 预算控制机制（采购/外协校验） | 2天 | P1 |
| 预算调整记录表和 API | 2天 | P1 |
| 成本台账表和 API | 3天 | P1 |
| 决算偏差分析 | 2天 | P1 |

### Phase 3: 管理提升 (后续)

| 任务 | 工作量 | 优先级 |
|-----|-------|-------|
| 经验库和模板反馈 | 3天 | P2 |
| 部门财务汇总 | 2天 | P2 |
| 四算检查点配置 | 2天 | P2 |
| 四算经营看板 | 3天 | P2 |

---

## 9. 附录

### 9.1 现有模型文件引用

- `app/models/project.py` - Project, ProjectCost, FinancialProjectCost, ProjectPaymentPlan
- `app/models/budget.py` - ProjectBudget, ProjectBudgetItem, ProjectCostAllocationRule
- `app/models/sales.py` - Quote, QuoteVersion, QuoteCostTemplate

### 9.2 现有 API 文件引用

- `app/api/v1/endpoints/budget.py` - 预算管理 API
- `app/api/v1/endpoints/costs/basic.py` - 成本 CRUD API
- `app/api/v1/endpoints/sales/cost_management.py` - 成本模板管理 API
- `app/api/v1/endpoints/projects/payment_plans.py` - 收款计划 API
- `app/api/v1/endpoints/timesheet/reports.py` - 工时成本报表 API

---

*报告生成日期：2026-01-17*
*分析依据：四算设计文档 v1.0*

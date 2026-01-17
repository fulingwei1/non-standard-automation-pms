# 项目四算体系设计文档

> 概算、预算、核算、决算 - 项目经营管理闭环

## 1. 背景与目标

### 1.1 四算的定义

| 阶段 | 含义 | 价值 |
|-----|------|------|
| **概算** | 设计项目利润的过程 | 从目标利润反推成本上限 |
| **预算** | 管理增收节支的过程 | 承接概算，细化到可执行 |
| **核算** | 管理增收节支的过程 | 归集实际成本，对比预算 |
| **决算** | 传承经验的过程 | 总结经验，反馈概算模板 |

### 1.2 核心理念

- **项目是细胞** - 项目是最小核算单元，项目清楚了，部门和公司就清楚了
- **各级一把手是概算经理** - 部门负责人对概算利润负责
- **四算拉通** - 概算→预算→核算→决算形成闭环，经验传承

### 1.3 设计目标

建立**分层四算体系**：

```
公司级经营看板
    ↑ 汇总
部门/系统部级汇总
    ↑ 汇总
项目级四算（概算→预算→核算→决算）
    ↑ 归集
机台/设备级明细
```

---

## 2. 概算模块设计

### 2.1 概算流程

```
合同金额（或报价）
    ↓
目标利润率（如25%）
    ↓
允许成本上限 = 合同金额 × (1 - 目标利润率)
    ↓
成本拆解（物料/人工/外协/其他）
    ↓
概算审批 → 成为预算基准
```

### 2.2 数据模型

#### 项目概算主表 `project_estimates`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 主键 |
| estimate_no | String(50) | 概算编号（GS+年月日+序号） |
| project_id | Integer | 项目ID（可空，中标后关联） |
| opportunity_id | Integer | 商机ID |
| quote_id | Integer | 报价ID |
| contract_amount | Numeric(14,2) | 合同/报价金额 |
| target_margin_rate | Numeric(5,2) | 目标利润率 |
| target_profit | Numeric(14,2) | 目标利润 |
| allowed_cost | Numeric(14,2) | 允许成本上限 |
| estimated_cost | Numeric(14,2) | 概算成本 |
| estimated_profit | Numeric(14,2) | 概算利润 |
| estimated_margin | Numeric(5,2) | 概算利润率 |
| estimate_manager_id | Integer | 概算经理ID |
| estimate_manager_name | String(50) | 概算经理姓名 |
| status | String(20) | 状态：DRAFT/SUBMITTED/APPROVED/REJECTED |
| version | String(20) | 版本号 |
| approved_by | Integer | 审批人 |
| approved_at | DateTime | 审批时间 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

#### 概算明细表 `project_estimate_items`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 主键 |
| estimate_id | Integer | 概算ID |
| cost_category | String(50) | 成本大类：MATERIAL/LABOR/OUTSOURCE/OTHER |
| cost_item | String(200) | 成本明细项 |
| estimated_amount | Numeric(14,2) | 概算金额 |
| reference_source | String(50) | 参考来源：TEMPLATE/HISTORY/MANUAL |
| reference_project_id | Integer | 参考项目ID |
| machine_id | Integer | 机台ID（可选） |
| remark | Text | 备注 |

### 2.3 概算审批层级

| 概算利润率 | 审批层级 | 审批人 |
|-----------|---------|-------|
| ≥25% | 一级 | 销售经理 |
| 20%-25% | 二级 | 部门负责人（概算经理） |
| 15%-20% | 三级 | 销售总监 |
| <15% | 四级 | 财务总监 + 总经理 |

---

## 3. 预算模块设计

### 3.1 预算流程

```
概算审批通过
    ↓
自动/手动生成预算草稿
    ↓
细化预算明细
    ↓
预算审批
    ↓
预算生效（控制采购/外协）
```

### 3.2 数据模型扩展

#### 现有 `project_budgets` 表扩展字段

| 字段 | 类型 | 说明 |
|-----|------|------|
| estimate_id | Integer | 关联概算ID |
| estimate_no | String(50) | 概算编号（冗余） |
| budget_source | String(20) | 来源：ESTIMATE/MANUAL/TEMPLATE |
| budget_category | String(20) | 类型：PROJECT/PLATFORM/SHARED |
| control_mode | String(20) | 控制模式：HARD/SOFT/NONE |
| warning_threshold | Numeric(5,2) | 预警阈值（如0.80） |
| original_amount | Numeric(14,2) | 原始预算 |
| adjusted_amount | Numeric(14,2) | 调整后预算 |
| adjustment_count | Integer | 调整次数 |

#### 新增：预算调整记录表 `project_budget_adjustments`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 主键 |
| budget_id | Integer | 预算ID |
| adjustment_no | String(50) | 调整单号 |
| adjustment_type | String(20) | 类型：INCREASE/DECREASE/TRANSFER |
| before_amount | Numeric(14,2) | 调整前金额 |
| adjust_amount | Numeric(14,2) | 调整金额 |
| after_amount | Numeric(14,2) | 调整后金额 |
| reason_category | String(50) | 原因分类：ECN/SCOPE_CHANGE/PRICE_CHANGE/OTHER |
| reason_detail | Text | 详细原因 |
| related_ecn_id | Integer | 关联ECN |
| status | String(20) | 状态 |
| submitted_by | Integer | 提交人 |
| approved_by | Integer | 审批人 |
| approved_at | DateTime | 审批时间 |

### 3.3 预算控制机制

采购/外协提交时自动校验：

| 预算使用率 | 控制模式=HARD | 控制模式=SOFT |
|-----------|--------------|--------------|
| <80% | 正常提交 | 正常提交 |
| 80%-100% | 预警，可提交 | 预警，可提交 |
| >100% | 阻止提交 | 预警，可提交 |

---

## 4. 核算模块设计

### 4.1 成本归集流程

```
采购入库 ──→ 自动归集物料成本
外协验收 ──→ 自动归集外协成本
工时审批 ──→ 自动计算人工成本
费用报销 ──→ 自动归集其他费用
         ↓
    项目成本台账
```

### 4.2 数据模型

#### 项目成本台账 `project_cost_ledgers`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 主键 |
| project_id | Integer | 项目ID |
| machine_id | Integer | 机台ID（可空） |
| period_type | String(20) | 期间类型：MONTHLY/QUARTERLY/YEARLY/CUMULATIVE |
| period_value | String(20) | 期间值（如2025-01） |
| material_cost | Numeric(14,2) | 物料成本 |
| labor_cost | Numeric(14,2) | 人工成本 |
| outsource_cost | Numeric(14,2) | 外协成本 |
| travel_cost | Numeric(14,2) | 差旅费用 |
| other_cost | Numeric(14,2) | 其他费用 |
| total_cost | Numeric(14,2) | 合计 |
| budget_amount | Numeric(14,2) | 对应预算 |
| variance_amount | Numeric(14,2) | 预算差异 |
| variance_rate | Numeric(5,2) | 差异率 |
| estimate_amount | Numeric(14,2) | 对应概算 |
| estimate_variance | Numeric(14,2) | 概算差异 |
| status | String(20) | 状态：DRAFT/CONFIRMED/LOCKED |
| confirmed_by | Integer | 确认人 |
| confirmed_at | DateTime | 确认时间 |

#### 成本归集规则表 `cost_allocation_rules`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 主键 |
| rule_name | String(100) | 规则名称 |
| rule_type | String(20) | 类型：DIRECT/SHARED/OVERHEAD |
| cost_category | String(50) | 适用成本类别 |
| source_module | String(50) | 来源模块 |
| allocation_basis | String(50) | 分摊依据 |
| allocation_formula | JSON | 分摊公式 |
| is_active | Boolean | 是否启用 |
| priority | Integer | 优先级 |

#### 部门财务汇总表 `dept_financial_summaries`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 主键 |
| dept_id | Integer | 部门ID |
| period_type | String(20) | 期间类型 |
| period_value | String(20) | 期间值 |
| project_count | Integer | 项目数量 |
| active_projects | Integer | 进行中项目 |
| completed_projects | Integer | 已完工项目 |
| total_estimate_revenue | Numeric(14,2) | 概算收入合计 |
| total_estimate_cost | Numeric(14,2) | 概算成本合计 |
| total_estimate_profit | Numeric(14,2) | 概算利润合计 |
| avg_estimate_margin | Numeric(5,2) | 平均概算利润率 |
| total_budget | Numeric(14,2) | 预算合计 |
| total_actual_cost | Numeric(14,2) | 实际成本合计 |
| total_actual_revenue | Numeric(14,2) | 实际收入合计 |
| total_actual_profit | Numeric(14,2) | 实际利润合计 |
| budget_variance | Numeric(14,2) | 预算偏差 |
| estimate_accuracy | Numeric(5,2) | 概算准确率 |

---

## 5. 决算模块设计

### 5.1 决算流程

```
项目完工
    ↓
财务决算（结清账目）
    ↓
偏差分析（找原因）
    ↓
经验沉淀（入知识库）
    ↓
反馈概算模板
```

### 5.2 数据模型

#### 项目决算表 `project_settlement_finals`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 主键 |
| settlement_no | String(50) | 决算编号 |
| project_id | Integer | 项目ID |
| project_code | String(50) | 项目编码 |
| estimate_id | Integer | 概算ID |
| budget_id | Integer | 预算ID |
| contract_amount | Numeric(14,2) | 合同金额 |
| change_amount | Numeric(14,2) | 变更金额 |
| final_revenue | Numeric(14,2) | 最终收入 |
| received_amount | Numeric(14,2) | 已回款 |
| receivable_amount | Numeric(14,2) | 应收未收 |
| material_cost | Numeric(14,2) | 物料成本 |
| labor_cost | Numeric(14,2) | 人工成本 |
| outsource_cost | Numeric(14,2) | 外协成本 |
| travel_cost | Numeric(14,2) | 差旅费用 |
| other_cost | Numeric(14,2) | 其他费用 |
| total_cost | Numeric(14,2) | 成本合计 |
| gross_profit | Numeric(14,2) | 毛利润 |
| gross_margin | Numeric(5,2) | 毛利率 |
| estimate_cost | Numeric(14,2) | 概算成本 |
| estimate_profit | Numeric(14,2) | 概算利润 |
| estimate_margin | Numeric(5,2) | 概算利润率 |
| cost_variance | Numeric(14,2) | 成本偏差 |
| profit_variance | Numeric(14,2) | 利润偏差 |
| estimate_accuracy | Numeric(5,2) | 概算准确率 |
| budget_amount | Numeric(14,2) | 预算金额 |
| budget_variance | Numeric(14,2) | 预算偏差 |
| budget_accuracy | Numeric(5,2) | 预算执行率 |
| status | String(20) | 状态 |
| settlement_date | Date | 决算日期 |
| prepared_by | Integer | 编制人 |
| reviewed_by | Integer | 审核人 |
| approved_by | Integer | 审批人 |
| approved_at | DateTime | 审批时间 |

#### 决算偏差分析表 `settlement_variance_analyses`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 主键 |
| settlement_id | Integer | 决算ID |
| variance_category | String(50) | 偏差分类 |
| variance_type | String(20) | 类型：FAVORABLE/UNFAVORABLE |
| estimated_amount | Numeric(14,2) | 概算金额 |
| actual_amount | Numeric(14,2) | 实际金额 |
| variance_amount | Numeric(14,2) | 偏差金额 |
| variance_rate | Numeric(5,2) | 偏差率 |
| root_cause | String(50) | 根本原因分类 |
| cause_detail | Text | 原因详述 |
| related_ecn_ids | JSON | 关联ECN |
| lesson_learned | Text | 经验教训 |
| improvement_action | Text | 改进措施 |
| feedback_to_template | Boolean | 是否反馈到概算模板 |
| template_update_note | Text | 模板更新说明 |

**根本原因分类（root_cause）：**
- ESTIMATE_ERROR - 概算估计不准
- PRICE_CHANGE - 价格变动
- SCOPE_CHANGE - 范围变更
- EFFICIENCY - 效率问题
- QUALITY_ISSUE - 质量问题返工
- EXTERNAL - 外部因素

#### 项目经验库表 `project_lessons_learned`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 主键 |
| settlement_id | Integer | 来源决算ID |
| project_id | Integer | 项目ID |
| project_type | String(50) | 项目类型 |
| product_category | String(50) | 产品类别 |
| industry | String(50) | 行业 |
| customer_id | Integer | 客户ID |
| contract_scale | String(20) | 合同规模区间 |
| lesson_type | String(50) | 经验类型：COST/SCHEDULE/QUALITY/RISK/OTHER |
| title | String(200) | 标题 |
| description | Text | 详细描述 |
| estimated_value | Numeric(14,2) | 概算值 |
| actual_value | Numeric(14,2) | 实际值 |
| variance_rate | Numeric(5,2) | 偏差率 |
| recommendation | Text | 建议 |
| applicable_scope | Text | 适用范围 |
| reference_count | Integer | 被引用次数 |
| last_referenced_at | DateTime | 最后引用时间 |

---

## 6. 四算拉通与LTC集成

### 6.1 集成点配置表 `four_estimate_checkpoints`

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 主键 |
| checkpoint_code | String(50) | 检查点编码 |
| checkpoint_name | String(100) | 检查点名称 |
| trigger_module | String(50) | 触发模块 |
| trigger_action | String(50) | 触发动作 |
| trigger_status | String(50) | 触发状态 |
| check_type | String(50) | 检查类型 |
| check_rule | JSON | 检查规则 |
| on_pass | String(50) | 通过时动作 |
| on_fail | String(50) | 失败时动作 |
| notify_roles | JSON | 通知角色 |
| is_active | Boolean | 是否启用 |

### 6.2 预置检查点

| 编码 | 名称 | 触发时机 | 检查内容 | 失败处理 |
|-----|------|---------|---------|---------|
| CP01 | 报价概算检查 | 报价提交审批 | 概算是否完成 | 阻止提交 |
| CP02 | 概算利润率检查 | 报价审批 | 利润率是否达标 | 升级审批 |
| CP03 | 签约概算检查 | 合同签订 | 概算是否审批通过 | 阻止签订 |
| CP04 | 项目预算检查 | 项目启动 | 预算是否生成 | 提醒生成 |
| CP05 | 采购预算检查 | 采购申请 | 是否超预算 | 预警/阻止 |
| CP06 | 完工决算检查 | 项目完工 | 决算是否完成 | 阻止结项 |
| CP07 | 结项决算检查 | 质保结束 | 决算是否审批 | 提醒完成 |

### 6.3 四算状态流转

```
项目状态        四算状态              允许操作
───────────────────────────────────────────────────
投标中         概算编制中            创建/编辑概算
               概算待审批            提交概算审批
               概算已审批            可以签合同
───────────────────────────────────────────────────
已签约         预算生成中            概算转预算
               预算待审批            提交预算审批
               预算已生效            可以执行采购
───────────────────────────────────────────────────
执行中         核算进行中            成本自动归集
               核算月度确认          月度核算确认
───────────────────────────────────────────────────
已完工         决算编制中            创建决算报告
               决算待审核            提交决算审批
               决算已完成            可以结项
───────────────────────────────────────────────────
已结项         四算归档              经验沉淀
```

---

## 7. 角色与权限设计

### 7.1 四算相关角色

| 角色代码 | 角色名称 | 职责 |
|---------|---------|------|
| estimate_manager | 概算经理 | 对项目概算负责，通常是部门负责人 |
| project_fc | 项目财经经理(PFC) | 项目级财务管理，负责四算执行 |
| dept_fc | 部门财经经理(BFC) | 部门级财务汇总与分析 |
| cfo | 财务总监 | 公司级财务管理 |

### 7.2 权限矩阵

| 功能 | 项目经理 | PFC | 概算经理 | BFC | CFO |
|-----|---------|-----|---------|-----|-----|
| 创建概算 | ✓ | ✓ | ✓ | - | - |
| 编辑概算 | ✓ | ✓ | ✓ | - | - |
| 审批概算(L1) | - | - | - | ✓ | - |
| 审批概算(L2) | - | - | ✓ | - | - |
| 审批概算(L3) | - | - | - | - | ✓ |
| 创建预算 | - | ✓ | - | - | - |
| 审批预算 | - | - | - | ✓ | ✓ |
| 查看成本 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 确认核算 | - | ✓ | - | ✓ | - |
| 创建决算 | - | ✓ | - | - | - |
| 审核决算 | - | - | ✓ | ✓ | - |
| 审批决算 | - | - | - | - | ✓ |
| 管理模板 | - | - | - | - | ✓ |

### 7.3 数据权限范围

| 角色 | 数据范围 |
|-----|---------|
| 项目经理 | 自己负责的项目 |
| PFC | 分配给自己的项目 |
| BFC | 部门所有项目 |
| CFO | 所有项目 |

---

## 8. 实施路径建议

### Phase 1：基础闭环（优先）

- [ ] 概算模块（简化版）
- [ ] 预算扩展（概算→预算转化）
- [ ] 核算归集（采购/外协自动归集）
- [ ] 决算模块（简化版）

### Phase 2：深化控制

- [ ] 预算控制（采购校验）
- [ ] 核算月度确认
- [ ] 决算偏差分析
- [ ] 经验库

### Phase 3：管理提升

- [ ] 部门级汇总
- [ ] 概算模板管理
- [ ] 四算检查点
- [ ] 经营分析报表

---

## 9. 与现有系统的集成点

| 现有模块 | 集成内容 |
|---------|---------|
| 报价模块 (Quote) | 增加概算关联，报价提交前必须完成概算 |
| 合同模块 (Contract) | 签约时检查概算审批状态 |
| 项目模块 (Project) | 增加四算状态字段，关联概算/预算/决算 |
| 采购模块 (Purchase) | 增加预算校验，成本自动归集 |
| 外协模块 (Outsourcing) | 增加预算校验，成本自动归集 |
| 工时模块 (Timesheet) | 人工成本自动归集到项目 |
| 角色权限 (Permission) | 新增 PFC/BFC/概算经理角色 |

---

*文档创建日期：2026-01-17*
*设计状态：已通过评审，待实施*

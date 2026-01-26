# 审批系统合并设计方案

> 日期: 2026-01-21
> 状态: 已批准

## 背景

当前系统存在审批系统重复实现问题：

- **服务层**: 31 个相关服务分布在两个目录
  - `approval_engine/` (24 个服务) - 活跃使用
  - `approval_workflow/` (5 个服务) - 无外部引用
- **数据库表**: 13 个审批相关表，仅 1 个有数据

## 决策

1. **服务层**: 保留 `approval_engine`，删除 `approval_workflow`
2. **数据库**: 合并为 3 张统一审批表，删除 13 个旧表

## 统一数据模型

### 架构

```
┌─────────────────────────────────────────────────────────────┐
│  approval_templates (审批模板)                               │
│  - 定义各业务类型的审批流程规则                               │
├─────────────────────────────────────────────────────────────┤
│  approval_instances (审批实例)                               │
│  - entity_type + entity_id 关联任意业务对象                  │
│  - 记录整体审批状态                                          │
├─────────────────────────────────────────────────────────────┤
│  approval_actions (审批动作)                                 │
│  - 记录每次审批/驳回/转审操作                                │
│  - 支持多级审批的历史追踪                                    │
└─────────────────────────────────────────────────────────────┘
```

### entity_type 枚举值

`CONTRACT`, `QUOTE`, `INVOICE`, `ECN`, `TIMESHEET`, `TASK`, `PROJECT`

## 表结构设计

### 1. approval_templates (审批模板)

```sql
CREATE TABLE approval_templates (
    id INTEGER PRIMARY KEY,
    entity_type VARCHAR(30) NOT NULL,     -- CONTRACT/QUOTE/INVOICE/ECN/TIMESHEET/TASK
    template_name VARCHAR(100) NOT NULL,
    description TEXT,

    -- 审批规则 (JSON)
    routing_rules JSON,                    -- 条件路由: {"amount>100000": "DIRECTOR"}
    approval_levels INTEGER DEFAULT 1,     -- 审批层级数

    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- 每种业务类型一个活跃模板
CREATE UNIQUE INDEX idx_template_active ON approval_templates(entity_type) WHERE is_active = 1;
```

### 2. approval_instances (审批实例)

```sql
CREATE TABLE approval_instances (
    id INTEGER PRIMARY KEY,
    template_id INTEGER REFERENCES approval_templates(id),

    -- 多态关联
    entity_type VARCHAR(30) NOT NULL,
    entity_id INTEGER NOT NULL,

    -- 状态
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING/APPROVED/REJECTED/CANCELLED
    current_level INTEGER DEFAULT 1,

    -- 发起人
    initiator_id INTEGER REFERENCES users(id),
    submitted_at DATETIME,
    completed_at DATETIME,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX idx_instance_entity ON approval_instances(entity_type, entity_id);
```

### 3. approval_actions (审批动作)

```sql
CREATE TABLE approval_actions (
    id INTEGER PRIMARY KEY,
    instance_id INTEGER REFERENCES approval_instances(id),

    -- 审批信息
    action_type VARCHAR(20) NOT NULL,      -- APPROVE/REJECT/DELEGATE/WITHDRAW
    approval_level INTEGER NOT NULL,

    -- 操作人
    actor_id INTEGER REFERENCES users(id),
    delegate_to_id INTEGER REFERENCES users(id),  -- 转审目标

    -- 意见
    comment TEXT,
    acted_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_action_instance ON approval_actions(instance_id);
```

## 迁移计划

### 数据迁移

仅 `task_approval_workflows` 有 59 条数据需要迁移：

```sql
-- 迁移到 approval_instances
INSERT INTO approval_instances (entity_type, entity_id, status, initiator_id, submitted_at, completed_at)
SELECT
    'TASK',
    task_id,
    approval_status,
    submitted_by,
    submitted_at,
    approved_at
FROM task_approval_workflows;

-- 迁移到 approval_actions (已审批的记录)
INSERT INTO approval_actions (instance_id, action_type, approval_level, actor_id, comment, acted_at)
SELECT
    ai.id,
    CASE WHEN taw.approval_status = 'APPROVED' THEN 'APPROVE' ELSE 'REJECT' END,
    1,
    taw.approver_id,
    COALESCE(taw.approval_note, taw.rejection_reason),
    taw.approved_at
FROM task_approval_workflows taw
JOIN approval_instances ai ON ai.entity_type = 'TASK' AND ai.entity_id = taw.task_id
WHERE taw.approval_status IN ('APPROVED', 'REJECTED');
```

### 删除的表 (13个)

迁移完成后删除以下空表：

1. `approval_history`
2. `approval_records`
3. `approval_workflow_steps`
4. `approval_workflows`
5. `contract_approvals`
6. `ecn_approval_matrix`
7. `ecn_approvals`
8. `quote_approvals`
9. `quote_cost_approvals`
10. `role_assignment_approvals`
11. `invoice_approvals`
12. `timesheet_approval_log`
13. `task_approval_workflows` (数据已迁移)

## 服务层重构

### 保留: approval_engine/

```
app/services/approval_engine/
├── __init__.py           # 统一导出
├── engine/
│   ├── core.py          # 核心流程控制
│   ├── submit.py        # 提交审批
│   ├── approve.py       # 审批/驳回
│   ├── actions.py       # 动作处理
│   └── query.py         # 查询服务
├── adapters/
│   ├── base.py          # 适配器基类
│   ├── contract.py      # 合同适配器
│   ├── quote.py         # 报价适配器
│   ├── invoice.py       # 发票适配器
│   ├── ecn.py           # ECN适配器
│   ├── timesheet.py     # 工时适配器
│   └── project.py       # 项目适配器
├── delegate.py          # 代理人服务
├── executor.py          # 节点执行器
├── notify/              # 通知服务
└── router.py            # 路由服务
```

### 删除: approval_workflow/

```
app/services/approval_workflow/  # 整个目录删除
├── __init__.py
├── approval_actions.py
├── core.py
├── helpers.py
├── queries.py
└── workflow_start.py
```

## 实施步骤

### Phase 1: 准备 (无破坏性)

1.1 创建新的 3 张统一表
1.2 创建新的 Model 类
1.3 编写数据迁移脚本

### Phase 2: 迁移数据

2.1 执行 task_approval_workflows → 新表迁移
2.2 验证数据完整性

### Phase 3: 切换服务层

3.1 更新 approval_engine 使用新表
3.2 删除 approval_workflow 目录
3.3 更新相关 import

### Phase 4: 清理

4.1 删除 13 个旧表
4.2 删除旧 Model 类
4.3 运行测试验证

## 风险控制

- **回滚点**: Phase 2 完成后可回滚（新旧表并存）
- **测试覆盖**: 现有 approval 相关测试需全部通过
- **零停机**: 迁移期间服务不中断

## 预计工作量

| 阶段 | 文件数 | 复杂度 |
|------|--------|--------|
| Phase 1 | 4 | 低 |
| Phase 2 | 2 | 低 |
| Phase 3 | ~15 | 中 |
| Phase 4 | ~20 | 低 |

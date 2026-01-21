# 项目管理模块整合设计文档

## 概述

本文档描述项目管理相关功能的整合方案，解决当前代码碎片化问题。

### 问题背景

当前项目管理功能过度拆分：
- **API 层**: 139 个文件分布在 13 个独立模块
- **服务层**: 21+ 个细碎服务，职责重叠
- **数据模型**: 15 个核心表（已良好组织）

### 核心痛点

1. **开发效率低** - 找代码困难，改动需要修改太多文件
2. **维护成本高** - 功能重复，逻辑不一致
3. **前端集成复杂** - API 太多太分散，调用复杂
4. **性能问题** - 服务之间调用链太长

---

## 设计目标

采用**按项目聚合 + 保留跨项目顶级路由**的混合模式，支持矩阵式管理的双维度查询需求。

---

## 目标架构

### 1. API 路由结构

#### 1.1 项目内操作路由（合并到 `/projects`）

```
/projects/
├── /                           # 项目列表、创建
├── /templates/*                # 项目模板 (已有)
├── /analytics/*                # 跨项目分析 (新增入口)
│
└── /{project_id}/
    ├── /                       # 项目详情、更新、删除
    ├── /overview               # 项目概览仪表盘
    │
    ├── /stages/                # ← 合并自 project_stages/
    │   ├── /                   # 阶段列表
    │   ├── /{stage_id}         # 阶段详情
    │   ├── /nodes/             # 节点操作
    │   └── /progress           # 阶段进度
    │
    ├── /progress/              # ← 合并自 progress/
    │   ├── /summary            # 进度摘要
    │   ├── /tasks/             # 任务进度
    │   ├── /forecast           # 进度预测
    │   └── /baselines/         # 基线管理
    │
    ├── /milestones/            # ← 合并自 milestones/
    │   ├── /                   # 里程碑列表
    │   └── /{milestone_id}     # 里程碑详情
    │
    ├── /members/               # ← 合并自 members/
    │   ├── /                   # 成员列表
    │   └── /{member_id}        # 成员详情
    │
    ├── /machines/              # ← 合并自 machines/
    │   ├── /                   # 设备列表
    │   └── /{machine_id}       # 设备详情
    │
    ├── /costs/                 # ← 合并自 costs/
    │   ├── /                   # 成本列表
    │   ├── /summary            # 成本汇总
    │   └── /budget             # 预算对比
    │
    ├── /roles/                 # ← 合并自 project_roles/
    │   └── /                   # 项目角色配置
    │
    ├── /evaluation/            # ← 合并自 project_evaluation/
    │   └── /                   # 项目评价
    │
    ├── /work-logs/             # ← 合并自 work_log/
    │   └── /                   # 工作日志
    │
    └── /timesheet/             # ← 合并自 timesheet/ (项目维度)
        └── /                   # 项目工时记录
```

#### 1.2 跨项目顶级路由（保持独立）

```
/my/                            # 个人维度
├── /projects                   # 我参与的项目列表
├── /timesheet/                 # ← 合并自 timesheet/ (个人维度)
│   ├── /                       # 我的工时记录
│   ├── /summary                # 我的工时汇总
│   └── /pending                # 待填报提醒
├── /workload                   # 我的工作量
├── /tasks                      # 我的任务
└── /work-logs                  # 我的工作日志

/departments/{dept_id}/         # 部门维度
├── /workload                   # ← 合并自 workload/
│   ├── /summary                # 部门工作量汇总
│   ├── /distribution           # 负载分布
│   └── /members/{user_id}      # 成员工作量详情
├── /projects                   # 部门相关项目
└── /timesheet/                 # 部门工时统计
    └── /summary                # 部门工时汇总

/analytics/                     # 组织/PMO 维度 (新增)
├── /projects/
│   ├── /health                 # 项目健康度汇总
│   ├── /progress               # 跨项目进度对比
│   ├── /risks                  # 风险汇总
│   └── /pipeline               # 项目管道分析
├── /workload/
│   ├── /overview               # 全局工作量概览
│   └── /bottlenecks            # 资源瓶颈分析
└── /costs/
    ├── /summary                # 成本汇总
    └── /variance               # 成本偏差分析
```

### 2. 服务层结构

从 21+ 个细碎服务整合为 5 个核心服务：

```
app/services/project/
├── __init__.py
│
├── core_service.py             # 项目核心 CRUD + 状态管理
│   └── ProjectCoreService
│       ├── create/update/delete/get
│       ├── change_status()
│       └── clone_project()
│
├── execution_service.py        # 执行层：阶段 + 进度 + 里程碑
│   └── ProjectExecutionService
│       ├── get_stages() / update_stage()
│       ├── get_progress() / update_progress()
│       ├── get_milestones()
│       └── forecast_completion()
│
├── resource_service.py         # 资源层：成员 + 工时 + 工作量
│   └── ProjectResourceService
│       ├── get_members() / assign_member()
│       ├── get_timesheet() / log_time()
│       └── calculate_workload()
│
├── finance_service.py          # 财务层：成本 + 预算 + 付款
│   └── ProjectFinanceService
│       ├── get_costs() / add_cost()
│       ├── get_budget_variance()
│       └── get_payment_plans()
│
└── analytics_service.py        # 分析层：仪表盘 + 统计 + 报表
    └── ProjectAnalyticsService
        ├── get_dashboard()
        ├── get_health_summary()
        ├── get_cross_project_stats()
        └── export_report()
```

### 3. 目录结构变化

#### 3.1 API 层目录

**迁移前** (13 个独立目录):
```
app/api/v1/endpoints/
├── projects/           (51 files)
├── progress/           (18 files)
├── project_stages/     (12 files)
├── milestones/         (3 files)
├── members/            (5 files)
├── machines/           (4 files)
├── costs/              (8 files)
├── timesheet/          (8 files)
├── workload/           (6 files)
├── work_log/           (5 files)
├── project_evaluation/ (4 files)
├── project_roles/      (6 files)
└── rd_project/         (9 files)
```

**迁移后** (4 个聚合目录):
```
app/api/v1/endpoints/
├── projects/           # 项目内所有操作
│   ├── core/
│   ├── stages/
│   ├── progress/
│   ├── milestones/
│   ├── members/
│   ├── machines/
│   ├── costs/
│   ├── roles/
│   ├── evaluation/
│   ├── work_logs/
│   ├── timesheet/
│   └── templates/
├── my/                 # 个人维度
├── departments/        # 部门维度
└── analytics/          # 组织/PMO 维度
```

---

## 迁移策略

### Phase 1: 后端准备 (1-2 天)

**目标**: 创建新结构，新旧并存

1. 创建新目录结构
   ```
   app/api/v1/endpoints/projects/stages/
   app/api/v1/endpoints/projects/progress/
   app/api/v1/endpoints/my/
   app/api/v1/endpoints/departments/
   app/api/v1/endpoints/analytics/
   app/services/project/
   ```

2. 创建新服务类（空壳，逐步迁移逻辑）

3. 注册新路由（与旧路由并存）

### Phase 2: 后端迁移 (3-5 天)

**目标**: 迁移业务逻辑，旧路由代理到新路由

1. 按模块迁移业务逻辑到新服务
2. 新路由调用新服务
3. 旧路由添加 deprecation 警告并代理到新路由

```python
# 兼容层示例
@router.get("/milestones/{milestone_id}", deprecated=True)
async def get_milestone_legacy(milestone_id: int, db: Session = Depends(get_db)):
    """
    Deprecated: 请使用 GET /projects/{project_id}/milestones/{milestone_id}
    """
    # 查找 milestone 所属项目
    milestone = db.query(ProjectMilestone).filter_by(id=milestone_id).first()
    if not milestone:
        raise HTTPException(404, "Milestone not found")
    # 代理到新路由
    return await get_project_milestone(milestone.project_id, milestone_id, db)
```

4. 单元测试验证

### Phase 3: 前端迁移 (2-3 天)

**目标**: 更新前端 API 调用

1. 更新 `frontend/src/services/api/projects.js`
   - 整合 progress.js, workload.js 等内容

2. 创建新 API 模块
   - `frontend/src/services/api/my.js`
   - `frontend/src/services/api/departments.js`
   - `frontend/src/services/api/analytics.js`

3. 更新组件调用

4. 删除废弃的 API 文件

5. 集成测试

### Phase 4: 清理 (1 天)

**目标**: 移除旧代码

1. 移除后端旧路由文件
2. 移除旧服务文件
3. 更新 API 文档
4. 更新 CLAUDE.md

---

## 模块映射表

| 原模块 | 目标位置 | 文件数 | 优先级 |
|--------|----------|--------|--------|
| `project_stages/` | `projects/{id}/stages/` | 12 | P1 |
| `progress/` | `projects/{id}/progress/` | 18 | P1 |
| `milestones/` | `projects/{id}/milestones/` | 3 | P2 |
| `members/` | `projects/{id}/members/` | 5 | P2 |
| `machines/` | `projects/{id}/machines/` | 4 | P2 |
| `costs/` | `projects/{id}/costs/` | 8 | P2 |
| `project_roles/` | `projects/{id}/roles/` | 6 | P3 |
| `project_evaluation/` | `projects/{id}/evaluation/` | 4 | P3 |
| `work_log/` | `projects/{id}/work-logs/` | 5 | P3 |
| `timesheet/` (项目) | `projects/{id}/timesheet/` | 4 | P3 |
| `timesheet/` (个人) | `my/timesheet/` | 4 | P3 |
| `workload/` (部门) | `departments/{id}/workload/` | 6 | P3 |

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 旧 API 调用失败 | 高 | 保留旧路由作为代理，添加 deprecation 头 |
| 服务层调用链断裂 | 中 | 渐进式迁移，旧服务暂时代理到新服务 |
| 前端遗漏更新 | 中 | 后端日志记录废弃 API 调用，主动发现遗漏 |
| 测试覆盖不足 | 低 | 迁移前补充关键路径测试 |

---

## 预期收益

1. **开发效率提升**
   - API 文件数从 139 减少到约 60
   - 服务文件数从 21+ 减少到 5

2. **前端集成简化**
   - 路由前缀从 13 个减少到 4 个
   - API 调用更直观（RESTful 嵌套资源）

3. **维护成本降低**
   - 职责边界清晰
   - 重复逻辑消除

4. **性能改善**
   - 服务调用链缩短
   - 数据查询可优化（减少跨服务查询）

---

## 附录

### A. 当前模块统计

```
API 层:
├── projects/           51 files
├── progress/           18 files
├── project_stages/     12 files
├── rd_project/          9 files
├── costs/               8 files
├── timesheet/           8 files
├── project_roles/       6 files
├── workload/            6 files
├── members/             5 files
├── work_log/            5 files
├── machines/            4 files
├── project_evaluation/  4 files
└── milestones/          3 files
Total: 139 files

服务层:
├── project_*_service.py    13 files
├── progress_*_service.py    3 files
└── stage_*_service.py       3 files
Total: 21+ files
```

### B. 前端 API 模块

```
frontend/src/services/api/
├── projects.js      # 需要整合其他模块
├── progress.js      # → 合并到 projects.js
├── workload.js      # → 拆分到 my.js + departments.js
└── ...
```

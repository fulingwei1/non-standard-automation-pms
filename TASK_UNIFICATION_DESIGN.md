# 双任务表整合设计（A 路线：task_unified 收编 tasks）

> 日期：2026-07-03 · 状态：**P1+P2+P3 已完成**（P2/P3 以门面方案原子切换，commit 20e106fa；余 P4 旧表下线）
> 背景：`tasks`(项目执行任务, 131行) 与 `task_unified`(任务中心, 91行) 并存互不相通——
> task_unified 模型自称"统一任务表（聚合所有类型任务）"且 source_type 预留 PROJECT，
> 但项目任务从未收编。本设计按其原始意图完成统一。

## 一、目标与原则

1. **单一事实源**：所有任务（项目执行/工作流/审批待办/手工）最终只存 `task_unified`。
2. **契约不破**：现有 API 路径与响应形状不变（`/progress/projects/{id}/tasks`、`/task-center/*` 均保留），只换底层数据源——前端页面无感。
3. **可回滚**：迁移全程保留旧表与 ID 映射表，任何阶段可切回。
4. **分期落地**：四个阶段，每期独立验收、独立提交，期间系统始终可用。

## 二、现状事实（2026-07-03 勘察）

| | tasks | task_unified |
|---|---|---|
| 模型 | models/progress.py `Task`（18列） | models/task_center.py `TaskUnified`（61列） |
| 数据 | 131 行（TODO 55 / IN_PROGRESS 33 / DONE 40 / NULL 3） | 91 行（WORKFLOW 50 / CONTRACT_APPROVAL 20 / 其他 21） |
| 后端消费 | **34 文件**（13 端点 + 21 服务：进度/工时/负荷/绩效/健康度/导出/仪表盘） | **30 文件**（task_center 全套端点 + 服务） |
| 前端 | ProgressBoard、ProjectDetail/TasksTab、progress.js | TaskCenter 页、task.js |
| FK 引用 | task_dependencies(14行,双列)、progress_logs(20)、baseline_tasks(8)、progress_reports(3)、quality_risk_detection(3) | parent_task_id 自引用 |
| 已知断链 | 前端 taskApi.update/delete 调 PUT/DELETE /tasks/* **后端从不存在** | — |

冲突检查：两表 task_code 零冲突；tasks.owner_id 有 10 行 NULL（task_unified.assignee_id NOT NULL，迁移需兜底）。

## 三、目标模型：task_unified 扩展

新增 5 列（alembic + sqlite/mysql 双迁移）：

```sql
ALTER TABLE task_unified ADD COLUMN project_stage VARCHAR(20);   -- 承接 tasks.stage (S1-S9)
ALTER TABLE task_unified ADD COLUMN machine_id INTEGER;          -- 承接 tasks.machine_id
ALTER TABLE task_unified ADD COLUMN milestone_id INTEGER;        -- 承接 tasks.milestone_id
ALTER TABLE task_unified ADD COLUMN weight NUMERIC(5,2);         -- 承接 tasks.weight (进度加权)
ALTER TABLE task_unified ADD COLUMN block_reason TEXT;           -- 承接 tasks.block_reason
-- 索引: idx_tu_project_stage(project_id, project_stage), idx_tu_machine(machine_id)
```

## 四、字段映射

| tasks | task_unified | 说明 |
|---|---|---|
| id | —（新自增） | 旧→新写入 `task_id_map` 映射表 |
| project_id | project_id | 直迁；同时回填 project_code/project_name（冗余列） |
| machine_id / milestone_id | machine_id / milestone_id | 新列直迁 |
| task_code | task_code | 零冲突已验证；NULL 则生成 `PT-{old_id}` |
| task_name | title | 直迁 |
| stage | project_stage | 新列直迁 |
| status | status | 值映射：TODO→PENDING · IN_PROGRESS→IN_PROGRESS · DONE→COMPLETED · BLOCKED→PAUSED(+block_reason) · NULL→PENDING |
| owner_id | assignee_id | NULL(10行) 兜底为项目 pm_id，再兜底 admin；assignee_name 同步回填 |
| plan_start / plan_end | plan_start_date / plan_end_date | 直迁 |
| actual_start / actual_end | actual_start_date / actual_end_date | 直迁 |
| progress_percent | progress | 直迁 |
| weight / block_reason | weight / block_reason | 新列直迁 |
| —（常量） | task_type='PROJECT', source_type='PROJECT', source_id=project_id | 收编标记 |

task-center 状态机（PENDING/IN_PROGRESS/COMPLETED/PAUSED，来自 batch_status.py 实测）完全覆盖 tasks 的取值域。

## 五、ID 策略与引用重接

新表自增导致旧 id 失效，迁移事务内：

1. 建 `task_id_map(old_task_id PK, new_task_id, migrated_at)`。
2. 逐行 INSERT task_unified → 记映射。
3. 重接 5 张 FK 表（合计 48 行）：task_dependencies(task_id+depends_on_task_id)、progress_logs、baseline_tasks、progress_reports、quality_risk_detection。
4. **非 FK 引用排查**（无外键约束、fk_clean 扫不到，逐一确认）：`timesheet.task_id`、`work_log_mentions(target_type='TASK')`、`task_unified.source_id`、以及全库 `%task_id%` 列清单在 Phase 1 执行前用 PRAGMA 全表扫描定稿。

回滚：旧表全程不删；`task_id_map` 反向即可恢复引用；Phase 4 前任何时点可切回。

## 六、消费方改造（34 文件分三批）

- **批1·读路径（低危）**：progress_compat、projects/progress/summary、workload_compat、projects/workload、performance/*(3)、dashboard/*(3)、health_*(2)、delay_root_cause、project_timeline、project_export、issues/related_lists —— `db.query(Task)` → `db.query(TaskUnified).filter(task_type=='PROJECT')`，建议先落一个 `project_tasks_query(db)` helper 统一入口。
- **批2·写路径（中危）**：progress_compat 创建任务、template_projects、template_configs/apply、unified_import/task_importer、pmo_initiation 售前遗留事项同步、AI 日报 tasks 扫描 —— 写 TaskUnified（带 task_type='PROJECT' 常量与冗余列回填）。
- **批3·关联路径**：projects/timesheet、projects/members、resource_plan、change_impact、timesheet/records —— task_id 语义换新 id（依赖第五节重接完成）。

## 七、前端改造

1. progress.js taskApi：**顺带修断链**——update/delete/updateProgress 改调 task-center 既有端点（PUT /task-center/tasks/{id} 等），list/get 维持 /progress 契约不动。
2. TaskCenter 页新增"项目任务"过滤（task_type=PROJECT 自然可见，验证我的任务聚合）。
3. ProgressBoard/TasksTab 无改动（后端契约不变）。

## 八、分期计划与验收

| 期 | 内容 | 验收标准 |
|---|---|---|
| **P1 扩列+迁移+双读校验** | 新列迁移、数据迁移脚本、task_id_map、FK 重接；tasks 保留只读 | ①131 行全部入 task_unified 且逐字段比对一致 ②5 张引用表 48 行重接后行数/关联完整 ③双读对账脚本：新旧两源逐项目任务数/状态分布一致 |
| **P2 写路径切换** | 批2 改造；tasks 表停写 | ①新建项目任务落 task_unified ②WBS 模板生成、售前遗留同步、导入链全部落新表 ③tasks 表行数冻结 |
| **P3 读路径+前端** | 批1/批3 改造；前端断链修复 | ①进度/工时/负荷/绩效/日报数字与 P1 对账基线一致 ②任务中心"我的任务"含项目任务 ③项目任务页编辑/删除首次真正可用 |
| **P4 下线** | Task 模型删除、tasks 表改名 tasks_deprecated（保留一个版本周期后删） | 全库无 models.progress.Task 引用；全量回归绿 |

每期独立 commit + push；P1-P3 期间出现异常按第五节回滚。

## 九、风险与对策

| 风险 | 对策 |
|---|---|
| 隐蔽的 task_id 引用漏扫 | P1 前全库列名扫描 + 双读校验期观察；老表保留可追溯 |
| 绩效/负荷统计口径漂移 | P1 建立对账基线（每人/每项目任务数、工时汇总），P3 复算比对 |
| task-center 权限模型与项目任务不匹配（项目成员可见性 vs assignee 可见性） | P3 在 my_tasks/overview 增加 task_type=PROJECT 时按项目成员放行的分支；单独测试 |
| 测试面大（进度/绩效/工时相关既有用例） | 每期跑定向 sweep；已知隔离债用单文件复核 |

## 十、工作量粗估

P1 ≈ 2-3 天（迁移+校验脚本为主）；P2 ≈ 2 天；P3 ≈ 4-6 天（消费面最大）；P4 ≈ 1 天。合计 **9-12 个工作日**，比原估 2-4 周乐观，因消费方多为查询语句替换且契约不变。

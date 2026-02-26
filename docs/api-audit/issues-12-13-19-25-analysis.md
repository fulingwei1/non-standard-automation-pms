# API 端点审计分析：Issues #12, #13, #19, #25

日期: 2026-02-26

## #12 Roles 双入口

**文件:**
- `app/api/v1/endpoints/roles.py` → `/roles/` — 系统级角色 CRUD（角色管理、权限分配、导航配置）
- `app/api/v1/endpoints/projects/roles/` → `/projects/{project_id}/roles/` — 项目级角色（项目角色配置、负责人、团队成员）

**结论: 不同域，无需合并** ✅

系统角色管理（创建/编辑角色定义）与项目角色分配（谁在哪个项目担任什么角色）是完全不同的业务域。路由前缀也清晰区分。

## #13 Timesheet 双入口

**文件:**
- `app/api/v1/endpoints/timesheet/` → `/timesheet/` — 全局工时管理（记录、审批、周报、月报、统计、报表、工作流）
- `app/api/v1/endpoints/projects/timesheet/` → `/projects/{project_id}/timesheet/` — 项目维度工时 CRUD

**结论: 不同域，无需合并** ✅

全局工时管理（跨项目的工时记录和审批流）与项目维度工时查询（特定项目下的工时统计）是不同的访问视角。RESTful 设计中这是标准的资源嵌套模式。

## #19 任务进度更新双入口

**文件:**
- `app/api/v1/endpoints/engineers/progress.py` → 权限 `engineer:read`，使用 `schemas.ProgressUpdateRequest`
- `app/api/v1/endpoints/task_center/update.py` → 权限 `task_center:update`，使用 `TaskProgressUpdate`

**结论: 有意设计，不同角色入口** ✅

两者都调用同一个底层服务 `task_progress_service.update_task_progress`，但面向不同用户角色：
- 工程师通过工程师面板更新自己的任务进度
- 项目管理员通过任务中心更新任意任务进度

不同的权限要求和 schema 验证证明这是合理的多入口设计。`task_center/update.py` 的文档也明确说明了这一点。

## #25 批量操作

**文件（7个）:**
1. `task_center/batch.py` — 路由聚合器（无业务逻辑）
2. `task_center/batch_helpers.py` — 辅助函数
3. `task_center/batch_status.py` — 状态批量操作
4. `task_center/batch_attributes.py` — 属性批量操作
5. `task_center/batch_statistics.py` — 批量操作统计
6. `issues/batch.py` — 问题批量操作
7. `projects/status/batch.py` — 项目状态批量操作

**结论: 已重构完成** ✅

所有批量操作端点已迁移到通用框架 `app/utils/batch_operations.py`（`BatchOperationExecutor`）。该框架提供：
- 统一的验证、执行、日志记录流程
- 事务管理
- 数据范围过滤（`create_scope_filter`）
- 软删除/硬删除支持
- 状态批量更新快捷方法

无需额外提取 `BatchOperationMixin`，现有的 `BatchOperationExecutor` 组合模式比 Mixin 继承更灵活。

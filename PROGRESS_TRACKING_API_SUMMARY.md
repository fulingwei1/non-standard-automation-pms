# 进度跟踪 API 实现总结

## 概述

本文档总结了进度跟踪模块（WBS模板管理、项目任务管理、进度填报、进度看板与报表）的 API 实现情况。

## 实现时间

2025-01-XX

## 1. WBS 模板管理 API (`/api/v1/wbs-templates`)

### 1.1 WBS模板列表

**端点**: `GET /wbs-templates`

**功能**:
- 获取WBS模板列表（支持分页、搜索、筛选）

**请求参数**:
- `page`: 页码（查询参数，默认1）
- `page_size`: 每页数量（查询参数，默认20）
- `keyword`: 关键词搜索（查询参数，可选，搜索模板编码/名称）
- `project_type`: 项目类型筛选（查询参数，可选）
- `equipment_type`: 设备类型筛选（查询参数，可选）
- `is_active`: 是否启用（查询参数，可选）

**响应**: `WbsTemplateListResponse`

### 1.2 WBS模板详情

**端点**: `GET /wbs-templates/{template_id}`

**功能**:
- 获取WBS模板的详细信息

**响应**: `WbsTemplateResponse`

### 1.3 创建WBS模板

**端点**: `POST /wbs-templates`

**功能**:
- 创建新的WBS模板

**请求体**: `WbsTemplateCreate`

**响应**: `WbsTemplateResponse`

### 1.4 更新WBS模板

**端点**: `PUT /wbs-templates/{template_id}`

**功能**:
- 更新WBS模板信息

**请求体**: `WbsTemplateUpdate`

**响应**: `WbsTemplateResponse`

### 1.5 模板任务列表

**端点**: `GET /wbs-templates/{template_id}/tasks`

**功能**:
- 获取WBS模板的任务列表

**响应**: `List[WbsTemplateTaskResponse]`

### 1.6 添加模板任务

**端点**: `POST /wbs-templates/{template_id}/tasks`

**功能**:
- 向WBS模板添加任务

**请求体**: `WbsTemplateTaskCreate`

**响应**: `WbsTemplateTaskResponse`

### 1.7 更新模板任务

**端点**: `PUT /wbs-template-tasks/{task_id}`

**功能**:
- 更新WBS模板任务信息

**请求体**: `WbsTemplateTaskUpdate`

**响应**: `WbsTemplateTaskResponse`

## 2. 项目任务管理 API

### 2.1 从模板初始化WBS

**端点**: `POST /projects/{project_id}/init-wbs`

**功能**:
- 从WBS模板一键生成项目计划
- 自动创建项目任务和任务依赖关系

**请求体**: `InitWbsRequest`

**请求参数**:
- `template_id`: WBS模板ID
- `start_date`: 项目开始日期
- `machine_ids`: 机台ID列表（可选）

**响应**: `InitWbsResponse`

**响应数据**:
```json
{
  "project_id": 1,
  "template_id": 1,
  "template_name": "标准单机类WBS模板",
  "created_tasks": 50,
  "created_dependencies": 30,
  "start_date": "2025-02-01",
  "tasks": [...]
}
```

### 2.2 项目任务列表

**端点**: `GET /projects/{project_id}/tasks`

**功能**:
- 获取项目的任务列表
- 支持筛选（阶段、状态、负责人等）

**请求参数**:
- `stage`: 阶段筛选（查询参数，可选）
- `status`: 状态筛选（查询参数，可选）
- `assignee_id`: 负责人ID筛选（查询参数，可选）

**响应**: `TaskListResponse`

### 2.3 创建项目任务

**端点**: `POST /projects/{project_id}/tasks`

**功能**:
- 创建新的项目任务

**请求体**: `TaskCreate`

**响应**: `TaskResponse`

### 2.4 更新项目任务

**端点**: `PUT /tasks/{task_id}`

**功能**:
- 更新项目任务信息

**请求体**: `TaskUpdate`

**响应**: `TaskResponse`

### 2.5 任务详情

**端点**: `GET /tasks/{task_id}`

**功能**:
- 获取任务的详细信息

**响应**: `TaskResponse`

### 2.6 更新任务进度

**端点**: `PUT /tasks/{task_id}/progress`

**功能**:
- 更新任务的进度百分比

**请求参数**:
- `progress_pct`: 进度百分比（查询参数，0-100）

**响应**: `TaskResponse`

### 2.7 完成任务

**端点**: `PUT /tasks/{task_id}/complete`

**功能**:
- 标记任务为已完成
- 自动更新进度为100%

**响应**: `TaskResponse`

### 2.8 任务依赖关系

**端点**: `GET /tasks/{task_id}/dependencies`

**功能**:
- 获取任务的前置任务列表

**响应**: `List[TaskDependencyResponse]`

### 2.9 设置任务依赖

**端点**: `POST /tasks/{task_id}/dependencies`

**功能**:
- 设置任务的前置任务依赖

**请求体**: `TaskDependencyCreate`

**请求参数**:
- `depends_on_task_id`: 前置任务ID

**响应**: `TaskDependencyResponse`

### 2.10 任务负责人分配

**端点**: `PUT /tasks/{task_id}/assignee`

**功能**:
- 分配或更新任务负责人

**请求体**: `TaskAssigneeUpdate`

**请求参数**:
- `assignee_id`: 负责人ID

**响应**: `TaskResponse`

## 3. 进度填报 API

### 3.1 提交进度日报

**端点**: `POST /progress-reports`

**功能**:
- 提交进度日报或周报

**请求体**: `ProgressReportCreate`

**请求参数**:
- `project_id`: 项目ID
- `report_type`: 报告类型（DAILY/WEEKLY）
- `report_date`: 报告日期
- `tasks`: 任务进度列表

**响应**: `ProgressReportResponse`

### 3.2 进度报告列表

**端点**: `GET /progress-reports`

**功能**:
- 获取进度报告列表（支持分页、筛选）

**请求参数**:
- `page`: 页码（查询参数，默认1）
- `page_size`: 每页数量（查询参数，默认20）
- `project_id`: 项目ID筛选（查询参数，可选）
- `report_type`: 报告类型筛选（查询参数，可选）
- `start_date`: 开始日期（查询参数，可选）
- `end_date`: 结束日期（查询参数，可选）

**响应**: `ProgressReportListResponse`

### 3.3 进度报告详情

**端点**: `GET /progress-reports/{report_id}`

**功能**:
- 获取进度报告的详细信息

**响应**: `ProgressReportResponse`

### 3.4 项目进度汇总

**端点**: `GET /projects/{project_id}/progress-summary`

**功能**:
- 获取项目整体完成率
- 包含各阶段进度统计

**响应**: `ProgressSummaryResponse`

**响应数据**:
```json
{
  "project_id": 1,
  "project_name": "项目1",
  "total_tasks": 100,
  "completed_tasks": 60,
  "in_progress_tasks": 30,
  "pending_tasks": 10,
  "overall_progress": 65.5,
  "by_stage": [
    {
      "stage": "S1",
      "stage_name": "需求分析",
      "total_tasks": 10,
      "completed_tasks": 10,
      "progress": 100.0
    }
  ]
}
```

### 3.5 机台进度汇总

**端点**: `GET /machines/{machine_id}/progress-summary`

**功能**:
- 获取机台的整体完成率
- 包含各阶段进度统计

**响应**: `MachineProgressSummaryResponse`

## 4. 进度看板与报表 API

### 4.1 甘特图数据

**端点**: `GET /projects/{project_id}/gantt`

**功能**:
- 获取项目的甘特图数据
- 包含任务时间线、依赖关系

**响应**: `GanttDataResponse`

**响应数据**:
```json
{
  "project_id": 1,
  "tasks": [
    {
      "id": 1,
      "name": "任务1",
      "start_date": "2025-02-01",
      "end_date": "2025-02-10",
      "progress": 50.0,
      "status": "IN_PROGRESS",
      "dependencies": [2]
    }
  ]
}
```

### 4.2 进度看板

**端点**: `GET /projects/{project_id}/progress-board`

**功能**:
- 获取项目的进度看板数据
- 按状态分组显示任务

**响应**: `ProgressBoardResponse`

**响应数据**:
```json
{
  "project_id": 1,
  "columns": [
    {
      "status": "PENDING",
      "status_name": "待开始",
      "tasks": [...],
      "count": 10
    },
    {
      "status": "IN_PROGRESS",
      "status_name": "进行中",
      "tasks": [...],
      "count": 30
    },
    {
      "status": "COMPLETED",
      "status_name": "已完成",
      "tasks": [...],
      "count": 60
    }
  ]
}
```

### 4.3 里程碑达成率

**端点**: `GET /reports/milestone-rate`

**功能**:
- 获取里程碑达成率统计

**请求参数**:
- `project_ids`: 项目ID列表（查询参数，可选，逗号分隔）
- `start_date`: 开始日期（查询参数，可选）
- `end_date`: 结束日期（查询参数，可选）

**响应**: `MilestoneRateResponse`

### 4.4 延期原因统计

**端点**: `GET /reports/delay-reasons`

**功能**:
- 获取延期原因统计（Top N）

**请求参数**:
- `project_ids`: 项目ID列表（查询参数，可选，逗号分隔）
- `top_n`: Top N数量（查询参数，可选，默认10）

**响应**: `DelayReasonsResponse`

**响应数据**:
```json
{
  "total_delayed_tasks": 50,
  "reasons": [
    {
      "reason": "物料短缺",
      "count": 20,
      "percentage": 40.0
    },
    {
      "reason": "人员不足",
      "count": 15,
      "percentage": 30.0
    }
  ]
}
```

### 4.5 计划基线管理

**端点**: `GET /projects/{project_id}/baselines`

**功能**:
- 获取项目的计划基线列表

**响应**: `BaselineListResponse`

**端点**: `POST /projects/{project_id}/baselines`

**功能**:
- 创建项目计划基线（快照当前计划）

**请求体**: `BaselineCreate`

**响应**: `BaselineResponse`

**端点**: `GET /baselines/{baseline_id}`

**功能**:
- 获取计划基线的详细信息

**响应**: `BaselineResponse`

## 5. 实现特性

### 5.1 WBS模板管理

- ✅ 支持单机类/线体类模板
- ✅ 模板任务管理（包含依赖关系）
- ✅ 模板版本管理

### 5.2 项目任务管理

- ✅ 从模板一键初始化WBS
- ✅ 任务依赖关系管理
- ✅ 任务进度跟踪
- ✅ 任务负责人分配

### 5.3 进度填报

- ✅ 支持日报/周报
- ✅ 任务进度批量更新
- ✅ 项目/机台进度汇总

### 5.4 进度看板与报表

- ✅ 甘特图数据生成
- ✅ 进度看板（按状态分组）
- ✅ 里程碑达成率统计
- ✅ 延期原因分析
- ✅ 计划基线管理

## 6. 数据模型

### 6.1 WbsTemplate

- `template_code`: 模板编码
- `template_name`: 模板名称
- `project_type`: 项目类型
- `equipment_type`: 设备类型
- `version_no`: 版本号
- `is_active`: 是否启用

### 6.2 WbsTemplateTask

- `template_id`: 模板ID
- `task_name`: 任务名称
- `stage`: 阶段（S1-S9）
- `default_owner_role`: 默认负责人角色
- `plan_days`: 计划天数
- `weight`: 权重
- `depends_on_template_task_id`: 依赖的模板任务ID

### 6.3 Task

- `project_id`: 项目ID
- `machine_id`: 机台ID（可选）
- `task_name`: 任务名称
- `stage`: 阶段
- `status`: 状态（PENDING/IN_PROGRESS/COMPLETED/BLOCKED）
- `progress_pct`: 进度百分比
- `assignee_id`: 负责人ID
- `plan_start_date`: 计划开始日期
- `plan_end_date`: 计划结束日期
- `actual_start_date`: 实际开始日期
- `actual_end_date`: 实际结束日期

### 6.4 TaskDependency

- `task_id`: 任务ID
- `depends_on_task_id`: 前置任务ID
- `dependency_type`: 依赖类型（FS/SS/FF/SF）

### 6.5 ProgressReport

- `project_id`: 项目ID
- `report_type`: 报告类型（DAILY/WEEKLY）
- `report_date`: 报告日期
- `reporter_id`: 报告人ID
- `tasks`: 任务进度列表（JSON）

## 7. 使用示例

### 7.1 从模板初始化WBS

```bash
POST /api/v1/projects/1/init-wbs
Content-Type: application/json

{
  "template_id": 1,
  "start_date": "2025-02-01",
  "machine_ids": [1, 2]
}
```

### 7.2 更新任务进度

```bash
PUT /api/v1/tasks/1/progress?progress_pct=50
```

### 7.3 提交进度日报

```bash
POST /api/v1/progress-reports
Content-Type: application/json

{
  "project_id": 1,
  "report_type": "DAILY",
  "report_date": "2025-01-22",
  "tasks": [
    {
      "task_id": 1,
      "progress_pct": 50,
      "note": "已完成50%"
    }
  ]
}
```

### 7.4 获取甘特图数据

```bash
GET /api/v1/projects/1/gantt
```

### 7.5 获取进度看板

```bash
GET /api/v1/projects/1/progress-board
```

## 8. 后续优化建议

1. **任务依赖优化**:
   - 支持更多依赖类型（开始-开始、结束-结束等）
   - 支持依赖关系可视化
   - 支持关键路径计算

2. **进度预测优化**:
   - 基于历史数据预测任务完成时间
   - 支持进度偏差分析
   - 支持进度预警

3. **报表增强**:
   - 支持更多维度的统计分析
   - 支持报表导出（Excel/PDF）
   - 支持自定义报表

4. **集成优化**:
   - 与项目健康度集成
   - 与工时管理集成
   - 与物料管理集成（任务阻塞预警）

5. **自动化优化**:
   - 支持自动进度更新（基于工时填报）
   - 支持自动延期预警
   - 支持自动生成进度报告

## 9. 相关文件

- `app/api/v1/endpoints/progress.py` - 进度跟踪API实现
- `app/models/progress.py` - 进度跟踪模型定义（WbsTemplate, Task, TaskDependency等）
- `app/schemas/progress.py` - 进度跟踪Schema定义




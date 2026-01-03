# 项目进度管理系统 - API接口文档

## 概述

- **基础URL**: `http://your-domain/api/v1`
- **认证方式**: Bearer Token
- **响应格式**: JSON

---

## 工时管理 `/timesheets`

### 审核工时

```
POST /timesheets/approve
```

**请求体**

```json
{
  "timesheet_ids": [1, 2, 3],
  "status": "通过",
  "comment": "审核通过"
}
```

### 获取月度汇总

```
GET /timesheets/month-summary?user_id=1&year=2025&month=1
```

**响应示例**

```json
{
  "code": 200,
  "data": {
    "total_hours": 168,
    "standard_hours": 176,
    "overtime_hours": 12,
    "project_breakdown": [
      {"project_code": "PRJ-001", "hours": 120, "percentage": 71.4},
      {"project_code": "PRJ-002", "hours": 48, "percentage": 28.6}
    ]
  }
}
```

---

## 负荷管理 `/workload`

### 获取用户负荷

```
GET /workload/user/{user_id}
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | date | 否 | 开始日期 |
| end_date | date | 否 | 结束日期 |

**响应示例**

```json
{
  "code": 200,
  "data": {
    "user_id": 1,
    "user_name": "张工",
    "summary": {
      "total_assigned_hours": 180,
      "standard_hours": 176,
      "allocation_rate": 102.3
    },
    "by_project": [
      {"project_code": "PRJ-001", "assigned_hours": 120, "task_count": 5}
    ]
  }
}
```

### 获取团队负荷

```
GET /workload/team
```

**响应示例**

```json
{
  "code": 200,
  "data": [
    {
      "user_id": 1,
      "user_name": "张工",
      "dept_name": "机械组",
      "allocation_rate": 102,
      "task_count": 8,
      "overdue_count": 0
    }
  ]
}
```

### 获取负荷热力图

```
GET /workload/heatmap?weeks=4
```

### 获取可用资源

```
GET /workload/available?min_hours=20
```

---

## 预警管理 `/alerts`

### 获取预警列表

```
GET /alerts
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | int | 否 | 项目ID |
| alert_type | string | 否 | 预警类型 |
| alert_level | string | 否 | 预警级别(红/橙/黄) |
| status | string | 否 | 状态(待处理/处理中/已处理) |

**响应示例**

```json
{
  "code": 200,
  "data": {
    "total": 5,
    "list": [
      {
        "alert_id": 1,
        "alert_type": "任务逾期",
        "alert_level": "红",
        "alert_title": "任务\"电气设计\"已逾期3天",
        "project_code": "PRJ-001",
        "owner_name": "王工",
        "status": "待处理",
        "created_time": "2025-01-02 10:00"
      }
    ]
  }
}
```

### 预警类型说明

| 类型 | 说明 | 触发条件 |
|------|------|---------|
| 任务逾期 | 任务已超过计划完成日期 | 当前日期 > 计划结束日期 |
| 进度滞后 | 实际进度落后于计划进度 | SPI < 0.9 |
| 任务即将到期 | 任务即将到达截止日期 | 剩余天数 <= 3天 |
| 负荷过高 | 人员工作负荷超标 | 负荷率 > 110% |
| 里程碑风险 | 里程碑节点存在延期风险 | 前置任务延期 |

### 处理预警

```
PUT /alerts/{alert_id}/handle
```

**请求体**

```json
{
  "action": "处理中",
  "comment": "正在协调资源解决"
}
```

### 触发预警检查

```
POST /alerts/check
```

---

## 看板统计 `/dashboard`

### 获取工作台数据

```
GET /dashboard/overview
```

**响应示例**

```json
{
  "code": 200,
  "data": {
    "project_stats": {
      "total": 15,
      "active": 8,
      "warning": 2
    },
    "task_stats": {
      "my_tasks": 12,
      "in_progress": 5,
      "overdue": 1
    },
    "alert_stats": {
      "pending": 5,
      "critical": 1
    },
    "recent_updates": [
      {
        "type": "进度更新",
        "content": "张工更新了任务\"方案设计\"进度至80%",
        "time": "2025-01-02 16:30"
      }
    ]
  }
}
```

### 获取项目看板

```
GET /dashboard/project/{project_id}
```

---

## 数据模型

### Project 项目

| 字段 | 类型 | 说明 |
|------|------|------|
| project_id | int | 项目ID |
| project_code | string | 项目编号 |
| project_name | string | 项目名称 |
| customer_id | int | 客户ID |
| project_level | string | 项目级别(A/B/C/D) |
| pm_id | int | 项目经理ID |
| te_id | int | 技术负责人ID |
| status | string | 状态 |
| plan_start_date | date | 计划开始日期 |
| plan_end_date | date | 计划结束日期 |
| plan_manhours | float | 计划工时 |
| progress_rate | int | 进度百分比 |
| health_status | string | 健康状态(绿/黄/红) |

### Task 任务

| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | int | 任务ID |
| project_id | int | 所属项目 |
| parent_id | int | 父任务ID |
| wbs_code | string | WBS编码 |
| task_name | string | 任务名称 |
| phase | string | 所属阶段 |
| task_type | string | 类型(task/milestone) |
| owner_id | int | 负责人ID |
| status | string | 状态 |
| plan_start_date | date | 计划开始 |
| plan_end_date | date | 计划结束 |
| plan_manhours | float | 计划工时 |
| actual_manhours | float | 实际工时 |
| progress_rate | int | 进度百分比 |
| weight | int | 权重 |
| is_critical | bool | 是否关键路径 |

### Timesheet 工时

| 字段 | 类型 | 说明 |
|------|------|------|
| timesheet_id | int | 工时ID |
| user_id | int | 用户ID |
| project_id | int | 项目ID |
| task_id | int | 任务ID |
| work_date | date | 工作日期 |
| hours | float | 工时数 |
| work_content | string | 工作内容 |
| status | string | 状态 |
| overtime_type | string | 加班类型 |

### Alert 预警

| 字段 | 类型 | 说明 |
|------|------|------|
| alert_id | int | 预警ID |
| alert_type | string | 预警类型 |
| alert_level | string | 级别(红/橙/黄) |
| alert_title | string | 预警标题 |
| project_id | int | 关联项目 |
| task_id | int | 关联任务 |
| owner_id | int | 责任人 |
| status | string | 处理状态 |

---

## 状态码说明

### 项目状态

| 状态 | 说明 |
|------|------|
| 未启动 | 项目尚未开始 |
| 进行中 | 项目正在执行 |
| 已完成 | 项目已完成 |
| 已暂停 | 项目暂停中 |
| 已取消 | 项目已取消 |

### 任务状态

| 状态 | 说明 |
|------|------|
| 未开始 | 任务尚未开始 |
| 进行中 | 任务正在执行 |
| 已完成 | 任务已完成 |
| 阻塞 | 任务被阻塞 |

### 工时状态

| 状态 | 说明 |
|------|------|
| 草稿 | 未提交 |
| 待审核 | 已提交待审 |
| 已通过 | 审核通过 |
| 已驳回 | 审核驳回 |

---

## 认证说明

所有API请求需要在Header中携带Token:

```
Authorization: Bearer <your_token>
```

获取Token:

```
POST /auth/login
{
  "username": "admin",
  "password": "password"
}
```

---

## 在线文档

启动服务后访问:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

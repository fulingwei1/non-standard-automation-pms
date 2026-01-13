# 预警与异常管理 API 实现总结

## 概述

本文档总结了预警与异常管理功能的 API 实现情况，包括预警规则、预警记录、异常事件和项目健康度快照。

## 实现时间

2025-01-XX

## 1. 预警规则管理 API (`/api/v1/alert-rules`)

### 1.1 预警规则列表

**端点**: `GET /alert-rules`

**功能**:
- 获取预警规则列表（支持分页、搜索、筛选）

**请求参数**:
- `page`: 页码（查询参数，默认1）
- `page_size`: 每页数量（查询参数，默认20）
- `keyword`: 关键词搜索（查询参数，可选，搜索规则编码/名称）
- `rule_type`: 规则类型筛选（查询参数，可选）
- `target_type`: 监控对象类型筛选（查询参数，可选）
- `is_enabled`: 是否启用（查询参数，可选）

**响应**: `PaginatedResponse[AlertRuleResponse]`

### 1.2 预警规则详情

**端点**: `GET /alert-rules/{rule_id}`

**功能**:
- 获取预警规则的详细信息

**响应**: `AlertRuleResponse`

### 1.3 创建预警规则

**端点**: `POST /alert-rules`

**功能**:
- 创建新的预警规则

**请求体**: `AlertRuleCreate`

**响应**: `AlertRuleResponse`

**业务规则**:
- ✅ 检查规则编码唯一性
- ✅ 记录创建人

### 1.4 更新预警规则

**端点**: `PUT /alert-rules/{rule_id}`

**功能**:
- 更新预警规则信息

**请求体**: `AlertRuleUpdate`

**响应**: `AlertRuleResponse`

**业务规则**:
- ✅ 系统预置规则不允许修改

### 1.5 启用/禁用规则

**端点**: `PUT /alert-rules/{rule_id}/toggle`

**功能**:
- 启用或禁用预警规则

**响应**: `AlertRuleResponse`

### 1.6 预警规则模板

**端点**: `GET /alert-rule-templates`

**功能**:
- 获取预警规则模板列表

**响应**: `List[dict]`

## 2. 预警记录管理 API (`/api/v1/alerts`)

### 2.1 预警记录列表

**端点**: `GET /alerts`

**功能**:
- 获取预警记录列表（支持分页、筛选）

**请求参数**:
- `page`: 页码（查询参数，默认1）
- `page_size`: 每页数量（查询参数，默认20）
- `project_id`: 项目ID筛选（查询参数，可选）
- `rule_type`: 规则类型筛选（查询参数，可选）
- `alert_level`: 预警级别筛选（查询参数，可选）
- `status`: 状态筛选（查询参数，可选）
- `start_date`: 开始日期（查询参数，可选）
- `end_date`: 结束日期（查询参数，可选）

**响应**: `PaginatedResponse[AlertRecordListResponse]`

### 2.2 预警详情

**端点**: `GET /alerts/{alert_id}`

**功能**:
- 获取预警记录的详细信息

**响应**: `AlertRecordResponse`

### 2.3 确认预警

**端点**: `PUT /alerts/{alert_id}/acknowledge`

**功能**:
- 确认预警（PMC确认）
- 将状态从 `PENDING` 改为 `ACKNOWLEDGED`

**响应**: `AlertRecordResponse`

**业务规则**:
- ✅ 只有待处理状态的预警才能确认

### 2.4 处理预警

**端点**: `PUT /alerts/{alert_id}/resolve`

**功能**:
- 处理预警（标记为已解决）
- 将状态改为 `RESOLVED`

**请求体**: `AlertRecordHandle`（可选）

**响应**: `AlertRecordResponse`

**业务规则**:
- ✅ 已处理的预警不能重复处理

### 2.5 忽略预警

**端点**: `PUT /alerts/{alert_id}/ignore`

**功能**:
- 忽略预警
- 将状态改为 `IGNORED`

**响应**: `AlertRecordResponse`

**业务规则**:
- ✅ 已处理的预警不能忽略

### 2.6 预警通知列表

**端点**: `GET /alert-notifications`

**功能**:
- 获取预警通知列表（支持分页、筛选）

**请求参数**:
- `page`: 页码（查询参数，默认1）
- `page_size`: 每页数量（查询参数，默认20）
- `user_id`: 用户ID筛选（查询参数，可选，默认当前用户）
- `is_read`: 是否已读（查询参数，可选）

**响应**: `PaginatedResponse`

### 2.7 标记通知已读

**端点**: `PUT /alert-notifications/{notification_id}/read`

**功能**:
- 标记预警通知为已读

**响应**: `ResponseModel`

**业务规则**:
- ✅ 只能标记自己的通知

## 3. 异常事件管理 API (`/api/v1/exceptions`)

### 3.1 异常事件列表

**端点**: `GET /exceptions`

**功能**:
- 获取异常事件列表（支持分页、筛选）

**请求参数**:
- `page`: 页码（查询参数，默认1）
- `page_size`: 每页数量（查询参数，默认20）
- `keyword`: 关键词搜索（查询参数，可选，搜索异常编号/标题）
- `project_id`: 项目ID筛选（查询参数，可选）
- `event_type`: 异常类型筛选（查询参数，可选）
- `severity`: 严重程度筛选（查询参数，可选）
- `status`: 状态筛选（查询参数，可选）
- `responsible_user_id`: 责任人ID筛选（查询参数，可选）

**响应**: `PaginatedResponse`

**响应数据**:
```json
{
  "items": [
    {
      "id": 1,
      "event_no": "EXC-250122-001",
      "source_type": "ALERT",
      "project_id": 1,
      "project_name": "项目1",
      "event_type": "SCHEDULE",
      "severity": "CRITICAL",
      "event_title": "项目进度严重延迟",
      "status": "OPEN",
      "discovered_at": "2025-01-22T10:00:00",
      "schedule_impact": 5,
      "cost_impact": 10000.0,
      "is_overdue": false
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

### 3.2 创建异常事件

**端点**: `POST /exceptions`

**功能**:
- 创建新的异常事件

**请求体**: `ExceptionEventCreate`

**请求参数**:
- `source_type`: 来源类型（ALERT/MANUAL/ISSUE/OTHER）
- `source_id`: 来源ID（可选）
- `alert_id`: 关联预警ID（可选）
- `project_id`: 项目ID（可选）
- `machine_id`: 设备ID（可选）
- `event_type`: 异常类型（SCHEDULE/QUALITY/COST/RESOURCE/SAFETY/OTHER）
- `severity`: 严重程度（MINOR/MAJOR/CRITICAL/BLOCKER）
- `event_title`: 异常标题
- `event_description`: 异常描述
- `discovery_location`: 发现地点（可选）
- `impact_scope`: 影响范围（可选）
- `schedule_impact`: 工期影响（天，可选）
- `cost_impact`: 成本影响（可选）
- `responsible_dept`: 责任部门（可选）
- `responsible_user_id`: 责任人ID（可选）
- `due_date`: 要求完成日期（可选）

**响应**: `ExceptionEventResponse`

**业务规则**:
- ✅ 自动生成异常编号（EXC-yymmdd-xxx）
- ✅ 自动设置发现时间和发现人
- ✅ 验证项目和设备存在性

### 3.3 异常事件详情

**端点**: `GET /exceptions/{event_id}`

**功能**:
- 获取异常事件的详细信息
- 包含处理记录列表

**响应**: `ExceptionEventResponse`

**响应数据**:
```json
{
  "id": 1,
  "event_no": "EXC-250122-001",
  "source_type": "ALERT",
  "project_id": 1,
  "project_name": "项目1",
  "event_type": "SCHEDULE",
  "severity": "CRITICAL",
  "event_title": "项目进度严重延迟",
  "event_description": "详细描述...",
  "status": "OPEN",
  "discovered_at": "2025-01-22T10:00:00",
  "discovered_by_name": "张三",
  "schedule_impact": 5,
  "cost_impact": 10000.0,
  "root_cause": "根本原因分析...",
  "solution": "解决方案...",
  "actions": [
    {
      "id": 1,
      "action_type": "ANALYSIS",
      "action_content": "已分析根本原因",
      "action_user_name": "李四",
      "created_at": "2025-01-22T11:00:00"
    }
  ]
}
```

### 3.4 更新异常状态

**端点**: `PUT /exceptions/{event_id}/status`

**功能**:
- 更新异常事件的状态

**请求参数**:
- `status`: 新状态（查询参数，OPEN/ANALYZING/RESOLVING/RESOLVED/CLOSED/DEFERRED）

**响应**: `ExceptionEventResponse`

**业务规则**:
- ✅ 如果状态为RESOLVED，自动记录解决时间和解决人

### 3.5 添加处理记录

**端点**: `POST /exceptions/{event_id}/actions`

**功能**:
- 添加异常事件的处理记录

**请求参数**:
- `action_type`: 操作类型（查询参数）
- `action_content`: 操作内容（查询参数）

**响应**: `ResponseModel`

**响应数据**:
```json
{
  "code": 200,
  "message": "处理记录已添加",
  "data": {
    "action_id": 1,
    "event_id": 1
  }
}
```

### 3.6 异常升级

**端点**: `POST /exceptions/{event_id}/escalate`

**功能**:
- 异常升级（提升严重程度或更换责任人）

**请求参数**:
- `escalate_to_user_id`: 升级到用户ID（查询参数，可选）
- `escalate_to_dept`: 升级到部门（查询参数，可选）
- `escalation_reason`: 升级原因（查询参数，可选）

**响应**: `ExceptionEventResponse`

**业务规则**:
- ✅ 创建升级记录
- ✅ 更新责任人
- ✅ 自动提升严重程度（MINOR→MAJOR→CRITICAL）

### 3.7 从问题创建异常

**端点**: `POST /exceptions/from-issue`

**功能**:
- 从问题创建异常事件

**请求参数**:
- `issue_id`: 问题ID（查询参数）
- `event_type`: 异常类型（查询参数）
- `severity`: 严重程度（查询参数）

**响应**: `ExceptionEventResponse`

**业务规则**:
- ✅ 自动从问题复制相关信息
- ✅ 设置来源类型为ISSUE

## 4. 项目健康度快照 API

### 4.1 健康度趋势查询

**端点**: `GET /projects/{project_id}/health-history`

**功能**:
- 查询项目健康度历史趋势

**请求参数**:
- `project_id`: 项目ID（路径参数）
- `start_date`: 开始日期（查询参数，可选）
- `end_date`: 结束日期（查询参数，可选）

**响应**: `List[dict]`

**响应数据**:
```json
[
  {
    "id": 1,
    "snapshot_date": "2025-01-22",
    "overall_health": "H2",
    "schedule_health": "H2",
    "cost_health": "H1",
    "quality_health": "H1",
    "resource_health": "H2",
    "health_score": 75,
    "open_alerts": 5,
    "open_exceptions": 2,
    "blocking_issues": 1,
    "schedule_variance": -5.0,
    "cost_variance": 2.0,
    "budget_used_pct": 60.0,
    "milestone_on_track": 8,
    "milestone_delayed": 2,
    "top_risks": [
      {
        "risk": "物料短缺",
        "level": "HIGH"
      }
    ]
  }
]
```

### 4.2 预警统计分析

**端点**: `GET /alerts/statistics`

**功能**:
- 获取预警统计分析数据

**请求参数**:
- `project_id`: 项目ID筛选（查询参数，可选）
- `start_date`: 开始日期（查询参数，可选）
- `end_date`: 结束日期（查询参数，可选）

**响应**: `dict`

**响应数据**:
```json
{
  "total_alerts": 100,
  "by_level": {
    "LOW": 20,
    "WARNING": 40,
    "HIGH": 30,
    "CRITICAL": 10
  },
  "by_type": {
    "SCHEDULE": 30,
    "COST": 25,
    "QUALITY": 20,
    "RESOURCE": 15,
    "OTHER": 10
  },
  "by_status": {
    "OPEN": 40,
    "ACKNOWLEDGED": 30,
    "RESOLVED": 30
  },
  "by_project": {
    "项目1": 50,
    "项目2": 30,
    "项目3": 20
  },
  "by_date": {
    "2025-01-20": 10,
    "2025-01-21": 15,
    "2025-01-22": 20
  },
  "summary": {
    "open_count": 40,
    "acknowledged_count": 30,
    "resolved_count": 30,
    "critical_count": 10,
    "high_count": 30
  }
}
```

## 5. 实现特性

### 5.1 预警规则管理

- ✅ 支持自定义预警规则
- ✅ 系统预置规则保护
- ✅ 规则启用/禁用控制
- ✅ 规则模板支持

### 5.2 预警记录管理

- ✅ 预警状态流转（PENDING→ACKNOWLEDGED→RESOLVED）
- ✅ 预警通知机制
- ✅ 多维度筛选和统计

### 5.3 异常事件管理

- ✅ 异常事件全生命周期管理
- ✅ 处理记录跟踪
- ✅ 异常升级机制
- ✅ 从问题/预警创建异常

### 5.4 项目健康度快照

- ✅ 健康度历史趋势查询
- ✅ 多维度健康指标
- ✅ 预警统计分析

## 6. 数据模型

### 6.1 AlertRule

- `rule_code`: 规则编码
- `rule_name`: 规则名称
- `rule_type`: 规则类型
- `target_type`: 监控对象类型
- `condition_config`: 条件配置（JSON）
- `is_enabled`: 是否启用
- `is_system`: 是否系统预置

### 6.2 AlertRecord

- `alert_no`: 预警编号
- `project_id`: 项目ID
- `rule_id`: 规则ID
- `rule_type`: 规则类型
- `alert_level`: 预警级别
- `status`: 状态
- `alert_content`: 预警内容
- `handler_id`: 处理人ID

### 6.3 ExceptionEvent

- `event_no`: 异常编号
- `source_type`: 来源类型
- `source_id`: 来源ID
- `alert_id`: 关联预警ID
- `project_id`: 项目ID
- `event_type`: 异常类型
- `severity`: 严重程度
- `status`: 状态
- `schedule_impact`: 工期影响
- `cost_impact`: 成本影响
- `root_cause`: 根本原因
- `solution`: 解决方案

### 6.4 ProjectHealthSnapshot

- `project_id`: 项目ID
- `snapshot_date`: 快照日期
- `overall_health`: 综合健康度
- `health_score`: 健康评分
- `open_alerts`: 未处理预警数
- `open_exceptions`: 未关闭异常数
- `schedule_variance`: 进度偏差
- `cost_variance`: 成本偏差

## 7. 使用示例

### 7.1 创建预警规则

```bash
POST /api/v1/alert-rules
Content-Type: application/json

{
  "rule_code": "RULE-001",
  "rule_name": "项目进度延迟预警",
  "rule_type": "SCHEDULE",
  "target_type": "PROJECT",
  "condition_config": {
    "progress_threshold": 80,
    "delay_days": 3
  }
}
```

### 7.2 确认预警

```bash
PUT /api/v1/alerts/1/acknowledge
```

### 7.3 创建异常事件

```bash
POST /api/v1/exceptions
Content-Type: application/json

{
  "source_type": "ALERT",
  "alert_id": 1,
  "project_id": 1,
  "event_type": "SCHEDULE",
  "severity": "CRITICAL",
  "event_title": "项目进度严重延迟",
  "event_description": "详细描述...",
  "schedule_impact": 5,
  "cost_impact": 10000.0
}
```

### 7.4 异常升级

```bash
POST /api/v1/exceptions/1/escalate?escalate_to_user_id=2&escalation_reason=需要上级处理
```

### 7.5 获取健康度趋势

```bash
GET /api/v1/projects/1/health-history?start_date=2025-01-01&end_date=2025-01-31
```

### 7.6 预警统计分析

```bash
GET /api/v1/alerts/statistics?project_id=1&start_date=2025-01-01&end_date=2025-01-31
```

## 8. 后续优化建议

1. **预警规则优化**:
   - 支持更复杂的条件配置
   - 支持规则优先级
   - 支持规则组合

2. **异常处理优化**:
   - 支持异常处理工作流
   - 支持异常处理模板
   - 支持异常处理提醒

3. **健康度快照优化**:
   - 自动生成健康度快照（定时任务）
   - 支持健康度预测
   - 支持健康度对比分析

4. **统计分析增强**:
   - 支持更多维度的统计分析
   - 支持图表数据导出
   - 支持自定义报表

5. **集成优化**:
   - 与项目管理系统集成
   - 与问题管理系统集成
   - 与通知系统集成

## 9. 相关文件

- `app/api/v1/endpoints/alerts.py` - 预警与异常管理API实现
- `app/models/alert.py` - 预警与异常模型定义
- `app/schemas/alert.py` - 预警与异常Schema定义




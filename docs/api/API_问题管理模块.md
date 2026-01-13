# 问题管理模块 API 文档

> **文档版本**: v1.0  
> **最后更新**: 2026-01-15  
> **模块**: 问题管理中心

---

## 一、概述

问题管理模块提供完整的问题生命周期管理功能，包括问题创建、状态流转、跟进管理、统计分析等。

**基础路径**: `/api/v1/issues`

---

## 二、问题 CRUD 操作

### 2.1 创建问题

**端点**: `POST /api/v1/issues`

**请求体**:
```json
{
  "category": "PROJECT",
  "issue_type": "DEFECT",
  "severity": "MAJOR",
  "priority": "HIGH",
  "title": "问题标题",
  "description": "问题描述",
  "project_id": 1,
  "machine_id": 1,
  "task_id": 1,
  "assignee_id": 2,
  "due_date": "2026-01-20",
  "is_blocking": false,
  "impact_scope": "影响范围",
  "impact_level": "HIGH",
  "root_cause": "DESIGN_ERROR",
  "tags": ["标签1", "标签2"]
}
```

**响应**: `201 Created`
```json
{
  "id": 1,
  "issue_no": "IS20260115001",
  "title": "问题标题",
  "status": "OPEN",
  ...
}
```

**说明**:
- 自动生成问题编号（格式：ISyymmddxxx）
- 如果 `is_blocking=true`，自动创建预警记录
- 自动记录提出人和提出时间

---

### 2.2 获取问题列表

**端点**: `GET /api/v1/issues`

**查询参数**:
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20，最大100）
- `status`: 状态筛选（OPEN/PROCESSING/RESOLVED/CLOSED等）
- `severity`: 严重程度筛选（CRITICAL/MAJOR/MINOR）
- `priority`: 优先级筛选（URGENT/HIGH/MEDIUM/LOW）
- `category`: 分类筛选（PROJECT/TASK/ACCEPTANCE）
- `keyword`: 关键词搜索（标题、描述）
- `project_id`: 项目ID筛选
- `assignee_id`: 处理人ID筛选
- `is_blocking`: 是否阻塞筛选

**响应**: `200 OK`
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

---

### 2.3 获取问题详情

**端点**: `GET /api/v1/issues/{issue_id}`

**响应**: `200 OK`
```json
{
  "id": 1,
  "issue_no": "IS20260115001",
  "title": "问题标题",
  "description": "问题描述",
  "status": "OPEN",
  "severity": "MAJOR",
  "priority": "HIGH",
  "project_id": 1,
  "project_name": "项目名称",
  "assignee_id": 2,
  "assignee_name": "处理人",
  "is_blocking": false,
  "follow_up_count": 3,
  "created_at": "2026-01-15T10:00:00",
  ...
}
```

---

### 2.4 更新问题

**端点**: `PUT /api/v1/issues/{issue_id}`

**请求体**: 支持部分更新
```json
{
  "title": "更新后的标题",
  "priority": "URGENT",
  "is_blocking": true
}
```

**响应**: `200 OK`

**说明**:
- 如果 `is_blocking` 从 `false` 变为 `true`，自动创建预警
- 如果 `is_blocking` 从 `true` 变为 `false`，自动关闭相关预警

---

### 2.5 删除问题

**端点**: `DELETE /api/v1/issues/{issue_id}`

**响应**: `200 OK` 或 `204 No Content`

**说明**: 软删除，仅管理员可操作

---

## 三、问题操作

### 3.1 分配问题

**端点**: `POST /api/v1/issues/{issue_id}/assign`

**请求体**:
```json
{
  "assignee_id": 2,
  "due_date": "2026-01-20",
  "comment": "分配给处理人"
}
```

**响应**: `200 OK`

**说明**:
- 自动创建跟进记录
- 发送通知给被分配人

---

### 3.2 解决问题

**端点**: `POST /api/v1/issues/{issue_id}/resolve`

**请求体**:
```json
{
  "solution": "解决方案描述",
  "comment": "解决说明"
}
```

**响应**: `200 OK`

**说明**:
- 状态自动变更为 `RESOLVED`
- 如果是阻塞问题，自动关闭相关预警
- 发送通知给提出人

---

### 3.3 验证问题

**端点**: `POST /api/v1/issues/{issue_id}/verify`

**请求体**:
```json
{
  "verified_result": "PASS",
  "comment": "验证通过"
}
```

**响应**: `200 OK`

**说明**:
- 验证通过（PASS）时自动关闭问题
- 验证不通过（FAIL）时状态变回 `OPEN`

---

### 3.4 关闭问题

**端点**: `POST /api/v1/issues/{issue_id}/close`

**请求体**:
```json
{
  "comment": "关闭说明"
}
```

**响应**: `200 OK`

---

### 3.5 取消问题

**端点**: `POST /api/v1/issues/{issue_id}/cancel`

**请求体**:
```json
{
  "comment": "取消原因"
}
```

**响应**: `200 OK`

---

### 3.6 变更状态

**端点**: `POST /api/v1/issues/{issue_id}/status`

**请求体**:
```json
{
  "status": "PROCESSING",
  "comment": "状态变更说明"
}
```

**响应**: `200 OK`

---

## 四、跟进管理

### 4.1 获取跟进记录

**端点**: `GET /api/v1/issues/{issue_id}/follow-ups`

**响应**: `200 OK`
```json
[
  {
    "id": 1,
    "follow_up_type": "COMMENT",
    "content": "跟进内容",
    "operator_name": "操作人",
    "created_at": "2026-01-15T10:00:00"
  }
]
```

---

### 4.2 创建跟进记录

**端点**: `POST /api/v1/issues/{issue_id}/follow-ups`

**请求体**:
```json
{
  "follow_up_type": "COMMENT",
  "content": "跟进内容"
}
```

**响应**: `201 Created`

---

## 五、批量操作

### 5.1 批量分配

**端点**: `POST /api/v1/issues/batch-assign`

**请求体**:
```json
{
  "issue_ids": [1, 2, 3],
  "assignee_id": 2,
  "due_date": "2026-01-20"
}
```

**响应**: `200 OK`

---

### 5.2 批量状态变更

**端点**: `POST /api/v1/issues/batch-status`

**请求体**:
```json
{
  "issue_ids": [1, 2, 3],
  "new_status": "PROCESSING"
}
```

**响应**: `200 OK`

---

### 5.3 批量关闭

**端点**: `POST /api/v1/issues/batch-close`

**请求体**:
```json
{
  "issue_ids": [1, 2, 3]
}
```

**响应**: `200 OK`

---

## 六、数据导入导出

### 6.1 导出问题

**端点**: `GET /api/v1/issues/export`

**查询参数**: 支持所有列表筛选参数

**响应**: `200 OK` (Excel文件)

**文件格式**: `.xlsx`

---

### 6.2 导入问题

**端点**: `POST /api/v1/issues/import`

**请求**: `multipart/form-data`
- `file`: Excel文件

**响应**: `200 OK`

---

## 七、统计分析

### 7.1 获取总体统计

**端点**: `GET /api/v1/issues/statistics/overview`

**响应**: `200 OK`
```json
{
  "total": 100,
  "open": 20,
  "processing": 15,
  "resolved": 50,
  "closed": 10,
  "blocking": 5,
  "overdue": 3
}
```

---

### 7.2 获取趋势数据

**端点**: `GET /api/v1/issues/statistics/trend`

**查询参数**:
- `group_by`: 分组方式（day/week/month）
- `start_date`: 开始日期
- `end_date`: 结束日期

**响应**: `200 OK`
```json
{
  "trend": [
    {
      "date": "2026-01-15",
      "created": 5,
      "resolved": 3,
      "closed": 2
    }
  ]
}
```

---

### 7.3 获取工程师统计

**端点**: `GET /api/v1/issues/statistics/engineer`

**查询参数**:
- `start_date`: 开始日期
- `end_date`: 结束日期

**响应**: `200 OK`
```json
{
  "engineers": [
    {
      "engineer_id": 1,
      "engineer_name": "工程师",
      "total_issues": 10,
      "resolved_issues": 8,
      "avg_resolve_time": 24.5
    }
  ]
}
```

---

### 7.4 获取原因分析

**端点**: `GET /api/v1/issues/statistics/cause-analysis`

**查询参数**:
- `start_date`: 开始日期
- `end_date`: 结束日期
- `top_n`: Top N（默认10）

**响应**: `200 OK`
```json
{
  "total_issues": 100,
  "top_causes": [
    {
      "cause": "DESIGN_ERROR",
      "count": 30,
      "percentage": 30.0,
      "issue_ids": [1, 2, 3]
    }
  ]
}
```

---

### 7.5 获取统计快照列表

**端点**: `GET /api/v1/issues/statistics/snapshots`

**查询参数**:
- `page`: 页码
- `page_size`: 每页数量
- `start_date`: 开始日期
- `end_date`: 结束日期

**响应**: `200 OK`
```json
{
  "items": [...],
  "total": 30,
  "page": 1,
  "page_size": 20,
  "pages": 2
}
```

---

### 7.6 获取统计快照详情

**端点**: `GET /api/v1/issues/statistics/snapshots/{snapshot_id}`

**响应**: `200 OK`
```json
{
  "id": 1,
  "snapshot_date": "2026-01-15",
  "total_issues": 100,
  "open_issues": 20,
  "status_distribution": {...},
  "severity_distribution": {...},
  ...
}
```

---

### 7.7 获取看板数据

**端点**: `GET /api/v1/issues/board`

**查询参数**: 支持筛选参数

**响应**: `200 OK`
```json
{
  "columns": [
    {
      "status": "OPEN",
      "issues": [...]
    }
  ]
}
```

---

## 八、问题模板管理

### 8.1 获取模板列表

**端点**: `GET /api/v1/issue-templates`

**查询参数**:
- `page`: 页码
- `page_size`: 每页数量
- `keyword`: 关键词搜索
- `category`: 分类筛选
- `is_active`: 状态筛选

**响应**: `200 OK`

---

### 8.2 获取模板详情

**端点**: `GET /api/v1/issue-templates/{template_id}`

**响应**: `200 OK`

---

### 8.3 创建模板

**端点**: `POST /api/v1/issue-templates`

**请求体**:
```json
{
  "template_name": "模板名称",
  "template_code": "TEMPLATE_001",
  "category": "PROJECT",
  "issue_type": "DEFECT",
  "title_template": "{project_name} - 问题",
  "description_template": "问题描述模板",
  "default_severity": "MINOR",
  "default_priority": "MEDIUM"
}
```

**响应**: `201 Created`

---

### 8.4 更新模板

**端点**: `PUT /api/v1/issue-templates/{template_id}`

**请求体**: 支持部分更新

**响应**: `200 OK`

---

### 8.5 删除模板

**端点**: `DELETE /api/v1/issue-templates/{template_id}`

**响应**: `200 OK`

**说明**: 软删除（设置is_active=False）

---

### 8.6 从模板创建问题

**端点**: `POST /api/v1/issue-templates/{template_id}/create-issue`

**请求体**:
```json
{
  "project_id": 1,
  "machine_id": 1,
  "assignee_id": 2,
  "due_date": "2026-01-20"
}
```

**响应**: `201 Created`

**说明**:
- 自动填充模板默认值
- 支持模板变量替换
- 自动更新模板使用统计

---

## 九、错误码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

---

## 十、使用示例

### 10.1 创建阻塞问题

```python
import requests

headers = {"Authorization": "Bearer <token>"}
data = {
    "category": "PROJECT",
    "issue_type": "DEFECT",
    "severity": "CRITICAL",
    "priority": "URGENT",
    "title": "温度控制问题",
    "description": "温度波动超过规格要求",
    "is_blocking": True,
    "project_id": 1
}

response = requests.post(
    "http://localhost:8000/api/v1/issues",
    json=data,
    headers=headers
)
```

### 10.2 批量处理问题

```python
# 批量分配
batch_data = {
    "issue_ids": [1, 2, 3],
    "assignee_id": 2,
    "due_date": "2026-01-20"
}

response = requests.post(
    "http://localhost:8000/api/v1/issues/batch-assign",
    json=batch_data,
    headers=headers
)
```

---

**文档版本**: v1.0  
**最后更新**: 2026-01-15

# 问题管理模块 API 实现总结

## 概述

本文档总结了问题管理中心模块的 API 实现情况。问题管理模块统一管理项目问题、任务问题、验收问题等。

## 实现时间

2025-01-XX

## 1. 核心功能 API（已实现）

### 1.1 问题列表

**端点**: `GET /api/v1/issues`

**功能**:
- 获取问题列表（支持分页、多维度筛选）

**请求参数**:
- `page`: 页码（查询参数，默认1）
- `page_size`: 每页数量（查询参数，默认20）
- `category`: 问题分类（查询参数，可选）
- `project_id`: 项目ID（查询参数，可选）
- `machine_id`: 机台ID（查询参数，可选）
- `task_id`: 任务ID（查询参数，可选）
- `issue_type`: 问题类型（查询参数，可选）
- `severity`: 严重程度（查询参数，可选）
- `priority`: 优先级（查询参数，可选）
- `status`: 状态（查询参数，可选）
- `assignee_id`: 处理人ID（查询参数，可选）
- `reporter_id`: 提出人ID（查询参数，可选）
- `is_blocking`: 是否阻塞（查询参数，可选）
- `is_overdue`: 是否逾期（查询参数，可选）
- `keyword`: 关键词搜索（查询参数，可选）

**响应**: `IssueListResponse`

### 1.2 问题详情

**端点**: `GET /api/v1/issues/{issue_id}`

**功能**:
- 获取问题的详细信息

**响应**: `IssueResponse`

### 1.3 创建问题

**端点**: `POST /api/v1/issues`

**功能**:
- 创建新的问题
- 自动生成问题编号（ISyymmddxxx）

**请求体**: `IssueCreate`

**响应**: `IssueResponse`

### 1.4 更新问题

**端点**: `PUT /api/v1/issues/{issue_id}`

**功能**:
- 更新问题信息

**请求体**: `IssueUpdate`

**响应**: `IssueResponse`

### 1.5 分配问题

**端点**: `POST /api/v1/issues/{issue_id}/assign`

**功能**:
- 分配问题给处理人

**请求体**: `IssueAssignRequest`

**响应**: `IssueResponse`

### 1.6 解决问题

**端点**: `POST /api/v1/issues/{issue_id}/resolve`

**功能**:
- 标记问题为已解决
- 填写解决方案

**请求体**: `IssueResolveRequest`

**响应**: `IssueResponse`

### 1.7 验证问题

**端点**: `POST /api/v1/issues/{issue_id}/verify`

**功能**:
- 验证问题解决结果
- 验证通过后自动关闭

**请求体**: `IssueVerifyRequest`

**响应**: `IssueResponse`

### 1.8 变更问题状态

**端点**: `POST /api/v1/issues/{issue_id}/status`

**功能**:
- 手动变更问题状态

**请求体**: `IssueStatusChangeRequest`

**响应**: `IssueResponse`

### 1.9 获取跟进记录

**端点**: `GET /api/v1/issues/{issue_id}/follow-ups`

**功能**:
- 获取问题的所有跟进记录

**响应**: `List[IssueFollowUpResponse]`

### 1.10 创建跟进记录

**端点**: `POST /api/v1/issues/{issue_id}/follow-ups`

**功能**:
- 添加问题跟进记录

**请求体**: `IssueFollowUpCreate`

**响应**: `IssueFollowUpResponse`

### 1.11 问题统计

**端点**: `GET /api/v1/issues/statistics/overview`

**功能**:
- 获取问题统计信息（多维度统计）

**请求参数**:
- `project_id`: 项目ID筛选（查询参数，可选）

**响应**: `IssueStatistics`

**响应数据**:
```json
{
  "total": 100,
  "open": 30,
  "processing": 20,
  "resolved": 30,
  "closed": 20,
  "overdue": 10,
  "blocking": 5,
  "by_severity": {
    "CRITICAL": 10,
    "MAJOR": 30,
    "MINOR": 60
  },
  "by_category": {
    "PROJECT": 50,
    "TASK": 30,
    "ACCEPTANCE": 20
  },
  "by_type": {
    "DEFECT": 40,
    "RISK": 30,
    "BLOCKER": 20,
    "OTHER": 10
  }
}
```

## 2. 扩展功能 API（已实现）

### 2.1 关闭问题

**端点**: `POST /api/v1/issues/{issue_id}/close`

**功能**:
- 直接关闭问题（无需验证）

**响应**: `IssueResponse`

**业务规则**:
- ✅ 自动记录跟进记录
- ✅ 状态更新为CLOSED

### 2.2 取消问题

**端点**: `POST /api/v1/issues/{issue_id}/cancel`

**功能**:
- 取消/撤销问题

**请求参数**:
- `cancel_reason`: 取消原因（查询参数，可选）

**响应**: `IssueResponse`

**业务规则**:
- ✅ 已关闭或已取消的问题不能再次取消
- ✅ 自动记录跟进记录

### 2.3 关联问题列表

**端点**: `GET /api/v1/issues/{issue_id}/related`

**功能**:
- 获取关联的父子问题列表

**响应**: `List[IssueResponse]`

**返回内容**:
- 父问题（如果存在）
- 所有子问题

### 2.4 创建关联问题

**端点**: `POST /api/v1/issues/{issue_id}/related`

**功能**:
- 创建子问题或关联问题

**请求体**: `IssueCreate`

**响应**: `IssueResponse`

**业务规则**:
- ✅ 自动关联到父问题
- ✅ 自动继承项目/机台/任务信息（如果未指定）

### 2.5 项目问题列表

**端点**: `GET /api/v1/issues/projects/{project_id}/issues`

**功能**:
- 获取项目下的所有问题

**请求参数**:
- `page`: 页码（查询参数，默认1）
- `page_size`: 每页数量（查询参数，默认20）
- `status`: 状态筛选（查询参数，可选）

**响应**: `IssueListResponse`

### 2.6 机台问题列表

**端点**: `GET /api/v1/issues/machines/{machine_id}/issues`

**功能**:
- 获取机台下的所有问题

**请求参数**:
- `page`: 页码（查询参数，默认1）
- `page_size`: 每页数量（查询参数，默认20）
- `status`: 状态筛选（查询参数，可选）

**响应**: `IssueListResponse`

## 3. 待实现功能（P1/P2优先级）

### 3.1 删除问题（软删除）

**端点**: `DELETE /api/v1/issues/{issue_id}`

**功能**:
- 软删除问题（仅管理员）

**状态**: ❌ 待实现

### 3.2 任务问题列表

**端点**: `GET /api/v1/issues/tasks/{task_id}/issues`

**功能**:
- 获取任务下的所有问题

**状态**: ❌ 待实现

### 3.3 验收问题列表

**端点**: `GET /api/v1/issues/acceptance-orders/{order_id}/issues`

**功能**:
- 获取验收单下的所有问题

**状态**: ❌ 待实现

### 3.4 批量操作

**端点**:
- `POST /api/v1/issues/batch-assign` - 批量分配问题
- `POST /api/v1/issues/batch-status` - 批量更新状态
- `POST /api/v1/issues/batch-close` - 批量关闭问题

**功能**:
- 批量处理问题

**状态**: ❌ 待实现

### 3.5 导入导出

**端点**:
- `GET /api/v1/issues/export` - 导出Excel/CSV
- `POST /api/v1/issues/import` - 批量导入问题

**功能**:
- 问题数据导入导出

**状态**: ❌ 待实现

### 3.6 看板数据

**端点**: `GET /api/v1/issues/board`

**功能**:
- 获取问题看板视图数据（按状态分组）

**状态**: ❌ 待实现

### 3.7 趋势分析

**端点**: `GET /api/v1/issues/statistics/trend`

**功能**:
- 获取问题时间序列趋势分析

**状态**: ❌ 待实现

## 4. 实现特性

### 4.1 问题生命周期

- ✅ 状态流转：OPEN → PROCESSING → RESOLVED → VERIFIED → CLOSED
- ✅ 支持直接关闭（无需验证）
- ✅ 支持取消问题
- ✅ 自动记录状态变更历史

### 4.2 问题关联

- ✅ 支持关联项目、机台、任务、验收单
- ✅ 支持父子问题关联
- ✅ 自动继承关联信息

### 4.3 跟进记录

- ✅ 自动记录状态变更
- ✅ 支持手动添加跟进记录
- ✅ 跟进记录类型：COMMENT/STATUS_CHANGE/ASSIGNMENT/SOLUTION/VERIFICATION

### 4.4 多维度筛选

- ✅ 支持按分类、类型、严重程度、优先级筛选
- ✅ 支持按项目、机台、任务筛选
- ✅ 支持按处理人、提出人筛选
- ✅ 支持关键词搜索
- ✅ 支持逾期问题筛选

## 5. 数据模型

### 5.1 Issue

- `issue_no`: 问题编号（自动生成）
- `category`: 问题分类（PROJECT/TASK/ACCEPTANCE等）
- `project_id`: 关联项目ID
- `machine_id`: 关联机台ID
- `task_id`: 关联任务ID
- `acceptance_order_id`: 关联验收单ID
- `related_issue_id`: 关联问题ID（父子问题）
- `issue_type`: 问题类型（DEFECT/DEVIATION/RISK/BLOCKER等）
- `severity`: 严重程度（CRITICAL/MAJOR/MINOR）
- `priority`: 优先级（LOW/MEDIUM/HIGH/URGENT）
- `status`: 状态（OPEN/PROCESSING/RESOLVED/VERIFIED/CLOSED/CANCELLED）
- `is_blocking`: 是否阻塞
- `follow_up_count`: 跟进次数
- `last_follow_up_at`: 最后跟进时间

### 5.2 IssueFollowUpRecord

- `issue_id`: 问题ID
- `follow_up_type`: 跟进类型
- `content`: 跟进内容
- `operator_id`: 操作人ID
- `old_status`: 原状态
- `new_status`: 新状态

## 6. 使用示例

### 6.1 创建问题

```bash
POST /api/v1/issues
Content-Type: application/json

{
  "category": "PROJECT",
  "project_id": 1,
  "issue_type": "DEFECT",
  "severity": "MAJOR",
  "priority": "HIGH",
  "title": "项目进度延迟",
  "description": "详细描述...",
  "is_blocking": true
}
```

### 6.2 分配问题

```bash
POST /api/v1/issues/1/assign
Content-Type: application/json

{
  "assignee_id": 2,
  "due_date": "2025-01-25"
}
```

### 6.3 解决问题

```bash
POST /api/v1/issues/1/resolve
Content-Type: application/json

{
  "solution": "已调整计划，增加人员投入",
  "resolved_note": "问题已解决"
}
```

### 6.4 验证问题

```bash
POST /api/v1/issues/1/verify
Content-Type: application/json

{
  "verified_result": "VERIFIED",
  "comment": "验证通过"
}
```

### 6.5 创建关联问题

```bash
POST /api/v1/issues/1/related
Content-Type: application/json

{
  "category": "PROJECT",
  "issue_type": "RISK",
  "severity": "MINOR",
  "title": "子问题标题",
  "description": "子问题描述"
}
```

## 7. 完成度评估

### 核心功能（P0）：✅ 100% 完成

- ✅ 问题列表（分页+多维度筛选）
- ✅ 问题详情
- ✅ 创建问题
- ✅ 更新问题
- ✅ 分配问题
- ✅ 解决问题
- ✅ 验证问题
- ✅ 变更问题状态
- ✅ 获取跟进记录
- ✅ 创建跟进记录
- ✅ 问题统计
- ✅ 关闭问题
- ✅ 取消问题
- ✅ 关联问题管理
- ✅ 项目/机台问题列表

### 扩展功能（P1）：⚠️ 0% 完成

- ❌ 删除问题（软删除）
- ❌ 任务问题列表
- ❌ 验收问题列表
- ❌ 批量操作
- ❌ 导入导出
- ❌ 看板数据

### 高级功能（P2）：❌ 0% 完成

- ❌ 趋势分析

## 8. 总结

问题管理模块的**核心功能（P0）已100%完成**，包括：

- ✅ 完整的CRUD操作
- ✅ 问题生命周期管理（分配→解决→验证→关闭）
- ✅ 跟进记录管理
- ✅ 关联问题管理
- ✅ 多维度筛选和统计

**扩展功能（P1/P2）**待后续补充，包括批量操作、导入导出、看板视图等。

## 9. 相关文件

- `app/api/v1/endpoints/issues.py` - 问题管理API实现
- `app/models/issue.py` - Issue模型定义
- `app/schemas/issue.py` - 问题相关Schema定义




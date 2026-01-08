# 验收管理模块问题管理 API 完善说明

## 修改日期
2025-01-15

## 修改内容

### 1. 新增 Schema 定义 ✅

在 `app/schemas/acceptance.py` 中添加了以下 Schema：

1. **`AcceptanceIssueAssign`** - 指派问题请求
   - `assigned_to`: 处理负责人ID
   - `due_date`: 要求完成日期（可选）
   - `remark`: 备注（可选）

2. **`AcceptanceIssueResolve`** - 解决问题请求
   - `solution`: 解决方案（必填）
   - `attachments`: 附件列表（可选）

3. **`AcceptanceIssueVerify`** - 验证问题请求
   - `verified_result`: 验证结果（VERIFIED/REJECTED）
   - `remark`: 备注（可选）

4. **`AcceptanceIssueDefer`** - 延期问题请求
   - `reason`: 延期原因（必填）
   - `new_due_date`: 新的完成日期（必填）

5. **`IssueFollowUpCreate`** - 创建跟进记录请求
   - `action_type`: 操作类型（COMMENT/STATUS_CHANGE/ASSIGN/RESOLVE/VERIFY）
   - `action_content`: 操作内容（必填）
   - `attachments`: 附件列表（可选）

6. **`IssueFollowUpResponse`** - 跟进记录响应
   - 包含跟进记录的所有字段和创建人信息

7. **更新 `AcceptanceIssueResponse`**
   - 新增字段：`resolved_by`, `resolved_by_name`
   - 新增字段：`verified_at`, `verified_by`, `verified_by_name`, `verified_result`
   - 新增字段：`attachments`

### 2. 新增 API 端点 ✅

在 `app/api/v1/endpoints/acceptance.py` 中添加了以下端点：

#### 2.1 获取问题详情

**端点**: `GET /acceptance-issues/{issue_id}`

**功能**: 获取单个问题的详细信息，包括所有关联信息

**响应**: `AcceptanceIssueResponse`

#### 2.2 指派问题

**端点**: `POST /acceptance-issues/{issue_id}/assign`

**功能**: 
- 指派问题给指定负责人
- 设置完成日期
- 自动更新问题状态为 PROCESSING（如果当前是 OPEN）
- 创建跟进记录

**请求体**: `AcceptanceIssueAssign`

**响应**: `AcceptanceIssueResponse`

#### 2.3 解决问题

**端点**: `POST /acceptance-issues/{issue_id}/resolve`

**功能**:
- 标记问题为已解决
- 记录解决方案
- 记录解决时间和解决人
- 支持添加附件
- 创建跟进记录

**请求体**: `AcceptanceIssueResolve`

**响应**: `AcceptanceIssueResponse`

**业务规则**:
- 只有非 CLOSED 状态的问题才能解决
- 解决后状态变为 RESOLVED

#### 2.4 验证问题

**端点**: `POST /acceptance-issues/{issue_id}/verify`

**功能**:
- 验证已解决的问题
- 验证通过：问题状态变为 CLOSED
- 验证不通过：问题状态重新变为 OPEN，清除解决信息
- 记录验证时间和验证人
- 创建跟进记录

**请求体**: `AcceptanceIssueVerify`

**响应**: `AcceptanceIssueResponse`

**业务规则**:
- 只能验证 RESOLVED 状态的问题
- 验证结果必须是 VERIFIED 或 REJECTED
- VERIFIED：问题关闭
- REJECTED：问题重新打开，需要重新处理

#### 2.5 延期问题

**端点**: `POST /acceptance-issues/{issue_id}/defer`

**功能**:
- 延期问题的完成日期
- 记录延期原因
- 更新问题状态为 DEFERRED（如果当前不是 DEFERRED）
- 创建跟进记录

**请求体**: `AcceptanceIssueDefer`

**响应**: `AcceptanceIssueResponse`

**业务规则**:
- 已关闭的问题不能延期

#### 2.6 获取跟进记录

**端点**: `GET /acceptance-issues/{issue_id}/follow-ups`

**功能**: 获取问题的所有跟进记录，按时间顺序排列

**响应**: `List[IssueFollowUpResponse]`

#### 2.7 添加跟进记录（增强版）

**端点**: `POST /acceptance-issues/{issue_id}/follow-ups`

**功能**: 
- 添加问题跟进记录
- 支持指定操作类型
- 支持添加附件

**请求体**: `IssueFollowUpCreate`

**响应**: `ResponseModel`

**改进**:
- 原版本只支持简单的跟进记录（通过 Query 参数）
- 新版本支持完整的跟进记录创建（通过 Request Body）

### 3. 代码优化 ✅

#### 3.1 创建辅助函数

添加了 `build_issue_response()` 辅助函数，用于统一构建问题响应对象：
- 自动查询并填充用户名称（发现人、负责人、解决人、验证人）
- 减少代码重复
- 确保响应格式一致

#### 3.2 统一响应格式

所有问题相关的 API 端点现在都使用 `build_issue_response()` 函数，确保：
- 响应字段完整
- 用户名称正确填充
- 代码维护性更好

#### 3.3 自动创建跟进记录

以下操作会自动创建跟进记录：
- 指派问题：记录指派人和完成日期变更
- 解决问题：记录解决方案和状态变更
- 验证问题：记录验证结果和状态变更
- 延期问题：记录延期原因和日期变更

## API 端点清单

### 问题管理 API（完整列表）

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/acceptance-orders/{order_id}/issues` | GET | 获取问题列表 | ✅ 已存在 |
| `/acceptance-orders/{order_id}/issues` | POST | 创建问题 | ✅ 已存在 |
| `/acceptance-issues/{issue_id}` | GET | 获取问题详情 | ✅ **新增** |
| `/acceptance-issues/{issue_id}` | PUT | 更新问题 | ✅ 已存在 |
| `/acceptance-issues/{issue_id}/assign` | POST | 指派问题 | ✅ **新增** |
| `/acceptance-issues/{issue_id}/resolve` | POST | 解决问题 | ✅ **新增** |
| `/acceptance-issues/{issue_id}/verify` | POST | 验证问题 | ✅ **新增** |
| `/acceptance-issues/{issue_id}/defer` | POST | 延期问题 | ✅ **新增** |
| `/acceptance-issues/{issue_id}/close` | PUT | 关闭问题 | ✅ 已存在 |
| `/acceptance-issues/{issue_id}/follow-ups` | GET | 获取跟进记录 | ✅ **新增** |
| `/acceptance-issues/{issue_id}/follow-ups` | POST | 添加跟进记录 | ✅ 已存在（已增强） |

## 业务规则实现

### 问题状态流转

```
OPEN (待处理)
  ↓ [指派]
PROCESSING (处理中)
  ↓ [解决]
RESOLVED (已解决)
  ↓ [验证]
  ├─ VERIFIED → CLOSED (已关闭)
  └─ REJECTED → OPEN (重新打开)
  
[延期]
DEFERRED (已延期)
```

### 验证规则

1. **解决问题**
   - ✅ 只有非 CLOSED 状态的问题才能解决
   - ✅ 解决后状态变为 RESOLVED
   - ✅ 自动记录解决时间和解决人

2. **验证问题**
   - ✅ 只能验证 RESOLVED 状态的问题
   - ✅ 验证结果必须是 VERIFIED 或 REJECTED
   - ✅ VERIFIED：问题关闭
   - ✅ REJECTED：问题重新打开，清除解决信息

3. **延期问题**
   - ✅ 已关闭的问题不能延期
   - ✅ 延期后状态变为 DEFERRED（如果当前不是）

## 使用示例

### 1. 获取问题详情

```http
GET /api/v1/acceptance-issues/123
```

**响应**:
```json
{
  "id": 123,
  "issue_no": "AI-FAT001-001",
  "order_id": 1,
  "title": "主轴电机异响",
  "status": "OPEN",
  "severity": "CRITICAL",
  "is_blocking": true,
  "found_by_name": "张三",
  "assigned_to_name": null,
  ...
}
```

### 2. 指派问题

```http
POST /api/v1/acceptance-issues/123/assign
Content-Type: application/json

{
  "assigned_to": 5,
  "due_date": "2025-01-20",
  "remark": "请尽快处理"
}
```

### 3. 解决问题

```http
POST /api/v1/acceptance-issues/123/resolve
Content-Type: application/json

{
  "solution": "已更换主轴电机，问题已解决",
  "attachments": ["file1.jpg", "file2.pdf"]
}
```

### 4. 验证问题

```http
POST /api/v1/acceptance-issues/123/verify
Content-Type: application/json

{
  "verified_result": "VERIFIED",
  "remark": "验证通过，问题已彻底解决"
}
```

### 5. 延期问题

```http
POST /api/v1/acceptance-issues/123/defer
Content-Type: application/json

{
  "reason": "需要等待供应商发货",
  "new_due_date": "2025-01-25"
}
```

### 6. 获取跟进记录

```http
GET /api/v1/acceptance-issues/123/follow-ups
```

**响应**:
```json
[
  {
    "id": 1,
    "issue_id": 123,
    "action_type": "ASSIGN",
    "action_content": "问题已指派给 李四",
    "old_value": null,
    "new_value": "5",
    "created_by_name": "张三",
    "created_at": "2025-01-15T10:00:00"
  },
  {
    "id": 2,
    "issue_id": 123,
    "action_type": "RESOLVE",
    "action_content": "问题已解决：已更换主轴电机",
    "old_value": "PROCESSING",
    "new_value": "RESOLVED",
    "created_by_name": "李四",
    "created_at": "2025-01-16T14:30:00"
  }
]
```

## 完成度统计

### 问题管理 API 完成度

| 功能 | 设计文档要求 | 实现状态 | 说明 |
|------|-------------|---------|------|
| 获取问题列表 | ✅ | ✅ 已实现 | - |
| 创建问题 | ✅ | ✅ 已实现 | - |
| 获取问题详情 | ✅ | ✅ **新增** | 之前缺失 |
| 更新问题 | ✅ | ✅ 已实现 | - |
| 指派问题 | ✅ | ✅ **新增** | 之前通过 PUT 实现，现在有专门端点 |
| 解决问题 | ✅ | ✅ **新增** | 之前通过 PUT 实现，现在有专门端点 |
| 验证问题 | ✅ | ✅ **新增** | 之前缺失 |
| 延期问题 | ✅ | ✅ **新增** | 之前缺失 |
| 关闭问题 | ✅ | ✅ 已实现 | - |
| 获取跟进记录 | ✅ | ✅ **新增** | 之前缺失 |
| 添加跟进记录 | ✅ | ✅ 已实现（已增强） | 原版本功能简单，现已增强 |

**完成度：11/11 (100%)** ✅

## 相关文档
- 设计文档：`claude 设计方案/验收管理模块_详细设计文档.md` (第865-941行)
- 评估报告：`验收管理模块完成情况评估.md`

## 状态
✅ **已完成** - 问题管理 API 已完善，符合设计文档要求

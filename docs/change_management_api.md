# 项目变更管理 API 文档

## 基础信息

- **Base URL**: `/api/v1/projects/{project_id}/changes`
- **认证方式**: Bearer Token (JWT)
- **数据格式**: JSON
- **字符编码**: UTF-8

---

## 目录

1. [变更请求管理](#变更请求管理)
2. [审批管理](#审批管理)
3. [状态管理](#状态管理)
4. [统计分析](#统计分析)
5. [数据模型](#数据模型)
6. [错误代码](#错误代码)

---

## 变更请求管理

### 1. 创建变更请求

提交新的变更请求。

**接口**: `POST /api/v1/projects/{project_id}/changes`

**权限**: `change:create`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 变更标题，最长200字符 |
| description | string | 否 | 变更描述 |
| change_type | string | 是 | 变更类型：REQUIREMENT/DESIGN/SCOPE/TECHNICAL |
| change_source | string | 是 | 变更来源：CUSTOMER/INTERNAL |
| cost_impact | decimal | 否 | 成本影响（元） |
| cost_impact_level | string | 否 | 成本影响等级：LOW/MEDIUM/HIGH/CRITICAL |
| time_impact | integer | 否 | 时间影响（天） |
| time_impact_level | string | 否 | 时间影响等级 |
| scope_impact | string | 否 | 范围影响描述 |
| scope_impact_level | string | 否 | 范围影响等级 |
| risk_assessment | string | 否 | 风险评估 |
| impact_details | object | 否 | 影响详情（JSON） |
| notify_customer | boolean | 否 | 是否通知客户，默认false |
| notify_team | boolean | 否 | 是否通知团队，默认true |
| attachments | array | 否 | 附件列表 |

**请求示例**:

```json
{
  "title": "增加数据导出功能",
  "description": "客户要求增加Excel导出功能，包含所有业务数据",
  "change_type": "REQUIREMENT",
  "change_source": "CUSTOMER",
  "cost_impact": 15000.00,
  "cost_impact_level": "MEDIUM",
  "time_impact": 10,
  "time_impact_level": "MEDIUM",
  "scope_impact": "新增导出模块，影响现有报表功能",
  "scope_impact_level": "MEDIUM",
  "risk_assessment": "可能影响系统性能",
  "impact_details": {
    "cost": {
      "labor": 12000,
      "material": 3000,
      "total": 15000,
      "description": "需1名开发人员10天"
    },
    "schedule": {
      "delay_days": 10,
      "affected_milestones": ["MS-002"],
      "description": "延后第二里程碑"
    },
    "scope": {
      "added_features": ["Excel导出", "PDF导出"],
      "removed_features": [],
      "modified_features": ["报表模块"]
    }
  },
  "notify_team": true,
  "attachments": [
    {
      "name": "需求文档.pdf",
      "url": "/uploads/requirement.pdf",
      "size": 1024000
    }
  ]
}
```

**响应示例**:

```json
{
  "code": 200,
  "message": "变更请求提交成功",
  "data": {
    "id": 1,
    "change_code": "CHG-PRJ001-001",
    "project_id": 1,
    "title": "增加数据导出功能",
    "status": "SUBMITTED",
    "submitter_id": 1,
    "submitter_name": "张三",
    "submit_date": "2026-02-14T10:00:00",
    "approval_decision": "PENDING",
    "created_at": "2026-02-14T10:00:00"
  }
}
```

---

### 2. 获取变更列表

查询项目的变更请求列表。

**接口**: `GET /api/v1/projects/{project_id}/changes`

**权限**: `change:read`

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认20 |
| change_type | string | 否 | 变更类型过滤 |
| change_source | string | 否 | 变更来源过滤 |
| status | string | 否 | 状态过滤 |
| submitter_id | integer | 否 | 提交人ID过滤 |
| search | string | 否 | 搜索关键词（标题/描述/编号） |

**响应示例**:

```json
{
  "code": 200,
  "message": "获取变更请求列表成功",
  "data": {
    "items": [
      {
        "id": 1,
        "change_code": "CHG-PRJ001-001",
        "project_id": 1,
        "title": "增加数据导出功能",
        "change_type": "REQUIREMENT",
        "change_source": "CUSTOMER",
        "status": "PENDING_APPROVAL",
        "submitter_name": "张三",
        "submit_date": "2026-02-14T10:00:00",
        "cost_impact": 15000.00,
        "time_impact": 10,
        "approval_decision": "PENDING",
        "created_at": "2026-02-14T10:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 3. 获取变更详情

获取单个变更请求的详细信息。

**接口**: `GET /api/v1/projects/{project_id}/changes/{change_id}`

**权限**: `change:read`

**响应示例**:

```json
{
  "code": 200,
  "message": "获取变更请求详情成功",
  "data": {
    "id": 1,
    "change_code": "CHG-PRJ001-001",
    "project_id": 1,
    "title": "增加数据导出功能",
    "description": "客户要求增加Excel导出功能",
    "change_type": "REQUIREMENT",
    "change_source": "CUSTOMER",
    "status": "APPROVED",
    "submitter_id": 1,
    "submitter_name": "张三",
    "submit_date": "2026-02-14T10:00:00",
    "cost_impact": 15000.00,
    "cost_impact_level": "MEDIUM",
    "time_impact": 10,
    "time_impact_level": "MEDIUM",
    "scope_impact": "新增导出模块",
    "scope_impact_level": "MEDIUM",
    "risk_assessment": "可能影响系统性能",
    "impact_details": {...},
    "approver_id": 2,
    "approver_name": "李四",
    "approval_date": "2026-02-15T14:00:00",
    "approval_decision": "APPROVED",
    "approval_comments": "同意该变更",
    "implementation_plan": null,
    "implementation_start_date": null,
    "implementation_end_date": null,
    "verification_notes": null,
    "close_date": null,
    "attachments": [...],
    "notify_customer": false,
    "notify_team": true,
    "created_at": "2026-02-14T10:00:00",
    "updated_at": "2026-02-15T14:00:00"
  }
}
```

---

### 4. 更新变更请求

更新变更请求信息（仅未批准/未拒绝/未关闭的变更可更新）。

**接口**: `PUT /api/v1/projects/{project_id}/changes/{change_id}`

**权限**: `change:update`

**请求参数**: 同创建接口，但所有字段都是可选的

**响应**: 返回更新后的完整变更信息

---

## 审批管理

### 5. 审批变更

审批变更请求（批准/拒绝/退回）。

**接口**: `POST /api/v1/projects/{project_id}/changes/{change_id}/approve`

**权限**: `change:approve`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| decision | string | 是 | 审批决策：APPROVED/REJECTED/RETURNED |
| comments | string | 否 | 审批意见 |
| attachments | array | 否 | 审批附件 |

**请求示例**:

```json
{
  "decision": "APPROVED",
  "comments": "同意该变更，按计划实施",
  "attachments": [
    {
      "name": "审批意见.pdf",
      "url": "/uploads/approval.pdf"
    }
  ]
}
```

**响应示例**:

```json
{
  "code": 200,
  "message": "审批完成",
  "data": {
    "id": 1,
    "status": "APPROVED",
    "approval_decision": "APPROVED",
    "approver_id": 2,
    "approver_name": "李四",
    "approval_date": "2026-02-15T14:00:00",
    "approval_comments": "同意该变更，按计划实施"
  }
}
```

---

### 6. 获取审批记录

获取变更的所有审批记录。

**接口**: `GET /api/v1/projects/{project_id}/changes/{change_id}/approvals`

**权限**: `change:read`

**响应示例**:

```json
{
  "code": 200,
  "message": "获取审批记录成功",
  "data": {
    "items": [
      {
        "id": 1,
        "change_request_id": 1,
        "approver_id": 2,
        "approver_name": "李四",
        "approver_role": "PM",
        "approval_date": "2026-02-15T14:00:00",
        "decision": "APPROVED",
        "comments": "同意该变更",
        "attachments": [],
        "created_at": "2026-02-15T14:00:00"
      }
    ]
  }
}
```

---

## 状态管理

### 7. 更新变更状态

手动更新变更状态（需遵循状态机规则）。

**接口**: `POST /api/v1/projects/{project_id}/changes/{change_id}/status`

**权限**: `change:update`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| new_status | string | 是 | 新状态 |
| notes | string | 否 | 说明 |

**请求示例**:

```json
{
  "new_status": "IMPLEMENTING",
  "notes": "开始实施变更"
}
```

---

### 8. 更新实施信息

更新变更的实施计划和进度。

**接口**: `POST /api/v1/projects/{project_id}/changes/{change_id}/implement`

**权限**: `change:update`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| implementation_plan | string | 否 | 实施计划 |
| implementation_start_date | datetime | 否 | 实施开始日期 |
| implementation_end_date | datetime | 否 | 实施结束日期 |
| implementation_status | string | 否 | 实施状态 |
| implementation_notes | string | 否 | 实施备注 |

**请求示例**:

```json
{
  "implementation_plan": "分三个阶段实施：\n1. 数据模型设计\n2. 接口开发\n3. 前端集成",
  "implementation_start_date": "2026-02-20T00:00:00",
  "implementation_end_date": "2026-03-05T00:00:00",
  "implementation_status": "进行中",
  "implementation_notes": "第一阶段已完成"
}
```

---

### 9. 验证变更

验证变更实施效果。

**接口**: `POST /api/v1/projects/{project_id}/changes/{change_id}/verify`

**权限**: `change:verify`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| verification_notes | string | 是 | 验证说明 |

**请求示例**:

```json
{
  "verification_notes": "功能已验证通过，符合预期要求。测试覆盖率95%。"
}
```

---

### 10. 关闭变更

手动关闭变更请求。

**接口**: `POST /api/v1/projects/{project_id}/changes/{change_id}/close`

**权限**: `change:close`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| close_notes | string | 否 | 关闭说明 |

**请求示例**:

```json
{
  "close_notes": "变更已完成并验收，所有功能正常运行"
}
```

---

## 统计分析

### 11. 获取变更统计

获取变更请求的统计信息。

**接口**: `GET /api/v1/projects/{project_id}/changes/statistics/summary`

**权限**: `change:read`

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | integer | 否 | 项目ID（如已在路径中指定则忽略） |
| start_date | datetime | 否 | 开始日期 |
| end_date | datetime | 否 | 结束日期 |

**响应示例**:

```json
{
  "code": 200,
  "message": "获取统计信息成功",
  "data": {
    "total": 25,
    "by_status": {
      "SUBMITTED": 3,
      "PENDING_APPROVAL": 5,
      "APPROVED": 8,
      "IMPLEMENTING": 4,
      "CLOSED": 5
    },
    "by_type": {
      "REQUIREMENT": 10,
      "DESIGN": 8,
      "SCOPE": 4,
      "TECHNICAL": 3
    },
    "by_source": {
      "CUSTOMER": 15,
      "INTERNAL": 10
    },
    "pending_approval": 5,
    "approved": 8,
    "rejected": 0,
    "total_cost_impact": 250000.00,
    "total_time_impact": 180
  }
}
```

---

## 数据模型

### ChangeRequest (变更请求)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 主键ID |
| change_code | string | 变更编号，格式：CHG-项目编码-序号 |
| project_id | integer | 项目ID |
| title | string | 变更标题 |
| description | string | 变更描述 |
| change_type | enum | 变更类型 |
| change_source | enum | 变更来源 |
| submitter_id | integer | 提交人ID |
| submitter_name | string | 提交人姓名 |
| submit_date | datetime | 提交日期 |
| cost_impact | decimal | 成本影响（元） |
| cost_impact_level | enum | 成本影响等级 |
| time_impact | integer | 时间影响（天） |
| time_impact_level | enum | 时间影响等级 |
| scope_impact | string | 范围影响描述 |
| scope_impact_level | enum | 范围影响等级 |
| risk_assessment | string | 风险评估 |
| impact_details | json | 影响详情 |
| status | enum | 变更状态 |
| approver_id | integer | 审批人ID |
| approver_name | string | 审批人姓名 |
| approval_date | datetime | 审批日期 |
| approval_decision | enum | 审批决策 |
| approval_comments | string | 审批意见 |
| implementation_* | various | 实施相关字段 |
| verification_* | various | 验证相关字段 |
| close_* | various | 关闭相关字段 |
| attachments | json | 附件列表 |
| notify_customer | boolean | 是否通知客户 |
| notify_team | boolean | 是否通知团队 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 枚举值

#### ChangeTypeEnum (变更类型)
- `REQUIREMENT`: 需求变更
- `DESIGN`: 设计变更
- `SCOPE`: 范围变更
- `TECHNICAL`: 技术变更

#### ChangeSourceEnum (变更来源)
- `CUSTOMER`: 客户提出
- `INTERNAL`: 内部提出

#### ChangeStatusEnum (变更状态)
- `SUBMITTED`: 已提交
- `ASSESSING`: 影响评估中
- `PENDING_APPROVAL`: 待审批
- `APPROVED`: 已批准
- `REJECTED`: 已拒绝
- `IMPLEMENTING`: 实施中
- `VERIFYING`: 验证中
- `CLOSED`: 已关闭
- `CANCELLED`: 已取消

#### ImpactLevelEnum (影响等级)
- `LOW`: 低影响
- `MEDIUM`: 中等影响
- `HIGH`: 高影响
- `CRITICAL`: 严重影响

#### ApprovalDecisionEnum (审批决策)
- `PENDING`: 待审批
- `APPROVED`: 批准
- `REJECTED`: 拒绝
- `RETURNED`: 退回修改

---

## 错误代码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 400 | 请求参数错误 | 检查请求参数格式 |
| 401 | 未认证 | 提供有效的认证token |
| 403 | 权限不足 | 检查用户权限 |
| 404 | 资源不存在 | 确认资源ID正确 |
| 422 | 业务逻辑错误 | 检查业务规则（如状态转换） |
| 500 | 服务器错误 | 联系技术支持 |

### 常见业务错误

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| "项目不存在" | 项目ID无效 | 检查project_id |
| "变更请求不存在" | 变更ID无效 | 检查change_id |
| "只有待审批状态的变更请求才能审批" | 状态不正确 | 先更新状态为PENDING_APPROVAL |
| "不允许从X转换到Y" | 状态转换违反规则 | 参考状态机图 |
| "状态为X的变更请求不能修改" | 变更已确定 | 创建新的变更请求 |

---

**文档版本**: v1.0  
**最后更新**: 2026-02-14  
**API版本**: v1

# 项目变更管理用户指南

## 目录

1. [功能概述](#功能概述)
2. [快速开始](#快速开始)
3. [变更请求生命周期](#变更请求生命周期)
4. [操作指南](#操作指南)
5. [权限说明](#权限说明)
6. [最佳实践](#最佳实践)
7. [常见问题](#常见问题)

---

## 功能概述

项目变更管理模块帮助团队系统化地管理项目中的各类变更请求，包括需求变更、设计变更、范围变更和技术变更。通过标准化的审批流程和完整的影响评估，确保变更的可控性和可追溯性。

### 核心功能

- ✅ **变更请求提交**：支持多种变更类型和来源
- ✅ **影响评估**：成本、时间、范围三维度评估
- ✅ **审批工作流**：完整的状态机管理
- ✅ **实施跟踪**：从批准到验证的全过程
- ✅ **通知机制**：自动通知相关人员
- ✅ **统计分析**：变更趋势和影响分析

---

## 快速开始

### 1. 提交变更请求

```http
POST /api/v1/projects/{project_id}/changes
Content-Type: application/json

{
  "title": "增加数据导出功能",
  "description": "客户要求增加Excel导出功能",
  "change_type": "REQUIREMENT",
  "change_source": "CUSTOMER",
  "cost_impact": 15000.00,
  "cost_impact_level": "MEDIUM",
  "time_impact": 10,
  "time_impact_level": "MEDIUM",
  "notify_team": true
}
```

### 2. 查看变更列表

```http
GET /api/v1/projects/{project_id}/changes?status=PENDING_APPROVAL
```

### 3. 审批变更

```http
POST /api/v1/projects/{project_id}/changes/{change_id}/approve
Content-Type: application/json

{
  "decision": "APPROVED",
  "comments": "同意该变更，按计划实施"
}
```

---

## 变更请求生命周期

### 状态流转图

```
提交 (SUBMITTED)
    ↓
影响评估 (ASSESSING)
    ↓
待审批 (PENDING_APPROVAL)
    ↓
    ├── 已批准 (APPROVED) → 实施中 (IMPLEMENTING) → 验证中 (VERIFYING) → 已关闭 (CLOSED)
    ├── 已拒绝 (REJECTED) [终态]
    └── 已取消 (CANCELLED) [终态]
```

### 状态说明

| 状态 | 说明 | 可转换状态 |
|------|------|------------|
| SUBMITTED | 已提交 | ASSESSING, CANCELLED |
| ASSESSING | 影响评估中 | PENDING_APPROVAL, SUBMITTED, CANCELLED |
| PENDING_APPROVAL | 待审批 | APPROVED, REJECTED, ASSESSING, CANCELLED |
| APPROVED | 已批准 | IMPLEMENTING, CANCELLED |
| REJECTED | 已拒绝 | - |
| IMPLEMENTING | 实施中 | VERIFYING, APPROVED |
| VERIFYING | 验证中 | CLOSED, IMPLEMENTING |
| CLOSED | 已关闭 | - |
| CANCELLED | 已取消 | - |

---

## 操作指南

### 1. 提交变更请求

#### 必填信息
- **标题**：简明扼要的变更描述
- **变更类型**：REQUIREMENT（需求）/ DESIGN（设计）/ SCOPE（范围）/ TECHNICAL（技术）
- **变更来源**：CUSTOMER（客户）/ INTERNAL（内部）

#### 影响评估（可选但建议填写）
- **成本影响**：预估增加的成本（元）
- **成本影响等级**：LOW / MEDIUM / HIGH / CRITICAL
- **时间影响**：预估延迟的天数
- **时间影响等级**：LOW / MEDIUM / HIGH / CRITICAL
- **范围影响**：文字描述范围变化
- **范围影响等级**：LOW / MEDIUM / HIGH / CRITICAL
- **风险评估**：相关风险说明

#### 详细评估（JSON格式）
```json
{
  "cost": {
    "labor": 10000,
    "material": 5000,
    "total": 15000,
    "description": "需增加2名开发人员"
  },
  "schedule": {
    "delay_days": 15,
    "affected_milestones": ["MS-001", "MS-002"],
    "description": "影响交付里程碑"
  },
  "scope": {
    "added_features": ["功能A", "功能B"],
    "removed_features": [],
    "modified_features": ["功能C"]
  }
}
```

### 2. 影响评估

提交变更后，项目经理或技术负责人需要进行影响评估：

```http
PUT /api/v1/projects/{project_id}/changes/{change_id}
Content-Type: application/json

{
  "cost_impact": 20000.00,
  "cost_impact_level": "HIGH",
  "time_impact": 20,
  "time_impact_level": "HIGH",
  "impact_details": {
    "cost": {...},
    "schedule": {...},
    "scope": {...}
  }
}
```

### 3. 提交审批

评估完成后，将状态更新为待审批：

```http
POST /api/v1/projects/{project_id}/changes/{change_id}/status
Content-Type: application/json

{
  "new_status": "PENDING_APPROVAL"
}
```

### 4. 审批变更

PM或有权限的人员进行审批：

#### 批准
```json
{
  "decision": "APPROVED",
  "comments": "同意该变更",
  "attachments": [
    {
      "name": "审批意见.pdf",
      "url": "/uploads/approval.pdf"
    }
  ]
}
```

#### 拒绝
```json
{
  "decision": "REJECTED",
  "comments": "成本太高，不批准"
}
```

#### 退回修改
```json
{
  "decision": "RETURNED",
  "comments": "请补充详细的影响分析"
}
```

### 5. 实施变更

变更批准后，开始实施：

```http
POST /api/v1/projects/{project_id}/changes/{change_id}/implement
Content-Type: application/json

{
  "implementation_plan": "分三个阶段实施...",
  "implementation_start_date": "2026-02-20T00:00:00",
  "implementation_end_date": "2026-03-05T00:00:00",
  "implementation_status": "进行中"
}
```

### 6. 验证变更

实施完成后，进行验证：

```http
POST /api/v1/projects/{project_id}/changes/{change_id}/verify
Content-Type: application/json

{
  "verification_notes": "功能已验证通过，符合预期"
}
```

### 7. 关闭变更

验证通过后自动关闭，也可手动关闭：

```http
POST /api/v1/projects/{project_id}/changes/{change_id}/close
Content-Type: application/json

{
  "close_notes": "变更已完成并验收"
}
```

---

## 权限说明

| 操作 | 所需权限 |
|------|----------|
| 提交变更 | `change:create` |
| 查看变更列表 | `change:read` |
| 查看变更详情 | `change:read` |
| 更新变更信息 | `change:update` |
| 审批变更 | `change:approve` |
| 验证变更 | `change:verify` |
| 关闭变更 | `change:close` |

### 权限分配建议

- **项目成员**：`change:create`, `change:read`
- **项目经理**：`change:create`, `change:read`, `change:update`, `change:approve`, `change:close`
- **技术负责人**：`change:create`, `change:read`, `change:update`, `change:verify`
- **质量负责人**：`change:read`, `change:verify`

---

## 最佳实践

### 1. 变更分类

- **需求变更**：客户需求变化、功能新增或修改
- **设计变更**：技术方案调整、架构优化
- **范围变更**：项目边界调整、交付内容变化
- **技术变更**：技术栈更换、工具升级

### 2. 影响评估原则

1. **全面性**：评估成本、时间、范围三个维度
2. **准确性**：基于数据和经验进行合理评估
3. **及时性**：在变更提出后尽快完成评估
4. **文档化**：详细记录评估过程和依据

### 3. 审批决策指南

| 影响等级 | 建议决策 |
|----------|----------|
| LOW | 快速批准 |
| MEDIUM | 权衡利弊后决定 |
| HIGH | 详细评估后谨慎决定 |
| CRITICAL | 升级至高层决策 |

### 4. 通知管理

- **提交时**：通知PM和技术负责人
- **待审批时**：通知审批人
- **已批准时**：通知实施团队和提交人
- **已拒绝时**：通知提交人并说明原因
- **已关闭时**：通知所有相关人员

---

## 常见问题

### Q1: 如何修改已提交的变更？

**A**: 只有状态为 SUBMITTED、ASSESSING、PENDING_APPROVAL 的变更可以修改。使用 PUT 接口更新变更信息。

### Q2: 变更被拒绝后能否重新提交？

**A**: 已拒绝的变更不能修改状态。如需重新提交，请创建新的变更请求。

### Q3: 如何查看变更的审批历史？

**A**: 使用 `/changes/{change_id}/approvals` 接口查看所有审批记录。

### Q4: 变更的成本和时间影响如何计入项目？

**A**: 系统自动统计所有已批准变更的影响，可通过统计接口查看。

### Q5: 能否批量审批多个变更？

**A**: 目前不支持批量审批，需逐个审批以确保每个变更都经过充分评估。

### Q6: 变更通知如何配置？

**A**: 在提交变更时设置 `notify_team` 和 `notify_customer` 字段。

### Q7: 如何导出变更记录？

**A**: 使用查询接口获取变更列表后，可导出为Excel或PDF格式。

---

## 附录

### 变更类型说明

| 类型 | 英文 | 说明 | 示例 |
|------|------|------|------|
| 需求变更 | REQUIREMENT | 功能需求的增减改 | 新增导出功能 |
| 设计变更 | DESIGN | 设计方案调整 | 改用微服务架构 |
| 范围变更 | SCOPE | 项目范围调整 | 增加培训服务 |
| 技术变更 | TECHNICAL | 技术选型变化 | 更换前端框架 |

### 影响等级说明

| 等级 | 成本影响 | 时间影响 | 处理建议 |
|------|----------|----------|----------|
| LOW | <5000元 | <3天 | 快速处理 |
| MEDIUM | 5000-20000元 | 3-10天 | 正常流程 |
| HIGH | 20000-50000元 | 10-30天 | 详细评估 |
| CRITICAL | >50000元 | >30天 | 升级决策 |

---

**文档版本**: v1.0  
**最后更新**: 2026-02-14  
**维护者**: 项目管理团队

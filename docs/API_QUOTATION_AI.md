# AI报价单自动生成器 API文档

## 概述

AI报价单自动生成器提供智能化的报价单生成、管理和导出功能，支持一键生成三档方案、PDF导出、版本管理和审批流程。

**Base URL**: `/api/v1/presale/ai`

**认证方式**: Bearer Token

---

## API端点列表

### 1. 生成报价单

**端点**: `POST /generate-quotation`

**描述**: 根据报价项自动生成专业报价单

**请求体**:
```json
{
  "presale_ticket_id": 1,
  "customer_id": 1,
  "quotation_type": "standard",
  "items": [
    {
      "name": "定制化ERP系统开发",
      "description": "包含库存管理、财务管理、人力资源等模块",
      "quantity": 1,
      "unit": "套",
      "unit_price": 150000,
      "category": "软件开发"
    }
  ],
  "tax_rate": 0.13,
  "discount_rate": 0.05,
  "validity_days": 30,
  "payment_terms": "首付30%，中期验收30%，终期验收40%"
}
```

**响应**:
```json
{
  "id": 1,
  "quotation_number": "QT-20260215-0001",
  "quotation_type": "standard",
  "items": [...],
  "subtotal": 150000,
  "tax": 19500,
  "discount": 7500,
  "total": 162000,
  "payment_terms": "...",
  "validity_days": 30,
  "status": "draft",
  "version": 1,
  "created_at": "2026-02-15T10:00:00",
  "generation_time": 2.5
}
```

---

### 2. 生成三档报价方案

**端点**: `POST /generate-three-tier-quotations`

**描述**: 一键生成基础版、标准版、高级版三档报价方案，并提供智能推荐

**请求体**:
```json
{
  "presale_ticket_id": 1,
  "customer_id": 1,
  "base_requirements": "企业需要一套ERP系统，包含基本的进销存和财务管理功能",
  "budget_range": {
    "min": 50000,
    "max": 200000
  },
  "priority_features": ["库存管理", "财务管理", "报表分析"]
}
```

**响应**:
```json
{
  "basic": {
    "id": 1,
    "quotation_number": "QT-20260215-0001",
    "quotation_type": "basic",
    "total": 90000,
    ...
  },
  "standard": {
    "id": 2,
    "quotation_number": "QT-20260215-0002",
    "quotation_type": "standard",
    "total": 180000,
    ...
  },
  "premium": {
    "id": 3,
    "quotation_number": "QT-20260215-0003",
    "quotation_type": "premium",
    "total": 350000,
    ...
  },
  "recommendation": "standard",
  "comparison": {
    "price_range": {
      "basic": 90000,
      "standard": 180000,
      "premium": 350000
    },
    "features_count": {
      "basic": 2,
      "standard": 4,
      "premium": 7
    },
    "discount": {
      "basic": 0,
      "standard": 9000,
      "premium": 35000
    }
  }
}
```

---

### 3. 获取报价单

**端点**: `GET /quotation/{quotation_id}`

**描述**: 获取指定报价单的详细信息

**路径参数**:
- `quotation_id` (integer): 报价单ID

**响应**:
```json
{
  "id": 1,
  "quotation_number": "QT-20260215-0001",
  "quotation_type": "standard",
  "items": [...],
  "subtotal": 150000,
  "tax": 19500,
  "discount": 7500,
  "total": 162000,
  "status": "draft",
  "version": 1,
  ...
}
```

---

### 4. 更新报价单

**端点**: `PUT /quotation/{quotation_id}`

**描述**: 更新报价单信息，自动创建新版本

**请求体**:
```json
{
  "items": [...],
  "tax_rate": 0.09,
  "discount_rate": 0.10,
  "validity_days": 60,
  "payment_terms": "更新后的付款条款",
  "status": "approved"
}
```

**响应**: 更新后的报价单完整信息

**说明**:
- 每次更新会自动递增版本号
- 所有字段都是可选的，只更新提供的字段
- 会自动重新计算总价
- 创建版本快照

---

### 5. 导出报价单PDF

**端点**: `POST /export-quotation-pdf/{quotation_id}`

**描述**: 将报价单导出为专业PDF文档

**路径参数**:
- `quotation_id` (integer): 报价单ID

**响应**:
```json
{
  "quotation_id": 1,
  "pdf_url": "uploads/quotations/quotation_QT-20260215-0001.pdf",
  "message": "PDF生成成功"
}
```

**PDF特性**:
- 专业排版
- 包含公司Logo（如配置）
- 完整的报价项清单
- 价格汇总和税费明细
- 付款条款
- 有效期说明

---

### 6. 发送报价单邮件

**端点**: `POST /send-quotation-email/{quotation_id}`

**描述**: 通过邮件发送报价单PDF

**请求体**:
```json
{
  "to_email": "customer@example.com",
  "cc_emails": ["manager@company.com"],
  "subject": "项目报价单 - QT-20260215-0001",
  "message": "尊敬的客户，请查收附件中的报价单。",
  "include_pdf": true
}
```

**响应**:
```json
{
  "quotation_id": 1,
  "to_email": "customer@example.com",
  "message": "邮件发送成功"
}
```

**说明**:
- 如果报价单还没有生成PDF，会自动生成
- 邮件发送后，报价单状态自动更新为 `sent`

---

### 7. 获取报价单版本历史

**端点**: `GET /quotation-history/{ticket_id}`

**描述**: 获取指定工单的所有报价单版本历史

**路径参数**:
- `ticket_id` (integer): 售前工单ID

**响应**:
```json
{
  "quotation_id": 1,
  "current_version": 3,
  "versions": [
    {
      "id": 3,
      "quotation_id": 1,
      "version": 3,
      "snapshot_data": {...},
      "changed_by": 1,
      "change_summary": "调整折扣率; 有效期调整为60天",
      "created_at": "2026-02-15T14:00:00"
    },
    {
      "id": 2,
      "quotation_id": 1,
      "version": 2,
      "snapshot_data": {...},
      "changed_by": 1,
      "change_summary": "更新报价项",
      "created_at": "2026-02-15T12:00:00"
    },
    {
      "id": 1,
      "quotation_id": 1,
      "version": 1,
      "snapshot_data": {...},
      "changed_by": 1,
      "change_summary": "初始创建",
      "created_at": "2026-02-15T10:00:00"
    }
  ],
  "total_versions": 3
}
```

---

### 8. 审批报价单

**端点**: `POST /approve-quotation/{quotation_id}`

**描述**: 审批或拒绝报价单

**请求体**:
```json
{
  "status": "approved",
  "comments": "方案合理，批准通过"
}
```

**参数说明**:
- `status`: 审批状态，`approved`（通过）或 `rejected`（拒绝）
- `comments`: 审批意见（可选）

**响应**:
```json
{
  "id": 1,
  "quotation_id": 1,
  "approver_id": 2,
  "status": "approved",
  "comments": "方案合理，批准通过",
  "created_at": "2026-02-15T10:00:00",
  "approved_at": "2026-02-15T11:00:00"
}
```

**说明**:
- 审批后报价单状态会自动更新
- `approved` → 报价单状态变为 `approved`
- `rejected` → 报价单状态变为 `rejected`

---

## 数据模型

### QuotationType（报价单类型）

- `basic`: 基础版
- `standard`: 标准版
- `premium`: 高级版

### QuotationStatus（报价单状态）

- `draft`: 草稿
- `pending_approval`: 待审批
- `approved`: 已审批
- `sent`: 已发送
- `accepted`: 已接受
- `rejected`: 已拒绝

### QuotationItem（报价项）

```json
{
  "name": "项目名称",
  "description": "项目描述",
  "quantity": 1,
  "unit": "套",
  "unit_price": 100000,
  "total_price": 100000,
  "category": "软件开发"
}
```

---

## 错误响应

所有API在错误时返回标准格式：

```json
{
  "detail": "错误描述信息"
}
```

### HTTP状态码

- `200 OK`: 请求成功
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器错误

---

## 使用示例

### Python示例

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/presale/ai"
TOKEN = "your_access_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 1. 生成三档方案
response = requests.post(
    f"{BASE_URL}/generate-three-tier-quotations",
    headers=headers,
    json={
        "presale_ticket_id": 1,
        "base_requirements": "企业需要ERP系统",
        "budget_range": {"min": 50000, "max": 200000}
    }
)
result = response.json()

# 获取推荐方案
recommendation = result["recommendation"]
standard_quotation = result[recommendation]

# 2. 导出PDF
quotation_id = standard_quotation["id"]
pdf_response = requests.post(
    f"{BASE_URL}/export-quotation-pdf/{quotation_id}",
    headers=headers
)
pdf_url = pdf_response.json()["pdf_url"]

# 3. 发送邮件
requests.post(
    f"{BASE_URL}/send-quotation-email/{quotation_id}",
    headers=headers,
    json={
        "to_email": "customer@example.com",
        "subject": "项目报价单",
        "message": "请查收附件中的报价单。"
    }
)
```

### cURL示例

```bash
# 生成报价单
curl -X POST "http://localhost:8000/api/v1/presale/ai/generate-quotation" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "presale_ticket_id": 1,
    "quotation_type": "standard",
    "items": [
      {
        "name": "ERP系统开发",
        "quantity": 1,
        "unit": "套",
        "unit_price": 150000
      }
    ]
  }'

# 导出PDF
curl -X POST "http://localhost:8000/api/v1/presale/ai/export-quotation-pdf/1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 审批报价单
curl -X POST "http://localhost:8000/api/v1/presale/ai/approve-quotation/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved",
    "comments": "批准通过"
  }'
```

---

## 最佳实践

1. **使用三档方案**: 优先使用 `/generate-three-tier-quotations` 为客户提供多种选择
2. **版本管理**: 重大修改前先保存当前版本，使用 `/quotation-history` 查看变更记录
3. **PDF生成**: 发送邮件前确保PDF已生成，避免重复生成
4. **审批流程**: 重要报价单建议经过审批后再发送给客户
5. **有效期管理**: 根据项目复杂度设置合理的有效期（30-90天）

---

## 性能指标

- 报价单生成时间: <10秒
- PDF生成时间: <5秒
- 三档方案生成: <15秒
- 并发支持: 100+ 请求/秒

---

## 更新日志

### v1.0.0 (2026-02-15)

- ✅ 8个核心API端点
- ✅ 三档方案智能生成
- ✅ PDF自动导出
- ✅ 版本管理和历史追踪
- ✅ 审批流程
- ✅ 24+单元测试
- ✅ 完整API文档

---

**技术支持**: Team 5 - AI Quotation Generator

# 合同管理模块 API 文档

## 📚 概述

合同管理模块提供完整的合同生命周期管理，包括：
- 合同CRUD操作
- 分级审批流程
- 合同条款管理
- 合同附件管理
- 合同状态流转
- 合同统计分析

**Base URL**: `/api/v1/contracts/enhanced`

---

## 🔐 认证

所有API接口需要Bearer Token认证：

```
Authorization: Bearer <your_access_token>
```

---

## 📋 合同CRUD

### 1. 创建合同

**POST** `/`

#### 请求体
```json
{
  "contract_name": "XX公司自动化设备采购合同",
  "contract_type": "sales",
  "customer_id": 1,
  "total_amount": 150000.00,
  "received_amount": 0.00,
  "signing_date": "2026-02-15",
  "effective_date": "2026-02-15",
  "expiry_date": "2027-02-15",
  "contract_period": 12,
  "contract_subject": "自动化生产线设备",
  "payment_terms": "分3期付款：首付30%，发货前40%，验收后30%",
  "delivery_terms": "签约后60个工作日内交付",
  "sales_owner_id": 5,
  "contract_manager_id": 8,
  "terms": [
    {
      "term_type": "subject",
      "term_content": "设备包括：主控系统、传送带、检测装置等"
    },
    {
      "term_type": "warranty",
      "term_content": "质保期12个月，免费维护"
    }
  ]
}
```

#### 响应
```json
{
  "id": 1,
  "contract_code": "HT-20260215-001",
  "contract_name": "XX公司自动化设备采购合同",
  "contract_type": "sales",
  "status": "draft",
  "total_amount": 150000.00,
  "received_amount": 0.00,
  "unreceived_amount": 150000.00,
  "created_at": "2026-02-15T10:00:00"
}
```

### 2. 获取合同列表

**GET** `/?skip=0&limit=20&status=draft&customer_id=1&keyword=自动化`

#### 查询参数
- `skip`: 跳过记录数（分页）
- `limit`: 返回记录数（分页）
- `status`: 状态筛选（draft/approving/signed/executing/completed/voided）
- `customer_id`: 客户ID筛选
- `contract_type`: 合同类型筛选（sales/purchase/framework）
- `keyword`: 关键词搜索（合同编号/名称）

#### 响应
```json
{
  "items": [
    {
      "id": 1,
      "contract_code": "HT-20260215-001",
      "contract_name": "XX公司自动化设备采购合同",
      "status": "draft",
      "total_amount": 150000.00
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

### 3. 获取合同详情

**GET** `/{contract_id}`

#### 响应
```json
{
  "id": 1,
  "contract_code": "HT-20260215-001",
  "contract_name": "XX公司自动化设备采购合同",
  "contract_type": "sales",
  "customer_id": 1,
  "status": "draft",
  "total_amount": 150000.00,
  "received_amount": 0.00,
  "unreceived_amount": 150000.00,
  "terms": [
    {
      "id": 1,
      "term_type": "subject",
      "term_content": "设备包括：主控系统、传送带、检测装置等"
    }
  ],
  "approvals": [],
  "attachments": []
}
```

### 4. 更新合同

**PUT** `/{contract_id}`

⚠️ **仅草稿状态可更新**

#### 请求体
```json
{
  "contract_name": "修改后的合同名称",
  "total_amount": 180000.00
}
```

### 5. 删除合同

**DELETE** `/{contract_id}`

⚠️ **仅草稿状态可删除**

---

## ✅ 合同审批流程

### 审批规则

| 合同金额 | 审批流程 |
|---------|---------|
| < 10万 | 销售经理审批 |
| 10-50万 | 销售总监审批 |
| > 50万 | 销售总监 → 财务总监 → 总经理 |

### 1. 提交审批

**POST** `/{contract_id}/submit`

#### 请求体
```json
{
  "comment": "合同已准备完毕，请审批"
}
```

#### 响应
```json
{
  "id": 1,
  "status": "approving",
  "approvals": [
    {
      "id": 1,
      "approval_level": 1,
      "approval_role": "sales_manager",
      "approval_status": "pending"
    }
  ]
}
```

### 2. 获取审批记录

**GET** `/{contract_id}/approvals`

#### 响应
```json
[
  {
    "id": 1,
    "approval_level": 1,
    "approval_role": "sales_manager",
    "approver_id": 5,
    "approver_name": "张经理",
    "approval_status": "approved",
    "approval_opinion": "同意",
    "approved_at": "2026-02-15T11:00:00"
  }
]
```

### 3. 审批通过

**POST** `/{contract_id}/approve?approval_id=1`

#### 请求体
```json
{
  "approval_status": "approved",
  "approval_opinion": "同意签署"
}
```

### 4. 审批驳回

**POST** `/{contract_id}/reject?approval_id=1`

#### 请求体
```json
{
  "approval_status": "rejected",
  "approval_opinion": "合同金额需要调整，请重新提交"
}
```

### 5. 待审批列表（我的待办）

**GET** `/approvals/pending`

#### 响应
```json
[
  {
    "id": 1,
    "contract_id": 1,
    "approval_level": 1,
    "approval_role": "sales_manager",
    "approval_status": "pending",
    "contract": {
      "contract_code": "HT-20260215-001",
      "contract_name": "XX公司自动化设备采购合同"
    }
  }
]
```

---

## 📝 合同条款管理

### 条款类型
- `subject`: 标的条款
- `price`: 价格条款
- `delivery`: 交付条款
- `payment`: 付款条款
- `warranty`: 质保条款
- `breach`: 违约条款

### 1. 添加条款

**POST** `/{contract_id}/terms`

#### 请求体
```json
{
  "term_type": "payment",
  "term_content": "首付30%，签约3日内支付；发货前40%；验收后30%"
}
```

### 2. 获取条款列表

**GET** `/{contract_id}/terms`

### 3. 更新条款

**PUT** `/terms/{term_id}`

#### 请求体
```json
{
  "term_content": "修改后的条款内容"
}
```

### 4. 删除条款

**DELETE** `/terms/{term_id}`

---

## 📎 合同附件管理

### 1. 上传附件

**POST** `/{contract_id}/attachments`

#### 请求体
```json
{
  "file_name": "合同正本.pdf",
  "file_path": "/uploads/contracts/001.pdf",
  "file_type": "application/pdf",
  "file_size": 1024000
}
```

### 2. 获取附件列表

**GET** `/{contract_id}/attachments`

### 3. 删除附件

**DELETE** `/attachments/{attachment_id}`

### 4. 下载附件

**GET** `/attachments/{attachment_id}/download`

---

## 🔄 合同状态流转

### 状态流转图

```
草稿 → 提交审批 → 审批中 → 已审批 → 已签署 → 执行中 → 已完成
                  ↓ (驳回)
                草稿

作废：任意状态（除已完成）可作废
```

### 1. 标记为已签署

**POST** `/{contract_id}/sign`

⚠️ 前置条件：status = 'approved'

### 2. 标记为执行中

**POST** `/{contract_id}/execute`

⚠️ 前置条件：status = 'signed'

### 3. 标记为已完成

**POST** `/{contract_id}/complete`

⚠️ 前置条件：status = 'executing'

### 4. 作废合同

**POST** `/{contract_id}/void`

⚠️ 已完成的合同不能作废

#### 请求体
```json
{
  "comment": "客户取消订单"
}
```

---

## 📊 合同统计

**GET** `/stats/summary`

#### 响应
```json
{
  "total_count": 100,
  "draft_count": 15,
  "approving_count": 8,
  "signed_count": 20,
  "executing_count": 35,
  "completed_count": 18,
  "voided_count": 4,
  "total_amount": 15000000.00,
  "received_amount": 8500000.00,
  "unreceived_amount": 6500000.00
}
```

---

## ⚠️ 错误代码

| 状态码 | 说明 |
|-------|------|
| 400 | 请求参数错误 / 业务逻辑错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

### 错误响应示例
```json
{
  "detail": "只能更新草稿状态的合同"
}
```

---

## 🔧 常见使用场景

### 场景1：创建合同并提交审批
```python
# 1. 创建合同
response = requests.post(
    f"{base_url}/",
    json={
        "contract_name": "测试合同",
        "contract_type": "sales",
        "customer_id": 1,
        "total_amount": 120000.00
    }
)
contract_id = response.json()["id"]

# 2. 添加条款
requests.post(
    f"{base_url}/{contract_id}/terms",
    json={
        "term_type": "payment",
        "term_content": "分期付款"
    }
)

# 3. 提交审批
requests.post(
    f"{base_url}/{contract_id}/submit",
    json={"comment": "请审批"}
)
```

### 场景2：审批流程
```python
# 1. 获取待审批列表
response = requests.get(f"{base_url}/approvals/pending")
pending = response.json()[0]

# 2. 审批通过
requests.post(
    f"{base_url}/{pending['contract_id']}/approve?approval_id={pending['id']}",
    json={"approval_opinion": "同意"}
)
```

### 场景3：合同执行流程
```python
# 审批通过后 -> 签署 -> 执行 -> 完成
requests.post(f"{base_url}/{contract_id}/sign")
requests.post(f"{base_url}/{contract_id}/execute")
requests.post(f"{base_url}/{contract_id}/complete")
```

---

## 📌 注意事项

1. **合同编号自动生成**：格式为 `HT-YYYYMMDD-XXX`，每日自动递增
2. **未收款金额自动计算**：`unreceived_amount = total_amount - received_amount`
3. **状态限制**：
   - 只能更新/删除草稿状态的合同
   - 状态流转必须遵循流程图
   - 已完成合同不可作废
4. **审批流程**：
   - 根据合同金额自动创建审批流程
   - 所有审批通过后状态变为 'approved'
   - 驳回后状态回到 'draft'
5. **权限控制**：
   - 需要配置审批角色与用户的映射关系
   - 不同角色有不同的操作权限

---

**版本**: v1.0  
**更新时间**: 2026-02-15

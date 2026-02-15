# 客户档案与联系人管理 API 文档

## 概述

本模块提供完整的客户关系管理（CRM）功能，包括客户档案管理、联系人管理和客户标签管理。

**基础URL**: `/api/v1/sales`

**版本**: v1.0.0

**更新日期**: 2026-02-15

---

## 客户档案管理

### 1. 创建客户

**端点**: `POST /customers`

**权限**: 需要登录，销售人员或管理员

**请求体**:
```json
{
  "name": "示例科技有限公司",
  "short_name": "示例科技",
  "customer_type": "enterprise",
  "industry": "电子制造",
  "scale": "中型",
  "address": "上海市浦东新区张江高科技园区",
  "website": "https://example.com",
  "established_date": "2015-03-20",
  "credit_limit": 1000000.00,
  "payment_terms": "月结30天",
  "account_period": 30,
  "customer_source": "展会",
  "status": "potential",
  "annual_revenue": 0,
  "cooperation_years": 0
}
```

**字段说明**:
- `name` (必填): 客户名称
- `customer_code` (可选): 客户编码，留空自动生成
- `customer_type` (可选): 客户类型，`enterprise`（企业）或 `individual`（个人），默认 `enterprise`
- `status` (可选): 客户状态
  - `potential`: 潜在客户
  - `prospect`: 意向客户
  - `customer`: 成交客户
  - `lost`: 流失客户

**响应示例**:
```json
{
  "id": 1,
  "customer_code": "CUS202602150001",
  "name": "示例科技有限公司",
  "short_name": "示例科技",
  "customer_type": "enterprise",
  "customer_level": "D",
  "industry": "电子制造",
  "status": "potential",
  "sales_owner_id": 1,
  "sales_owner_name": "张三",
  "contacts_count": 0,
  "tags": [],
  "created_at": "2026-02-15T10:00:00",
  "updated_at": "2026-02-15T10:00:00"
}
```

---

### 2. 获取客户列表

**端点**: `GET /customers`

**权限**: 需要登录

**查询参数**:
- `page` (可选): 页码，默认 1
- `page_size` (可选): 每页数量，默认 20
- `keyword` (可选): 关键词搜索（客户名称、编号、简称）
- `customer_level` (可选): 客户等级筛选（A/B/C/D）
- `status` (可选): 客户状态筛选
- `industry` (可选): 行业筛选
- `sales_owner_id` (可选): 负责销售人员ID筛选
- `order_by` (可选): 排序字段，默认 `created_at`
- `order_desc` (可选): 是否降序，默认 `true`

**响应示例**:
```json
{
  "total": 150,
  "items": [
    {
      "id": 1,
      "customer_code": "CUS202602150001",
      "name": "示例科技有限公司",
      "customer_level": "A",
      "status": "customer",
      "industry": "电子制造",
      "annual_revenue": 1500000.00,
      "cooperation_years": 5,
      "sales_owner_name": "张三",
      "contacts_count": 3,
      "tags": ["重点客户", "长期合作"],
      "last_follow_up_at": "2026-02-14T15:30:00",
      "created_at": "2021-01-10T09:00:00"
    }
  ]
}
```

---

### 3. 获取客户详情

**端点**: `GET /customers/{customer_id}`

**权限**: 需要登录，负责人或管理员

**路径参数**:
- `customer_id`: 客户ID

**响应**: 同创建客户的响应格式

---

### 4. 更新客户

**端点**: `PUT /customers/{customer_id}`

**权限**: 需要登录，负责人或管理员

**请求体**:
```json
{
  "industry": "半导体制造",
  "scale": "大型",
  "annual_revenue": 2000000.00,
  "cooperation_years": 6
}
```

**说明**: 只需提供需要更新的字段。更新 `annual_revenue` 或 `cooperation_years` 会自动重新计算客户等级。

---

### 5. 删除客户

**端点**: `DELETE /customers/{customer_id}`

**权限**: 需要登录，负责人或管理员

**响应**: HTTP 204 No Content

**说明**: 删除客户会级联删除其所有联系人和标签。

---

### 6. 获取客户统计

**端点**: `GET /customers/stats`

**权限**: 需要登录

**响应示例**:
```json
{
  "total_customers": 150,
  "potential_count": 30,
  "prospect_count": 45,
  "customer_count": 70,
  "lost_count": 5,
  "level_a_count": 10,
  "level_b_count": 25,
  "level_c_count": 40,
  "level_d_count": 75,
  "total_annual_revenue": 50000000.00,
  "avg_cooperation_years": 3.5
}
```

---

## 客户分级规则

客户等级根据 `annual_revenue`（年成交额）和 `cooperation_years`（合作年限）自动计算：

| 等级 | 年成交额 | 合作年限 |
|------|---------|---------|
| A级  | > 100万  | > 3年   |
| B级  | 50-100万 | 1-3年   |
| C级  | 10-50万  | < 1年   |
| D级  | < 10万 或潜在客户 | - |

**自动更新**: 创建客户或更新 `annual_revenue`/`cooperation_years` 时自动计算并更新等级。

---

## 联系人管理

### 1. 添加联系人

**端点**: `POST /customers/{customer_id}/contacts`

**权限**: 需要登录，客户负责人或管理员

**请求体**:
```json
{
  "name": "李经理",
  "position": "采购经理",
  "department": "采购部",
  "mobile": "13800138000",
  "phone": "021-88888888",
  "email": "lijingli@example.com",
  "wechat": "lijingli_wx",
  "birthday": "1985-06-15",
  "hobbies": "高尔夫、摄影",
  "notes": "决策链关键人物",
  "is_primary": false
}
```

**响应示例**:
```json
{
  "id": 1,
  "customer_id": 1,
  "customer_name": "示例科技有限公司",
  "name": "李经理",
  "position": "采购经理",
  "department": "采购部",
  "mobile": "13800138000",
  "email": "lijingli@example.com",
  "is_primary": false,
  "created_at": "2026-02-15T10:30:00"
}
```

---

### 2. 获取客户联系人列表

**端点**: `GET /customers/{customer_id}/contacts`

**权限**: 需要登录，客户负责人或管理员

**查询参数**:
- `page` (可选): 页码
- `page_size` (可选): 每页数量

**响应**: 主要联系人排在前面

---

### 3. 获取所有联系人（全局搜索）

**端点**: `GET /contacts`

**权限**: 需要登录

**查询参数**:
- `keyword` (可选): 关键词搜索（姓名、手机、邮箱）
- `customer_id` (可选): 筛选指定客户的联系人

---

### 4. 获取联系人详情

**端点**: `GET /contacts/{contact_id}`

---

### 5. 更新联系人

**端点**: `PUT /contacts/{contact_id}`

**请求体**: 同添加联系人，所有字段可选

---

### 6. 删除联系人

**端点**: `DELETE /contacts/{contact_id}`

**响应**: HTTP 204 No Content

---

### 7. 设置主要联系人

**端点**: `POST /contacts/{contact_id}/set-primary`

**权限**: 需要登录，客户负责人或管理员

**说明**: 设置为主要联系人后，该客户的其他联系人的 `is_primary` 会自动设为 `false`。

---

## 客户标签管理

### 1. 获取预定义标签

**端点**: `GET /customer-tags/predefined`

**响应示例**:
```json
{
  "tags": [
    "重点客户",
    "战略客户",
    "普通客户",
    "流失客户",
    "高价值客户",
    "长期合作",
    "新客户"
  ]
}
```

---

### 2. 添加单个标签

**端点**: `POST /customers/{customer_id}/tags`

**请求体**:
```json
{
  "customer_id": 1,
  "tag_name": "重点客户"
}
```

**说明**: 同一客户不能有重复标签。

---

### 3. 批量添加标签

**端点**: `POST /customers/{customer_id}/tags/batch`

**请求体**:
```json
{
  "customer_id": 1,
  "tag_names": ["重点客户", "长期合作", "高价值客户"]
}
```

**说明**: 自动过滤已存在的标签。

---

### 4. 获取客户标签列表

**端点**: `GET /customers/{customer_id}/tags`

**响应示例**:
```json
[
  {
    "id": 1,
    "customer_id": 1,
    "tag_name": "重点客户",
    "created_at": "2026-02-15T10:00:00"
  },
  {
    "id": 2,
    "customer_id": 1,
    "tag_name": "长期合作",
    "created_at": "2026-02-15T10:01:00"
  }
]
```

---

### 5. 删除标签（按ID）

**端点**: `DELETE /customers/{customer_id}/tags/{tag_id}`

---

### 6. 删除标签（按名称）

**端点**: `DELETE /customers/{customer_id}/tags?tag_name={tag_name}`

---

## 错误响应

所有端点遵循统一的错误响应格式：

```json
{
  "detail": "错误描述信息"
}
```

**常见错误码**:
- `400 Bad Request`: 请求参数错误、重复创建等
- `401 Unauthorized`: 未登录
- `403 Forbidden`: 无权限访问
- `404 Not Found`: 资源不存在

---

## 数据权限

- **销售人员**: 只能查看和管理自己负责的客户
- **管理员**: 可查看和管理所有客户
- **删除操作**: 仅负责人和管理员可执行

---

## 使用示例

### Python 示例

```python
import requests

# 登录获取token
login_response = requests.post(
    "http://api.example.com/api/v1/auth/login",
    json={"username": "user", "password": "pass"}
)
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 创建客户
customer_data = {
    "name": "新客户公司",
    "industry": "电子制造",
    "customer_source": "展会"
}
response = requests.post(
    "http://api.example.com/api/v1/sales/customers",
    json=customer_data,
    headers=headers
)
customer = response.json()
customer_id = customer["id"]

# 添加联系人
contact_data = {
    "name": "张经理",
    "position": "采购经理",
    "mobile": "13800138000",
    "is_primary": True
}
requests.post(
    f"http://api.example.com/api/v1/sales/customers/{customer_id}/contacts",
    json=contact_data,
    headers=headers
)

# 添加标签
requests.post(
    f"http://api.example.com/api/v1/sales/customers/{customer_id}/tags/batch",
    json={"customer_id": customer_id, "tag_names": ["重点客户", "新客户"]},
    headers=headers
)
```

---

## 更新日志

**v1.0.0** (2026-02-15)
- 初始版本发布
- 客户档案完整CRUD
- 联系人管理
- 客户分级自动化
- 标签管理功能

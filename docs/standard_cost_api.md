# 标准成本库管理 API 文档

## 概述

标准成本库管理API提供了完整的标准成本CRUD操作、批量导入、历史记录查询和项目集成功能。

**Base URL:** `/api/v1/standard-costs`

## 认证

所有API端点都需要认证。请在请求头中包含JWT token：

```
Authorization: Bearer <your_token>
```

## 权限要求

- `cost:read` - 查询标准成本
- `cost:manage` - 创建、更新、删除标准成本

## API端点

### 1. 标准成本CRUD

#### 1.1 创建标准成本

**POST** `/api/v1/standard-costs/`

创建新的标准成本项。

**权限:** cost:manage

**请求体:**

```json
{
  "cost_code": "MAT-001",
  "cost_name": "钢板Q235",
  "cost_category": "MATERIAL",
  "specification": "8mm厚度",
  "unit": "kg",
  "standard_cost": 4.50,
  "currency": "CNY",
  "cost_source": "HISTORICAL_AVG",
  "source_description": "基于过去6个月平均价格",
  "effective_date": "2026-01-01",
  "expiry_date": null,
  "description": "普通碳素结构钢板",
  "notes": "市场价格稳定"
}
```

**字段说明:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| cost_code | string | 是 | 成本项编码，唯一标识 |
| cost_name | string | 是 | 成本项名称 |
| cost_category | string | 是 | 成本类别：MATERIAL/LABOR/OVERHEAD |
| specification | string | 否 | 规格型号 |
| unit | string | 是 | 单位（kg、件、人天等） |
| standard_cost | decimal | 是 | 标准成本 |
| currency | string | 否 | 币种，默认CNY |
| cost_source | string | 是 | 成本来源：HISTORICAL_AVG/INDUSTRY_STANDARD/EXPERT_ESTIMATE/VENDOR_QUOTE |
| source_description | string | 否 | 来源说明 |
| effective_date | date | 是 | 生效日期(YYYY-MM-DD) |
| expiry_date | date | 否 | 失效日期(YYYY-MM-DD)，为空表示长期有效 |
| description | string | 否 | 成本说明 |
| notes | string | 否 | 备注 |

**响应示例:**

```json
{
  "id": 1,
  "cost_code": "MAT-001",
  "cost_name": "钢板Q235",
  "cost_category": "MATERIAL",
  "specification": "8mm厚度",
  "unit": "kg",
  "standard_cost": 4.50,
  "currency": "CNY",
  "cost_source": "HISTORICAL_AVG",
  "source_description": "基于过去6个月平均价格",
  "effective_date": "2026-01-01",
  "expiry_date": null,
  "version": 1,
  "is_active": true,
  "parent_id": null,
  "created_by": 1,
  "updated_by": null,
  "description": "普通碳素结构钢板",
  "notes": "市场价格稳定",
  "created_at": "2026-02-14T10:00:00",
  "updated_at": "2026-02-14T10:00:00"
}
```

**错误响应:**

- `400 Bad Request` - 成本编码已存在
- `401 Unauthorized` - 未认证
- `403 Forbidden` - 无权限

#### 1.2 获取标准成本列表

**GET** `/api/v1/standard-costs/`

获取标准成本列表，支持分页和筛选。

**权限:** cost:read

**查询参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认20 |
| cost_category | string | 否 | 成本类别筛选 |
| cost_source | string | 否 | 成本来源筛选 |
| is_active | boolean | 否 | 是否有效 |

**响应示例:**

```json
{
  "items": [
    {
      "id": 1,
      "cost_code": "MAT-001",
      "cost_name": "钢板Q235",
      "cost_category": "MATERIAL",
      "unit": "kg",
      "standard_cost": 4.50,
      "currency": "CNY",
      "effective_date": "2026-01-01",
      "is_active": true,
      "version": 1
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

#### 1.3 搜索标准成本

**GET** `/api/v1/standard-costs/search`

搜索标准成本，支持多条件组合。

**权限:** cost:read

**查询参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 关键词（编码/名称/规格） |
| cost_category | string | 否 | 成本类别 |
| cost_source | string | 否 | 成本来源 |
| is_active | boolean | 否 | 是否有效，默认true |
| effective_date_from | date | 否 | 生效日期起 |
| effective_date_to | date | 否 | 生效日期止 |

**响应示例:**

```json
[
  {
    "id": 1,
    "cost_code": "MAT-001",
    "cost_name": "钢板Q235",
    "cost_category": "MATERIAL",
    "specification": "8mm厚度",
    "unit": "kg",
    "standard_cost": 4.50,
    "currency": "CNY",
    "is_active": true
  }
]
```

#### 1.4 获取标准成本详情

**GET** `/api/v1/standard-costs/{cost_id}`

获取指定标准成本的详细信息。

**权限:** cost:read

**响应示例:**

```json
{
  "id": 1,
  "cost_code": "MAT-001",
  "cost_name": "钢板Q235",
  "cost_category": "MATERIAL",
  "specification": "8mm厚度",
  "unit": "kg",
  "standard_cost": 4.50,
  "currency": "CNY",
  "cost_source": "HISTORICAL_AVG",
  "source_description": "基于过去6个月平均价格",
  "effective_date": "2026-01-01",
  "expiry_date": null,
  "version": 1,
  "is_active": true,
  "parent_id": null,
  "created_by": 1,
  "updated_by": null,
  "description": "普通碳素结构钢板",
  "notes": null,
  "created_at": "2026-02-14T10:00:00",
  "updated_at": "2026-02-14T10:00:00"
}
```

**错误响应:**

- `404 Not Found` - 标准成本不存在

#### 1.5 更新标准成本

**PUT** `/api/v1/standard-costs/{cost_id}`

更新标准成本。系统会创建新版本，保留历史版本。

**权限:** cost:manage

**请求体:**

```json
{
  "standard_cost": 5.00,
  "cost_source": "VENDOR_QUOTE",
  "source_description": "供应商涨价",
  "notes": "原材料价格上涨10%"
}
```

**响应示例:**

```json
{
  "id": 2,
  "cost_code": "MAT-001",
  "cost_name": "钢板Q235",
  "standard_cost": 5.00,
  "version": 2,
  "is_active": true,
  "parent_id": 1,
  "updated_by": 1,
  "created_at": "2026-02-14T11:00:00",
  "updated_at": "2026-02-14T11:00:00"
}
```

#### 1.6 停用标准成本

**DELETE** `/api/v1/standard-costs/{cost_id}`

停用标准成本（软删除）。

**权限:** cost:manage

**响应示例:**

```json
{
  "code": 200,
  "message": "标准成本已停用",
  "data": {
    "id": 1
  }
}
```

### 2. 历史记录和版本管理

#### 2.1 获取标准成本历史记录

**GET** `/api/v1/standard-costs/history`

获取标准成本历史变动记录，支持分页和筛选。

**权限:** cost:read

**查询参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码 |
| page_size | integer | 否 | 每页数量 |
| cost_id | integer | 否 | 标准成本ID筛选 |
| change_type | string | 否 | 变更类型筛选 |
| date_from | date | 否 | 变更日期起 |
| date_to | date | 否 | 变更日期止 |

**响应示例:**

```json
{
  "items": [
    {
      "id": 1,
      "standard_cost_id": 1,
      "change_type": "CREATE",
      "change_date": "2026-02-14",
      "old_cost": null,
      "new_cost": 4.50,
      "old_effective_date": null,
      "new_effective_date": "2026-01-01",
      "change_reason": "创建标准成本",
      "change_description": "创建成本项：钢板Q235",
      "changed_by": 1,
      "changed_by_name": "管理员",
      "created_at": "2026-02-14T10:00:00"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

#### 2.2 获取特定成本的历史记录

**GET** `/api/v1/standard-costs/{cost_id}/history`

获取指定标准成本的所有历史记录。

**权限:** cost:read

**响应示例:**

```json
[
  {
    "id": 2,
    "standard_cost_id": 1,
    "change_type": "UPDATE",
    "change_date": "2026-02-14",
    "old_cost": 4.50,
    "new_cost": 5.00,
    "change_reason": "价格上涨",
    "changed_by": 1,
    "changed_by_name": "管理员"
  },
  {
    "id": 1,
    "standard_cost_id": 1,
    "change_type": "CREATE",
    "change_date": "2026-01-01",
    "new_cost": 4.50,
    "changed_by": 1,
    "changed_by_name": "管理员"
  }
]
```

#### 2.3 获取成本版本列表

**GET** `/api/v1/standard-costs/{cost_id}/versions`

获取标准成本的所有版本。

**权限:** cost:read

**响应示例:**

```json
[
  {
    "id": 2,
    "version": 2,
    "cost_code": "MAT-001",
    "cost_name": "钢板Q235",
    "standard_cost": 5.00,
    "currency": "CNY",
    "unit": "kg",
    "effective_date": "2026-02-14",
    "is_active": true,
    "created_at": "2026-02-14T11:00:00"
  },
  {
    "id": 1,
    "version": 1,
    "cost_code": "MAT-001",
    "cost_name": "钢板Q235",
    "standard_cost": 4.50,
    "currency": "CNY",
    "unit": "kg",
    "effective_date": "2026-01-01",
    "is_active": false,
    "created_at": "2026-01-01T10:00:00"
  }
]
```

### 3. 批量导入

#### 3.1 下载导入模板

**GET** `/api/v1/standard-costs/template`

下载标准成本导入模板（Excel格式）。

**权限:** cost:manage

**响应:** Excel文件下载

#### 3.2 批量导入标准成本

**POST** `/api/v1/standard-costs/import`

批量导入标准成本数据，支持Excel和CSV格式。

**权限:** cost:manage

**请求:**

- Content-Type: multipart/form-data
- 文件字段名: file
- 支持格式: .xlsx, .xls, .csv

**响应示例:**

```json
{
  "success_count": 15,
  "error_count": 2,
  "errors": [
    {
      "row": 5,
      "field": "cost_category",
      "message": "无效的成本类别：INVALID"
    },
    {
      "row": 8,
      "field": "cost_code",
      "message": "成本项编码不能为空"
    }
  ],
  "warnings": [
    {
      "row": 10,
      "cost_code": "MAT-001",
      "message": "成本编码 MAT-001 已存在，将跳过"
    }
  ]
}
```

### 4. 项目集成

#### 4.1 应用标准成本到项目预算

**POST** `/api/v1/standard-costs/projects/{project_id}/costs/apply-standard`

将标准成本应用到项目预算，自动创建预算单据。

**权限:** cost:manage

**请求体:**

```json
{
  "project_id": 1,
  "cost_items": [
    {
      "cost_code": "MAT-001",
      "quantity": 100
    },
    {
      "cost_code": "LAB-001",
      "quantity": 20
    }
  ],
  "budget_name": "基于标准成本的预算V1.0",
  "effective_date": "2026-03-01",
  "notes": "根据项目需求应用标准成本"
}
```

**响应示例:**

```json
{
  "budget_id": 123,
  "budget_no": "BUD20260214001",
  "project_id": 1,
  "total_amount": 24450.00,
  "applied_items_count": 2,
  "message": "成功应用 2 项标准成本，创建预算 BUD20260214001"
}
```

#### 4.2 项目成本对比

**GET** `/api/v1/standard-costs/projects/{project_id}/costs/compare-standard`

对比项目实际成本与标准成本的差异。

**权限:** cost:read

**查询参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| comparison_date | date | 否 | 对比日期，默认当前日期 |

**响应示例:**

```json
{
  "project_id": 1,
  "project_code": "PRJ-2026-001",
  "project_name": "智能制造系统开发",
  "comparison_date": "2026-02-14",
  "items": [
    {
      "cost_code": "MAT-001",
      "cost_name": "钢板Q235",
      "cost_category": "MATERIAL",
      "unit": "kg",
      "standard_cost": 4.50,
      "actual_cost": 4.80,
      "quantity": 100,
      "standard_total": 450.00,
      "actual_total": 480.00,
      "variance": 30.00,
      "variance_rate": 6.67
    }
  ],
  "total_standard_cost": 24450.00,
  "total_actual_cost": 25200.00,
  "total_variance": 750.00,
  "total_variance_rate": 3.07
}
```

## 错误码

| HTTP状态码 | 说明 |
|-----------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

## 数据字典

### 成本类别 (cost_category)

| 值 | 说明 |
|----|------|
| MATERIAL | 物料成本 |
| LABOR | 人工成本 |
| OVERHEAD | 制造费用 |

### 成本来源 (cost_source)

| 值 | 说明 |
|----|------|
| HISTORICAL_AVG | 历史平均 |
| INDUSTRY_STANDARD | 行业标准 |
| EXPERT_ESTIMATE | 专家估计 |
| VENDOR_QUOTE | 供应商报价 |

### 变更类型 (change_type)

| 值 | 说明 |
|----|------|
| CREATE | 创建 |
| UPDATE | 更新 |
| ACTIVATE | 激活 |
| DEACTIVATE | 停用 |

## 使用示例

### Python示例

```python
import requests

# 认证
headers = {
    "Authorization": "Bearer your_token_here"
}

# 创建标准成本
data = {
    "cost_code": "MAT-001",
    "cost_name": "钢板Q235",
    "cost_category": "MATERIAL",
    "unit": "kg",
    "standard_cost": 4.50,
    "cost_source": "HISTORICAL_AVG",
    "effective_date": "2026-01-01"
}

response = requests.post(
    "http://api.example.com/api/v1/standard-costs/",
    json=data,
    headers=headers
)

print(response.json())

# 搜索标准成本
response = requests.get(
    "http://api.example.com/api/v1/standard-costs/search",
    params={"keyword": "钢板", "cost_category": "MATERIAL"},
    headers=headers
)

print(response.json())
```

### cURL示例

```bash
# 创建标准成本
curl -X POST \
  http://api.example.com/api/v1/standard-costs/ \
  -H 'Authorization: Bearer your_token' \
  -H 'Content-Type: application/json' \
  -d '{
    "cost_code": "MAT-001",
    "cost_name": "钢板Q235",
    "cost_category": "MATERIAL",
    "unit": "kg",
    "standard_cost": 4.50,
    "cost_source": "HISTORICAL_AVG",
    "effective_date": "2026-01-01"
  }'

# 获取列表
curl -X GET \
  'http://api.example.com/api/v1/standard-costs/?page=1&page_size=20' \
  -H 'Authorization: Bearer your_token'
```

## 版本历史

- v1.0 (2026-02-14) - 初始版本
  - 基础CRUD功能
  - 批量导入功能
  - 历史记录和版本管理
  - 项目集成功能

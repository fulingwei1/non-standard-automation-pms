# 智能采购管理系统 API 使用手册

## 目录
- [一、接口概览](#一接口概览)
- [二、认证方式](#二认证方式)
- [三、采购建议管理](#三采购建议管理)
- [四、供应商绩效管理](#四供应商绩效管理)
- [五、供应商报价管理](#五供应商报价管理)
- [六、采购订单管理](#六采购订单管理)
- [七、错误码说明](#七错误码说明)
- [八、最佳实践](#八最佳实践)

---

## 一、接口概览

### 1.1 Base URL

```
https://api.example.com/api/v1/purchase
```

### 1.2 接口列表

| 编号 | 方法 | 路径 | 功能 |
|------|------|------|------|
| 1 | GET | /suggestions | 采购建议列表 |
| 2 | POST | /suggestions/{id}/approve | 批准采购建议 |
| 3 | POST | /suggestions/{id}/create-order | 建议转订单 |
| 4 | GET | /suppliers/{id}/performance | 供应商绩效 |
| 5 | POST | /suppliers/{id}/evaluate | 触发评估 |
| 6 | GET | /suppliers/ranking | 供应商排名 |
| 7 | POST | /quotations | 创建报价 |
| 8 | GET | /quotations/compare | 比价 |
| 9 | GET | /orders/{id}/tracking | 订单跟踪 |
| 10 | POST | /orders/{id}/receive | 收货确认 |

---

## 二、认证方式

### 2.1 获取 Token

```bash
POST /api/v1/auth/login

Request Body:
{
  "username": "your_username",
  "password": "your_password"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 2.2 使用 Token

在所有请求的 Header 中添加:

```
Authorization: Bearer <access_token>
```

---

## 三、采购建议管理

### 3.1 获取采购建议列表

**接口地址**: `GET /suggestions`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 状态: PENDING/APPROVED/REJECTED/ORDERED |
| source_type | string | 否 | 来源: SHORTAGE/SAFETY_STOCK/FORECAST/MANUAL |
| material_id | integer | 否 | 物料ID |
| project_id | integer | 否 | 项目ID |
| urgency_level | string | 否 | 紧急程度: LOW/NORMAL/HIGH/URGENT |
| skip | integer | 否 | 跳过数量 (分页,默认0) |
| limit | integer | 否 | 返回数量 (分页,默认20,最大100) |

**请求示例**:

```bash
curl -X GET "https://api.example.com/api/v1/purchase/suggestions?status=PENDING&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**:

```json
[
  {
    "id": 1,
    "suggestion_no": "PS20260216001",
    "material_id": 123,
    "material_code": "MAT001",
    "material_name": "电容器 100uF",
    "specification": "16V 贴片",
    "unit": "个",
    "suggested_qty": 500,
    "current_stock": 100,
    "safety_stock": 300,
    "source_type": "SAFETY_STOCK",
    "urgency_level": "NORMAL",
    "suggested_supplier_id": 5,
    "suggested_supplier_name": "深圳XX电子",
    "ai_confidence": 85.50,
    "recommendation_reason": {
      "total_score": 85.5,
      "performance_score": 92.0,
      "price_score": 80.0,
      "delivery_score": 85.0,
      "history_score": 85.0
    },
    "estimated_unit_price": 0.95,
    "estimated_total_amount": 475.00,
    "status": "PENDING",
    "created_at": "2026-02-16T10:30:00",
    "updated_at": "2026-02-16T10:30:00"
  }
]
```

### 3.2 批准采购建议

**接口地址**: `POST /suggestions/{id}/approve`

**Path 参数**:
- `id`: 建议ID

**Request Body**:

```json
{
  "approved": true,
  "review_note": "批准,按建议执行",
  "suggested_supplier_id": 5  // 可选,修改推荐供应商
}
```

**请求示例**:

```bash
curl -X POST "https://api.example.com/api/v1/purchase/suggestions/1/approve" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "approved": true,
    "review_note": "批准"
  }'
```

**响应示例**:

```json
{
  "message": "采购建议已批准",
  "data": {
    "suggestion_id": 1
  }
}
```

### 3.3 建议转订单

**接口地址**: `POST /suggestions/{id}/create-order`

**Path 参数**:
- `id`: 建议ID

**Request Body**:

```json
{
  "supplier_id": 5,  // 可选,不传则使用建议的供应商
  "required_date": "2026-02-20",  // 可选
  "payment_terms": "月结30天",
  "delivery_address": "深圳市XX区XX路XX号",
  "remark": "请按时交货"
}
```

**请求示例**:

```bash
curl -X POST "https://api.example.com/api/v1/purchase/suggestions/1/create-order" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "required_date": "2026-02-20",
    "payment_terms": "月结30天"
  }'
```

**响应示例**:

```json
{
  "message": "采购订单创建成功",
  "data": {
    "order_id": 123,
    "order_no": "PO20260216001"
  }
}
```

---

## 四、供应商绩效管理

### 4.1 获取供应商绩效

**接口地址**: `GET /suppliers/{id}/performance`

**Path 参数**:
- `id`: 供应商ID

**Query 参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| evaluation_period | string | 否 | 评估期间 (YYYY-MM) |
| limit | integer | 否 | 返回记录数 (默认12) |

**请求示例**:

```bash
curl -X GET "https://api.example.com/api/v1/purchase/suppliers/5/performance?evaluation_period=2026-01" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**:

```json
[
  {
    "id": 1,
    "supplier_id": 5,
    "supplier_code": "SUP001",
    "supplier_name": "深圳XX电子",
    "evaluation_period": "2026-01",
    "period_start": "2026-01-01",
    "period_end": "2026-01-31",
    "total_orders": 20,
    "total_amount": 50000.00,
    "on_time_delivery_rate": 95.00,
    "on_time_orders": 19,
    "late_orders": 1,
    "avg_delay_days": 1.00,
    "quality_pass_rate": 98.50,
    "total_received_qty": 10000,
    "qualified_qty": 9850,
    "rejected_qty": 150,
    "price_competitiveness": 85.00,
    "avg_price_vs_market": -5.00,
    "response_speed_score": 90.00,
    "avg_response_hours": 6.00,
    "overall_score": 92.50,
    "rating": "A+",
    "weight_config": {
      "on_time_delivery": 30,
      "quality": 30,
      "price": 20,
      "response": 20
    },
    "status": "PUBLISHED",
    "created_at": "2026-02-01T00:00:00",
    "updated_at": "2026-02-01T00:00:00"
  }
]
```

### 4.2 触发供应商评估

**接口地址**: `POST /suppliers/{id}/evaluate`

**Path 参数**:
- `id`: 供应商ID

**Request Body**:

```json
{
  "supplier_id": 5,
  "evaluation_period": "2026-01",
  "weight_config": {
    "on_time_delivery": 30,
    "quality": 30,
    "price": 20,
    "response": 20
  }
}
```

**请求示例**:

```bash
curl -X POST "https://api.example.com/api/v1/purchase/suppliers/5/evaluate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_id": 5,
    "evaluation_period": "2026-01"
  }'
```

**响应示例**:

```json
{
  "id": 1,
  "supplier_id": 5,
  "supplier_code": "SUP001",
  "supplier_name": "深圳XX电子",
  "evaluation_period": "2026-01",
  "overall_score": 92.50,
  "rating": "A+",
  ...
}
```

### 4.3 供应商排名

**接口地址**: `GET /suppliers/ranking`

**Query 参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| evaluation_period | string | 是 | 评估期间 (YYYY-MM) |
| limit | integer | 否 | 返回数量 (默认20) |

**请求示例**:

```bash
curl -X GET "https://api.example.com/api/v1/purchase/suppliers/ranking?evaluation_period=2026-01&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**:

```json
{
  "evaluation_period": "2026-01",
  "total_suppliers": 10,
  "rankings": [
    {
      "supplier_id": 5,
      "supplier_code": "SUP001",
      "supplier_name": "深圳XX电子",
      "overall_score": 92.50,
      "rating": "A+",
      "on_time_delivery_rate": 95.00,
      "quality_pass_rate": 98.50,
      "price_competitiveness": 85.00,
      "response_speed_score": 90.00,
      "total_orders": 20,
      "total_amount": 50000.00,
      "evaluation_period": "2026-01",
      "rank": 1
    },
    {
      "supplier_id": 8,
      "supplier_code": "SUP002",
      "supplier_name": "广州YY科技",
      "overall_score": 88.00,
      "rating": "A",
      "rank": 2,
      ...
    }
  ]
}
```

---

## 五、供应商报价管理

### 5.1 创建供应商报价

**接口地址**: `POST /quotations`

**Request Body**:

```json
{
  "supplier_id": 5,
  "material_id": 123,
  "unit_price": 0.92,
  "currency": "CNY",
  "min_order_qty": 100,
  "lead_time_days": 7,
  "valid_from": "2026-02-16",
  "valid_to": "2026-05-16",
  "payment_terms": "月结30天",
  "warranty_period": "12个月",
  "tax_rate": 13,
  "remark": "批量订购可优惠"
}
```

**请求示例**:

```bash
curl -X POST "https://api.example.com/api/v1/purchase/quotations" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_id": 5,
    "material_id": 123,
    "unit_price": 0.92,
    "valid_from": "2026-02-16",
    "valid_to": "2026-05-16"
  }'
```

**响应示例**:

```json
{
  "id": 1,
  "quotation_no": "QT20260216001",
  "supplier_id": 5,
  "supplier_code": "SUP001",
  "supplier_name": "深圳XX电子",
  "material_id": 123,
  "material_code": "MAT001",
  "material_name": "电容器 100uF",
  "unit_price": 0.92,
  "currency": "CNY",
  "min_order_qty": 100,
  "lead_time_days": 7,
  "valid_from": "2026-02-16",
  "valid_to": "2026-05-16",
  "status": "ACTIVE",
  "created_at": "2026-02-16T10:30:00"
}
```

### 5.2 比价

**接口地址**: `GET /quotations/compare`

**Query 参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| material_id | integer | 是 | 物料ID |
| supplier_ids | string | 否 | 供应商ID列表 (逗号分隔) |

**请求示例**:

```bash
curl -X GET "https://api.example.com/api/v1/purchase/quotations/compare?material_id=123&supplier_ids=5,8,12" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**:

```json
{
  "material_id": 123,
  "material_code": "MAT001",
  "material_name": "电容器 100uF",
  "quotations": [
    {
      "quotation_id": 1,
      "quotation_no": "QT20260216001",
      "supplier_id": 5,
      "supplier_code": "SUP001",
      "supplier_name": "深圳XX电子",
      "unit_price": 0.92,
      "currency": "CNY",
      "min_order_qty": 100,
      "lead_time_days": 7,
      "valid_from": "2026-02-16",
      "valid_to": "2026-05-16",
      "payment_terms": "月结30天",
      "tax_rate": 13,
      "is_selected": false,
      "performance_score": 92.50,
      "performance_rating": "A+"
    },
    {
      "quotation_id": 2,
      "quotation_no": "QT20260216002",
      "supplier_id": 8,
      "supplier_code": "SUP002",
      "supplier_name": "广州YY科技",
      "unit_price": 0.89,  // 最低价
      "min_order_qty": 200,
      "lead_time_days": 10,
      "performance_score": 85.00,
      "performance_rating": "A",
      ...
    }
  ],
  "best_price_supplier_id": 8,
  "recommended_supplier_id": 5,
  "recommendation_reason": "基于价格和供应商绩效综合评估推荐"
}
```

---

## 六、采购订单管理

### 6.1 订单跟踪

**接口地址**: `GET /orders/{id}/tracking`

**Path 参数**:
- `id`: 订单ID

**请求示例**:

```bash
curl -X GET "https://api.example.com/api/v1/purchase/orders/123/tracking" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**:

```json
[
  {
    "id": 5,
    "order_id": 123,
    "order_no": "PO20260216001",
    "event_type": "RECEIVED",
    "event_time": "2026-02-20T14:30:00",
    "event_description": "收货确认,收货单号:GR20260220001",
    "old_status": "SHIPPED",
    "new_status": "RECEIVED",
    "tracking_no": "SF1234567890",
    "logistics_company": "顺丰速运",
    "operator_id": 10,
    "operator_name": "张三",
    "created_at": "2026-02-20T14:30:00"
  },
  {
    "id": 4,
    "order_id": 123,
    "order_no": "PO20260216001",
    "event_type": "SHIPPED",
    "event_time": "2026-02-18T10:00:00",
    "event_description": "供应商已发货",
    "old_status": "CONFIRMED",
    "new_status": "SHIPPED",
    "tracking_no": "SF1234567890",
    "estimated_arrival": "2026-02-20",
    "operator_name": "供应商系统",
    "created_at": "2026-02-18T10:00:00"
  },
  ...
]
```

### 6.2 收货确认

**接口地址**: `POST /orders/{id}/receive`

**Path 参数**:
- `id`: 订单ID

**Request Body**:

```json
{
  "receipt_date": "2026-02-20",
  "delivery_note_no": "DN20260220001",
  "logistics_company": "顺丰速运",
  "tracking_no": "SF1234567890",
  "items": [
    {
      "order_item_id": 1,
      "delivery_qty": 500,
      "received_qty": 500,
      "remark": "外观良好"
    }
  ],
  "remark": "收货正常"
}
```

**请求示例**:

```bash
curl -X POST "https://api.example.com/api/v1/purchase/orders/123/receive" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "receipt_date": "2026-02-20",
    "items": [
      {
        "order_item_id": 1,
        "delivery_qty": 500,
        "received_qty": 500
      }
    ]
  }'
```

**响应示例**:

```json
{
  "message": "收货确认成功",
  "data": {
    "receipt_id": 45,
    "receipt_no": "GR20260220001"
  }
}
```

---

## 七、错误码说明

### 7.1 HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 (Token无效) |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 7.2 业务错误码

```json
{
  "detail": "采购建议不存在",
  "error_code": "SUGGESTION_NOT_FOUND"
}
```

| 错误码 | 说明 |
|--------|------|
| SUGGESTION_NOT_FOUND | 采购建议不存在 |
| INVALID_STATUS | 状态不允许操作 |
| SUPPLIER_NOT_FOUND | 供应商不存在 |
| MATERIAL_NOT_FOUND | 物料不存在 |
| ORDER_NOT_FOUND | 订单不存在 |
| INVALID_PERIOD_FORMAT | 评估期间格式错误 |
| DUPLICATE_QUOTATION | 报价已存在 |

---

## 八、最佳实践

### 8.1 分页查询

```python
import requests

def get_all_suggestions(token):
    """获取所有采购建议 (分页)"""
    base_url = "https://api.example.com/api/v1/purchase/suggestions"
    headers = {"Authorization": f"Bearer {token}"}
    
    all_suggestions = []
    skip = 0
    limit = 50
    
    while True:
        response = requests.get(
            f"{base_url}?skip={skip}&limit={limit}",
            headers=headers
        )
        
        data = response.json()
        if not data:
            break
        
        all_suggestions.extend(data)
        skip += limit
    
    return all_suggestions
```

### 8.2 批量评估供应商

```python
def batch_evaluate_suppliers(token, evaluation_period, supplier_ids):
    """批量评估供应商"""
    base_url = "https://api.example.com/api/v1/purchase/suppliers"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    results = []
    for supplier_id in supplier_ids:
        response = requests.post(
            f"{base_url}/{supplier_id}/evaluate",
            headers=headers,
            json={
                "supplier_id": supplier_id,
                "evaluation_period": evaluation_period
            }
        )
        
        if response.status_code == 200:
            results.append(response.json())
        else:
            print(f"Supplier {supplier_id} evaluation failed: {response.text}")
    
    return results
```

### 8.3 自动生成建议并转订单

```python
def auto_purchase_workflow(token, material_id, supplier_id):
    """自动采购工作流"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 1. 查询物料的采购建议
    suggestions = requests.get(
        f"https://api.example.com/api/v1/purchase/suggestions?material_id={material_id}&status=PENDING",
        headers=headers
    ).json()
    
    if not suggestions:
        print("No pending suggestions")
        return
    
    suggestion = suggestions[0]
    
    # 2. 批准建议
    requests.post(
        f"https://api.example.com/api/v1/purchase/suggestions/{suggestion['id']}/approve",
        headers=headers,
        json={"approved": True}
    )
    
    # 3. 转为订单
    order_response = requests.post(
        f"https://api.example.com/api/v1/purchase/suggestions/{suggestion['id']}/create-order",
        headers=headers,
        json={
            "supplier_id": supplier_id,
            "required_date": "2026-02-28"
        }
    )
    
    order_data = order_response.json()
    print(f"Order created: {order_data['data']['order_no']}")
    
    return order_data
```

### 8.4 错误处理

```python
def safe_api_call(url, method="GET", **kwargs):
    """带错误处理的API调用"""
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {e.response.text}")
        return None
    except requests.exceptions.ConnectionError:
        print("Connection Error")
        return None
    except requests.exceptions.Timeout:
        print("Request Timeout")
        return None
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return None
```

### 8.5 定时任务集成

```python
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()

@scheduler.scheduled_job('cron', day='1', hour='0', minute='0')
def monthly_supplier_evaluation():
    """每月自动评估所有供应商"""
    from datetime import datetime
    
    # 评估上个月
    last_month = datetime.now().replace(day=1) - timedelta(days=1)
    period = last_month.strftime('%Y-%m')
    
    # 获取所有供应商
    suppliers = get_all_suppliers(token)
    
    # 批量评估
    results = batch_evaluate_suppliers(
        token,
        period,
        [s['id'] for s in suppliers]
    )
    
    print(f"Evaluated {len(results)} suppliers for period {period}")

scheduler.start()
```

---

## 九、SDK 示例 (Python)

```python
class PurchaseIntelligenceClient:
    """智能采购管理 SDK"""
    
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def get_suggestions(self, **filters):
        """获取采购建议列表"""
        url = f"{self.base_url}/suggestions"
        response = requests.get(url, headers=self.headers, params=filters)
        return response.json()
    
    def approve_suggestion(self, suggestion_id, approved, note=None):
        """批准采购建议"""
        url = f"{self.base_url}/suggestions/{suggestion_id}/approve"
        data = {"approved": approved, "review_note": note}
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
    def get_supplier_performance(self, supplier_id, period=None):
        """获取供应商绩效"""
        url = f"{self.base_url}/suppliers/{supplier_id}/performance"
        params = {"evaluation_period": period} if period else {}
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    
    def compare_quotations(self, material_id, supplier_ids=None):
        """比价"""
        url = f"{self.base_url}/quotations/compare"
        params = {"material_id": material_id}
        if supplier_ids:
            params["supplier_ids"] = ",".join(map(str, supplier_ids))
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()

# 使用示例
client = PurchaseIntelligenceClient(
    base_url="https://api.example.com/api/v1/purchase",
    token="YOUR_TOKEN"
)

# 获取待审批建议
suggestions = client.get_suggestions(status="PENDING")

# 批准第一个建议
if suggestions:
    result = client.approve_suggestion(
        suggestion_id=suggestions[0]['id'],
        approved=True,
        note="批准采购"
    )
```

---

**文档版本**: v1.0  
**最后更新**: 2026-02-16  
**技术支持**: dev@example.com

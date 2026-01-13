# 采购订单管理 API 实现总结

## 概述

本文档总结了采购订单管理和收货管理功能的 API 实现情况。

## 实现时间

2025-01-XX

## 1. 采购订单管理 API (`/api/v1/purchase-orders`)

### 已实现的端点

1. **GET `/purchase-orders`** - 获取采购订单列表（支持分页、搜索、筛选）
   - 分页参数：`page`, `page_size`
   - 搜索参数：`keyword`（订单编号/标题）
   - 筛选参数：`supplier_id`, `project_id`, `status`, `payment_status`
   - 返回：`PaginatedResponse[PurchaseOrderListResponse]`

2. **GET `/purchase-orders/{order_id}`** - 获取采购订单详情
   - 返回：`PurchaseOrderResponse`（包含明细列表）

3. **POST `/purchase-orders`** - 创建采购订单
   - 请求体：`PurchaseOrderCreate`（包含明细列表）
   - 返回：`PurchaseOrderResponse`
   - 特性：
     - ✅ 自动生成订单编号（PO-yymmdd-xxx）
     - ✅ 自动计算总金额、税额、含税金额
     - ✅ 验证供应商和项目存在性

4. **PUT `/purchase-orders/{order_id}`** - 更新采购订单
   - 请求体：`PurchaseOrderUpdate`
   - 返回：`PurchaseOrderResponse`
   - 特性：
     - ✅ 只有草稿状态才能更新

5. **PUT `/purchase-orders/{order_id}/submit`** - 提交采购订单
   - 返回：`ResponseModel`
   - 特性：
     - ✅ 只有草稿状态才能提交
     - ✅ 检查是否有明细
     - ✅ 自动设置提交时间

6. **PUT `/purchase-orders/{order_id}/approve`** - 审批采购订单
   - 查询参数：`approved`（是否审批通过），`approval_note`（审批意见）
   - 返回：`ResponseModel`
   - 特性：
     - ✅ 只有已提交状态才能审批
     - ✅ 支持通过和驳回
     - ✅ 记录审批人和审批时间

7. **GET `/purchase-orders/{order_id}/items`** - 获取采购订单明细列表
   - 返回：`List[PurchaseOrderItemResponse]`

8. **PUT `/purchase-order-items/{item_id}/receive`** - 更新采购订单明细的到货状态
   - 查询参数：`received_qty`（已收货数量），`qualified_qty`（合格数量，可选）
   - 返回：`ResponseModel`
   - 特性：
     - ✅ 自动更新状态（PENDING/PARTIAL_RECEIVED/RECEIVED）
     - ✅ 自动计算不合格数量

### 特性

- ✅ 订单编号自动生成（PO-yymmdd-xxx）
- ✅ 自动计算总金额、税额、含税金额
- ✅ 状态控制（草稿→提交→审批→已下单）
- ✅ 明细行号自动管理
- ✅ 认证和权限检查（采购权限）

## 2. 从BOM生成采购需求 API

**端点**: `POST /api/v1/bom/{bom_id}/generate-pr`

**功能**:
- 从BOM明细中提取需要采购的物料
- 按供应商分组物料
- 生成采购需求清单

**请求参数**:
- `bom_id`: BOM ID（路径参数）
- `supplier_id`: 默认供应商ID（查询参数，可选）

**响应**: `ResponseModel`

**响应数据**:
```json
{
  "code": 200,
  "message": "已生成采购需求，共2个供应商",
  "data": {
    "bom_id": 1,
    "bom_no": "BOM-PJ202501-001",
    "project_id": 1,
    "machine_id": 1,
    "purchase_requests": [
      {
        "supplier_id": 1,
        "supplier_name": "供应商A",
        "items": [
          {
            "bom_item_id": 1,
            "material_id": 1,
            "material_code": "MAT-001",
            "material_name": "物料1",
            "quantity": 10,
            "unit_price": 5.0,
            "amount": 50.0,
            "required_date": "2025-02-01",
            "is_key_item": false
          }
        ],
        "total_amount": 50.0,
        "item_count": 1
      }
    ],
    "summary": {
      "total_suppliers": 2,
      "total_items": 5,
      "total_amount": 500.0
    }
  }
}
```

**业务规则**:
- ✅ 只提取来源类型为 `PURCHASE` 的物料
- ✅ 计算未采购数量（数量 - 已采购数量）
- ✅ 按供应商分组（从BOM明细、物料默认供应商获取）
- ✅ 跳过已完全采购的物料

## 3. 收货管理 API (`/api/v1/purchase-orders/goods-receipts`)

### 已实现的端点

1. **GET `/goods-receipts`** - 获取收货记录列表（支持分页、搜索、筛选）
   - 分页参数：`page`, `page_size`
   - 搜索参数：`keyword`（收货单号/送货单号）
   - 筛选参数：`order_id`, `supplier_id`, `status`, `inspect_status`
   - 返回：`PaginatedResponse`

2. **POST `/goods-receipts`** - 创建收货单
   - 请求体：`GoodsReceiptCreate`（包含明细列表）
   - 返回：`GoodsReceiptResponse`
   - 特性：
     - ✅ 自动生成收货单编号（GR-yymmdd-xxx）
     - ✅ 自动更新订单明细的已收货数量
     - ✅ 自动更新订单明细状态
     - ✅ 自动更新采购订单的已收货金额

3. **GET `/goods-receipts/{receipt_id}`** - 获取收货单详情
   - 返回：`GoodsReceiptResponse`（包含明细列表）

4. **GET `/goods-receipts/{receipt_id}/items`** - 获取收货单明细列表
   - 返回：`List[GoodsReceiptItemResponse]`

5. **PUT `/goods-receipts/{receipt_id}/receive`** - 更新收货单状态
   - 查询参数：`status`（PENDING/RECEIVED/REJECTED）
   - 返回：`ResponseModel`

### 特性

- ✅ 收货单编号自动生成（GR-yymmdd-xxx）
- ✅ 自动更新订单明细的收货状态
- ✅ 收货数量验证（不能超过订单数量）
- ✅ 自动计算已收货金额

## 4. Schema 定义

### 4.1 采购订单相关

- `PurchaseOrderCreate` - 创建采购订单（包含明细列表）
- `PurchaseOrderUpdate` - 更新采购订单
- `PurchaseOrderResponse` - 采购订单响应（包含明细列表）
- `PurchaseOrderListResponse` - 采购订单列表响应
- `PurchaseOrderItemCreate` - 创建采购订单明细
- `PurchaseOrderItemResponse` - 采购订单明细响应

### 4.2 收货单相关

- `GoodsReceiptCreate` - 创建收货单（包含明细列表）
- `GoodsReceiptResponse` - 收货单响应（包含明细列表）
- `GoodsReceiptItemResponse` - 收货单明细响应

## 5. 实现特性

### 5.1 自动计算

- ✅ 采购订单总金额、税额、含税金额自动计算
- ✅ 订单明细金额自动计算
- ✅ 收货单自动更新订单明细状态

### 5.2 状态管理

- ✅ 采购订单状态流转：DRAFT → SUBMITTED → APPROVED/REJECTED → ORDERED → ...
- ✅ 订单明细状态：PENDING → PARTIAL_RECEIVED → RECEIVED
- ✅ 收货单状态：PENDING → RECEIVED/REJECTED

### 5.3 数据验证

- ✅ 供应商和项目存在性验证
- ✅ 收货数量验证（不能超过订单数量）
- ✅ 合格数量验证（不能超过收货数量）
- ✅ 状态流转验证

## 6. 安全特性

- ✅ JWT 认证（所有端点）
- ✅ 采购权限检查（`require_procurement_access`）
- ✅ 数据验证

## 7. 错误处理

- ✅ 404：订单/明细/收货单不存在
- ✅ 400：状态不允许操作、数量验证失败
- ✅ 401：未认证
- ✅ 403：无权限

## 8. 使用示例

### 8.1 创建采购订单

```bash
POST /api/v1/purchase-orders
Content-Type: application/json

{
  "supplier_id": 1,
  "project_id": 1,
  "order_title": "项目1采购订单",
  "required_date": "2025-02-01",
  "items": [
    {
      "material_id": 1,
      "material_code": "MAT-001",
      "material_name": "物料1",
      "quantity": 10,
      "unit_price": 5.0,
      "tax_rate": 13,
      "unit": "件"
    }
  ]
}
```

### 8.2 提交采购订单

```bash
PUT /api/v1/purchase-orders/1/submit
```

### 8.3 审批采购订单

```bash
PUT /api/v1/purchase-orders/1/approve?approved=true&approval_note=审批通过
```

### 8.4 从BOM生成采购需求

```bash
POST /api/v1/bom/1/generate-pr?supplier_id=1
```

**响应**: 采购需求清单（按供应商分组）

### 8.5 创建收货单

```bash
POST /api/v1/purchase-orders/goods-receipts
Content-Type: application/json

{
  "order_id": 1,
  "receipt_date": "2025-01-20",
  "delivery_note_no": "DN-001",
  "items": [
    {
      "order_item_id": 1,
      "delivery_qty": 10,
      "received_qty": 10
    }
  ]
}
```

## 9. 后续优化建议

1. **批量操作**:
   - 批量创建采购订单
   - 批量审批
   - 批量收货

2. **采购订单状态流转优化**:
   - 添加更多状态（如部分到货、已取消等）
   - 状态流转历史记录

3. **从BOM生成采购需求优化**:
   - 支持直接创建采购订单
   - 支持合并多个BOM的采购需求
   - 支持按项目汇总采购需求

4. **收货管理优化**:
   - 支持质检流程
   - 支持入库管理
   - 支持退货处理

5. **价格管理**:
   - 历史价格记录
   - 价格对比分析
   - 价格预警

6. **交期管理**:
   - 交期预警
   - 交期统计分析
   - 供应商交期评估

## 10. 相关文件

- `app/api/v1/endpoints/purchase.py` - 采购订单和收货管理API实现
- `app/api/v1/endpoints/bom.py` - BOM管理API（包含生成采购需求）
- `app/models/purchase.py` - 采购订单和收货单模型定义
- `app/schemas/purchase.py` - 采购相关Schema定义
- `app/core/security.py` - 权限检查（`require_procurement_access`）




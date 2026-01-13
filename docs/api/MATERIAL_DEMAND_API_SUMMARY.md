# 物料需求计划 API 实现总结

## 概述

本文档总结了物料需求计划(MRP)功能的 API 实现情况。

## 实现时间

2025-01-XX

## 1. 物料需求汇总 API

**端点**: `GET /material-demands`

**功能**:
- 从BOM明细汇总物料需求（多项目汇总）
- 支持分页、筛选
- 计算可用库存、在途数量、短缺数量

**请求参数**:
- `page`: 页码（查询参数，默认1）
- `page_size`: 每页数量（查询参数，默认20）
- `material_id`: 物料ID筛选（查询参数，可选）
- `material_code`: 物料编码筛选（查询参数，可选）
- `project_id`: 项目ID筛选（查询参数，可选）
- `start_date`: 需求开始日期（查询参数，可选）
- `end_date`: 需求结束日期（查询参数，可选）

**响应**: `PaginatedResponse`

**响应数据**:
```json
{
  "items": [
    {
      "material_id": 1,
      "material_code": "MAT-001",
      "material_name": "物料1",
      "specification": "规格1",
      "unit": "件",
      "total_demand": 100.0,
      "available_stock": 50.0,
      "in_transit_qty": 20.0,
      "total_available": 70.0,
      "shortage_qty": 30.0,
      "earliest_date": "2025-02-01",
      "latest_date": "2025-02-15",
      "demand_count": 5,
      "is_key_material": false
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

**计算逻辑**:
- 总需求 = 所有BOM明细中该物料的数量总和
- 可用库存 = 当前库存 + 在途数量
- 短缺数量 = max(0, 总需求 - 可用库存)
- 按短缺数量降序排序

## 2. 需求与库存对比 API

**端点**: `GET /material-demands/vs-stock`

**功能**:
- 对比物料需求与库存
- 考虑安全库存
- 计算库存状态

**请求参数**:
- `project_ids`: 项目ID列表（查询参数，可选，逗号分隔）
- `material_ids`: 物料ID列表（查询参数，可选，逗号分隔）

**响应**: `List[dict]`

**响应数据**:
```json
[
  {
    "material_id": 1,
    "material_code": "MAT-001",
    "material_name": "物料1",
    "specification": "规格1",
    "unit": "件",
    "total_demand": 100.0,
    "current_stock": 50.0,
    "safety_stock": 10.0,
    "in_transit_qty": 20.0,
    "available_stock": 60.0,
    "shortage_qty": 40.0,
    "stock_status": "INSUFFICIENT",
    "is_key_material": true,
    "lead_time_days": 7
  }
]
```

**库存状态**:
- `SUFFICIENT`: 库存充足
- `INSUFFICIENT`: 库存不足（短缺数量 <= 总需求的50%）
- `CRITICAL`: 库存严重不足（短缺数量 > 总需求的50%）

**计算逻辑**:
- 可用库存 = 当前库存 + 在途数量 - 安全库存
- 短缺数量 = max(0, 总需求 - 可用库存)
- 按关键物料和短缺数量排序

## 3. 自动生成采购需求 API

**端点**: `POST /material-demands/generate-pr`

**功能**:
- 从物料缺口自动生成采购需求
- 考虑最小订购量
- 自动匹配供应商

**请求参数**:
- `project_ids`: 项目ID列表（查询参数，可选，逗号分隔）
- `material_ids`: 物料ID列表（查询参数，可选，逗号分隔，为空则生成所有短缺物料）
- `supplier_id`: 默认供应商ID（查询参数，可选）

**响应**: `ResponseModel`

**响应数据**:
```json
{
  "code": 200,
  "message": "成功生成 10 条采购需求",
  "data": {
    "count": 10,
    "items": [
      {
        "material_id": 1,
        "material_code": "MAT-001",
        "material_name": "物料1",
        "quantity": 50.0,
        "unit": "件",
        "unit_price": 10.0,
        "required_date": "2025-02-01",
        "supplier_id": 1
      }
    ]
  }
}
```

**业务规则**:
- ✅ 只生成短缺数量 > 0 的物料
- ✅ 考虑最小订购量（purchase_qty = max(shortage_qty, min_order_qty)）
- ✅ 自动匹配供应商（优先使用默认供应商，其次使用物料默认供应商）
- ✅ 跳过没有供应商的物料
- ✅ 使用历史价格或标准价格作为单价

## 4. 需求时间表 API

**端点**: `GET /material-demands/schedule`

**功能**:
- 按日期分组显示物料需求
- 支持按天/周/月分组

**请求参数**:
- `project_ids`: 项目ID列表（查询参数，可选，逗号分隔）
- `start_date`: 开始日期（查询参数，可选，默认今天）
- `end_date`: 结束日期（查询参数，可选，默认30天后）
- `group_by`: 分组方式（查询参数，可选，默认"day"）
  - `day`: 按天分组
  - `week`: 按周分组（使用该周的周一作为日期）
  - `month`: 按月分组（使用该月的第一天作为日期）

**响应**: `List[dict]`

**响应数据**:
```json
[
  {
    "date": "2025-02-01",
    "materials": [
      {
        "material_id": 1,
        "material_code": "MAT-001",
        "material_name": "物料1",
        "demand_qty": 10.0
      },
      {
        "material_id": 2,
        "material_code": "MAT-002",
        "material_name": "物料2",
        "demand_qty": 20.0
      }
    ],
    "total_materials": 2,
    "total_demand": 30.0
  },
  {
    "date": "2025-02-02",
    "materials": [...],
    "total_materials": 3,
    "total_demand": 50.0
  }
]
```

**分组逻辑**:
- **按天**: 使用BOM明细的`required_date`
- **按周**: 使用该周的周一作为分组键
- **按月**: 使用该月的第一天作为分组键

## 5. 物料交期预测 API

**端点**: `GET /materials/{material_id}/lead-time-forecast`

**功能**:
- 基于历史采购订单数据预测物料交期
- 计算平均交期、最短交期、最长交期
- 提供建议交期

**请求参数**:
- `material_id`: 物料ID（路径参数）
- `days`: 统计天数（查询参数，可选，默认90天）

**响应**: `dict`

**响应数据**:
```json
{
  "material_id": 1,
  "material_code": "MAT-001",
  "material_name": "物料1",
  "standard_lead_time": 7,
  "historical_count": 10,
  "forecast_avg_lead_time": 8.5,
  "forecast_min_lead_time": 5.0,
  "forecast_max_lead_time": 12.0,
  "recommended_lead_time": 10.5
}
```

**计算逻辑**:
- 查询过去N天内的采购订单到货记录
- 计算订单日期到收货日期的天数差
- 平均交期 = 所有历史交期的平均值
- 最短交期 = 历史交期的最小值
- 最长交期 = 历史交期的最大值
- 建议交期 = 平均交期 + 2天缓冲

**如果没有历史数据**:
- 使用物料的标准交期（`lead_time_days`）
- 平均交期 = 标准交期
- 最短交期 = 标准交期 - 2天
- 最长交期 = 标准交期 + 5天

## 6. 实现特性

### 6.1 数据汇总

- ✅ 多项目物料需求汇总
- ✅ 按物料分组统计
- ✅ 考虑在途数量
- ✅ 计算短缺数量

### 6.2 库存对比

- ✅ 需求与库存对比
- ✅ 考虑安全库存
- ✅ 库存状态判断
- ✅ 关键物料标识

### 6.3 采购需求生成

- ✅ 自动识别短缺物料
- ✅ 考虑最小订购量
- ✅ 自动匹配供应商
- ✅ 使用历史价格

### 6.4 时间表分析

- ✅ 按日期分组需求
- ✅ 支持多种分组方式
- ✅ 需求汇总统计

### 6.5 交期预测

- ✅ 基于历史数据预测
- ✅ 统计分析（平均/最短/最长）
- ✅ 建议交期计算

## 7. 使用示例

### 7.1 获取物料需求汇总

```bash
GET /api/v1/material-demands?project_id=1&page=1&page_size=20
```

### 7.2 需求与库存对比

```bash
GET /api/v1/material-demands/vs-stock?project_ids=1,2,3
```

### 7.3 生成采购需求

```bash
POST /api/v1/material-demands/generate-pr?project_ids=1,2&supplier_id=1
```

### 7.4 获取需求时间表

```bash
GET /api/v1/material-demands/schedule?project_ids=1,2&start_date=2025-02-01&end_date=2025-02-28&group_by=week
```

### 7.5 物料交期预测

```bash
GET /api/v1/materials/1/lead-time-forecast?days=90
```

## 8. 后续优化建议

1. **需求预测优化**:
   - 支持基于历史需求趋势预测未来需求
   - 支持季节性需求预测
   - 支持需求波动分析

2. **采购需求生成优化**:
   - 支持批量创建采购订单
   - 支持采购需求审批流程
   - 支持采购需求合并（同一供应商）

3. **交期预测优化**:
   - 考虑供应商交期历史
   - 考虑物料类型和复杂度
   - 支持交期预警

4. **库存优化**:
   - 支持安全库存自动计算
   - 支持库存周转率分析
   - 支持库存成本分析

5. **集成优化**:
   - 与采购订单系统集成
   - 与库存管理系统集成
   - 与供应商管理系统集成

## 9. 相关文件

- `app/api/v1/endpoints/material_demands.py` - 物料需求计划API实现
- `app/models/material.py` - Material模型定义
- `app/models/purchase.py` - PurchaseOrder, PurchaseOrderItem模型定义
- `app/core/security.py` - 权限检查（`require_procurement_access`）




# 项目成本管理 API 实现总结

## 概述

本文档总结了项目成本管理功能的 API 实现情况。

## 实现时间

2025-01-XX

## 1. API 端点

### 1.1 成本记录列表

**端点**: `GET /api/v1/costs`

**功能**:
- 获取成本记录列表（支持分页、筛选）
- 支持多条件筛选

**请求参数**:
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20，最大100）
- `project_id`: 项目ID筛选（可选）
- `machine_id`: 机台ID筛选（可选）
- `cost_type`: 成本类型筛选（可选）
- `cost_category`: 成本分类筛选（可选）
- `start_date`: 开始日期筛选（可选，YYYY-MM-DD格式）
- `end_date`: 结束日期筛选（可选，YYYY-MM-DD格式）

**响应**: `PaginatedResponse[ProjectCostResponse]`

### 1.2 项目成本列表

**端点**: `GET /api/v1/costs/projects/{project_id}/costs`

**功能**:
- 获取指定项目的成本记录列表
- 支持按机台和成本类型筛选

**请求参数**:
- `project_id`: 项目ID（路径参数）
- `machine_id`: 机台ID筛选（查询参数，可选）
- `cost_type`: 成本类型筛选（查询参数，可选）

**响应**: `List[ProjectCostResponse]`

### 1.3 创建成本记录

**端点**: `POST /api/v1/costs`

**功能**:
- 创建新的成本记录
- 自动更新项目的实际成本
- 验证机台是否属于项目

**请求体**: `ProjectCostCreate`

**响应**: `ProjectCostResponse`

**特性**:
- ✅ 自动设置创建人
- ✅ 验证项目存在性
- ✅ 验证机台归属（如果指定了机台）
- ✅ 自动更新项目实际成本

### 1.4 为项目创建成本记录

**端点**: `POST /api/v1/costs/projects/{project_id}/costs`

**功能**:
- 为指定项目创建成本记录
- 自动确保project_id一致

**请求参数**:
- `project_id`: 项目ID（路径参数）

**请求体**: `ProjectCostCreate`

**响应**: `ProjectCostResponse`

### 1.5 获取成本记录详情

**端点**: `GET /api/v1/costs/{cost_id}`

**功能**:
- 获取成本记录详情

**响应**: `ProjectCostResponse`

### 1.6 更新成本记录

**端点**: `PUT /api/v1/costs/{cost_id}`

**功能**:
- 更新成本记录
- 自动更新项目的实际成本（减去旧金额，加上新金额）

**请求体**: `ProjectCostUpdate`

**响应**: `ProjectCostResponse`

**特性**:
- ✅ 支持部分更新
- ✅ 自动更新项目实际成本

### 1.7 删除成本记录

**端点**: `DELETE /api/v1/costs/{cost_id}`

**功能**:
- 删除成本记录
- 自动更新项目的实际成本（减去删除的金额）

**响应**: `ResponseModel`

**特性**:
- ✅ 自动更新项目实际成本
- ✅ 确保项目成本不为负数

### 1.8 项目成本汇总统计

**端点**: `GET /api/v1/costs/projects/{project_id}/costs/summary`

**功能**:
- 获取项目的成本汇总统计
- 包含总成本、按类型统计、按分类统计、按机台统计

**响应**: `dict`

**响应字段**:
```json
{
  "project_id": 1,
  "project_code": "PJ20250101001",
  "project_name": "测试项目",
  "contract_amount": 1000000.00,
  "budget_amount": 800000.00,
  "actual_cost": 750000.00,
  "summary": {
    "total_amount": 750000.00,
    "total_tax": 97500.00,
    "total_with_tax": 847500.00,
    "total_count": 50
  },
  "by_type": [
    {
      "cost_type": "MATERIAL",
      "amount": 500000.00,
      "count": 30
    },
    ...
  ],
  "by_category": [
    {
      "cost_category": "PURCHASE",
      "amount": 400000.00,
      "count": 25
    },
    ...
  ],
  "by_machine": [
    {
      "machine_id": 1,
      "machine_code": "M001",
      "machine_name": "设备1",
      "amount": 300000.00,
      "count": 20
    },
    ...
  ]
}
```

## 2. Schema 定义

### 2.1 ProjectCostCreate

```python
class ProjectCostCreate(BaseModel):
    """创建成本记录"""
    
    project_id: int
    machine_id: Optional[int] = None
    cost_type: str
    cost_category: str
    source_module: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    source_no: Optional[str] = None
    amount: Decimal
    tax_amount: Optional[Decimal] = 0
    description: Optional[str] = None
    cost_date: date
```

### 2.2 ProjectCostUpdate

```python
class ProjectCostUpdate(BaseModel):
    """更新成本记录"""
    
    machine_id: Optional[int] = None
    cost_type: Optional[str] = None
    cost_category: Optional[str] = None
    source_module: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    source_no: Optional[str] = None
    amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    description: Optional[str] = None
    cost_date: Optional[date] = None
```

### 2.3 ProjectCostResponse

```python
class ProjectCostResponse(TimestampSchema):
    """成本记录响应"""
    
    id: int
    project_id: int
    machine_id: Optional[int] = None
    cost_type: str
    cost_category: str
    source_module: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    source_no: Optional[str] = None
    amount: Decimal
    tax_amount: Decimal
    description: Optional[str] = None
    cost_date: date
```

## 3. 实现特性

### 3.1 自动成本更新

- ✅ 创建成本记录时，自动更新项目的 `actual_cost` 字段
- ✅ 更新成本记录时，自动调整项目的 `actual_cost` 字段
- ✅ 删除成本记录时，自动减少项目的 `actual_cost` 字段
- ✅ 确保项目成本不为负数

### 3.2 数据验证

- ✅ 验证项目存在性
- ✅ 验证机台归属（如果指定了机台，确保机台属于该项目）
- ✅ 日期格式验证
- ✅ 金额验证

### 3.3 查询优化

- ✅ 支持多条件筛选
- ✅ 支持日期范围筛选
- ✅ 分页支持
- ✅ 按成本日期倒序排列

### 3.4 统计功能

- ✅ 总成本统计（金额、税额、含税总额、记录数）
- ✅ 按成本类型统计
- ✅ 按成本分类统计
- ✅ 按机台统计（包含机台信息）

## 4. 安全特性

- ✅ JWT 认证（所有端点）
- ✅ 用户权限检查
- ✅ 数据验证

## 5. 错误处理

- ✅ 404：项目/机台/成本记录不存在
- ✅ 400：日期格式错误、机台不属于项目
- ✅ 401：未认证
- ✅ 403：无权限

## 6. 使用示例

### 6.1 创建成本记录

```bash
POST /api/v1/costs
Content-Type: application/json

{
  "project_id": 1,
  "machine_id": 1,
  "cost_type": "MATERIAL",
  "cost_category": "PURCHASE",
  "source_module": "PURCHASE",
  "source_type": "PURCHASE_ORDER",
  "source_id": 100,
  "source_no": "PO-20250101001",
  "amount": 10000.00,
  "tax_amount": 1300.00,
  "description": "采购物料成本",
  "cost_date": "2025-01-15"
}
```

### 6.2 获取项目成本汇总

```bash
GET /api/v1/costs/projects/1/costs/summary
```

**响应**:
```json
{
  "project_id": 1,
  "project_code": "PJ20250101001",
  "project_name": "测试项目",
  "contract_amount": 1000000.00,
  "budget_amount": 800000.00,
  "actual_cost": 750000.00,
  "summary": {
    "total_amount": 750000.00,
    "total_tax": 97500.00,
    "total_with_tax": 847500.00,
    "total_count": 50
  },
  "by_type": [...],
  "by_category": [...],
  "by_machine": [...]
}
```

## 7. 后续优化建议

1. **成本预算对比**: 添加预算与实际成本对比分析
2. **成本趋势分析**: 按时间维度分析成本趋势
3. **成本预警**: 当实际成本超过预算时发送预警
4. **成本分摊**: 支持将成本分摊到多个机台或项目
5. **成本导入导出**: 支持Excel导入导出成本记录
6. **成本审批流程**: 对于大额成本，添加审批流程
7. **成本来源追溯**: 更详细地记录成本来源，支持反向追溯

## 8. 相关文件

- `app/api/v1/endpoints/costs.py` - 成本管理API实现
- `app/models/project.py` - ProjectCost 模型定义
- `app/schemas/project.py` - 成本相关Schema定义
- `app/api/v1/api.py` - API路由注册




# 库存管理系统 - 快速开始

**5分钟快速上手库存管理系统**

---

## 📦 安装和配置

### 1. 数据库迁移

```bash
# 执行迁移
cd ~/.openclaw/workspace/non-standard-automation-pms
alembic upgrade head
```

### 2. 注册API路由

在 `app/api/v1/api.py` 中添加:

```python
from app.api.v1.endpoints.inventory.inventory_router import router as inventory_router

api_router.include_router(
    inventory_router,
    prefix="/api/v1",
    tags=["inventory"]
)
```

### 3. 启动服务

```bash
python start.sh
```

---

## 🚀 基础操作

### 1. 采购入库 (第一步)

**场景**: 采购的物料到货,办理入库

**API**:
```bash
POST http://localhost:8000/api/v1/inventory/purchase-in
```

**请求**:
```json
{
  "material_id": 1,
  "quantity": 1000,
  "unit_price": 50.00,
  "location": "仓库A",
  "batch_number": "BATCH-001",
  "purchase_order_id": 1001
}
```

**响应**:
```json
{
  "success": true,
  "message": "入库成功: 1000 件",
  "stock_quantity": 1000.0
}
```

### 2. 查询库存

**API**:
```bash
GET http://localhost:8000/api/v1/inventory/stocks?material_id=1
```

**响应**:
```json
[
  {
    "material_code": "MAT-001",
    "material_name": "物料A",
    "location": "仓库A",
    "quantity": 1000.0,
    "available_quantity": 1000.0,
    "reserved_quantity": 0.0,
    "unit_price": 50.00,
    "status": "NORMAL"
  }
]
```

### 3. 预留物料 (可选)

**场景**: 为项目预留物料,防止被其他项目领用

**API**:
```bash
POST http://localhost:8000/api/v1/inventory/reserve
```

**请求**:
```json
{
  "material_id": 1,
  "quantity": 200,
  "project_id": 5,
  "expected_use_date": "2026-03-01"
}
```

**响应**:
```json
{
  "success": true,
  "message": "物料预留成功",
  "reservation_no": "RSV-20260216120000-1",
  "reserved_quantity": 200.0
}
```

### 4. 领料出库

**场景**: 生产车间领取物料

**API**:
```bash
POST http://localhost:8000/api/v1/inventory/issue
```

**请求**:
```json
{
  "material_id": 1,
  "quantity": 150,
  "location": "仓库A",
  "work_order_id": 3001,
  "cost_method": "FIFO"
}
```

**响应**:
```json
{
  "success": true,
  "message": "领料成功: 150",
  "total_cost": 7500.00
}
```

### 5. 退料入库

**场景**: 车间退回多领的物料

**API**:
```bash
POST http://localhost:8000/api/v1/inventory/return
```

**请求**:
```json
{
  "material_id": 1,
  "quantity": 20,
  "location": "仓库A",
  "work_order_id": 3001,
  "remark": "多领退回"
}
```

---

## 📊 库存盘点

### 1. 创建盘点任务

**API**:
```bash
POST http://localhost:8000/api/v1/inventory/count/tasks
```

**请求**:
```json
{
  "count_type": "FULL",
  "count_date": "2026-02-20",
  "location": "仓库A",
  "assigned_to": 1
}
```

**响应**:
```json
{
  "task_no": "CNT-20260220120000",
  "count_type": "FULL",
  "status": "PENDING",
  "total_items": 10
}
```

### 2. 录入实盘数量

**API**:
```bash
PUT http://localhost:8000/api/v1/inventory/count/details/{detail_id}
```

**请求**:
```json
{
  "actual_quantity": 985.0,
  "remark": "实盘确认"
}
```

**响应**:
```json
{
  "success": true,
  "system_quantity": 1000.0,
  "actual_quantity": 985.0,
  "difference": -15.0,
  "difference_rate": -1.5
}
```

### 3. 审批调整

**API**:
```bash
POST http://localhost:8000/api/v1/inventory/count/tasks/{task_id}/approve
```

**响应**:
```json
{
  "success": true,
  "message": "盘点审批完成,共调整 3 条记录",
  "total_adjustments": 3,
  "total_diff_value": -150.00
}
```

---

## 📈 库存分析

### 库存周转率

**API**:
```bash
GET http://localhost:8000/api/v1/inventory/analysis/turnover?material_id=1
```

**响应**:
```json
{
  "total_issue_value": 75000.00,
  "avg_stock_value": 25000.00,
  "turnover_rate": 3.0,
  "turnover_days": 122
}
```

### 库龄分析

**API**:
```bash
GET http://localhost:8000/api/v1/inventory/analysis/aging?location=仓库A
```

**响应**:
```json
{
  "aging_summary": {
    "0-30天": {
      "count": 5,
      "total_value": 50000.00
    },
    "31-90天": {
      "count": 3,
      "total_value": 15000.00
    }
  }
}
```

---

## 🔧 代码示例

### Python示例

```python
from app.services.inventory_management_service import InventoryManagementService
from decimal import Decimal

# 初始化服务
service = InventoryManagementService(db, tenant_id=1)

# 采购入库
result = service.purchase_in(
    material_id=1,
    quantity=Decimal('1000'),
    unit_price=Decimal('50.00'),
    location='仓库A',
    batch_number='BATCH-001'
)

# 领料出库
result = service.issue_material(
    material_id=1,
    quantity=Decimal('150'),
    location='仓库A',
    cost_method='FIFO'
)

# 预留物料
reservation = service.reserve_material(
    material_id=1,
    quantity=Decimal('200'),
    project_id=5
)

# 查询库存
stocks = service.get_stock(material_id=1)
available = service.get_available_quantity(material_id=1)
```

---

## 📋 常用场景

### 场景1: 完整的出入库流程

```
1. 采购入库 (purchase_in)
   ↓
2. 为项目预留 (reserve_material)
   ↓
3. 领料出库 (issue_material)
   ↓
4. 退回多余物料 (return_material)
```

### 场景2: 月度盘点流程

```
1. 创建盘点任务 (create_count_task)
   ↓
2. 开始盘点 (start_count_task)
   ↓
3. 录入实盘数量 (record_actual_quantity)
   ↓
4. 审批调整 (approve_adjustment)
```

### 场景3: 仓库间调拨

```
transfer_stock(
    material_id=1,
    quantity=100,
    from_location='仓库A',
    to_location='仓库B'
)
```

---

## ⚠️ 注意事项

1. **库存不足**: 系统会自动检查库存,不足时会抛出 `InsufficientStockError`
2. **预留占用**: 预留的库存不能被其他项目领用
3. **成本核算**: 根据物料特性选择合适的成本核算方法 (FIFO/LIFO/加权平均)
4. **批次管理**: 有保质期的物料建议使用批次管理
5. **盘点冻结**: 盘点期间禁止出入库操作

---

## 📚 更多文档

- [设计文档](./inventory_tracking_design.md) - 详细的技术设计
- [操作手册](./inventory_management_manual.md) - 完整的操作指南
- [盘点指南](./stock_count_guide.md) - 库存盘点详细流程

---

## 🆘 获取帮助

- **技术问题**: 查看 [常见问题](./inventory_management_manual.md#常见问题)
- **API文档**: http://localhost:8000/docs
- **联系支持**: tech-support@example.com

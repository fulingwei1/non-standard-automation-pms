# 物料全流程跟踪系统 - 设计文档

**Team 2 交付文档**  
**版本**: 1.0  
**日期**: 2026-02-16

---

## 📋 目录

1. [系统概述](#系统概述)
2. [数据模型设计](#数据模型设计)
3. [核心服务设计](#核心服务设计)
4. [API接口设计](#api接口设计)
5. [技术实现](#技术实现)
6. [性能优化](#性能优化)

---

## 系统概述

### 业务背景

物料全流程跟踪系统实现了从采购入库到生产消耗的完整生命周期管理,解决以下核心问题:

1. **库存实时跟踪**: 实时记录所有物料交易,确保库存数据准确
2. **成本核算**: 支持FIFO/LIFO/加权平均等多种成本核算方法
3. **物料预留**: 为项目/工单预留物料,防止挪用
4. **库存盘点**: 定期盘点,及时发现和调整库存差异
5. **数据分析**: 库存周转率、库龄分析等决策支持

### 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                     API层 (12个接口)                      │
├─────────────────────────────────────────────────────────┤
│  InventoryManagementService  │  StockCountService       │
├─────────────────────────────────────────────────────────┤
│  MaterialTransaction  │  MaterialStock                   │
│  MaterialReservation  │  StockAdjustment                │
│  StockCountTask      │  StockCountDetail                │
└─────────────────────────────────────────────────────────┘
```

---

## 数据模型设计

### 1. MaterialTransaction - 物料交易记录表

**用途**: 记录所有物料流转,实现全流程追溯

```python
class MaterialTransaction(Base):
    id: int                          # 主键
    tenant_id: int                   # 租户ID
    material_id: int                 # 物料ID
    transaction_type: str            # 交易类型
    quantity: Decimal                # 数量
    unit_price: Decimal              # 单价
    source_location: str             # 来源位置
    target_location: str             # 目标位置
    batch_number: str                # 批次号
    related_order_id: int            # 关联单据ID
    transaction_date: datetime       # 交易时间
    cost_method: str                 # 成本核算方法
```

**交易类型**:
- `PURCHASE_IN`: 采购入库
- `TRANSFER_IN`: 调拨入库
- `ISSUE`: 领用出库
- `RETURN`: 退料入库
- `ADJUST`: 盘点调整
- `SCRAP`: 报废

**索引设计**:
- `idx_mat_trans_material`: material_id
- `idx_mat_trans_type`: transaction_type
- `idx_mat_trans_date`: transaction_date
- `idx_mat_trans_batch`: batch_number

### 2. MaterialStock - 物料库存表

**用途**: 实时库存状态,支持多仓库/多批次

```python
class MaterialStock(Base):
    id: int                          # 主键
    tenant_id: int                   # 租户ID
    material_id: int                 # 物料ID
    location: str                    # 仓库位置
    batch_number: str                # 批次号
    quantity: Decimal                # 库存总数
    available_quantity: Decimal      # 可用数量
    reserved_quantity: Decimal       # 预留数量
    unit_price: Decimal              # 加权平均单价
    total_value: Decimal             # 库存总价值
    status: str                      # 状态
```

**库存状态**:
- `NORMAL`: 正常
- `LOW`: 低库存
- `LOCKED`: 锁定
- `EXPIRED`: 过期
- `EMPTY`: 已清空

**唯一约束**: `(material_id, location, batch_number)` - 确保同一物料在同一位置的同一批次只有一条记录

### 3. MaterialReservation - 物料预留表

**用途**: 为项目/工单预留物料,避免挪用

```python
class MaterialReservation(Base):
    id: int                          # 主键
    reservation_no: str              # 预留单号
    material_id: int                 # 物料ID
    reserved_quantity: Decimal       # 预留数量
    used_quantity: Decimal           # 已用数量
    remaining_quantity: Decimal      # 剩余数量
    project_id: int                  # 项目ID
    work_order_id: int               # 工单ID
    status: str                      # 状态
```

**预留状态**:
- `ACTIVE`: 生效中
- `PARTIAL_USED`: 部分使用
- `USED`: 已使用
- `CANCELLED`: 已取消
- `EXPIRED`: 已过期

### 4. StockAdjustment - 库存调整表

**用途**: 记录所有库存调整,支持审批流程

```python
class StockAdjustment(Base):
    id: int                          # 主键
    adjustment_no: str               # 调整单号
    material_id: int                 # 物料ID
    original_quantity: Decimal       # 账面数量
    actual_quantity: Decimal         # 实盘数量
    difference: Decimal              # 差异数量
    adjustment_type: str             # 调整类型
    status: str                      # 审批状态
    approved_by: int                 # 审批人
```

**调整类型**:
- `INVENTORY`: 盘点调整
- `DAMAGE`: 破损
- `LOSS`: 丢失
- `CORRECTION`: 纠正

### 5. StockCountTask - 库存盘点任务表

**用途**: 盘点任务管理

```python
class StockCountTask(Base):
    id: int                          # 主键
    task_no: str                     # 任务号
    count_type: str                  # 盘点类型
    location: str                    # 盘点位置
    count_date: date                 # 盘点日期
    status: str                      # 状态
    total_items: int                 # 总物料数
    counted_items: int               # 已盘点数
    matched_items: int               # 账实相符数
    diff_items: int                  # 差异物料数
```

**盘点类型**:
- `FULL`: 全盘
- `PARTIAL`: 抽盘
- `CYCLE`: 循环盘点

### 6. StockCountDetail - 库存盘点明细表

**用途**: 盘点明细数据

```python
class StockCountDetail(Base):
    id: int                          # 主键
    task_id: int                     # 任务ID
    material_id: int                 # 物料ID
    system_quantity: Decimal         # 系统数量
    actual_quantity: Decimal         # 实盘数量
    difference: Decimal              # 差异数量
    status: str                      # 状态
```

---

## 核心服务设计

### InventoryManagementService - 库存管理服务

**职责**: 库存CRUD、交易记录、出入库操作、物料预留

#### 核心方法

**1. 库存查询**
```python
get_stock(material_id, location=None, batch_number=None)
get_available_quantity(material_id, location=None)
get_total_quantity(material_id)
```

**2. 交易记录**
```python
create_transaction(material_id, transaction_type, quantity, ...)
get_transactions(material_id, transaction_type, start_date, end_date)
```

**3. 出入库操作**
```python
purchase_in(material_id, quantity, unit_price, location, ...)
issue_material(material_id, quantity, location, cost_method='FIFO')
return_material(material_id, quantity, location, ...)
transfer_stock(material_id, quantity, from_location, to_location)
```

**4. 物料预留**
```python
reserve_material(material_id, quantity, project_id, ...)
cancel_reservation(reservation_id, cancel_reason)
```

**5. 库存分析**
```python
calculate_turnover_rate(material_id, start_date, end_date)
analyze_aging(location)
```

#### 成本核算算法

**FIFO (先进先出)**
```python
def _select_stock_for_issue(material_id, location, quantity, 'FIFO'):
    # 按入库时间升序排列
    stocks = query.order_by(MaterialStock.last_in_date.asc())
    # 从最早的库存开始出库
    ...
```

**LIFO (后进先出)**
```python
def _select_stock_for_issue(material_id, location, quantity, 'LIFO'):
    # 按入库时间降序排列
    stocks = query.order_by(MaterialStock.last_in_date.desc())
    # 从最新的库存开始出库
    ...
```

**加权平均**
```python
def update_weighted_avg_price(stock, new_qty, new_price):
    old_value = stock.quantity * stock.unit_price
    new_value = new_qty * new_price
    total_qty = stock.quantity + new_qty
    stock.unit_price = (old_value + new_value) / total_qty
```

### StockCountService - 库存盘点服务

**职责**: 盘点任务创建、明细管理、差异调整、审批

#### 核心方法

**1. 盘点任务管理**
```python
create_count_task(count_type, count_date, location, ...)
start_count_task(task_id)
cancel_count_task(task_id)
get_count_tasks(status, start_date, end_date)
```

**2. 盘点明细管理**
```python
get_count_details(task_id)
record_actual_quantity(detail_id, actual_quantity, counted_by)
batch_record_quantities(records, counted_by)
mark_for_recount(detail_id, recount_reason)
```

**3. 调整审批**
```python
approve_adjustment(task_id, approved_by, auto_adjust=True)
```

**4. 盘点分析**
```python
get_count_summary(task_id)
analyze_count_history(material_id, location, start_date, end_date)
```

#### 盘点流程

```
创建盘点任务 → 开始盘点 → 录入实盘数量 → (复盘) → 审批调整 → 完成
```

---

## API接口设计

### 1. GET /inventory/stocks - 库存查询

**请求参数**:
- `material_id` (可选): 物料ID
- `location` (可选): 仓库位置
- `status` (可选): 库存状态

**响应**:
```json
[
  {
    "id": 1,
    "material_code": "MAT-001",
    "material_name": "物料A",
    "location": "仓库A",
    "quantity": 500.0,
    "available_quantity": 450.0,
    "reserved_quantity": 50.0,
    "unit_price": 55.67,
    "status": "NORMAL"
  }
]
```

### 2. GET /inventory/stocks/{material_id}/transactions - 交易记录

**请求参数**:
- `transaction_type` (可选): 交易类型
- `start_date` (可选): 开始日期
- `end_date` (可选): 结束日期
- `limit`: 返回数量限制 (默认100)

**响应**: 交易记录列表

### 3. POST /inventory/reserve - 预留物料

**请求体**:
```json
{
  "material_id": 1,
  "quantity": 100,
  "project_id": 5,
  "expected_use_date": "2026-03-01",
  "remark": "项目X预留"
}
```

**响应**:
```json
{
  "success": true,
  "message": "物料预留成功",
  "reservation_id": 123,
  "reservation_no": "RSV-20260216120000-1"
}
```

### 4. POST /inventory/issue - 领料

**请求体**:
```json
{
  "material_id": 1,
  "quantity": 50,
  "location": "仓库A",
  "work_order_id": 10,
  "cost_method": "FIFO",
  "reservation_id": 123
}
```

**响应**:
```json
{
  "success": true,
  "message": "领料成功: 50",
  "total_cost": 2783.5,
  "transactions": 2
}
```

### 5. POST /inventory/return - 退料

**请求体**:
```json
{
  "material_id": 1,
  "quantity": 10,
  "location": "仓库A",
  "work_order_id": 10,
  "remark": "多领退回"
}
```

### 6. POST /inventory/transfer - 库存转移

**请求体**:
```json
{
  "material_id": 1,
  "quantity": 30,
  "from_location": "仓库A",
  "to_location": "仓库B",
  "batch_number": "BATCH-001"
}
```

### 7. GET /inventory/count/tasks - 盘点任务列表

**请求参数**:
- `status` (可选): 任务状态
- `start_date` (可选): 开始日期
- `end_date` (可选): 结束日期

### 8. POST /inventory/count/tasks - 创建盘点任务

**请求体**:
```json
{
  "count_type": "FULL",
  "count_date": "2026-02-20",
  "location": "仓库A",
  "assigned_to": 5,
  "remark": "月度全盘"
}
```

### 9. PUT /inventory/count/details/{id} - 录入实盘数量

**请求体**:
```json
{
  "actual_quantity": 485.5,
  "remark": "实盘确认"
}
```

### 10. POST /inventory/count/tasks/{id}/approve - 批准调整

**请求参数**:
- `auto_adjust`: 是否自动执行库存调整 (默认true)

### 11. GET /inventory/analysis/turnover - 库存周转率

**请求参数**:
- `material_id` (可选): 物料ID
- `start_date` (可选): 开始日期
- `end_date` (可选): 结束日期

**响应**:
```json
{
  "period": {
    "start_date": "2026-02-01",
    "end_date": "2026-02-16"
  },
  "total_issue_value": 120000.0,
  "avg_stock_value": 50000.0,
  "turnover_rate": 2.4,
  "turnover_days": 152
}
```

### 12. GET /inventory/analysis/aging - 库龄分析

**请求参数**:
- `location` (可选): 仓库位置

**响应**:
```json
{
  "aging_summary": {
    "0-30天": {
      "count": 10,
      "total_quantity": 5000,
      "total_value": 250000
    },
    "31-90天": {...},
    ...
  },
  "details": [...]
}
```

---

## 技术实现

### 1. 数据库事务

所有涉及库存更新的操作都使用数据库事务确保一致性:

```python
@transaction
def issue_material(self, material_id, quantity, ...):
    # 1. 检查库存
    # 2. 创建交易记录
    # 3. 更新库存
    # 4. 释放预留
    # 所有步骤在一个事务中完成
```

### 2. 并发控制

使用乐观锁防止并发更新冲突:

```python
# 使用version字段或updated_at字段进行乐观锁控制
stock = db.query(MaterialStock).with_for_update().get(id)
```

### 3. 索引优化

```sql
-- 交易记录查询优化
CREATE INDEX idx_mat_trans_material_date 
ON material_transaction (material_id, transaction_date);

-- 库存查询优化
CREATE UNIQUE INDEX idx_mat_stock_unique 
ON material_stock (material_id, location, batch_number);
```

### 4. 租户隔离

所有表都包含 `tenant_id` 字段,确保多租户数据隔离:

```python
query = db.query(MaterialStock).filter(
    MaterialStock.tenant_id == current_user.tenant_id
)
```

---

## 性能优化

### 1. 库存计算优化

**方案**: 冗余存储 vs 实时计算

- **MaterialStock表**: 冗余存储quantity, available_quantity, reserved_quantity
- **优点**: 查询快速,不需要聚合计算
- **代价**: 每次交易需要更新,事务复杂度增加

### 2. 交易记录分表

**方案**: 按月份分表

```python
# material_transaction_202602
# material_transaction_202603
# ...
```

### 3. 批量操作

```python
def batch_record_quantities(records):
    # 批量更新,减少数据库往返
    for record in records:
        ...
    db.bulk_update_mappings(StockCountDetail, updates)
    db.commit()
```

### 4. 缓存策略

**Redis缓存**:
- 物料基础信息
- 库存汇总数据 (TTL: 5分钟)
- 盘点任务状态

**缓存失效**:
- 库存更新后清除相关缓存
- 使用发布/订阅模式通知缓存更新

---

## 总结

本系统实现了物料从采购到消耗的全生命周期跟踪,核心特性:

✅ **6个数据模型** - 完整覆盖库存管理场景  
✅ **12个API接口** - 支持所有核心业务流程  
✅ **3种成本核算方法** - FIFO/LIFO/加权平均  
✅ **物料预留机制** - 防止挪用  
✅ **完整盘点流程** - 从任务创建到审批调整  
✅ **数据分析功能** - 周转率、库龄分析  
✅ **数据库事务** - 确保数据一致性  
✅ **多租户支持** - 完整租户隔离  

**下一步优化方向**:
1. 库存预警规则引擎
2. 物料批次有效期管理
3. 库存报表可视化
4. 移动端盘点APP

# 已弃用数据模型处理指南

## 概述

本文档说明如何处理已弃用的数据模型，以 `Supplier` 和 `OutsourcingVendor` 迁移到 `Vendor` 为例。

---

## 处理已弃用数据模型的常见策略

### 策略 1: 兼容层 + 视图（当前采用）

**适用场景**: 
- 数据已合并到新表
- 需要保持向后兼容
- 逐步迁移代码

**优点**:
- ✅ 零停机迁移
- ✅ 可以逐步迁移代码
- ✅ 降低风险

**缺点**:
- ⚠️ 视图不支持关系（relationship）
- ⚠️ 需要维护兼容层代码
- ⚠️ 性能可能略低于直接查询

**当前状态**: 
- `Supplier` → 指向 `suppliers_view` 视图
- `OutsourcingVendor` → 指向 `outsourcing_vendors_view` 视图
- 底层数据已合并到 `vendors` 表

### 策略 2: 直接替换（激进）

**适用场景**:
- 使用范围小
- 可以接受短暂停机
- 团队规模小，容易协调

**优点**:
- ✅ 代码简洁
- ✅ 无兼容层负担

**缺点**:
- ❌ 需要一次性迁移所有代码
- ❌ 风险较高
- ❌ 可能影响生产环境

### 策略 3: 别名/类型别名（Python 特有）

**适用场景**:
- 模型接口完全兼容
- 只是重命名

**优点**:
- ✅ 迁移成本最低
- ✅ 可以逐步替换

**缺点**:
- ⚠️ 需要确保接口完全兼容
- ⚠️ 可能隐藏问题

---

## 当前项目的最佳实践

### 阶段 1: 保持兼容层（当前阶段）

**目标**: 确保现有代码继续工作，同时引导新代码使用新模型

**实施**:

1. **保留已弃用模型作为兼容层**
   ```python
   # app/models/material.py
   class Supplier(Base, TimestampMixin):
       """
       供应商表（兼容层）
       注意：此表已合并到 vendors 表中。
       新代码应使用 app.models.vendor.Vendor 代替。
       """
       __tablename__ = 'suppliers_view'  # 指向视图
       # ... 字段定义
   ```

2. **添加清晰的弃用警告**
   ```python
   def __repr__(self):
       return f'<Supplier {self.supplier_code} (deprecated, use Vendor instead)>'
   ```

3. **在文档中说明迁移路径**
   ```python
   """
   迁移路径：
   1. 运行 migrations/20250122_merge_vendors_sqlite.sql
   2. 将代码中的 Supplier 替换为 Vendor
   3. 添加 vendor_type='MATERIAL' 过滤条件
   """
   ```

### 阶段 2: 逐步迁移代码

**目标**: 将使用已弃用模型的代码迁移到新模型

**迁移步骤**:

#### 步骤 1: 识别所有使用位置

```bash
# 查找 Supplier 的使用
grep -r "from.*Supplier\|import.*Supplier\|Supplier(" app/

# 查找 OutsourcingVendor 的使用
grep -r "from.*OutsourcingVendor\|import.*OutsourcingVendor\|OutsourcingVendor(" app/
```

#### 步骤 2: 创建迁移清单

**Supplier 使用位置** (5 处):
- `app/api/v1/endpoints/suppliers.py`
- `app/api/v1/endpoints/materials/suppliers.py`
- `app/services/urgent_purchase_from_shortage_service.py`
- `app/services/inventory_analysis_service.py`
- `app/api/v1/endpoints/business_support_orders/customer_registrations.py`

**OutsourcingVendor 使用位置** (7 处):
- `app/api/v1/endpoints/outsourcing/payments/print.py`
- `app/api/v1/endpoints/outsourcing/payments/crud.py`
- `app/api/v1/endpoints/report_center/templates.py`
- `app/api/v1/endpoints/report_center/rd_expense.py`
- `app/api/v1/endpoints/report_center/configs.py`
- `app/api/v1/endpoints/report_center/bi.py`
- `app/api/v1/endpoints/outsourcing/suppliers.py`

#### 步骤 3: 逐个文件迁移

**迁移模板**:

```python
# ❌ 旧代码
from app.models.material import Supplier

def get_supplier(supplier_id: int):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    return supplier

# ✅ 新代码
from app.models.vendor import Vendor

def get_supplier(supplier_id: int):
    supplier = db.query(Vendor).filter(
        Vendor.id == supplier_id,
        Vendor.vendor_type == 'MATERIAL'  # 添加类型过滤
    ).first()
    return supplier
```

**关键差异**:

1. **导入变更**
   ```python
   # 旧
   from app.models.material import Supplier
   from app.models.outsourcing import OutsourcingVendor
   
   # 新
   from app.models.vendor import Vendor
   ```

2. **添加类型过滤**
   ```python
   # 物料供应商
   db.query(Vendor).filter(
       Vendor.vendor_type == 'MATERIAL',
       # ... 其他条件
   )
   
   # 外协商
   db.query(Vendor).filter(
       Vendor.vendor_type == 'OUTSOURCING',
       # ... 其他条件
   )
   ```

3. **字段名可能不同**
   ```python
   # Supplier 使用 supplier_code
   # Vendor 也使用 supplier_code（兼容）
   # 但注意：OutsourcingVendor 使用 vendor_code
   # Vendor 统一使用 supplier_code
   ```

#### 步骤 4: 更新关系查询

**注意**: 视图不支持 relationship，迁移后可以使用关系：

```python
# ❌ 旧代码（视图不支持关系）
supplier = db.query(Supplier).first()
# supplier.materials  # 不可用

# ✅ 新代码（可以使用关系）
vendor = db.query(Vendor).filter(
    Vendor.vendor_type == 'MATERIAL'
).first()
vendor.materials  # 可用
vendor.purchase_orders  # 可用
```

#### 步骤 5: 更新 Schema

```python
# app/schemas/material.py 或 app/schemas/vendor.py

# ❌ 旧
class SupplierResponse(BaseModel):
    supplier_code: str
    supplier_name: str
    # ...

# ✅ 新（如果还没有统一 Schema）
class VendorResponse(BaseModel):
    supplier_code: str
    supplier_name: str
    vendor_type: str  # 新增
    # ...
```

### 阶段 3: 移除兼容层（最终阶段）

**前提条件**:
- ✅ 所有代码已迁移
- ✅ 所有测试通过
- ✅ 生产环境验证完成
- ✅ 文档已更新

**实施步骤**:

1. **移除已弃用模型定义**
   ```python
   # app/models/material.py
   # 删除 Supplier 类定义
   
   # app/models/outsourcing.py
   # 删除 OutsourcingVendor 类定义
   ```

2. **移除视图（可选）**
   ```sql
   -- 如果不再需要视图
   DROP VIEW IF EXISTS suppliers_view;
   DROP VIEW IF EXISTS outsourcing_vendors_view;
   ```

3. **更新导入检查**
   ```python
   # 确保没有残留导入
   grep -r "from.*Supplier\|import.*Supplier" app/
   grep -r "from.*OutsourcingVendor\|import.*OutsourcingVendor" app/
   ```

---

## 迁移检查清单

### 代码迁移

- [ ] 识别所有使用已弃用模型的位置
- [ ] 创建迁移分支
- [ ] 逐个文件迁移
- [ ] 添加类型过滤条件（`vendor_type`）
- [ ] 更新字段名（如 `vendor_code` → `supplier_code`）
- [ ] 更新关系查询（如果适用）
- [ ] 运行测试确保功能正常

### 测试验证

- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] API 测试通过
- [ ] 前端功能测试通过
- [ ] 性能测试（查询性能）

### 文档更新

- [ ] 更新 API 文档
- [ ] 更新开发指南
- [ ] 更新迁移文档
- [ ] 更新架构文档

### 部署准备

- [ ] 代码审查完成
- [ ] 数据库迁移脚本准备
- [ ] 回滚计划准备
- [ ] 监控和告警配置

---

## 常见问题和解决方案

### Q1: 视图不支持 relationship，怎么办？

**A**: 迁移到 `Vendor` 模型后，可以使用关系：

```python
# 迁移前（视图，不支持关系）
supplier = db.query(Supplier).first()
# supplier.materials  # 不可用

# 迁移后（表，支持关系）
vendor = db.query(Vendor).filter(
    Vendor.vendor_type == 'MATERIAL'
).first()
vendor.materials  # 可用
```

### Q2: 字段名不一致怎么办？

**A**: 统一使用 `Vendor` 模型的字段名：

```python
# OutsourcingVendor 使用 vendor_code
# Vendor 统一使用 supplier_code

# 迁移时需要注意
# 旧: vendor.vendor_code
# 新: vendor.supplier_code
```

### Q3: 如何确保迁移不影响现有功能？

**A**: 采用渐进式迁移：

1. **保持兼容层** - 已弃用模型继续工作
2. **逐个迁移** - 一次迁移一个文件
3. **充分测试** - 每个文件迁移后运行测试
4. **监控验证** - 生产环境监控

### Q4: 如何处理外键约束？

**A**: 检查并更新外键引用：

```python
# 检查外键
# MaterialSupplier.vendor_id 应该指向 vendors.id
# PurchaseOrder.vendor_id 应该指向 vendors.id
# OutsourcingOrder.vendor_id 应该指向 vendors.id

# 确保迁移脚本已更新外键
```

### Q5: 性能影响如何？

**A**: 迁移到 `Vendor` 后性能可能更好：

- ✅ 直接查询表，而非视图
- ✅ 可以使用关系，减少查询次数
- ✅ 更好的索引支持

---

## 迁移示例

### 示例 1: API 端点迁移

**文件**: `app/api/v1/endpoints/suppliers.py`

```python
# ❌ 旧代码
from app.models.material import Supplier

@router.get("/", response_model=List[SupplierResponse])
def list_suppliers(db: Session = Depends(get_db)):
    suppliers = db.query(Supplier).all()
    return suppliers

# ✅ 新代码
from app.models.vendor import Vendor

@router.get("/", response_model=List[VendorResponse])
def list_suppliers(db: Session = Depends(get_db)):
    suppliers = db.query(Vendor).filter(
        Vendor.vendor_type == 'MATERIAL'
    ).all()
    return suppliers
```

### 示例 2: 服务层迁移

**文件**: `app/services/urgent_purchase_from_shortage_service.py`

```python
# ❌ 旧代码
from app.models.material import Supplier, MaterialSupplier

def get_supplier_by_code(supplier_code: str):
    return db.query(Supplier).filter(
        Supplier.supplier_code == supplier_code
    ).first()

# ✅ 新代码
from app.models.vendor import Vendor

def get_supplier_by_code(supplier_code: str):
    return db.query(Vendor).filter(
        Vendor.supplier_code == supplier_code,
        Vendor.vendor_type == 'MATERIAL'
    ).first()
```

### 示例 3: 外协商迁移

**文件**: `app/api/v1/endpoints/outsourcing/suppliers.py`

```python
# ❌ 旧代码
from app.models.outsourcing import OutsourcingVendor

vendor = OutsourcingVendor(
    vendor_code=code,  # 注意：字段名不同
    vendor_name=name,
    # ...
)

# ✅ 新代码
from app.models.vendor import Vendor

vendor = Vendor(
    supplier_code=code,  # 统一使用 supplier_code
    supplier_name=name,
    vendor_type='OUTSOURCING',  # 必须指定类型
    # ...
)
```

---

## 风险评估

### 低风险

- ✅ 新代码使用新模型
- ✅ 兼容层保持工作
- ✅ 可以逐步迁移

### 中风险

- ⚠️ 字段名差异（`vendor_code` vs `supplier_code`）
- ⚠️ 类型过滤遗漏（忘记添加 `vendor_type`）
- ⚠️ 关系查询变更

### 高风险

- ❌ 一次性移除兼容层
- ❌ 未充分测试就部署
- ❌ 忽略外键约束

---

## 回滚计划

如果迁移出现问题，可以快速回滚：

1. **代码回滚**: Git revert 到迁移前
2. **数据库回滚**: 视图仍然存在，无需回滚
3. **验证**: 确保旧代码继续工作

---

## 时间线建议

### 第 1 周: 准备阶段
- 识别所有使用位置
- 创建迁移清单
- 准备测试用例

### 第 2-3 周: 迁移阶段
- 逐个文件迁移
- 每个文件迁移后测试
- 代码审查

### 第 4 周: 验证阶段
- 完整测试
- 性能测试
- 生产环境验证

### 第 5 周: 清理阶段（可选）
- 移除兼容层
- 移除视图
- 更新文档

---

## 总结

处理已弃用数据模型的最佳实践：

1. **保持兼容层** - 使用视图作为过渡
2. **渐进式迁移** - 逐个文件迁移，降低风险
3. **充分测试** - 每个步骤都验证
4. **清晰文档** - 说明迁移路径和注意事项
5. **监控验证** - 生产环境持续监控

当前项目已采用最佳实践，下一步是逐步迁移使用已弃用模型的代码。

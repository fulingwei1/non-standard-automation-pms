# 已弃用数据模型迁移计划

## 目标

将 `Supplier` 和 `OutsourcingVendor` 的使用迁移到统一的 `Vendor` 模型。

---

## 当前状态

### 已弃用模型

1. **Supplier** (`app/models/material.py`)
   - 指向视图: `suppliers_view`
   - 应迁移到: `Vendor` (vendor_type='MATERIAL')
   - 使用位置: 5 处

2. **OutsourcingVendor** (`app/models/outsourcing.py`)
   - 指向视图: `outsourcing_vendors_view`
   - 应迁移到: `Vendor` (vendor_type='OUTSOURCING')
   - 使用位置: 7 处

### 新模型

- **Vendor** (`app/models/vendor.py`)
  - 统一表: `vendors`
  - 支持类型: MATERIAL, OUTSOURCING
  - 已在新代码中使用

---

## 迁移清单

### Supplier → Vendor 迁移 (5 处)

#### 1. `app/api/v1/endpoints/suppliers.py`
- **状态**: ⏳ 待迁移
- **优先级**: 高
- **影响**: API 端点
- **操作**:
  ```python
  # 替换导入
  - from app.models.material import Supplier
  + from app.models.vendor import Vendor
  
  # 添加类型过滤
  + .filter(Vendor.vendor_type == 'MATERIAL')
  ```

#### 2. `app/api/v1/endpoints/materials/suppliers.py`
- **状态**: ⏳ 待迁移
- **优先级**: 高
- **影响**: 物料供应商 API
- **操作**: 同上

#### 3. `app/services/urgent_purchase_from_shortage_service.py`
- **状态**: ⏳ 待迁移
- **优先级**: 中
- **影响**: 紧急采购服务
- **操作**: 同上

#### 4. `app/services/inventory_analysis_service.py`
- **状态**: ⏳ 待迁移
- **优先级**: 中
- **影响**: 库存分析服务
- **操作**: 同上

#### 5. `app/api/v1/endpoints/business_support_orders/customer_registrations.py`
- **状态**: ⏳ 待迁移
- **优先级**: 低
- **影响**: 客户注册
- **操作**: 同上

### OutsourcingVendor → Vendor 迁移 (7 处)

#### 1. `app/api/v1/endpoints/outsourcing/payments/print.py`
- **状态**: ⏳ 待迁移
- **优先级**: 中
- **影响**: 外协付款打印
- **操作**:
  ```python
  # 替换导入
  - from app.models.outsourcing import OutsourcingVendor
  + from app.models.vendor import Vendor
  
  # 添加类型过滤
  + .filter(Vendor.vendor_type == 'OUTSOURCING')
  
  # 注意字段名: vendor_code → supplier_code
  ```

#### 2. `app/api/v1/endpoints/outsourcing/payments/crud.py`
- **状态**: ⏳ 待迁移
- **优先级**: 高
- **影响**: 外协付款 CRUD
- **操作**: 同上

#### 3. `app/api/v1/endpoints/report_center/templates.py`
- **状态**: ⏳ 待迁移
- **优先级**: 中
- **影响**: 报表中心模板
- **操作**: 同上

#### 4. `app/api/v1/endpoints/report_center/rd_expense.py`
- **状态**: ⏳ 待迁移
- **优先级**: 中
- **影响**: 研发费用报表
- **操作**: 同上

#### 5. `app/api/v1/endpoints/report_center/configs.py`
- **状态**: ⏳ 待迁移
- **优先级**: 中
- **影响**: 报表配置
- **操作**: 同上

#### 6. `app/api/v1/endpoints/report_center/bi.py`
- **状态**: ⏳ 待迁移
- **优先级**: 中
- **影响**: BI 报表
- **操作**: 同上

#### 7. `app/api/v1/endpoints/outsourcing/suppliers.py`
- **状态**: ⏳ 待迁移
- **优先级**: 高
- **影响**: 外协供应商管理
- **操作**: 同上

---

## 迁移步骤

### 阶段 1: 准备 (1-2 天)

- [ ] 创建迁移分支: `git checkout -b migrate/deprecated-models`
- [ ] 运行现有测试确保基线正常
- [ ] 创建测试用例覆盖所有使用场景

### 阶段 2: Supplier 迁移 (3-5 天)

按优先级逐个迁移：

1. [ ] 迁移 `app/api/v1/endpoints/suppliers.py`
   - [ ] 替换导入
   - [ ] 添加类型过滤
   - [ ] 更新测试
   - [ ] 运行测试验证

2. [ ] 迁移 `app/api/v1/endpoints/materials/suppliers.py`
   - [ ] 同上步骤

3. [ ] 迁移服务层文件
   - [ ] `app/services/urgent_purchase_from_shortage_service.py`
   - [ ] `app/services/inventory_analysis_service.py`
   - [ ] `app/api/v1/endpoints/business_support_orders/customer_registrations.py`

### 阶段 3: OutsourcingVendor 迁移 (3-5 天)

按优先级逐个迁移：

1. [ ] 迁移 `app/api/v1/endpoints/outsourcing/payments/crud.py`
   - [ ] 替换导入
   - [ ] 添加类型过滤
   - [ ] 更新字段名（vendor_code → supplier_code）
   - [ ] 更新测试
   - [ ] 运行测试验证

2. [ ] 迁移 `app/api/v1/endpoints/outsourcing/suppliers.py`
   - [ ] 同上步骤

3. [ ] 迁移其他文件
   - [ ] `app/api/v1/endpoints/outsourcing/payments/print.py`
   - [ ] `app/api/v1/endpoints/report_center/templates.py`
   - [ ] `app/api/v1/endpoints/report_center/rd_expense.py`
   - [ ] `app/api/v1/endpoints/report_center/configs.py`
   - [ ] `app/api/v1/endpoints/report_center/bi.py`

### 阶段 4: 验证 (2-3 天)

- [ ] 运行完整测试套件
- [ ] API 集成测试
- [ ] 前端功能测试
- [ ] 性能测试
- [ ] 代码审查

### 阶段 5: 清理 (可选，1 天)

- [ ] 确认所有代码已迁移
- [ ] 移除已弃用模型（或保留作为最终兼容层）
- [ ] 更新文档
- [ ] 合并到主分支

---

## 迁移模板

### Supplier → Vendor 模板

```python
# ========== 导入变更 ==========
# 旧
from app.models.material import Supplier

# 新
from app.models.vendor import Vendor

# ========== 查询变更 ==========
# 旧
supplier = db.query(Supplier).filter(
    Supplier.id == supplier_id
).first()

# 新
supplier = db.query(Vendor).filter(
    Vendor.id == supplier_id,
    Vendor.vendor_type == 'MATERIAL'  # 添加类型过滤
).first()

# ========== 创建变更 ==========
# 旧
supplier = Supplier(
    supplier_code=code,
    supplier_name=name,
    # ...
)

# 新
supplier = Vendor(
    supplier_code=code,
    supplier_name=name,
    vendor_type='MATERIAL',  # 必须指定类型
    # ...
)
```

### OutsourcingVendor → Vendor 模板

```python
# ========== 导入变更 ==========
# 旧
from app.models.outsourcing import OutsourcingVendor

# 新
from app.models.vendor import Vendor

# ========== 查询变更 ==========
# 旧
vendor = db.query(OutsourcingVendor).filter(
    OutsourcingVendor.vendor_code == code
).first()

# 新
vendor = db.query(Vendor).filter(
    Vendor.supplier_code == code,  # 注意字段名变更
    Vendor.vendor_type == 'OUTSOURCING'  # 添加类型过滤
).first()

# ========== 创建变更 ==========
# 旧
vendor = OutsourcingVendor(
    vendor_code=code,  # 注意字段名
    vendor_name=name,
    # ...
)

# 新
vendor = Vendor(
    supplier_code=code,  # 统一使用 supplier_code
    supplier_name=name,  # 统一使用 supplier_name
    vendor_type='OUTSOURCING',  # 必须指定类型
    # ...
)
```

---

## 注意事项

### 1. 字段名差异

**OutsourcingVendor** 使用:
- `vendor_code`
- `vendor_name`

**Vendor** 统一使用:
- `supplier_code`
- `supplier_name`

迁移时需要更新所有字段引用。

### 2. 类型过滤

所有查询必须添加 `vendor_type` 过滤，否则可能返回错误类型的数据。

### 3. 关系支持

迁移后可以使用 relationship:
```python
# 迁移前（视图，不支持）
# supplier.materials  # 不可用

# 迁移后（表，支持）
vendor.materials  # 可用
vendor.purchase_orders  # 可用
```

### 4. Schema 更新

如果使用 Pydantic Schema，需要更新:
```python
# 确保 Schema 支持 vendor_type 字段
class VendorResponse(BaseModel):
    supplier_code: str
    supplier_name: str
    vendor_type: str  # 新增
    # ...
```

---

## 测试检查清单

每个文件迁移后需要验证:

- [ ] 单元测试通过
- [ ] 查询返回正确数据
- [ ] 类型过滤正确
- [ ] 字段名更新正确
- [ ] 创建/更新操作正常
- [ ] 关系查询正常（如果使用）
- [ ] API 响应格式正确
- [ ] 前端功能正常

---

## 回滚计划

如果迁移出现问题:

1. **代码回滚**
   ```bash
   git revert <commit-hash>
   ```

2. **数据库无需回滚**
   - 视图仍然存在
   - 兼容层继续工作

3. **验证**
   - 运行测试确保回滚成功
   - 检查生产环境功能

---

## 时间估算

| 阶段 | 时间 | 说明 |
|------|------|------|
| 准备 | 1-2 天 | 创建分支、测试用例 |
| Supplier 迁移 | 3-5 天 | 5 个文件 |
| OutsourcingVendor 迁移 | 3-5 天 | 7 个文件 |
| 验证 | 2-3 天 | 完整测试 |
| 清理 | 1 天 | 可选 |
| **总计** | **10-16 天** | 约 2-3 周 |

---

## 成功标准

- ✅ 所有使用已弃用模型的代码已迁移
- ✅ 所有测试通过
- ✅ 生产环境验证通过
- ✅ 性能无退化
- ✅ 文档已更新

---

## 后续工作

迁移完成后:

1. **监控** - 观察生产环境 1-2 周
2. **文档** - 更新开发指南
3. **清理** - 考虑移除兼容层（可选）
4. **培训** - 确保团队了解新模型使用

---

## 相关文档

- [已弃用数据模型处理指南](../guides/deprecated_model_migration_guide.md)
- [已弃用 API 使用报告](../reports/deprecated_api_usage_report.md)
- [Vendor 模型文档](../../app/models/vendor.py)

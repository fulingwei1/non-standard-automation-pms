# 系统功能转换为权限完整指南

> 更新日期：2026-01-10

## 一、当前状态分析

### 1.1 功能与权限对比

| 指标 | 数量 | 说明 |
|------|:----:|------|
| **API模块总数** | 66 | 系统中定义的所有功能模块 |
| **API端点总数** | 1,498 | 所有GET/POST/PUT/DELETE端点 |
| **权限模块数** | 6 | 数据库中定义的权限模块 |
| **权限总数** | 67 | 数据库中定义的权限数量 |
| **有权限检查的模块** | 18 | 代码中使用了权限检查的模块 |
| **无权限检查的模块** | 48 | 代码中未使用权限检查的模块 |
| **权限覆盖率** | 7.5% | 113/1506 个端点有权限检查 |

### 1.2 已转换权限的模块

以下模块已经转换为权限：

1. **ecn** - 工程变更管理（27个权限）
2. **project** - 项目管理（17个权限）
3. **crm** - 客户关系管理（10个权限）
4. **system** - 系统管理（5个权限）
5. **supply** - 采购供应（4个权限）
6. **finance** - 财务管理（4个权限）

### 1.3 未转换权限的模块（48个）

以下模块尚未转换为权限，需要逐步转换：

- acceptance（验收管理）
- alerts（预警管理）
- assembly_kit（装配套件）
- bom（物料清单）
- bonus（奖金管理）
- budget（预算管理）
- business_support（业务支持）
- costs（成本管理）
- customers（客户管理）
- documents（文档管理）
- engineers（工程师管理）
- hourly_rate（时薪管理）
- hr_management（人事管理）
- issues（问题管理）
- kit_rate（齐套率）
- machines（设备管理）
- materials（物料管理）
- outsourcing（外协管理）
- performance（绩效管理）
- production（生产管理）
- progress（进度管理）
- projects（项目管理）
- purchase（采购管理）
- sales（销售管理）
- suppliers（供应商管理）
- ... 等48个模块

---

## 二、功能转换为权限的标准流程

### 2.1 转换步骤概览

```
1. 分析模块功能
   ↓
2. 设计权限结构
   ↓
3. 创建权限定义（数据库迁移脚本）
   ↓
4. 在API端点中添加权限检查
   ↓
5. 分配权限给角色
   ↓
6. 测试验证
```

### 2.2 详细步骤说明

#### 步骤1：分析模块功能

**目标**：了解模块有哪些功能，需要哪些权限

**方法**：
1. 查看API端点文件：`app/api/v1/endpoints/{module}.py`
2. 统计所有端点（GET/POST/PUT/DELETE）
3. 分析每个端点的功能（查看/创建/更新/删除/审批等）

**示例**：分析 `purchase` 模块

```python
# app/api/v1/endpoints/purchase.py
# 功能列表：
# - GET /purchase-orders/          → 查看采购订单列表
# - GET /purchase-orders/{id}       → 查看采购订单详情
# - POST /purchase-orders/         → 创建采购订单
# - PUT /purchase-orders/{id}      → 更新采购订单
# - PUT /purchase-orders/{id}/approve → 审批采购订单
# - POST /goods-receipts/           → 创建收货单
# ...
```

#### 步骤2：设计权限结构

**权限编码规范**：`{module}:{resource}:{action}`

**常见操作类型**：
- `read` - 查看
- `create` - 创建
- `update` - 更新
- `delete` - 删除
- `approve` - 审批
- `submit` - 提交
- `manage` - 管理（包含创建、更新、删除）

**示例**：为 `purchase` 模块设计权限

```python
# 采购订单权限
'purchase:order:read'      # 查看采购订单
'purchase:order:create'    # 创建采购订单
'purchase:order:update'   # 更新采购订单
'purchase:order:delete'   # 删除采购订单
'purchase:order:approve'  # 审批采购订单

# 收货单权限
'purchase:receipt:read'    # 查看收货单
'purchase:receipt:create'  # 创建收货单
'purchase:receipt:update'  # 更新收货单

# 或者使用粗粒度权限
'purchase:order:manage'    # 采购订单管理（包含所有操作）
'purchase:receipt:manage'  # 收货单管理
```

#### 步骤3：创建数据库迁移脚本

**文件命名**：`migrations/YYYYMMDD_{module}_permissions_{db_type}.sql`

**SQLite示例**：

```sql
-- migrations/20260110_purchase_permissions_sqlite.sql
BEGIN;

-- 采购订单权限
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description)
VALUES 
    ('purchase:order:read', '采购订单查看', 'purchase', 'order', 'read', '可以查看采购订单列表和详情'),
    ('purchase:order:create', '采购订单创建', 'purchase', 'order', 'create', '可以创建采购订单'),
    ('purchase:order:update', '采购订单更新', 'purchase', 'order', 'update', '可以更新采购订单'),
    ('purchase:order:delete', '采购订单删除', 'purchase', 'order', 'delete', '可以删除采购订单'),
    ('purchase:order:approve', '采购订单审批', 'purchase', 'order', 'approve', '可以审批采购订单'),
    
    -- 收货单权限
    ('purchase:receipt:read', '收货单查看', 'purchase', 'receipt', 'read', '可以查看收货单'),
    ('purchase:receipt:create', '收货单创建', 'purchase', 'receipt', 'create', '可以创建收货单'),
    ('purchase:receipt:update', '收货单更新', 'purchase', 'receipt', 'update', '可以更新收货单');

COMMIT;
```

**MySQL示例**：

```sql
-- migrations/20260110_purchase_permissions_mysql.sql
SET NAMES utf8mb4;

-- 采购订单权限
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description)
VALUES 
    ('purchase:order:read', '采购订单查看', 'purchase', 'order', 'read', '可以查看采购订单列表和详情'),
    ('purchase:order:create', '采购订单创建', 'purchase', 'order', 'create', '可以创建采购订单'),
    ('purchase:order:update', '采购订单更新', 'purchase', 'order', 'update', '可以更新采购订单'),
    ('purchase:order:delete', '采购订单删除', 'purchase', 'order', 'delete', '可以删除采购订单'),
    ('purchase:order:approve', '采购订单审批', 'purchase', 'order', 'approve', '可以审批采购订单'),
    
    -- 收货单权限
    ('purchase:receipt:read', '收货单查看', 'purchase', 'receipt', 'read', '可以查看收货单'),
    ('purchase:receipt:create', '收货单创建', 'purchase', 'receipt', 'create', '可以创建收货单'),
    ('purchase:receipt:update', '收货单更新', 'purchase', 'receipt', 'update', '可以更新收货单');
```

#### 步骤4：在API端点中添加权限检查

**方法1：使用 `require_permission`（推荐）**

```python
# app/api/v1/endpoints/purchase.py
from app.core.security import require_permission

@router.get("/purchase-orders/")
async def list_purchase_orders(
    current_user: User = Depends(require_permission("purchase:order:read")),
    db: Session = Depends(get_db),
):
    """获取采购订单列表 - 需要 purchase:order:read 权限"""
    ...

@router.post("/purchase-orders/")
async def create_purchase_order(
    order_data: PurchaseOrderCreate,
    current_user: User = Depends(require_permission("purchase:order:create")),
    db: Session = Depends(get_db),
):
    """创建采购订单 - 需要 purchase:order:create 权限"""
    ...

@router.put("/purchase-orders/{order_id}/approve")
async def approve_purchase_order(
    order_id: int,
    current_user: User = Depends(require_permission("purchase:order:approve")),
    db: Session = Depends(get_db),
):
    """审批采购订单 - 需要 purchase:order:approve 权限"""
    ...
```

**方法2：使用模块级权限检查函数**

```python
# app/core/security.py
def require_purchase_access():
    """采购模块访问权限检查"""
    def check(user: User = Depends(get_current_active_user)):
        if not has_purchase_access(user):
            raise HTTPException(
                status_code=403,
                detail="您没有权限访问采购模块"
            )
        return user
    return Depends(check)

# app/api/v1/endpoints/purchase.py
@router.get("/purchase-orders/")
async def list_purchase_orders(
    current_user: User = Depends(require_purchase_access()),
    db: Session = Depends(get_db),
):
    """获取采购订单列表"""
    ...
```

#### 步骤5：执行迁移脚本

```bash
# SQLite
sqlite3 data/app.db < migrations/20260110_purchase_permissions_sqlite.sql

# MySQL
mysql -u user -p database < migrations/20260110_purchase_permissions_mysql.sql
```

#### 步骤6：分配权限给角色

**方法1：通过SQL直接分配**

```sql
-- 为采购经理分配所有采购权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    r.id,
    p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.role_code = 'PU_MGR'
  AND p.module = 'purchase';

-- 为采购专员分配查看和管理权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    r.id,
    p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.role_code = 'PU'
  AND p.module = 'purchase'
  AND p.action IN ('read', 'create', 'update');
```

**方法2：通过API分配**

```python
# PUT /api/v1/roles/{role_id}/permissions
{
  "permission_ids": [1, 2, 3, ...]  # 权限ID列表
}
```

**方法3：通过角色管理页面**

访问 `/roles` 页面，选择角色，分配权限。

#### 步骤7：测试验证

1. **测试有权限的用户**：应该能正常访问
2. **测试无权限的用户**：应该返回 403 Forbidden
3. **测试权限边界**：验证不同权限级别的访问控制

---

## 三、批量转换工具

### 3.1 自动生成权限迁移脚本

系统提供了脚本来自动分析模块并生成权限定义：

```bash
# 分析模块并生成权限定义建议
python scripts/generate_module_permissions.py --module purchase

# 批量分析所有模块
python scripts/generate_module_permissions.py --all
```

### 3.2 权限分配脚本

```bash
# 为角色批量分配权限
python scripts/assign_permissions_to_roles.py \
    --role PU_MGR \
    --module purchase \
    --actions read,create,update,delete,approve
```

---

## 四、权限转换优先级建议

### 4.1 高优先级模块（核心业务）

1. **purchase** - 采购管理（已有部分权限，需完善）
2. **materials** - 物料管理
3. **bom** - BOM管理
4. **machines** - 设备管理
5. **projects** - 项目管理（已有部分权限，需完善）
6. **sales** - 销售管理
7. **acceptance** - 验收管理
8. **outsourcing** - 外协管理

### 4.2 中优先级模块（辅助功能）

1. **alerts** - 预警管理
2. **issues** - 问题管理
3. **performance** - 绩效管理
4. **bonus** - 奖金管理
5. **costs** - 成本管理
6. **production** - 生产管理

### 4.3 低优先级模块（系统功能）

1. **users** - 用户管理（已有system权限）
2. **roles** - 角色管理（已有system权限）
3. **organization** - 组织管理
4. **documents** - 文档管理
5. **notifications** - 通知管理

---

## 五、权限转换检查清单

转换每个模块时，请确认：

- [ ] 已分析模块的所有API端点
- [ ] 已设计权限结构（权限编码、名称、描述）
- [ ] 已创建数据库迁移脚本（SQLite和MySQL版本）
- [ ] 已在API端点中添加权限检查
- [ ] 已执行迁移脚本
- [ ] 已为相关角色分配权限
- [ ] 已测试有权限用户的访问
- [ ] 已测试无权限用户的访问（应返回403）
- [ ] 已更新文档说明

---

## 六、常见问题

### Q1: 如何决定使用粗粒度还是细粒度权限？

**A**: 
- **粗粒度权限**（如 `purchase:order:manage`）：适用于权限要求简单的模块，一个权限控制所有操作
- **细粒度权限**（如 `purchase:order:read`, `purchase:order:create`）：适用于需要精细控制的模块，不同角色需要不同操作权限

**建议**：
- 核心业务模块（采购、销售、项目）使用细粒度权限
- 辅助功能模块可以使用粗粒度权限

### Q2: 如何为现有模块添加权限而不影响现有功能？

**A**: 
1. 先创建权限定义（迁移脚本）
2. 为所有相关角色分配权限（确保现有用户不受影响）
3. 再在API端点中添加权限检查

### Q3: 如何处理需要多个权限的端点？

**A**: 
```python
# 方法1：使用多个权限检查（需要同时拥有）
@router.get("/complex-operation")
async def complex_operation(
    user1: User = Depends(require_permission("permission1")),
    user2: User = Depends(require_permission("permission2")),
):
    # user1 和 user2 是同一个用户，但需要同时拥有两个权限
    ...

# 方法2：在函数内部检查
@router.get("/complex-operation")
async def complex_operation(
    current_user: User = Depends(get_current_active_user),
):
    if not (has_permission(current_user, "permission1") and 
            has_permission(current_user, "permission2")):
        raise HTTPException(403, "需要同时拥有 permission1 和 permission2")
    ...
```

### Q4: 如何批量转换多个模块？

**A**: 
1. 按优先级逐个转换
2. 使用脚本批量生成权限定义
3. 使用脚本批量分配权限给角色
4. 逐个模块测试验证

---

## 七、相关文档

- [系统功能与权限完整对应关系](./SYSTEM_FUNCTIONS_PERMISSIONS_COMPLETE.md)
- [功能权限映射报告](./FUNCTION_PERMISSION_MAPPING.md)
- [权限系统完整指南](./PERMISSION_SYSTEM_COMPLETE_GUIDE.md)

---

## 八、下一步行动

1. **立即转换**：采购模块（purchase）- 已有部分权限，需要完善
2. **计划转换**：物料管理（materials）、BOM管理（bom）
3. **长期规划**：逐步转换所有66个模块

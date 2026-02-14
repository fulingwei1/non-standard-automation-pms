# 角色继承功能指南

## 📋 目录

1. [功能概述](#功能概述)
2. [核心概念](#核心概念)
3. [使用场景](#使用场景)
4. [技术实现](#技术实现)
5. [API 文档](#api-文档)
6. [使用示例](#使用示例)
7. [最佳实践](#最佳实践)
8. [常见问题](#常见问题)

---

## 功能概述

角色继承是权限管理系统的核心功能之一，允许子角色自动继承父角色的权限，实现权限的层级化管理。

### ✨ 主要特性

- ✅ **多级继承**：支持 Level 0 → 1 → 2 → 3 四层继承
- ✅ **权限合并**：子角色权限 = 自身权限 + 父角色权限
- ✅ **灵活控制**：通过 `inherit_permissions` 标志控制是否继承
- ✅ **循环检测**：自动检测并防止循环继承
- ✅ **性能优化**：三层缓存机制（权限、层级、继承链）
- ✅ **多租户隔离**：支持租户级权限过滤
- ✅ **可视化工具**：提供角色层级可视化脚本

---

## 核心概念

### 1. 角色层级 (Role Level)

角色按继承关系分为 4 个层级：

| Level | 名称 | 说明 | 示例 |
|-------|------|------|------|
| 0 | 根角色 | 最顶层，无父角色 | 超级管理员、系统管理员 |
| 1 | 一级子角色 | 继承根角色 | 部门经理、事业部负责人 |
| 2 | 二级子角色 | 继承一级角色 | 项目经理、团队主管 |
| 3 | 三级子角色 | 继承二级角色 | 普通员工、实习生 |

### 2. 继承标志 (inherit_permissions)

每个角色都有一个 `inherit_permissions` 布尔字段：

- **True**：继承父角色的所有权限
- **False**：不继承，只拥有自己的权限

### 3. 权限合并算法

```
子角色总权限 = 自身权限 ∪ 父角色权限 ∪ 祖父角色权限 ∪ ...
```

**注意**：
- 如果某一层 `inherit_permissions=False`，则继承链在该层中断
- 权限自动去重（使用 Set 集合）

### 4. 继承链 (Inheritance Chain)

从子角色向上追溯到根角色的路径，例如：

```
员工 → 项目经理 → 部门经理 → 超级管理员
```

---

## 使用场景

### 场景 1: 分级权限管理

**需求**：公司有多级管理层级，下级自动拥有上级的基础权限，同时有自己的特殊权限。

```
超级管理员 (Level 0)
├── 部门经理 (Level 1) - 继承超管基础权限 + 部门管理权限
│   └── 项目经理 (Level 2) - 继承经理权限 + 项目管理权限
│       └── 普通员工 (Level 3) - 继承PM权限 + 任务执行权限
```

### 场景 2: 权限模板复用

**需求**：多个角色共享基础权限，但有不同的扩展权限。

```
基础员工角色 (Level 0) - 查看、提交工时等基础权限
├── 销售角色 (Level 1, 继承) - 基础权限 + 客户管理
├── 研发角色 (Level 1, 继承) - 基础权限 + 代码提交
└── 财务角色 (Level 1, 继承) - 基础权限 + 财务审批
```

### 场景 3: 权限隔离

**需求**：某些角色不继承任何权限，完全独立。

```
审计角色 (Level 0, inherit_permissions=False)
- 仅有审计相关权限，不继承任何其他权限
```

---

## 技术实现

### 数据库模型

```python
class Role(Base):
    id = Column(Integer, primary_key=True)
    role_code = Column(String(50), unique=True)
    role_name = Column(String(100))
    parent_id = Column(Integer, ForeignKey('roles.id'))  # 父角色ID
    inherit_permissions = Column(Boolean, default=True)  # 是否继承
    # ... 其他字段
```

### 递归查询 SQL

系统使用递归 CTE（Common Table Expression）高效查询继承权限：

```sql
WITH RECURSIVE role_tree AS (
    -- 用户直接拥有的角色
    SELECT r.id, r.parent_id, r.inherit_permissions
    FROM roles r
    JOIN user_roles ur ON ur.role_id = r.id
    WHERE ur.user_id = :user_id

    UNION ALL

    -- 递归获取父角色（仅当 inherit_permissions=1 时）
    SELECT r.id, r.parent_id, r.inherit_permissions
    FROM roles r
    JOIN role_tree rt ON r.id = rt.parent_id
    WHERE rt.inherit_permissions = 1
)
SELECT DISTINCT ap.perm_code
FROM role_tree rt
JOIN role_api_permissions rap ON rt.id = rap.role_id
JOIN api_permissions ap ON rap.permission_id = ap.id
WHERE ap.is_active = 1
```

### 缓存机制

系统实现三层缓存提升性能：

1. **权限缓存** (`_permission_cache`)：缓存角色的所有继承权限
2. **层级缓存** (`_level_cache`)：缓存角色的层级数
3. **继承链缓存** (`_chain_cache`)：缓存角色的完整继承链

**缓存失效**：
- 修改角色时：`RoleInheritanceUtils.clear_cache(role_id)`
- 全局清除：`RoleInheritanceUtils.clear_cache()`

---

## API 文档

### RoleInheritanceUtils 类

#### get_inherited_permissions()

获取角色的所有权限（包含继承）。

```python
RoleInheritanceUtils.get_inherited_permissions(
    db: Session,
    role_id: int,
    tenant_id: Optional[int] = None
) -> Set[str]
```

**参数**：
- `db`: 数据库会话
- `role_id`: 角色ID
- `tenant_id`: 租户ID（用于多租户权限过滤）

**返回**：权限编码集合

**示例**：
```python
perms = RoleInheritanceUtils.get_inherited_permissions(db, role_id=5, tenant_id=1)
print(perms)  # {'project:read', 'project:create', 'user:view', ...}
```

---

#### get_role_chain()

获取角色的完整继承链。

```python
RoleInheritanceUtils.get_role_chain(
    db: Session,
    role_id: int
) -> List[Role]
```

**返回**：角色列表，按继承顺序 [当前角色, 父角色, 祖父角色, ...]

**示例**：
```python
chain = RoleInheritanceUtils.get_role_chain(db, role_id=5)
for role in chain:
    print(f"Level {role.id}: {role.role_name}")
# 输出：
# Level 5: 普通员工
# Level 3: 项目经理
# Level 1: 超级管理员
```

---

#### calculate_role_level()

计算角色在继承树中的层级。

```python
RoleInheritanceUtils.calculate_role_level(
    db: Session,
    role_id: int
) -> int
```

**返回**：层级数（0=根角色，1=一级子角色，...）

---

#### detect_circular_inheritance()

检测设置父角色是否会导致循环继承。

```python
RoleInheritanceUtils.detect_circular_inheritance(
    db: Session,
    role_id: int,
    new_parent_id: int
) -> bool
```

**返回**：True=会导致循环，False=安全

**示例**：
```python
# 假设 role2 是 role1 的子角色
is_circular = RoleInheritanceUtils.detect_circular_inheritance(db, role1, role2)
# 返回 True，因为 role1 -> role2 会形成循环
```

---

#### validate_role_hierarchy()

验证角色层级的完整性。

```python
RoleInheritanceUtils.validate_role_hierarchy(
    db: Session
) -> Tuple[bool, List[str]]
```

**返回**：(是否有效, 错误信息列表)

**示例**：
```python
is_valid, errors = RoleInheritanceUtils.validate_role_hierarchy(db)
if not is_valid:
    for error in errors:
        print(f"错误: {error}")
```

---

#### get_role_tree_data()

获取角色树数据（用于前端可视化）。

```python
RoleInheritanceUtils.get_role_tree_data(
    db: Session,
    tenant_id: Optional[int] = None
) -> List[Dict]
```

**返回**：角色树数据结构

**示例**：
```python
tree = RoleInheritanceUtils.get_role_tree_data(db, tenant_id=1)
# [
#   {
#     "id": 1,
#     "code": "admin",
#     "name": "超级管理员",
#     "level": 0,
#     "own_permissions": 50,
#     "total_permissions": 50,
#     "children": [
#       {
#         "id": 2,
#         "code": "manager",
#         "name": "部门经理",
#         "level": 1,
#         "own_permissions": 10,
#         "total_permissions": 60,
#         "children": [...]
#       }
#     ]
#   }
# ]
```

---

## 使用示例

### 示例 1: 创建继承角色

```python
from app.models.user import Role
from app.core.database import SessionLocal

db = SessionLocal()

# 创建父角色
parent_role = Role(
    role_code="department_manager",
    role_name="部门经理",
    parent_id=None,  # 根角色
    inherit_permissions=False,
    is_active=True
)
db.add(parent_role)
db.commit()

# 创建子角色
child_role = Role(
    role_code="project_manager",
    role_name="项目经理",
    parent_id=parent_role.id,  # 设置父角色
    inherit_permissions=True,  # 继承父角色权限
    is_active=True
)
db.add(child_role)
db.commit()
```

---

### 示例 2: 分配权限并验证继承

```python
from app.models.user import ApiPermission, RoleApiPermission
from app.utils.role_inheritance_utils import RoleInheritanceUtils

# 给父角色分配权限
parent_perm = ApiPermission(
    perm_code="department:manage",
    perm_name="部门管理",
    is_active=True
)
db.add(parent_perm)
db.commit()

db.add(RoleApiPermission(role_id=parent_role.id, permission_id=parent_perm.id))
db.commit()

# 给子角色分配自己的权限
child_perm = ApiPermission(
    perm_code="project:manage",
    perm_name="项目管理",
    is_active=True
)
db.add(child_perm)
db.commit()

db.add(RoleApiPermission(role_id=child_role.id, permission_id=child_perm.id))
db.commit()

# 验证子角色的权限（应包含继承的权限）
child_permissions = RoleInheritanceUtils.get_inherited_permissions(db, child_role.id)
print(child_permissions)
# 输出: {'department:manage', 'project:manage'}
```

---

### 示例 3: 检测循环继承

```python
from app.utils.role_inheritance_utils import RoleInheritanceUtils

# 尝试设置循环继承
is_circular = RoleInheritanceUtils.detect_circular_inheritance(
    db,
    role_id=parent_role.id,
    new_parent_id=child_role.id
)

if is_circular:
    print("⚠️ 警告：这会导致循环继承！")
else:
    parent_role.parent_id = child_role.id
    db.commit()
```

---

### 示例 4: 可视化角色层级

```bash
# 文本格式
python scripts/visualize_role_hierarchy.py --format text

# JSON 格式
python scripts/visualize_role_hierarchy.py --format json --output roles.json

# HTML 格式（在浏览器中查看）
python scripts/visualize_role_hierarchy.py --format html --output roles.html

# 验证层级完整性
python scripts/visualize_role_hierarchy.py --validate

# 查看单个角色详情
python scripts/visualize_role_hierarchy.py --role 5
```

---

## 最佳实践

### 1. 设计原则

✅ **DO**：
- 保持继承层级在 3 层以内（Level 0-2）
- 使用语义化的角色编码（如 `dept_manager`、`project_member`）
- 在根角色设置通用权限，子角色设置特定权限
- 定期验证角色层级（`validate_role_hierarchy()`）

❌ **DON'T**：
- 避免过深的继承（超过 4 层）
- 避免在中间层随意设置 `inherit_permissions=False`
- 避免循环继承

---

### 2. 性能优化

```python
# ✅ 批量查询用户权限时，使用缓存
from app.utils.role_inheritance_utils import RoleInheritanceUtils

# 第一次查询会缓存结果
perms1 = RoleInheritanceUtils.get_inherited_permissions(db, role_id)

# 后续查询直接从缓存读取
perms2 = RoleInheritanceUtils.get_inherited_permissions(db, role_id)

# 修改角色后清除缓存
role.description = "新描述"
db.commit()
RoleInheritanceUtils.clear_cache(role.id)
```

---

### 3. 多租户隔离

```python
# ✅ 查询租户权限时，传入 tenant_id
perms = RoleInheritanceUtils.get_inherited_permissions(
    db,
    role_id=5,
    tenant_id=1  # 只返回租户1的权限
)
```

---

### 4. 角色设计示例

#### 企业组织架构

```
超级管理员 (Level 0) - 系统所有权限
├── 事业部总监 (Level 1, 继承) - 基础权限 + 事业部管理
│   └── 部门经理 (Level 2, 继承) - 基础权限 + 部门管理
│       └── 项目经理 (Level 3, 继承) - 基础权限 + 项目管理
└── 审计角色 (Level 1, 不继承) - 仅审计权限
```

#### 项目团队

```
项目负责人 (Level 0) - 项目所有权限
├── 技术负责人 (Level 1, 继承) - 项目权限 + 技术管理
│   └── 开发工程师 (Level 2, 继承) - 项目权限 + 代码提交
├── 产品负责人 (Level 1, 继承) - 项目权限 + 需求管理
└── 测试工程师 (Level 1, 继承) - 项目权限 + 测试管理
```

---

## 常见问题

### Q1: 如何查看角色的继承关系？

**A**: 使用可视化工具：

```bash
# 查看所有角色树
python scripts/visualize_role_hierarchy.py --format text

# 查看特定角色
python scripts/visualize_role_hierarchy.py --role 5
```

---

### Q2: 如何修改角色的父角色？

**A**: 先检测循环，再修改：

```python
from app.utils.role_inheritance_utils import RoleInheritanceUtils

# 检测是否会导致循环
is_circular = RoleInheritanceUtils.detect_circular_inheritance(
    db, role_id=5, new_parent_id=3
)

if not is_circular:
    role = db.query(Role).filter(Role.id == 5).first()
    role.parent_id = 3
    db.commit()
    # 清除缓存
    RoleInheritanceUtils.clear_cache(5)
else:
    print("错误：会导致循环继承")
```

---

### Q3: 为什么子角色没有继承到父角色的权限？

**A**: 检查以下几点：

1. 子角色的 `inherit_permissions` 是否为 `True`
2. 父角色和子角色是否都处于 `is_active=True` 状态
3. 中间层角色的 `inherit_permissions` 是否为 `True`（多级继承时）
4. 缓存是否过期（尝试清除缓存）

```python
# 调试工具
chain = RoleInheritanceUtils.get_role_chain(db, role_id)
for role in chain:
    print(f"{role.role_name}: inherit={role.inherit_permissions}, active={role.is_active}")
```

---

### Q4: 如何实现"权限黑名单"（子角色排除某些父权限）？

**A**: 当前不支持权限黑名单。建议：

1. 使用 `inherit_permissions=False`，手动分配权限
2. 创建独立的角色，不使用继承
3. 在应用层做权限过滤

---

### Q5: 继承层级最多支持几层？

**A**: 理论上无限制，但建议：

- **推荐**：3 层（Level 0-2）
- **最大**：4 层（Level 0-3）
- 超过 4 层会触发验证警告

---

## 附录

### 相关文件

- **模型定义**：`app/models/user.py`
- **工具类**：`app/utils/role_inheritance_utils.py`
- **可视化脚本**：`scripts/visualize_role_hierarchy.py`
- **测试用例**：`tests/test_role_inheritance.py`
- **服务层**：`app/services/permission_service.py`

### 相关数据库表

- `roles` - 角色表
- `role_api_permissions` - 角色权限关联表
- `api_permissions` - API权限表
- `user_roles` - 用户角色关联表

---

## 更新日志

- **2026-02-14**：初版发布，支持 4 层继承、循环检测、可视化工具
- **TBD**：计划支持权限黑名单、动态继承规则

---

**文档维护者**: 角色继承工作组  
**最后更新**: 2026-02-14

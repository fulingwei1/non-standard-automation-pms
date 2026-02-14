# 角色继承功能演示与示例

## 🎯 快速开始

### 1. 运行功能验证

```bash
cd ~/.openclaw/workspace/non-standard-automation-pms
python3 verify_role_inheritance.py
```

### 2. 可视化角色层级

```bash
# 查看文本格式
python3 scripts/visualize_role_hierarchy.py --format text

# 生成HTML可视化
python3 scripts/visualize_role_hierarchy.py --format html --output roles.html

# 验证层级完整性
python3 scripts/visualize_role_hierarchy.py --validate
```

---

## 📚 实战示例

### 示例 1: 创建企业角色体系

```python
from app.models.user import Role, ApiPermission, RoleApiPermission
from app.core.database import SessionLocal

db = SessionLocal()

# ========== Level 0: 超级管理员 ==========
super_admin = Role(
    role_code="super_admin",
    role_name="超级管理员",
    parent_id=None,
    inherit_permissions=False,
    is_active=True
)
db.add(super_admin)
db.commit()

# 分配系统级权限
system_perms = ["system:view", "system:manage", "user:manage"]
for perm_code in system_perms:
    perm = ApiPermission(
        perm_code=perm_code,
        perm_name=f"权限-{perm_code}",
        module="system",
        is_active=True
    )
    db.add(perm)
    db.commit()
    
    db.add(RoleApiPermission(
        role_id=super_admin.id,
        permission_id=perm.id
    ))
db.commit()

# ========== Level 1: 部门经理 ==========
dept_manager = Role(
    role_code="dept_manager",
    role_name="部门经理",
    parent_id=super_admin.id,  # 继承超级管理员
    inherit_permissions=True,   # 启用继承
    is_active=True
)
db.add(dept_manager)
db.commit()

# 部门经理自己的权限
dept_perms = ["dept:manage", "employee:view"]
for perm_code in dept_perms:
    perm = ApiPermission(
        perm_code=perm_code,
        perm_name=f"权限-{perm_code}",
        module="department",
        is_active=True
    )
    db.add(perm)
    db.commit()
    
    db.add(RoleApiPermission(
        role_id=dept_manager.id,
        permission_id=perm.id
    ))
db.commit()

# ========== Level 2: 项目经理 ==========
project_manager = Role(
    role_code="project_manager",
    role_name="项目经理",
    parent_id=dept_manager.id,  # 继承部门经理
    inherit_permissions=True,
    is_active=True
)
db.add(project_manager)
db.commit()

# 项目经理自己的权限
project_perms = ["project:create", "project:manage"]
for perm_code in project_perms:
    perm = ApiPermission(
        perm_code=perm_code,
        perm_name=f"权限-{perm_code}",
        module="project",
        is_active=True
    )
    db.add(perm)
    db.commit()
    
    db.add(RoleApiPermission(
        role_id=project_manager.id,
        permission_id=perm.id
    ))
db.commit()

# ========== Level 3: 普通员工 ==========
employee = Role(
    role_code="employee",
    role_name="普通员工",
    parent_id=project_manager.id,
    inherit_permissions=True,
    is_active=True
)
db.add(employee)
db.commit()

# 员工自己的权限
employee_perms = ["task:execute", "timesheet:submit"]
for perm_code in employee_perms:
    perm = ApiPermission(
        perm_code=perm_code,
        perm_name=f"权限-{perm_code}",
        module="employee",
        is_active=True
    )
    db.add(perm)
    db.commit()
    
    db.add(RoleApiPermission(
        role_id=employee.id,
        permission_id=perm.id
    ))
db.commit()

print("✅ 企业角色体系创建完成")
```

### 查看普通员工的所有权限

```python
from app.utils.role_inheritance_utils import RoleInheritanceUtils

# 普通员工继承的所有权限
employee_perms = RoleInheritanceUtils.get_inherited_permissions(db, employee.id)

print(f"普通员工总权限数: {len(employee_perms)}")
print(f"权限列表:")
for perm in sorted(employee_perms):
    print(f"  - {perm}")

# 预期输出:
# 普通员工总权限数: 9
# 权限列表:
#   - dept:manage
#   - employee:view
#   - project:create
#   - project:manage
#   - system:manage
#   - system:view
#   - task:execute
#   - timesheet:submit
#   - user:manage
```

---

### 示例 2: 权限隔离角色

```python
# 创建审计角色（不继承任何权限）
auditor = Role(
    role_code="auditor",
    role_name="审计员",
    parent_id=None,  # 独立角色
    inherit_permissions=False,
    is_active=True
)
db.add(auditor)
db.commit()

# 仅分配审计相关权限
audit_perms = ["audit:view", "audit:export", "log:read"]
for perm_code in audit_perms:
    perm = ApiPermission(
        perm_code=perm_code,
        perm_name=f"权限-{perm_code}",
        module="audit",
        is_active=True
    )
    db.add(perm)
    db.commit()
    
    db.add(RoleApiPermission(
        role_id=auditor.id,
        permission_id=perm.id
    ))
db.commit()

# 审计员只有自己的3个权限，不继承其他角色
auditor_perms = RoleInheritanceUtils.get_inherited_permissions(db, auditor.id)
print(f"审计员权限: {auditor_perms}")
# 输出: {'audit:view', 'audit:export', 'log:read'}
```

---

### 示例 3: 检测并防止循环继承

```python
from app.utils.role_inheritance_utils import RoleInheritanceUtils

# 假设我们想让 super_admin 继承 employee（这会形成循环）
is_circular = RoleInheritanceUtils.detect_circular_inheritance(
    db,
    role_id=super_admin.id,
    new_parent_id=employee.id
)

if is_circular:
    print("⚠️ 检测到循环继承！禁止此操作")
else:
    super_admin.parent_id = employee.id
    db.commit()
    print("✅ 父角色设置成功")
```

---

### 示例 4: 动态修改继承关系

```python
# 场景：项目经理升职为部门总监，直接继承超级管理员
from app.utils.role_inheritance_utils import RoleInheritanceUtils

# 修改前：查看项目经理的层级和权限
before_level = RoleInheritanceUtils.calculate_role_level(db, project_manager.id)
before_perms = RoleInheritanceUtils.get_inherited_permissions(db, project_manager.id)

print(f"修改前 - Level: {before_level}, 权限数: {len(before_perms)}")

# 修改父角色
project_manager.parent_id = super_admin.id  # 改为直接继承超级管理员
db.commit()

# 清除缓存
RoleInheritanceUtils.clear_cache(project_manager.id)

# 修改后
after_level = RoleInheritanceUtils.calculate_role_level(db, project_manager.id)
after_perms = RoleInheritanceUtils.get_inherited_permissions(db, project_manager.id)

print(f"修改后 - Level: {after_level}, 权限数: {len(after_perms)}")
```

---

### 示例 5: 用户拥有多个角色

```python
from app.models.user import User, UserRole
from app.utils.role_inheritance_utils import RoleInheritanceUtils

# 创建用户
user = User(
    username="zhang_san",
    real_name="张三",
    password_hash="...",
    is_active=True
)
db.add(user)
db.commit()

# 分配多个角色
db.add(UserRole(user_id=user.id, role_id=project_manager.id))
db.add(UserRole(user_id=user.id, role_id=auditor.id))
db.commit()

# 合并多个角色的权限
user_role_ids = [project_manager.id, auditor.id]
merged_perms = RoleInheritanceUtils.merge_role_permissions(db, user_role_ids)

print(f"用户总权限数: {len(merged_perms)}")
print(f"权限来源:")
print(f"  - 项目经理及其继承: {len(RoleInheritanceUtils.get_inherited_permissions(db, project_manager.id))}个")
print(f"  - 审计员: {len(RoleInheritanceUtils.get_inherited_permissions(db, auditor.id))}个")
```

---

## 🔧 管理工具

### 1. 验证角色层级完整性

```python
from app.utils.role_inheritance_utils import RoleInheritanceUtils

is_valid, errors = RoleInheritanceUtils.validate_role_hierarchy(db)

if is_valid:
    print("✅ 角色层级验证通过")
else:
    print("❌ 发现以下问题:")
    for error in errors:
        print(f"  - {error}")
```

### 2. 查看继承统计

```python
from app.utils.role_inheritance_utils import RoleInheritanceUtils

stats = RoleInheritanceUtils.get_inheritance_statistics(db)

print("📊 角色继承统计")
print(f"总角色数: {stats['total_roles']}")
print(f"根角色数: {stats['root_roles']}")
print(f"继承角色数: {stats['inherited_roles']}")
print(f"非继承角色数: {stats['non_inherited_roles']}")
print(f"最大继承深度: Level {stats['max_depth']}")
print(f"缓存状态: {stats['cache_size']}")
```

### 3. 查看角色继承链

```python
from app.utils.role_inheritance_utils import RoleInheritanceUtils

chain = RoleInheritanceUtils.get_role_chain(db, employee.id)

print("📋 员工角色继承链:")
for i, role in enumerate(chain):
    print(f"  Level {i}: {role.role_name} ({role.role_code})")
    
# 输出:
# Level 0: 普通员工 (employee)
# Level 1: 项目经理 (project_manager)
# Level 2: 部门经理 (dept_manager)
# Level 3: 超级管理员 (super_admin)
```

---

## 📊 性能优化示例

### 使用缓存提升查询性能

```python
from app.utils.role_inheritance_utils import RoleInheritanceUtils
import time

# 第一次查询（查数据库，写入缓存）
start = time.time()
perms1 = RoleInheritanceUtils.get_inherited_permissions(db, employee.id)
time1 = time.time() - start
print(f"第一次查询耗时: {time1*1000:.2f}ms")

# 第二次查询（从缓存读取）
start = time.time()
perms2 = RoleInheritanceUtils.get_inherited_permissions(db, employee.id)
time2 = time.time() - start
print(f"第二次查询耗时: {time2*1000:.2f}ms")

print(f"性能提升: {(time1/time2):.1f}x")
```

---

## 🎨 可视化示例

### 生成角色树数据

```python
from app.utils.role_inheritance_utils import RoleInheritanceUtils
import json

tree = RoleInheritanceUtils.get_role_tree_data(db)

# 美化输出
print(json.dumps(tree, indent=2, ensure_ascii=False))
```

**输出示例**:

```json
[
  {
    "id": 1,
    "code": "super_admin",
    "name": "超级管理员",
    "level": 0,
    "parent_id": null,
    "inherit_permissions": false,
    "own_permissions": 3,
    "total_permissions": 3,
    "children": [
      {
        "id": 2,
        "code": "dept_manager",
        "name": "部门经理",
        "level": 1,
        "parent_id": 1,
        "inherit_permissions": true,
        "own_permissions": 2,
        "total_permissions": 5,
        "children": [
          {
            "id": 3,
            "code": "project_manager",
            "name": "项目经理",
            "level": 2,
            "parent_id": 2,
            "inherit_permissions": true,
            "own_permissions": 2,
            "total_permissions": 7,
            "children": [
              {
                "id": 4,
                "code": "employee",
                "name": "普通员工",
                "level": 3,
                "parent_id": 3,
                "inherit_permissions": true,
                "own_permissions": 2,
                "total_permissions": 9,
                "children": []
              }
            ]
          }
        ]
      }
    ]
  }
]
```

---

## 🚀 API 集成示例

### 在 FastAPI 中使用

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.utils.role_inheritance_utils import RoleInheritanceUtils

router = APIRouter()

@router.get("/roles/{role_id}/permissions")
def get_role_permissions(role_id: int, db: Session = Depends(get_db)):
    """获取角色的所有权限（含继承）"""
    perms = RoleInheritanceUtils.get_inherited_permissions(db, role_id)
    return {
        "role_id": role_id,
        "total_permissions": len(perms),
        "permissions": sorted(perms)
    }

@router.get("/roles/{role_id}/chain")
def get_role_chain(role_id: int, db: Session = Depends(get_db)):
    """获取角色继承链"""
    chain = RoleInheritanceUtils.get_role_chain(db, role_id)
    return {
        "role_id": role_id,
        "chain_length": len(chain),
        "chain": [
            {
                "level": i,
                "id": r.id,
                "code": r.role_code,
                "name": r.role_name,
                "inherit_permissions": r.inherit_permissions
            }
            for i, r in enumerate(chain)
        ]
    }

@router.get("/roles/tree")
def get_role_tree(db: Session = Depends(get_db)):
    """获取角色树"""
    tree = RoleInheritanceUtils.get_role_tree_data(db)
    return {"tree": tree}

@router.post("/roles/{role_id}/parent")
def update_parent_role(
    role_id: int,
    parent_id: int,
    db: Session = Depends(get_db)
):
    """更新父角色（带循环检测）"""
    # 检测循环
    is_circular = RoleInheritanceUtils.detect_circular_inheritance(
        db, role_id, parent_id
    )
    
    if is_circular:
        return {"error": "会导致循环继承"}, 400
    
    # 更新
    role = db.query(Role).filter(Role.id == role_id).first()
    role.parent_id = parent_id
    db.commit()
    
    # 清除缓存
    RoleInheritanceUtils.clear_cache(role_id)
    
    return {"message": "父角色更新成功"}
```

---

## 📝 总结

本演示涵盖了角色继承功能的所有核心用法：

- ✅ 创建多级角色体系
- ✅ 权限自动继承和合并
- ✅ 循环继承检测
- ✅ 继承关系可视化
- ✅ 性能缓存优化
- ✅ API 集成
- ✅ 完整性验证

详细文档请参阅：[角色继承功能指南](./role-inheritance-guide.md)

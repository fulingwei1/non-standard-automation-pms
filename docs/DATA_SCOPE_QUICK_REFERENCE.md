# 数据范围过滤快速参考

## 一分钟快速上手

### 基本用法

```python
from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

# 过滤查询
query = DataScopeServiceEnhanced.apply_data_scope(
    query=query,
    db=db,
    user=current_user,
    resource_type="project"
)

# 检查权限
can_access = DataScopeServiceEnhanced.can_access_data(
    db=db,
    user=current_user,
    resource_type="project",
    data=project_instance
)
```

---

## 数据范围速查表

| 范围 | 代码 | 可见范围 | 使用场景 |
|------|------|----------|----------|
| 全部 | `ALL` | 所有数据 | 超级管理员 |
| 事业部 | `BUSINESS_UNIT` | 本事业部及子部门 | 事业部总监 |
| 部门 | `DEPARTMENT` | 本部门及子部门 | 部门经理 |
| 团队 | `TEAM` | 本团队 | 团队leader |
| 项目 | `PROJECT` | 参与的项目 | 项目成员 |
| 个人 | `OWN` | 自己的数据 | 普通员工 |
| 下属 | `SUBORDINATE` | 自己+直接下属 | 经理 |

---

## 常用模式

### 1. API 端点标准模式

```python
@router.get("/api/resources")
def list_resources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Resource)
    query = DataScopeServiceEnhanced.apply_data_scope(
        query, db, current_user, "resource"
    )
    return query.all()
```

### 2. 详情权限检查模式

```python
@router.get("/api/resources/{id}")
def get_resource(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resource = db.query(Resource).filter(Resource.id == id).first()
    if not resource:
        raise HTTPException(404)
    
    if not DataScopeServiceEnhanced.can_access_data(
        db, current_user, "resource", resource
    ):
        raise HTTPException(403)
    
    return resource
```

### 3. 自定义字段映射

```python
query = DataScopeServiceEnhanced.apply_data_scope(
    query=query,
    db=db,
    user=current_user,
    resource_type="purchase_order",
    org_field="department_id",     # 组织字段
    owner_field="requester_id",    # 所有者字段
    pm_field="project_manager_id"  # PM字段
)
```

### 4. 通用过滤器模式

```python
from app.services.data_scope.generic_filter import GenericFilterService
from app.services.data_scope.config import DataScopeConfig

config = DataScopeConfig(
    owner_field="created_by",
    additional_owner_fields=["assignee_id", "reviewer_id"],
    project_field="project_id",
    dept_through_project=True
)

query = GenericFilterService.filter_by_scope(
    db, query, Model, current_user, config
)
```

---

## 字段配置速查

### 标准字段名

```python
# 组织相关
org_field = "org_unit_id"      # 组织单元ID
org_field = "department_id"    # 部门ID
org_field = "dept_id"          # 部门ID（简写）

# 所有者相关
owner_field = "created_by"     # 创建者
owner_field = "owner_id"       # 拥有者
owner_field = "assignee_id"    # 分配人
owner_field = "requester_id"   # 申请人

# 项目相关
pm_field = "pm_id"             # 项目经理
pm_field = "project_id"        # 项目ID
```

---

## 调试技巧

### 1. 查看用户组织

```python
orgs = DataScopeServiceEnhanced.get_user_org_units(db, user_id)
print(f"用户组织: {orgs}")
```

### 2. 查看可访问范围

```python
accessible = DataScopeServiceEnhanced.get_accessible_org_units(
    db, user_id, scope_type
)
print(f"可访问组织: {accessible}")
```

### 3. 启用调试日志

```python
import logging
logging.getLogger("app.services.data_scope_service_enhanced").setLevel(logging.DEBUG)
```

### 4. 检查权限配置

```python
from app.services.permission_service import PermissionService
scopes = PermissionService.get_user_data_scopes(db, user_id)
print(f"用户权限: {scopes}")
```

---

## 常见错误

### ❌ 错误 1: 字段名拼写错误

```python
# 错误
query = DataScopeServiceEnhanced.apply_data_scope(
    query, db, user, "project",
    org_field="dept_idd"  # 拼写错误
)

# 正确
query = DataScopeServiceEnhanced.apply_data_scope(
    query, db, user, "project",
    org_field="dept_id"
)
```

### ❌ 错误 2: 忘记指定resource_type

```python
# 错误
query = DataScopeServiceEnhanced.apply_data_scope(
    query, db, user
)  # 缺少 resource_type

# 正确
query = DataScopeServiceEnhanced.apply_data_scope(
    query, db, user, "project"
)
```

### ❌ 错误 3: 在超级管理员模式下调试

```python
# 如果 user.is_superuser == True
# 所有过滤都会被跳过！

# 调试时使用普通用户
user.is_superuser = False  # 临时设置
```

---

## 性能检查清单

- [ ] 组织表有 `path` 字段
- [ ] 添加了必要的数据库索引
- [ ] 使用 `in_()` 而不是循环查询
- [ ] 考虑添加缓存（大规模应用）
- [ ] 监控慢查询日志

---

## 安全检查清单

- [ ] API 端点都应用了数据权限过滤
- [ ] 详情查看有二次权限检查
- [ ] 更新/删除操作验证所有权
- [ ] 敏感操作记录日志
- [ ] 异常时拒绝访问（安全优先）

---

## 资源链接

- 📖 [完整使用指南](./DATA_SCOPE_USAGE_GUIDE.md)
- 🔧 [优化报告](./data_scope_optimization_report.md)
- 💻 [源代码](../app/services/data_scope_service_enhanced.py)
- 🧪 [测试用例](../tests/unit/test_data_scope_enhanced.py)

---

**提示**: 遇到问题？先检查日志，确认字段名，验证用户组织分配！

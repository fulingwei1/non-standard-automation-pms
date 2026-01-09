# 数据权限控制指南

> 更新日期：2026-01-XX

## 一、数据权限控制概述

### 1.1 核心概念

系统通过**角色的数据权限范围（Data Scope）**来控制用户可以看到哪些数据：

- **功能权限**：控制用户能否访问某个API（功能）
- **数据权限**：控制用户可以看到哪些数据（数据范围）

### 1.2 数据权限范围类型

| 范围 | 说明 | 适用角色示例 | 数据可见性 |
|------|------|------------|-----------|
| **ALL** | 全部可见 | 总经理、董事长、系统管理员 | 可以看到所有数据 |
| **DEPT** | 同部门可见 | 部门经理、部门成员 | 只能看到同部门的数据 |
| **PROJECT** | 参与项目可见 | 项目经理、项目成员、工程师 | 只能看到参与的项目 |
| **OWN** | 自己创建/负责的可见 | 普通员工 | 只能看到自己创建或负责的数据 |
| **CUSTOMER** | 客户门户 | 客户用户 | 只能看到自己的项目 |

---

## 二、数据权限控制机制

### 2.1 工作原理

```
用户请求数据
  ↓
获取用户的所有角色
  ↓
计算数据权限范围（取最宽松的）
  ↓
根据数据权限范围过滤数据
  ↓
返回过滤后的数据
```

### 2.2 权限范围优先级

当用户有多个角色时，系统取**最宽松**的数据权限范围：

```
ALL > DEPT > PROJECT > OWN
```

**示例**：
- 用户同时拥有"项目经理"（PROJECT）和"部门经理"（DEPT）两个角色
- 最终数据权限范围 = **DEPT**（取最宽松的）

---

## 三、实际应用场景

### 3.1 场景1：总经理 vs 工程师访问项目数据

#### 需求
- **总经理**：可以看到所有项目
- **工程师**：只能看到自己参与的项目

#### 配置步骤

**步骤1：配置总经理角色的数据权限范围**

```python
# 通过角色管理页面或API
PUT /api/v1/roles/{role_id}
{
  "role_code": "gm",
  "role_name": "总经理",
  "data_scope": "ALL"  # 全部可见
}
```

**步骤2：配置工程师角色的数据权限范围**

```python
# 通过角色管理页面或API
PUT /api/v1/roles/{role_id}
{
  "role_code": "engineer",
  "role_name": "工程师",
  "data_scope": "PROJECT"  # 参与项目可见
}
```

**步骤3：分配角色给用户**

```python
# 总经理用户
PUT /api/v1/users/{gm_user_id}/roles
{
  "role_ids": [1]  # 总经理角色ID
}

# 工程师用户
PUT /api/v1/users/{engineer_user_id}/roles
{
  "role_ids": [2]  # 工程师角色ID
}
```

#### 效果

**总经理访问项目列表**：
```python
GET /api/v1/projects
# 返回：所有项目（不进行过滤）
```

**工程师访问项目列表**：
```python
GET /api/v1/projects
# 返回：只返回该工程师参与的项目（通过project_members表过滤）
```

### 3.2 场景2：部门经理只能看到同部门项目

#### 配置

```python
PUT /api/v1/roles/{role_id}
{
  "role_code": "dept_manager",
  "role_name": "部门经理",
  "data_scope": "DEPT"  # 同部门可见
}
```

#### 工作原理

1. 系统获取用户的部门信息（`user.department`）
2. 通过部门名称查找部门ID
3. 过滤项目：`Project.dept_id == 部门ID`

### 3.3 场景3：普通员工只能看到自己负责的项目

#### 配置

```python
PUT /api/v1/roles/{role_id}
{
  "role_code": "user",
  "role_name": "普通员工",
  "data_scope": "OWN"  # 自己创建/负责的可见
}
```

#### 工作原理

过滤条件：
- `Project.created_by == user.id`（自己创建的项目）
- 或 `Project.pm_id == user.id`（自己负责的项目）

---

## 四、代码实现

### 4.1 数据权限过滤（自动应用）

在项目列表API中，系统会自动应用数据权限过滤：

```python
# app/api/v1/endpoints/projects.py
@router.get("/", response_model=PaginatedResponse[ProjectListResponse])
def read_projects(
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(deps.get_db),
    ...
):
    query = db.query(Project)
    
    # ... 其他筛选条件 ...
    
    # 自动应用数据权限过滤
    from app.services.data_scope_service import DataScopeService
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)
    
    # 返回过滤后的数据
    return query.all()
```

### 4.2 数据权限检查（单个项目）

在访问单个项目时，系统会检查权限：

```python
# app/api/v1/endpoints/projects.py
@router.get("/{project_id}")
def get_project(
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(deps.get_db),
):
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)
    
    # 返回项目详情
    return project
```

### 4.3 数据权限范围计算

```python
# app/services/data_scope_service.py
def get_user_data_scope(db: Session, user: User) -> str:
    """获取用户的数据权限范围（取最宽松的）"""
    if user.is_superuser:
        return DataScopeEnum.ALL.value
    
    # 获取用户所有角色的数据权限范围
    scopes = set()
    for user_role in user.roles:
        role = user_role.role
        if role and role.is_active:
            scopes.add(role.data_scope)
    
    # 返回最宽松的权限
    if DataScopeEnum.ALL.value in scopes:
        return DataScopeEnum.ALL.value
    elif DataScopeEnum.DEPT.value in scopes:
        return DataScopeEnum.DEPT.value
    elif DataScopeEnum.PROJECT.value in scopes:
        return DataScopeEnum.PROJECT.value
    else:
        return DataScopeEnum.OWN.value
```

---

## 五、配置指南

### 5.1 通过角色管理页面配置

1. 登录系统管理员账号
2. 进入「系统管理」→「角色管理」
3. 选择要配置的角色
4. 编辑「数据权限范围」字段
5. 选择合适的数据权限范围：
   - **全部可见（ALL）**：总经理、董事长、系统管理员
   - **同部门可见（DEPT）**：部门经理、部门成员
   - **参与项目可见（PROJECT）**：项目经理、工程师、项目成员
   - **自己创建/负责的可见（OWN）**：普通员工
6. 保存

### 5.2 通过API配置

```python
# 更新角色的数据权限范围
PUT /api/v1/roles/{role_id}
{
  "role_code": "gm",
  "role_name": "总经理",
  "data_scope": "ALL",  # 全部可见
  "description": "总经理可以查看所有数据"
}
```

### 5.3 常见角色配置示例

| 角色 | 数据权限范围 | 说明 |
|------|------------|------|
| 总经理 | ALL | 可以看到所有项目和数据 |
| 部门经理 | DEPT | 只能看到同部门的项目 |
| 项目经理 | PROJECT | 只能看到参与的项目 |
| 工程师 | PROJECT | 只能看到参与的项目 |
| 普通员工 | OWN | 只能看到自己创建或负责的项目 |
| 系统管理员 | ALL | 可以看到所有数据 |

---

## 六、数据权限过滤逻辑

### 6.1 ALL（全部可见）

```python
if data_scope == "ALL":
    # 不进行任何过滤，返回所有数据
    return query  # 不添加任何过滤条件
```

**适用场景**：
- 总经理需要查看所有项目
- 系统管理员需要管理所有数据

### 6.2 DEPT（同部门可见）

```python
if data_scope == "DEPT":
    # 通过部门名称查找部门ID
    dept = db.query(Department).filter(Department.dept_name == user.department).first()
    if dept:
        # 只返回同部门的项目
        return query.filter(Project.dept_id == dept.id)
```

**适用场景**：
- 部门经理只能看到本部门的项目
- 部门成员只能看到本部门的项目

**前提条件**：
- 用户必须有 `department` 字段（部门名称）
- 项目必须有 `dept_id` 字段（部门ID）

### 6.3 PROJECT（参与项目可见）

```python
if data_scope == "PROJECT":
    # 获取用户参与的项目ID列表
    user_project_ids = DataScopeService.get_user_project_ids(db, user.id)
    # 只返回参与的项目
    return query.filter(Project.id.in_(user_project_ids))
```

**适用场景**：
- 项目经理只能看到自己负责的项目
- 工程师只能看到自己参与的项目

**前提条件**：
- 用户必须是项目的成员（通过 `project_members` 表关联）
- 项目成员记录必须是激活状态（`is_active = True`）

### 6.4 OWN（自己创建/负责的可见）

```python
if data_scope == "OWN":
    # 只返回自己创建或负责的项目
    return query.filter(
        or_(
            Project.created_by == user.id,  # 自己创建的
            Project.pm_id == user.id         # 自己负责的
        )
    )
```

**适用场景**：
- 普通员工只能看到自己创建的项目
- 项目经理只能看到自己负责的项目

---

## 七、项目成员管理

### 7.1 添加项目成员

为了让工程师能够看到项目，需要将工程师添加为项目成员：

```python
POST /api/v1/projects/{project_id}/members
{
  "user_id": 123,  # 工程师用户ID
  "role_type": "engineer",  # 项目角色类型
  "is_active": true
}
```

### 7.2 检查项目成员

系统通过 `project_members` 表判断用户是否参与项目：

```python
# app/services/data_scope_service.py
def get_user_project_ids(db: Session, user_id: int) -> Set[int]:
    """获取用户参与的项目ID列表"""
    members = (
        db.query(ProjectMember.project_id)
        .filter(
            ProjectMember.user_id == user_id,
            ProjectMember.is_active == True
        )
        .all()
    )
    return {m[0] for m in members}
```

---

## 八、常见问题

### Q1: 为什么工程师看不到项目？

**A**: 可能的原因：
1. 工程师角色的 `data_scope` 不是 `PROJECT`
2. 工程师没有被添加为项目成员
3. 项目成员记录被禁用了（`is_active = False`）

**解决方法**：
1. 检查角色配置：确保 `data_scope = "PROJECT"`
2. 添加项目成员：将工程师添加到项目成员列表
3. 检查成员状态：确保 `is_active = True`

### Q2: 为什么总经理看不到所有项目？

**A**: 可能的原因：
1. 总经理角色的 `data_scope` 不是 `ALL`
2. 用户没有正确分配角色

**解决方法**：
1. 检查角色配置：确保 `data_scope = "ALL"`
2. 检查用户角色：确保用户拥有总经理角色

### Q3: 用户有多个角色，数据权限如何确定？

**A**: 系统取**最宽松**的数据权限范围。

**示例**：
- 用户同时拥有"工程师"（PROJECT）和"部门经理"（DEPT）两个角色
- 最终数据权限范围 = **DEPT**（更宽松）

### Q4: 如何临时让用户看到所有数据？

**A**: 
1. 给用户分配一个 `data_scope = "ALL"` 的角色
2. 或设置 `user.is_superuser = True`（超级管理员）

### Q5: 数据权限变更何时生效？

**A**: 
- 数据权限变更立即生效，无需重启服务
- 用户下次请求时就会使用新的数据权限范围

---

## 九、最佳实践

### 9.1 角色设计原则

1. **按职责设计角色**：
   - 管理层角色：`data_scope = "ALL"`
   - 部门管理角色：`data_scope = "DEPT"`
   - 项目相关角色：`data_scope = "PROJECT"`
   - 普通员工角色：`data_scope = "OWN"`

2. **权限范围要合理**：
   - 不要给普通员工 `ALL` 权限
   - 不要给管理层 `OWN` 权限

3. **定期审查权限**：
   - 定期检查用户的角色分配
   - 确保数据权限范围符合实际需求

### 9.2 项目成员管理

1. **及时添加成员**：
   - 项目创建后，及时添加项目成员
   - 确保所有相关人员都能看到项目

2. **及时移除成员**：
   - 项目结束后，及时移除不再需要的成员
   - 避免数据泄露

3. **使用项目角色类型**：
   - 为项目成员分配合适的项目角色类型
   - 便于后续权限管理和统计

---

## 十、总结

### 数据权限控制的核心

1. ✅ **通过角色配置**：数据权限范围配置在角色上，不是用户上
2. ✅ **自动过滤**：系统自动根据用户的数据权限范围过滤数据
3. ✅ **多角色支持**：用户有多个角色时，取最宽松的权限范围
4. ✅ **灵活配置**：可以根据实际需求灵活配置不同角色的数据权限范围

### 配置要点

- **总经理**：`data_scope = "ALL"` → 可以看到所有项目
- **工程师**：`data_scope = "PROJECT"` → 只能看到参与的项目
- **部门经理**：`data_scope = "DEPT"` → 只能看到同部门的项目
- **普通员工**：`data_scope = "OWN"` → 只能看到自己创建或负责的项目

---

## 十一、相关文档

- [权限系统完整指南](./PERMISSION_SYSTEM_COMPLETE_GUIDE.md)
- [权限机制说明](./PERMISSION_MECHANISM_EXPLANATION.md)
- [数据权限和审计实现](./DATA_SCOPE_AND_AUDIT_IMPLEMENTATION.md)

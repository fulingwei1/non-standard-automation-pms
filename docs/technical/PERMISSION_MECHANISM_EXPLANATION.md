# 权限机制说明

> 更新日期：2026-01-XX

## 一、核心理解

**您的理解完全正确！**

### 权限系统的工作机制

```
API端点（功能）
  ↓
权限（Permission）
  ↓
角色（Role）
  ↓
用户（User）
```

**关键点**：
1. ✅ **API = 功能**：每个API端点代表一个功能
2. ✅ **权限控制**：通过权限（Permission）来控制API的访问
3. ✅ **角色分配**：权限分配给角色（Role），而不是直接分配给用户
4. ✅ **用户继承**：用户通过拥有角色来获得权限
5. ✅ **多角色支持**：一个用户可以有多个角色，权限取并集

---

## 二、权限检查流程

### 2.1 用户请求API时的检查流程

```
用户请求 → 获取用户信息 → 遍历用户的所有角色 → 检查角色是否拥有该权限 → 允许/拒绝
```

### 2.2 代码实现

```python
# app/core/security.py
def check_permission(user: User, permission_code: str) -> bool:
    """检查用户权限"""
    # 1. 超级管理员直接通过
    if user.is_superuser:
        return True

    # 2. 遍历用户的所有角色
    for user_role in user.roles:
        # 3. 遍历角色的所有权限
        for role_permission in user_role.role.permissions:
            # 4. 检查是否有匹配的权限
            if role_permission.permission.permission_code == permission_code:
                return True
    
    # 5. 所有角色都没有该权限，拒绝访问
    return False
```

### 2.3 API端点使用示例

```python
# app/api/v1/endpoints/projects.py
@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    current_user: User = Depends(require_permission("project:read"))
):
    """
    获取项目列表
    
    权限要求：project:read
    - 如果用户有该权限 → 允许访问
    - 如果用户没有该权限 → 返回403 Forbidden
    """
    ...
```

---

## 三、多角色权限合并机制

### 3.1 功能权限（取并集）

**规则**：用户有多个角色时，只要**任一角色**拥有该权限，用户就有权限。

**示例**：
```
用户：张三
角色1：项目经理（pm）→ 拥有权限：project:read, project:write
角色2：销售工程师（sales）→ 拥有权限：sales:read, sales:write

张三的权限 = project:read, project:write, sales:read, sales:write
```

**代码实现**：
```python
# check_permission函数会遍历所有角色
for user_role in user.roles:  # 遍历所有角色
    for role_permission in user_role.role.permissions:
        if role_permission.permission.permission_code == permission_code:
            return True  # 找到就返回True
```

### 3.2 数据权限范围（取最宽松的）

**规则**：用户有多个角色时，取**最宽松**的数据权限范围。

**优先级**：ALL > DEPT > PROJECT > OWN

**示例**：
```
用户：李四
角色1：项目经理（pm）→ data_scope = PROJECT
角色2：部门经理（dept_manager）→ data_scope = DEPT

李四的数据权限范围 = DEPT（取最宽松的）
```

**代码实现**：
```python
# app/services/data_scope_service.py
def get_user_data_scope(db: Session, user: User) -> str:
    if user.is_superuser:
        return DataScopeEnum.ALL.value
    
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

## 四、权限配置流程

### 4.1 配置步骤

1. **创建权限**（通常在数据库迁移脚本中）
   ```sql
   INSERT INTO permissions (permission_code, permission_name, module, resource, action)
   VALUES ('project:read', '项目查看权限', 'project', 'project', 'read');
   ```

2. **创建角色**（通过角色管理页面或API）
   ```python
   POST /api/v1/roles/
   {
     "role_code": "pm",
     "role_name": "项目经理",
     "data_scope": "PROJECT"
   }
   ```

3. **分配权限给角色**（通过角色管理页面或API）
   ```python
   PUT /api/v1/roles/{role_id}/permissions
   {
     "permission_ids": [1, 2, 3, ...]  # 权限ID列表
   }
   ```

4. **分配角色给用户**（通过用户管理页面或API）
   ```python
   PUT /api/v1/users/{user_id}/roles
   {
     "role_ids": [1, 2, ...]  # 角色ID列表
   }
   ```

### 4.2 完整示例

**场景**：让用户"张三"能够查看项目列表

1. **权限已存在**：`project:read`（权限ID=1）
2. **角色已存在**：`项目经理`（角色ID=1）
3. **分配权限给角色**：
   ```python
   PUT /api/v1/roles/1/permissions
   {
     "permission_ids": [1]  # project:read
   }
   ```
4. **分配角色给用户**：
   ```python
   PUT /api/v1/users/1/roles
   {
     "role_ids": [1]  # 项目经理
   }
   ```

**结果**：张三现在可以访问 `GET /api/v1/projects` API

---

## 五、实际应用场景

### 5.1 场景1：用户有多个角色

**用户**：王五
- 角色1：项目经理（pm）
  - 权限：project:read, project:write, project:delete
  - 数据权限：PROJECT
- 角色2：销售工程师（sales）
  - 权限：sales:read, sales:write
  - 数据权限：OWN

**王五的权限**：
- 功能权限：project:read, project:write, project:delete, sales:read, sales:write（并集）
- 数据权限：PROJECT（最宽松）

**访问控制**：
- ✅ 可以访问项目列表API（有project:read权限）
- ✅ 可以访问销售列表API（有sales:read权限）
- ✅ 可以查看参与的项目（数据权限PROJECT）
- ❌ 不能查看所有项目（数据权限不是ALL）

### 5.2 场景2：权限未分配

**用户**：赵六
- 角色：普通员工（user）
  - 权限：无
  - 数据权限：OWN

**访问控制**：
- ❌ 不能访问项目列表API（没有project:read权限）
- ❌ 不能访问销售列表API（没有sales:read权限）
- ✅ 只能查看自己创建的项目（数据权限OWN）

### 5.3 场景3：超级管理员

**用户**：系统管理员
- is_superuser = True

**访问控制**：
- ✅ 可以访问所有API（绕过权限检查）
- ✅ 可以查看所有数据（数据权限ALL）

---

## 六、权限检查的层次

### 6.1 三层检查

1. **认证层**（Authentication）
   - 检查用户是否登录
   - 验证JWT Token
   - 位置：`get_current_active_user`

2. **授权层**（Authorization - 功能权限）
   - 检查用户是否有权限访问该API
   - 位置：`require_permission("permission_code")`

3. **数据权限层**（Authorization - 数据权限）
   - 检查用户可以看到哪些数据
   - 位置：`filter_projects_by_scope()`

### 6.2 完整示例

```python
@router.get("/projects/{project_id}")
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),  # 1. 认证检查
    db: Session = Depends(get_db),
):
    # 2. 功能权限检查（如果需要）
    # 这里没有使用require_permission，因为所有登录用户都可以查看项目详情
    
    # 3. 数据权限检查
    check_project_access_or_raise(db, current_user, project_id)
    
    # 4. 业务逻辑
    project = db.query(Project).filter(Project.id == project_id).first()
    return project
```

---

## 七、常见问题

### Q1: 如果用户有多个角色，权限如何合并？

**A**: 
- **功能权限**：取并集（任一角色有权限即可）
- **数据权限**：取最宽松的范围（ALL > DEPT > PROJECT > OWN）

### Q2: 如何给用户添加新权限？

**A**: 
1. 确保权限已创建
2. 将权限分配给角色
3. 将角色分配给用户

**注意**：不能直接给用户分配权限，必须通过角色。

### Q3: 如何撤销用户的权限？

**A**: 
1. 从用户的角色中移除该角色
2. 或从角色中移除该权限（会影响所有拥有该角色的用户）

### Q4: 权限变更何时生效？

**A**: 
- 权限变更立即生效，无需重启服务
- 用户下次请求时就会使用新的权限

### Q5: 如何查看用户有哪些权限？

**A**: 
1. 通过用户管理页面查看用户的角色
2. 通过角色管理页面查看角色的权限
3. 或调用API：`GET /api/v1/auth/me` 查看当前用户的权限

---

## 八、总结

### 权限系统的核心原则

1. ✅ **API = 功能**：每个API端点代表一个功能
2. ✅ **权限控制API**：通过权限编码控制API访问
3. ✅ **角色分配权限**：权限分配给角色，不直接分配给用户
4. ✅ **用户继承权限**：用户通过拥有角色来获得权限
5. ✅ **多角色支持**：用户可以有多个角色，权限取并集
6. ✅ **数据权限分离**：功能权限和数据权限分开管理

### 权限配置的最佳实践

1. **权限粒度**：按功能模块划分权限（如 project:read, project:write）
2. **角色设计**：按岗位职责设计角色（如 项目经理、销售工程师）
3. **权限分配**：将相关权限组合分配给角色
4. **用户分配**：根据用户的实际职责分配角色
5. **定期审查**：定期审查用户的角色和权限，确保符合实际需求

---

## 九、相关文档

- [权限系统完整指南](./PERMISSION_SYSTEM_COMPLETE_GUIDE.md)
- [权限功能实现总结](./PERMISSION_IMPLEMENTATION_SUMMARY.md)
- [数据权限和审计实现](./DATA_SCOPE_AND_AUDIT_IMPLEMENTATION.md)

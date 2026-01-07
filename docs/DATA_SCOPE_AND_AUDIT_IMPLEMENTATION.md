# 数据权限与审计功能实现文档

> 实现日期：2026-01-06  
> 版本：v1.0

## 一、概述

本文档记录了数据权限控制和权限审计功能的完整实现，包括数据权限服务、审计服务、API集成等。

## 二、实现内容

### 2.1 数据权限服务（DataScopeService）

**文件位置**：`app/services/data_scope_service.py`

**核心功能**：
- 获取用户数据权限范围（ALL/DEPT/PROJECT/OWN/CUSTOMER）
- 根据数据权限范围过滤项目查询
- 检查用户对指定项目的访问权限
- 检查用户对指定客户的访问权限

**数据权限范围说明**：

| 范围 | 说明 | 优先级 |
|------|------|:------:|
| ALL | 全部可见 | 最高 |
| DEPT | 同部门可见 | 中 |
| PROJECT | 参与项目可见 | 中 |
| OWN | 自己创建/负责的对象可见 | 低 |
| CUSTOMER | 客户门户仅看自身项目 | 特殊 |

**主要方法**：

1. `get_user_data_scope(db, user)` - 获取用户的数据权限范围
   - 超级管理员自动返回 `ALL`
   - 取用户所有角色中最宽松的权限范围

2. `filter_projects_by_scope(db, query, user, project_ids)` - 过滤项目查询
   - 根据用户数据权限范围自动过滤项目列表
   - 支持预过滤项目ID列表

3. `check_project_access(db, user, project_id)` - 检查项目访问权限
   - 返回布尔值，表示是否有权限访问

4. `check_customer_access(db, user, customer_id)` - 检查客户访问权限
   - 用于客户门户等场景

### 2.2 权限审计服务（PermissionAuditService）

**文件位置**：`app/services/permission_audit_service.py`

**核心功能**：
- 记录权限相关操作的审计日志
- 支持用户操作、角色操作、权限分配等审计

**审计操作类型**：

**用户操作**：
- `USER_CREATED` - 用户创建
- `USER_UPDATED` - 用户更新
- `USER_DELETED` - 用户删除
- `USER_ACTIVATED` - 用户激活
- `USER_DEACTIVATED` - 用户禁用
- `USER_ROLE_ASSIGNED` - 用户角色分配
- `USER_ROLE_REVOKED` - 用户角色回收

**角色操作**：
- `ROLE_CREATED` - 角色创建
- `ROLE_UPDATED` - 角色更新
- `ROLE_DELETED` - 角色删除
- `ROLE_ACTIVATED` - 角色激活
- `ROLE_DEACTIVATED` - 角色禁用
- `ROLE_PERMISSION_ASSIGNED` - 角色权限分配
- `ROLE_PERMISSION_REVOKED` - 角色权限回收

**主要方法**：

1. `log_audit()` - 通用审计日志记录
2. `log_user_role_assignment()` - 记录用户角色分配
3. `log_role_permission_assignment()` - 记录角色权限分配
4. `log_user_operation()` - 记录用户操作
5. `log_role_operation()` - 记录角色操作

### 2.3 权限审计模型（PermissionAudit）

**文件位置**：`app/models/user.py`

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| operator_id | Integer | 操作人ID |
| action | String(50) | 操作类型 |
| target_type | String(20) | 目标类型（user/role/permission） |
| target_id | Integer | 目标ID |
| detail | Text | 详细信息（JSON格式） |
| ip_address | String(50) | 操作IP地址 |
| user_agent | String(500) | 用户代理 |
| created_at | DateTime | 创建时间 |

### 2.4 API集成

#### 2.4.1 用户管理API

**文件位置**：`app/api/v1/endpoints/users.py`

**集成的审计日志**：
- 用户创建时记录 `USER_CREATED`
- 用户更新时记录 `USER_UPDATED`
- 用户状态变更时记录 `USER_ACTIVATED` 或 `USER_DEACTIVATED`
- 用户角色分配时记录 `USER_ROLE_ASSIGNED`

#### 2.4.2 角色管理API

**文件位置**：`app/api/v1/endpoints/roles.py`

**集成的审计日志**：
- 角色创建时记录 `ROLE_CREATED`
- 角色更新时记录 `ROLE_UPDATED`
- 角色状态变更时记录 `ROLE_ACTIVATED` 或 `ROLE_DEACTIVATED`
- 角色权限分配时记录 `ROLE_PERMISSION_ASSIGNED`

#### 2.4.3 项目查询API

**文件位置**：`app/api/v1/endpoints/projects.py`

**数据权限应用**：
- `GET /projects` - 项目列表自动应用数据权限过滤
- `GET /projects/{project_id}` - 项目详情检查访问权限

#### 2.4.4 权限审计查询API

**文件位置**：`app/api/v1/endpoints/audits.py`

**API端点**：
- `GET /audits` - 获取权限审计日志列表（支持分页和筛选）
- `GET /audits/{audit_id}` - 获取权限审计日志详情

**筛选参数**：
- `operator_id` - 操作人ID
- `target_type` - 目标类型（user/role/permission）
- `target_id` - 目标ID
- `action` - 操作类型
- `start_date` - 开始日期
- `end_date` - 结束日期

## 三、使用示例

### 3.1 在API中应用数据权限过滤

```python
from app.services.data_scope_service import DataScopeService

@router.get("/projects")
def read_projects(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    query = db.query(Project)
    
    # 应用数据权限过滤
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)
    
    # 继续其他查询逻辑...
    return query.all()
```

### 3.2 检查项目访问权限

```python
from app.services.data_scope_service import DataScopeService

@router.get("/projects/{project_id}")
def read_project(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    # 检查访问权限
    if not DataScopeService.check_project_access(db, current_user, project_id):
        raise HTTPException(
            status_code=403,
            detail="您没有权限访问该项目"
        )
    
    # 继续查询逻辑...
```

### 3.3 记录审计日志

```python
from app.services.permission_audit_service import PermissionAuditService
from fastapi import Request

@router.put("/users/{user_id}/roles")
def assign_user_roles(
    user_id: int,
    role_data: UserRoleAssign,
    request: Request,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(deps.get_db),
):
    # 执行角色分配逻辑...
    
    # 记录审计日志
    PermissionAuditService.log_user_role_assignment(
        db=db,
        operator_id=current_user.id,
        user_id=user_id,
        role_ids=role_data.role_ids,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
```

## 四、数据权限判定逻辑

### 4.1 权限范围优先级

用户可能有多个角色，每个角色有不同的数据权限范围。系统取最宽松的权限范围：

1. 如果任一角色有 `ALL`，则用户拥有 `ALL` 权限
2. 否则，如果任一角色有 `DEPT`，则用户拥有 `DEPT` 权限
3. 否则，如果任一角色有 `PROJECT`，则用户拥有 `PROJECT` 权限
4. 否则，用户拥有 `OWN` 权限

### 4.2 项目访问判定

1. **ALL权限**：可以访问所有项目
2. **DEPT权限**：只能访问同部门的项目
3. **PROJECT权限**：只能访问参与的项目（通过 `project_members` 表判断）
4. **OWN权限**：只能访问自己创建或负责的项目（`created_by` 或 `pm_id`）

### 4.3 部门匹配逻辑

- 通过 `User.department`（部门名称）匹配 `Department.dept_name`
- 获取部门ID后，匹配 `Project.dept_id`

## 五、注意事项

1. **性能考虑**：
   - 数据权限过滤在数据库层面进行，避免应用层过滤
   - 对于大量数据的查询，建议添加适当的索引

2. **审计日志**：
   - 审计日志记录失败不影响主业务流程
   - 使用 try-except 包裹审计日志记录，确保主流程不受影响

3. **权限变更**：
   - 权限变更会立即生效，无需重启服务
   - 建议在权限变更后清除相关缓存（如果使用缓存）

4. **超级管理员**：
   - 超级管理员（`is_superuser=True`）自动拥有所有权限
   - 不受数据权限范围限制

## 六、后续优化建议

1. **缓存优化**：
   - 使用 Redis 缓存用户权限信息
   - 权限变更时自动失效缓存

2. **子部门支持**：
   - 扩展 `DEPT` 权限，支持查看子部门的数据

3. **字段级权限**：
   - 对敏感字段（如合同金额、回款等）实现字段级权限控制

4. **审计日志分析**：
   - 提供审计日志统计分析功能
   - 支持导出审计日志

## 七、相关文件清单

### 新增文件
- `app/services/data_scope_service.py` - 数据权限服务
- `app/services/permission_audit_service.py` - 权限审计服务
- `app/api/v1/endpoints/audits.py` - 权限审计查询API
- `docs/DATA_SCOPE_AND_AUDIT_IMPLEMENTATION.md` - 本文档

### 修改文件
- `app/models/user.py` - 添加 `PermissionAudit` 模型
- `app/models/__init__.py` - 导出 `PermissionAudit`
- `app/core/security.py` - 添加项目访问权限检查函数
- `app/api/v1/endpoints/users.py` - 集成审计日志
- `app/api/v1/endpoints/roles.py` - 集成审计日志
- `app/api/v1/endpoints/projects.py` - 应用数据权限过滤
- `app/api/v1/api.py` - 注册审计API路由
- `DEVELOPMENT_TASKS.md` - 更新任务状态

## 八、测试建议

1. **数据权限测试**：
   - 测试不同数据权限范围的用户访问项目列表
   - 测试项目详情访问权限检查
   - 测试部门权限匹配逻辑

2. **审计日志测试**：
   - 测试用户操作审计日志记录
   - 测试角色操作审计日志记录
   - 测试审计日志查询功能

3. **边界情况测试**：
   - 测试无部门信息的用户
   - 测试无项目成员的用户
   - 测试超级管理员权限




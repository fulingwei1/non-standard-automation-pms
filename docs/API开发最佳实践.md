# API 开发最佳实践 - 租户隔离版

## 概述

本文档提供非标自动化项目管理系统中 API 开发的最佳实践，重点关注租户隔离的正确使用方法。

## 目录

1. [基本原则](#基本原则)
2. [API 模板](#api-模板)
3. [常见场景](#常见场景)
4. [错误处理](#错误处理)
5. [测试指南](#测试指南)
6. [常见错误](#常见错误)

---

## 基本原则

### 1. 始终使用装饰器

❌ **错误示例**：

```python
@router.get("/projects")
async def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 忘记添加租户过滤！
    projects = db.query(Project).all()
    return projects
```

✅ **正确示例**：

```python
from app.core.decorators import require_tenant_isolation

@router.get("/projects")
@require_tenant_isolation
async def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 自动过滤当前租户
    projects = db.query(Project).all()
    return projects
```

### 2. 参数顺序约定

为了装饰器正常工作，推荐参数顺序：

```python
async def endpoint_function(
    # 1. 路径参数
    resource_id: int,
    # 2. 查询参数
    skip: int = 0,
    limit: int = 100,
    # 3. 请求体
    data: ModelCreate = None,
    # 4. 依赖注入（db 在前，current_user 在后）
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pass
```

### 3. 创建资源时强制租户一致性

❌ **错误示例**：

```python
@router.post("/customers")
async def create_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    customer = Customer(**data.dict())  # tenant_id 可能被篡改！
    db.add(customer)
    db.commit()
    return customer
```

✅ **正确示例**：

```python
from app.core.permissions.tenant_access import ensure_tenant_consistency

@router.post("/customers")
@require_tenant_isolation
async def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer_dict = data.dict()
    customer_dict = ensure_tenant_consistency(current_user, customer_dict)
    customer = Customer(**customer_dict)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer
```

---

## API 模板

### 列表查询（GET /resources）

```python
from typing import List
from fastapi import Query
from app.core.decorators import require_tenant_isolation

@router.get("/projects", response_model=List[ProjectResponse])
@require_tenant_isolation
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目列表
    
    - 自动过滤当前租户的项目
    - 支持分页和状态筛选
    """
    query = db.query(Project)
    
    # 添加其他过滤条件
    if status:
        query = query.filter(Project.status == status)
    
    # 分页
    total = query.count()
    projects = query.offset(skip).limit(limit).all()
    
    return projects
```

### 单个资源查询（GET /resources/{id}）

```python
from fastapi import HTTPException, status
from app.core.decorators import require_tenant_isolation, tenant_resource_check

@router.get("/projects/{project_id}", response_model=ProjectResponse)
@require_tenant_isolation
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目详情
    
    - 自动验证项目属于当前租户
    - 404 如果项目不存在或不属于当前租户
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 显式验证访问权限（可选，TenantQuery 已自动过滤）
    tenant_resource_check(current_user, project.tenant_id, "Project")
    
    return project
```

### 创建资源（POST /resources）

```python
from app.core.permissions.tenant_access import ensure_tenant_consistency

@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
@require_tenant_isolation
async def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新项目
    
    - 自动设置 tenant_id 为当前用户的租户
    - 验证数据有效性
    """
    # 确保租户一致性
    project_dict = data.dict()
    project_dict = ensure_tenant_consistency(current_user, project_dict)
    
    # 创建项目
    project = Project(**project_dict)
    db.add(project)
    
    try:
        db.commit()
        db.refresh(project)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )
    
    return project
```

### 更新资源（PUT /resources/{id}）

```python
@router.put("/projects/{project_id}", response_model=ProjectResponse)
@require_tenant_isolation
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新项目
    
    - 验证项目存在且属于当前租户
    - 只更新提供的字段
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 显式验证访问权限
    tenant_resource_check(current_user, project.tenant_id, "Project")
    
    # 更新字段
    for key, value in data.dict(exclude_unset=True).items():
        # 防止修改 tenant_id
        if key == 'tenant_id':
            continue
        setattr(project, key, value)
    
    try:
        db.commit()
        db.refresh(project)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        )
    
    return project
```

### 删除资源（DELETE /resources/{id}）

```python
@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_tenant_isolation
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除项目
    
    - 验证项目存在且属于当前租户
    - 软删除或硬删除
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 显式验证访问权限
    tenant_resource_check(current_user, project.tenant_id, "Project")
    
    try:
        # 软删除
        project.is_deleted = True
        # 或硬删除
        # db.delete(project)
        
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project"
        )
    
    return None
```

### 系统管理 API（仅超级管理员）

```python
from app.core.decorators import allow_cross_tenant

@router.get("/admin/statistics")
@allow_cross_tenant(admin_only=True)
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取全局统计
    
    - 仅超级管理员可访问
    - 跨租户数据查询
    """
    # 需要显式禁用租户过滤
    project_query = db.query(Project)
    project_query._skip_tenant_filter = True
    total_projects = project_query.count()
    
    order_query = db.query(Order)
    order_query._skip_tenant_filter = True
    total_orders = order_query.count()
    
    return {
        "total_projects": total_projects,
        "total_orders": total_orders
    }
```

---

## 常见场景

### 场景1: 关联查询

```python
@router.get("/orders/{order_id}/items")
@require_tenant_isolation
async def get_order_items(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取订单明细"""
    # 两个表都会自动过滤
    items = (
        db.query(OrderItem)
        .join(Order)
        .filter(Order.id == order_id)
        .all()
    )
    
    if not items:
        raise HTTPException(status_code=404, detail="Order not found or no items")
    
    return items
```

### 场景2: 跨表资源创建

```python
from app.core.permissions.tenant_access import validate_tenant_match

@router.post("/orders")
@require_tenant_isolation
async def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建订单"""
    # 验证客户和项目是否属于当前租户
    customer = db.query(Customer).filter(Customer.id == data.customer_id).first()
    project = db.query(Project).filter(Project.id == data.project_id).first()
    
    if not customer or not project:
        raise HTTPException(status_code=404, detail="Customer or project not found")
    
    # 验证所有资源属于同一租户
    if not validate_tenant_match(current_user, customer.tenant_id, project.tenant_id):
        raise HTTPException(
            status_code=400,
            detail="Customer and project must belong to the same tenant"
        )
    
    # 创建订单
    order_dict = data.dict()
    order_dict = ensure_tenant_consistency(current_user, order_dict)
    order = Order(**order_dict)
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return order
```

### 场景3: 批量操作

```python
from app.core.permissions.tenant_access import check_bulk_access

@router.post("/projects/batch-update")
@require_tenant_isolation
async def batch_update_projects(
    project_ids: List[int],
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量更新项目"""
    # 查询项目（自动过滤租户）
    projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
    
    if len(projects) != len(project_ids):
        raise HTTPException(
            status_code=404,
            detail="Some projects not found or not accessible"
        )
    
    # 批量权限检查
    if not check_bulk_access(current_user, projects):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 批量更新
    for project in projects:
        for key, value in data.dict(exclude_unset=True).items():
            if key != 'tenant_id':
                setattr(project, key, value)
    
    db.commit()
    
    return {"updated": len(projects)}
```

### 场景4: 聚合查询

```python
from sqlalchemy import func

@router.get("/projects/statistics")
@require_tenant_isolation
async def get_project_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """项目统计"""
    # 自动过滤当前租户
    stats = (
        db.query(
            Project.status,
            func.count(Project.id).label('count'),
            func.sum(Project.budget).label('total_budget')
        )
        .group_by(Project.status)
        .all()
    )
    
    return [
        {
            "status": stat.status,
            "count": stat.count,
            "total_budget": float(stat.total_budget or 0)
        }
        for stat in stats
    ]
```

---

## 错误处理

### 标准错误响应

```python
from fastapi.responses import JSONResponse

@router.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """处理租户验证错误"""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

@router.exception_handler(PermissionError)
async def permission_error_handler(request, exc):
    """处理权限错误"""
    return JSONResponse(
        status_code=403,
        content={"detail": "Access denied"}
    )
```

### 常见错误码

| 状态码 | 场景 | 说明 |
|--------|------|------|
| 400 | Bad Request | tenant_id 不匹配、资源跨租户引用 |
| 401 | Unauthorized | 未认证用户 |
| 403 | Forbidden | 租户访问被拒绝 |
| 404 | Not Found | 资源不存在或不属于当前租户 |
| 500 | Internal Server Error | 系统错误 |

---

## 测试指南

### 单元测试

```python
import pytest
from app.core.database.tenant_query import TenantQuery

def test_tenant_filter_applied():
    """测试租户过滤是否自动应用"""
    # 设置租户上下文
    set_current_tenant_id(100)
    
    # 创建查询
    query = db.query(Project)
    
    # 验证生成的SQL包含租户过滤
    sql = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
    assert "tenant_id = 100" in sql
```

### 集成测试

```python
from fastapi.testclient import TestClient

def test_list_projects_filtered_by_tenant(client: TestClient, db: Session):
    """测试项目列表按租户过滤"""
    # 创建两个租户的数据
    project1 = Project(name="Tenant 1 Project", tenant_id=1)
    project2 = Project(name="Tenant 2 Project", tenant_id=2)
    db.add_all([project1, project2])
    db.commit()
    
    # 租户1用户登录
    token = get_auth_token(user_tenant_id=1)
    response = client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # 验证只返回租户1的项目
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) == 1
    assert projects[0]["name"] == "Tenant 1 Project"
```

### 安全测试

```python
def test_cannot_access_other_tenant_resource(client: TestClient, db: Session):
    """测试不能访问其他租户的资源"""
    # 创建租户2的项目
    project = Project(name="Tenant 2 Project", tenant_id=2)
    db.add(project)
    db.commit()
    
    # 租户1用户尝试访问
    token = get_auth_token(user_tenant_id=1)
    response = client.get(
        f"/api/v1/projects/{project.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # 应该返回404（而不是403，避免信息泄露）
    assert response.status_code == 404
```

---

## 常见错误

### ❌ 错误1: 忘记使用装饰器

```python
# 错误！没有租户隔离保护
@router.get("/projects")
async def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()
```

**后果**: 返回所有租户的数据，严重安全漏洞！

### ❌ 错误2: 手动添加过滤条件

```python
# 多余！TenantQuery 已经自动过滤
@router.get("/projects")
@require_tenant_isolation
async def list_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 不需要手动过滤
    return db.query(Project).filter(Project.tenant_id == current_user.tenant_id).all()
```

**后果**: 代码冗余，可能导致重复过滤。

### ❌ 错误3: 创建时未验证租户

```python
# 错误！允许恶意用户创建其他租户的资源
@router.post("/projects")
async def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(**data.dict())  # data.tenant_id 可能被篡改
    db.add(project)
    db.commit()
    return project
```

**后果**: 安全漏洞，用户可以创建任意租户的数据。

### ❌ 错误4: 系统API未限制权限

```python
# 错误！未限制超级管理员
@router.get("/admin/all-data")
async def get_all_data(db: Session = Depends(get_db)):
    query = db.query(Project)
    query._skip_tenant_filter = True
    return query.all()
```

**后果**: 任何用户都能访问所有数据。

---

## 检查清单

开发新 API 时，确保：

- [ ] 使用 `@require_tenant_isolation` 或 `@allow_cross_tenant` 装饰器
- [ ] 函数参数包含 `db: Session = Depends(get_db)` 和 `current_user: User = Depends(get_current_user)`
- [ ] 创建资源时使用 `ensure_tenant_consistency()`
- [ ] 不要手动添加 `filter(Model.tenant_id == ...)` （除非有特殊原因）
- [ ] 系统管理 API 限制为超级管理员
- [ ] 显式禁用过滤时记录日志
- [ ] 编写单元测试和集成测试
- [ ] 添加 API 文档字符串

---

## 总结

遵循这些最佳实践，可以确保：

✅ **安全性**：所有 API 自动隔离租户数据  
✅ **一致性**：统一的代码风格和模式  
✅ **可维护性**：易于理解和修改  
✅ **可测试性**：标准的测试模式  

## 相关文档

- [租户过滤实现原理](./租户过滤实现原理.md)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 查询指南](https://docs.sqlalchemy.org/en/14/orm/query.html)

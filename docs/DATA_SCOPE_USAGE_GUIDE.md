# 数据范围过滤使用指南

## 目录
1. [概述](#概述)
2. [数据范围类型](#数据范围类型)
3. [快速开始](#快速开始)
4. [使用示例](#使用示例)
5. [最佳实践](#最佳实践)
6. [性能优化](#性能优化)
7. [故障排查](#故障排查)

---

## 概述

数据范围过滤（Data Scope Filtering）是一个权限控制机制，用于限制用户只能访问特定范围内的数据。系统支持多种数据范围类型，从全部数据到仅个人数据。

### 主要特性
- ✅ 多种数据范围类型（ALL, DEPT, PROJECT, OWN等）
- ✅ 基于组织架构的权限控制
- ✅ 灵活的字段映射配置
- ✅ 高性能的查询优化
- ✅ 统一的枚举映射层
- ✅ 详细的日志记录

---

## 数据范围类型

### 1. ALL（全部数据）
**描述**: 用户可以访问系统中的所有数据  
**适用场景**: 超级管理员、高级管理层  
**示例**: CEO、CTO可以查看所有项目和订单

### 2. BUSINESS_UNIT（事业部数据）
**描述**: 用户可以访问其所属事业部及下属部门的所有数据  
**适用场景**: 事业部总监  
**示例**: 硬件事业部总监可以查看硬件事业部下所有项目

### 3. DEPARTMENT（部门数据）
**描述**: 用户可以访问其所属部门及子部门的所有数据  
**适用场景**: 部门经理  
**示例**: 研发部经理可以查看研发部及其下属团队的所有任务

### 4. TEAM（团队数据）
**描述**: 用户只能访问其直接所属团队的数据  
**适用场景**: 团队负责人  
**示例**: 前端团队leader只能查看前端团队的数据

### 5. PROJECT（项目数据）
**描述**: 用户可以访问其参与的项目相关数据  
**适用场景**: 项目成员、跨部门协作  
**示例**: PM、开发人员可以查看自己参与的项目

### 6. OWN（个人数据）
**描述**: 用户只能访问自己创建或拥有的数据  
**适用场景**: 普通员工、默认权限  
**示例**: 员工只能查看自己创建的工单

### 7. SUBORDINATE（下属数据）
**描述**: 用户可以访问自己及直接下属的数据  
**适用场景**: 直属管理关系  
**示例**: 经理可以查看自己和直接下属的工作日志

### 8. CUSTOM（自定义规则）
**描述**: 基于自定义规则的数据访问控制  
**适用场景**: 特殊业务场景  
**示例**: 客户门户用户只能查看自己公司的项目

---

## 快速开始

### 1. 基本导入

```python
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced
```

### 2. 应用数据权限过滤

```python
def get_projects(db: Session, current_user: User):
    """获取用户有权限访问的项目列表"""
    from app.models.project import Project
    
    # 创建基础查询
    query = db.query(Project)
    
    # 应用数据权限过滤
    query = DataScopeServiceEnhanced.apply_data_scope(
        query=query,
        db=db,
        user=current_user,
        resource_type="project",
        org_field="dept_id",        # 组织字段名
        owner_field="created_by",   # 所有者字段名
        pm_field="pm_id"            # 项目经理字段名（可选）
    )
    
    # 执行查询
    return query.all()
```

### 3. 检查数据访问权限

```python
def can_edit_project(db: Session, current_user: User, project_id: int) -> bool:
    """检查用户是否有权限编辑项目"""
    from app.models.project import Project
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return False
    
    # 检查访问权限
    return DataScopeServiceEnhanced.can_access_data(
        db=db,
        user=current_user,
        resource_type="project",
        data=project,
        org_field="dept_id",
        owner_field="created_by"
    )
```

---

## 使用示例

### 示例 1: 采购订单过滤

```python
from app.models.purchase import PurchaseOrder
from app.services.data_scope.config import DATA_SCOPE_CONFIGS

def get_purchase_orders(db: Session, current_user: User):
    """获取采购订单列表（根据用户权限）"""
    
    query = db.query(PurchaseOrder)
    
    # 使用预定义配置
    config = DATA_SCOPE_CONFIGS.get("purchase_order")
    
    # 方式1: 使用 DataScopeService
    query = DataScopeServiceEnhanced.apply_data_scope(
        query=query,
        db=db,
        user=current_user,
        resource_type="purchase_order",
        org_field="department_id",
        owner_field="requester_id",
        pm_field="project_id"  # 通过项目间接关联
    )
    
    return query.all()
```

### 示例 2: 使用通用过滤器

```python
from app.services.data_scope.generic_filter import GenericFilterService
from app.services.data_scope.config import DataScopeConfig

def get_tasks(db: Session, current_user: User):
    """获取任务列表（通用过滤器方式）"""
    from app.models.task import Task
    
    query = db.query(Task)
    
    # 自定义配置
    config = DataScopeConfig(
        owner_field="assignee_id",
        additional_owner_fields=["created_by"],
        project_field="project_id",
        dept_through_project=True
    )
    
    # 应用通用过滤器
    query = GenericFilterService.filter_by_scope(
        db=db,
        query=query,
        model=Task,
        user=current_user,
        config=config
    )
    
    return query.all()
```

### 示例 3: 多条件过滤

```python
def get_issues(db: Session, current_user: User, status: str = None):
    """获取问题列表（支持额外过滤条件）"""
    from app.models.issue import Issue
    
    query = db.query(Issue)
    
    # 先应用业务过滤条件
    if status:
        query = query.filter(Issue.status == status)
    
    # 再应用数据权限过滤
    query = DataScopeServiceEnhanced.apply_data_scope(
        query=query,
        db=db,
        user=current_user,
        resource_type="issue",
        org_field="department_id",
        owner_field="reporter_id"
    )
    
    return query.all()
```

### 示例 4: 自定义过滤函数

```python
from sqlalchemy import or_

def custom_customer_filter(query, user, data_scope, db):
    """自定义客户数据过滤函数"""
    from app.models.project import Project
    
    if data_scope == "CUSTOMER":
        # 客户门户：只能看自己公司的项目
        if user.customer_id:
            query = query.filter(
                or_(
                    query.model_class.customer_id == user.customer_id,
                    query.model_class.created_by == user.id
                )
            )
        else:
            return query.filter(False)
    
    return query

# 使用自定义过滤函数
config = DataScopeConfig(
    owner_field="created_by",
    custom_filter=custom_customer_filter
)

query = GenericFilterService.filter_by_scope(
    db=db,
    query=query,
    model=Project,
    user=current_user,
    config=config
)
```

### 示例 5: API 端点集成

```python
from fastapi import APIRouter, Depends
from app.core.deps import get_current_user, get_db

router = APIRouter()

@router.get("/api/projects")
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = 1,
    size: int = 20
):
    """项目列表API（带数据权限过滤）"""
    from app.models.project import Project
    
    # 创建查询
    query = db.query(Project)
    
    # 应用数据权限过滤
    query = DataScopeServiceEnhanced.apply_data_scope(
        query=query,
        db=db,
        user=current_user,
        resource_type="project",
        org_field="dept_id",
        owner_field="created_by",
        pm_field="pm_id"
    )
    
    # 分页
    total = query.count()
    projects = query.offset((page - 1) * size).limit(size).all()
    
    return {
        "total": total,
        "page": page,
        "size": size,
        "data": projects
    }

@router.get("/api/projects/{project_id}")
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目详情（带权限检查）"""
    from app.models.project import Project
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查访问权限
    if not DataScopeServiceEnhanced.can_access_data(
        db=db,
        user=current_user,
        resource_type="project",
        data=project,
        org_field="dept_id",
        owner_field="created_by"
    ):
        raise HTTPException(status_code=403, detail="无权访问此项目")
    
    return project
```

---

## 最佳实践

### 1. 选择合适的数据范围类型

```python
# ✅ 好的做法：根据角色选择合适的范围
role_scope_mapping = {
    "CEO": "ALL",
    "事业部总监": "BUSINESS_UNIT",
    "部门经理": "DEPARTMENT",
    "团队leader": "TEAM",
    "项目经理": "PROJECT",
    "普通员工": "OWN"
}

# ❌ 避免：所有人都设置为 ALL
# 这会导致权限控制失效
```

### 2. 使用预定义配置

```python
# ✅ 好的做法：使用预定义配置
from app.services.data_scope.config import DATA_SCOPE_CONFIGS

config = DATA_SCOPE_CONFIGS.get("purchase_order")
query = GenericFilterService.filter_by_scope(db, query, PurchaseOrder, user, config)

# ❌ 避免：每次都手动创建配置
# 增加维护成本，容易出错
```

### 3. 合理使用字段映射

```python
# ✅ 好的做法：明确指定字段映射
query = DataScopeServiceEnhanced.apply_data_scope(
    query=query,
    db=db,
    user=current_user,
    resource_type="purchase_order",
    org_field="department_id",      # 明确的组织字段
    owner_field="requester_id",     # 明确的所有者字段
    pm_field="project_manager_id"   # 明确的PM字段
)

# ⚠️ 注意：确保字段在模型中存在
# 否则会跳过过滤或返回空结果
```

### 4. 分层权限检查

```python
# ✅ 好的做法：先检查列表权限，再检查详情权限
def update_project(db: Session, user: User, project_id: int, data: dict):
    """更新项目（分层权限检查）"""
    
    # 第一层：查询时过滤
    query = db.query(Project).filter(Project.id == project_id)
    query = DataScopeServiceEnhanced.apply_data_scope(
        query, db, user, "project", org_field="dept_id"
    )
    project = query.first()
    
    if not project:
        raise HTTPException(404, "项目不存在或无权访问")
    
    # 第二层：操作前再次检查
    if not DataScopeServiceEnhanced.can_access_data(
        db, user, "project", project, org_field="dept_id"
    ):
        raise HTTPException(403, "无权修改此项目")
    
    # 执行更新
    for key, value in data.items():
        setattr(project, key, value)
    db.commit()
    
    return project
```

### 5. 日志和监控

```python
import logging

logger = logging.getLogger(__name__)

def get_sensitive_data(db: Session, user: User):
    """获取敏感数据（带日志）"""
    
    logger.info(
        f"用户 {user.id} 访问敏感数据",
        extra={
            "user_id": user.id,
            "username": user.username,
            "resource_type": "sensitive_data"
        }
    )
    
    query = db.query(SensitiveData)
    query = DataScopeServiceEnhanced.apply_data_scope(
        query, db, user, "sensitive_data"
    )
    
    results = query.all()
    
    logger.info(f"返回 {len(results)} 条记录")
    
    return results
```

---

## 性能优化

### 1. 使用组织 path 字段

```python
# ✅ 高性能：使用 path 字段（单次查询）
# OrganizationUnit 表应该有 path 字段
# 例如: path = "/1/5/10/" 表示组织树路径

# 自动使用优化的查询方式
ids = DataScopeServiceEnhanced._get_subtree_ids_optimized(db, org_id)

# ❌ 低性能：递归查询（N+1问题）
# 当没有 path 字段时会自动降级
```

### 2. 添加数据库索引

```sql
-- 组织表索引
CREATE INDEX idx_org_unit_path ON organization_unit(path);
CREATE INDEX idx_org_unit_parent_id ON organization_unit(parent_id);
CREATE INDEX idx_org_unit_is_active ON organization_unit(is_active);

-- 用户组织分配表索引
CREATE INDEX idx_emp_org_assignment_user ON employee_org_assignment(employee_id);
CREATE INDEX idx_emp_org_assignment_org ON employee_org_assignment(org_unit_id);
CREATE INDEX idx_emp_org_assignment_active ON employee_org_assignment(is_active);

-- 业务表索引
CREATE INDEX idx_project_dept_id ON project(dept_id);
CREATE INDEX idx_project_created_by ON project(created_by);
CREATE INDEX idx_purchase_order_dept ON purchase_order(department_id);
```

### 3. 使用缓存（规划中）

```python
# 未来版本将支持缓存
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_user_accessible_orgs_cached(user_id: int, scope_type: str):
    """缓存用户可访问的组织单元"""
    # 实现细节...
    pass
```

### 4. 批量查询优化

```python
# ✅ 好的做法：使用 IN 查询
accessible_org_ids = DataScopeServiceEnhanced.get_accessible_org_units(
    db, user.id, scope_type
)
query = query.filter(Project.dept_id.in_(accessible_org_ids))

# ❌ 避免：循环单条查询
# for org_id in org_ids:
#     query = query.filter(Project.dept_id == org_id)
```

---

## 故障排查

### 问题 1: 用户看不到任何数据

**症状**: 查询返回空结果

**可能原因**:
1. 用户没有分配组织单元
2. 用户权限设置为 OWN 但不是数据所有者
3. 模型缺少必要的字段

**解决方案**:
```python
# 检查用户组织单元
user_orgs = DataScopeServiceEnhanced.get_user_org_units(db, user.id)
print(f"用户组织单元: {user_orgs}")

# 检查可访问组织
accessible_orgs = DataScopeServiceEnhanced.get_accessible_org_units(
    db, user.id, scope_type
)
print(f"可访问组织: {accessible_orgs}")

# 检查用户权限
from app.services.permission_service import PermissionService
scopes = PermissionService.get_user_data_scopes(db, user.id)
print(f"数据范围: {scopes}")
```

### 问题 2: 权限过滤不生效

**症状**: 用户能看到不应该看到的数据

**可能原因**:
1. 字段名配置错误
2. 超级管理员跳过了过滤
3. 范围类型设置错误

**解决方案**:
```python
# 检查字段是否存在
from app.models.project import Project
print(f"模型字段: {Project.__table__.columns.keys()}")

# 启用详细日志
import logging
logging.getLogger("app.services.data_scope_service_enhanced").setLevel(logging.DEBUG)

# 检查用户是否是超级管理员
print(f"是否超级管理员: {user.is_superuser}")
```

### 问题 3: 性能问题

**症状**: 查询很慢

**可能原因**:
1. 缺少数据库索引
2. 组织树过深导致递归查询
3. 没有使用 path 字段优化

**解决方案**:
```python
# 检查查询执行计划
from sqlalchemy import text
explain_query = text("EXPLAIN ANALYZE " + str(query))
result = db.execute(explain_query)
print(result.fetchall())

# 添加必要的索引（参见性能优化章节）

# 确保组织表有 path 字段
from app.models.organization import OrganizationUnit
org = db.query(OrganizationUnit).first()
print(f"组织路径: {org.path if org else 'N/A'}")
```

---

## 附录

### 枚举映射表

| ScopeType | DataScopeEnum | 描述 |
|-----------|---------------|------|
| ALL | ALL | 全部数据 |
| BUSINESS_UNIT | DEPT | 事业部数据（映射到DEPT） |
| DEPARTMENT | DEPT | 部门数据 |
| TEAM | DEPT | 团队数据（映射到DEPT） |
| PROJECT | PROJECT | 项目数据 |
| OWN | OWN | 个人数据 |

### 常用字段名

| 资源类型 | 组织字段 | 所有者字段 | PM字段 |
|----------|----------|------------|--------|
| project | dept_id | created_by | pm_id |
| purchase_order | department_id | requester_id | - |
| task | - | assignee_id | project_id |
| issue | department_id | reporter_id | - |
| document | - | uploaded_by | project_id |

### 相关文档

- [权限系统架构](./PERMISSION_ARCHITECTURE.md)
- [组织架构管理](./ORGANIZATION_MANAGEMENT.md)
- [API 权限控制](./API_PERMISSION_CONTROL.md)

---

**版本**: v1.0.0  
**更新时间**: 2026-02-14  
**维护者**: PMS开发团队

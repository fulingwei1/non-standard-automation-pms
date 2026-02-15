# -*- coding: utf-8 -*-
"""
租户访问权限检查

提供细粒度的租户资源访问控制。

核心功能：
1. check_tenant_access - 检查用户是否有权访问资源
2. validate_tenant_match - 验证多个资源是否属于同一租户
3. ensure_tenant_consistency - 确保创建的资源使用正确的租户ID

使用场景：
- API 处理逻辑中显式验证
- 跨表关联前检查
- 批量操作前预检

Author: Team 3 - 租户隔离小组
Date: 2026-02-16
"""

import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


def check_tenant_access(user: Any, resource_tenant_id: Optional[int]) -> bool:
    """
    检查用户是否有权访问指定租户的资源
    
    访问规则：
    1. 超级管理员（is_superuser=True 且 tenant_id=None）可以访问所有资源
    2. 系统级资源（tenant_id=None）所有用户都可以访问
    3. 普通用户只能访问本租户（user.tenant_id == resource_tenant_id）的资源
    
    这个函数是租户隔离的核心逻辑，所有权限检查都基于这些规则。
    
    使用方法：
        # 检查项目访问权限
        if not check_tenant_access(current_user, project.tenant_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 检查用户是否可以创建资源
        if not check_tenant_access(current_user, new_tenant_id):
            raise HTTPException(status_code=403, detail="Cannot create resource for this tenant")
    
    Args:
        user: 当前用户对象（需要有 tenant_id 和 is_superuser 属性）
        resource_tenant_id: 资源的租户ID（None 表示系统级资源）
        
    Returns:
        bool: True 表示有权访问，False 表示无权访问
    
    Examples:
        >>> # 超级管理员访问任何资源
        >>> superuser = User(id=1, tenant_id=None, is_superuser=True)
        >>> check_tenant_access(superuser, 100)  # True
        
        >>> # 普通用户访问本租户资源
        >>> user = User(id=2, tenant_id=100, is_superuser=False)
        >>> check_tenant_access(user, 100)  # True
        
        >>> # 普通用户访问其他租户资源
        >>> check_tenant_access(user, 200)  # False
        
        >>> # 任何用户访问系统级资源
        >>> check_tenant_access(user, None)  # True
    """
    # 获取用户的租户ID和超级管理员状态
    user_tenant_id = getattr(user, 'tenant_id', None)
    is_superuser = getattr(user, 'is_superuser', False)
    
    # 规则1：超级管理员可以访问所有数据
    if is_superuser and user_tenant_id is None:
        logger.debug(
            f"Superuser {getattr(user, 'id', 'unknown')} granted access to "
            f"resource with tenant_id={resource_tenant_id}"
        )
        return True
    
    # 规则2：系统级资源（tenant_id=None）所有用户可访问
    if resource_tenant_id is None:
        logger.debug(
            f"User {getattr(user, 'id', 'unknown')} granted access to "
            f"system resource (tenant_id=None)"
        )
        return True
    
    # 规则3：普通用户只能访问本租户资源
    has_access = user_tenant_id == resource_tenant_id
    
    if has_access:
        logger.debug(
            f"User {getattr(user, 'id', 'unknown')} (tenant={user_tenant_id}) "
            f"granted access to resource (tenant={resource_tenant_id})"
        )
    else:
        logger.warning(
            f"User {getattr(user, 'id', 'unknown')} (tenant={user_tenant_id}) "
            f"DENIED access to resource (tenant={resource_tenant_id})"
        )
    
    return has_access


def validate_tenant_match(
    user: Any,
    *tenant_ids: Optional[int]
) -> bool:
    """
    验证多个资源是否都属于用户可访问的租户
    
    这个函数用于检查批量操作或关联操作中涉及的所有资源是否合法。
    例如：创建订单时关联的客户、项目、产品等是否都属于同一租户。
    
    使用方法：
        @router.post("/orders")
        async def create_order(
            data: OrderCreate,
            current_user: User = Depends(get_current_user)
        ):
            # 验证客户、项目都属于当前租户
            if not validate_tenant_match(
                current_user,
                customer.tenant_id,
                project.tenant_id
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Resources belong to different tenants"
                )
            
            # 继续创建订单
            ...
    
    Args:
        user: 当前用户对象
        *tenant_ids: 要检查的租户ID列表
        
    Returns:
        bool: True 表示所有资源都可访问且属于同一租户，False 表示有问题
    """
    if not tenant_ids:
        return True
    
    # 检查每个租户ID是否都可访问
    for tid in tenant_ids:
        if not check_tenant_access(user, tid):
            logger.warning(
                f"Tenant mismatch detected: user={getattr(user, 'id', 'unknown')}, "
                f"user_tenant={getattr(user, 'tenant_id', None)}, "
                f"resource_tenants={tenant_ids}"
            )
            return False
    
    # 检查所有非None的租户ID是否相同
    non_null_tenants = [tid for tid in tenant_ids if tid is not None]
    if non_null_tenants and len(set(non_null_tenants)) > 1:
        logger.warning(
            f"Multiple different tenant IDs in one operation: {non_null_tenants}"
        )
        return False
    
    return True


def ensure_tenant_consistency(
    user: Any,
    resource_data: dict,
    tenant_field: str = 'tenant_id'
) -> dict:
    """
    确保创建的资源使用正确的租户ID
    
    这个函数用于创建资源时自动设置或验证 tenant_id，防止：
    1. 普通用户尝试创建其他租户的资源
    2. 忘记设置 tenant_id
    3. tenant_id 被恶意篡改
    
    使用方法：
        @router.post("/projects")
        async def create_project(
            data: ProjectCreate,
            current_user: User = Depends(get_current_user)
        ):
            # 确保项目属于当前用户的租户
            project_dict = data.dict()
            project_dict = ensure_tenant_consistency(current_user, project_dict)
            
            project = Project(**project_dict)
            db.add(project)
            db.commit()
            return project
    
    Args:
        user: 当前用户对象
        resource_data: 资源数据字典
        tenant_field: 租户ID字段名（默认 'tenant_id'）
        
    Returns:
        dict: 修正后的资源数据
        
    Raises:
        ValueError: 如果普通用户尝试创建其他租户的资源
    """
    user_tenant_id = getattr(user, 'tenant_id', None)
    is_superuser = getattr(user, 'is_superuser', False)
    
    # 获取请求中的 tenant_id
    requested_tenant_id = resource_data.get(tenant_field)
    
    # 超级管理员可以为任何租户创建资源
    if is_superuser and user_tenant_id is None:
        # 如果没有指定 tenant_id，保持为 None（系统级资源）
        logger.debug(
            f"Superuser creating resource with tenant_id={requested_tenant_id}"
        )
        return resource_data
    
    # 普通用户只能为自己的租户创建资源
    if requested_tenant_id is not None and requested_tenant_id != user_tenant_id:
        error_msg = (
            f"User {getattr(user, 'id', 'unknown')} (tenant={user_tenant_id}) "
            f"attempted to create resource for tenant={requested_tenant_id}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # 自动设置租户ID
    resource_data[tenant_field] = user_tenant_id
    logger.debug(
        f"Resource tenant_id set to {user_tenant_id} for user {getattr(user, 'id', 'unknown')}"
    )
    
    return resource_data


def check_bulk_access(
    user: Any,
    resources: List[Any],
    tenant_field: str = 'tenant_id'
) -> bool:
    """
    检查用户是否有权访问资源列表中的所有资源
    
    用于批量操作前的权限预检。
    
    Args:
        user: 当前用户对象
        resources: 资源对象列表
        tenant_field: 租户ID字段名
        
    Returns:
        bool: True 表示全部可访问，False 表示有无权访问的资源
    """
    for resource in resources:
        resource_tenant_id = getattr(resource, tenant_field, None)
        if not check_tenant_access(user, resource_tenant_id):
            logger.warning(
                f"Bulk access check failed: user={getattr(user, 'id', 'unknown')}, "
                f"resource_id={getattr(resource, 'id', 'unknown')}, "
                f"resource_tenant={resource_tenant_id}"
            )
            return False
    
    return True


# 导出公共接口
__all__ = [
    'check_tenant_access',
    'validate_tenant_match',
    'ensure_tenant_consistency',
    'check_bulk_access',
]

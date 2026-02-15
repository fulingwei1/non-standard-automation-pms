# -*- coding: utf-8 -*-
"""
租户隔离装饰器

提供 API 端点级别的租户隔离检查和配置。

核心功能：
1. require_tenant_isolation - 强制API端点执行租户隔离
2. allow_cross_tenant - 允许跨租户访问（仅超级管理员）
3. tenant_resource_check - 检查资源是否属于当前租户

使用场景：
- 所有业务 API 都应该使用 @require_tenant_isolation
- 系统管理 API 可以使用 @allow_cross_tenant
- 资源访问前使用 tenant_resource_check 验证权限

Author: Team 3 - 租户隔离小组
Date: 2026-02-16
"""

import logging
from functools import wraps
from typing import Callable, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def require_tenant_isolation(func: Callable) -> Callable:
    """
    装饰器：强制API端点执行租户隔离检查
    
    这个装饰器确保：
    1. API 端点接收到的用户已经通过认证
    2. 用户的 tenant_id 被设置到数据库会话的 info 字典中
    3. 后续的数据库查询会自动应用租户过滤
    
    使用方法：
        @router.get("/projects")
        @require_tenant_isolation
        async def list_projects(
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user)
        ):
            # 查询会自动过滤当前租户的数据
            projects = db.query(Project).all()
            return projects
    
    注意事项：
    - 必须在依赖注入之后使用（函数参数中要有 db 和 current_user）
    - 适用于所有业务 API
    - 系统 API 应该使用 @allow_cross_tenant
    
    Args:
        func: 要装饰的异步函数
        
    Returns:
        装饰后的函数
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 从参数中获取数据库会话和当前用户
        db: Optional[Session] = kwargs.get('db')
        current_user = kwargs.get('current_user')
        
        if db is None:
            logger.error(f"@require_tenant_isolation: 'db' not found in kwargs for {func.__name__}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database session not available"
            )
        
        if current_user is None:
            logger.error(f"@require_tenant_isolation: 'current_user' not found in kwargs for {func.__name__}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # 将租户信息设置到数据库会话中
        # 这样即使 TenantQuery 无法从请求上下文获取用户，也能从 session.info 获取
        if not hasattr(db, 'info'):
            db.info = {}
        
        db.info['tenant_id'] = current_user.tenant_id
        db.info['current_user'] = current_user
        
        logger.debug(
            f"Tenant isolation enforced: endpoint={func.__name__}, "
            f"user_id={current_user.id}, tenant_id={current_user.tenant_id}"
        )
        
        # 执行原函数
        return await func(*args, **kwargs)
    
    return wrapper


def allow_cross_tenant(admin_only: bool = True):
    """
    装饰器工厂：允许跨租户访问
    
    这个装饰器用于系统管理 API，允许访问所有租户的数据。
    
    参数：
        admin_only: 是否仅允许超级管理员（默认 True）
    
    使用方法：
        @router.get("/admin/all-projects")
        @allow_cross_tenant(admin_only=True)
        async def list_all_projects(
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user)
        ):
            # 获取所有租户的项目
            query = db.query(Project)
            query._skip_tenant_filter = True
            projects = query.all()
            return projects
    
    安全注意事项：
    - 仅用于系统管理 API
    - 建议始终设置 admin_only=True
    - 需要配合权限检查使用
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            
            if current_user is None:
                logger.error(f"@allow_cross_tenant: 'current_user' not found for {func.__name__}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # 检查是否是超级管理员
            if admin_only and not getattr(current_user, 'is_superuser', False):
                logger.warning(
                    f"Non-admin user {current_user.id} attempted cross-tenant access "
                    f"to {func.__name__}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Superuser access required"
                )
            
            logger.info(
                f"Cross-tenant access granted: endpoint={func.__name__}, "
                f"user_id={current_user.id}, is_superuser={current_user.is_superuser}"
            )
            
            # 执行原函数
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def tenant_resource_check(
    user,
    resource_tenant_id: Optional[int],
    resource_name: str = "resource"
) -> None:
    """
    检查用户是否有权访问指定租户的资源
    
    这个函数用于在 API 处理逻辑中显式检查资源访问权限。
    虽然 TenantQuery 已经自动过滤，但在某些场景下需要额外验证：
    1. 创建资源时验证 tenant_id
    2. 更新资源时验证所有权
    3. 关联资源时验证跨租户引用
    
    使用方法：
        @router.put("/projects/{project_id}")
        async def update_project(
            project_id: int,
            data: ProjectUpdate,
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user)
        ):
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            # 验证资源访问权限
            tenant_resource_check(current_user, project.tenant_id, "Project")
            
            # 继续更新逻辑
            ...
    
    Args:
        user: 当前用户对象
        resource_tenant_id: 资源的租户ID
        resource_name: 资源名称（用于错误消息）
        
    Raises:
        HTTPException: 如果用户无权访问该资源
    """
    from app.core.permissions.tenant_access import check_tenant_access
    
    if not check_tenant_access(user, resource_tenant_id):
        logger.warning(
            f"Tenant access denied: user_id={user.id}, user_tenant={user.tenant_id}, "
            f"resource_tenant={resource_tenant_id}, resource={resource_name}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: {resource_name} belongs to a different tenant"
        )
    
    logger.debug(
        f"Tenant access granted: user_id={user.id}, resource={resource_name}, "
        f"tenant_id={resource_tenant_id}"
    )


# 导出公共接口
__all__ = [
    'require_tenant_isolation',
    'allow_cross_tenant',
    'tenant_resource_check',
]

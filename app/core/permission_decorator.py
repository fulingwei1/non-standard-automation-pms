# -*- coding: utf-8 -*-
"""
权限装饰器 (Permission Decorator)

提供统一的 FastAPI 依赖注入式权限检查装饰器
"""

from typing import List, Optional, Callable
from functools import wraps
import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.permission_service import PermissionService

logger = logging.getLogger(__name__)


def require_permissions(
    permissions: List[str],
    require_all: bool = True
) -> Callable:
    """
    权限检查依赖工厂

    Args:
        permissions: 所需权限编码列表
        require_all: True 表示需要所有权限，False 表示只需任一权限

    Returns:
        FastAPI 依赖函数

    Usage:
        @router.get("/projects")
        async def list_projects(
            current_user: User = Depends(require_permissions(['project:read']))
        ):
            pass

        @router.post("/projects")
        async def create_project(
            current_user: User = Depends(require_permissions(['project:create', 'project:update'], require_all=False))
        ):
            pass
    """
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        # 超级管理员跳过检查
        if current_user.is_superuser:
            return current_user

        # 获取用户权限
        user_permissions = PermissionService.get_user_permissions(db, current_user.id)

        # 检查权限
        if require_all:
            has_permission = all(p in user_permissions for p in permissions)
        else:
            has_permission = any(p in user_permissions for p in permissions)

        if not has_permission:
            required = "所有" if require_all else "任一"
            logger.warning(
                f"权限检查失败: user_id={current_user.id}, "
                f"required={permissions}, require_all={require_all}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"没有执行此操作的权限（需要{required}权限: {', '.join(permissions)}）"
            )

        return current_user

    return permission_dependency


def require_permission(permission: str) -> Callable:
    """
    单个权限检查依赖工厂（简化版）

    Args:
        permission: 权限编码

    Returns:
        FastAPI 依赖函数

    Usage:
        @router.get("/projects")
        async def list_projects(
            current_user: User = Depends(require_permission('project:read'))
        ):
            pass
    """
    return require_permissions([permission], require_all=True)


def require_any_permission(*permissions: str) -> Callable:
    """
    任一权限检查依赖工厂

    Args:
        *permissions: 权限编码（可变参数）

    Returns:
        FastAPI 依赖函数

    Usage:
        @router.get("/projects")
        async def list_projects(
            current_user: User = Depends(require_any_permission('project:read', 'project:admin'))
        ):
            pass
    """
    return require_permissions(list(permissions), require_all=False)


def require_module_access(module: str) -> Callable:
    """
    模块级访问权限检查依赖工厂

    Args:
        module: 模块名称（如 procurement, finance, production）

    Returns:
        FastAPI 依赖函数

    Usage:
        @router.get("/procurement/orders")
        async def list_orders(
            current_user: User = Depends(require_module_access('procurement'))
        ):
            pass
    """
    permission_code = f"{module}:read"
    return require_permission(permission_code)


# ============================================================
# 模块级权限检查（兼容旧代码）
# ============================================================

def require_procurement_access() -> Callable:
    """采购模块访问权限"""
    return require_module_access('procurement')


def require_finance_access() -> Callable:
    """财务模块访问权限"""
    return require_module_access('finance')


def require_production_access() -> Callable:
    """生产模块访问权限"""
    return require_module_access('production')


def require_hr_access() -> Callable:
    """人力资源模块访问权限"""
    return require_module_access('hr')


def require_sales_access() -> Callable:
    """销售模块访问权限"""
    return require_module_access('sales')


def require_service_access() -> Callable:
    """售后服务模块访问权限"""
    return require_module_access('service')


def require_project_access() -> Callable:
    """项目管理模块访问权限"""
    return require_module_access('project')


# ============================================================
# 数据权限检查装饰器
# ============================================================

def with_data_scope(resource_type: str) -> Callable:
    """
    数据权限范围注入装饰器

    将用户的数据权限范围注入到请求上下文中

    Args:
        resource_type: 资源类型

    Returns:
        装饰器函数

    Usage:
        @router.get("/projects")
        @with_data_scope('project')
        async def list_projects(
            current_user: User = Depends(get_current_active_user),
            data_scope: str = None  # 会被自动注入
        ):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_active_user),
            db: Session = Depends(get_db),
            **kwargs
        ):
            # 获取数据权限范围
            scopes = PermissionService.get_user_data_scopes(db, current_user.id)
            data_scope = scopes.get(resource_type, 'OWN')

            # 注入到 kwargs
            kwargs['data_scope'] = data_scope

            return await func(*args, current_user=current_user, db=db, **kwargs)

        return wrapper
    return decorator


# ============================================================
# 权限检查辅助函数
# ============================================================

async def check_resource_permission(
    db: Session,
    user: User,
    resource_type: str,
    action: str
) -> bool:
    """
    检查用户对资源的操作权限

    Args:
        db: 数据库会话
        user: 用户对象
        resource_type: 资源类型
        action: 操作类型（create, read, update, delete）

    Returns:
        是否有权限
    """
    permission_code = f"{resource_type}:{action}"
    return PermissionService.check_permission(db, user.id, permission_code, user)


def permission_required(permission_code: str):
    """
    同步函数的权限检查装饰器

    Args:
        permission_code: 权限编码

    Returns:
        装饰器函数

    Usage:
        @permission_required('project:create')
        def create_project(db: Session, user: User, data: dict):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, db: Session = None, user: User = None, **kwargs):
            if user is None:
                raise ValueError("user 参数是必需的")

            if db is None:
                raise ValueError("db 参数是必需的")

            # 超级管理员跳过检查
            if user.is_superuser:
                return func(*args, db=db, user=user, **kwargs)

            # 检查权限
            if not PermissionService.check_permission(db, user.id, permission_code, user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"没有执行此操作的权限（需要权限: {permission_code}）"
                )

            return func(*args, db=db, user=user, **kwargs)

        return wrapper
    return decorator

# -*- coding: utf-8 -*-
"""
通用权限检查模块

包含基础权限检查和权限装饰器
"""

import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...models.user import User
from .deps import get_db, get_current_active_user

logger = logging.getLogger(__name__)


def check_permission(user: User, permission_code: str, db: Session = None) -> bool:
    """检查用户权限"""
    if user.is_superuser:
        return True

    # 使用SQL查询避免ORM关系错误
    try:
        from sqlalchemy import text
        if db is None:
            # 如果没有提供db，尝试使用ORM（可能失败）
            for user_role in user.roles:
                for role_permission in user_role.role.permissions:
                    if role_permission.permission.permission_code == permission_code:
                        return True
            return False
        else:
            # 使用SQL查询
            sql = """
                SELECT COUNT(*)
                FROM user_roles ur
                JOIN role_permissions rp ON ur.role_id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.id
                WHERE ur.user_id = :user_id
                AND p.perm_code = :permission_code
            """
            result = db.execute(text(sql), {
                "user_id": user.id,
                "permission_code": permission_code
            }).scalar()
            return result > 0
    except Exception as e:
        logger.warning(f"权限检查失败，使用ORM查询: {e}")
        # 降级到ORM查询
        try:
            for user_role in user.roles:
                for role_permission in user_role.role.permissions:
                    if role_permission.permission.permission_code == permission_code:
                        return True
        except Exception:
            pass
        return False


def require_permission(permission_code: str):
    """权限装饰器依赖"""

    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        if not check_permission(current_user, permission_code, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有执行此操作的权限"
            )
        return current_user

    return permission_checker

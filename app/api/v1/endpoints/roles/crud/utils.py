# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
角色CRUD工具函数

提供角色相关的辅助函数
"""

import logging
from typing import List

from sqlalchemy.orm import Session

from app.models.user import Role, RolePermission, UserRole

logger = logging.getLogger(__name__)



def _get_role_user_ids(db: Session, role_id: int) -> List[int]:
    """获取角色下所有用户的 ID 列表"""
    user_roles = db.query(UserRole).filter(UserRole.role_id == role_id).all()
    return [ur.user_id for ur in user_roles]


def _get_child_role_ids(db: Session, role_id: int, visited: set = None) -> List[int]:
    """递归获取所有子角色 ID（权限继承影响链）"""
    if visited is None:
        visited = set()

    if role_id in visited:
        return []

    visited.add(role_id)
    child_roles = db.query(Role).filter(Role.parent_id == role_id).all()
    result = [r.id for r in child_roles]

    for child in child_roles:
        result.extend(_get_child_role_ids(db, child.id, visited))

    return result


def _invalidate_role_cache(db: Session, role_id: int, include_children: bool = True):
    """
    使角色相关缓存失效

    Args:
        db: 数据库会话
        role_id: 角色 ID
        include_children: 是否同时失效子角色的缓存（用于权限继承场景）
    """
    try:
        from app.services.permission_cache_service import get_permission_cache_service
        
        cache_service = get_permission_cache_service()

        # 获取该角色下的所有用户
        user_ids = _get_role_user_ids(db, role_id)

        # 如果需要包含子角色，递归获取
        if include_children:
            child_role_ids = _get_child_role_ids(db, role_id)
            for child_id in child_role_ids:
                user_ids.extend(_get_role_user_ids(db, child_id))
            user_ids = list(set(user_ids))  # 去重

        # 使缓存失效
        cache_service.invalidate_role_and_users(role_id, user_ids)
        logger.info(f"Cache invalidated for role {role_id}, affected users: {len(user_ids)}")
    except Exception as e:
        logger.warning(f"Cache invalidation failed for role {role_id}: {e}")


def _would_create_cycle(db: Session, role_id: int, new_parent_id: int) -> bool:
    """检查设置新父角色是否会导致循环引用"""
    from app.models.user import Role
    
    visited = {role_id}
    current_id = new_parent_id

    while current_id is not None:
        if current_id in visited:
            return True
        visited.add(current_id)
        parent = db.query(Role).filter(Role.id == current_id).first()
        current_id = parent.parent_id if parent else None

    return False


def _count_inherited_permissions(db: Session, parent_id: int, visited: set = None) -> int:
    """递归计算继承的权限数量"""
    from app.models.user import Role, RolePermission
    
    if visited is None:
        visited = set()

    if parent_id is None or parent_id in visited:
        return 0

    visited.add(parent_id)
    parent = db.query(Role).filter(Role.id == parent_id).first()
    if not parent:
        return 0

    count = db.query(RolePermission).filter(RolePermission.role_id == parent_id).count()
    if parent.parent_id:
        count += _count_inherited_permissions(db, parent.parent_id, visited)

    return count


def _get_parent_roles(db: Session, parent_id: int, visited: set = None) -> List[Role]:
    """递归获取所有父角色（防止循环引用）"""
    from app.models.user import Role
    from typing import List
    
    if visited is None:
        visited = set()

    if parent_id in visited:
        return []

    visited.add(parent_id)
    parent = db.query(Role).filter(Role.id == parent_id).first()
    if not parent:
        return []

    result = [parent]
    if parent.parent_id:
        result.extend(_get_parent_roles(db, parent.parent_id, visited))

    return result

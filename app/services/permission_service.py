# -*- coding: utf-8 -*-
"""
权限服务 (Permission Service)

提供统一的权限检查接口，替代分散的硬编码角色检查函数
"""

import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.organization import (
    EmployeeOrgAssignment,
    OrganizationUnit,
    Position,
    PositionRole,
)
from app.models.permission import (
    DataScopeRule,
    MenuPermission,
    RoleDataScope,
    RoleMenu,
)
from app.models.user import Permission, Role, RolePermission, User, UserRole

logger = logging.getLogger(__name__)


class PermissionService:
    """
    权限服务类

    提供用户权限的获取、检查、菜单构建等功能
    """

    @staticmethod
    def get_user_effective_roles(db: Session, user_id: int) -> List[Role]:
        """
        获取用户的有效角色（直接分配 + 岗位默认角色）

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            角色列表
        """
        roles_set: Set[int] = set()
        roles: List[Role] = []

        try:
            # 1. 获取直接分配的角色
            user_roles = db.query(UserRole).filter(
                UserRole.user_id == user_id
            ).all()

            for ur in user_roles:
                if ur.role_id not in roles_set:
                    role = db.query(Role).filter(
                        Role.id == ur.role_id,
                        Role.is_active == True
                    ).first()
                    if role:
                        roles_set.add(role.id)
                        roles.append(role)

            # 2. 获取岗位默认角色
            assignments = db.query(EmployeeOrgAssignment).join(
                User, User.employee_id == EmployeeOrgAssignment.employee_id
            ).filter(
                User.id == user_id,
                EmployeeOrgAssignment.is_active == True
            ).all()

            for assignment in assignments:
                if assignment.position_id:
                    position_roles = db.query(PositionRole).filter(
                        PositionRole.position_id == assignment.position_id,
                        PositionRole.is_active == True
                    ).all()

                    for pr in position_roles:
                        if pr.role_id not in roles_set:
                            role = db.query(Role).filter(
                                Role.id == pr.role_id,
                                Role.is_active == True
                            ).first()
                            if role:
                                roles_set.add(role.id)
                                roles.append(role)

        except Exception as e:
            logger.warning(f"获取用户角色失败 (user_id={user_id}): {e}")
            # 降级：仅返回直接分配的角色
            try:
                sql = text("""
                    SELECT r.* FROM roles r
                    JOIN user_roles ur ON r.id = ur.role_id
                    WHERE ur.user_id = :user_id AND r.is_active = 1
                """)
                result = db.execute(sql, {"user_id": user_id})
                for row in result:
                    role = Role()
                    role.id = row.id
                    role.role_code = row.role_code
                    role.role_name = row.role_name
                    roles.append(role)
            except Exception as e2:
                logger.error(f"降级查询也失败: {e2}")

        return roles

    @staticmethod
    def get_user_permissions(db: Session, user_id: int) -> List[str]:
        """
        获取用户的所有权限编码列表

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            权限编码列表
        """
        permissions_set: Set[str] = set()

        try:
            # 获取用户的所有角色
            roles = PermissionService.get_user_effective_roles(db, user_id)

            # 获取每个角色的权限
            for role in roles:
                role_perms = db.query(RolePermission).filter(
                    RolePermission.role_id == role.id
                ).all()

                for rp in role_perms:
                    perm = db.query(Permission).filter(
                        Permission.id == rp.permission_id
                    ).first()
                    if perm and perm.permission_code:
                        permissions_set.add(perm.permission_code)

        except Exception as e:
            logger.warning(f"获取用户权限失败，使用SQL查询: {e}")
            try:
                sql = text("""
                    SELECT DISTINCT p.perm_code
                    FROM permissions p
                    JOIN role_permissions rp ON p.id = rp.permission_id
                    JOIN user_roles ur ON rp.role_id = ur.role_id
                    WHERE ur.user_id = :user_id
                """)
                result = db.execute(sql, {"user_id": user_id})
                for row in result:
                    if row.perm_code:
                        permissions_set.add(row.perm_code)
            except Exception as e2:
                logger.error(f"SQL查询权限也失败: {e2}")

        return list(permissions_set)

    @staticmethod
    def check_permission(
        db: Session,
        user_id: int,
        permission_code: str,
        user: Optional[User] = None
    ) -> bool:
        """
        检查用户是否有指定权限

        Args:
            db: 数据库会话
            user_id: 用户ID
            permission_code: 权限编码
            user: 用户对象（可选，用于检查超级管理员）

        Returns:
            是否有权限
        """
        # 超级管理员拥有所有权限
        if user and user.is_superuser:
            return True

        if not user:
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.is_superuser:
                return True

        # 检查权限
        permissions = PermissionService.get_user_permissions(db, user_id)
        return permission_code in permissions

    @staticmethod
    def check_any_permission(
        db: Session,
        user_id: int,
        permission_codes: List[str],
        user: Optional[User] = None
    ) -> bool:
        """
        检查用户是否有任一权限

        Args:
            db: 数据库会话
            user_id: 用户ID
            permission_codes: 权限编码列表
            user: 用户对象（可选）

        Returns:
            是否有任一权限
        """
        if user and user.is_superuser:
            return True

        permissions = PermissionService.get_user_permissions(db, user_id)
        return any(code in permissions for code in permission_codes)

    @staticmethod
    def check_all_permissions(
        db: Session,
        user_id: int,
        permission_codes: List[str],
        user: Optional[User] = None
    ) -> bool:
        """
        检查用户是否有所有权限

        Args:
            db: 数据库会话
            user_id: 用户ID
            permission_codes: 权限编码列表
            user: 用户对象（可选）

        Returns:
            是否有所有权限
        """
        if user and user.is_superuser:
            return True

        permissions = PermissionService.get_user_permissions(db, user_id)
        return all(code in permissions for code in permission_codes)

    @staticmethod
    def get_user_menus(db: Session, user_id: int, user: Optional[User] = None) -> List[Dict[str, Any]]:
        """
        获取用户可访问的菜单树

        Args:
            db: 数据库会话
            user_id: 用户ID
            user: 用户对象（可选）

        Returns:
            菜单树列表
        """
        # 超级管理员获取所有菜单
        if user and user.is_superuser:
            menus = db.query(MenuPermission).filter(
                MenuPermission.is_active == True,
                MenuPermission.is_visible == True,
                MenuPermission.parent_id == None
            ).order_by(MenuPermission.sort_order).all()
            return [menu.to_dict() for menu in menus]

        # 获取用户的所有角色
        roles = PermissionService.get_user_effective_roles(db, user_id)
        role_ids = [r.id for r in roles]

        if not role_ids:
            return []

        # 获取角色关联的菜单ID
        menu_ids: Set[int] = set()
        role_menus = db.query(RoleMenu).filter(
            RoleMenu.role_id.in_(role_ids),
            RoleMenu.is_active == True
        ).all()

        for rm in role_menus:
            menu_ids.add(rm.menu_id)

        if not menu_ids:
            return []

        # 构建菜单树
        def build_menu_tree(parent_id: Optional[int] = None) -> List[Dict[str, Any]]:
            menus = db.query(MenuPermission).filter(
                MenuPermission.id.in_(menu_ids),
                MenuPermission.is_active == True,
                MenuPermission.is_visible == True,
                MenuPermission.parent_id == parent_id
            ).order_by(MenuPermission.sort_order).all()

            result = []
            for menu in menus:
                menu_dict = {
                    "id": menu.id,
                    "code": menu.menu_code,
                    "name": menu.menu_name,
                    "path": menu.menu_path,
                    "icon": menu.menu_icon,
                    "type": menu.menu_type,
                    "sort": menu.sort_order,
                }
                children = build_menu_tree(menu.id)
                if children:
                    menu_dict["children"] = children
                result.append(menu_dict)
            return result

        return build_menu_tree()

    @staticmethod
    def get_user_data_scopes(db: Session, user_id: int) -> Dict[str, str]:
        """
        获取用户的数据权限范围映射

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            数据权限映射 { resource_type: scope_type }
        """
        scopes: Dict[str, str] = {}

        try:
            # 获取用户的所有角色
            roles = PermissionService.get_user_effective_roles(db, user_id)
            role_ids = [r.id for r in roles]

            if not role_ids:
                return scopes

            # 获取每个角色的数据权限
            role_data_scopes = db.query(RoleDataScope).filter(
                RoleDataScope.role_id.in_(role_ids),
                RoleDataScope.is_active == True
            ).all()

            # 合并数据权限（取最大范围）
            scope_priority = {
                'ALL': 6,
                'BUSINESS_UNIT': 5,
                'DEPARTMENT': 4,
                'TEAM': 3,
                'PROJECT': 2,
                'OWN': 1,
                'CUSTOM': 0,
            }

            for rds in role_data_scopes:
                rule = db.query(DataScopeRule).filter(
                    DataScopeRule.id == rds.scope_rule_id
                ).first()

                if rule:
                    resource = rds.resource_type
                    current_scope = scopes.get(resource)
                    new_scope = rule.scope_type

                    # 取更大的权限范围
                    if not current_scope or scope_priority.get(new_scope, 0) > scope_priority.get(current_scope, 0):
                        scopes[resource] = new_scope

        except Exception as e:
            logger.error(f"获取用户数据权限失败: {e}")

        return scopes

    @staticmethod
    def get_full_permission_data(
        db: Session,
        user_id: int,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        获取用户的完整权限数据（用于前端）

        Args:
            db: 数据库会话
            user_id: 用户ID
            user: 用户对象（可选）

        Returns:
            包含 permissions, menus, dataScopes 的字典
        """
        return {
            "permissions": PermissionService.get_user_permissions(db, user_id),
            "menus": PermissionService.get_user_menus(db, user_id, user),
            "dataScopes": PermissionService.get_user_data_scopes(db, user_id),
        }


# ============================================================
# 兼容层：保持与旧系统的兼容性
# ============================================================

def check_permission_compat(user: User, permission_code: str, db: Session) -> bool:
    """
    兼容层：检查权限（保持与旧代码兼容）

    Args:
        user: 用户对象
        permission_code: 权限编码
        db: 数据库会话

    Returns:
        是否有权限
    """
    return PermissionService.check_permission(db, user.id, permission_code, user)


# 模块级权限检查（兼容旧函数）
def has_module_permission(user: User, module: str, db: Session) -> bool:
    """
    检查用户是否有模块级访问权限

    Args:
        user: 用户对象
        module: 模块名称（procurement, finance, production 等）
        db: 数据库会话

    Returns:
        是否有权限
    """
    if user.is_superuser:
        return True

    # 检查模块的 read 权限
    permission_code = f"{module}:read"
    return PermissionService.check_permission(db, user.id, permission_code, user)

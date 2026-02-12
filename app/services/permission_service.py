# -*- coding: utf-8 -*-
"""
权限服务 (Permission Service)

提供统一的权限检查接口，替代分散的硬编码角色检查函数
使用 ApiPermission 模型替代旧的 Permission 模型
"""

import logging
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.organization import (
    EmployeeOrgAssignment,
    PositionRole,
)
from app.models.permission import (
    DataScopeRule,
    MenuPermission,
    RoleDataScope,
    RoleMenu,
)
from app.models.user import Role, User, UserRole

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
                        Role.is_active
                    ).first()
                    if role:
                        roles_set.add(role.id)
                        roles.append(role)
            
            # 2. 获取岗位默认角色
            assignments = db.query(EmployeeOrgAssignment).join(
                User, User.employee_id == EmployeeOrgAssignment.employee_id
            ).filter(
                User.id == user_id,
                EmployeeOrgAssignment.is_active
            ).all()
            
            for assignment in assignments:
                if assignment.position_id:
                    position_roles = db.query(PositionRole).filter(
                        PositionRole.position_id == assignment.position_id,
                        PositionRole.is_active
                    ).all()
                    
                    for pr in position_roles:
                        if pr.role_id not in roles_set:
                            role = db.query(Role).filter(
                                Role.id == pr.role_id,
                                Role.is_active
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
    def get_user_permissions(
        db: Session, user_id: int, tenant_id: Optional[int] = None
    ) -> List[str]:
        """
        获取用户的所有权限编码列表（支持多租户隔离 + 角色继承）

        多租户权限规则：
        - 系统级权限（tenant_id=NULL）：所有租户可用
        - 租户级权限（tenant_id=N）：仅该租户可用

        Args:
            db: 数据库会话
            user_id: 用户ID
            tenant_id: 租户ID（可选，用于过滤租户专属权限）

        Returns:
            权限编码列表
        """
        permissions_set: Set[str] = set()

        # 如果未提供 tenant_id，尝试从用户获取
        if tenant_id is None:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                tenant_id = user.tenant_id

        try:
            # 使用递归 SQL 查询（支持角色继承 + 租户隔离）
            sql = text("""
                WITH RECURSIVE role_tree AS (
                    -- 用户直接拥有的角色
                    SELECT r.id, r.parent_id, r.inherit_permissions
                    FROM roles r
                    JOIN user_roles ur ON ur.role_id = r.id
                    WHERE ur.user_id = :user_id

                    UNION ALL

                    -- 递归获取父角色（仅当 inherit_permissions=1 时）
                    SELECT r.id, r.parent_id, r.inherit_permissions
                    FROM roles r
                    JOIN role_tree rt ON r.id = rt.parent_id
                    WHERE rt.inherit_permissions = 1
                )
                SELECT DISTINCT ap.perm_code
                FROM role_tree rt
                JOIN role_api_permissions rap ON rt.id = rap.role_id
                JOIN api_permissions ap ON rap.permission_id = ap.id
                WHERE ap.is_active = 1
                AND (ap.tenant_id IS NULL OR ap.tenant_id = :tenant_id)
            """)
            result = db.execute(sql, {"user_id": user_id, "tenant_id": tenant_id})
            for row in result:
                if row[0]:
                    permissions_set.add(row[0])

        except Exception as e:
            logger.warning(f"获取用户权限失败（角色继承查询），回退到简单查询: {e}")
            try:
                # 回退到简单查询（不含角色继承）
                sql = text("""
                    SELECT DISTINCT ap.perm_code
                    FROM api_permissions ap
                    JOIN role_api_permissions rap ON ap.id = rap.permission_id
                    JOIN user_roles ur ON rap.role_id = ur.role_id
                    WHERE ur.user_id = :user_id AND ap.is_active = 1
                    AND (ap.tenant_id IS NULL OR ap.tenant_id = :tenant_id)
                """)
                result = db.execute(sql, {"user_id": user_id, "tenant_id": tenant_id})
                for row in result:
                    if row[0]:
                        permissions_set.add(row[0])
            except Exception as e2:
                logger.error(f"SQL查询权限也失败: {e2}")

        return list(permissions_set)
    
    @staticmethod
    def check_permission(
        db: Session,
        user_id: int,
        permission_code: str,
        user: Optional[User] = None,
        tenant_id: Optional[int] = None
    ) -> bool:
        """
        检查用户是否有指定权限（支持多租户隔离）

        Args:
            db: 数据库会话
            user_id: 用户ID
            permission_code: 权限编码
            user: 用户对象（可选，用于检查超级管理员）
            tenant_id: 租户ID（可选，用于权限隔离）

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

        # 获取租户ID（优先使用传入的，否则从用户获取）
        effective_tenant_id = tenant_id or (user.tenant_id if user else None)

        # 检查权限（包含租户隔离）
        permissions = PermissionService.get_user_permissions(db, user_id, effective_tenant_id)
        return permission_code in permissions

    @staticmethod
    def check_any_permission(
        db: Session,
        user_id: int,
        permission_codes: List[str],
        user: Optional[User] = None,
        tenant_id: Optional[int] = None
    ) -> bool:
        """
        检查用户是否有任一权限（支持多租户隔离）

        Args:
            db: 数据库会话
            user_id: 用户ID
            permission_codes: 权限编码列表
            user: 用户对象（可选）
            tenant_id: 租户ID（可选）

        Returns:
            是否有任一权限
        """
        if user and user.is_superuser:
            return True

        effective_tenant_id = tenant_id or (user.tenant_id if user else None)
        permissions = PermissionService.get_user_permissions(db, user_id, effective_tenant_id)
        return any(code in permissions for code in permission_codes)
    
    @staticmethod
    def check_all_permissions(
        db: Session,
        user_id: int,
        permission_codes: List[str],
        user: Optional[User] = None,
        tenant_id: Optional[int] = None
    ) -> bool:
        """
        检查用户是否有所有权限（支持多租户隔离）

        Args:
            db: 数据库会话
            user_id: 用户ID
            permission_codes: 权限编码列表
            user: 用户对象（可选）
            tenant_id: 租户ID（可选）

        Returns:
            是否有所有权限
        """
        if user and user.is_superuser:
            return True

        effective_tenant_id = tenant_id or (user.tenant_id if user else None)
        permissions = PermissionService.get_user_permissions(db, user_id, effective_tenant_id)
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
                MenuPermission.is_active,
                MenuPermission.is_visible,
                MenuPermission.parent_id is None
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
            RoleMenu.is_active
        ).all()
        
        for rm in role_menus:
            menu_ids.add(rm.menu_id)
        
        if not menu_ids:
            return []
        
        # 构建菜单树
        def build_menu_tree(parent_id: Optional[int] = None) -> List[Dict[str, Any]]:
            menus = db.query(MenuPermission).filter(
                MenuPermission.id.in_(menu_ids),
                MenuPermission.is_active,
                MenuPermission.is_visible,
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
                RoleDataScope.is_active
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
        # 获取租户ID
        tenant_id = user.tenant_id if user else None

        return {
            "permissions": PermissionService.get_user_permissions(db, user_id, tenant_id),
            "menus": PermissionService.get_user_menus(db, user_id, user),
            "dataScopes": PermissionService.get_user_data_scopes(db, user_id),
        }


# ============================================================
# 兼容层：保持与旧系统的兼容性
# ============================================================

def check_permission_compat(user: User, permission_code: str, db: Session) -> bool:
    """
    兼容层：检查权限（保持与旧代码兼容，自动获取租户ID）

    Args:
        user: 用户对象
        permission_code: 权限编码
        db: 数据库会话

    Returns:
        是否有权限
    """
    tenant_id = getattr(user, "tenant_id", None)
    return PermissionService.check_permission(db, user.id, permission_code, user, tenant_id)

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

    # 检查模块的 read 权限（自动获取租户ID）
    tenant_id = getattr(user, "tenant_id", None)
    permission_code = f"{module}:read"
    return PermissionService.check_permission(db, user.id, permission_code, user, tenant_id)

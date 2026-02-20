# -*- coding: utf-8 -*-
"""
角色管理业务逻辑服务
"""

import logging
from typing import List, Optional, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy import or_, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.models.user import (
    ApiPermission,
    Role,
    RoleApiPermission,
    RoleTemplate,
    UserRole,
)

logger = logging.getLogger(__name__)

# 系统预置角色编码，禁止通过 API 创建同名角色（防止权限提升）
RESERVED_ROLE_CODES = {
    # 超级管理员相关
    "ADMIN", "admin", "SUPERUSER", "superuser", "ROOT", "root",
    "super_admin", "system_admin", "sysadmin", "administrator",
    "Administrator", "ADMINISTRATOR",
    # 高管角色
    "GM", "CFO", "CTO", "CEO", "COO", "SALES_DIR",
    "gm", "cfo", "cto", "ceo", "coo", "sales_dir",
    # 系统角色
    "SYSTEM", "system", "internal", "INTERNAL",
    # 租户管理员
    "TENANT_ADMIN", "tenant_admin", "TenantAdmin",
    # 其他敏感角色
    "SECURITY", "security", "AUDIT", "audit",
}


class RoleManagementService:
    """角色管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_role_by_id(self, role_id: int, tenant_id: Optional[int] = None) -> Role:
        """
        根据ID获取角色
        
        Args:
            role_id: 角色ID
            tenant_id: 租户ID（可选，用于验证）
            
        Returns:
            角色对象
            
        Raises:
            HTTPException: 角色不存在时抛出404
        """
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        return role

    def list_roles_by_tenant(
        self,
        tenant_id: Optional[int],
        page: int = 1,
        page_size: int = 10,
        keyword: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        获取角色列表（按租户隔离）
        
        Args:
            tenant_id: 租户ID
            page: 页码
            page_size: 每页数量
            keyword: 关键词搜索
            is_active: 是否启用
            
        Returns:
            包含角色列表和分页信息的字典
        """
        query = self.db.query(Role).filter(
            or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None))
        )

        if keyword:
            query = query.filter(
                or_(
                    Role.role_code.contains(keyword),
                    Role.role_name.contains(keyword),
                )
            )

        if is_active is not None:
            query = query.filter(Role.is_active == is_active)

        total = query.count()
        roles = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "items": [self._role_to_dict(r) for r in roles],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_permissions_list(
        self,
        module: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取权限列表
        
        Args:
            module: 模块筛选
            
        Returns:
            权限列表
        """
        # SQLite schema debug logging
        if (hasattr(self.db, "bind") and 
            self.db.bind is not None and 
            self.db.bind.dialect.name == "sqlite"):
            pragma_columns = self.db.execute(
                text("PRAGMA table_info(api_permissions)")
            ).fetchall()
            logger.warning(
                "api_permissions schema snapshot: %s",
                [row[1] for row in pragma_columns],
            )

        query = (
            self.db.query(
                ApiPermission.id.label("id"),
                ApiPermission.perm_code.label("perm_code"),
                ApiPermission.perm_name.label("perm_name"),
                ApiPermission.module.label("module"),
                ApiPermission.action.label("action"),
            )
            .filter(ApiPermission.is_active)
        )

        if module:
            query = query.filter(ApiPermission.module == module)

        try:
            permissions = query.order_by(
                ApiPermission.module, 
                ApiPermission.perm_code
            ).all()
        except OperationalError as exc:
            logger.error(
                "Failed to load ApiPermission records (falling back to empty list): %s",
                exc,
            )
            self.db.rollback()
            permissions = []

        return [
            {
                "id": p.id,
                "permission_code": p.perm_code,
                "permission_name": p.perm_name,
                "module": p.module,
                "action": p.action,
            }
            for p in permissions
        ]

    def get_role_templates(self) -> List[Dict[str, Any]]:
        """
        获取角色模板列表
        
        Returns:
            角色模板列表
        """
        templates = (
            self.db.query(RoleTemplate)
            .filter(RoleTemplate.is_active)
            .order_by(RoleTemplate.template_name)
            .all()
        )

        return [
            {
                "id": t.id,
                "role_code": t.template_code,
                "role_name": t.template_name,
                "description": t.description,
                "data_scope": t.data_scope,
                "permission_codes": t.permission_snapshot,
            }
            for t in templates
        ]

    def get_all_role_configs(self, tenant_id: Optional[int]) -> List[Dict[str, Any]]:
        """
        获取所有角色配置（按租户隔离）
        
        Args:
            tenant_id: 租户ID
            
        Returns:
            角色配置列表
        """
        roles = (
            self.db.query(Role)
            .filter(
                Role.is_active,
                or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None)),
            )
            .order_by(Role.sort_order)
            .all()
        )

        return [
            {
                "id": role.id,
                "role_code": role.role_code,
                "role_name": role.role_name,
                "data_scope": role.data_scope,
                "nav_groups": role.nav_groups,
                "ui_config": role.ui_config,
            }
            for role in roles
        ]

    def get_user_nav_groups(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户的导航组配置（合并所有角色的导航组）
        
        Args:
            user_id: 用户ID
            
        Returns:
            合并后的导航组列表
        """
        user_roles = self.db.query(UserRole).filter(
            UserRole.user_id == user_id
        ).all()
        role_ids = [ur.role_id for ur in user_roles]

        if not role_ids:
            return []

        roles = self.db.query(Role).filter(
            Role.id.in_(role_ids),
            Role.is_active
        ).all()

        # 合并导航组（去重）
        merged_nav_groups = []
        seen_labels = set()

        for role in roles:
            if role.nav_groups:
                for group in role.nav_groups:
                    label = group.get("label", "")
                    if label not in seen_labels:
                        merged_nav_groups.append(group)
                        seen_labels.add(label)

        return merged_nav_groups

    def create_role(
        self,
        role_code: str,
        role_name: str,
        tenant_id: Optional[int],
        description: Optional[str] = None,
        data_scope: str = "OWN",
    ) -> Role:
        """
        创建角色
        
        Args:
            role_code: 角色编码
            role_name: 角色名称
            tenant_id: 租户ID
            description: 描述
            data_scope: 数据范围
            
        Returns:
            创建的角色对象
            
        Raises:
            HTTPException: 角色编码为保留编码或已存在时抛出400
        """
        # 安全检查：禁止创建与系统预置角色同名的角色
        if (role_code in RESERVED_ROLE_CODES or 
            role_code.upper() in RESERVED_ROLE_CODES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"角色编码 {role_code} 为系统保留编码，不允许使用",
            )

        # 检查角色编码是否已存在
        existing = self.db.query(Role).filter(
            Role.role_code == role_code,
            or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None))
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"角色编码 {role_code} 已存在",
            )

        role = Role(
            tenant_id=tenant_id,
            role_code=role_code,
            role_name=role_name,
            description=description,
            data_scope=data_scope,
            is_active=True,
        )
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)

        return role

    def update_role(
        self,
        role_id: int,
        role_code: Optional[str] = None,
        role_name: Optional[str] = None,
        description: Optional[str] = None,
        data_scope: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Role:
        """
        更新角色
        
        Args:
            role_id: 角色ID
            role_code: 角色编码
            role_name: 角色名称
            description: 描述
            data_scope: 数据范围
            is_active: 是否启用
            
        Returns:
            更新后的角色对象
            
        Raises:
            HTTPException: 角色不存在或系统角色不允许修改编码时抛出
        """
        role = self.get_role_by_id(role_id)

        # 系统预置角色不允许修改编码
        if role.is_system and role_code and role_code != role.role_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统预置角色不允许修改编码"
            )

        if role_code is not None:
            role.role_code = role_code
        if role_name is not None:
            role.role_name = role_name
        if description is not None:
            role.description = description
        if data_scope is not None:
            role.data_scope = data_scope
        if is_active is not None:
            role.is_active = is_active

        self.db.commit()
        self.db.refresh(role)

        return role

    def delete_role(self, role_id: int) -> None:
        """
        删除角色
        
        Args:
            role_id: 角色ID
            
        Raises:
            HTTPException: 角色不存在、系统角色或有用户使用时抛出
        """
        role = self.get_role_by_id(role_id)

        if role.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统预置角色不允许删除"
            )

        # 检查是否有用户使用此角色
        user_count = self.db.query(UserRole).filter(
            UserRole.role_id == role_id
        ).count()
        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"该角色下有 {user_count} 个用户，无法删除",
            )

        self.db.delete(role)
        self.db.commit()

    def update_role_permissions(
        self,
        role_id: int,
        permission_ids: List[int],
        tenant_id: Optional[int] = None,
    ) -> None:
        """
        更新角色权限
        
        Args:
            role_id: 角色ID
            permission_ids: 权限ID列表
            tenant_id: 租户ID（用于缓存清除）
            
        Raises:
            HTTPException: 角色不存在时抛出404
        """
        role = self.get_role_by_id(role_id)

        # 删除现有权限
        self.db.query(RoleApiPermission).filter(
            RoleApiPermission.role_id == role_id
        ).delete()

        # 添加新权限
        for perm_id in permission_ids:
            perm = self.db.query(ApiPermission).filter(
                ApiPermission.id == perm_id
            ).first()
            if perm:
                self.db.add(RoleApiPermission(
                    role_id=role_id,
                    permission_id=perm_id
                ))

        self.db.commit()

        # 清除权限缓存
        self._invalidate_permission_cache(role_id, tenant_id)

    def get_role_nav_groups(self, role_id: int) -> List[Dict[str, Any]]:
        """
        获取角色的导航组配置
        
        Args:
            role_id: 角色ID
            
        Returns:
            导航组列表
        """
        role = self.get_role_by_id(role_id)
        return role.nav_groups or []

    def update_role_nav_groups(
        self,
        role_id: int,
        nav_groups: List[Dict[str, Any]]
    ) -> None:
        """
        更新角色的导航组配置
        
        Args:
            role_id: 角色ID
            nav_groups: 导航组列表
        """
        role = self.get_role_by_id(role_id)
        role.nav_groups = nav_groups
        self.db.commit()

    # ============================================================
    # 角色层级管理
    # ============================================================

    def get_role_hierarchy_tree(
        self,
        tenant_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """
        获取角色层级树
        
        Args:
            tenant_id: 租户ID
            
        Returns:
            树形结构的角色列表
        """
        roles = (
            self.db.query(Role)
            .filter(
                Role.is_active,
                or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None)),
            )
            .order_by(Role.sort_order)
            .all()
        )

        # 构建树形结构
        role_map = {
            r.id: {
                "id": r.id,
                "role_code": r.role_code,
                "role_name": r.role_name,
                "parent_id": r.parent_id,
                "data_scope": r.data_scope,
                "children": [],
            }
            for r in roles
        }

        tree = []
        for role in roles:
            node = role_map[role.id]
            if role.parent_id and role.parent_id in role_map:
                role_map[role.parent_id]["children"].append(node)
            else:
                tree.append(node)

        return tree

    def update_role_parent(
        self,
        role_id: int,
        parent_id: Optional[int]
    ) -> Role:
        """
        更新角色的父角色
        
        Args:
            role_id: 角色ID
            parent_id: 父角色ID（None表示顶级角色）
            
        Returns:
            更新后的角色对象
            
        Raises:
            HTTPException: 角色不存在、系统角色或形成循环引用时抛出
        """
        role = self.get_role_by_id(role_id)

        if role.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统预置角色不允许修改层级"
            )

        # 检查父角色是否存在
        if parent_id is not None:
            parent_role = self.db.query(Role).filter(
                Role.id == parent_id
            ).first()
            if not parent_role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="父角色不存在"
                )

            # 检查是否形成循环引用
            if self._would_create_cycle(role_id, parent_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不能将子角色设为父角色（会形成循环引用）",
                )

        role.parent_id = parent_id
        self.db.commit()
        self.db.refresh(role)

        return role

    def get_role_ancestors(self, role_id: int) -> List[Dict[str, Any]]:
        """
        获取角色的所有祖先角色
        
        Args:
            role_id: 角色ID
            
        Returns:
            祖先角色列表
        """
        role = self.get_role_by_id(role_id)

        ancestors = []
        current = role

        while current.parent_id is not None:
            parent = self.db.query(Role).filter(
                Role.id == current.parent_id
            ).first()
            if parent:
                ancestors.append({
                    "id": parent.id,
                    "role_code": parent.role_code,
                    "role_name": parent.role_name,
                    "data_scope": parent.data_scope,
                })
                current = parent
            else:
                break

        return ancestors

    def get_role_descendants(self, role_id: int) -> List[Dict[str, Any]]:
        """
        获取角色的所有子孙角色
        
        Args:
            role_id: 角色ID
            
        Returns:
            子孙角色列表
        """
        role = self.get_role_by_id(role_id)

        descendants = []
        self._collect_descendants(role_id, descendants)

        return descendants

    # ============================================================
    # 私有辅助方法
    # ============================================================

    def _role_to_dict(self, role: Role) -> Dict[str, Any]:
        """将角色对象转换为字典"""
        return {
            "id": role.id,
            "role_code": role.role_code,
            "role_name": role.role_name,
            "description": role.description,
            "data_scope": role.data_scope,
            "is_active": role.is_active,
            "is_system": role.is_system,
            "parent_id": role.parent_id,
            "sort_order": role.sort_order,
            "tenant_id": role.tenant_id,
        }

    def _would_create_cycle(self, role_id: int, new_parent_id: int) -> bool:
        """检查设置新父角色是否会形成循环引用"""
        current_id = new_parent_id
        visited = {role_id}

        while current_id is not None:
            if current_id in visited:
                return True
            visited.add(current_id)

            parent_role = self.db.query(Role).filter(
                Role.id == current_id
            ).first()
            if parent_role:
                current_id = parent_role.parent_id
            else:
                break

        return False

    def _collect_descendants(self, parent_id: int, result: List[Dict[str, Any]]) -> None:
        """递归收集所有子孙角色"""
        children = (
            self.db.query(Role)
            .filter(Role.parent_id == parent_id, Role.is_active)
            .all()
        )
        for child in children:
            result.append({
                "id": child.id,
                "role_code": child.role_code,
                "role_name": child.role_name,
                "parent_id": child.parent_id,
                "data_scope": child.data_scope,
            })
            self._collect_descendants(child.id, result)

    def _invalidate_permission_cache(
        self,
        role_id: int,
        tenant_id: Optional[int]
    ) -> None:
        """清除角色权限缓存"""
        try:
            from app.services.permission_cache_service import get_permission_cache_service
            cache_service = get_permission_cache_service()
            cache_service.invalidate_role_and_users(role_id, tenant_id=tenant_id)
        except Exception as e:
            logger.warning(f"清除权限缓存失败: {e}")

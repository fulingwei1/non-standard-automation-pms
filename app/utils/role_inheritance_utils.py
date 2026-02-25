# -*- coding: utf-8 -*-
"""
角色继承工具模块

提供角色继承相关的工具函数：
1. 递归获取继承权限
2. 检测循环继承
3. 计算角色层级
4. 权限合并
5. 缓存优化
"""

import logging
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from app.models.user import ApiPermission, Role, RoleApiPermission

logger = logging.getLogger(__name__)


class RoleInheritanceUtils:
    """角色继承工具类"""

    # 权限缓存：{role_id: {permission_codes}}
    _permission_cache: Dict[int, Set[str]] = {}
    # 层级缓存：{role_id: level}
    _level_cache: Dict[int, int] = {}
    # 继承链缓存：{role_id: [parent_id, grandparent_id, ...]}
    _chain_cache: Dict[int, List[int]] = {}

    @staticmethod
    def clear_cache(role_id: Optional[int] = None):
        """
        清除缓存

        Args:
            role_id: 角色ID，如果为None则清除所有缓存
        """
        if role_id is None:
            RoleInheritanceUtils._permission_cache.clear()
            RoleInheritanceUtils._level_cache.clear()
            RoleInheritanceUtils._chain_cache.clear()
            logger.info("已清除所有角色继承缓存")
        else:
            RoleInheritanceUtils._permission_cache.pop(role_id, None)
            RoleInheritanceUtils._level_cache.pop(role_id, None)
            RoleInheritanceUtils._chain_cache.pop(role_id, None)
            logger.info(f"已清除角色 {role_id} 的继承缓存")

    @staticmethod
    def get_role_chain(db: Session, role_id: int) -> List[Role]:
        """
        获取角色的完整继承链（从子到父）

        Args:
            db: 数据库会话
            role_id: 角色ID

        Returns:
            角色列表，按继承顺序排列 [当前角色, 父角色, 祖父角色, ...]
        """
        # 检查缓存
        if role_id in RoleInheritanceUtils._chain_cache:
            cached_ids = RoleInheritanceUtils._chain_cache[role_id]
            roles = db.query(Role).filter(Role.id.in_(cached_ids)).all()
            # 按缓存顺序排序
            roles_dict = {r.id: r for r in roles}
            return [roles_dict[rid] for rid in cached_ids if rid in roles_dict]

        chain: List[Role] = []
        visited_ids: Set[int] = set()
        current_id = role_id

        while current_id:
            # 检测循环继承
            if current_id in visited_ids:
                logger.error(f"检测到循环继承：角色 {role_id} 的继承链中存在循环")
                break

            role = db.query(Role).filter(Role.id == current_id).first()
            if not role:
                break

            chain.append(role)
            visited_ids.add(current_id)

            # 如果不继承权限，停止追溯
            if not role.inherit_permissions:
                break

            current_id = role.parent_id

        # 缓存继承链ID
        RoleInheritanceUtils._chain_cache[role_id] = [r.id for r in chain]

        return chain

    @staticmethod
    def get_inherited_permissions(
        db: Session, role_id: int, tenant_id: Optional[int] = None
    ) -> Set[str]:
        """
        获取角色的所有权限（包含继承的权限）

        权限合并策略：
        - 子角色权限 = 自身权限 + 父角色权限（如果 inherit_permissions=True）
        - 递归向上合并，直到 inherit_permissions=False 或到达根角色

        Args:
            db: 数据库会话
            role_id: 角色ID
            tenant_id: 租户ID（用于多租户权限过滤）

        Returns:
            权限编码集合
        """
        # 检查缓存
        cache_key = f"{role_id}_{tenant_id}" if tenant_id else str(role_id)
        if role_id in RoleInheritanceUtils._permission_cache:
            cached = RoleInheritanceUtils._permission_cache[role_id]
            logger.debug(f"角色 {role_id} 权限缓存命中，共 {len(cached)} 个权限")
            return cached.copy()

        permissions: Set[str] = set()

        try:
            # 获取继承链
            chain = RoleInheritanceUtils.get_role_chain(db, role_id)

            # 从每个角色获取权限（从父到子，子角色权限会覆盖）
            for role in reversed(chain):
                role_perms = (
                    db.query(ApiPermission.perm_code)
                    .join(
                        RoleApiPermission,
                        RoleApiPermission.permission_id == ApiPermission.id,
                    )
                    .filter(
                        RoleApiPermission.role_id == role.id,
                        ApiPermission.is_active == True,
                    )
                )

                # 多租户权限过滤
                if tenant_id is not None:
                    role_perms = role_perms.filter(
                        (ApiPermission.tenant_id.is_(None))
                        | (ApiPermission.tenant_id == tenant_id)
                    )

                for (perm_code,) in role_perms.all():
                    if perm_code:
                        permissions.add(perm_code)

            # 缓存结果
            RoleInheritanceUtils._permission_cache[role_id] = permissions.copy()
            logger.info(
                f"角色 {role_id} 获取到 {len(permissions)} 个权限（包含继承）"
            )

        except Exception as e:
            logger.error(f"获取角色 {role_id} 继承权限失败: {e}")

        return permissions

    @staticmethod
    def calculate_role_level(db: Session, role_id: int) -> int:
        """
        计算角色在继承树中的层级

        Args:
            db: 数据库会话
            role_id: 角色ID

        Returns:
            层级数（0=根角色，1=第一级子角色，以此类推）
        """
        # 检查缓存
        if role_id in RoleInheritanceUtils._level_cache:
            return RoleInheritanceUtils._level_cache[role_id]

        chain = RoleInheritanceUtils.get_role_chain(db, role_id)
        level = len(chain) - 1  # 链长度-1就是层级

        # 缓存结果
        RoleInheritanceUtils._level_cache[role_id] = level

        return level

    @staticmethod
    def detect_circular_inheritance(db: Session, role_id: int, new_parent_id: int) -> bool:
        """
        检测设置父角色是否会导致循环继承

        Args:
            db: 数据库会话
            role_id: 当前角色ID
            new_parent_id: 拟设置的父角色ID

        Returns:
            True=会导致循环，False=安全
        """
        if role_id == new_parent_id:
            return True

        # 检查新父角色的继承链中是否包含当前角色
        parent_chain = RoleInheritanceUtils.get_role_chain(db, new_parent_id)
        parent_chain_ids = {r.id for r in parent_chain}

        return role_id in parent_chain_ids

    @staticmethod
    def get_role_tree_data(db: Session, tenant_id: Optional[int] = None) -> List[Dict]:
        """
        获取角色树数据（用于前端可视化）

        Args:
            db: 数据库会话
            tenant_id: 租户ID（用于多租户过滤）

        Returns:
            角色树数据列表
        """
        # 查询所有活跃角色
        query = db.query(Role).filter(Role.is_active == True)

        if tenant_id is not None:
            query = query.filter(
                (Role.tenant_id.is_(None)) | (Role.tenant_id == tenant_id)
            )

        roles = query.all()

        # 构建角色字典
        role_dict = {r.id: r for r in roles}

        def build_tree_node(role: Role) -> Dict:
            """构建树节点"""
            # 计算权限数量
            perm_count = (
                db.query(RoleApiPermission)
                .filter(RoleApiPermission.role_id == role.id)
                .count()
            )

            # 获取继承权限数量
            inherited_perms = RoleInheritanceUtils.get_inherited_permissions(
                db, role.id, tenant_id
            )

            node = {
                "id": role.id,
                "code": role.role_code,
                "name": role.role_name,
                "description": role.description,
                "level": RoleInheritanceUtils.calculate_role_level(db, role.id),
                "parent_id": role.parent_id,
                "inherit_permissions": role.inherit_permissions,
                "is_system": role.is_system,
                "own_permissions": perm_count,
                "total_permissions": len(inherited_perms),
                "children": [],
            }

            # 递归构建子节点
            children = [r for r in roles if r.parent_id == role.id]
            for child in children:
                node["children"].append(build_tree_node(child))

            return node

        # 构建根节点列表（parent_id 为 None 的角色）
        root_roles = [r for r in roles if r.parent_id is None]
        tree = [build_tree_node(r) for r in root_roles]

        return tree

    @staticmethod
    def merge_role_permissions(
        db: Session, role_ids: List[int], tenant_id: Optional[int] = None
    ) -> Set[str]:
        """
        合并多个角色的权限（用于用户拥有多个角色的情况）

        Args:
            db: 数据库会话
            role_ids: 角色ID列表
            tenant_id: 租户ID

        Returns:
            合并后的权限集合
        """
        merged_permissions: Set[str] = set()

        for role_id in role_ids:
            perms = RoleInheritanceUtils.get_inherited_permissions(
                db, role_id, tenant_id
            )
            merged_permissions.update(perms)

        logger.info(f"合并 {len(role_ids)} 个角色的权限，共 {len(merged_permissions)} 个")
        return merged_permissions

    @staticmethod
    def get_inheritance_statistics(db: Session) -> Dict:
        """
        获取角色继承统计信息

        Returns:
            统计信息字典
        """
        total_roles = db.query(Role).filter(Role.is_active == True).count()
        root_roles = (
            db.query(Role)
            .filter(Role.is_active == True, Role.parent_id.is_(None))
            .count()
        )
        inherited_roles = (
            db.query(Role)
            .filter(
                Role.is_active == True,
                Role.parent_id.isnot(None),
                Role.inherit_permissions == True,
            )
            .count()
        )

        # 最大层级深度
        max_depth = 0
        all_roles = db.query(Role).filter(Role.is_active == True).all()
        for role in all_roles:
            depth = RoleInheritanceUtils.calculate_role_level(db, role.id)
            max_depth = max(max_depth, depth)

        return {
            "total_roles": total_roles,
            "root_roles": root_roles,
            "inherited_roles": inherited_roles,
            "non_inherited_roles": total_roles - inherited_roles - root_roles,
            "max_depth": max_depth,
            "cache_size": {
                "permissions": len(RoleInheritanceUtils._permission_cache),
                "levels": len(RoleInheritanceUtils._level_cache),
                "chains": len(RoleInheritanceUtils._chain_cache),
            },
        }

    @staticmethod
    def validate_role_hierarchy(db: Session) -> Tuple[bool, List[str]]:
        """
        验证角色层级的完整性

        检查：
        1. 是否存在循环继承
        2. parent_id 是否有效
        3. 继承层级是否超过限制（默认最大4层）

        Returns:
            (是否有效, 错误信息列表)
        """
        errors: List[str] = []
        all_roles = db.query(Role).filter(Role.is_active == True).all()

        for role in all_roles:
            # 检查 parent_id 是否有效
            if role.parent_id:
                parent = db.query(Role).filter(Role.id == role.parent_id).first()
                if not parent:
                    errors.append(
                        f"角色 {role.role_code} (ID:{role.id}) 的父角色 ID {role.parent_id} 不存在"
                    )
                    continue

                # 检查循环继承
                chain = RoleInheritanceUtils.get_role_chain(db, role.id)
                chain_ids = [r.id for r in chain]
                if len(chain_ids) != len(set(chain_ids)):
                    errors.append(
                        f"角色 {role.role_code} (ID:{role.id}) 存在循环继承"
                    )

                # 检查层级深度
                level = RoleInheritanceUtils.calculate_role_level(db, role.id)
                if level > 3:  # 最大支持4层（0-3）
                    errors.append(
                        f"角色 {role.role_code} (ID:{role.id}) 的继承层级过深 (Level {level})"
                    )

        is_valid = len(errors) == 0
        return is_valid, errors

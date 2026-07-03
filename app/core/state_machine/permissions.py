# -*- coding: utf-8 -*-
"""
状态机权限验证

提供统一的权限检查机制，支持：
- 简单权限声明
- 角色检查
- 灵活的用户对象适配
"""

from typing import Any, Optional, Tuple

from app.core.state_machine.exceptions import PermissionDeniedError  # noqa: F401 - re-exported


class StateMachinePermissionChecker:
    """
    状态机权限检查器

    提供混合权限验证方案：
    1. 简单权限声明（required_permission）
    2. 角色检查（required_role）
    3. 复杂验证器（validator函数）

    使用方式：
        checker = StateMachinePermissionChecker()
        has_perm, reason = checker.check_permission(
            current_user,
            required_permission="ecn:approve",
            required_role="PROJECT_MANAGER"
        )
    """

    @staticmethod
    def check_permission(
        current_user: Any,
        required_permission: Optional[str] = None,
        required_role: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        检查权限

        验证逻辑：
        1. 如果没有权限要求，直接通过
        2. 如果需要权限但未提供用户，拒绝
        3. 检查用户是否有所需权限
        4. 检查用户是否有所需角色

        Args:
            current_user: 当前用户对象（应有 has_permission 或 has_role 方法）
            required_permission: 所需权限字符串（如 "ecn:approve"）
            required_role: 所需角色字符串（如 "PROJECT_MANAGER"）

        Returns:
            (是否有权限, 失败原因)

        示例:
            # 无权限要求
            has_perm, _ = check_permission(user)  # True

            # 需要权限
            has_perm, reason = check_permission(
                user,
                required_permission="issue:assign"
            )

            # 需要角色
            has_perm, reason = check_permission(
                user,
                required_role="PROJECT_MANAGER"
            )
        """
        # 无权限要求，直接通过
        if not required_permission and not required_role:
            return True, ""

        # 需要权限但未提供用户
        if not current_user:
            return False, "未提供操作人信息"

        # 系统/租户管理员在 API 权限层已被视为全权限用户；状态机内部也应保持一致。
        if StateMachinePermissionChecker._is_admin_user(current_user):
            return True, ""

        # 检查权限
        if required_permission:
            perm_valid, perm_reason = StateMachinePermissionChecker._check_permission_attr(
                current_user, required_permission
            )
            if not perm_valid:
                return False, perm_reason

        # 检查角色
        if required_role:
            role_valid, role_reason = StateMachinePermissionChecker._check_role_attr(
                current_user, required_role
            )
            if not role_valid:
                return False, role_reason

        return True, ""

    @staticmethod
    def _is_admin_user(current_user: Any) -> bool:
        """Best-effort admin shortcut that avoids treating bare Mock attrs as truthy."""
        if getattr(current_user, "is_superuser", None) is True:
            return True
        if getattr(current_user, "is_tenant_admin", None) is True:
            return True
        return False

    @staticmethod
    def _check_permission_attr(current_user: Any, required_permission: str) -> Tuple[bool, str]:
        """
        检查用户权限属性

        支持多种用户对象结构：
        1. has_permission(permission) 方法
        2. permissions 属性（列表或集合）
        """
        # 方法1：has_permission 函数
        if hasattr(current_user, "has_permission"):
            has_perm_attr = getattr(current_user, "has_permission")
            if callable(has_perm_attr):
                try:
                    if not has_perm_attr(required_permission):
                        return False, f"缺少权限: {required_permission}"
                    return True, ""
                except Exception as e:
                    return False, f"权限检查失败: {str(e)}"
            else:
                return False, "has_permission 应该是方法"

        # 方法2：permissions 属性
        permissions = getattr(current_user, "permissions", None)
        if isinstance(permissions, (list, set, tuple)):
            if required_permission not in permissions:
                return False, f"缺少权限: {required_permission}"
            return True, ""

        # 方法3：真实 User ORM 对象，复用现有 API 权限逻辑的无 DB 兜底。
        user_id = getattr(current_user, "id", None)
        username = getattr(current_user, "username", None)
        if isinstance(user_id, int) and isinstance(username, str):
            try:
                from app.core.auth import check_permission as auth_check_permission

                if auth_check_permission(current_user, required_permission):
                    return True, ""
                return False, f"缺少权限: {required_permission}"
            except Exception as e:
                return False, f"权限检查失败: {str(e)}"

        # 用户对象不支持权限检查
        return False, "用户对象不支持权限检查（缺少 has_permission 方法或 permissions 属性）"

    @staticmethod
    def _check_role_attr(current_user: Any, required_role: str) -> Tuple[bool, str]:
        """
        检查用户角色属性

        支持多种用户对象结构：
        1. has_role(role) 方法
        2. roles 属性（列表，元素可能是字符串或Role对象）
        """
        # 方法1：has_role 函数
        if hasattr(current_user, "has_role"):
            has_role_attr = getattr(current_user, "has_role")
            if callable(has_role_attr):
                try:
                    if not has_role_attr(required_role):
                        return False, f"缺少角色: {required_role}"
                    return True, ""
                except Exception as e:
                    return False, f"角色检查失败: {str(e)}"
            else:
                return False, "has_role 应该是方法"

        # 方法2：roles 属性
        roles = getattr(current_user, "roles", None)
        if roles is not None:
            if callable(getattr(roles, "all", None)):
                try:
                    roles = roles.all()
                except Exception:
                    roles = []

            if isinstance(roles, (list, set, tuple)):
                # 支持字符串列表、Role对象列表、UserRole.role 关系对象列表
                role_names = []
                for role_item in roles:
                    role = getattr(role_item, "role", role_item)
                    if isinstance(role, str):
                        role_names.append(role)
                    else:
                        for attr in ("name", "role_code", "role_name"):
                            value = getattr(role, attr, None)
                            if value:
                                role_names.append(value)

                if required_role not in role_names:
                    return False, f"缺少角色: {required_role}"
                return True, ""

        # 用户对象不支持角色检查
        return False, "用户对象不支持角色检查（缺少 has_role 方法或 roles 属性）"

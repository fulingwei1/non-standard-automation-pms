# -*- coding: utf-8 -*-
"""
毛利率数据权限服务

根据用户角色控制毛利率信息的可见范围：
- 销售 (SALES): 只看自己负责项目的毛利率
- 售前 (PRESALES): 看关联工单的项目毛利率
- 项目经理 (PM): 看自己管理项目的完整毛利率
- 财务 (FINANCE): 看所有项目毛利率
- 管理层 (MANAGEMENT): 看所有项目毛利率
- 系统管理员: 看所有项目毛利率
"""

import logging
from typing import List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.user import User
from app.core.auth import is_superuser, is_system_admin

logger = logging.getLogger(__name__)

# 角色编码常量
ROLE_SALES = "SALES"
ROLE_PRESALES = "PRESALES"
ROLE_PM = "PM"
ROLE_FINANCE = "FINANCE"
ROLE_MANAGEMENT = "MANAGEMENT"
ROLE_ADMIN = "ADMIN"

# 可以查看所有项目毛利率的角色
FULL_ACCESS_ROLES = {ROLE_FINANCE, ROLE_MANAGEMENT, ROLE_ADMIN}


class MarginPermissionService:
    """毛利率数据权限服务"""

    @staticmethod
    def get_user_roles(user: User) -> Set[str]:
        """
        获取用户的角色编码集合

        Args:
            user: 用户对象

        Returns:
            角色编码集合
        """
        roles = set()
        user_roles = getattr(user, "roles", None)

        if not user_roles:
            return roles

        # 处理动态关系
        if hasattr(user_roles, "all"):
            user_roles = user_roles.all()

        for user_role in user_roles or []:
            role = getattr(user_role, "role", user_role)
            role_code = getattr(role, "role_code", None)
            if role_code:
                roles.add(role_code)

        return roles

    @staticmethod
    def can_view_all_margins(user: User) -> bool:
        """
        判断用户是否可以查看所有项目的毛利率

        Args:
            user: 用户对象

        Returns:
            是否有完整访问权限
        """
        # 超级管理员和系统管理员可以查看所有
        if is_superuser(user) or is_system_admin(user):
            return True

        # 检查是否有完整访问权限的角色
        user_roles = MarginPermissionService.get_user_roles(user)
        return bool(user_roles & FULL_ACCESS_ROLES)

    @staticmethod
    def get_accessible_project_ids(
        user: User,
        db: Session,
        project_ids: Optional[List[int]] = None
    ) -> List[int]:
        """
        获取用户可以访问毛利率数据的项目ID列表

        Args:
            user: 用户对象
            db: 数据库会话
            project_ids: 可选的项目ID过滤列表

        Returns:
            可访问的项目ID列表
        """
        # 完整访问权限
        if MarginPermissionService.can_view_all_margins(user):
            if project_ids:
                return project_ids
            # 返回所有项目ID
            result = db.execute(text("SELECT id FROM projects WHERE is_deleted = 0"))
            return [row[0] for row in result.fetchall()]

        user_roles = MarginPermissionService.get_user_roles(user)
        accessible_ids = set()

        # 销售：查看自己负责的项目（sales_rep_id = user.id）
        if ROLE_SALES in user_roles:
            sql = """
                SELECT id FROM projects
                WHERE sales_rep_id = :user_id AND is_deleted = 0
            """
            result = db.execute(text(sql), {"user_id": user.id})
            accessible_ids.update(row[0] for row in result.fetchall())

        # 售前：查看关联工单的项目
        if ROLE_PRESALES in user_roles:
            sql = """
                SELECT DISTINCT p.id
                FROM projects p
                JOIN presale_support_ticket t ON t.project_id = p.id
                WHERE (t.applicant_id = :user_id OR t.assignee_id = :user_id)
                AND p.is_deleted = 0
            """
            result = db.execute(text(sql), {"user_id": user.id})
            accessible_ids.update(row[0] for row in result.fetchall())

            # 也可以通过投标方案关联的项目
            sql = """
                SELECT DISTINCT s.project_id
                FROM presale_solution s
                WHERE s.author_id = :user_id AND s.project_id IS NOT NULL
            """
            result = db.execute(text(sql), {"user_id": user.id})
            accessible_ids.update(row[0] for row in result.fetchall() if row[0])

        # PM：查看自己管理的项目（pm_id = user.id）
        if ROLE_PM in user_roles:
            sql = """
                SELECT id FROM projects
                WHERE pm_id = :user_id AND is_deleted = 0
            """
            result = db.execute(text(sql), {"user_id": user.id})
            accessible_ids.update(row[0] for row in result.fetchall())

        # 如果提供了过滤列表，取交集
        if project_ids:
            accessible_ids = accessible_ids & set(project_ids)

        return list(accessible_ids)

    @staticmethod
    def can_view_project_margin(
        user: User,
        project_id: int,
        db: Session
    ) -> bool:
        """
        判断用户是否可以查看指定项目的毛利率

        Args:
            user: 用户对象
            project_id: 项目ID
            db: 数据库会话

        Returns:
            是否有访问权限
        """
        # 完整访问权限
        if MarginPermissionService.can_view_all_margins(user):
            return True

        # 检查是否在可访问列表中
        accessible_ids = MarginPermissionService.get_accessible_project_ids(
            user, db, [project_id]
        )
        return project_id in accessible_ids

    @staticmethod
    def get_margin_visibility_level(user: User) -> str:
        """
        获取用户的毛利率可见级别

        Returns:
            - "full": 完整访问（可看所有项目）
            - "own": 只能看自己相关的项目
            - "none": 无访问权限
        """
        if MarginPermissionService.can_view_all_margins(user):
            return "full"

        user_roles = MarginPermissionService.get_user_roles(user)
        if user_roles & {ROLE_SALES, ROLE_PRESALES, ROLE_PM}:
            return "own"

        return "none"

    @staticmethod
    def filter_margin_data(
        user: User,
        margin_data: dict,
        db: Session
    ) -> dict:
        """
        根据权限过滤毛利率数据

        对于没有完整访问权限的用户，可能需要隐藏某些敏感信息

        Args:
            user: 用户对象
            margin_data: 原始毛利率数据
            db: 数据库会话

        Returns:
            过滤后的毛利率数据
        """
        # 完整访问权限返回所有数据
        if MarginPermissionService.can_view_all_margins(user):
            return margin_data

        # 对于销售和售前，可能需要隐藏某些敏感信息
        # 目前返回相同数据，但可以根据业务需求调整
        return margin_data


# 便捷函数
def can_view_project_margin(user: User, project_id: int, db: Session) -> bool:
    """检查用户是否可以查看项目毛利率"""
    return MarginPermissionService.can_view_project_margin(user, project_id, db)


def get_accessible_project_ids(
    user: User,
    db: Session,
    project_ids: Optional[List[int]] = None
) -> List[int]:
    """获取用户可以访问的项目ID列表"""
    return MarginPermissionService.get_accessible_project_ids(user, db, project_ids)


def get_margin_visibility_level(user: User) -> str:
    """获取用户的毛利率可见级别"""
    return MarginPermissionService.get_margin_visibility_level(user)

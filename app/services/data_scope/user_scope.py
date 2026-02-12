# -*- coding: utf-8 -*-
"""
用户权限范围相关方法
获取用户的数据权限范围和关联数据
"""

from typing import Set

from sqlalchemy.orm import Session

from app.models.enums import DataScopeEnum
from app.models.project import ProjectMember
from app.models.user import User


class UserScopeService:
    """用户权限范围服务"""

    @staticmethod
    def get_user_data_scope(db: Session, user: User) -> str:
        """
        获取用户的数据权限范围（取最宽松的）

        优先级：ALL > DEPT > SUBORDINATE > PROJECT > OWN
        """
        if user.is_superuser:
            return DataScopeEnum.ALL.value

        # 获取用户所有角色的数据权限范围
        scopes = set()
        for user_role in user.roles:
            role = user_role.role
            if role and role.is_active:
                scopes.add(role.data_scope)

        # 返回最宽松的权限
        if DataScopeEnum.ALL.value in scopes:
            return DataScopeEnum.ALL.value
        elif DataScopeEnum.DEPT.value in scopes:
            return DataScopeEnum.DEPT.value
        elif DataScopeEnum.SUBORDINATE.value in scopes:
            return DataScopeEnum.SUBORDINATE.value
        elif DataScopeEnum.PROJECT.value in scopes:
            return DataScopeEnum.PROJECT.value
        else:
            return DataScopeEnum.OWN.value

    @staticmethod
    def get_user_project_ids(db: Session, user_id: int) -> Set[int]:
        """获取用户参与的项目ID列表"""
        members = (
            db.query(ProjectMember.project_id)
            .filter(
                ProjectMember.user_id == user_id,
                ProjectMember.is_active
            )
            .all()
        )
        return {m[0] for m in members}

    @staticmethod
    def get_subordinate_ids(db: Session, user_id: int) -> Set[int]:
        """获取用户的直接下属ID列表"""
        subordinates = (
            db.query(User.id)
            .filter(
                User.reporting_to == user_id,
                User.is_active
            )
            .all()
        )
        return {s[0] for s in subordinates}

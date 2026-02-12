# -*- coding: utf-8 -*-
"""
问题过滤相关方法
根据用户数据权限范围过滤问题(Issue)查询
"""

from typing import List

from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from app.models.enums import DataScopeEnum
from app.models.issue import Issue
from app.models.organization import Department
from app.models.project import Project
from app.models.user import User

from .user_scope import UserScopeService


class IssueFilterService:
    """问题过滤服务"""

    @staticmethod
    def filter_issues_by_scope(
        db: Session,
        query: Query,
        user: User,
    ) -> Query:
        """
        根据用户数据权限范围过滤问题(Issue)查询。

        规则（尽量符合"只看与自己相关"的默认预期）：
        - ALL：全部可见
        - OWN：本人参与（提出/处理/责任/解决/验证）
        - SUBORDINATE：本人 + 直接下属参与
        - DEPT：同部门用户参与 + 本部门项目的问题
        - PROJECT：参与项目的问题 + 本人参与的问题
        """
        if user.is_superuser:
            return query

        data_scope = UserScopeService.get_user_data_scope(db, user)

        participant_columns = [
            Issue.reporter_id,
            Issue.assignee_id,
            Issue.responsible_engineer_id,
            Issue.resolved_by,
            Issue.verified_by,
        ]

        def _participants_condition(user_ids: List[int]):
            user_ids = [uid for uid in user_ids if uid is not None]
            if not user_ids:
                return False
            return or_(*[col.in_(user_ids) for col in participant_columns])

        if data_scope == DataScopeEnum.ALL.value:
            return query

        if data_scope == DataScopeEnum.OWN.value:
            return query.filter(_participants_condition([user.id]))

        if data_scope == DataScopeEnum.SUBORDINATE.value:
            allowed_ids = UserScopeService.get_subordinate_ids(db, user.id) | {user.id}
            return query.filter(_participants_condition(list(allowed_ids)))

        if data_scope == DataScopeEnum.PROJECT.value:
            user_project_ids = UserScopeService.get_user_project_ids(db, user.id)
            conditions = [_participants_condition([user.id])]
            if user_project_ids:
                conditions.append(Issue.project_id.in_(list(user_project_ids)))
            return query.filter(or_(*conditions))

        if data_scope == DataScopeEnum.DEPT.value:
            # 1) 同部门用户参与的问题
            dept_user_ids: List[int] = []
            if user.department:
                dept_user_rows = (
                    db.query(User.id)
                    .filter(User.department == user.department, User.is_active)
                    .all()
                )
                dept_user_ids = [row[0] for row in dept_user_rows]

            conditions = []
            if dept_user_ids:
                conditions.append(_participants_condition(dept_user_ids))
            else:
                # 没有部门信息则降级 OWN
                conditions.append(_participants_condition([user.id]))

            # 2) 本部门项目的问题（即使参与人跨部门，经理也应可见）
            import logging
            logger = logging.getLogger(__name__)
            try:
                if user.department:
                    dept = (
                        db.query(Department)
                        .filter(Department.dept_name == user.department)
                        .first()
                    )
                    if dept:
                        dept_project_rows = (
                            db.query(Project.id).filter(Project.dept_id == dept.id).all()
                        )
                        dept_project_ids = [row[0] for row in dept_project_rows]
                        if dept_project_ids:
                            conditions.append(Issue.project_id.in_(dept_project_ids))
            except Exception:
                # 部门表可能未初始化，忽略项目维度过滤
                logger.debug("部门表查询失败，已忽略项目维度过滤", exc_info=True)

            return query.filter(or_(*conditions))

        # 其他/未知范围：默认降级为 OWN
        return query.filter(_participants_condition([user.id]))

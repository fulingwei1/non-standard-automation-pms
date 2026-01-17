# -*- coding: utf-8 -*-
"""
数据权限服务
实现基于角色的数据权限过滤
"""

import logging
from typing import List, Optional, Set

from sqlalchemy import and_, or_
from sqlalchemy.orm import Query, Session

from app.models.enums import DataScopeEnum
from app.models.project import Project, ProjectMember
from app.models.user import Role, User

logger = logging.getLogger(__name__)


class DataScopeService:
    """数据权限范围服务"""

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
                ProjectMember.is_active == True
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
                User.is_active == True
            )
            .all()
        )
        return {s[0] for s in subordinates}

    @staticmethod
    def filter_projects_by_scope(
        db: Session,
        query: Query,
        user: User,
        project_ids: Optional[List[int]] = None
    ) -> Query:
        """
        根据用户数据权限范围过滤项目查询

        Args:
            db: 数据库会话
            query: 项目查询对象
            user: 当前用户
            project_ids: 可选的预过滤项目ID列表

        Returns:
            过滤后的查询对象
        """
        if user.is_superuser:
            return query

        data_scope = DataScopeService.get_user_data_scope(db, user)

        if data_scope == DataScopeEnum.ALL.value:
            # 全部可见，无需过滤
            return query
        elif data_scope == DataScopeEnum.DEPT.value:
            # 同部门可见
            # 通过部门名称匹配部门ID
            from app.models.organization import Department
            dept_name = user.department
            if dept_name:
                # 通过部门名称查找部门ID
                dept = db.query(Department).filter(Department.dept_name == dept_name).first()
                if dept:
                    # 查询同部门的项目
                    dept_ids = [dept.id]
                    # 可以扩展为包含子部门
                    return query.filter(Project.dept_id.in_(dept_ids))

            # 如果没有部门信息，降级为OWN
            return DataScopeService._filter_own_projects(query, user)
        elif data_scope == DataScopeEnum.SUBORDINATE.value:
            # 下属项目可见：自己的项目 + 直接下属创建/负责的项目
            subordinate_ids = DataScopeService.get_subordinate_ids(db, user.id)
            # 包括自己和所有下属
            allowed_user_ids = subordinate_ids | {user.id}
            return query.filter(
                or_(
                    Project.created_by.in_(allowed_user_ids),
                    Project.pm_id.in_(allowed_user_ids)
                )
            )
        elif data_scope == DataScopeEnum.PROJECT.value:
            # 参与项目可见
            user_project_ids = DataScopeService.get_user_project_ids(db, user.id)
            if project_ids:
                # 取交集
                allowed_ids = set(project_ids) & user_project_ids
            else:
                allowed_ids = user_project_ids

            if allowed_ids:
                return query.filter(Project.id.in_(allowed_ids))
            else:
                # 没有参与任何项目，返回空结果
                return query.filter(Project.id == -1)  # 永远不匹配的条件
        else:  # OWN
            # 自己创建/负责的项目可见
            return DataScopeService._filter_own_projects(query, user)

    @staticmethod
    def filter_issues_by_scope(
        db: Session,
        query: Query,
        user: User,
    ) -> Query:
        """
        根据用户数据权限范围过滤问题(Issue)查询。

        规则（尽量符合“只看与自己相关”的默认预期）：
        - ALL：全部可见
        - OWN：本人参与（提出/处理/责任/解决/验证）
        - SUBORDINATE：本人 + 直接下属参与
        - DEPT：同部门用户参与 + 本部门项目的问题
        - PROJECT：参与项目的问题 + 本人参与的问题
        """
        if user.is_superuser:
            return query

        from app.models.issue import Issue

        data_scope = DataScopeService.get_user_data_scope(db, user)

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
            allowed_ids = DataScopeService.get_subordinate_ids(db, user.id) | {user.id}
            return query.filter(_participants_condition(list(allowed_ids)))

        if data_scope == DataScopeEnum.PROJECT.value:
            user_project_ids = DataScopeService.get_user_project_ids(db, user.id)
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
                    .filter(User.department == user.department, User.is_active == True)
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
            try:
                from app.models.organization import Department

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

    @staticmethod
    def _filter_own_projects(query: Query, user: User) -> Query:
        """过滤自己创建或负责的项目"""
        return query.filter(
            or_(
                Project.created_by == user.id,
                Project.pm_id == user.id
            )
        )

    @staticmethod
    def check_project_access(
        db: Session,
        user: User,
        project_id: int
    ) -> bool:
        """
        检查用户是否有权限访问指定项目

        Returns:
            True: 有权限
            False: 无权限
        """
        if user.is_superuser:
            return True

        data_scope = DataScopeService.get_user_data_scope(db, user)

        if data_scope == DataScopeEnum.ALL.value:
            return True
        elif data_scope == DataScopeEnum.DEPT.value:
            # 检查项目是否属于同部门
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return False
            if not user.department:
                return False
            # 通过部门名称查找部门ID
            from app.models.organization import Department
            dept = db.query(Department).filter(Department.dept_name == user.department).first()
            if not dept:
                return False
            return project.dept_id == dept.id
        elif data_scope == DataScopeEnum.SUBORDINATE.value:
            # 检查项目是否是自己或下属的
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return False
            subordinate_ids = DataScopeService.get_subordinate_ids(db, user.id)
            allowed_user_ids = subordinate_ids | {user.id}
            return (
                project.created_by in allowed_user_ids or
                project.pm_id in allowed_user_ids
            )
        elif data_scope == DataScopeEnum.PROJECT.value:
            # 检查是否是项目成员
            member = (
                db.query(ProjectMember)
                .filter(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user.id,
                    ProjectMember.is_active == True
                )
                .first()
            )
            return member is not None
        else:  # OWN
            # 检查是否是创建人或项目经理
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return False
            return (
                project.created_by == user.id or
                project.pm_id == user.id
            )

    @staticmethod
    def check_customer_access(
        db: Session,
        user: User,
        customer_id: int
    ) -> bool:
        """
        检查用户是否有权限访问指定客户的数据

        Returns:
            True: 有权限
            False: 无权限
        """
        if user.is_superuser:
            return True

        data_scope = DataScopeService.get_user_data_scope(db, user)

        if data_scope == DataScopeEnum.ALL.value:
            return True
        elif data_scope == DataScopeEnum.CUSTOMER.value:
            # 客户门户：只能看自己客户的项目
            # 这里需要根据业务逻辑实现，暂时返回True
            return True
        else:
            # 其他范围：通过项目间接访问客户
            # 检查是否有该客户的项目且用户有权限
            user_project_ids = DataScopeService.get_user_project_ids(db, user.id)
            if not user_project_ids:
                return False

            projects = (
                db.query(Project.customer_id)
                .filter(
                    Project.id.in_(user_project_ids),
                    Project.customer_id == customer_id
                )
                .first()
            )
            return projects is not None

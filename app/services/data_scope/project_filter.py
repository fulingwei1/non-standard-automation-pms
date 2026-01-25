# -*- coding: utf-8 -*-
"""
项目过滤相关方法
根据用户数据权限范围过滤项目查询
"""

from typing import List, Optional, Set

from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from app.models.enums import DataScopeEnum
from app.models.organization import Department
from app.models.project import Project
from app.models.user import User

from .user_scope import UserScopeService


class ProjectFilterService:
    """项目过滤服务"""

    @staticmethod
    def get_accessible_project_ids(
        db: Session,
        user: User,
    ) -> Set[int]:
        """
        获取用户有权限访问的所有项目ID

        根据用户的数据权限范围（ALL/DEPT/SUBORDINATE/PROJECT/OWN）
        返回用户可以访问的项目ID集合。

        Args:
            db: 数据库会话
            user: 当前用户

        Returns:
            用户可访问的项目ID集合
        """
        # 超级管理员可以访问所有项目
        if user.is_superuser:
            all_projects = db.query(Project.id).filter(Project.is_active == True).all()
            return {p[0] for p in all_projects}

        data_scope = UserScopeService.get_user_data_scope(db, user)

        if data_scope == DataScopeEnum.ALL.value:
            # 全部可见
            all_projects = db.query(Project.id).filter(Project.is_active == True).all()
            return {p[0] for p in all_projects}

        elif data_scope == DataScopeEnum.DEPT.value:
            # 同部门可见
            project_ids = set()
            dept_name = user.department
            if dept_name:
                dept = db.query(Department).filter(
                    Department.dept_name == dept_name
                ).first()
                if dept:
                    dept_projects = db.query(Project.id).filter(
                        Project.dept_id == dept.id,
                        Project.is_active == True,
                    ).all()
                    project_ids = {p[0] for p in dept_projects}

            # 同时包含自己参与的项目
            user_project_ids = UserScopeService.get_user_project_ids(db, user.id)
            return project_ids | user_project_ids

        elif data_scope == DataScopeEnum.SUBORDINATE.value:
            # 下属项目可见：自己的项目 + 直接下属创建/负责的项目
            subordinate_ids = UserScopeService.get_subordinate_ids(db, user.id)
            allowed_user_ids = subordinate_ids | {user.id}

            sub_projects = db.query(Project.id).filter(
                or_(
                    Project.created_by.in_(allowed_user_ids),
                    Project.pm_id.in_(allowed_user_ids),
                ),
                Project.is_active == True,
            ).all()
            project_ids = {p[0] for p in sub_projects}

            # 同时包含自己参与的项目
            user_project_ids = UserScopeService.get_user_project_ids(db, user.id)
            return project_ids | user_project_ids

        elif data_scope == DataScopeEnum.PROJECT.value:
            # 参与项目可见
            return UserScopeService.get_user_project_ids(db, user.id)

        else:  # OWN
            # 自己创建/负责的项目 + 参与的项目
            own_projects = db.query(Project.id).filter(
                or_(
                    Project.created_by == user.id,
                    Project.pm_id == user.id,
                ),
                Project.is_active == True,
            ).all()
            project_ids = {p[0] for p in own_projects}

            # 同时包含自己参与的项目
            user_project_ids = UserScopeService.get_user_project_ids(db, user.id)
            return project_ids | user_project_ids

    @staticmethod
    def filter_related_by_project(
        db: Session,
        query: Query,
        user: User,
        project_id_column,
    ) -> Query:
        """
        根据用户数据权限过滤与项目关联的资源查询

        用于过滤 ProjectMember、ProjectMilestone、Timesheet 等
        通过 project_id 关联到项目的资源。

        Args:
            db: 数据库会话
            query: 查询对象
            user: 当前用户
            project_id_column: 资源表的 project_id 列（如 ProjectMember.project_id）

        Returns:
            过滤后的查询对象

        Example:
            query = db.query(ProjectMember)
            query = ProjectFilterService.filter_related_by_project(
                db, query, user, ProjectMember.project_id
            )
        """
        if user.is_superuser:
            return query

        accessible_ids = ProjectFilterService.get_accessible_project_ids(db, user)

        if accessible_ids:
            return query.filter(project_id_column.in_(accessible_ids))
        else:
            # 没有权限访问任何项目，返回空结果
            return query.filter(project_id_column == -1)

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

        data_scope = UserScopeService.get_user_data_scope(db, user)

        if data_scope == DataScopeEnum.ALL.value:
            # 全部可见，无需过滤
            return query
        elif data_scope == DataScopeEnum.DEPT.value:
            # 同部门可见
            # 通过部门名称匹配部门ID
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
            return ProjectFilterService._filter_own_projects(query, user)
        elif data_scope == DataScopeEnum.SUBORDINATE.value:
            # 下属项目可见：自己的项目 + 直接下属创建/负责的项目
            subordinate_ids = UserScopeService.get_subordinate_ids(db, user.id)
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
            user_project_ids = UserScopeService.get_user_project_ids(db, user.id)
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
            return ProjectFilterService._filter_own_projects(query, user)

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

        data_scope = UserScopeService.get_user_data_scope(db, user)

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
            dept = db.query(Department).filter(Department.dept_name == user.department).first()
            if not dept:
                return False
            return project.dept_id == dept.id
        elif data_scope == DataScopeEnum.SUBORDINATE.value:
            # 检查项目是否是自己或下属的
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return False
            subordinate_ids = UserScopeService.get_subordinate_ids(db, user.id)
            allowed_user_ids = subordinate_ids | {user.id}
            return (
                project.created_by in allowed_user_ids or
                project.pm_id in allowed_user_ids
            )
        elif data_scope == DataScopeEnum.PROJECT.value:
            # 检查是否是项目成员
            from app.models.project import ProjectMember
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

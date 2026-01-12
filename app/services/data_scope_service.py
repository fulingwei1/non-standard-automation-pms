# -*- coding: utf-8 -*-
"""
数据权限服务
实现基于角色的数据权限过滤
"""

from typing import List, Optional, Set
from sqlalchemy.orm import Session, Query
from sqlalchemy import or_, and_

from app.models.user import User, Role
from app.models.project import Project, ProjectMember
from app.models.enums import DataScopeEnum
from app.services.cache_service import DepartmentCache, UserProjectCache


class DataScopeService:
    """数据权限范围服务"""

    @staticmethod
    def get_user_data_scope(db: Session, user: User) -> str:
        """
        获取用户的数据权限范围（取最宽松的）
        
        优先级：ALL > DEPT > PROJECT > OWN
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
        elif DataScopeEnum.PROJECT.value in scopes:
            return DataScopeEnum.PROJECT.value
        else:
            return DataScopeEnum.OWN.value

    @staticmethod
    def get_user_project_ids(db: Session, user_id: int) -> Set[int]:
        """
        获取用户参与的项目ID列表（带缓存）
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            项目ID集合
        """
        # 先尝试从缓存获取
        cached_ids = UserProjectCache.get(user_id)
        if cached_ids is not None:
            return cached_ids
        
        # 缓存未命中，查询数据库
        from sqlalchemy import select
        
        stmt = (
            select(ProjectMember.project_id)
            .where(
                ProjectMember.user_id == user_id,
                ProjectMember.is_active == True
            )
        )
        result = db.execute(stmt)
        project_ids = {row[0] for row in result}
        
        # 存入缓存
        UserProjectCache.set(user_id, project_ids)
        
        return project_ids

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
            # 优化：使用部门ID缓存
            dept_name = user.department
            if dept_name:
                # 先从缓存获取部门ID
                dept_id = DepartmentCache.get(dept_name)
                if dept_id is None:
                    # 缓存未命中，查询数据库
                    from app.models.organization import Department
                    dept = db.query(Department.id).filter(
                        Department.dept_name == dept_name
                    ).first()
                    if dept:
                        dept_id = dept[0]
                        # 存入缓存
                        DepartmentCache.set(dept_name, dept_id)
                
                if dept_id:
                    # 查询同部门的项目
                    dept_ids = [dept_id]
                    # 可以扩展为包含子部门
                    return query.filter(Project.dept_id.in_(dept_ids))
            
            # 如果没有部门信息，降级为OWN
            return DataScopeService._filter_own_projects(query, user)
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


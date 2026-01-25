# -*- coding: utf-8 -*-
"""
权限检查辅助函数
提供便捷的权限检查工具
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User
from app.services.data_scope_service import DataScopeService


def check_project_access_or_raise(
    db: Session,
    user: User,
    project_id: int,
    error_message: Optional[str] = None
) -> Project:
    """
    检查项目访问权限，如果没有权限则抛出异常

    Args:
        db: 数据库会话
        user: 当前用户
        project_id: 项目ID
        error_message: 自定义错误消息

    Returns:
        Project对象（如果权限检查通过）

    Raises:
        HTTPException: 如果项目不存在或用户无权限
    """
    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    # 检查访问权限
    if not DataScopeService.check_project_access(db, user, project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_message or "您没有权限访问该项目"
        )

    return project


def filter_projects_by_scope(
    db: Session,
    query,
    user: User,
    project_ids: Optional[list] = None
):
    """
    根据用户数据权限范围过滤项目查询

    Args:
        db: 数据库会话
        query: SQLAlchemy查询对象
        user: 当前用户
        project_ids: 可选的预过滤项目ID列表

    Returns:
        过滤后的查询对象
    """
    return DataScopeService.filter_projects_by_scope(db, query, user, project_ids)


def get_accessible_project_ids(db: Session, user: User) -> set:
    """
    获取用户有权限访问的所有项目ID

    这是最常用的权限过滤方法，用于过滤与项目关联的资源。

    Args:
        db: 数据库会话
        user: 当前用户

    Returns:
        用户可访问的项目ID集合

    Example:
        project_ids = get_accessible_project_ids(db, current_user)
        query = query.filter(ProjectMember.project_id.in_(project_ids))
    """
    return DataScopeService.get_accessible_project_ids(db, user)


def filter_by_project_access(db: Session, query, user: User, project_id_column):
    """
    根据用户数据权限过滤与项目关联的资源查询

    用于过滤 ProjectMember、ProjectMilestone、Timesheet 等
    通过 project_id 关联到项目的资源。

    Args:
        db: 数据库会话
        query: 查询对象
        user: 当前用户
        project_id_column: 资源表的 project_id 列

    Returns:
        过滤后的查询对象

    Example:
        query = db.query(ProjectMember)
        query = filter_by_project_access(db, query, user, ProjectMember.project_id)
    """
    return DataScopeService.filter_related_by_project(db, query, user, project_id_column)




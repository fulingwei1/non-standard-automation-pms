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




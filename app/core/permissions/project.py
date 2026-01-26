# -*- coding: utf-8 -*-
"""
权限检查模块 - 项目权限
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user, get_db
from app.models.user import User


def check_project_access(project_id: int, current_user: User, db: Session) -> bool:
    """
    检查用户是否有权限访问指定项目

    Args:
        project_id: 项目ID
        current_user: 当前用户
        db: 数据库会话

    Returns:
        True: 有权限
        False: 无权限
    """
    from app.services.data_scope import DataScopeService

    return DataScopeService.check_project_access(db, current_user, project_id)


def require_project_access():
    """
    项目访问权限检查依赖（需要在路由中使用）

    使用方式：
        @router.get("/projects/{project_id}")
        def get_project(
            project_id: int,
            current_user: User = Depends(security.get_current_active_user),
            db: Session = Depends(deps.get_db),
            _: None = Depends(lambda p=project_id, u=current_user, d=db:
                security.check_project_access(p, u, d) or None)
        ):
    """

    def project_access_checker(
        project_id: int,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ):
        if not check_project_access(project_id, current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="您没有权限访问该项目"
            )
        return current_user

    return project_access_checker

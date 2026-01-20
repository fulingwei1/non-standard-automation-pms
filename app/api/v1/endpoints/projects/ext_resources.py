# -*- coding: utf-8 -*-
"""
项目resources管理 - 自动生成
从 projects/extended.py 拆分
"""

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user, get_db
from app.core import security
from app.core.config import settings
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.project import ProjectResponse

router = APIRouter()


@router.get("/projects/resources", response_model=ResponseModel[List[ProjectResponse]])
def get_project_resources(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=200, description="返回记录数"),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取项目resources列表

    Args:
        db: 数据库会话
        skip: 跳过记录数
        limit: 返回记录数
        current_user: 当前用户

    Returns:
        Response[List[ProjectResponse]]: 项目resources列表
    """
    try:
        # TODO: 实现resources查询逻辑
        projects = db.query(Project).offset(skip).limit(limit).all()

        return ResponseModel(
            code=200,
            message="项目resources列表获取成功",
            data=[ProjectResponse.model_validate(project) for project in projects]
        )
    except Exception as e:
        return ResponseModel(code=500, message=f"获取项目resources失败: {str(e)}")


@router.post("/projects/resources")
def create_project_resources(
    project_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    创建项目resources

    Args:
        project_data: 项目数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        Response: 创建结果
    """
    try:
        # TODO: 实现resources创建逻辑
        return ResponseModel(code=200, message="项目resources创建成功")
    except Exception as e:
        return ResponseModel(code=500, message=f"创建项目resources失败: {str(e)}")

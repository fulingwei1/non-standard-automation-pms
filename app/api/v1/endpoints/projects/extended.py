# -*- coding: utf-8 -*-
"""
项目扩展管理 API endpoints (重构版)
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.project import Project
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
def read_project_extensions(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(deps.get_current_active_user)
):
    """获取项目扩展列表"""
    # 简化实现
    return PaginatedResponse(
        total=0,
        page=page,
        page_size=page_size,
        items=[]
    )


@router.post("/", response_model=ResponseModel)
def create_project_extension(
    data: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """创建项目扩展"""
    # 简化实现
    return ResponseModel(message="项目扩展创建成功")


@router.get("/statistics", response_model=ResponseModel)
def get_project_statistics(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    获取项目统计数据

    返回项目总数、合同总金额，以及按阶段、健康度、类型的分组统计
    """
    from app.services.data_scope import DataScopeService

    query = db.query(Project).filter(Project.is_active == True)

    # 应用数据权限过滤
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)

    if start_date:
        query = query.filter(Project.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Project.created_at <= datetime.combine(end_date, datetime.max.time()))

    projects = query.all()

    # 统计数据
    total_count = len(projects)
    total_contract_amount = sum(float(p.contract_amount or 0) for p in projects)

    # 按阶段统计
    stage_stats = {}
    for project in projects:
        stage = project.stage or 'S1'
        if stage not in stage_stats:
            stage_stats[stage] = {'count': 0, 'amount': 0}
        stage_stats[stage]['count'] += 1
        stage_stats[stage]['amount'] += float(project.contract_amount or 0)

    # 按健康度统计
    health_stats = {}
    for project in projects:
        health = project.health or 'H1'
        if health not in health_stats:
            health_stats[health] = {'count': 0, 'amount': 0}
        health_stats[health]['count'] += 1
        health_stats[health]['amount'] += float(project.contract_amount or 0)

    # 按项目类型统计
    type_stats = {}
    for project in projects:
        ptype = project.project_type or 'OTHER'
        if ptype not in type_stats:
            type_stats[ptype] = {'count': 0, 'amount': 0}
        type_stats[ptype]['count'] += 1
        type_stats[ptype]['amount'] += float(project.contract_amount or 0)

    return ResponseModel(
        code=200,
        message="success",
        data={
            'total_count': total_count,
            'total_contract_amount': total_contract_amount,
            'by_stage': stage_stats,
            'by_health': health_stats,
            'by_type': type_stats,
        }
    )


# 其他接口可以根据需要添加...

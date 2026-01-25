# -*- coding: utf-8 -*-
"""
项目模块 - 统计功能

包含项目统计数据
"""

from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/stats", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_stats(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目统计数据
    """
    query = db.query(Project).filter(Project.is_active == True)

    # 应用数据权限过滤
    from app.services.data_scope import DataScopeService
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

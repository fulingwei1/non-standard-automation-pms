# -*- coding: utf-8 -*-
"""
项目模块 - 看板功能

包含项目看板视图
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/board", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_board(
    *,
    db: Session = Depends(deps.get_db),
    project_type: Optional[str] = Query(None, description="项目类型筛选"),
    pm_id: Optional[int] = Query(None, description="项目经理ID筛选"),
    health: Optional[str] = Query(None, description="健康度筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目看板视图 - 按阶段分组展示项目
    """
    query = db.query(Project).filter(Project.is_active == True)

    # 应用数据权限过滤
    from app.services.data_scope import DataScopeService
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)

    if project_type:
        query = query.filter(Project.project_type == project_type)
    if pm_id:
        query = query.filter(Project.pm_id == pm_id)
    if health:
        query = query.filter(Project.health == health)

    projects = query.all()

    # 按阶段分组
    stages = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']
    stage_names = {
        'S1': '需求进入',
        'S2': '需求澄清',
        'S3': '立项评审',
        'S4': '方案设计',
        'S5': '采购制造',
        'S6': '装配联调',
        'S7': '出厂验收',
        'S8': '现场交付',
        'S9': '质保结项',
    }

    board = {}
    for stage in stages:
        board[stage] = {
            'stage': stage,
            'stage_name': stage_names.get(stage, stage),
            'projects': [],
            'count': 0,
            'total_contract_amount': 0,
        }

    for project in projects:
        stage = project.stage or 'S1'
        if stage in board:
            board[stage]['projects'].append({
                'id': project.id,
                'project_code': project.project_code,
                'project_name': project.project_name,
                'customer_name': project.customer_name,
                'project_type': project.project_type,
                'stage': project.stage,
                'status': project.status,
                'pm_id': project.pm_id,
                'pm_name': project.pm_name,
                'te_id': getattr(project, "te_id", None),
                'sales_id': getattr(project, "sales_id", None),
                'health': project.health,
                'progress_pct': project.progress_pct,
                'contract_amount': float(project.contract_amount or 0),
                'planned_end_date': project.planned_end_date.isoformat() if project.planned_end_date else None,
            })
            board[stage]['count'] += 1
            board[stage]['total_contract_amount'] += float(project.contract_amount or 0)

    return ResponseModel(
        code=200,
        message="success",
        data={
            'stages': stages,
            'board': board,
            'total_projects': len(projects),
        }
    )

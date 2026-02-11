# -*- coding: utf-8 -*-
"""
项目绩效 API端点
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.organization import Employee
from app.models.project import Project
from app.models.staff_matching import HrProjectPerformance
from app.models.user import User
from app.schemas import staff_matching as schemas
from app.services.staff_matching import StaffMatchingService
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


@router.get("/", response_model=List[schemas.ProjectPerformanceResponse])
def list_performance(
    employee_id: Optional[int] = Query(None, description="员工ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    contribution_level: Optional[str] = Query(None, description="贡献等级"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取项目绩效列表"""
    query = db.query(HrProjectPerformance)

    if employee_id:
        query = query.filter(HrProjectPerformance.employee_id == employee_id)
    if project_id:
        query = query.filter(HrProjectPerformance.project_id == project_id)
    if contribution_level:
        query = query.filter(HrProjectPerformance.contribution_level == contribution_level)

    performances = query.order_by(HrProjectPerformance.evaluation_date.desc()).offset(pagination.offset).limit(pagination.limit).all()

    result = []
    for perf in performances:
        result.append({
            'id': perf.id,
            'employee_id': perf.employee_id,
            'project_id': perf.project_id,
            'role_code': perf.role_code,
            'role_name': perf.role_name,
            'performance_score': perf.performance_score,
            'quality_score': perf.quality_score,
            'collaboration_score': perf.collaboration_score,
            'on_time_rate': perf.on_time_rate,
            'contribution_level': perf.contribution_level,
            'hours_spent': perf.hours_spent,
            'evaluation_date': perf.evaluation_date,
            'evaluator_id': perf.evaluator_id,
            'comments': perf.comments,
            'created_at': perf.created_at,
            'project_name': perf.project.name if perf.project else None,
            'employee_name': perf.employee.name if perf.employee else None
        })

    return result


@router.post("/", response_model=schemas.ProjectPerformanceResponse, status_code=status.HTTP_201_CREATED)
def create_performance(
    perf_data: schemas.ProjectPerformanceCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:create"))
):
    """创建项目绩效记录"""
    # 验证员工和项目存在
    employee = db.query(Employee).filter(Employee.id == perf_data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")

    project = db.query(Project).filter(Project.id == perf_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 检查是否已存在
    existing = db.query(HrProjectPerformance).filter(
        HrProjectPerformance.employee_id == perf_data.employee_id,
        HrProjectPerformance.project_id == perf_data.project_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="该员工在此项目的绩效记录已存在")

    performance = HrProjectPerformance(
        **perf_data.model_dump(),
        evaluator_id=current_user.id
    )
    db.add(performance)
    db.commit()
    db.refresh(performance)

    # 更新员工档案
    StaffMatchingService.aggregate_employee_profile(db, perf_data.employee_id)

    return {
        'id': performance.id,
        'employee_id': performance.employee_id,
        'project_id': performance.project_id,
        'role_code': performance.role_code,
        'role_name': performance.role_name,
        'performance_score': performance.performance_score,
        'quality_score': performance.quality_score,
        'collaboration_score': performance.collaboration_score,
        'on_time_rate': performance.on_time_rate,
        'contribution_level': performance.contribution_level,
        'hours_spent': performance.hours_spent,
        'evaluation_date': performance.evaluation_date,
        'evaluator_id': performance.evaluator_id,
        'comments': performance.comments,
        'created_at': performance.created_at,
        'project_name': project.name,
        'employee_name': employee.name
    }


@router.get("/employee/{employee_id}", response_model=List[schemas.ProjectPerformanceResponse])
def get_employee_performance_history(
    employee_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取员工项目绩效历史"""
    performances = db.query(HrProjectPerformance).filter(
        HrProjectPerformance.employee_id == employee_id
    ).order_by(HrProjectPerformance.evaluation_date.desc()).all()

    result = []
    for perf in performances:
        result.append({
            'id': perf.id,
            'employee_id': perf.employee_id,
            'project_id': perf.project_id,
            'role_code': perf.role_code,
            'role_name': perf.role_name,
            'performance_score': perf.performance_score,
            'quality_score': perf.quality_score,
            'collaboration_score': perf.collaboration_score,
            'on_time_rate': perf.on_time_rate,
            'contribution_level': perf.contribution_level,
            'hours_spent': perf.hours_spent,
            'evaluation_date': perf.evaluation_date,
            'evaluator_id': perf.evaluator_id,
            'comments': perf.comments,
            'created_at': perf.created_at,
            'project_name': perf.project.name if perf.project else None,
            'employee_name': perf.employee.name if perf.employee else None
        })

    return result

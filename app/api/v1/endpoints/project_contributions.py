# -*- coding: utf-8 -*-
"""
项目贡献度API端点
支持查询、评分、报告生成
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.project import Project
from app.services.project_contribution_service import ProjectContributionService
from app.schemas.common import ResponseModel

router = APIRouter()


class ContributionRateRequest(BaseModel):
    """贡献度评分请求"""
    pm_rating: int = Body(..., ge=1, le=5, description="项目经理评分 1-5")
    period: str = Body(..., description="统计周期 YYYY-MM")


@router.get("/projects/{project_id}/contributions", response_model=dict)
def get_project_contributions(
    project_id: int,
    period: Optional[str] = Query(None, description="统计周期 YYYY-MM"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目贡献度列表
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)
    
    service = ProjectContributionService(db)
    contributions = service.get_project_contributions(project_id, period)
    
    return {
        'contributions': [
            {
                'id': c.id,
                'user_id': c.user_id,
                'user_name': (
                    (c.user.employee.name if hasattr(c.user, 'employee') and c.user.employee and hasattr(c.user.employee, 'name') else None) or
                    (c.user.real_name if hasattr(c.user, 'real_name') and c.user.real_name else None) or
                    (c.user.username if c.user and hasattr(c.user, 'username') and c.user.username else None) or
                    f'User {c.user_id}'
                ) if c.user else f'User {c.user_id}',
                'period': c.period,
                'task_count': c.task_count,
                'task_hours': float(c.task_hours or 0),
                'actual_hours': float(c.actual_hours or 0),
                'deliverable_count': c.deliverable_count,
                'issue_count': c.issue_count,
                'issue_resolved': c.issue_resolved,
                'contribution_score': float(c.contribution_score or 0),
                'pm_rating': c.pm_rating,
                'bonus_amount': float(c.bonus_amount or 0),
            }
            for c in contributions
        ]
    }


@router.post("/projects/{project_id}/contributions/{user_id}/rate", response_model=ResponseModel)
def rate_member_contribution(
    project_id: int,
    user_id: int,
    request: ContributionRateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目经理评分
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)
    
    # 验证当前用户是否为项目经理
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if project.pm_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有项目经理可以评分")
    
    service = ProjectContributionService(db)
    try:
        service.rate_member_contribution(
            project_id,
            user_id,
            request.period,
            request.pm_rating,
            current_user.id
        )
        return ResponseModel(code=200, message="评分成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/contributions/report", response_model=dict)
def get_contribution_report(
    project_id: int,
    period: Optional[str] = Query(None, description="统计周期 YYYY-MM"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    生成项目贡献度报告
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)
    
    service = ProjectContributionService(db)
    return service.generate_contribution_report(project_id, period)


@router.get("/users/{user_id}/project-contributions", response_model=dict)
def get_user_project_contributions(
    user_id: int,
    start_period: Optional[str] = Query(None, description="开始周期 YYYY-MM"),
    end_period: Optional[str] = Query(None, description="结束周期 YYYY-MM"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取个人项目贡献汇总
    """
    # 只能查看自己的贡献，除非是管理员
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权查看他人贡献")
    
    service = ProjectContributionService(db)
    contributions = service.get_user_project_contributions(
        user_id,
        start_period=start_period,
        end_period=end_period
    )
    
    return {
        'contributions': [
            {
                'project_id': c.project_id,
                'project_name': c.project.project_name if c.project else f'Project {c.project_id}',
                'period': c.period,
                'task_count': c.task_count,
                'actual_hours': float(c.actual_hours or 0),
                'deliverable_count': c.deliverable_count,
                'issue_resolved': c.issue_resolved,
                'contribution_score': float(c.contribution_score or 0),
                'pm_rating': c.pm_rating,
                'bonus_amount': float(c.bonus_amount or 0),
            }
            for c in contributions
        ]
    }


@router.post("/projects/{project_id}/contributions/calculate", response_model=ResponseModel)
def calculate_contributions(
    project_id: int,
    period: str = Query(..., description="统计周期 YYYY-MM"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    计算项目所有成员的贡献度
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)
    
    # 获取项目成员
    from app.models.project import ProjectMember
    members = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.is_active == True
    ).all()
    
    service = ProjectContributionService(db)
    calculated_count = 0
    
    for member in members:
        try:
            service.calculate_member_contribution(
                project_id,
                member.user_id,
                period
            )
            calculated_count += 1
        except Exception as e:
            # 记录错误但继续处理其他成员
            print(f"Error calculating contribution for user {member.user_id}: {e}")
    
    return ResponseModel(
        code=200,
        message=f"已计算 {calculated_count} 位成员的贡献度"
    )

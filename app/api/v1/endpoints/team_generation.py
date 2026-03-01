# -*- coding: utf-8 -*-
"""
AI 自动组队 API
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.services.team_generation_service import TeamGenerationService

router = APIRouter()


@router.post("/projects/{project_id}/generate-team", summary="AI 自动生成项目组")
def generate_team(
    project_id: int = Path(..., description="项目 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    AI 自动生成项目组方案
    
    流程：
    1. 分析项目需求
    2. 确定所需角色
    3. 匹配工程师
    4. 生成团队方案
    
    返回：
    - 团队组成
    - 角色分配
    - 匹配度分析
    - 优势与风险
    """
    service = TeamGenerationService(db)
    team_plan = service.generate_team_plan(project_id)
    
    if 'error' in team_plan:
        raise HTTPException(status_code=404, detail=team_plan['error'])
    
    return team_plan


@router.post("/projects/{project_id}/save-team-plan", summary="保存项目组方案")
def save_team_plan(
    project_id: int = Path(..., description="项目 ID"),
    team_data: dict = Body(..., description="团队方案数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """保存 AI 生成的团队方案"""
    service = TeamGenerationService(db)
    
    # 添加项目 ID
    team_data['project_id'] = project_id
    
    plan = service.save_team_plan(team_data, current_user.id)
    
    return {
        'plan_id': plan.id,
        'plan_no': plan.plan_no,
        'status': plan.status,
        'total_members': plan.total_members,
        'overall_score': plan.overall_score,
    }


@router.get("/team-plans/{plan_id}", summary="获取团队方案详情")
def get_team_plan(
    plan_id: int = Path(..., description="方案 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取团队方案详情"""
    from app.models.project_team import ProjectTeamPlan, ProjectTeamMember
    
    plan = db.query(ProjectTeamPlan).filter(ProjectTeamPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="方案不存在")
    
    members = db.query(ProjectTeamMember).filter(
        ProjectTeamMember.team_plan_id == plan_id
    ).all()
    
    return {
        'plan': plan,
        'members': [
            {
                'id': m.id,
                'engineer_id': m.engineer_id,
                'engineer_name': m.engineer_name,
                'role': m.role,
                'role_name': m.role_name,
                'estimated_hours': m.estimated_hours,
                'match_score': m.match_score,
                'match_reason': m.match_reason,
            }
            for m in members
        ],
    }


@router.post("/team-plans/{plan_id}/submit", summary="提交团队方案审批")
def submit_team_plan(
    plan_id: int = Path(..., description="方案 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """提交团队方案审批"""
    from app.models.project_team import ProjectTeamPlan
    from datetime import datetime
    
    plan = db.query(ProjectTeamPlan).filter(ProjectTeamPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="方案不存在")
    
    plan.status = 'PENDING'
    plan.submitted_at = datetime.now()
    plan.submitted_by = current_user.id
    
    db.commit()
    
    return {'message': '方案已提交审批', 'status': plan.status}


@router.post("/team-plans/{plan_id}/approve", summary="审批团队方案")
def approve_team_plan(
    plan_id: int = Path(..., description="方案 ID"),
    decision: str = Body(..., description="决策 APPROVE/REJECT"),
    comments: Optional[str] = Body(None, description="审批意见"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """审批团队方案"""
    from app.models.project_team import ProjectTeamPlan, ProjectTeamApproval
    from datetime import datetime
    
    plan = db.query(ProjectTeamPlan).filter(ProjectTeamPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="方案不存在")
    
    plan.status = 'APPROVED' if decision == 'APPROVE' else 'REJECTED'
    plan.approved_by = current_user.id
    plan.approved_at = datetime.now()
    
    if decision == 'REJECT':
        plan.rejected_reason = comments
    
    # 记录审批
    approval = ProjectTeamApproval(
        approval_no=f"APR{datetime.now().strftime('%Y%m%d%H%M%S')}",
        team_plan_id=plan_id,
        approver_id=current_user.id,
        approver_name=current_user.real_name or current_user.username,
        decision=decision,
        comments=comments,
    )
    db.add(approval)
    db.commit()
    
    return {'message': '方案已审批', 'status': plan.status}

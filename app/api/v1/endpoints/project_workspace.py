# -*- coding: utf-8 -*-
"""
项目工作空间API端点
整合项目奖金、会议、问题、文档等数据
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.project import Project, ProjectDocument, ProjectMember
from app.models.task_center import TaskUnified
from app.models.issue import Issue
from app.services.project_bonus_service import ProjectBonusService
from app.services.project_meeting_service import ProjectMeetingService
from app.services.project_solution_service import ProjectSolutionService
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/projects/{project_id}/workspace", response_model=dict)
def get_project_workspace(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目工作空间数据
    整合项目概览、团队、任务、奖金、会议、问题、文档等信息
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    from app.services.project_workspace_service import (
        build_project_basic_info,
        build_team_info,
        build_task_info,
        build_bonus_info,
        build_meeting_info,
        build_issue_info,
        build_solution_info,
        build_document_info
    )
    
    # 检查项目访问权限
    check_project_access_or_raise(db, current_user, project_id)
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 构建各类信息
    project_info = build_project_basic_info(project)
    team_info = build_team_info(db, project_id)
    task_info = build_task_info(db, project_id)
    bonus_info = build_bonus_info(db, project_id)
    meeting_info = build_meeting_info(db, project_id)
    issue_info = build_issue_info(db, project_id)
    solution_info = build_solution_info(db, project_id)
    document_info = build_document_info(db, project_id)
    
    return {
        'project': project_info,
        'team': team_info,
        'tasks': task_info,
        'bonus': bonus_info,
        'meetings': meeting_info,
        'issues': issue_info,
        'solutions': solution_info,
        'documents': document_info,
    }


@router.get("/projects/{project_id}/bonuses", response_model=dict)
def get_project_bonuses(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目奖金信息
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)
    
    bonus_service = ProjectBonusService(db)
    
    return {
        'rules': [
            {
                'id': r.id,
                'rule_name': r.rule_name,
                'bonus_type': r.bonus_type,
            }
            for r in bonus_service.get_project_bonus_rules(project_id)
        ],
        'calculations': [
            {
                'id': c.id,
                'calculation_code': c.calculation_code,
                'user_name': c.user.real_name or c.user.username if c.user else 'Unknown',
                'calculated_amount': float(c.calculated_amount or 0),
                'status': c.status,
            }
            for c in bonus_service.get_project_bonus_calculations(project_id)
        ],
        'statistics': bonus_service.get_project_bonus_statistics(project_id),
        'member_summary': bonus_service.get_project_member_bonus_summary(project_id),
    }


@router.get("/projects/{project_id}/meetings", response_model=dict)
def get_project_meetings(
    project_id: int,
    status: Optional[str] = Query(None, description="会议状态"),
    rhythm_level: Optional[str] = Query(None, description="节律层级"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目关联的会议列表
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)
    
    meeting_service = ProjectMeetingService(db)
    meetings = meeting_service.get_project_meetings(
        project_id,
        status=status,
        rhythm_level=rhythm_level
    )
    
    return {
        'meetings': [
            {
                'id': m.id,
                'meeting_name': m.meeting_name,
                'meeting_date': m.meeting_date.isoformat() if m.meeting_date else None,
                'rhythm_level': m.rhythm_level,
                'status': m.status,
                'organizer_name': m.organizer_name,
                'minutes': m.minutes,
                'decisions': m.decisions,
            }
            for m in meetings
        ],
        'statistics': meeting_service.get_project_meeting_statistics(project_id),
    }


@router.post("/projects/{project_id}/meetings/{meeting_id}/link", response_model=ResponseModel)
def link_meeting_to_project(
    project_id: int,
    meeting_id: int,
    is_primary: bool = Query(False, description="是否设为主项目"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    将会议关联到项目
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)
    
    meeting_service = ProjectMeetingService(db)
    success = meeting_service.link_meeting_to_project(
        meeting_id,
        project_id,
        is_primary=is_primary
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="关联失败")
    
    return ResponseModel(code=200, message="关联成功")


@router.get("/projects/{project_id}/issues", response_model=dict)
def get_project_issues(
    project_id: int,
    status: Optional[str] = Query(None, description="问题状态"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目问题列表
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)
    
    from app.models.issue import Issue
    query = db.query(Issue).filter(Issue.project_id == project_id)
    
    if status:
        query = query.filter(Issue.status == status)
    
    issues = query.order_by(Issue.report_date.desc()).all()
    
    return {
        'issues': [
            {
                'id': i.id,
                'issue_no': i.issue_no,
                'title': i.title,
                'status': i.status,
                'severity': i.severity,
                'priority': i.priority,
                'solution': i.solution,
                'assignee_name': i.assignee_name,
            }
            for i in issues
        ],
    }


@router.get("/projects/{project_id}/solutions", response_model=dict)
def get_project_solutions(
    project_id: int,
    issue_type: Optional[str] = Query(None, description="问题类型"),
    category: Optional[str] = Query(None, description="问题分类"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目解决方案库
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)
    
    solution_service = ProjectSolutionService(db)
    
    return {
        'solutions': solution_service.get_project_solutions(
            project_id,
            issue_type=issue_type,
            category=category
        ),
        'statistics': solution_service.get_project_solution_statistics(project_id),
    }

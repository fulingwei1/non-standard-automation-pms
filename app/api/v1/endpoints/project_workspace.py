# -*- coding: utf-8 -*-
"""
项目工作空间API端点
整合项目奖金、会议、问题、文档等数据
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

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
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取项目基本信息
    project_info = {
        'id': project.id,
        'project_code': project.project_code,
        'project_name': project.project_name,
        'stage': project.stage,
        'status': project.status,
        'health': project.health,
        'progress_pct': float(project.progress_pct or 0),
        'contract_amount': float(project.contract_amount or 0),
        'pm_name': project.pm_name,
    }
    
    # 获取项目成员
    members = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.is_active == True
    ).all()
    team_info = [
        {
            'user_id': m.user_id,
            'user_name': m.user.real_name or m.user.username if m.user else 'Unknown',
            'role_code': m.role_code,
            'allocation_pct': float(m.allocation_pct or 100),
            'start_date': m.start_date.isoformat() if m.start_date else None,
            'end_date': m.end_date.isoformat() if m.end_date else None,
        }
        for m in members
    ]
    
    # 获取项目任务
    tasks = db.query(TaskUnified).filter(
        TaskUnified.project_id == project_id
    ).limit(50).all()
    task_info = [
        {
            'id': t.id,
            'title': t.title,
            'status': t.status,
            'assignee_name': t.assignee_name,
            'plan_end_date': t.plan_end_date.isoformat() if t.plan_end_date else None,
            'progress': float(t.progress or 0),
        }
        for t in tasks
    ]
    
    # 获取项目奖金
    bonus_service = ProjectBonusService(db)
    bonus_rules = bonus_service.get_project_bonus_rules(project_id)
    bonus_calculations = bonus_service.get_project_bonus_calculations(project_id)
    bonus_distributions = bonus_service.get_project_bonus_distributions(project_id)
    bonus_statistics = bonus_service.get_project_bonus_statistics(project_id)
    bonus_member_summary = bonus_service.get_project_member_bonus_summary(project_id)
    
    bonus_info = {
        'rules': [
            {
                'id': r.id,
                'rule_name': r.rule_name,
                'bonus_type': r.bonus_type,
                'coefficient': float(r.coefficient or 0),
            }
            for r in bonus_rules
        ],
        'calculations': [
            {
                'id': c.id,
                'calculation_code': c.calculation_code,
                'user_name': c.user.real_name or c.user.username if c.user else 'Unknown',
                'calculated_amount': float(c.calculated_amount or 0),
                'status': c.status,
                'calculated_at': c.calculated_at.isoformat() if c.calculated_at else None,
            }
            for c in bonus_calculations[:20]  # 限制返回数量
        ],
        'distributions': [
            {
                'id': d.id,
                'user_name': d.user.real_name or d.user.username if d.user else 'Unknown',
                'distributed_amount': float(d.distributed_amount or 0),
                'status': d.status,
                'distributed_at': d.distributed_at.isoformat() if d.distributed_at else None,
            }
            for d in bonus_distributions[:20]
        ],
        'statistics': bonus_statistics,
        'member_summary': bonus_member_summary,
    }
    
    # 获取项目会议
    meeting_service = ProjectMeetingService(db)
    meetings = meeting_service.get_project_meetings(project_id)
    meeting_statistics = meeting_service.get_project_meeting_statistics(project_id)
    
    meeting_info = {
        'meetings': [
            {
                'id': m.id,
                'meeting_name': m.meeting_name,
                'meeting_date': m.meeting_date.isoformat() if m.meeting_date else None,
                'rhythm_level': m.rhythm_level,
                'status': m.status,
                'organizer_name': m.organizer_name,
                'has_minutes': bool(m.minutes),
                'has_decisions': bool(m.decisions),
            }
            for m in meetings[:20]
        ],
        'statistics': meeting_statistics,
    }
    
    # 获取项目问题
    issues = db.query(Issue).filter(
        Issue.project_id == project_id
    ).order_by(Issue.report_date.desc()).limit(50).all()
    
    issue_info = {
        'issues': [
            {
                'id': i.id,
                'issue_no': i.issue_no,
                'title': i.title,
                'status': i.status,
                'severity': i.severity,
                'priority': i.priority,
                'has_solution': bool(i.solution),
                'assignee_name': i.assignee_name,
                'report_date': i.report_date.isoformat() if i.report_date else None,
            }
            for i in issues
        ],
    }
    
    # 获取解决方案
    solution_service = ProjectSolutionService(db)
    solutions = solution_service.get_project_solutions(project_id)
    solution_statistics = solution_service.get_project_solution_statistics(project_id)
    
    solution_info = {
        'solutions': solutions[:20],
        'statistics': solution_statistics,
    }
    
    # 获取项目文档
    documents = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id
    ).order_by(ProjectDocument.created_at.desc()).limit(20).all()
    
    document_info = [
        {
            'id': d.id,
            'doc_name': d.doc_name,
            'doc_type': d.doc_type,
            'version': d.version,
            'status': d.status,
            'created_at': d.created_at.isoformat() if d.created_at else None,
        }
        for d in documents
    ]
    
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

# -*- coding: utf-8 -*-
"""
项目工作空间服务
"""

from typing import Any, Dict, List

from sqlalchemy.orm import Session, joinedload

from app.models.issue import Issue
from app.models.project import Project, ProjectDocument, ProjectMember
from app.models.task_center import TaskUnified
from app.services.project_bonus_service import ProjectBonusService
from app.services.project_meeting_service import ProjectMeetingService
from app.services.project_solution_service import ProjectSolutionService


def build_project_basic_info(project: Project) -> Dict[str, Any]:
    """
    构建项目基本信息

    Returns:
        Dict[str, Any]: 项目基本信息字典
    """
    return {
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


def build_team_info(
    db: Session,
    project_id: int
) -> List[Dict[str, Any]]:
    """
    构建团队信息

    Returns:
        List[Dict[str, Any]]: 团队成员信息列表
    """
    members = (
        db.query(ProjectMember)
        .options(joinedload(ProjectMember.user))
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.is_active == True
        )
        .all()
    )

    return [
        {
            'user_id': m.user_id,
            'user_name': m.user.real_name or m.user.username if m.user else f'user_{m.user_id}',
            'role_code': m.role_code,
            'allocation_pct': float(m.allocation_pct or 100),
            'start_date': m.start_date.isoformat() if m.start_date else None,
            'end_date': m.end_date.isoformat() if m.end_date else None,
        }
        for m in members
    ]


def build_task_info(
    db: Session,
    project_id: int,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    构建任务信息

    Returns:
        List[Dict[str, Any]]: 任务信息列表
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.project_id == project_id
    ).limit(limit).all()

    return [
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


def build_bonus_info(
    db: Session,
    project_id: int
) -> Dict[str, Any]:
    """
    构建奖金信息（带错误处理）

    Returns:
        Dict[str, Any]: 奖金信息字典
    """
    try:
        bonus_service = ProjectBonusService(db)
        bonus_rules = bonus_service.get_project_bonus_rules(project_id) or []
        bonus_calculations = bonus_service.get_project_bonus_calculations(project_id) or []
        bonus_distributions = bonus_service.get_project_bonus_distributions(project_id) or []
        bonus_statistics = bonus_service.get_project_bonus_statistics(project_id) or {}
        bonus_member_summary = bonus_service.get_project_member_bonus_summary(project_id) or []

        return {
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
                    'user_name': getattr(c.user, 'real_name', None) or getattr(c.user, 'username', None) if hasattr(c, 'user') and c.user else 'Unknown',
                    'calculated_amount': float(c.calculated_amount or 0),
                    'status': c.status,
                    'calculated_at': c.calculated_at.isoformat() if hasattr(c, 'calculated_at') and c.calculated_at else None,
                }
                for c in bonus_calculations[:20]  # 限制返回数量
            ],
            'distributions': [
                {
                    'id': d.id,
                    'user_name': getattr(d.user, 'real_name', None) or getattr(d.user, 'username', None) if hasattr(d, 'user') and d.user else 'Unknown',
                    'distributed_amount': float(d.distributed_amount or 0),
                    'status': d.status,
                    'distributed_at': d.distributed_at.isoformat() if hasattr(d, 'distributed_at') and d.distributed_at else None,
                }
                for d in bonus_distributions[:20]
            ],
            'statistics': bonus_statistics,
            'member_summary': bonus_member_summary,
        }
    except Exception as e:
        import logging
        logging.error(f"获取项目奖金数据失败: {str(e)}")
        return {
            'rules': [],
            'calculations': [],
            'distributions': [],
            'statistics': {},
            'member_summary': [],
        }


def build_meeting_info(
    db: Session,
    project_id: int
) -> Dict[str, Any]:
    """
    构建会议信息（带错误处理）

    Returns:
        Dict[str, Any]: 会议信息字典
    """
    try:
        meeting_service = ProjectMeetingService(db)
        meetings = meeting_service.get_project_meetings(project_id) or []
        meeting_statistics = meeting_service.get_project_meeting_statistics(project_id) or {}

        return {
            'meetings': [
                {
                    'id': m.id,
                    'meeting_name': getattr(m, 'meeting_name', ''),
                    'meeting_date': m.meeting_date.isoformat() if hasattr(m, 'meeting_date') and m.meeting_date else None,
                    'rhythm_level': getattr(m, 'rhythm_level', ''),
                    'status': getattr(m, 'status', ''),
                    'organizer_name': getattr(m, 'organizer_name', ''),
                    'minutes': getattr(m, 'minutes', ''),
                    'has_minutes': bool(getattr(m, 'minutes', '')),
                }
                for m in meetings[:20]
            ],
            'statistics': meeting_statistics,
        }
    except Exception as e:
        import logging
        logging.error(f"获取项目会议数据失败: {str(e)}")
        return {
            'meetings': [],
            'statistics': {},
        }


def build_issue_info(
    db: Session,
    project_id: int,
    limit: int = 50
) -> Dict[str, Any]:
    """
    构建问题信息

    Returns:
        Dict[str, Any]: 问题信息字典
    """
    issues = db.query(Issue).filter(
        Issue.project_id == project_id
    ).order_by(Issue.report_date.desc()).limit(limit).all()

    return {
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


def build_solution_info(
    db: Session,
    project_id: int
) -> Dict[str, Any]:
    """
    构建解决方案信息（带错误处理）

    Returns:
        Dict[str, Any]: 解决方案信息字典
    """
    try:
        solution_service = ProjectSolutionService(db)
        solutions = solution_service.get_project_solutions(project_id) or []
        solution_statistics = solution_service.get_project_solution_statistics(project_id) or {}

        return {
            'solutions': solutions[:20] if isinstance(solutions, list) else [],
            'statistics': solution_statistics,
        }
    except Exception as e:
        import logging
        logging.error(f"获取项目解决方案数据失败: {str(e)}")
        return {
            'solutions': [],
            'statistics': {},
        }


def build_document_info(
    db: Session,
    project_id: int,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    构建文档信息

    Returns:
        List[Dict[str, Any]]: 文档信息列表
    """
    documents = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id
    ).order_by(ProjectDocument.created_at.desc()).limit(limit).all()

    return [
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

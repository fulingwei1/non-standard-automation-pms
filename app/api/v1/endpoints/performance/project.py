# -*- coding: utf-8 -*-
"""
项目绩效 - 自动生成
从 performance.py 拆分
"""

# -*- coding: utf-8 -*-
"""
绩效管理 API endpoints
核心功能：多层级绩效视图、绩效对比、趋势分析、排行榜
"""

from typing import Any, List, Optional, Dict
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func, case

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Project
from app.models.organization import Department, Employee
from app.models.performance import (
    PerformancePeriod, PerformanceIndicator, PerformanceResult,
    PerformanceEvaluation, PerformanceAppeal, ProjectContribution,
    PerformanceRankingSnapshot,
    # New Performance System
    MonthlyWorkSummary, PerformanceEvaluationRecord, EvaluationWeightConfig
)
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.performance import (
    PersonalPerformanceResponse, PerformanceTrendResponse,
    TeamPerformanceResponse, DepartmentPerformanceResponse, PerformanceRankingResponse,
    ProjectPerformanceResponse, ProjectProgressReportResponse, PerformanceCompareResponse,
    # New Performance System
    MonthlyWorkSummaryCreate, MonthlyWorkSummaryUpdate, MonthlyWorkSummaryResponse,
    MonthlyWorkSummaryListItem, PerformanceEvaluationRecordCreate,
    PerformanceEvaluationRecordUpdate, PerformanceEvaluationRecordResponse,
    EvaluationTaskItem, EvaluationTaskListResponse, EvaluationDetailResponse,
    MyPerformanceResponse, EvaluationWeightConfigCreate, EvaluationWeightConfigResponse,
    EvaluationWeightConfigListResponse
)
from app.services.performance_service import PerformanceService
from app.services.performance_integration_service import PerformanceIntegrationService

router = APIRouter()


def _check_performance_view_permission(current_user: User, target_user_id: int, db: Session) -> bool:
    """
    检查用户是否有权限查看指定用户的绩效

    规则：
    1. 可以查看自己的绩效
    2. 部门经理可以查看本部门员工的绩效
    3. 项目经理可以查看项目成员的绩效
    4. 管理员可以查看所有人的绩效

    Returns:
        bool: 是否有权限查看
    """
    if current_user.is_superuser:
        return True

    # 查看自己的绩效
    if current_user.id == target_user_id:
        return True

    # 检查是否是部门经理
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        return False

    # 检查是否有管理角色
    manager_roles = ['dept_manager', 'department_manager', '部门经理',
                     'pm', 'project_manager', '项目经理',
                     'admin', 'super_admin', '管理员']

    has_manager_role = False
    for user_role in (current_user.roles or []):
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ''
        if role_code in manager_roles or role_name in manager_roles:
            has_manager_role = True
            break

    if not has_manager_role:
        return False

    # 检查是否是同一部门
    if target_user.department_id and current_user.department_id == target_user.department_id:
        return True

    # 检查是否管理同一项目
    from app.models.project import Project
    user_projects = db.query(Project).filter(Project.pm_id == current_user.id).all()
    project_ids = [p.id for p in user_projects]

    target_projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
    for project in target_projects:
        # 检查目标用户是否是项目成员
        from app.models.progress import Task
        member_task = db.query(Task).filter(
            Task.project_id == project.id,
            Task.owner_id == target_user_id
        ).first()
        if member_task:
            return True

    return False


def _get_team_members(db: Session, team_id: int) -> List[int]:
    """
    获取团队成员ID列表

    Args:
        db: 数据库会话
        team_id: 团队ID（暂时使用department_id作为team_id）

    Returns:
        List[int]: 成员ID列表
    """
    # 临时使用部门作为团队
    from app.models.organization import Department
    users = db.query(User).filter(
        User.department_id == team_id,
        User.is_active == True
    ).all()
    return [u.id for u in users]


def _get_department_members(db: Session, dept_id: int) -> List[int]:
    """
    获取部门成员ID列表

    Args:
        db: 数据库会话
        dept_id: 部门ID

    Returns:
        List[int]: 成员ID列表
    """
    users = db.query(User).filter(
        User.department_id == dept_id,
        User.is_active == True
    ).all()
    return [u.id for u in users]


def _get_evaluator_type(user: User, db: Session) -> str:
    """
    判断评价人类型（部门经理/项目经理）

    Args:
        user: 用户对象
        db: 数据库会话

    Returns:
        str: 评价人类型（DEPT_MANAGER/PROJECT_MANAGER/BOTH）
    """
    is_dept_manager = False
    is_project_manager = False

    for user_role in (user.roles or []):
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ''

        if role_code in ['dept_manager', 'department_manager', '部门经理'] or role_name in ['dept_manager', 'department_manager', '部门经理']:
            is_dept_manager = True
        if role_code in ['pm', 'project_manager', '项目经理'] or role_name in ['pm', 'project_manager', '项目经理']:
            is_project_manager = True

    if is_dept_manager and is_project_manager:
        return 'BOTH'
    elif is_dept_manager:
        return 'DEPT_MANAGER'
    elif is_project_manager:
        return 'PROJECT_MANAGER'
    else:
        return 'OTHER'


def _get_team_name(db: Session, team_id: int) -> str:
    """获取团队名称"""
    from app.models.organization import Department
    dept = db.query(Department).filter(Department.id == team_id).first()
    return dept.name if dept else f"团队{team_id}"


def _get_department_name(db: Session, dept_id: int) -> str:
    """获取部门名称"""
    from app.models.organization import Department
    dept = db.query(Department).filter(Department.id == dept_id).first()
    return dept.name if dept else f"部门{dept_id}"



from fastapi import APIRouter

router = APIRouter(
    prefix="/performance/project",
    tags=["project"]
)

# 共 3 个路由

# ==================== 项目绩效 ====================

@router.get("/project/{project_id}", response_model=ProjectPerformanceResponse, status_code=status.HTTP_200_OK)
def get_project_performance(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    period_id: Optional[int] = Query(None, description="周期ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目成员绩效（项目贡献）
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if period_id:
        period = db.query(PerformancePeriod).filter(PerformancePeriod.id == period_id).first()
    else:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.status == "FINALIZED"
        ).order_by(desc(PerformancePeriod.end_date)).first()
    
    if not period:
        raise HTTPException(status_code=404, detail="未找到考核周期")
    
    # 获取项目贡献
    contributions = db.query(ProjectContribution).filter(
        ProjectContribution.period_id == period.id,
        ProjectContribution.project_id == project_id
    ).all()
    
    members = []
    total_contribution = Decimal("0")
    
    for contrib in contributions:
        user = db.query(User).filter(User.id == contrib.user_id).first()
        score = contrib.contribution_score or Decimal("0")
        total_contribution += score
        
        members.append({
            "user_id": contrib.user_id,
            "user_name": user.real_name or user.username if user else None,
            "contribution_score": float(score),
            "work_hours": float(contrib.hours_spent) if contrib.hours_spent else 0,
            "task_count": contrib.task_count or 0
        })
    
    # 按贡献分排序
    members.sort(key=lambda x: x["contribution_score"], reverse=True)
    
    return ProjectPerformanceResponse(
        project_id=project_id,
        project_name=project.project_name,
        period_id=period.id,
        period_name=period.period_name,
        member_count=len(members),
        total_contribution_score=total_contribution,
        members=members
    )


@router.get("/project/{project_id}/progress", response_model=ProjectProgressReportResponse, status_code=status.HTTP_200_OK)
def get_project_progress_report(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    report_type: str = Query("WEEKLY", description="报告类型：WEEKLY/MONTHLY"),
    report_date: Optional[date] = Query(None, description="报告日期（默认今天）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目进展报告（周报/月报）
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if not report_date:
        report_date = datetime.now().date()

    # 从进度跟踪模块获取数据
    from app.models.progress import Task
    project_tasks = db.query(Task).filter(Task.project_id == project_id).all()

    total_tasks = len(project_tasks)
    completed_tasks = len([t for t in project_tasks if t.status == "DONE"])
    overall_progress = int(project.progress or 0)

    # 检查是否按计划进行
    on_schedule = True
    delayed_tasks = [t for t in project_tasks if t.plan_end and t.plan_end < datetime.now().date() and t.status not in ["DONE", "CANCELLED"]]
    if delayed_tasks:
        on_schedule = False

    progress_summary = {
        "overall_progress": overall_progress,
        "completed_tasks": completed_tasks,
        "total_tasks": total_tasks,
        "on_schedule": on_schedule
    }

    # 获取成员贡献
    member_contributions = []
    from collections import defaultdict
    member_task_count = defaultdict(int)
    member_hours = defaultdict(float)

    for task in project_tasks:
        if task.owner_id:
            member_task_count[task.owner_id] += 1
            # 假设每个任务平均工时为 4 小时
            member_hours[task.owner_id] += 4

    for user_id, task_count in member_task_count.items():
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            member_contributions.append({
                "user_id": user_id,
                "user_name": user.real_name or user.username,
                "task_count": task_count,
                "estimated_hours": member_hours[user_id]
            })

    member_contributions.sort(key=lambda x: x["task_count"], reverse=True)

    # 获取关键成果（最近完成的任务）
    key_achievements = []
    completed = [t for t in project_tasks if t.status == "DONE"]
    completed.sort(key=lambda x: x.updated_at or x.created_at or datetime.now(), reverse=True)
    for task in completed[:5]:
        key_achievements.append({
            "task_name": task.task_name,
            "completed_date": task.updated_at.isoformat() if task.updated_at else None,
            "description": task.description[:100] if task.description else ""
        })

    # 获取风险和问题（逾期任务）
    risks_and_issues = []
    for task in delayed_tasks[:10]:
        risks_and_issues.append({
            "type": "DELAYED_TASK",
            "description": f"任务 '{task.task_name}' 已逾期",
            "severity": "HIGH" if (datetime.now().date() - task.plan_end).days > 7 else "MEDIUM",
            "task_id": task.id,
            "task_name": task.task_name,
            "due_date": task.plan_end.isoformat()
        })

    return ProjectProgressReportResponse(
        project_id=project_id,
        project_name=project.project_name,
        report_type=report_type,
        report_date=report_date,
        progress_summary=progress_summary,
        member_contributions=member_contributions,
        key_achievements=key_achievements,
        risks_and_issues=risks_and_issues
    )


@router.get("/compare", response_model=PerformanceCompareResponse, status_code=status.HTTP_200_OK)
def compare_performance(
    *,
    db: Session = Depends(deps.get_db),
    user_ids: str = Query(..., description="用户ID列表，逗号分隔"),
    period_id: Optional[int] = Query(None, description="周期ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    绩效对比（多人对比）
    """
    user_id_list = [int(uid.strip()) for uid in user_ids.split(",") if uid.strip()]
    
    if period_id:
        period = db.query(PerformancePeriod).filter(PerformancePeriod.id == period_id).first()
    else:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.status == "FINALIZED"
        ).order_by(desc(PerformancePeriod.end_date)).first()
    
    if not period:
        raise HTTPException(status_code=404, detail="未找到考核周期")
    
    comparison_data = []
    
    for user_id in user_id_list:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            continue
        
        result = db.query(PerformanceResult).filter(
            PerformanceResult.period_id == period.id,
            PerformanceResult.user_id == user_id
        ).first()
        
        comparison_data.append({
            "user_id": user_id,
            "user_name": user.real_name or user.username,
            "score": float(result.total_score) if result and result.total_score else 0,
            "level": result.level if result else "QUALIFIED",
            "department_name": result.department_name if result else None
        })
    
    return PerformanceCompareResponse(
        user_ids=user_id_list,
        period_id=period.id,
        period_name=period.period_name,
        comparison_data=comparison_data
    )




# -*- coding: utf-8 -*-
"""
个人绩效 - 自动生成
从 performance.py 拆分
"""

# -*- coding: utf-8 -*-
"""
绩效管理 API endpoints
核心功能：多层级绩效视图、绩效对比、趋势分析、排行榜
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, case, desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.organization import Department, Employee
from app.models.performance import (  # New Performance System
    EvaluationWeightConfig,
    MonthlyWorkSummary,
    PerformanceAppeal,
    PerformanceEvaluation,
    PerformanceEvaluationRecord,
    PerformanceIndicator,
    PerformancePeriod,
    PerformanceRankingSnapshot,
    PerformanceResult,
    ProjectContribution,
)
from app.models.project import Project
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.performance import (  # New Performance System
    DepartmentPerformanceResponse,
    EvaluationDetailResponse,
    EvaluationTaskItem,
    EvaluationTaskListResponse,
    EvaluationWeightConfigCreate,
    EvaluationWeightConfigListResponse,
    EvaluationWeightConfigResponse,
    MonthlyWorkSummaryCreate,
    MonthlyWorkSummaryListItem,
    MonthlyWorkSummaryResponse,
    MonthlyWorkSummaryUpdate,
    MyPerformanceResponse,
    PerformanceCompareResponse,
    PerformanceEvaluationRecordCreate,
    PerformanceEvaluationRecordResponse,
    PerformanceEvaluationRecordUpdate,
    PerformanceRankingResponse,
    PerformanceTrendResponse,
    PersonalPerformanceResponse,
    ProjectPerformanceResponse,
    ProjectProgressReportResponse,
    TeamPerformanceResponse,
)
from app.services.performance_integration_service import PerformanceIntegrationService
from app.services.performance_service import PerformanceService

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
    prefix="/performance/individual",
    tags=["individual"]
)

# 共 3 个路由

# ==================== 个人绩效 ====================

@router.get("/my", response_model=PersonalPerformanceResponse, status_code=status.HTTP_200_OK)
def get_my_performance(
    *,
    db: Session = Depends(deps.get_db),
    period_type: str = Query("MONTHLY", description="周期类型：WEEKLY/MONTHLY/QUARTERLY/YEARLY"),
    period_id: Optional[int] = Query(None, description="周期ID（不提供则取最新）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    查看我的绩效（周/月/季度）
    """
    # 获取周期
    if period_id:
        period = db.query(PerformancePeriod).filter(PerformancePeriod.id == period_id).first()
    else:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.period_type == period_type,
            PerformancePeriod.status == "FINALIZED"
        ).order_by(desc(PerformancePeriod.end_date)).first()

    if not period:
        raise HTTPException(status_code=404, detail="未找到对应的考核周期")

    # 获取绩效结果
    result = db.query(PerformanceResult).filter(
        PerformanceResult.period_id == period.id,
        PerformanceResult.user_id == current_user.id
    ).first()

    if not result:
        return PersonalPerformanceResponse(
            user_id=current_user.id,
            user_name=current_user.real_name or current_user.username,
            period_id=period.id,
            period_name=period.period_name,
            period_type=period.period_type,
            start_date=period.start_date,
            end_date=period.end_date,
            total_score=Decimal("0"),
            level="QUALIFIED",
            indicators=[],
            project_contributions=[]
        )

    # 获取指标明细
    indicators = []
    if result.indicator_scores:
        for ind_id, score in result.indicator_scores.items():
            indicator = db.query(PerformanceIndicator).filter(PerformanceIndicator.id == int(ind_id)).first()
            if indicator:
                indicators.append({
                    "indicator_id": indicator.id,
                    "indicator_name": indicator.indicator_name,
                    "indicator_type": indicator.indicator_type,
                    "score": float(score),
                    "weight": float(indicator.weight) if indicator.weight else 0
                })

    # 获取项目贡献
    contributions = db.query(ProjectContribution).filter(
        ProjectContribution.period_id == period.id,
        ProjectContribution.user_id == current_user.id
    ).all()

    project_contributions = []
    for contrib in contributions:
        project = db.query(Project).filter(Project.id == contrib.project_id).first()
        project_contributions.append({
            "project_id": contrib.project_id,
            "project_name": project.project_name if project else None,
            "contribution_score": float(contrib.contribution_score) if contrib.contribution_score else 0,
            "work_hours": float(contrib.hours_spent) if contrib.hours_spent else 0,
            "task_count": contrib.task_count or 0
        })

    # 计算排名
    rank = None
    all_results = db.query(PerformanceResult).filter(
        PerformanceResult.period_id == period.id
    ).order_by(desc(PerformanceResult.total_score)).all()

    for idx, r in enumerate(all_results, 1):
        if r.user_id == current_user.id:
            rank = idx
            break

    return PersonalPerformanceResponse(
        user_id=current_user.id,
        user_name=current_user.real_name or current_user.username,
        period_id=period.id,
        period_name=period.period_name,
        period_type=period.period_type,
        start_date=period.start_date,
        end_date=period.end_date,
        total_score=result.total_score or Decimal("0"),
        level=result.level or "QUALIFIED",
        rank=rank,
        indicators=indicators,
        project_contributions=project_contributions
    )


@router.get("/user/{user_id}", response_model=PersonalPerformanceResponse, status_code=status.HTTP_200_OK)
def get_user_performance(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    period_id: Optional[int] = Query(None, description="周期ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    查看指定人员绩效（权限控制）
    """
    # 检查权限（只能查看自己或下属的绩效）
    if not _check_performance_view_permission(current_user, user_id, db):
        raise HTTPException(status_code=403, detail="您没有权限查看此用户的绩效")

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 获取周期
    if period_id:
        period = db.query(PerformancePeriod).filter(PerformancePeriod.id == period_id).first()
    else:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.status == "FINALIZED"
        ).order_by(desc(PerformancePeriod.end_date)).first()

    if not period:
        raise HTTPException(status_code=404, detail="未找到考核周期")

    result = db.query(PerformanceResult).filter(
        PerformanceResult.period_id == period.id,
        PerformanceResult.user_id == user_id
    ).first()

    if not result:
        return PersonalPerformanceResponse(
            user_id=user_id,
            user_name=target_user.real_name or target_user.username,
            period_id=period.id,
            period_name=period.period_name,
            period_type=period.period_type,
            start_date=period.start_date,
            end_date=period.end_date,
            total_score=Decimal("0"),
            level="QUALIFIED",
            indicators=[],
            project_contributions=[]
        )

    # 获取指标明细
    indicators = []
    if result.indicator_scores:
        for ind_id, score in result.indicator_scores.items():
            indicator = db.query(PerformanceIndicator).filter(PerformanceIndicator.id == int(ind_id)).first()
            if indicator:
                indicators.append({
                    "indicator_id": indicator.id,
                    "indicator_name": indicator.indicator_name,
                    "indicator_type": indicator.indicator_type,
                    "score": float(score),
                    "weight": float(indicator.weight) if indicator.weight else 0
                })

    # 获取项目贡献
    contributions = db.query(ProjectContribution).filter(
        ProjectContribution.period_id == period.id,
        ProjectContribution.user_id == user_id
    ).all()

    project_contributions = []
    for contrib in contributions:
        project = db.query(Project).filter(Project.id == contrib.project_id).first()
        project_contributions.append({
            "project_id": contrib.project_id,
            "project_name": project.project_name if project else None,
            "contribution_score": float(contrib.contribution_score) if contrib.contribution_score else 0,
            "work_hours": float(contrib.hours_spent) if contrib.hours_spent else 0,
            "task_count": contrib.task_count or 0
        })

    # 计算排名
    rank = None
    all_results = db.query(PerformanceResult).filter(
        PerformanceResult.period_id == period.id
    ).order_by(desc(PerformanceResult.total_score)).all()

    for idx, r in enumerate(all_results, 1):
        if r.user_id == user_id:
            rank = idx
            break

    return PersonalPerformanceResponse(
        user_id=user_id,
        user_name=target_user.real_name or target_user.username,
        period_id=period.id,
        period_name=period.period_name,
        period_type=period.period_type,
        start_date=period.start_date,
        end_date=period.end_date,
        total_score=result.total_score or Decimal("0"),
        level=result.level or "QUALIFIED",
        rank=rank,
        indicators=indicators,
        project_contributions=project_contributions
    )


@router.get("/trends/{user_id}", response_model=PerformanceTrendResponse, status_code=status.HTTP_200_OK)
def get_performance_trends(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    period_type: str = Query("MONTHLY", description="周期类型"),
    periods_count: int = Query(6, ge=1, le=12, description="查询期数"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    绩效趋势分析（多期对比）
    """
    # 检查权限（只能查看自己或下属的绩效）
    if not _check_performance_view_permission(current_user, user_id, db):
        raise HTTPException(status_code=403, detail="您没有权限查看此用户的绩效")

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 获取最近的几个周期
    periods = db.query(PerformancePeriod).filter(
        PerformancePeriod.period_type == period_type,
        PerformancePeriod.status == "FINALIZED"
    ).order_by(desc(PerformancePeriod.end_date)).limit(periods_count).all()

    periods_data = []
    scores = []

    for period in periods:
        result = db.query(PerformanceResult).filter(
            PerformanceResult.period_id == period.id,
            PerformanceResult.user_id == user_id
        ).first()

        score = float(result.total_score) if result and result.total_score else 0
        scores.append(score)

        periods_data.append({
            "period_id": period.id,
            "period_name": period.period_name,
            "start_date": period.start_date.isoformat(),
            "end_date": period.end_date.isoformat(),
            "score": score,
            "level": result.level if result else "QUALIFIED"
        })

    # 计算趋势
    if len(scores) >= 2:
        recent_avg = sum(scores[:3]) / min(3, len(scores))
        earlier_avg = sum(scores[-3:]) / min(3, len(scores[-3:]))
        if recent_avg > earlier_avg * 1.05:
            trend_direction = "UP"
        elif recent_avg < earlier_avg * 0.95:
            trend_direction = "DOWN"
        else:
            trend_direction = "STABLE"
    else:
        trend_direction = "STABLE"

    avg_score = Decimal(str(sum(scores) / len(scores))) if scores else Decimal("0")
    max_score = Decimal(str(max(scores))) if scores else Decimal("0")
    min_score = Decimal(str(min(scores))) if scores else Decimal("0")

    return PerformanceTrendResponse(
        user_id=user_id,
        user_name=target_user.real_name or target_user.username,
        periods=periods_data,
        trend_direction=trend_direction,
        avg_score=avg_score,
        max_score=max_score,
        min_score=min_score
    )




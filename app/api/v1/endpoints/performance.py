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


# ==================== 团队/部门绩效 ====================

@router.get("/team/{team_id}", response_model=TeamPerformanceResponse, status_code=status.HTTP_200_OK)
def get_team_performance(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    period_id: Optional[int] = Query(None, description="周期ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    团队绩效汇总（平均分/排名）
    """
    # 获取团队名称
    team_name = _get_team_name(db, team_id)

    # 获取团队成员
    member_ids = _get_team_members(db, team_id)

    # 获取周期
    if period_id:
        period = db.query(PerformancePeriod).filter(PerformancePeriod.id == period_id).first()
    else:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.status == "FINALIZED"
        ).order_by(desc(PerformancePeriod.end_date)).first()
    
    # 获取团队成员绩效
    results = db.query(PerformanceResult).filter(
        PerformanceResult.period_id == period.id,
        PerformanceResult.user_id.in_(member_ids)
    ).all()
    
    if not results:
        return TeamPerformanceResponse(
            team_id=team_id,
            team_name=team_name,
            period_id=period.id,
            period_name=period.period_name,
            member_count=0,
            avg_score=Decimal("0"),
            max_score=Decimal("0"),
            min_score=Decimal("0"),
            level_distribution={},
            members=[]
        )
    
    scores = [float(r.total_score) if r.total_score else 0 for r in results]
    avg_score = Decimal(str(sum(scores) / len(scores))) if scores else Decimal("0")
    max_score = Decimal(str(max(scores))) if scores else Decimal("0")
    min_score = Decimal(str(min(scores))) if scores else Decimal("0")
    
    # 等级分布
    level_distribution = {}
    for r in results:
        level = r.level or "QUALIFIED"
        level_distribution[level] = level_distribution.get(level, 0) + 1
    
    # 成员列表
    members = []
    for r in results:
        user = db.query(User).filter(User.id == r.user_id).first()
        members.append({
            "user_id": r.user_id,
            "user_name": user.real_name or user.username if user else None,
            "score": float(r.total_score) if r.total_score else 0,
            "level": r.level or "QUALIFIED"
        })
    
    # 按分数排序
    members.sort(key=lambda x: x["score"], reverse=True)
    
    return TeamPerformanceResponse(
        team_id=team_id,
        team_name=team_name,
        period_id=period.id,
        period_name=period.period_name,
        member_count=len(results),
        avg_score=avg_score,
        max_score=max_score,
        min_score=min_score,
        level_distribution=level_distribution,
        members=members
    )


@router.get("/department/{dept_id}", response_model=DepartmentPerformanceResponse, status_code=status.HTTP_200_OK)
def get_department_performance(
    *,
    db: Session = Depends(deps.get_db),
    dept_id: int,
    period_id: Optional[int] = Query(None, description="周期ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    部门绩效汇总（等级分布）
    """
    # 获取部门名称
    department_name = _get_department_name(db, dept_id)

    # 获取部门成员
    member_ids = _get_department_members(db, dept_id)

    if period_id:
        period = db.query(PerformancePeriod).filter(PerformancePeriod.id == period_id).first()
    else:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.status == "FINALIZED"
        ).order_by(desc(PerformancePeriod.end_date)).first()

    if not period:
        raise HTTPException(status_code=404, detail="未找到考核周期")

    results = db.query(PerformanceResult).filter(
        PerformanceResult.period_id == period.id,
        PerformanceResult.department_id == dept_id
    ).all()

    if not results:
        return DepartmentPerformanceResponse(
            department_id=dept_id,
            department_name=department_name,
            period_id=period.id,
            period_name=period.period_name,
            member_count=0,
            avg_score=Decimal("0"),
            level_distribution={},
            teams=[]
        )
    
    scores = [float(r.total_score) if r.total_score else 0 for r in results]
    avg_score = Decimal(str(sum(scores) / len(scores))) if scores else Decimal("0")
    
    # 等级分布
    level_distribution = {}
    for r in results:
        level = r.level or "QUALIFIED"
        level_distribution[level] = level_distribution.get(level, 0) + 1

    # 获取团队列表（使用子部门）
    from app.models.organization import Department
    sub_teams = db.query(Department).filter(
        Department.parent_id == dept_id
    ).all()
    teams = [{"team_id": t.id, "team_name": t.name} for t in sub_teams]

    return DepartmentPerformanceResponse(
        department_id=dept_id,
        department_name=department_name,
        period_id=period.id,
        period_name=period.period_name,
        member_count=len(results),
        avg_score=avg_score,
        level_distribution=level_distribution,
        teams=teams
    )


@router.get("/ranking", response_model=PerformanceRankingResponse, status_code=status.HTTP_200_OK)
def get_performance_ranking(
    *,
    db: Session = Depends(deps.get_db),
    ranking_type: str = Query("COMPANY", description="排行榜类型：TEAM/DEPARTMENT/COMPANY"),
    period_id: Optional[int] = Query(None, description="周期ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    绩效排行榜（团队/部门/公司）
    """
    if period_id:
        period = db.query(PerformancePeriod).filter(PerformancePeriod.id == period_id).first()
    else:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.status == "FINALIZED"
        ).order_by(desc(PerformancePeriod.end_date)).first()
    
    if not period:
        raise HTTPException(status_code=404, detail="未找到考核周期")
    
    rankings = []
    
    if ranking_type == "COMPANY":
        # 公司排行榜
        results = db.query(PerformanceResult).filter(
            PerformanceResult.period_id == period.id
        ).order_by(desc(PerformanceResult.total_score)).limit(100).all()
        
        for idx, result in enumerate(results, 1):
            user = db.query(User).filter(User.id == result.user_id).first()
            rankings.append({
                "rank": idx,
                "user_id": result.user_id,
                "user_name": user.real_name or user.username if user else None,
                "department_name": result.department_name,
                "score": float(result.total_score) if result.total_score else 0,
                "level": result.level or "QUALIFIED"
            })
    
    elif ranking_type == "TEAM":
        # 团队排行榜：按部门统计平均分
        from app.models.organization import Department
        departments = db.query(Department).all()

        for dept in departments:
            dept_results = db.query(PerformanceResult).filter(
                PerformanceResult.period_id == period.id,
                PerformanceResult.department_id == dept.id
            ).all()

            if dept_results:
                avg_score = sum(float(r.total_score or 0) for r in dept_results) / len(dept_results)
                rankings.append({
                    "rank": 0,  # 稍后填充
                    "entity_id": dept.id,
                    "entity_name": dept.name,
                    "score": round(avg_score, 2),
                    "member_count": len(dept_results)
                })

        # 排序并填充排名
        rankings.sort(key=lambda x: x["score"], reverse=True)
        for idx, r in enumerate(rankings, 1):
            r["rank"] = idx

    elif ranking_type == "DEPARTMENT":
        # 部门排行榜：与团队排行榜类似，但包含更多信息
        from app.models.organization import Department
        departments = db.query(Department).all()

        for dept in departments:
            dept_results = db.query(PerformanceResult).filter(
                PerformanceResult.period_id == period.id,
                PerformanceResult.department_id == dept.id
            ).all()

            if dept_results:
                avg_score = sum(float(r.total_score or 0) for r in dept_results) / len(dept_results)

                # 等级分布
                level_dist = {}
                for r in dept_results:
                    level = r.level or "QUALIFIED"
                    level_dist[level] = level_dist.get(level, 0) + 1

                rankings.append({
                    "rank": 0,  # 稍后填充
                    "entity_id": dept.id,
                    "entity_name": dept.name,
                    "score": round(avg_score, 2),
                    "member_count": len(dept_results),
                    "level_distribution": level_dist
                })

        # 排序并填充排名
        rankings.sort(key=lambda x: x["score"], reverse=True)
        for idx, r in enumerate(rankings, 1):
            r["rank"] = idx
    
    return PerformanceRankingResponse(
        ranking_type=ranking_type,
        period_id=period.id,
        period_name=period.period_name,
        rankings=rankings
    )


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


# ==================== 新绩效系统 - 员工端 API ====================

@router.post("/monthly-summary", response_model=MonthlyWorkSummaryResponse, status_code=status.HTTP_201_CREATED)
def create_monthly_work_summary(
    *,
    db: Session = Depends(deps.get_db),
    summary_in: MonthlyWorkSummaryCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    员工创建月度工作总结（提交）
    """
    # 检查是否已存在该周期的总结
    existing = db.query(MonthlyWorkSummary).filter(
        MonthlyWorkSummary.employee_id == current_user.id,
        MonthlyWorkSummary.period == summary_in.period
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"您已提交过 {summary_in.period} 的工作总结"
        )

    # 创建工作总结
    summary = MonthlyWorkSummary(
        employee_id=current_user.id,
        period=summary_in.period,
        work_content=summary_in.work_content,
        self_evaluation=summary_in.self_evaluation,
        highlights=summary_in.highlights,
        problems=summary_in.problems,
        next_month_plan=summary_in.next_month_plan,
        status='SUBMITTED',
        submit_date=datetime.now()
    )

    db.add(summary)
    db.commit()
    db.refresh(summary)

    # 创建待评价任务（通知部门经理和项目经理）
    PerformanceService.create_evaluation_tasks(db, summary)

    return summary


@router.put("/monthly-summary/draft", response_model=MonthlyWorkSummaryResponse, status_code=status.HTTP_200_OK)
def save_monthly_summary_draft(
    *,
    db: Session = Depends(deps.get_db),
    period: str = Query(..., description="评价周期 (YYYY-MM)"),
    summary_update: MonthlyWorkSummaryUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    员工保存工作总结草稿
    """
    # 查找现有草稿
    summary = db.query(MonthlyWorkSummary).filter(
        MonthlyWorkSummary.employee_id == current_user.id,
        MonthlyWorkSummary.period == period
    ).first()

    if not summary:
        # 创建新草稿
        summary = MonthlyWorkSummary(
            employee_id=current_user.id,
            period=period,
            work_content=summary_update.work_content or "",
            self_evaluation=summary_update.self_evaluation or "",
            highlights=summary_update.highlights,
            problems=summary_update.problems,
            next_month_plan=summary_update.next_month_plan,
            status='DRAFT'
        )
        db.add(summary)
    else:
        # 更新草稿（只能更新DRAFT状态的）
        if summary.status != 'DRAFT':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只能更新草稿状态的工作总结"
            )

        # 更新字段
        if summary_update.work_content is not None:
            summary.work_content = summary_update.work_content
        if summary_update.self_evaluation is not None:
            summary.self_evaluation = summary_update.self_evaluation
        if summary_update.highlights is not None:
            summary.highlights = summary_update.highlights
        if summary_update.problems is not None:
            summary.problems = summary_update.problems
        if summary_update.next_month_plan is not None:
            summary.next_month_plan = summary_update.next_month_plan

    db.commit()
    db.refresh(summary)

    return summary


@router.get("/monthly-summary/history", response_model=List[MonthlyWorkSummaryListItem], status_code=status.HTTP_200_OK)
def get_monthly_summary_history(
    *,
    db: Session = Depends(deps.get_db),
    limit: int = Query(12, ge=1, le=24, description="获取最近N个月"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    员工查看历史工作总结
    """
    summaries = db.query(MonthlyWorkSummary).filter(
        MonthlyWorkSummary.employee_id == current_user.id
    ).order_by(desc(MonthlyWorkSummary.period)).limit(limit).all()

    result = []
    for summary in summaries:
        # 统计评价数量
        eval_count = db.query(PerformanceEvaluationRecord).filter(
            PerformanceEvaluationRecord.summary_id == summary.id,
            PerformanceEvaluationRecord.status == 'COMPLETED'
        ).count()

        result.append(MonthlyWorkSummaryListItem(
            id=summary.id,
            period=summary.period,
            status=summary.status,
            submit_date=summary.submit_date,
            evaluation_count=eval_count,
            created_at=summary.created_at
        ))

    return result


@router.get("/my-performance", response_model=MyPerformanceResponse, status_code=status.HTTP_200_OK)
def get_my_performance_new(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    员工查看我的绩效（新系统）
    """
    # 获取最新周期
    current_date = date.today()
    current_period = current_date.strftime("%Y-%m")

    # 获取当前周期的工作总结
    current_summary = db.query(MonthlyWorkSummary).filter(
        MonthlyWorkSummary.employee_id == current_user.id,
        MonthlyWorkSummary.period == current_period
    ).first()

    # 当前评价状态
    if current_summary:
        # 获取部门经理评价
        dept_eval = db.query(PerformanceEvaluationRecord).filter(
            PerformanceEvaluationRecord.summary_id == current_summary.id,
            PerformanceEvaluationRecord.evaluator_type == 'DEPT_MANAGER'
        ).first()

        dept_evaluation_status = {
            "status": dept_eval.status if dept_eval else "PENDING",
            "evaluator": dept_eval.evaluator.real_name if dept_eval and dept_eval.evaluator else "未知",
            "score": dept_eval.score if dept_eval and dept_eval.status == 'COMPLETED' else None
        }

        # 获取项目经理评价
        project_evals = db.query(PerformanceEvaluationRecord).filter(
            PerformanceEvaluationRecord.summary_id == current_summary.id,
            PerformanceEvaluationRecord.evaluator_type == 'PROJECT_MANAGER'
        ).all()

        project_evaluations_status = []
        for proj_eval in project_evals:
            project_evaluations_status.append({
                "project_name": proj_eval.project.project_name if proj_eval.project else "未知项目",
                "status": proj_eval.status,
                "evaluator": proj_eval.evaluator.real_name if proj_eval.evaluator else "未知",
                "score": proj_eval.score if proj_eval.status == 'COMPLETED' else None,
                "weight": proj_eval.project_weight
            })

        current_status = {
            "period": current_period,
            "summary_status": current_summary.status,
            "dept_evaluation": dept_evaluation_status,
            "project_evaluations": project_evaluations_status
        }
    else:
        current_status = {
            "period": current_period,
            "summary_status": "NOT_SUBMITTED",
            "dept_evaluation": {"status": "PENDING", "evaluator": "未知", "score": None},
            "project_evaluations": []
        }

    # 计算最新绩效结果
    latest_result = None
    if current_summary and current_summary.status == 'COMPLETED':
        score_result = PerformanceService.calculate_final_score(
            db, current_summary.id, current_summary.period
        )
        if score_result:
            latest_result = {
                "period": current_summary.period,
                "final_score": score_result['final_score'],
                "level": PerformanceService.get_score_level(score_result['final_score']),
                "dept_score": score_result['dept_score'],
                "project_score": score_result['project_score']
            }

    # 季度趋势（最近3个月）
    quarterly_trend = []
    for i in range(3):
        past_period = (date.today() - timedelta(days=30*i)).strftime("%Y-%m")
        past_summary = db.query(MonthlyWorkSummary).filter(
            MonthlyWorkSummary.employee_id == current_user.id,
            MonthlyWorkSummary.period == past_period,
            MonthlyWorkSummary.status == 'COMPLETED'
        ).first()

        if past_summary:
            score_result = PerformanceService.calculate_final_score(
                db, past_summary.id, past_summary.period
            )
            if score_result:
                quarterly_trend.append({
                    "period": past_summary.period,
                    "score": score_result['final_score']
                })

    # 历史记录（最近3个月）
    history = PerformanceService.get_historical_performance(db, current_user.id, 3)

    return MyPerformanceResponse(
        current_status=current_status,
        latest_result=latest_result,
        quarterly_trend=quarterly_trend,
        history=history
    )


# ==================== 新绩效系统 - 经理端 API ====================

@router.get("/evaluation-tasks", response_model=EvaluationTaskListResponse, status_code=status.HTTP_200_OK)
def get_evaluation_tasks(
    *,
    db: Session = Depends(deps.get_db),
    period: Optional[str] = Query(None, description="评价周期 (YYYY-MM)"),
    status_filter: Optional[str] = Query(None, description="状态筛选: PENDING/COMPLETED"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    经理查看待评价任务列表（带权限过滤）
    """
    if not period:
        period = date.today().strftime("%Y-%m")

    # 获取当前用户可管理的员工列表
    manageable_employee_ids = PerformanceService.get_manageable_employees(
        db, current_user, period
    )

    if not manageable_employee_ids:
        # 如果不是经理角色，返回空列表
        return EvaluationTaskListResponse(
            total=0,
            pending_count=0,
            completed_count=0,
            tasks=[]
        )

    # 获取待评价的工作总结（只包含可管理的员工）
    summaries = db.query(MonthlyWorkSummary).filter(
        MonthlyWorkSummary.period == period,
        MonthlyWorkSummary.employee_id.in_(manageable_employee_ids),
        MonthlyWorkSummary.status.in_(['SUBMITTED', 'EVALUATING', 'COMPLETED'])
    ).all()

    # 获取当前用户的经理角色信息
    manager_roles = PerformanceService.get_user_manager_roles(db, current_user)

    tasks = []
    total = 0
    pending_count = 0
    completed_count = 0

    for summary in summaries:
        # 检查当前用户是否已评价
        my_eval = db.query(PerformanceEvaluationRecord).filter(
            PerformanceEvaluationRecord.summary_id == summary.id,
            PerformanceEvaluationRecord.evaluator_id == current_user.id
        ).first()

        if my_eval:
            eval_status = my_eval.status
            if eval_status == 'COMPLETED':
                completed_count += 1
            else:
                pending_count += 1
        else:
            # 创建待评价记录
            eval_status = 'PENDING'
            pending_count += 1

        # 判断是否需要筛选
        if status_filter:
            if status_filter == 'PENDING' and eval_status != 'PENDING':
                continue
            if status_filter == 'COMPLETED' and eval_status != 'COMPLETED':
                continue

        # 获取员工信息
        employee = summary.employee

        # 计算截止日期（下月5号）
        year, month = map(int, summary.period.split('-'))
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        deadline = date(next_year, next_month, 5)

        # 判断评价类型和项目信息
        evaluation_type = "dept"
        project_id = None
        project_name = None

        if my_eval:
            if my_eval.evaluator_type == 'PROJECT_MANAGER':
                evaluation_type = "project"
                project_id = my_eval.project_id
                if project_id:
                    project = db.query(Project).get(project_id)
                    project_name = project.project_name if project else None

        task = EvaluationTaskItem(
            task_id=summary.id,
            employee_id=summary.employee_id,
            employee_name=employee.real_name if employee else "未知",
            employee_department=employee.department if employee else None,
            period=summary.period,
            evaluation_type=evaluation_type,
            project_id=project_id,
            project_name=project_name,
            status=eval_status,
            deadline=deadline,
            submit_date=summary.submit_date
        )
        tasks.append(task)
        total += 1

    return EvaluationTaskListResponse(
        total=total,
        pending_count=pending_count,
        completed_count=completed_count,
        tasks=tasks
    )


@router.get("/evaluation/{task_id}", response_model=EvaluationDetailResponse, status_code=status.HTTP_200_OK)
def get_evaluation_detail(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    经理查看评价详情（工作总结+历史绩效）
    """
    # 获取工作总结
    summary = db.query(MonthlyWorkSummary).filter(
        MonthlyWorkSummary.id == task_id
    ).first()

    if not summary:
        raise HTTPException(status_code=404, detail="工作总结不存在")

    # 获取员工信息
    employee = summary.employee
    employee_info = {
        "id": employee.id,
        "name": employee.real_name or employee.username,
        "department": employee.department if employee else None,
        "position": employee.position if employee else None
    }

    # 获取历史绩效（最近3个月）
    historical_performance = PerformanceService.get_historical_performance(
        db, summary.employee_id, 3
    )

    # 获取我的评价记录
    my_evaluation = db.query(PerformanceEvaluationRecord).filter(
        PerformanceEvaluationRecord.summary_id == summary.id,
        PerformanceEvaluationRecord.evaluator_id == current_user.id
    ).first()

    return EvaluationDetailResponse(
        summary=summary,
        employee_info=employee_info,
        historical_performance=historical_performance,
        my_evaluation=my_evaluation
    )


@router.post("/evaluation/{task_id}", response_model=PerformanceEvaluationRecordResponse, status_code=status.HTTP_201_CREATED)
def submit_evaluation(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    evaluation_in: PerformanceEvaluationRecordCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    经理提交评价
    """
    # 获取工作总结
    summary = db.query(MonthlyWorkSummary).filter(
        MonthlyWorkSummary.id == task_id
    ).first()

    if not summary:
        raise HTTPException(status_code=404, detail="工作总结不存在")

    # 检查是否已评价
    existing_eval = db.query(PerformanceEvaluationRecord).filter(
        PerformanceEvaluationRecord.summary_id == task_id,
        PerformanceEvaluationRecord.evaluator_id == current_user.id
    ).first()

    if existing_eval and existing_eval.status == 'COMPLETED':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已完成该评价"
        )

    # 判断评价人类型（部门经理/项目经理）
    evaluator_type = _get_evaluator_type(current_user, db)

    if existing_eval:
        # 更新评价
        existing_eval.score = evaluation_in.score
        existing_eval.comment = evaluation_in.comment
        existing_eval.project_id = evaluation_in.project_id
        existing_eval.project_weight = evaluation_in.project_weight
        existing_eval.status = 'COMPLETED'
        existing_eval.evaluated_at = datetime.now()
        evaluation = existing_eval
    else:
        # 创建新评价
        evaluation = PerformanceEvaluationRecord(
            summary_id=task_id,
            evaluator_id=current_user.id,
            evaluator_type=evaluator_type,
            project_id=evaluation_in.project_id,
            project_weight=evaluation_in.project_weight,
            score=evaluation_in.score,
            comment=evaluation_in.comment,
            status='COMPLETED',
            evaluated_at=datetime.now()
        )
        db.add(evaluation)

    # 更新工作总结状态
    if summary.status == 'SUBMITTED':
        summary.status = 'EVALUATING'

    # 检查是否所有评价都已完成
    all_evals = db.query(PerformanceEvaluationRecord).filter(
        PerformanceEvaluationRecord.summary_id == task_id
    ).all()

    if all([e.status == 'COMPLETED' for e in all_evals]):
        summary.status = 'COMPLETED'

    db.commit()
    db.refresh(evaluation)

    return evaluation


# ==================== 新绩效系统 - HR端 API ====================

@router.get("/weight-config", response_model=EvaluationWeightConfigListResponse, status_code=status.HTTP_200_OK)
def get_weight_config(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("performance:manage")),
) -> Any:
    """
    HR查看权重配置（当前+历史）
    """
    # 获取当前配置（最新的）
    current_config = db.query(EvaluationWeightConfig).order_by(
        desc(EvaluationWeightConfig.effective_date)
    ).first()

    if not current_config:
        # 创建默认配置
        current_config = EvaluationWeightConfig(
            dept_manager_weight=50,
            project_manager_weight=50,
            effective_date=date.today(),
            operator_id=current_user.id,
            reason="系统默认配置"
        )
        db.add(current_config)
        db.commit()
        db.refresh(current_config)

    # 获取历史配置
    history = db.query(EvaluationWeightConfig).order_by(
        desc(EvaluationWeightConfig.effective_date)
    ).offset(1).limit(10).all()

    return EvaluationWeightConfigListResponse(
        current=current_config,
        history=history
    )


@router.put("/weight-config", response_model=EvaluationWeightConfigResponse, status_code=status.HTTP_201_CREATED)
def update_weight_config(
    *,
    db: Session = Depends(deps.get_db),
    config_in: EvaluationWeightConfigCreate,
    current_user: User = Depends(security.require_permission("performance:manage")),
) -> Any:
    """
    HR更新权重配置
    """
    # 验证权重总和
    if config_in.dept_manager_weight + config_in.project_manager_weight != 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="权重总和必须等于100%"
        )

    # 创建新配置
    new_config = EvaluationWeightConfig(
        dept_manager_weight=config_in.dept_manager_weight,
        project_manager_weight=config_in.project_manager_weight,
        effective_date=config_in.effective_date,
        operator_id=current_user.id,
        reason=config_in.reason
    )

    db.add(new_config)
    db.commit()
    db.refresh(new_config)

    return new_config


# ==================== 绩效融合 API ====================

@router.get("/integrated/{user_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_integrated_performance(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    period: Optional[str] = Query(None, description="考核周期 (格式: YYYY-MM)"),
    period_id: Optional[int] = Query(None, description="周期ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取融合后的绩效结果
    融合公式: 综合得分 = 基础绩效得分 × 70% + 任职资格得分 × 30%
    """
    # 权限检查：只能查看自己的或下属的绩效
    if user_id != current_user.id:
        # 检查是否是当前用户的下属
        manager_roles = PerformanceService.get_user_manager_roles(db, current_user)
        if not manager_roles.get('is_dept_manager') and not manager_roles.get('is_project_manager'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看该用户的绩效"
            )

    if period:
        result = PerformanceIntegrationService.calculate_integrated_score(
            db, user_id, period
        )
    elif period_id:
        result = PerformanceIntegrationService.get_integrated_performance_for_period(
            db, user_id, period_id
        )
    else:
        # 获取最新周期
        result = PerformanceIntegrationService.get_integrated_performance_for_period(
            db, user_id, None
        )

    if not result:
        raise HTTPException(status_code=404, detail="未找到绩效数据")

    return ResponseModel(code=200, message="获取成功", data=result)


@router.post("/calculate-integrated", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def calculate_integrated_performance(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int = Query(..., description="用户ID"),
    period: str = Query(..., description="考核周期 (格式: YYYY-MM)"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    计算融合绩效
    仅HR和管理层可调用
    """
    # 权限检查
    manager_roles = PerformanceService.get_user_manager_roles(db, current_user)
    if not (manager_roles.get('is_dept_manager') or 
            manager_roles.get('is_project_manager') or
            current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权执行此操作"
        )

    result = PerformanceIntegrationService.calculate_integrated_score(
        db, user_id, period
    )

    if not result:
        raise HTTPException(status_code=404, detail="未找到绩效数据")

    return ResponseModel(code=200, message="计算成功", data=result)

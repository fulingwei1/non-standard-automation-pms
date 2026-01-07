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
    PerformanceRankingSnapshot
)
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.performance import (
    PersonalPerformanceResponse, PerformanceTrendResponse,
    TeamPerformanceResponse, DepartmentPerformanceResponse, PerformanceRankingResponse,
    ProjectPerformanceResponse, ProjectProgressReportResponse, PerformanceCompareResponse
)

router = APIRouter()


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
    # TODO: 检查权限（只能查看自己或下属的绩效）
    
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
    # TODO: 权限检查
    
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
    # TODO: 获取团队信息
    # team = db.query(Team).filter(Team.id == team_id).first()
    # if not team:
    #     raise HTTPException(status_code=404, detail="团队不存在")
    
    # 获取周期
    if period_id:
        period = db.query(PerformancePeriod).filter(PerformancePeriod.id == period_id).first()
    else:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.status == "FINALIZED"
        ).order_by(desc(PerformancePeriod.end_date)).first()
    
    if not period:
        raise HTTPException(status_code=404, detail="未找到考核周期")
    
    # TODO: 获取团队成员
    # team_members = db.query(User).filter(User.team_id == team_id).all()
    # member_ids = [m.id for m in team_members]
    
    # 临时：使用部门ID作为团队ID
    member_ids = [current_user.id]  # TODO: 从团队表获取
    
    # 获取团队成员绩效
    results = db.query(PerformanceResult).filter(
        PerformanceResult.period_id == period.id,
        PerformanceResult.user_id.in_(member_ids)
    ).all()
    
    if not results:
        return TeamPerformanceResponse(
            team_id=team_id,
            team_name="未知团队",  # TODO: 从团队表获取
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
        team_name="未知团队",  # TODO
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
    # TODO: 获取部门信息
    # department = db.query(Department).filter(Department.id == dept_id).first()
    
    if period_id:
        period = db.query(PerformancePeriod).filter(PerformancePeriod.id == period_id).first()
    else:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.status == "FINALIZED"
        ).order_by(desc(PerformancePeriod.end_date)).first()
    
    if not period:
        raise HTTPException(status_code=404, detail="未找到考核周期")
    
    # TODO: 获取部门成员
    # dept_members = db.query(User).filter(User.department_id == dept_id).all()
    # member_ids = [m.id for m in dept_members]
    member_ids = [current_user.id]  # TODO
    
    results = db.query(PerformanceResult).filter(
        PerformanceResult.period_id == period.id,
        PerformanceResult.department_id == dept_id
    ).all()
    
    if not results:
        return DepartmentPerformanceResponse(
            department_id=dept_id,
            department_name="未知部门",  # TODO
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
    
    # TODO: 获取团队列表
    teams = []
    
    return DepartmentPerformanceResponse(
        department_id=dept_id,
        department_name="未知部门",  # TODO
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
        # TODO: 团队排行榜
        pass
    
    elif ranking_type == "DEPARTMENT":
        # TODO: 部门排行榜
        pass
    
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
    
    # TODO: 从进度跟踪模块获取数据
    progress_summary = {
        "overall_progress": 0,
        "completed_tasks": 0,
        "total_tasks": 0,
        "on_schedule": True
    }
    
    # TODO: 获取成员贡献
    member_contributions = []
    
    # TODO: 获取关键成果
    key_achievements = []
    
    # TODO: 获取风险和问题
    risks_and_issues = []
    
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

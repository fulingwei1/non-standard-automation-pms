# -*- coding: utf-8 -*-
"""
战略管理 API 端点 - 仪表板
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.strategy import (
    ExecutionStatusResponse,
    MyStrategyResponse,
    StrategyOverviewResponse,
)
from app.services import strategy as strategy_service

router = APIRouter()


@router.get("/overview/{strategy_id}", response_model=StrategyOverviewResponse)
def get_strategy_overview(
    strategy_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取战略概览

    返回战略基本信息、健康度、KPI 完成情况等概览数据
    """
    # 获取战略详情
    detail = strategy_service.get_strategy_detail(db, strategy_id)
    if not detail:
        return StrategyOverviewResponse(
            strategy_id=strategy_id,
            strategy_name="",
            year=0,
            status="",
            health_score=None,
            health_level=None,
            csf_count=0,
            kpi_count=0,
            annual_work_count=0,
            kpi_on_track=0,
            kpi_at_risk=0,
            kpi_off_track=0,
        )

    # 获取健康度详情
    health_summary = strategy_service.get_health_score_summary(db, strategy_id)

    # 统计 KPI 状态
    kpi_on_track = 0
    kpi_at_risk = 0
    kpi_off_track = 0

    for dim in health_summary.dimensions:
        kpi_on_track += dim.kpi_on_track
        kpi_at_risk += dim.kpi_at_risk
        kpi_off_track += dim.kpi_off_track

    return StrategyOverviewResponse(
        strategy_id=detail.id,
        strategy_name=detail.name,
        year=detail.year,
        status=detail.status,
        health_score=health_summary.overall_score,
        health_level=health_summary.overall_level,
        csf_count=detail.csf_count,
        kpi_count=detail.kpi_count,
        annual_work_count=detail.annual_work_count,
        kpi_on_track=kpi_on_track,
        kpi_at_risk=kpi_at_risk,
        kpi_off_track=kpi_off_track,
    )


@router.get("/my-strategy", response_model=MyStrategyResponse)
def get_my_strategy(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    获取我的战略相关信息

    返回当前用户负责的 KPI、重点工作等
    """
    from app.models.strategy import CSF, KPI, AnnualKeyWork

    user_id = current_user.id

    # 获取当前生效的战略
    active_strategy = strategy_service.get_active_strategy(db)
    if not active_strategy:
        return MyStrategyResponse(
            strategy_id=None,
            strategy_name=None,
            my_kpis=[],
            my_annual_works=[],
            my_personal_kpis=[],
            total_kpi_count=0,
            completed_kpi_count=0,
        )

    # 获取我负责的公司 KPI
    my_kpis = db.query(KPI).join(CSF).filter(
        CSF.strategy_id == active_strategy.id,
        CSF.is_active == True,
        KPI.is_active == True,
        KPI.owner_user_id == user_id
    ).all()

    # 获取我负责的年度重点工作
    my_annual_works = db.query(AnnualKeyWork).join(CSF).filter(
        CSF.strategy_id == active_strategy.id,
        CSF.is_active == True,
        AnnualKeyWork.is_active == True,
        AnnualKeyWork.owner_user_id == user_id
    ).all()

    # 获取我的个人 KPI
    my_personal_kpis, _ = strategy_service.list_personal_kpis(
        db, user_id=user_id, year=active_strategy.year, limit=100
    )

    # 统计完成情况
    total_count = len(my_personal_kpis)
    completed_count = sum(1 for kpi in my_personal_kpis if kpi.status == "COMPLETED")

    return MyStrategyResponse(
        strategy_id=active_strategy.id,
        strategy_name=active_strategy.name,
        my_kpis=[
            {
                "id": kpi.id,
                "code": kpi.code,
                "name": kpi.name,
                "target_value": kpi.target_value,
                "current_value": kpi.current_value,
                "completion_rate": strategy_service.calculate_kpi_completion_rate(kpi),
            }
            for kpi in my_kpis
        ],
        my_annual_works=[
            {
                "id": work.id,
                "code": work.code,
                "name": work.name,
                "status": work.status,
                "progress_percent": work.progress_percent,
            }
            for work in my_annual_works
        ],
        my_personal_kpis=[
            {
                "id": kpi.id,
                "code": kpi.code,
                "name": kpi.name,
                "target_value": kpi.target_value,
                "actual_value": kpi.actual_value,
                "status": kpi.status,
            }
            for kpi in my_personal_kpis
        ],
        total_kpi_count=total_count,
        completed_kpi_count=completed_count,
    )


@router.get("/execution-status/{strategy_id}", response_model=ExecutionStatusResponse)
def get_execution_status(
    strategy_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取执行状态

    按维度返回 KPI 和重点工作的执行状态
    """
    from app.models.strategy import CSF, KPI, AnnualKeyWork

    dimension_names = {
        "FINANCIAL": "财务维度",
        "CUSTOMER": "客户维度",
        "INTERNAL": "内部运营维度",
        "LEARNING": "学习成长维度",
    }

    items = []
    for dim_code, dim_name in dimension_names.items():
        # 统计 KPI
        kpis = db.query(KPI).join(CSF).filter(
            CSF.strategy_id == strategy_id,
            CSF.dimension == dim_code,
            CSF.is_active == True,
            KPI.is_active == True
        ).all()

        kpi_total = len(kpis)
        kpi_on_track = 0
        kpi_at_risk = 0
        kpi_off_track = 0

        for kpi in kpis:
            rate = strategy_service.calculate_kpi_completion_rate(kpi)
            if rate is None:
                continue
            if rate >= 80:
                kpi_on_track += 1
            elif rate >= 50:
                kpi_at_risk += 1
            else:
                kpi_off_track += 1

        # 统计年度重点工作
        works = db.query(AnnualKeyWork).join(CSF).filter(
            CSF.strategy_id == strategy_id,
            CSF.dimension == dim_code,
            CSF.is_active == True,
            AnnualKeyWork.is_active == True
        ).all()

        work_total = len(works)
        work_completed = sum(1 for w in works if w.status == "COMPLETED")
        work_in_progress = sum(1 for w in works if w.status == "IN_PROGRESS")
        work_not_started = sum(1 for w in works if w.status in ["NOT_STARTED", None])

        items.append({
            "dimension": dim_code,
            "dimension_name": dim_name,
            "kpi_total": kpi_total,
            "kpi_on_track": kpi_on_track,
            "kpi_at_risk": kpi_at_risk,
            "kpi_off_track": kpi_off_track,
            "work_total": work_total,
            "work_completed": work_completed,
            "work_in_progress": work_in_progress,
            "work_not_started": work_not_started,
        })

    return ExecutionStatusResponse(
        strategy_id=strategy_id,
        items=items,
    )


@router.get("/quick-stats", response_model=Dict[str, Any])
def get_quick_stats(
    db: Session = Depends(deps.get_db),
):
    """
    获取快速统计

    返回系统级的战略管理统计数据
    """
    from app.models.strategy import Strategy, CSF, KPI, AnnualKeyWork

    # 统计战略数量
    strategy_count = db.query(Strategy).filter(Strategy.is_active == True).count()
    active_strategy = strategy_service.get_active_strategy(db)

    # 统计 CSF 数量
    csf_count = 0
    kpi_count = 0
    work_count = 0

    if active_strategy:
        csf_count = db.query(CSF).filter(
            CSF.strategy_id == active_strategy.id,
            CSF.is_active == True
        ).count()

        kpi_count = db.query(KPI).join(CSF).filter(
            CSF.strategy_id == active_strategy.id,
            CSF.is_active == True,
            KPI.is_active == True
        ).count()

        work_count = db.query(AnnualKeyWork).join(CSF).filter(
            CSF.strategy_id == active_strategy.id,
            CSF.is_active == True,
            AnnualKeyWork.is_active == True
        ).count()

    return {
        "total_strategies": strategy_count,
        "active_strategy_id": active_strategy.id if active_strategy else None,
        "active_strategy_name": active_strategy.name if active_strategy else None,
        "csf_count": csf_count,
        "kpi_count": kpi_count,
        "annual_work_count": work_count,
    }

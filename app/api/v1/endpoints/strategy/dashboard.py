# -*- coding: utf-8 -*-
"""
战略管理 API 端点 - 仪表板

注意：此文件包含多个非标准dashboard端点：
- /overview/{strategy_id} - 特定战略概览
- /my-strategy - 用户个人战略信息
- /execution-status/{strategy_id} - 特定战略执行状态
- /quick-stats - 快速统计（类似dashboard）

这些端点不是典型的dashboard模式，更像是业务查询端点。
只有 /quick-stats 端点使用了基类重构。
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.common.dashboard.base import BaseDashboardEndpoint
from app.schemas.strategy import (
    ExecutionStatusResponse,
    MyStrategyDashboardResponse,
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


@router.get("/my-strategy", response_model=MyStrategyDashboardResponse)
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
        return MyStrategyDashboardResponse(
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
        CSF.is_active,
        KPI.is_active,
        KPI.owner_user_id == user_id
    ).all()

    # 获取我负责的年度重点工作
    my_annual_works = db.query(AnnualKeyWork).join(CSF).filter(
        CSF.strategy_id == active_strategy.id,
        CSF.is_active,
        AnnualKeyWork.is_active,
        AnnualKeyWork.owner_user_id == user_id
    ).all()

    # 获取我的个人 KPI（PersonalKPI 模型字段：id, kpi_name, target_value, actual_value, status，无 code）
    my_personal_kpis, _ = strategy_service.list_personal_kpis(
        db, user_id=user_id, year=active_strategy.year, limit=100
    )

    # 统计完成情况（PersonalKPI.status：PENDING/SELF_RATED/MANAGER_RATED/CONFIRMED）
    total_count = len(my_personal_kpis)
    completed_count = sum(1 for kpi in my_personal_kpis if getattr(kpi, "status", None) == "CONFIRMED")

    return MyStrategyDashboardResponse(
        strategy_id=active_strategy.id,
        strategy_name=active_strategy.name,
        my_kpis=[
            {
                "id": kpi.id,
                "code": kpi.code,
                "name": kpi.name,
                "target_value": float(kpi.target_value) if kpi.target_value is not None else None,
                "current_value": float(kpi.current_value) if kpi.current_value is not None else None,
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
                "code": f"PKPI-{kpi.id}",
                "name": kpi.kpi_name or "",
                "target_value": float(kpi.target_value) if kpi.target_value is not None else None,
                "actual_value": float(kpi.actual_value) if kpi.actual_value is not None else None,
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
            CSF.is_active,
            KPI.is_active
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
            CSF.is_active,
            AnnualKeyWork.is_active
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


class StrategyQuickStatsEndpoint(BaseDashboardEndpoint):
    """战略快速统计端点（使用基类）"""
    
    module_name = "strategy"
    permission_required = None
    
    def __init__(self):
        """初始化路由"""
        # 只注册quick-stats端点
        self.router = APIRouter()
        self._register_custom_routes()
    
    def _register_custom_routes(self):
        """注册quick-stats端点"""
        user_dependency = self._get_user_dependency()
        
        async def quick_stats_endpoint(
            db: Session = Depends(deps.get_db),
            current_user = Depends(user_dependency),
        ):
            return self._get_quick_stats_handler(db, current_user)
        
        self.router.add_api_route(
            "/quick-stats",
            quick_stats_endpoint,
            methods=["GET"],
            summary="获取快速统计",
            response_model=Dict[str, Any]
        )
    
    def get_dashboard_data(
        self,
        db: Session,
        current_user
    ) -> Dict[str, Any]:
        """
        获取快速统计
        返回系统级的战略管理统计数据
        """
        from app.models.strategy import Strategy, CSF, KPI, AnnualKeyWork

        # 统计战略数量
        strategy_count = db.query(Strategy).filter(Strategy.is_active).count()
        active_strategy = strategy_service.get_active_strategy(db)

        # 统计 CSF 数量
        csf_count = 0
        kpi_count = 0
        work_count = 0

        if active_strategy:
            csf_count = db.query(CSF).filter(
                CSF.strategy_id == active_strategy.id,
                CSF.is_active
            ).count()

            kpi_count = db.query(KPI).join(CSF).filter(
                CSF.strategy_id == active_strategy.id,
                CSF.is_active,
                KPI.is_active
            ).count()

            work_count = db.query(AnnualKeyWork).join(CSF).filter(
                CSF.strategy_id == active_strategy.id,
                CSF.is_active,
                AnnualKeyWork.is_active
            ).count()

        # 使用基类方法创建统计卡片
        stats = [
            self.create_stat_card(
                key="total_strategies",
                label="战略总数",
                value=strategy_count,
                unit="个",
                icon="strategy"
            ),
            self.create_stat_card(
                key="csf_count",
                label="关键成功因素",
                value=csf_count,
                unit="个",
                icon="csf"
            ),
            self.create_stat_card(
                key="kpi_count",
                label="KPI总数",
                value=kpi_count,
                unit="个",
                icon="kpi"
            ),
            self.create_stat_card(
                key="annual_work_count",
                label="年度重点工作",
                value=work_count,
                unit="个",
                icon="work"
            ),
        ]

        return {
            "stats": stats,
            "total_strategies": strategy_count,
            "active_strategy_id": active_strategy.id if active_strategy else None,
            "active_strategy_name": active_strategy.name if active_strategy else None,
            "csf_count": csf_count,
            "kpi_count": kpi_count,
            "annual_work_count": work_count,
        }
    
    def _get_quick_stats_handler(
        self,
        db: Session,
        current_user
    ) -> Dict[str, Any]:
        """快速统计处理器"""
        data = self.get_dashboard_data(db, current_user)
        # 移除stats字段，保持原有响应格式
        result = {k: v for k, v in data.items() if k != "stats"}
        return result


# 创建quick-stats端点实例
quick_stats_endpoint = StrategyQuickStatsEndpoint()

# 将quick-stats路由添加到主router
router.include_router(quick_stats_endpoint.router)

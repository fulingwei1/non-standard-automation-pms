# -*- coding: utf-8 -*-
"""
生产管理 Dashboard 适配器
"""

from datetime import date, datetime, timedelta
from typing import List

from sqlalchemy import case, func

from app.models.production import ProductionDailyReport, WorkOrder, Workshop
from app.schemas.dashboard import (
    DashboardStatCard,
    DashboardWidget,
    DetailedDashboardResponse,
)
from app.services.dashboard_adapter import DashboardAdapter, register_dashboard


@register_dashboard
class ProductionDashboardAdapter(DashboardAdapter):
    """生产管理工作台适配器"""

    @property
    def module_id(self) -> str:
        return "production"

    @property
    def module_name(self) -> str:
        return "生产管理"

    @property
    def supported_roles(self) -> List[str]:
        return ["production", "admin"]

    def get_stats(self) -> List[DashboardStatCard]:
        """获取统计卡片"""
        today = date.today()
        month_start = today.replace(day=1)

        # 统计车间数量
        workshop_count = (
            self.db.query(func.count(Workshop.id))
            .filter(Workshop.is_active == True)
            .scalar()
            or 0
        )

        # 统计本月工单
        work_order_stats = (
            self.db.query(
                func.count(WorkOrder.id).label("total"),
                func.sum(case((WorkOrder.status == "COMPLETED", 1), else_=0)).label(
                    "completed"
                ),
                func.sum(case((WorkOrder.status == "IN_PROGRESS", 1), else_=0)).label(
                    "in_progress"
                ),
            )
            .filter(WorkOrder.created_at >= month_start)
            .first()
        )

        total_orders = work_order_stats.total or 0
        completed_orders = work_order_stats.completed or 0
        in_progress_orders = work_order_stats.in_progress or 0

        # 计算产能利用率
        capacity_utilization = 0
        if total_orders > 0:
            capacity_utilization = round(
                (completed_orders + in_progress_orders) / total_orders * 100, 1
            )

        # 获取最近的日报数据计算质量合格率
        recent_reports = (
            self.db.query(ProductionDailyReport)
            .filter(ProductionDailyReport.report_date >= today - timedelta(days=30))
            .all()
        )

        pass_rate = 95.0  # 默认值
        if recent_reports:
            total_produced = sum(r.produced_quantity or 0 for r in recent_reports)
            total_defects = sum(r.defect_quantity or 0 for r in recent_reports)
            if total_produced > 0:
                pass_rate = round(
                    (total_produced - total_defects) / total_produced * 100, 1
                )

        return [
            DashboardStatCard(
                key="workshop_count",
                label="车间数量",
                value=workshop_count,
                unit="个",
                icon="workshop",
                color="blue",
            ),
            DashboardStatCard(
                key="total_orders",
                label="本月工单",
                value=total_orders,
                unit="个",
                icon="order",
                color="green",
            ),
            DashboardStatCard(
                key="in_progress_orders",
                label="进行中",
                value=in_progress_orders,
                unit="个",
                icon="progress",
                color="orange",
            ),
            DashboardStatCard(
                key="capacity_utilization",
                label="产能利用率",
                value=f"{capacity_utilization}%",
                icon="capacity",
                color="purple",
            ),
            DashboardStatCard(
                key="pass_rate",
                label="质量合格率",
                value=f"{pass_rate}%",
                icon="quality",
                color="cyan",
            ),
        ]

    def get_widgets(self) -> List[DashboardWidget]:
        """获取Widget列表"""
        return [
            DashboardWidget(
                widget_id="production_summary",
                widget_type="stats",
                title="生产概览",
                data={"message": "详细数据请查看详细模式"},
                order=1,
                span=24,
            )
        ]

    def get_detailed_data(self) -> DetailedDashboardResponse:
        """获取详细数据"""
        today = date.today()
        month_start = today.replace(day=1)

        # 统计数据（复用get_stats的逻辑）
        stats_cards = self.get_stats()
        summary = {card.key: card.value for card in stats_cards}

        return DetailedDashboardResponse(
            module=self.module_id,
            module_name=self.module_name,
            summary=summary,
            details={},
            generated_at=datetime.now(),
        )

# -*- coding: utf-8 -*-
"""
售前分析 Dashboard 适配器
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List

from sqlalchemy import func

from app.models.enums import LeadOutcomeEnum
from app.models.project import Project
from app.schemas.dashboard import (
    DashboardStatCard,
    DashboardWidget,
    DetailedDashboardResponse,
)
from app.services.dashboard_adapter import DashboardAdapter, register_dashboard


@register_dashboard
class PresalesDashboardAdapter(DashboardAdapter):
    """售前分析工作台适配器"""

    @property
    def module_id(self) -> str:
        return "presales"

    @property
    def module_name(self) -> str:
        return "售前分析"

    @property
    def supported_roles(self) -> List[str]:
        return ["presales", "sales", "admin"]

    def get_stats(self) -> List[DashboardStatCard]:
        """获取统计卡片"""
        today = date.today()
        year_start = date(today.year, 1, 1)

        # 年度统计
        ytd_projects = (
            self.db.query(Project).filter(Project.created_at >= year_start).all()
        )

        total_leads_ytd = len(ytd_projects)
        won_leads_ytd = sum(
            1 for p in ytd_projects if p.outcome == LeadOutcomeEnum.WON.value
        )
        lost_leads_ytd = sum(
            1 for p in ytd_projects if p.outcome == LeadOutcomeEnum.LOST.value
        )
        overall_win_rate = (
            won_leads_ytd / (won_leads_ytd + lost_leads_ytd)
            if (won_leads_ytd + lost_leads_ytd) > 0
            else 0
        )

        # 资源浪费统计
        from app.models.work_log import WorkLog

        total_hours = 0
        wasted_hours = 0

        for project in ytd_projects:
            hours = (
                self.db.query(func.sum(WorkLog.work_hours))
                .filter(WorkLog.project_id == project.id)
                .scalar()
                or 0
            )
            total_hours += hours

            if project.outcome in [
                LeadOutcomeEnum.LOST.value,
                LeadOutcomeEnum.ABANDONED.value,
            ]:
                wasted_hours += hours

        avg_investment = total_hours / total_leads_ytd if total_leads_ytd > 0 else 0
        waste_rate = wasted_hours / total_hours if total_hours > 0 else 0
        wasted_cost = Decimal(str(wasted_hours)) * Decimal("300")

        return [
            DashboardStatCard(
                key="total_leads_ytd",
                label="年度线索数",
                value=total_leads_ytd,
                unit="个",
                icon="leads",
                color="blue",
            ),
            DashboardStatCard(
                key="won_leads_ytd",
                label="赢单数",
                value=won_leads_ytd,
                unit="个",
                icon="win",
                color="green",
            ),
            DashboardStatCard(
                key="overall_win_rate",
                label="整体赢率",
                value=f"{overall_win_rate * 100:.1f}%",
                icon="rate",
                color="cyan",
            ),
            DashboardStatCard(
                key="avg_investment",
                label="平均投入工时",
                value=f"{avg_investment:.1f}",
                unit="小时",
                icon="time",
                color="orange",
            ),
            DashboardStatCard(
                key="waste_rate",
                label="资源浪费率",
                value=f"{waste_rate * 100:.1f}%",
                icon="waste",
                color="red",
            ),
            DashboardStatCard(
                key="wasted_cost",
                label="浪费成本",
                value=f"¥{float(wasted_cost):,.0f}",
                icon="money",
                color="purple",
            ),
        ]

    def get_widgets(self) -> List[DashboardWidget]:
        """获取Widget列表"""
        today = date.today()
        year_start = date(today.year, 1, 1)

        ytd_projects = (
            self.db.query(Project).filter(Project.created_at >= year_start).all()
        )

        # 按失败原因统计
        loss_reasons = {}
        for project in ytd_projects:
            if project.outcome in [
                LeadOutcomeEnum.LOST.value,
                LeadOutcomeEnum.ABANDONED.value,
            ]:
                reason = project.loss_reason or "OTHER"
                loss_reasons[reason] = loss_reasons.get(reason, 0) + 1

        # 月度统计（近6个月）
        monthly_stats = []
        for i in range(5, -1, -1):
            month_date = date(today.year, today.month, 1) - timedelta(days=30 * i)
            month_key = month_date.strftime("%Y-%m")

            month_projects = [
                p
                for p in ytd_projects
                if p.created_at and p.created_at.strftime("%Y-%m") == month_key
            ]
            month_won = sum(
                1 for p in month_projects if p.outcome == LeadOutcomeEnum.WON.value
            )
            month_lost = sum(
                1 for p in month_projects if p.outcome == LeadOutcomeEnum.LOST.value
            )

            monthly_stats.append(
                {
                    "month": month_key,
                    "total": len(month_projects),
                    "won": month_won,
                    "lost": month_lost,
                    "win_rate": round(
                        month_won / (month_won + month_lost), 3
                    )
                    if (month_won + month_lost) > 0
                    else 0,
                }
            )

        return [
            DashboardWidget(
                widget_id="loss_reasons",
                widget_type="chart",
                title="失败原因分布",
                data=loss_reasons,
                order=1,
                span=12,
            ),
            DashboardWidget(
                widget_id="monthly_trend",
                widget_type="chart",
                title="月度趋势",
                data=monthly_stats,
                order=2,
                span=12,
            ),
        ]

    def get_detailed_data(self) -> DetailedDashboardResponse:
        """获取详细数据"""
        stats_cards = self.get_stats()
        summary = {card.key: card.value for card in stats_cards}

        today = date.today()
        year_start = date(today.year, 1, 1)

        ytd_projects = (
            self.db.query(Project).filter(Project.created_at >= year_start).all()
        )

        # 月度统计完整数据
        monthly_stats = []
        for i in range(11, -1, -1):
            month_date = date(today.year, today.month, 1) - timedelta(days=30 * i)
            month_key = month_date.strftime("%Y-%m")

            month_projects = [
                p
                for p in ytd_projects
                if p.created_at and p.created_at.strftime("%Y-%m") == month_key
            ]
            month_won = sum(
                1 for p in month_projects if p.outcome == LeadOutcomeEnum.WON.value
            )
            month_lost = sum(
                1 for p in month_projects if p.outcome == LeadOutcomeEnum.LOST.value
            )

            monthly_stats.append(
                {
                    "month": month_key,
                    "total": len(month_projects),
                    "won": month_won,
                    "lost": month_lost,
                    "win_rate": round(
                        month_won / (month_won + month_lost), 3
                    )
                    if (month_won + month_lost) > 0
                    else 0,
                }
            )

        details = {"monthly_stats": monthly_stats}

        return DetailedDashboardResponse(
            module=self.module_id,
            module_name=self.module_name,
            summary=summary,
            details=details,
            generated_at=datetime.now(),
        )

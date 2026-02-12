# -*- coding: utf-8 -*-
"""
战略管理 Dashboard 适配器
"""

from datetime import datetime
from typing import List

from app.models.strategy import AnnualKeyWork, CSF, KPI, Strategy
from app.schemas.dashboard import (
    DashboardStatCard,
    DashboardWidget,
    DetailedDashboardResponse,
)
from app.services.dashboard_adapter import DashboardAdapter, register_dashboard


@register_dashboard
class StrategyDashboardAdapter(DashboardAdapter):
    """战略管理工作台适配器"""

    @property
    def module_id(self) -> str:
        return "strategy"

    @property
    def module_name(self) -> str:
        return "战略管理"

    @property
    def supported_roles(self) -> List[str]:
        return ["admin", "pmo", "strategy"]

    def get_stats(self) -> List[DashboardStatCard]:
        """获取统计卡片"""
        # 统计战略数量
        strategy_count = (
            self.db.query(Strategy).filter(Strategy.is_active).count()
        )

        # 获取当前生效的战略
        from app.services import strategy as strategy_service

        active_strategy = strategy_service.get_active_strategy(self.db)

        csf_count = 0
        kpi_count = 0
        work_count = 0
        kpi_on_track = 0
        kpi_at_risk = 0
        kpi_off_track = 0

        if active_strategy:
            # 统计CSF数量
            csf_count = (
                self.db.query(CSF)
                .filter(CSF.strategy_id == active_strategy.id, CSF.is_active)
                .count()
            )

            # 统计KPI
            kpis = (
                self.db.query(KPI)
                .join(CSF)
                .filter(
                    CSF.strategy_id == active_strategy.id,
                    CSF.is_active,
                    KPI.is_active,
                )
                .all()
            )

            kpi_count = len(kpis)

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
            work_count = (
                self.db.query(AnnualKeyWork)
                .join(CSF)
                .filter(
                    CSF.strategy_id == active_strategy.id,
                    CSF.is_active,
                    AnnualKeyWork.is_active,
                )
                .count()
            )

        return [
            DashboardStatCard(
                key="strategy_count",
                label="战略数量",
                value=strategy_count,
                unit="个",
                icon="strategy",
                color="blue",
            ),
            DashboardStatCard(
                key="csf_count",
                label="关键成功因素",
                value=csf_count,
                unit="个",
                icon="csf",
                color="green",
            ),
            DashboardStatCard(
                key="kpi_count",
                label="KPI指标",
                value=kpi_count,
                unit="个",
                icon="kpi",
                color="cyan",
            ),
            DashboardStatCard(
                key="kpi_on_track",
                label="进展正常",
                value=kpi_on_track,
                unit="个",
                icon="on-track",
                color="green",
            ),
            DashboardStatCard(
                key="kpi_at_risk",
                label="有风险",
                value=kpi_at_risk,
                unit="个",
                icon="at-risk",
                color="orange",
            ),
            DashboardStatCard(
                key="work_count",
                label="重点工作",
                value=work_count,
                unit="项",
                icon="work",
                color="purple",
            ),
        ]

    def get_widgets(self) -> List[DashboardWidget]:
        """获取Widget列表"""
        from app.services import strategy as strategy_service

        active_strategy = strategy_service.get_active_strategy(self.db)

        if not active_strategy:
            return []

        # 获取我负责的KPI
        my_kpis = (
            self.db.query(KPI)
            .join(CSF)
            .filter(
                CSF.strategy_id == active_strategy.id,
                CSF.is_active,
                KPI.is_active,
                KPI.owner_user_id == self.current_user.id,
            )
            .all()
        )

        my_kpis_data = [
            {
                "id": kpi.id,
                "code": kpi.code,
                "name": kpi.name,
                "target_value": kpi.target_value,
                "current_value": kpi.current_value,
                "completion_rate": strategy_service.calculate_kpi_completion_rate(kpi),
            }
            for kpi in my_kpis
        ]

        # 获取我负责的年度重点工作
        my_annual_works = (
            self.db.query(AnnualKeyWork)
            .join(CSF)
            .filter(
                CSF.strategy_id == active_strategy.id,
                CSF.is_active,
                AnnualKeyWork.is_active,
                AnnualKeyWork.owner_user_id == self.current_user.id,
            )
            .all()
        )

        my_works_data = [
            {
                "id": work.id,
                "code": work.code,
                "name": work.name,
                "status": work.status,
                "progress_percent": work.progress_percent,
            }
            for work in my_annual_works
        ]

        return [
            DashboardWidget(
                widget_id="my_kpis",
                widget_type="list",
                title="我的KPI",
                data=my_kpis_data,
                order=1,
                span=12,
            ),
            DashboardWidget(
                widget_id="my_annual_works",
                widget_type="list",
                title="我的重点工作",
                data=my_works_data,
                order=2,
                span=12,
            ),
        ]

    def get_detailed_data(self) -> DetailedDashboardResponse:
        """获取详细数据"""
        stats_cards = self.get_stats()
        summary = {card.key: card.value for card in stats_cards}

        from app.services import strategy as strategy_service

        active_strategy = strategy_service.get_active_strategy(self.db)

        if not active_strategy:
            return DetailedDashboardResponse(
                module=self.module_id,
                module_name=self.module_name,
                summary=summary,
                details={},
                generated_at=datetime.now(),
            )

        # 按维度统计
        dimension_names = {
            "FINANCIAL": "财务维度",
            "CUSTOMER": "客户维度",
            "INTERNAL": "内部运营维度",
            "LEARNING": "学习成长维度",
        }

        dimension_stats = []
        for dim_code, dim_name in dimension_names.items():
            # 统计KPI
            kpis = (
                self.db.query(KPI)
                .join(CSF)
                .filter(
                    CSF.strategy_id == active_strategy.id,
                    CSF.dimension == dim_code,
                    CSF.is_active,
                    KPI.is_active,
                )
                .all()
            )

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

            dimension_stats.append(
                {
                    "dimension": dim_code,
                    "dimension_name": dim_name,
                    "kpi_total": kpi_total,
                    "kpi_on_track": kpi_on_track,
                    "kpi_at_risk": kpi_at_risk,
                    "kpi_off_track": kpi_off_track,
                }
            )

        details = {"dimension_stats": dimension_stats}

        return DetailedDashboardResponse(
            module=self.module_id,
            module_name=self.module_name,
            summary=summary,
            details=details,
            generated_at=datetime.now(),
        )

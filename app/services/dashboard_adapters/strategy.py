# -*- coding: utf-8 -*-
"""兼容导出：dashboard_adapters.strategy."""

from app.schemas.dashboard import DashboardStatCard
from app.models.strategy import Strategy
from app.services import strategy as strategy_service
from app.services.dashboard.adapters.strategy import StrategyDashboardAdapter as _BaseAdapter


class StrategyDashboardAdapter(_BaseAdapter):
    def get_stats(self):
        strategy_count = self.db.query(Strategy).filter(Strategy.is_active).count()
        active_strategy = strategy_service.get_active_strategy(self.db)
        if not active_strategy:
            return [
                DashboardStatCard(
                    key="strategy_count",
                    title="战略数量",
                    value=strategy_count if isinstance(strategy_count, int) else 0,
                    unit="个",
                )
            ]
        return super().get_stats()


__all__ = ["StrategyDashboardAdapter", "strategy_service"]

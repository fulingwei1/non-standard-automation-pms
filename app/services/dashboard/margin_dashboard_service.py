# -*- coding: utf-8 -*-
"""
毛利率 Dashboard 服务

照抄 app/services/pmo_cockpit/pmo_cockpit_service.py 的全局聚合范式，
复用 ProfitAnalysisService.get_margin_analysis 做单项目毛利率计算。

四大块：
  1. KPI 卡：全局平均毛利率、达成目标项目占比、低于目标项目数、严重亏损项目数
  2. 分布：按 health 分桶（healthy/warning/critical）+ 按项目类型/行业
  3. 趋势：来自 ProjectMarginSnapshot（每日快照），委托 margin_trend_service
  4. 异常清单：低毛利项目 Top N（复用 get_low_profit_root_cause）
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models.project import Project

logger = logging.getLogger(__name__)

# 默认目标毛利率（与 ProfitAnalysisService.DEFAULT_TARGET_MARGIN 一致）
DEFAULT_TARGET_MARGIN = 25.0


class MarginDashboardService:
    """毛利率全局看板"""

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard(
        self, target_margin: float = DEFAULT_TARGET_MARGIN
    ) -> Dict[str, Any]:
        """聚合毛利率 Dashboard 全部数据。"""
        analyses = self._collect_project_margins(target_margin)

        return {
            "summary": self._build_summary(analyses, target_margin),
            "distribution": self._build_distribution(analyses),
            "anomalies": self._build_anomalies(target_margin),
            "generated_at": __import__("datetime").datetime.now().isoformat(),
        }

    # ================================================================
    # 1. 收集所有活跃项目的毛利率分析
    # ================================================================

    def _collect_project_margins(
        self, target_margin: float
    ) -> List[Dict[str, Any]]:
        """循环调 get_margin_analysis 收集所有活跃项目的毛利率。

        照抄 otd_metrics_service._margin_deviation 的循环范式。
        跳过无合同金额/报错的项目。
        """
        from app.services.profit_analysis_service import ProfitAnalysisService

        projects = (
            self.db.query(Project)
            .filter(Project.is_active.is_(True))
            .filter(Project.contract_amount.isnot(None))
            .filter(Project.contract_amount > 0)
            .all()
        )

        service = ProfitAnalysisService(self.db)
        analyses: List[Dict[str, Any]] = []
        for p in projects:
            try:
                a = service.get_margin_analysis(p.id, target_margin)
                if a and "error" not in a and "current_margin_rate" in a:
                    analyses.append(a)
            except Exception as e:
                logger.debug("毛利率分析失败 项目 %s: %s", p.id, e)
        return analyses

    # ================================================================
    # 2. KPI 卡
    # ================================================================

    def _build_summary(
        self, analyses: List[Dict[str, Any]], target_margin: float
    ) -> Dict[str, Any]:
        """KPI：平均毛利率、达成目标占比、低于目标数、严重亏损数。"""
        total = len(analyses)
        if total == 0:
            return {
                "total_projects": 0,
                "avg_margin_rate": 0.0,
                "target_margin_rate": target_margin,
                "healthy_count": 0,
                "warning_count": 0,
                "critical_count": 0,
                "below_target_count": 0,
                "achieve_target_rate_pct": 0.0,
            }

        rates = [float(a.get("current_margin_rate", 0)) for a in analyses]
        avg_rate = round(sum(rates) / total, 2)

        health_counts = {"healthy": 0, "warning": 0, "critical": 0}
        below_target = 0
        for a in analyses:
            h = a.get("health", "critical")
            if h in health_counts:
                health_counts[h] += 1
            if float(a.get("margin_gap", 0)) < 0:
                below_target += 1

        achieve = round(health_counts["healthy"] / total * 100, 2)

        return {
            "total_projects": total,
            "avg_margin_rate": avg_rate,
            "target_margin_rate": target_margin,
            "healthy_count": health_counts["healthy"],
            "warning_count": health_counts["warning"],
            "critical_count": health_counts["critical"],
            "below_target_count": below_target,
            "achieve_target_rate_pct": achieve,
        }

    # ================================================================
    # 3. 分布
    # ================================================================

    def _build_distribution(
        self, analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分布：按 health 分桶 + 毛利率区间分桶。"""
        # health 分桶
        health_dist = {"healthy": 0, "warning": 0, "critical": 0}
        for a in analyses:
            h = a.get("health", "critical")
            if h in health_dist:
                health_dist[h] += 1

        # 毛利率区间分桶
        buckets = {
            "亏损(<0%)": 0,
            "低毛利(0-10%)": 0,
            "中毛利(10-20%)": 0,
            "达标(20-30%)": 0,
            "高毛利(>30%)": 0,
        }
        for a in analyses:
            r = float(a.get("current_margin_rate", 0))
            if r < 0:
                buckets["亏损(<0%)"] += 1
            elif r < 10:
                buckets["低毛利(0-10%)"] += 1
            elif r < 20:
                buckets["中毛利(10-20%)"] += 1
            elif r < 30:
                buckets["达标(20-30%)"] += 1
            else:
                buckets["高毛利(>30%)"] += 1

        return {
            "by_health": health_dist,
            "by_margin_bucket": buckets,
        }

    # ================================================================
    # 4. 异常清单（复用 get_low_profit_root_cause）
    # ================================================================

    def _build_anomalies(self, target_margin: float) -> Dict[str, Any]:
        """低毛利项目 Top N + 根因（直接复用 get_low_profit_root_cause）。"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        try:
            service = ProfitAnalysisService(self.db)
            low = service.get_low_profit_root_cause(
                max_margin=target_margin * 0.5, limit=10
            )
            return {
                "low_profit_projects": low.get("low_profit_projects", [])[:10],
                "warning_signals": low.get("warning_signals", []),
                "total_low_profit": low.get("total_low_profit", 0),
            }
        except Exception as e:
            logger.warning("低毛利根因分析失败: %s", e)
            return {
                "low_profit_projects": [],
                "warning_signals": [],
                "total_low_profit": 0,
            }

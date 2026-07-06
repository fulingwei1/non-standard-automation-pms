# -*- coding: utf-8 -*-
"""
OTD 对比分析服务

两种对比：
1. 项目间对比：GET /otd/compare?ids=1,2,3
   多个项目的风险等级/毛利率/进度/延期天数并排对比
2. 时间对比：GET /otd/compare/trend?days=30
   全局指标"本期 vs 上期"变化（风险项目数/平均毛利率/准时交付率）
"""

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class OTDCompareService:
    """OTD 对比分析"""

    def __init__(self, db: Session):
        self.db = db
        self._today = date.today()

    # ================================================================
    # 项目间对比
    # ================================================================

    def compare_projects(
        self, project_ids: List[int]
    ) -> Dict[str, Any]:
        """多个项目并排对比：风险/毛利/进度/变更/延期。

        复用 scan_project + batch_margin_analysis，结果按 severity 排序。
        """
        from app.services.otd import OTDScanService
        from app.services.profit_analysis_service import ProfitAnalysisService

        svc = OTDScanService(self.db)
        profit_svc = ProfitAnalysisService(self.db)

        # 批量取毛利率（避免 N+1）
        analyses = profit_svc.batch_margin_analysis(project_ids=project_ids)
        margin_map = {a["project_id"]: a for a in analyses}

        items = []
        for pid in project_ids:
            # 扫描（不调 AI，快）
            profile = svc.scan_project(pid, include_ai=False)
            if "error" in profile:
                items.append({
                    "project_id": pid,
                    "error": profile["error"],
                })
                continue

            margin = margin_map.get(pid, {})
            items.append({
                "project_id": pid,
                "project_code": profile.get("project_code"),
                "project_name": profile.get("project_name"),
                "stage": profile.get("stage"),
                "severity": profile.get("severity"),
                "top_cause": profile.get("top_cause", ""),
                "risk_items_count": len(profile.get("risk_items", [])),
                "risk_dims": [it["dim"] for it in profile.get("risk_items", [])],
                "current_margin_rate": margin.get("current_margin_rate"),
                "target_margin_rate": margin.get("target_margin_rate"),
                "margin_gap": margin.get("margin_gap"),
                "health": margin.get("health"),
                "contract_amount": margin.get("contract_amount"),
                "actual_cost": margin.get("actual_cost"),
                "planned_end": profile.get("planned_end"),
                "progress": profile.get("progress"),
            })

        # 按 severity 降序（最严重的在前）
        sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        items.sort(key=lambda x: sev_order.get(x.get("severity", "LOW"), 99))

        # 找出差异最大的维度（共有的风险维度）
        all_dims = {}
        for item in items:
            for dim in item.get("risk_dims", []):
                all_dims[dim] = all_dims.get(dim, 0) + 1
        # 多个项目共有的风险维度（>=2 个项目命中的）
        shared_risks = [
            {"dim": dim, "project_count": cnt}
            for dim, cnt in sorted(all_dims.items(), key=lambda x: -x[1])
            if cnt >= 2
        ]

        return {
            "project_count": len(items),
            "projects": items,
            "shared_risks": shared_risks,  # 多项目共有的风险维度
            "generated_at": self._today.isoformat(),
        }

    # ================================================================
    # 时间对比（本期 vs 上期）
    # ================================================================

    def compare_trend(self, days: int = 30) -> Dict[str, Any]:
        """全局指标"本期 vs 上期"变化。

        本期 = 最近 N 天，上期 = 再往前 N 天。
        对比：风险项目数 / 平均毛利率 / 准时交付率 / 延期天数。
        """
        from app.services.otd import OTDMetricsService
        from app.services.otd.trend_service import OTDTrendService

        period_end = self._today
        period_start = period_end - timedelta(days=days)
        prev_end = period_start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days)

        # 当前指标（实时）
        metrics_svc = OTDMetricsService(self.db)
        current_metrics = metrics_svc.get_metrics(
            start_date=period_start,
            end_date=period_end,
            include_offenders=False,
        )

        # 上期指标
        prev_metrics = metrics_svc.get_metrics(
            start_date=prev_start,
            end_date=prev_end,
            include_offenders=False,
        )

        # 对比计算
        comparisons = []
        metric_pairs = [
            ("准时交付率(%)", "on_time_delivery_rate", "rate_pct"),
            ("平均延期天数", "delay_days", "avg_delay_days"),
            ("返工次数", "rework_count", "total_retry_count"),
            ("变更次数", "change_count", "grand_total"),
            ("平均毛利偏差(%)", "margin_deviation", "avg_margin_gap_pct"),
            ("平均验收周期(天)", "acceptance_cycle_days", "avg_cycle_days"),
            ("客户投诉率(%)", "customer_complaint_rate", "complaint_rate_pct"),
        ]

        for label, metric_key, value_key in metric_pairs:
            current = current_metrics.get("metrics", {}).get(metric_key, {})
            prev = prev_metrics.get("metrics", {}).get(metric_key, {})

            current_val = current.get(value_key, 0)
            prev_val = prev.get(value_key, 0)

            # 变化值和方向
            if isinstance(current_val, (int, float)) and isinstance(prev_val, (int, float)):
                change = round(current_val - prev_val, 2)
                # 判断方向：毛利率/准时交付率 高=好，其他低=好
                good_when_high = metric_key in ("on_time_delivery_rate",)
                if change == 0:
                    direction = "stable"
                elif (change > 0) == good_when_high:
                    direction = "better"
                else:
                    direction = "worse"
            else:
                change = None
                direction = "unknown"

            comparisons.append({
                "metric": label,
                "current": current_val,
                "previous": prev_val,
                "change": change,
                "direction": direction,  # better/worse/stable
            })

        return {
            "period": {
                "current": {
                    "start": period_start.isoformat(),
                    "end": period_end.isoformat(),
                    "days": days,
                    "label": f"近{days}天",
                },
                "previous": {
                    "start": prev_start.isoformat(),
                    "end": prev_end.isoformat(),
                    "days": days,
                    "label": f"前{days}天",
                },
            },
            "comparisons": comparisons,
            "summary": {
                "better_count": sum(1 for c in comparisons if c["direction"] == "better"),
                "worse_count": sum(1 for c in comparisons if c["direction"] == "worse"),
                "stable_count": sum(1 for c in comparisons if c["direction"] == "stable"),
            },
            "generated_at": self._today.isoformat(),
        }

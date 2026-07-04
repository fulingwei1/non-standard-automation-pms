# -*- coding: utf-8 -*-
"""
OTD 趋势分析服务

- get_project_trend：单项目风险趋势（severity/各维度命中随时间）
- get_global_trend：全局趋势（每日各等级项目数 + 各维度命中项目数）

照抄：
- health_trend_service.py:84-89 的连续日期补齐
- risk_analytics.py:347-371 的 func.date() + group_by 全局聚合
- health_trend_service.py:287-312 的事件打点（筛 OTD 自己产的预警）
"""

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.otd_risk_snapshot import OTDRiskSnapshot

logger = logging.getLogger(__name__)

SEVERITY_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
# 维度列（与 OTDRiskSnapshot 的 *_hit 字段对应）
DIM_HIT_FIELDS = [
    "procurement_delay_hit",
    "design_not_frozen_hit",
    "customer_change_hit",
    "budget_overrun_hit",
    "field_debug_hit",
    "acceptance_doc_hit",
    "payment_condition_hit",
    "key_milestone_hit",
    "progress_lag_hit",
    "margin_deviation_hit",
    "open_items_hit",
]
# 列名 → 可读名
DIM_LABELS = {
    "procurement_delay_hit": "采购延期",
    "design_not_frozen_hit": "图纸未冻结",
    "customer_change_hit": "客户变更频繁",
    "budget_overrun_hit": "BOM超预算",
    "field_debug_hit": "调试反复",
    "acceptance_doc_hit": "验收资料缺失",
    "payment_condition_hit": "回款条件不齐",
    "key_milestone_hit": "关键节点延期",
    "progress_lag_hit": "进度滞后",
    "margin_deviation_hit": "毛利偏差",
    "open_items_hit": "未关闭事项",
}


class OTDTrendService:
    """OTD 风险趋势分析"""

    def __init__(self, db: Session):
        self.db = db

    # ================================================================
    # 单项目趋势
    # ================================================================

    def get_project_trend(
        self, project_id: int, days: int = 30
    ) -> Dict[str, Any]:
        """单项目风险趋势（照抄 HealthTrendService.get_health_trend 范式）。

        返回连续日期序列 + severity 序列 + 各维度命中序列 + 预警事件打点。
        缺日不补值（severity/dimensions 该日为 None），但 dates 数组连续无空洞。
        """
        from app.models.project import Project

        project = (
            self.db.query(Project).filter(Project.id == project_id).first()
        )
        if not project:
            return {"error": "项目不存在", "project_id": project_id}

        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        snapshots = (
            self.db.query(OTDRiskSnapshot)
            .filter(
                OTDRiskSnapshot.project_id == project_id,
                OTDRiskSnapshot.snapshot_date >= start_date,
                OTDRiskSnapshot.snapshot_date <= end_date,
            )
            .order_by(OTDRiskSnapshot.snapshot_date.asc())
            .all()
        )

        # 建日期索引（照抄 health_trend_service.py:92-99）
        snap_map = {s.snapshot_date: s for s in snapshots}

        # 生成连续日期序列（照抄 health_trend_service.py:84-89）
        dates: List[str] = []
        severity_series: List[Optional[str]] = []
        risk_items_count_series: List[Optional[int]] = []
        dimensions: Dict[str, List[Optional[bool]]] = {
            label: [] for label in DIM_LABELS.values()
        }

        current = start_date
        while current <= end_date:
            dates.append(current.isoformat())
            snap = snap_map.get(current)
            if snap:
                severity_series.append(snap.severity)
                risk_items_count_series.append(snap.risk_items_count)
                for field, label in DIM_LABELS.items():
                    dimensions[label].append(bool(getattr(snap, field, False)))
            else:
                severity_series.append(None)
                risk_items_count_series.append(None)
                for label in DIM_LABELS.values():
                    dimensions[label].append(None)
            current += timedelta(days=1)

        # 预警事件打点（照抄 health_trend_service.py:287-312，筛 OTD 自己产的）
        events = self._get_otd_alert_events(project_id, start_date, end_date)

        return {
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days,
            },
            "dates": dates,
            "severity": severity_series,
            "risk_items_count": risk_items_count_series,
            "dimensions": dimensions,
            "events": events,
            "snapshot_count": len(snapshots),
        }

    # ================================================================
    # 全局趋势
    # ================================================================

    def get_global_trend(self, days: int = 30) -> Dict[str, Any]:
        """全局趋势：每日各等级项目数 + 各维度命中项目数（照抄 risk_analytics.py 聚合）。"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # 每日各 severity 的项目数（照抄 risk_analytics.py:347-371）
        rows = (
            self.db.query(
                OTDRiskSnapshot.snapshot_date,
                OTDRiskSnapshot.severity,
                func.count(OTDRiskSnapshot.id),
            )
            .filter(
                OTDRiskSnapshot.snapshot_date >= start_date,
                OTDRiskSnapshot.snapshot_date <= end_date,
            )
            .group_by(
                OTDRiskSnapshot.snapshot_date, OTDRiskSnapshot.severity
            )
            .all()
        )

        # 按 date 聚合
        by_date: Dict[str, Dict[str, int]] = {}
        for d, sev, cnt in rows:
            ds = d.isoformat() if hasattr(d, "isoformat") else str(d)
            if ds not in by_date:
                by_date[ds] = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
            if sev in by_date[ds]:
                by_date[ds][sev] = int(cnt)

        # 每日各维度命中项目数。
        # SQLite 的 Boolean 列实际存 0/1，直接 sum 即可（True=1, False=0）。
        # 不用 .cast() —— SQLite + Boolean Column 对 cast 兼容性差。
        dim_rows = (
            self.db.query(
                OTDRiskSnapshot.snapshot_date,
                *[
                    func.sum(getattr(OTDRiskSnapshot, f)).label(f)
                    for f in DIM_HIT_FIELDS
                ],
            )
            .filter(
                OTDRiskSnapshot.snapshot_date >= start_date,
                OTDRiskSnapshot.snapshot_date <= end_date,
            )
            .group_by(OTDRiskSnapshot.snapshot_date)
            .all()
        )
        heatmap: Dict[str, Dict[str, int]] = {}
        for row in dim_rows:
            d = row[0]
            ds = d.isoformat() if hasattr(d, "isoformat") else str(d)
            heatmap[ds] = {
                DIM_LABELS[f]: int(getattr(row, f) or 0) for f in DIM_HIT_FIELDS
            }

        # 连续日期补齐
        dates: List[str] = []
        severity_trend: List[Dict[str, Any]] = []
        heatmap_trend: List[Dict[str, Any]] = []
        current = start_date
        while current <= end_date:
            ds = current.isoformat()
            dates.append(ds)
            sev = by_date.get(ds, {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0})
            severity_trend.append({"date": ds, **sev})
            hm = heatmap.get(ds, {label: 0 for label in DIM_LABELS.values()})
            heatmap_trend.append({"date": ds, **hm})
            current += timedelta(days=1)

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days,
            },
            "dates": dates,
            "severity_trend": severity_trend,  # 每日各等级项目数
            "heatmap": heatmap_trend,  # 每日各维度命中项目数
            "total_snapshots": sum(
                sum(d.values()) for d in by_date.values()
            ),
            "generated_at": date.today().isoformat(),
        }

    # ================================================================
    # 预警事件打点（照抄 health_trend_service._get_alert_events）
    # ================================================================

    def _get_otd_alert_events(
        self, project_id: int, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """查时间窗内的 OTD 预警（筛 alert_data.source == otd_scan），用于趋势打点。"""
        from app.models.alert import AlertRecord
        from sqlalchemy import literal_column

        try:
            alerts = (
                self.db.query(AlertRecord)
                .filter(
                    AlertRecord.project_id == project_id,
                    AlertRecord.triggered_at.isnot(None),
                    func.date(AlertRecord.triggered_at) >= start_date,
                    func.date(AlertRecord.triggered_at) <= end_date,
                )
                .order_by(AlertRecord.triggered_at.asc())
                .all()
            )
            events = []
            for a in alerts:
                # 只取 OTD 自己产的（alert_data.source == otd_scan）
                data = a.alert_data or {}
                if isinstance(data, dict) and data.get("source") != "otd_scan":
                    continue
                ta = a.triggered_at
                events.append(
                    {
                        "date": ta.date().isoformat() if ta else None,
                        "severity": a.severity or a.alert_level,
                        "title": a.alert_title,
                        "status": a.status,
                    }
                )
            return events
        except Exception as e:
            logger.warning("查 OTD 预警事件失败 项目 %s: %s", project_id, e)
            return []

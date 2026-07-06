# -*- coding: utf-8 -*-
"""
毛利率趋势服务 + 快照写入

- create_snapshot：为单个项目落毛利率快照（同日幂等）
- batch_create_snapshots：批量落快照（定时任务用）
- get_project_trend：单项目毛利率趋势
- get_global_trend：全局平均毛利率趋势 + 各 health 分布

照抄 app/services/otd/trend_service.py 的连续日期补齐 + 列式聚合范式。
"""

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_margin_snapshot import ProjectMarginSnapshot

logger = logging.getLogger(__name__)


class MarginTrendService:
    """毛利率趋势与快照"""

    def __init__(self, db: Session):
        self.db = db
        self._today = date.today()

    # ================================================================
    # 快照写入（照抄 OTDScanService._create_snapshot 幂等范式）
    # ================================================================

    def create_snapshot(
        self, project_id: int, target_margin: float = 25.0
    ) -> bool:
        """为单个项目落毛利率快照。同日幂等。失败返回 False。"""
        try:
            # 同日幂等去重
            existing = (
                self.db.query(ProjectMarginSnapshot)
                .filter(
                    ProjectMarginSnapshot.project_id == project_id,
                    ProjectMarginSnapshot.snapshot_date == self._today,
                )
                .first()
            )
            if existing:
                return False

            from app.services.profit_analysis_service import ProfitAnalysisService

            analysis = ProfitAnalysisService(self.db).get_margin_analysis(
                project_id, target_margin
            )
            if not analysis or "error" in analysis:
                return False

            snap = ProjectMarginSnapshot(
                project_id=project_id,
                snapshot_date=self._today,
                current_margin_rate=analysis.get("current_margin_rate"),
                forecast_margin_rate=analysis.get("forecast_margin_rate"),
                margin_gap=analysis.get("margin_gap"),
                target_margin_rate=analysis.get("target_margin_rate"),
                health=analysis.get("health"),
                contract_amount=analysis.get("contract_amount"),
                actual_cost=analysis.get("actual_cost"),
                budget_amount=analysis.get("budget_amount"),
            )
            self.db.add(snap)
            self.db.flush()
            return True
        except Exception as e:
            logger.error("毛利率快照写入失败 项目 %s: %s", project_id, e)
            return False

    def batch_create_snapshots(
        self, target_margin: float = 25.0
    ) -> Dict[str, Any]:
        """批量落快照（定时任务用）。照抄 create_daily_risk_snapshots 范式。"""
        projects = (
            self.db.query(Project)
            .filter(Project.is_active.is_(True))
            .filter(Project.contract_amount.isnot(None))
            .filter(Project.contract_amount > 0)
            .all()
        )
        created = 0
        for p in projects:
            if self.create_snapshot(p.id, target_margin):
                created += 1
        self.db.commit()
        return {
            "total": len(projects),
            "created": created,
            "timestamp": self._today.isoformat(),
        }

    # ================================================================
    # 单项目趋势（照抄 OTDTrendService.get_project_trend）
    # ================================================================

    def get_project_trend(
        self, project_id: int, days: int = 30
    ) -> Dict[str, Any]:
        project = (
            self.db.query(Project).filter(Project.id == project_id).first()
        )
        if not project:
            return {"error": "项目不存在", "project_id": project_id}

        start_date = self._today - timedelta(days=days)
        snapshots = (
            self.db.query(ProjectMarginSnapshot)
            .filter(
                ProjectMarginSnapshot.project_id == project_id,
                ProjectMarginSnapshot.snapshot_date >= start_date,
            )
            .order_by(ProjectMarginSnapshot.snapshot_date.asc())
            .all()
        )
        snap_map = {s.snapshot_date: s for s in snapshots}

        dates: List[str] = []
        margin_series: List[Optional[float]] = []
        gap_series: List[Optional[float]] = []
        health_series: List[Optional[str]] = []

        current = start_date
        while current <= self._today:
            dates.append(current.isoformat())
            snap = snap_map.get(current)
            if snap:
                margin_series.append(
                    float(snap.current_margin_rate) if snap.current_margin_rate is not None else None
                )
                gap_series.append(
                    float(snap.margin_gap) if snap.margin_gap is not None else None
                )
                health_series.append(snap.health)
            else:
                margin_series.append(None)
                gap_series.append(None)
                health_series.append(None)
            current += timedelta(days=1)

        return {
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "period": {
                "start": start_date.isoformat(),
                "end": self._today.isoformat(),
                "days": days,
            },
            "dates": dates,
            "current_margin_rate": margin_series,
            "margin_gap": gap_series,
            "health": health_series,
            "snapshot_count": len(snapshots),
        }

    # ================================================================
    # 全局趋势（照抄 OTDTrendService.get_global_trend 的聚合）
    # ================================================================

    def get_global_trend(self, days: int = 30) -> Dict[str, Any]:
        """全局：每日平均毛利率 + 各 health 分布。"""
        start_date = self._today - timedelta(days=days)

        # 每日平均毛利率
        avg_rows = (
            self.db.query(
                ProjectMarginSnapshot.snapshot_date,
                func.avg(ProjectMarginSnapshot.current_margin_rate),
            )
            .filter(
                ProjectMarginSnapshot.snapshot_date >= start_date,
                ProjectMarginSnapshot.current_margin_rate.isnot(None),
            )
            .group_by(ProjectMarginSnapshot.snapshot_date)
            .all()
        )
        avg_map = {
            (d.isoformat() if hasattr(d, "isoformat") else str(d)): round(float(v), 2)
            for d, v in avg_rows
            if v is not None
        }

        # 每日各 health 项目数
        health_rows = (
            self.db.query(
                ProjectMarginSnapshot.snapshot_date,
                ProjectMarginSnapshot.health,
                func.count(ProjectMarginSnapshot.id),
            )
            .filter(
                ProjectMarginSnapshot.snapshot_date >= start_date,
                ProjectMarginSnapshot.health.isnot(None),
            )
            .group_by(
                ProjectMarginSnapshot.snapshot_date,
                ProjectMarginSnapshot.health,
            )
            .all()
        )
        health_map: Dict[str, Dict[str, int]] = {}
        for d, h, cnt in health_rows:
            ds = d.isoformat() if hasattr(d, "isoformat") else str(d)
            health_map.setdefault(
                ds, {"healthy": 0, "warning": 0, "critical": 0}
            )
            if h in health_map[ds]:
                health_map[ds][h] = int(cnt)

        # 连续日期补齐
        dates: List[str] = []
        avg_series: List[Optional[float]] = []
        health_series: List[Dict[str, int]] = []
        current = start_date
        while current <= self._today:
            ds = current.isoformat()
            dates.append(ds)
            avg_series.append(avg_map.get(ds))
            health_series.append(
                health_map.get(ds, {"healthy": 0, "warning": 0, "critical": 0})
            )
            current += timedelta(days=1)

        total_snaps = sum(sum(d.values()) for d in health_map.values())
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": self._today.isoformat(),
                "days": days,
            },
            "dates": dates,
            "avg_margin_rate": avg_series,
            "health_distribution": health_series,
            "total_snapshots": total_snaps,
            "needs_backfill": total_snaps < days,
            "hint": (
                "快照数据不足，趋势图可能有断点。"
                "建议调 POST /pmo/margin-dashboard/backfill 回填历史快照。"
                if total_snaps < days
                else None
            ),
            "generated_at": self._today.isoformat(),
        }

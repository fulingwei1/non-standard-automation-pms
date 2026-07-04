# -*- coding: utf-8 -*-
"""
毛利率 Dashboard + 趋势 + 快照测试

验证：
- Dashboard 返回 KPI/分布/异常结构
- 快照写入（同日幂等）
- 单项目/全局趋势结构
- mock ProfitAnalysisService 隔离外部成本计算
"""

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from app.models.project import Project
from app.models.project_margin_snapshot import ProjectMarginSnapshot


def _make_project(db, code="MARGIN-DASH-001", contract=100000, **overrides):
    from decimal import Decimal

    defaults = dict(
        project_code=code,
        project_name=f"毛利率测试 {code}",
        stage="S5",
        status="ST01",
        health="H1",
        progress_pct=30,
        is_active=True,
        is_archived=False,
        contract_amount=Decimal(str(contract)),
        planned_start_date=date.today() - timedelta(days=90),
        planned_end_date=date.today() + timedelta(days=30),
    )
    defaults.update(overrides)
    p = Project(**defaults)
    db.add(p)
    db.flush()
    return p


# ============================================================
# Dashboard
# ============================================================


class TestMarginDashboard:
    def test_dashboard_structure(self, db_session):
        """Dashboard 返回 summary/distribution/anomalies。"""
        from app.services.dashboard.margin_dashboard_service import (
            MarginDashboardService,
        )

        with patch(
            "app.services.profit_analysis_service.ProfitAnalysisService.get_margin_analysis",
            return_value={
                "current_margin_rate": 30.0,
                "margin_gap": 5.0,
                "health": "healthy",
                "contract_amount": 100000,
            },
        ):
            result = MarginDashboardService(db_session).get_dashboard()

        assert "summary" in result
        assert "distribution" in result
        assert "anomalies" in result
        assert "generated_at" in result
        summary = result["summary"]
        for key in (
            "total_projects",
            "avg_margin_rate",
            "healthy_count",
            "warning_count",
            "critical_count",
            "below_target_count",
            "achieve_target_rate_pct",
        ):
            assert key in summary

    def test_distribution_buckets(self, db_session):
        """分布按 health + 毛利率区间分桶。"""
        from app.services.dashboard.margin_dashboard_service import (
            MarginDashboardService,
        )

        _make_project(db_session, "MARGIN-BUCK-1")
        with patch(
            "app.services.profit_analysis_service.ProfitAnalysisService.get_margin_analysis",
            return_value={
                "current_margin_rate": 35.0,
                "margin_gap": 10.0,
                "health": "healthy",
            },
        ):
            result = MarginDashboardService(db_session).get_dashboard()

        dist = result["distribution"]
        assert "by_health" in dist
        assert "by_margin_bucket" in dist
        # 35% 落在高毛利桶
        assert dist["by_margin_bucket"]["高毛利(>30%)"] >= 1


# ============================================================
# 快照写入
# ============================================================


class TestMarginSnapshot:
    def test_snapshot_created(self, db_session):
        """create_snapshot 落一条快照。"""
        from app.services.dashboard.margin_trend_service import MarginTrendService

        project = _make_project(db_session, "MARGIN-SNAP-1")
        with patch(
            "app.services.profit_analysis_service.ProfitAnalysisService.get_margin_analysis",
            return_value={
                "current_margin_rate": 28.0,
                "forecast_margin_rate": 26.0,
                "margin_gap": 3.0,
                "target_margin_rate": 25.0,
                "health": "healthy",
                "contract_amount": 100000,
                "actual_cost": 72000,
                "budget_amount": 75000,
            },
        ):
            ok = MarginTrendService(db_session).create_snapshot(project.id)
        assert ok is True

        snap = (
            db_session.query(ProjectMarginSnapshot)
            .filter(ProjectMarginSnapshot.project_id == project.id)
            .first()
        )
        assert snap is not None
        assert float(snap.current_margin_rate) == 28.0
        assert snap.health == "healthy"

    def test_snapshot_same_day_dedup(self, db_session):
        """同项目同日重复只存一条。"""
        from app.services.dashboard.margin_trend_service import MarginTrendService

        project = _make_project(db_session, "MARGIN-SNAP-DEDUP")
        with patch(
            "app.services.profit_analysis_service.ProfitAnalysisService.get_margin_analysis",
            return_value={"current_margin_rate": 20.0, "health": "warning"},
        ):
            svc = MarginTrendService(db_session)
            assert svc.create_snapshot(project.id) is True
            assert svc.create_snapshot(project.id) is False  # 幂等

        cnt = (
            db_session.query(ProjectMarginSnapshot)
            .filter(
                ProjectMarginSnapshot.project_id == project.id,
                ProjectMarginSnapshot.snapshot_date == date.today(),
            )
            .count()
        )
        assert cnt == 1


# ============================================================
# 趋势
# ============================================================


class TestMarginTrend:
    def test_global_trend_structure(self, db_session):
        """全局趋势返回连续日期 + avg 序列 + health 分布。"""
        from app.services.dashboard.margin_trend_service import MarginTrendService

        project = _make_project(db_session, "MARGIN-TREND-G")
        db_session.add(
            ProjectMarginSnapshot(
                project_id=project.id,
                snapshot_date=date.today(),
                current_margin_rate=28.0,
                margin_gap=3.0,
                health="healthy",
            )
        )
        db_session.flush()

        result = MarginTrendService(db_session).get_global_trend(days=5)
        assert len(result["dates"]) == 6  # 5 天 = 6 个日期
        assert len(result["avg_margin_rate"]) == len(result["dates"])
        assert len(result["health_distribution"]) == len(result["dates"])
        assert result["total_snapshots"] >= 1

    def test_project_trend_not_found(self, db_session):
        """不存在的项目返回 error。"""
        from app.services.dashboard.margin_trend_service import MarginTrendService

        result = MarginTrendService(db_session).get_project_trend(999999, days=5)
        assert "error" in result

    def test_project_trend_continuous_dates(self, db_session):
        """单项目趋势返回连续日期（有快照天有值，无快照天 None）。"""
        from app.services.dashboard.margin_trend_service import MarginTrendService

        project = _make_project(db_session, "MARGIN-TREND-P")
        db_session.add(
            ProjectMarginSnapshot(
                project_id=project.id,
                snapshot_date=date.today() - timedelta(days=2),
                current_margin_rate=22.0,
                margin_gap=-3.0,
                health="warning",
            )
        )
        db_session.flush()

        result = MarginTrendService(db_session).get_project_trend(project.id, days=5)
        assert len(result["dates"]) == 6
        assert 22.0 in result["current_margin_rate"]  # 有快照天
        assert None in result["current_margin_rate"]  # 无快照天

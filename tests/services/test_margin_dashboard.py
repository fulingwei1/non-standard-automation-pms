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


# ============================================================
# batch_margin_analysis（N+1 修复后的批量接口）
# ============================================================


class TestBatchMarginAnalysis:
    def test_batch_returns_all_projects(self, db_session):
        """batch_margin_analysis 一次性返回所有活跃项目。"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        _make_project(db_session, "MARGIN-BATCH-1", contract=100000)
        _make_project(db_session, "MARGIN-BATCH-2", contract=200000)

        with patch(
            "app.services.profit_analysis_service.ProfitAnalysisService._get_actual_cost",
            return_value=50000,
        ):
            results = ProfitAnalysisService(db_session).batch_margin_analysis()

        assert len(results) >= 2
        codes = {r["project_code"] for r in results}
        assert "MARGIN-BATCH-1" in codes
        for r in results:
            assert "current_margin_rate" in r
            assert "health" in r

    def test_batch_skips_zero_contract(self, db_session):
        from app.services.profit_analysis_service import ProfitAnalysisService

        _make_project(db_session, "MARGIN-BATCH-ZERO", contract=0)
        results = ProfitAnalysisService(db_session).batch_margin_analysis()
        codes = {r["project_code"] for r in results}
        assert "MARGIN-BATCH-ZERO" not in codes

    def test_batch_margin_rate_correctness(self, db_session):
        """批量算的毛利率与单项目一致（同口径）。"""
        from app.models.project.financial import ProjectCost
        from app.services.profit_analysis_service import ProfitAnalysisService

        project = _make_project(db_session, "MARGIN-BATCH-CMP", contract=100000)
        db_session.add(
            ProjectCost(project_id=project.id, cost_type="MATERIAL", amount=60000)
        )
        db_session.flush()

        service = ProfitAnalysisService(db_session)
        single = service.get_margin_analysis(project.id)
        batch = service.batch_margin_analysis()
        batch_item = next(
            r for r in batch if r["project_code"] == "MARGIN-BATCH-CMP"
        )
        assert float(single["current_margin_rate"]) == float(
            batch_item["current_margin_rate"]
        )


class TestBatchCreateSnapshots:
    def test_batch_snapshots_created(self, db_session):
        from app.services.dashboard.margin_trend_service import MarginTrendService

        _make_project(db_session, "MARGIN-BSNAP-1", contract=100000)
        _make_project(db_session, "MARGIN-BSNAP-2", contract=200000)

        with patch(
            "app.services.profit_analysis_service.ProfitAnalysisService._get_actual_cost",
            return_value=40000,
        ):
            result = MarginTrendService(db_session).batch_create_snapshots()
        assert result["created"] >= 2

        with patch(
            "app.services.profit_analysis_service.ProfitAnalysisService._get_actual_cost",
            return_value=40000,
        ):
            result2 = MarginTrendService(db_session).batch_create_snapshots()
        assert result2["created"] == 0  # 幂等


class TestDashboardSummary:
    def test_summary_structure(self, db_session):
        from app.services.dashboard.margin_dashboard_service import (
            MarginDashboardService,
        )

        result = MarginDashboardService(db_session).get_dashboard()
        s = result["summary"]
        assert (
            s["healthy_count"] + s["warning_count"] + s["critical_count"]
            == s["total_projects"]
        )


class TestTrendColdStart:
    def test_needs_backfill_when_empty(self, db_session):
        """快照数 < days 时 needs_backfill=True，hint 引导。"""
        from app.services.dashboard.margin_trend_service import MarginTrendService

        # 用大 days 确保快照数 < days（即使有累积数据）
        result = MarginTrendService(db_session).get_global_trend(days=365)
        assert result["needs_backfill"] is True  # 不可能有 365 天快照
        assert result["hint"] is not None
        assert "backfill" in result["hint"]

    def test_needs_backfill_false_when_enough(self, db_session):
        from app.services.dashboard.margin_trend_service import MarginTrendService

        project = _make_project(db_session, "MARGIN-COLD-FILL")
        db_session.add(
            ProjectMarginSnapshot(
                project_id=project.id,
                snapshot_date=date.today(),
                current_margin_rate=28.0,
                health="healthy",
            )
        )
        db_session.commit()
        result = MarginTrendService(db_session).get_global_trend(days=1)
        assert result["needs_backfill"] is False


# ============================================================
# 项目等级毛利率底线（手册 Sheet9 红线）
# ============================================================


class TestProjectLevelMargin:
    """项目等级 S/A/B/C 对应不同毛利率底线。"""

    def test_target_margin_by_level(self, db_session):
        """S=40 / A=35 / B=30 / C=25，无等级=25。"""
        from app.services.dashboard.margin_level_service import get_target_margin

        assert get_target_margin(db_session, "S") == 40.0
        assert get_target_margin(db_session, "A") == 35.0
        assert get_target_margin(db_session, "B") == 30.0
        assert get_target_margin(db_session, "C") == 25.0
        assert get_target_margin(db_session, None) == 25.0

    def test_margin_floor_by_level(self, db_session):
        """底线：S=30 / C=20。"""
        from app.services.dashboard.margin_level_service import get_margin_floor

        assert get_margin_floor(db_session, "S") == 30.0
        assert get_margin_floor(db_session, "C") == 20.0

    def test_ensure_default_levels_initializes(self, db_session):
        """首次运行自动初始化手册红线到 DB。"""
        from app.models.sales.margin_alert import MarginAlertConfig
        from app.services.dashboard.margin_level_service import ensure_default_levels

        # 清理可能存在的
        db_session.query(MarginAlertConfig).filter(
            MarginAlertConfig.code.like("PROJECT_LEVEL_%")
        ).delete()
        db_session.commit()

        created = ensure_default_levels(db_session)
        assert created == 4  # S/A/B/C

        # 幂等：再跑不新增
        created2 = ensure_default_levels(db_session)
        assert created2 == 0

    def test_get_margin_analysis_uses_level(self, db_session):
        """get_margin_analysis 按项目等级取 target_margin。"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        project = _make_project(db_session, "MARGIN-LEVEL-S", contract=100000)
        project.project_level = "S"
        db_session.commit()

        a = ProfitAnalysisService(db_session).get_margin_analysis(project.id)
        assert a["target_margin_rate"] == 40.0  # S 级

        project.project_level = "C"
        db_session.commit()
        a2 = ProfitAnalysisService(db_session).get_margin_analysis(project.id)
        assert a2["target_margin_rate"] == 25.0  # C 级

    def test_batch_margin_includes_level(self, db_session):
        """batch_margin_analysis 返回里带 project_level。"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        project = _make_project(db_session, "MARGIN-BATCH-LVL", contract=100000)
        project.project_level = "A"
        db_session.commit()

        results = ProfitAnalysisService(db_session).batch_margin_analysis()
        item = next(
            r for r in results if r["project_code"] == "MARGIN-BATCH-LVL"
        )
        assert item["project_level"] == "A"
        assert item["target_margin_rate"] == 35.0  # A 级

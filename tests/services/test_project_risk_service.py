# -*- coding: utf-8 -*-
"""ProjectRiskService 单元测试"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import date, datetime
from decimal import Decimal

from app.services.project.project_risk_service import ProjectRiskService


def _mock_db():
    return MagicMock()


def _make_service(db=None):
    db = db or _mock_db()
    return ProjectRiskService(db), db


class TestCalculateRiskLevel:
    """_calculate_risk_level 规则测试"""

    def setup_method(self):
        self.svc, _ = _make_service()

    def test_low(self):
        assert self.svc._calculate_risk_level({}) == "LOW"

    def test_critical_by_overdue_ratio(self):
        assert self.svc._calculate_risk_level({"overdue_milestone_ratio": 0.5}) == "CRITICAL"

    def test_critical_by_critical_risks(self):
        assert self.svc._calculate_risk_level({"critical_risks_count": 1}) == "CRITICAL"

    def test_high_by_overdue_ratio(self):
        assert self.svc._calculate_risk_level({"overdue_milestone_ratio": 0.3}) == "HIGH"

    def test_high_by_high_risks(self):
        assert self.svc._calculate_risk_level({"high_risks_count": 2}) == "HIGH"

    def test_high_by_schedule_variance(self):
        assert self.svc._calculate_risk_level({"schedule_variance": -21}) == "HIGH"

    def test_medium_by_overdue_ratio(self):
        assert self.svc._calculate_risk_level({"overdue_milestone_ratio": 0.1}) == "MEDIUM"

    def test_medium_by_high_risks(self):
        assert self.svc._calculate_risk_level({"high_risks_count": 1}) == "MEDIUM"

    def test_medium_by_schedule_variance(self):
        assert self.svc._calculate_risk_level({"schedule_variance": -11}) == "MEDIUM"


class TestIsRiskUpgrade:

    def setup_method(self):
        self.svc, _ = _make_service()

    def test_upgrade(self):
        assert self.svc._is_risk_upgrade("LOW", "HIGH") is True

    def test_same(self):
        assert self.svc._is_risk_upgrade("HIGH", "HIGH") is False

    def test_downgrade(self):
        assert self.svc._is_risk_upgrade("HIGH", "LOW") is False


class TestCalculateProjectRisk:

    def test_project_not_found(self):
        svc, db = _make_service()
        chain = MagicMock()
        db.query.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = None
        with pytest.raises(ValueError, match="项目不存在"):
            svc.calculate_project_risk(999)

    def test_normal_calculation(self):
        svc, db = _make_service()

        project = MagicMock()
        project.id = 1
        project.project_code = "P001"
        project.progress_pct = Decimal("50")
        project.planned_end_date = None

        # db.query().filter().first() -> project
        # db.query(func.count()).filter().scalar() -> counts
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = project
        query_mock.scalar.return_value = 0
        query_mock.all.return_value = []

        result = svc.calculate_project_risk(1)
        assert result["project_id"] == 1
        assert result["project_code"] == "P001"
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


class TestAutoUpgradeRiskLevel:

    def test_no_previous_history(self):
        svc, db = _make_service()

        project = MagicMock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "Test"
        project.progress_pct = Decimal("0")
        project.planned_end_date = None

        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.first.return_value = project  # project query
        query_mock.scalar.return_value = 0
        query_mock.all.return_value = []

        # For history query, first() should return None (no previous)
        # But we share the mock chain, so override with side_effect:
        # We need smarter mocking. Let's patch calculate_project_risk instead.
        with patch.object(svc, 'calculate_project_risk') as mock_calc:
            mock_calc.return_value = {
                "project_id": 1,
                "project_code": "P001",
                "risk_level": "LOW",
                "risk_factors": {"overdue_milestone_ratio": 0},
            }
            # history query returns None
            query_mock.first.return_value = None

            result = svc.auto_upgrade_risk_level(1)
            assert result["old_risk_level"] == "LOW"
            assert result["new_risk_level"] == "LOW"
            assert result["is_upgrade"] is False
            db.add.assert_called()
            db.commit.assert_called()

    def test_upgrade_triggers_notification(self):
        svc, db = _make_service()
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock

        # Previous history
        old_history = MagicMock()
        old_history.new_risk_level = "LOW"
        query_mock.first.return_value = old_history

        with patch.object(svc, 'calculate_project_risk') as mock_calc, \
             patch.object(svc, '_send_risk_upgrade_notification') as mock_notify:
            mock_calc.return_value = {
                "project_id": 1,
                "project_code": "P001",
                "risk_level": "CRITICAL",
                "risk_factors": {"critical_risks_count": 2},
            }
            # project query for name
            project_mock = MagicMock()
            project_mock.project_name = "TestProj"
            query_mock.first.side_effect = [old_history, project_mock]

            result = svc.auto_upgrade_risk_level(1)
            assert result["is_upgrade"] is True
            assert result["new_risk_level"] == "CRITICAL"
            mock_notify.assert_called_once()


class TestBatchCalculateRisks:

    def test_batch_with_ids(self):
        svc, db = _make_service()
        p1 = MagicMock(); p1.id = 1; p1.project_code = "P1"
        p2 = MagicMock(); p2.id = 2; p2.project_code = "P2"

        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [p1, p2]

        with patch.object(svc, 'auto_upgrade_risk_level') as mock_auto:
            mock_auto.return_value = {"project_id": 1, "risk_level": "LOW"}
            results = svc.batch_calculate_risks(project_ids=[1, 2])
            assert len(results) == 2

    def test_batch_with_error(self):
        svc, db = _make_service()
        p1 = MagicMock(); p1.id = 1; p1.project_code = "P1"

        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [p1]

        with patch.object(svc, 'auto_upgrade_risk_level', side_effect=Exception("fail")):
            results = svc.batch_calculate_risks(project_ids=[1])
            assert len(results) == 1
            assert "error" in results[0]


class TestCreateRiskSnapshot:

    def test_creates_snapshot(self):
        svc, db = _make_service()
        with patch.object(svc, 'calculate_project_risk') as mock_calc:
            mock_calc.return_value = {
                "project_id": 1,
                "risk_level": "MEDIUM",
                "risk_factors": {
                    "overdue_milestones_count": 2,
                    "total_milestones_count": 10,
                    "overdue_tasks_count": 0,
                    "open_risks_count": 1,
                    "high_risks_count": 1,
                },
            }
            snapshot = svc.create_risk_snapshot(1)
            db.add.assert_called_once()
            db.commit.assert_called_once()


class TestGetRiskHistory:

    def test_returns_history(self):
        svc, db = _make_service()
        chain = MagicMock()
        db.query.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.limit.return_value = chain
        chain.all.return_value = ["h1", "h2"]
        result = svc.get_risk_history(1)
        assert result == ["h1", "h2"]


class TestGetRiskTrend:

    def test_returns_trend(self):
        svc, db = _make_service()
        snap = MagicMock()
        snap.snapshot_date = datetime(2026, 1, 15)
        snap.risk_level = "HIGH"
        snap.overdue_milestones_count = 3
        snap.open_risks_count = 2
        snap.high_risks_count = 1

        chain = MagicMock()
        db.query.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.all.return_value = [snap]

        result = svc.get_risk_trend(1, days=30)
        assert len(result) == 1
        assert result[0]["risk_level"] == "HIGH"


class TestMilestoneFactors:

    def test_no_milestones(self):
        svc, db = _make_service()
        chain = MagicMock()
        db.query.return_value = chain
        chain.filter.return_value = chain
        chain.scalar.return_value = 0
        chain.all.return_value = []

        factors = svc._calculate_milestone_factors(1, date.today())
        assert factors["total_milestones_count"] == 0
        assert factors["overdue_milestone_ratio"] == 0

    def test_with_overdue(self):
        svc, db = _make_service()
        chain = MagicMock()
        db.query.return_value = chain
        chain.filter.return_value = chain
        chain.scalar.return_value = 4

        m = MagicMock()
        m.planned_date = date(2025, 1, 1)
        chain.all.return_value = [m]

        factors = svc._calculate_milestone_factors(1, date(2025, 6, 1))
        assert factors["overdue_milestones_count"] == 1
        assert factors["max_overdue_days"] == (date(2025, 6, 1) - date(2025, 1, 1)).days


class TestPmoRiskFactors:

    def test_no_risks(self):
        svc, db = _make_service()
        chain = MagicMock()
        db.query.return_value = chain
        chain.filter.return_value = chain
        chain.all.return_value = []
        factors = svc._calculate_pmo_risk_factors(1)
        assert factors == {"open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0}

    def test_with_risks(self):
        svc, db = _make_service()
        chain = MagicMock()
        db.query.return_value = chain
        chain.filter.return_value = chain

        r1 = MagicMock(); r1.risk_level = "HIGH"
        r2 = MagicMock(); r2.risk_level = "CRITICAL"
        r3 = MagicMock(); r3.risk_level = "MEDIUM"
        chain.all.return_value = [r1, r2, r3]

        factors = svc._calculate_pmo_risk_factors(1)
        assert factors["open_risks_count"] == 3
        assert factors["high_risks_count"] == 2  # HIGH + CRITICAL
        assert factors["critical_risks_count"] == 1


class TestProgressFactors:

    def test_no_planned_end(self):
        svc, _ = _make_service()
        project = MagicMock()
        project.progress_pct = Decimal("30")
        project.planned_end_date = None
        factors = svc._calculate_progress_factors(project)
        assert factors["progress_pct"] == 30.0
        assert factors["schedule_variance"] == 0

    def test_with_planned_dates(self):
        svc, _ = _make_service()
        project = MagicMock()
        project.progress_pct = Decimal("50")
        project.planned_end_date = date(2026, 12, 31)
        project.planned_start_date = date(2026, 1, 1)
        project.actual_start_date = date(2026, 1, 1)
        project.contract_date = None
        factors = svc._calculate_progress_factors(project)
        assert "schedule_variance" in factors


class TestRiskLevelOrder:

    def test_order(self):
        assert ProjectRiskService.RISK_LEVEL_ORDER["LOW"] < ProjectRiskService.RISK_LEVEL_ORDER["CRITICAL"]

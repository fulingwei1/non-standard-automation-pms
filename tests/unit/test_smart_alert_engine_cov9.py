# -*- coding: utf-8 -*-
"""第九批: test_smart_alert_engine_cov9.py - SmartAlertEngine 单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime, date

pytest.importorskip("app.services.shortage.smart_alert_engine")

from app.services.shortage.smart_alert_engine import SmartAlertEngine


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def engine(mock_db):
    return SmartAlertEngine(db=mock_db)


def make_alert(id=1, material_id=10, shortage_qty=Decimal("50")):
    alert = MagicMock()
    alert.id = id
    alert.material_id = material_id
    alert.shortage_qty = shortage_qty
    alert.alert_level = "HIGH"
    alert.status = "OPEN"
    alert.alert_no = "ALERT-0001"
    return alert


class TestSmartAlertEngineInit:
    def test_init(self, engine, mock_db):
        assert engine.db is mock_db


class TestCalculateAlertLevel:
    """测试告警级别计算: calculate_alert_level(shortage_qty, required_qty, days_to_shortage, is_critical_path=False)"""

    def test_level_urgent_overdue(self, engine):
        result = engine.calculate_alert_level(
            shortage_qty=Decimal("50"),
            required_qty=Decimal("100"),
            days_to_shortage=0
        )
        assert result == "URGENT"

    def test_level_info_plenty_time(self, engine):
        result = engine.calculate_alert_level(
            shortage_qty=Decimal("10"),
            required_qty=Decimal("200"),
            days_to_shortage=60
        )
        assert result == "INFO"

    def test_level_critical_path_warning(self, engine):
        result = engine.calculate_alert_level(
            shortage_qty=Decimal("40"),
            required_qty=Decimal("100"),
            days_to_shortage=5,
            is_critical_path=True
        )
        assert result in ("URGENT", "CRITICAL", "WARNING")

    def test_level_warning_short_days(self, engine):
        result = engine.calculate_alert_level(
            shortage_qty=Decimal("60"),
            required_qty=Decimal("100"),
            days_to_shortage=6
        )
        assert result in ("CRITICAL", "WARNING", "URGENT")


class TestCalculateRiskScore:
    """测试风险分数计算"""

    def test_calculate_risk_score_normal(self, engine):
        # _calculate_risk_score(delay_days, cost_impact, project_count, shortage_qty)
        result = engine._calculate_risk_score(
            delay_days=10,
            cost_impact=Decimal("20000"),
            project_count=2,
            shortage_qty=Decimal("50")
        )
        assert isinstance(result, Decimal)
        assert 0 <= result <= 100

    def test_calculate_risk_score_max(self, engine):
        result = engine._calculate_risk_score(
            delay_days=60,
            cost_impact=Decimal("200000"),
            project_count=10,
            shortage_qty=Decimal("2000")
        )
        assert result == Decimal("100")

    def test_calculate_risk_score_zero(self, engine):
        result = engine._calculate_risk_score(
            delay_days=0,
            cost_impact=Decimal("0"),
            project_count=0,
            shortage_qty=Decimal("0")
        )
        assert result == Decimal("0")


class TestGenerateAlertNo:
    """测试告警编号生成"""

    def test_generate_alert_no(self, engine, mock_db):
        mock_db.query.return_value.filter.return_value.scalar.return_value = 5
        result = engine._generate_alert_no()
        assert isinstance(result, str)
        assert result.startswith("SA")


class TestScanAndAlert:
    """测试扫描预警"""

    def test_scan_and_alert_returns_list(self, engine, mock_db):
        with patch.object(engine, "_collect_material_demands", return_value=[]):
            result = engine.scan_and_alert(project_id=None)
            assert isinstance(result, list)

    def test_scan_and_alert_with_project(self, engine, mock_db):
        with patch.object(engine, "_collect_material_demands", return_value=[]):
            result = engine.scan_and_alert(project_id=1, days_ahead=14)
            assert isinstance(result, list)


class TestGenerateSolutions:
    """测试生成解决方案"""

    def test_generate_solutions_returns_list(self, engine, mock_db):
        alert = make_alert()
        with patch.object(engine, "_generate_urgent_purchase_plan", return_value=None):
            with patch.object(engine, "_generate_substitute_plans", return_value=[]):
                with patch.object(engine, "_generate_transfer_plans", return_value=[]):
                    with patch.object(engine, "_generate_partial_delivery_plan", return_value=None):
                        with patch.object(engine, "_generate_reschedule_plan", return_value=None):
                            result = engine.generate_solutions(alert)
                            assert isinstance(result, list)

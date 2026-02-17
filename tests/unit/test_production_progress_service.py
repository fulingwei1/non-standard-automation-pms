# -*- coding: utf-8 -*-
"""
production_progress_service.py 单元测试

覆盖范围：
1. calculate_progress_deviation / _calculate_planned_progress
2. calculate_deviation_percentage
3. identify_bottlenecks / _calculate_bottleneck_level
4. evaluate_alert_rules
5. dismiss_alert
6. get_alerts
7. get_work_order_timeline
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, call

import pytest

from app.services.production_progress_service import ProductionProgressService


def _make_service():
    db = MagicMock()
    return ProductionProgressService(db), db


# =============================================================================
# calculate_progress_deviation / _calculate_planned_progress
# =============================================================================

class TestCalculateProgressDeviation:
    def test_returns_zeros_when_work_order_not_found(self):
        svc, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        plan, dev, delayed = svc.calculate_progress_deviation(999, 50)
        assert plan == 0
        assert dev == 0
        assert delayed is False

    def test_deviation_is_ahead(self):
        svc, db = _make_service()
        wo = MagicMock()
        # Plan: Jan 1 - Jan 11 (10 days), check on Jan 6 -> plan=50%
        wo.plan_start_date = date(2026, 1, 1)
        wo.plan_end_date = date(2026, 1, 11)
        db.query.return_value.filter.return_value.first.return_value = wo

        plan, dev, delayed = svc.calculate_progress_deviation(1, 70, date(2026, 1, 6))
        assert plan == 50
        assert dev == 20
        assert delayed is False

    def test_deviation_is_delayed(self):
        svc, db = _make_service()
        wo = MagicMock()
        wo.plan_start_date = date(2026, 1, 1)
        wo.plan_end_date = date(2026, 1, 11)
        db.query.return_value.filter.return_value.first.return_value = wo

        # Plan at Jan 6 is 50%, actual is 30% => dev=-20 (<-5) => delayed
        plan, dev, delayed = svc.calculate_progress_deviation(1, 30, date(2026, 1, 6))
        assert plan == 50
        assert dev == -20
        assert delayed is True

    def test_before_plan_start_returns_plan_0(self):
        svc, db = _make_service()
        wo = MagicMock()
        wo.plan_start_date = date(2026, 3, 1)
        wo.plan_end_date = date(2026, 3, 31)
        db.query.return_value.filter.return_value.first.return_value = wo

        plan, dev, delayed = svc.calculate_progress_deviation(1, 0, date(2026, 2, 1))
        assert plan == 0
        assert delayed is False

    def test_after_plan_end_returns_plan_100(self):
        svc, db = _make_service()
        wo = MagicMock()
        wo.plan_start_date = date(2026, 1, 1)
        wo.plan_end_date = date(2026, 1, 10)
        db.query.return_value.filter.return_value.first.return_value = wo

        plan, dev, delayed = svc.calculate_progress_deviation(1, 90, date(2026, 1, 20))
        assert plan == 100

    def test_no_plan_dates_returns_zero(self):
        svc, db = _make_service()
        wo = MagicMock()
        wo.plan_start_date = None
        wo.plan_end_date = None
        db.query.return_value.filter.return_value.first.return_value = wo

        plan, dev, delayed = svc.calculate_progress_deviation(1, 50)
        assert plan == 0


# =============================================================================
# calculate_deviation_percentage
# =============================================================================

class TestCalculateDeviationPercentage:
    def setup_method(self):
        self.svc, _ = _make_service()

    def test_zero_when_plan_zero(self):
        result = self.svc.calculate_deviation_percentage(10, 0)
        assert result == Decimal("0")

    def test_correct_percentage(self):
        # abs(deviation=20) / plan=50 * 100 = 40%
        result = self.svc.calculate_deviation_percentage(20, 50)
        assert result == Decimal("40")

    def test_handles_negative_deviation(self):
        result = self.svc.calculate_deviation_percentage(-15, 60)
        assert result == Decimal("25")


# =============================================================================
# _calculate_bottleneck_level
# =============================================================================

class TestCalculateBottleneckLevel:
    def setup_method(self):
        self.svc, self.db = _make_service()

    def _make_ws_status(self, utilization):
        ws = MagicMock()
        ws.capacity_utilization = utilization
        return ws

    def test_level_3_high_utilization_many_pending(self):
        ws_status = self._make_ws_status(99.0)
        # pending_count > 3
        self.db.query.return_value.filter.return_value.scalar.return_value = 5
        level, reason = self.svc._calculate_bottleneck_level(ws_status, workstation_id=1)
        assert level == 3

    def test_level_2_moderate(self):
        ws_status = self._make_ws_status(96.0)
        # pending_count = 2
        self.db.query.return_value.filter.return_value.scalar.return_value = 2
        level, reason = self.svc._calculate_bottleneck_level(ws_status, workstation_id=1)
        assert level == 2

    def test_level_1_light(self):
        ws_status = self._make_ws_status(92.0)
        # pending_count = 0
        self.db.query.return_value.filter.return_value.scalar.return_value = 0
        level, reason = self.svc._calculate_bottleneck_level(ws_status, workstation_id=1)
        assert level == 1

    def test_level_0_normal(self):
        ws_status = self._make_ws_status(85.0)
        self.db.query.return_value.filter.return_value.scalar.return_value = 0
        level, reason = self.svc._calculate_bottleneck_level(ws_status, workstation_id=1)
        assert level == 0


# =============================================================================
# evaluate_alert_rules
# =============================================================================

class TestEvaluateAlertRules:
    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_returns_empty_when_work_order_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        alerts = self.svc.evaluate_alert_rules(999, user_id=1)
        assert alerts == []

    def test_generates_critical_delay_alert(self):
        wo = MagicMock()
        wo.id = 1
        wo.work_order_no = "WO-001"
        wo.progress = 20  # actual
        wo.workstation_id = None
        wo.completed_qty = 0
        wo.standard_hours = None
        wo.actual_hours = None
        wo.plan_start_date = date.today() - timedelta(days=20)
        wo.plan_end_date = date.today() + timedelta(days=5)  # plan progress ~80%

        self.db.query.return_value.filter.return_value.first.return_value = wo
        self.db.query.return_value.filter.return_value.scalar.return_value = None

        alerts = self.svc.evaluate_alert_rules(1, user_id=1)
        # 实际20% vs 计划~80%，偏差=-60 < -20, 应触发CRITICAL
        assert any(a.alert_level == "CRITICAL" for a in alerts)
        assert any(a.alert_type == "DELAY" for a in alerts)

    def test_generates_quality_alert_when_quality_low(self):
        wo = MagicMock()
        wo.id = 1
        wo.work_order_no = "WO-002"
        wo.progress = 100
        wo.plan_start_date = None
        wo.plan_end_date = None
        wo.workstation_id = None
        wo.completed_qty = 100
        wo.qualified_qty = 80  # quality_rate = 80% < 95%
        wo.standard_hours = None
        wo.actual_hours = None

        self.db.query.return_value.filter.return_value.first.return_value = wo

        alerts = self.svc.evaluate_alert_rules(1, user_id=1)
        assert any(a.alert_type == "QUALITY" for a in alerts)

    def test_generates_efficiency_alert(self):
        wo = MagicMock()
        wo.id = 1
        wo.work_order_no = "WO-003"
        wo.progress = 100
        wo.plan_start_date = None
        wo.plan_end_date = None
        wo.workstation_id = None
        wo.completed_qty = 0
        wo.standard_hours = Decimal("8")
        wo.actual_hours = Decimal("15")  # efficiency = 8/15*100 ≈ 53% < 80%

        self.db.query.return_value.filter.return_value.first.return_value = wo

        alerts = self.svc.evaluate_alert_rules(1, user_id=1)
        assert any(a.alert_type == "EFFICIENCY" for a in alerts)

    def test_generates_bottleneck_alert(self):
        wo = MagicMock()
        wo.id = 1
        wo.work_order_no = "WO-004"
        wo.progress = 50
        wo.plan_start_date = None
        wo.plan_end_date = None
        wo.workstation_id = 10
        wo.completed_qty = 0
        wo.standard_hours = None
        wo.actual_hours = None

        ws_status = MagicMock()
        ws_status.is_bottleneck = True
        ws_status.bottleneck_level = 2
        ws_status.capacity_utilization = Decimal("96")

        def side_effect_first(*args, **kwargs):
            # First call: work order, second: ws_status
            call_count = side_effect_first.count
            side_effect_first.count += 1
            if call_count == 0:
                return wo
            return ws_status
        side_effect_first.count = 0

        self.db.query.return_value.filter.return_value.first.side_effect = side_effect_first

        alerts = self.svc.evaluate_alert_rules(1, user_id=1)
        assert any(a.alert_type == "BOTTLENECK" for a in alerts)


# =============================================================================
# dismiss_alert
# =============================================================================

class TestDismissAlert:
    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_returns_false_when_alert_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.svc.dismiss_alert(999, user_id=1)
        assert result is False

    def test_dismisses_alert_successfully(self):
        alert = MagicMock()
        alert.status = "ACTIVE"
        self.db.query.return_value.filter.return_value.first.return_value = alert

        result = self.svc.dismiss_alert(1, user_id=10, note="已解决")
        assert result is True
        assert alert.status == "DISMISSED"
        assert alert.dismissed_by == 10
        assert alert.resolution_note == "已解决"
        self.db.commit.assert_called_once()

    def test_dismiss_without_note(self):
        alert = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = alert

        result = self.svc.dismiss_alert(1, user_id=5)
        assert result is True
        # note should NOT be set
        alert.resolution_note.__set__.assert_not_called() if hasattr(alert.resolution_note, '__set__') else None


# =============================================================================
# get_alerts
# =============================================================================

class TestGetAlerts:
    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_returns_all_active_alerts_by_default(self):
        mock_alerts = [MagicMock(), MagicMock()]
        query_chain = self.db.query.return_value
        query_chain.filter.return_value = query_chain
        query_chain.order_by.return_value.all.return_value = mock_alerts

        result = self.svc.get_alerts()
        assert len(result) == 2

    def test_filters_by_work_order_id(self):
        mock_alerts = [MagicMock()]
        query_chain = self.db.query.return_value
        query_chain.filter.return_value = query_chain
        query_chain.order_by.return_value.all.return_value = mock_alerts

        result = self.svc.get_alerts(work_order_id=5)
        assert len(result) == 1

    def test_filters_by_alert_type_and_level(self):
        mock_alerts = []
        query_chain = self.db.query.return_value
        query_chain.filter.return_value = query_chain
        query_chain.order_by.return_value.all.return_value = mock_alerts

        result = self.svc.get_alerts(alert_type="DELAY", alert_level="CRITICAL")
        assert result == []


# =============================================================================
# get_work_order_timeline
# =============================================================================

class TestGetWorkOrderTimeline:
    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_returns_none_when_work_order_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.svc.get_work_order_timeline(999)
        assert result is None

    def test_returns_timeline_object(self):
        wo = MagicMock()
        wo.id = 1
        wo.work_order_no = "WO-001"
        wo.task_name = "测试任务"
        wo.progress = 60
        wo.status = "IN_PROGRESS"
        wo.plan_start_date = date(2026, 1, 1)
        wo.plan_end_date = date(2026, 2, 1)
        wo.actual_start_time = None
        wo.actual_end_time = None

        self.db.query.return_value.filter.return_value.first.return_value = wo
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = self.svc.get_work_order_timeline(1)
        assert result is not None
        assert result.work_order_id == 1
        assert result.work_order_no == "WO-001"

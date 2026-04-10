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
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from app.services.production_progress_service import ProductionProgressService
from app.schemas.production_progress import ProductionProgressLogCreate


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

        # First call: work order for evaluate_alert_rules
        # Second call: work order inside calculate_progress_deviation
        # Third call: ws_status
        self.db.query.return_value.filter.return_value.first.side_effect = [wo, wo, ws_status]

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
        (
            alert.resolution_note.__set__.assert_not_called()
            if hasattr(alert.resolution_note, "__set__")
            else None
        )


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


# =============================================================================
# create_progress_log / realtime overview / deviations
# =============================================================================


class TestCreateProgressLog:
    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_raises_when_work_order_not_found(self):
        q1 = MagicMock()
        q1.filter.return_value.first.return_value = None
        self.db.query.side_effect = [q1]

        log_data = ProductionProgressLogCreate(
            work_order_id=999,
            workstation_id=10,
            current_progress=20,
            completed_qty=5,
            qualified_qty=5,
            defect_qty=0,
            work_hours=Decimal("1.5"),
            status="IN_PROGRESS",
            note="test",
        )

        with pytest.raises(ValueError, match="工单不存在"):
            self.svc.create_progress_log(log_data, user_id=1)

    @patch.object(ProductionProgressService, "_update_workstation_status")
    @patch.object(ProductionProgressService, "evaluate_alert_rules")
    @patch.object(ProductionProgressService, "calculate_progress_deviation")
    def test_creates_progress_log_and_new_alert(
        self, mock_calc, mock_eval, mock_update_ws
    ):
        work_order = MagicMock()
        work_order.id = 1
        work_order.status = "IN_PROGRESS"
        work_order.actual_hours = Decimal("1.5")

        last_log = MagicMock()
        last_log.current_progress = 40
        last_log.status = "IN_PROGRESS"
        last_log.cumulative_hours = Decimal("2.5")

        q1 = MagicMock()
        q1.filter.return_value.first.return_value = work_order
        q2 = MagicMock()
        q2.filter.return_value.order_by.return_value.first.return_value = last_log
        q3 = MagicMock()
        q3.filter.return_value.first.return_value = None
        self.db.query.side_effect = [q1, q2, q3]

        mock_calc.return_value = (55, 5, False)
        alert_data = MagicMock()
        alert_data.work_order_id = 1
        alert_data.alert_type = "DELAY"
        alert_data.model_dump.return_value = {
            "work_order_id": 1,
            "workstation_id": 10,
            "alert_type": "DELAY",
            "alert_level": "WARNING",
            "alert_title": "进度延期预警",
            "alert_message": "测试",
        }
        mock_eval.return_value = [alert_data]

        log_data = ProductionProgressLogCreate(
            work_order_id=1,
            workstation_id=10,
            current_progress=60,
            completed_qty=12,
            qualified_qty=11,
            defect_qty=1,
            work_hours=Decimal("2.5"),
            status="IN_PROGRESS",
            note="继续推进",
        )

        result = self.svc.create_progress_log(log_data, user_id=9)

        assert result.work_order_id == 1
        assert result.previous_progress == 40
        assert result.progress_delta == 20
        assert result.cumulative_hours == Decimal("5.0")
        assert result.plan_progress == 55
        assert result.deviation == 5
        assert result.is_delayed == 0

        assert work_order.progress == 60
        assert work_order.status == "IN_PROGRESS"
        assert work_order.completed_qty == 12
        assert work_order.qualified_qty == 11
        assert work_order.defect_qty == 1
        assert work_order.actual_hours == Decimal("4.0")

        assert self.db.add.call_count == 2
        mock_update_ws.assert_called_once_with(10, 1)
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(result)


class TestRealtimeOverviewAndRealtimeStatus:
    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_get_realtime_overview_with_workshop_filter(self):
        q_work_order = MagicMock()
        q_work_order.filter.return_value = q_work_order
        q_work_order.count.side_effect = [10, 4, 2]

        q_delayed = MagicMock()
        q_delayed.filter.return_value = q_delayed
        q_delayed.distinct.return_value = q_delayed
        q_delayed.join.return_value = q_delayed
        q_delayed.count.return_value = 3

        q_workstation = MagicMock()
        q_workstation.join.return_value = q_workstation
        q_workstation.filter.return_value = q_workstation
        q_workstation.count.side_effect = [5, 2, 1]

        q_alert = MagicMock()
        q_alert.filter.return_value = q_alert
        q_alert.join.return_value = q_alert
        q_alert.count.side_effect = [7, 2]

        q_avg_progress = MagicMock()
        q_avg_progress.filter.return_value = q_avg_progress
        q_avg_progress.scalar.return_value = Decimal("66.6")

        q_avg_utilization = MagicMock()
        q_avg_utilization.join.return_value = q_avg_utilization
        q_avg_utilization.filter.return_value = q_avg_utilization
        q_avg_utilization.scalar.return_value = Decimal("88.8")

        q_avg_efficiency = MagicMock()
        q_avg_efficiency.join.return_value = q_avg_efficiency
        q_avg_efficiency.filter.return_value = q_avg_efficiency
        q_avg_efficiency.scalar.return_value = Decimal("77.7")

        self.db.query.side_effect = [
            q_work_order,
            q_delayed,
            q_workstation,
            q_alert,
            q_avg_progress,
            q_avg_utilization,
            q_avg_efficiency,
        ]

        result = self.svc.get_realtime_overview(workshop_id=9)

        assert result.total_work_orders == 10
        assert result.in_progress == 4
        assert result.completed_today == 2
        assert result.delayed == 3
        assert result.active_workstations == 5
        assert result.idle_workstations == 2
        assert result.bottleneck_workstations == 1
        assert result.active_alerts == 7
        assert result.critical_alerts == 2
        assert result.overall_progress == Decimal("66.6")
        assert result.overall_capacity_utilization == Decimal("88.8")
        assert result.efficiency_rate == Decimal("77.7")

    def test_get_workstation_realtime_returns_first_match(self):
        ws_status = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = ws_status

        result = self.svc.get_workstation_realtime(7)
        assert result is ws_status


class TestGetProgressDeviationsExtended:
    def setup_method(self):
        self.svc, self.db = _make_service()

    @patch("app.services.production_progress_service.datetime")
    def test_get_progress_deviations_covers_risk_levels_and_estimation(self, mock_datetime):
        now = datetime(2026, 4, 10, 12, 0, 0)
        mock_datetime.now.return_value = now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        wo_critical = MagicMock()
        wo_critical.id = 1
        wo_critical.work_order_no = "WO-CRITICAL"
        wo_critical.task_name = "关键工单"
        wo_critical.progress = 50
        wo_critical.plan_end_date = date(2026, 4, 12)
        wo_critical.actual_start_time = now - timedelta(days=5)

        wo_high = MagicMock()
        wo_high.id = 2
        wo_high.work_order_no = "WO-HIGH"
        wo_high.task_name = "高风险工单"
        wo_high.progress = 40
        wo_high.plan_end_date = date(2026, 4, 20)
        wo_high.actual_start_time = None

        wo_medium = MagicMock()
        wo_medium.id = 3
        wo_medium.work_order_no = "WO-MEDIUM"
        wo_medium.task_name = "中风险工单"
        wo_medium.progress = 30
        wo_medium.plan_end_date = None
        wo_medium.actual_start_time = None

        wo_low = MagicMock()
        wo_low.id = 4
        wo_low.work_order_no = "WO-LOW"
        wo_low.task_name = "低风险工单"
        wo_low.progress = 80
        wo_low.plan_end_date = None
        wo_low.actual_start_time = None

        wo_skipped = MagicMock()
        wo_skipped.id = 5
        wo_skipped.work_order_no = "WO-SKIP"
        wo_skipped.task_name = "跳过工单"
        wo_skipped.progress = 20
        wo_skipped.plan_end_date = None
        wo_skipped.actual_start_time = None

        query_chain = MagicMock()
        query_chain.filter.return_value = query_chain
        query_chain.all.return_value = [wo_critical, wo_high, wo_medium, wo_low, wo_skipped]
        self.db.query.return_value = query_chain

        with patch.object(
            self.svc,
            "calculate_progress_deviation",
            side_effect=[
                (80, -30, True),
                (70, -18, True),
                (60, -12, True),
                (60, 12, True),
                (50, 10, False),
            ],
        ):
            result = self.svc.get_progress_deviations(workshop_id=3)

        assert [item.risk_level for item in result] == ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert result[0].work_order_no == "WO-CRITICAL"
        assert result[0].estimated_completion_date is not None
        assert result[0].delay_days is not None
        assert query_chain.filter.call_count >= 2


class TestGetAlertsExtended:
    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_filters_by_workstation_and_status(self):
        mock_alerts = [MagicMock()]
        query_chain = self.db.query.return_value
        query_chain.filter.return_value = query_chain
        query_chain.order_by.return_value.all.return_value = mock_alerts

        result = self.svc.get_alerts(workstation_id=8, status="DISMISSED")
        assert result == mock_alerts


class TestIdentifyBottlenecks:
    def setup_method(self):
        self.svc, self.db = _make_service()

    @patch.object(ProductionProgressService, "_calculate_bottleneck_level")
    def test_identify_bottlenecks_sorted_and_counted(self, mock_level):
        ws_status_1 = MagicMock()
        ws_status_1.capacity_utilization = Decimal("96")
        ws_status_1.work_hours_today = Decimal("6")
        ws_status_1.idle_hours_today = Decimal("2")
        ws_status_1.alert_count = 1

        ws_status_2 = MagicMock()
        ws_status_2.capacity_utilization = Decimal("99")
        ws_status_2.work_hours_today = Decimal("7")
        ws_status_2.idle_hours_today = Decimal("1")
        ws_status_2.alert_count = 3

        workstation_1 = MagicMock()
        workstation_1.id = 11
        workstation_1.workstation_code = "WS-11"
        workstation_1.workstation_name = "工位11"

        workstation_2 = MagicMock()
        workstation_2.id = 22
        workstation_2.workstation_code = "WS-22"
        workstation_2.workstation_name = "工位22"

        q_results = MagicMock()
        q_results.join.return_value = q_results
        q_results.filter.return_value = q_results
        q_results.all.return_value = [
            (ws_status_1, workstation_1),
            (ws_status_2, workstation_2),
        ]

        q_cur_1 = MagicMock()
        q_cur_1.filter.return_value.scalar.return_value = 1
        q_pen_1 = MagicMock()
        q_pen_1.filter.return_value.scalar.return_value = 2
        q_cur_2 = MagicMock()
        q_cur_2.filter.return_value.scalar.return_value = 3
        q_pen_2 = MagicMock()
        q_pen_2.filter.return_value.scalar.return_value = 4

        self.db.query.side_effect = [q_results, q_cur_1, q_pen_1, q_cur_2, q_pen_2]
        mock_level.side_effect = [
            (2, "中度瓶颈"),
            (3, "严重瓶颈"),
        ]

        result = self.svc.identify_bottlenecks(workshop_id=5, min_level=2)

        assert len(result) == 2
        assert result[0]["workstation_id"] == 22
        assert result[0]["bottleneck_level"] == 3
        assert result[0]["current_work_order_count"] == 3
        assert result[0]["pending_work_order_count"] == 4
        assert result[1]["workstation_id"] == 11
        assert result[1]["bottleneck_level"] == 2


class TestEvaluateAlertRulesExtended:
    def setup_method(self):
        self.svc, self.db = _make_service()

    @patch.object(ProductionProgressService, "calculate_progress_deviation")
    def test_generates_warning_delay_alert(self, mock_calc):
        wo = MagicMock()
        wo.id = 1
        wo.work_order_no = "WO-WARN"
        wo.progress = 35
        wo.workstation_id = None
        wo.completed_qty = 0
        wo.standard_hours = None
        wo.actual_hours = None

        self.db.query.return_value.filter.return_value.first.return_value = wo
        mock_calc.return_value = (50, -15, True)

        alerts = self.svc.evaluate_alert_rules(1, user_id=1)

        assert any(a.alert_type == "DELAY" and a.alert_level == "WARNING" for a in alerts)
        assert any(a.rule_code == "RULE_DELAY_WARNING" for a in alerts)


class TestUpdateWorkstationStatus:
    def setup_method(self):
        self.svc, self.db = _make_service()

    @patch("app.services.production_progress_service.WorkstationStatus")
    @patch.object(ProductionProgressService, "_calculate_bottleneck_level")
    def test_create_new_workstation_status(self, mock_level, mock_ws_cls):
        ws_status = MagicMock()
        ws_status.planned_hours_today = Decimal("8")
        mock_ws_cls.return_value = ws_status

        q1 = MagicMock()
        q1.filter.return_value.first.return_value = None
        q2 = MagicMock()
        q2.filter.return_value.scalar.return_value = Decimal("4")
        self.db.query.side_effect = [q1, q2]
        mock_level.return_value = (2, "中度")

        self.svc._update_workstation_status(10, 99)

        mock_ws_cls.assert_called_once()
        assert mock_ws_cls.call_args.kwargs["workstation_id"] == 10
        assert mock_ws_cls.call_args.kwargs["current_state"] == "BUSY"
        assert mock_ws_cls.call_args.kwargs["current_work_order_id"] == 99
        self.db.add.assert_called_with(ws_status)
        assert ws_status.work_hours_today == Decimal("4")
        assert ws_status.capacity_utilization == Decimal("50")
        assert ws_status.is_bottleneck == 1
        assert ws_status.bottleneck_level == 2

    @patch.object(ProductionProgressService, "_calculate_bottleneck_level")
    def test_update_existing_workstation_status_with_zero_plan_hours(self, mock_level):
        ws_status = MagicMock()
        ws_status.planned_hours_today = Decimal("0")

        q1 = MagicMock()
        q1.filter.return_value.first.return_value = ws_status
        q2 = MagicMock()
        q2.filter.return_value.scalar.return_value = Decimal("5")
        self.db.query.side_effect = [q1, q2]
        mock_level.return_value = (0, "正常")

        self.svc._update_workstation_status(12, 88)

        assert ws_status.current_work_order_id == 88
        assert ws_status.current_state == "BUSY"
        assert ws_status.work_hours_today == Decimal("5")
        assert ws_status.capacity_utilization == Decimal("0")
        assert ws_status.is_bottleneck == 0
        assert ws_status.bottleneck_level == 0


class TestGetProgressDeviationsMore:
    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_skips_small_deviation(self):
        wo = MagicMock()
        wo.id = 1
        wo.work_order_no = "WO-SMALL"
        wo.task_name = "小偏差工单"
        wo.progress = 55
        wo.plan_end_date = None
        wo.actual_start_time = None

        query_chain = MagicMock()
        query_chain.filter.return_value = query_chain
        query_chain.all.return_value = [wo]
        self.db.query.return_value = query_chain

        with patch.object(self.svc, "calculate_progress_deviation", return_value=(60, -9, True)):
            result = self.svc.get_progress_deviations(only_delayed=False)

        assert result == []

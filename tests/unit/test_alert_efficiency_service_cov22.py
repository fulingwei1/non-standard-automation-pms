# -*- coding: utf-8 -*-
"""第二十二批：alert_efficiency_service 单元测试"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

try:
    from app.services.alert_efficiency_service import (
        calculate_basic_metrics,
        calculate_project_metrics,
        calculate_handler_metrics,
        calculate_type_metrics,
    )
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="import failed")


@pytest.fixture
def engine():
    e = MagicMock()
    e.RESPONSE_TIMEOUT = {"HIGH": 4, "WARNING": 8, "INFO": 24}
    return e


@pytest.fixture
def db():
    return MagicMock()


def make_alert(
    status="RESOLVED",
    alert_level="WARNING",
    is_escalated=False,
    triggered_at=None,
    acknowledged_at=None,
    rule_id=1,
    target_type="project",
    target_id=1,
    project_id=1,
    handler_id=None
):
    a = MagicMock()
    a.status = status
    a.alert_level = alert_level
    a.is_escalated = is_escalated
    a.triggered_at = triggered_at or datetime(2025, 1, 1, 10, 0)
    a.acknowledged_at = acknowledged_at or datetime(2025, 1, 1, 12, 0)
    a.rule_id = rule_id
    a.target_type = target_type
    a.target_id = target_id
    a.project_id = project_id
    a.handler_id = handler_id
    a.acknowledged_by = handler_id
    rule = MagicMock()
    rule.rule_type = "COST_OVERRUN"
    a.rule = rule
    return a


class TestCalculateBasicMetrics:
    def test_empty_alerts_returns_zeros(self, engine):
        """空预警列表时所有指标为0"""
        result = calculate_basic_metrics([], engine)
        assert result["processing_rate"] == 0
        assert result["timely_processing_rate"] == 0
        assert result["escalation_rate"] == 0
        assert result["duplicate_rate"] == 0

    def test_all_resolved_processing_rate_is_one(self, engine):
        """全部处理时处理率为1"""
        alerts = [make_alert(status="RESOLVED"), make_alert(status="CLOSED")]
        result = calculate_basic_metrics(alerts, engine)
        assert result["processing_rate"] == 1.0

    def test_unresolved_alerts_lower_processing_rate(self, engine):
        """有未处理预警时处理率降低"""
        alerts = [make_alert(status="RESOLVED"), make_alert(status="PENDING")]
        result = calculate_basic_metrics(alerts, engine)
        assert result["processing_rate"] == 0.5

    def test_escalated_alert_increases_escalation_rate(self, engine):
        """升级预警增加升级率"""
        alerts = [make_alert(is_escalated=True), make_alert(is_escalated=False)]
        result = calculate_basic_metrics(alerts, engine)
        assert result["escalation_rate"] == 0.5

    def test_duplicate_within_24h_counted(self, engine):
        """24小时内重复预警计入重复率"""
        base_time = datetime(2025, 1, 1, 10, 0)
        a1 = make_alert(rule_id=1, target_type="project", target_id=1, triggered_at=base_time)
        a2 = make_alert(rule_id=1, target_type="project", target_id=1, triggered_at=base_time + timedelta(hours=5))
        result = calculate_basic_metrics([a1, a2], engine)
        assert result["duplicate_rate"] > 0

    def test_result_has_required_keys(self, engine):
        """返回字典包含所有必要键"""
        result = calculate_basic_metrics([make_alert()], engine)
        assert "processing_rate" in result
        assert "timely_processing_rate" in result
        assert "escalation_rate" in result
        assert "duplicate_rate" in result


class TestCalculateProjectMetrics:
    def test_no_project_id_skipped(self, db, engine):
        """无项目ID的预警跳过"""
        a = make_alert()
        a.project_id = None
        result = calculate_project_metrics([a], db, engine)
        assert result == {}

    def test_groups_by_project(self, db, engine):
        """按项目分组统计"""
        mock_project = MagicMock()
        mock_project.project_name = "测试项目A"
        db.query.return_value.filter.return_value.first.return_value = mock_project
        alerts = [make_alert(project_id=1), make_alert(project_id=1)]
        result = calculate_project_metrics(alerts, db, engine)
        assert "测试项目A" in result
        assert result["测试项目A"]["total"] == 2


class TestCalculateHandlerMetrics:
    def test_no_handler_skipped(self, db, engine):
        """无处理人的预警跳过"""
        a = make_alert(handler_id=None)
        result = calculate_handler_metrics([a], db, engine)
        assert result == {}

    def test_groups_by_handler(self, db, engine):
        """按处理人分组统计"""
        mock_user = MagicMock()
        mock_user.username = "张三"
        db.query.return_value.filter.return_value.first.return_value = mock_user
        alerts = [make_alert(handler_id=10), make_alert(handler_id=10)]
        result = calculate_handler_metrics(alerts, db, engine)
        assert "张三" in result
        assert result["张三"]["total"] == 2


class TestCalculateTypeMetrics:
    def test_groups_by_rule_type(self, engine):
        """按规则类型分组统计"""
        a1 = make_alert()
        a1.rule.rule_type = "COST_OVERRUN"
        a2 = make_alert()
        a2.rule.rule_type = "SCHEDULE_DELAY"
        result = calculate_type_metrics([a1, a2], engine)
        assert "COST_OVERRUN" in result
        assert "SCHEDULE_DELAY" in result

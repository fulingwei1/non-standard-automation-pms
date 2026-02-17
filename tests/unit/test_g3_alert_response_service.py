# -*- coding: utf-8 -*-
"""
G3组 - 预警响应时效分析服务单元测试
目标文件: app/services/alert_response_service.py
"""
import pytest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.alert_response_service import (
    calculate_response_times,
    calculate_resolve_times,
    calculate_response_distribution,
    calculate_level_metrics,
    calculate_type_metrics,
    calculate_project_metrics,
)


def make_alert(triggered_at=None, acknowledged_at=None,
               handle_end_at=None, alert_level="WARNING", rule_type="THRESHOLD",
               project_id=1):
    """工厂：创建模拟告警对象"""
    alert = MagicMock()
    alert.triggered_at = triggered_at
    alert.acknowledged_at = acknowledged_at
    alert.handle_end_at = handle_end_at
    alert.alert_level = alert_level
    mock_rule = MagicMock()
    mock_rule.rule_type = rule_type
    alert.rule = mock_rule
    alert.project_id = project_id
    return alert


class TestCalculateResponseTimes:
    """测试响应时间计算"""

    def test_empty_list(self):
        result = calculate_response_times([])
        assert result == []

    def test_alert_missing_triggered_at(self):
        alert = make_alert(triggered_at=None, acknowledged_at=datetime.now())
        result = calculate_response_times([alert])
        assert result == []

    def test_alert_missing_acknowledged_at(self):
        alert = make_alert(triggered_at=datetime.now(), acknowledged_at=None)
        result = calculate_response_times([alert])
        assert result == []

    def test_single_alert_30_min(self):
        t0 = datetime(2026, 1, 1, 10, 0, 0)
        t1 = datetime(2026, 1, 1, 10, 30, 0)
        alert = make_alert(triggered_at=t0, acknowledged_at=t1)
        result = calculate_response_times([alert])

        assert len(result) == 1
        assert abs(result[0]["minutes"] - 30.0) < 0.01
        assert abs(result[0]["hours"] - 0.5) < 0.001
        assert result[0]["alert"] is alert

    def test_multiple_alerts(self):
        now = datetime(2026, 1, 1, 12, 0, 0)
        alerts = [
            make_alert(triggered_at=now, acknowledged_at=now + timedelta(minutes=60)),
            make_alert(triggered_at=now, acknowledged_at=now + timedelta(hours=2)),
        ]
        result = calculate_response_times(alerts)
        assert len(result) == 2
        assert result[0]["minutes"] == 60
        assert result[1]["hours"] == 2.0


class TestCalculateResolveTimes:
    """测试解决时间计算"""

    def test_empty_list(self):
        result = calculate_resolve_times([])
        assert result == []

    def test_missing_handle_end_at(self):
        alert = make_alert(acknowledged_at=datetime.now(), handle_end_at=None)
        result = calculate_resolve_times([alert])
        assert result == []

    def test_resolve_time_90_min(self):
        t0 = datetime(2026, 1, 1, 8, 0, 0)
        t1 = datetime(2026, 1, 1, 9, 30, 0)
        alert = make_alert(acknowledged_at=t0, handle_end_at=t1)
        result = calculate_resolve_times([alert])

        assert len(result) == 1
        assert abs(result[0]["minutes"] - 90.0) < 0.01
        assert abs(result[0]["hours"] - 1.5) < 0.001


class TestCalculateResponseDistribution:
    """测试响应时效分布统计"""

    def _make_rt(self, hours):
        return {"hours": hours, "minutes": hours * 60, "alert": MagicMock()}

    def test_empty_input(self):
        result = calculate_response_distribution([])
        assert result["<1小时"] == 0
        assert result["1-4小时"] == 0
        assert result["4-8小时"] == 0
        assert result[">8小时"] == 0

    def test_under_1_hour(self):
        rt = self._make_rt(0.5)
        result = calculate_response_distribution([rt])
        assert result["<1小时"] == 1

    def test_1_to_4_hours(self):
        rt = self._make_rt(2.0)
        result = calculate_response_distribution([rt])
        assert result["1-4小时"] == 1

    def test_4_to_8_hours(self):
        rt = self._make_rt(6.0)
        result = calculate_response_distribution([rt])
        assert result["4-8小时"] == 1

    def test_over_8_hours(self):
        rt = self._make_rt(10.0)
        result = calculate_response_distribution([rt])
        assert result[">8小时"] == 1

    def test_mixed_distribution(self):
        rts = [
            self._make_rt(0.3),
            self._make_rt(2.5),
            self._make_rt(5.0),
            self._make_rt(9.0),
            self._make_rt(0.9),
        ]
        result = calculate_response_distribution(rts)
        assert result["<1小时"] == 2
        assert result["1-4小时"] == 1
        assert result["4-8小时"] == 1
        assert result[">8小时"] == 1


class TestCalculateLevelMetrics:
    """测试按级别统计响应时效"""

    def _make_rt(self, hours, level):
        alert = MagicMock()
        alert.alert_level = level
        return {"hours": hours, "alert": alert}

    def test_empty_input(self):
        result = calculate_level_metrics([])
        assert result == {}

    def test_single_level(self):
        rts = [self._make_rt(1.0, "WARNING"), self._make_rt(3.0, "WARNING")]
        result = calculate_level_metrics(rts)
        assert "WARNING" in result
        assert result["WARNING"]["count"] == 2
        assert abs(result["WARNING"]["avg_hours"] - 2.0) < 0.001
        assert result["WARNING"]["min_hours"] == 1.0
        assert result["WARNING"]["max_hours"] == 3.0

    def test_multiple_levels(self):
        rts = [
            self._make_rt(0.5, "INFO"),
            self._make_rt(2.0, "WARNING"),
            self._make_rt(5.0, "CRITICAL"),
        ]
        result = calculate_level_metrics(rts)
        assert "INFO" in result
        assert "WARNING" in result
        assert "CRITICAL" in result

    def test_none_level_uses_unknown(self):
        alert = MagicMock()
        alert.alert_level = None
        rt = {"hours": 1.0, "alert": alert}
        result = calculate_level_metrics([rt])
        assert "UNKNOWN" in result


class TestCalculateTypeMetrics:
    """测试按规则类型统计响应时效"""

    def _make_rt(self, hours, rule_type):
        alert = MagicMock()
        rule = MagicMock()
        rule.rule_type = rule_type
        alert.rule = rule
        return {"hours": hours, "alert": alert}

    def test_empty_input(self):
        result = calculate_type_metrics([])
        assert result == {}

    def test_single_type(self):
        rts = [self._make_rt(2.0, "THRESHOLD"), self._make_rt(4.0, "THRESHOLD")]
        result = calculate_type_metrics(rts)
        assert "THRESHOLD" in result
        assert result["THRESHOLD"]["count"] == 2

    def test_no_rule_uses_unknown(self):
        alert = MagicMock()
        alert.rule = None
        rt = {"hours": 1.5, "alert": alert}
        result = calculate_type_metrics([rt])
        assert "UNKNOWN" in result


class TestCalculateProjectMetrics:
    """测试按项目统计响应时效"""

    def _make_rt(self, hours, project_id):
        alert = MagicMock()
        alert.project_id = project_id
        return {"hours": hours, "alert": alert}

    def test_empty_input(self):
        db = MagicMock()
        result = calculate_project_metrics([], db)
        assert result == {}

    def test_metrics_aggregated_by_project(self):
        db = MagicMock()
        # 模拟 Project 查询
        mock_project = MagicMock()
        mock_project.project_name = "项目A"
        db.query.return_value.filter.return_value.first.return_value = mock_project

        rts = [self._make_rt(1.0, 1), self._make_rt(3.0, 1), self._make_rt(2.0, 2)]
        result = calculate_project_metrics(rts, db)

        assert len(result) >= 1

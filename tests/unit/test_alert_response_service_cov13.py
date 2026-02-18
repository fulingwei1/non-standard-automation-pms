# -*- coding: utf-8 -*-
"""第十三批 - 预警响应时效分析服务 单元测试"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta

try:
    from app.services.alert_response_service import (
        calculate_response_times,
        calculate_resolve_times,
        calculate_response_distribution,
    )
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_alert(triggered_delta_min=0, acknowledged_delta_min=30, handle_end_delta_min=120):
    """创建模拟预警记录"""
    alert = MagicMock()
    base = datetime(2024, 1, 1, 8, 0, 0)
    alert.triggered_at = base + timedelta(minutes=triggered_delta_min)
    alert.acknowledged_at = base + timedelta(minutes=acknowledged_delta_min)
    alert.handle_end_at = base + timedelta(minutes=handle_end_delta_min)
    return alert


class TestCalculateResponseTimes:
    def test_single_alert(self):
        """单条预警响应时间计算"""
        alert = make_alert(0, 30)
        result = calculate_response_times([alert])
        assert len(result) == 1
        assert abs(result[0]['minutes'] - 30) < 0.01
        assert abs(result[0]['hours'] - 0.5) < 0.01

    def test_missing_triggered_at_skipped(self):
        """缺少triggered_at的预警被跳过"""
        alert = MagicMock()
        alert.triggered_at = None
        alert.acknowledged_at = datetime.now()
        result = calculate_response_times([alert])
        assert len(result) == 0

    def test_missing_acknowledged_at_skipped(self):
        """缺少acknowledged_at的预警被跳过"""
        alert = MagicMock()
        alert.triggered_at = datetime.now()
        alert.acknowledged_at = None
        result = calculate_response_times([alert])
        assert len(result) == 0

    def test_multiple_alerts(self):
        """多条预警"""
        alerts = [make_alert(0, 30), make_alert(0, 60), make_alert(0, 120)]
        result = calculate_response_times(alerts)
        assert len(result) == 3


class TestCalculateResolveTimes:
    def test_resolve_time_calculation(self):
        """解决时间计算（确认到完成）"""
        alert = make_alert(0, 30, 150)
        result = calculate_resolve_times([alert])
        assert len(result) == 1
        assert abs(result[0]['minutes'] - 120) < 0.01


class TestCalculateResponseDistribution:
    def test_distribution_under_1h(self):
        """小于1小时分布"""
        rt = [{'hours': 0.5, 'minutes': 30, 'alert': MagicMock()}]
        dist = calculate_response_distribution(rt)
        assert dist['<1小时'] == 1

    def test_distribution_1_4h(self):
        """1-4小时分布"""
        rt = [{'hours': 2, 'minutes': 120, 'alert': MagicMock()}]
        dist = calculate_response_distribution(rt)
        assert dist['1-4小时'] == 1

    def test_distribution_4_8h(self):
        """4-8小时分布"""
        rt = [{'hours': 6, 'minutes': 360, 'alert': MagicMock()}]
        dist = calculate_response_distribution(rt)
        assert dist['4-8小时'] == 1

    def test_distribution_over_8h(self):
        """超过8小时分布"""
        rt = [{'hours': 12, 'minutes': 720, 'alert': MagicMock()}]
        dist = calculate_response_distribution(rt)
        assert dist['>8小时'] == 1

    def test_empty_distribution(self):
        """空列表分布"""
        dist = calculate_response_distribution([])
        assert all(v == 0 for v in dist.values())

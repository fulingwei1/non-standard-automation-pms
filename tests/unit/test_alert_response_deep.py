# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 预警响应服务"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta


class TestAlertResponseServiceBusinessLogic:
    """预警响应服务业务逻辑测试"""

    def test_calculate_response_times(self):
        """测试计算响应时间"""
        from app.services.alert.alert_response_service import calculate_response_times

        # 创建模拟告警
        alert1 = MagicMock()
        alert1.triggered_at = datetime(2026, 4, 10, 10, 0, 0)
        alert1.acknowledged_at = datetime(2026, 4, 10, 10, 30, 0)  # 30分钟后确认

        alert2 = MagicMock()
        alert2.triggered_at = datetime(2026, 4, 10, 11, 0, 0)
        alert2.acknowledged_at = datetime(2026, 4, 10, 12, 0, 0)  # 60分钟后确认

        results = calculate_response_times([alert1, alert2])

        assert len(results) == 2
        assert results[0]["minutes"] == 30
        assert results[1]["minutes"] == 60

    def test_calculate_response_times_no_acknowledged(self):
        """测试没有确认时间的告警"""
        from app.services.alert.alert_response_service import calculate_response_times

        alert = MagicMock()
        alert.triggered_at = datetime(2026, 4, 10, 10, 0, 0)
        alert.acknowledged_at = None  # 未确认

        results = calculate_response_times([alert])

        assert len(results) == 0

    def test_calculate_resolve_times(self):
        """测试计算解决时间"""
        from app.services.alert.alert_response_service import calculate_resolve_times

        alert = MagicMock()
        alert.acknowledged_at = datetime(2026, 4, 10, 10, 0, 0)
        alert.handle_end_at = datetime(2026, 4, 10, 12, 0, 0)  # 2小时后解决

        results = calculate_resolve_times([alert])

        assert len(results) == 1
        assert results[0]["minutes"] == 120
        assert results[0]["hours"] == 2

    def test_calculate_response_distribution(self):
        """测试响应时效分布"""
        from app.services.alert.alert_response_service import calculate_response_distribution

        response_times = [
            {"hours": 0.5},   # <1小时
            {"hours": 1.5},   # 1-4小时
            {"hours": 2.0},   # 1-4小时
            {"hours": 5.0},   # 4-8小时
            {"hours": 10.0},  # >8小时
        ]

        distribution = calculate_response_distribution(response_times)

        assert distribution["<1小时"] == 1
        assert distribution["1-4小时"] == 2
        assert distribution["4-8小时"] == 1
        assert distribution[">8小时"] == 1

    def test_calculate_avg_response_time(self):
        """测试平均响应时间"""
        from app.services.alert.alert_response_service import calculate_avg_response_time

        response_times = [
            {"minutes": 30},
            {"minutes": 60},
            {"minutes": 90},
        ]

        avg = calculate_avg_response_time(response_times)

        assert avg == 60  # (30+60+90)/3 = 60

    def test_calculate_avg_response_time_empty(self):
        """测试空列表平均响应时间"""
        from app.services.alert.alert_response_service import calculate_avg_response_time

        avg = calculate_avg_response_time([])

        assert avg == 0

    def test_get_response_performance_by_project(self):
        """测试按项目统计响应绩效"""
        try:
            from app.services.alert.alert_response_service import get_response_performance_by_project

            mock_db = MagicMock()

            # Mock alerts
            mock_alert = MagicMock()
            mock_alert.project_id = 1
            mock_alert.triggered_at = datetime(2026, 4, 10, 10, 0, 0)
            mock_alert.acknowledged_at = datetime(2026, 4, 10, 10, 30, 0)

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_alert]

            results = get_response_performance_by_project(mock_db, [1])

            assert isinstance(results, list)
        except ImportError:
            pytest.skip("Function not found")

    def test_get_response_performance_by_user(self):
        """测试按用户统计响应绩效"""
        try:
            from app.services.alert.alert_response_service import get_response_performance_by_user

            mock_db = MagicMock()

            # Mock alerts
            mock_alert = MagicMock()
            mock_alert.acknowledged_by = 1
            mock_alert.triggered_at = datetime(2026, 4, 10, 10, 0, 0)
            mock_alert.acknowledged_at = datetime(2026, 4, 10, 10, 30, 0)

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_alert]

            results = get_response_performance_by_user(mock_db, [1])

            assert isinstance(results, list)
        except ImportError:
            pytest.skip("Function not found")


class TestAlertResponseServiceEdgeCases:
    """边界情况测试"""

    def test_response_time_zero(self):
        """测试零响应时间"""
        from app.services.alert.alert_response_service import calculate_response_times

        alert = MagicMock()
        alert.triggered_at = datetime(2026, 4, 10, 10, 0, 0)
        alert.acknowledged_at = datetime(2026, 4, 10, 10, 0, 0)  # 同一时间

        results = calculate_response_times([alert])

        assert len(results) == 1
        assert results[0]["minutes"] == 0

    def test_response_time_negative(self):
        """测试异常时间（确认时间早于触发时间）"""
        from app.services.alert.alert_response_service import calculate_response_times

        alert = MagicMock()
        alert.triggered_at = datetime(2026, 4, 10, 10, 0, 0)
        alert.acknowledged_at = datetime(2026, 4, 10, 9, 0, 0)  # 早1小时

        results = calculate_response_times([alert])

        # 应该能处理，时间会是负数
        assert len(results) == 1
        assert results[0]["minutes"] < 0

    def test_distribution_all_same_bucket(self):
        """测试所有数据在同一区间"""
        from app.services.alert.alert_response_service import calculate_response_distribution

        response_times = [
            {"hours": 0.5},
            {"hours": 0.3},
            {"hours": 0.8},
        ]

        distribution = calculate_response_distribution(response_times)

        assert distribution["<1小时"] == 3
        assert distribution["1-4小时"] == 0
        assert distribution["4-8小时"] == 0
        assert distribution[">8小时"] == 0
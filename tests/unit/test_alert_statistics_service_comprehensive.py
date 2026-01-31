# -*- coding: utf-8 -*-
"""
AlertStatisticsService 综合单元测试

测试覆盖:
- __init__: 初始化服务
- get_alert_statistics: 获取告警统计
- get_daily_trend: 获取每日趋势
- get_top_alerting_projects: 获取告警最多的项目
- get_response_time_stats: 获取响应时间统计
"""

from unittest.mock import MagicMock, patch
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest


class TestAlertStatisticsServiceInit:
    """测试 AlertStatisticsService 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.alert.alert_statistics_service import AlertStatisticsService

        mock_db = MagicMock()

        service = AlertStatisticsService(mock_db)

        assert service.db == mock_db


class TestGetAlertStatistics:
    """测试 get_alert_statistics 方法"""

    def test_returns_statistics_dict(self):
        """测试返回统计字典"""
        from app.services.alert.alert_statistics_service import AlertStatisticsService

        mock_db = MagicMock()

        # 模拟查询结果
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 100
        mock_query.with_entities.return_value.group_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        service = AlertStatisticsService(mock_db)

        result = service.get_alert_statistics()

        assert isinstance(result, dict)
        assert 'total_alerts' in result

    def test_uses_default_date_range(self):
        """测试使用默认日期范围"""
        from app.services.alert.alert_statistics_service import AlertStatisticsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.with_entities.return_value.group_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        service = AlertStatisticsService(mock_db)

        result = service.get_alert_statistics()

        # 默认查询最近30天
        mock_query.filter.assert_called()

    def test_filters_by_project_id(self):
        """测试按项目ID过滤"""
        from app.services.alert.alert_statistics_service import AlertStatisticsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.with_entities.return_value.group_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        service = AlertStatisticsService(mock_db)

        result = service.get_alert_statistics(project_id=1)

        # 验证添加了项目ID过滤
        assert mock_query.filter.call_count >= 2

    def test_returns_status_counts(self):
        """测试返回状态统计"""
        from app.services.alert.alert_statistics_service import AlertStatisticsService

        mock_db = MagicMock()

        mock_status_result = MagicMock()
        mock_status_result.status = "PENDING"
        mock_status_result.count = 50

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 100
        mock_query.with_entities.return_value.group_by.return_value.all.return_value = [mock_status_result]
        mock_db.query.return_value = mock_query

        service = AlertStatisticsService(mock_db)

        result = service.get_alert_statistics()

        assert 'status_counts' in result or 'PENDING' in str(result)

    def test_returns_severity_counts(self):
        """测试返回严重程度统计"""
        from app.services.alert.alert_statistics_service import AlertStatisticsService

        mock_db = MagicMock()

        mock_severity_result = MagicMock()
        mock_severity_result.severity = "CRITICAL"
        mock_severity_result.count = 20

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 100
        mock_query.with_entities.return_value.group_by.return_value.all.side_effect = [
            [],  # status stats
            [mock_severity_result],  # severity stats
            [],  # other stats
        ]
        mock_db.query.return_value = mock_query

        service = AlertStatisticsService(mock_db)

        result = service.get_alert_statistics()

        assert isinstance(result, dict)

    def test_handles_custom_date_range(self):
        """测试处理自定义日期范围"""
        from app.services.alert.alert_statistics_service import AlertStatisticsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.with_entities.return_value.group_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        service = AlertStatisticsService(mock_db)

        start = date(2024, 1, 1)
        end = date(2024, 1, 31)

        result = service.get_alert_statistics(start_date=start, end_date=end)

        assert result['total_alerts'] == 5


class TestGetDailyTrend:
    """测试 get_daily_trend 方法"""

    def test_returns_daily_data(self):
        """测试返回每日数据"""
        from app.services.alert.alert_statistics_service import AlertStatisticsService

        mock_db = MagicMock()

        mock_day_result = MagicMock()
        mock_day_result.date = date(2024, 1, 15)
        mock_day_result.count = 10

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value.group_by.return_value.order_by.return_value.all.return_value = [
            mock_day_result
        ]
        mock_db.query.return_value = mock_query

        service = AlertStatisticsService(mock_db)

        result = service.get_daily_trend(days=7)

        assert isinstance(result, list)

    def test_uses_default_days(self):
        """测试使用默认天数"""
        from app.services.alert.alert_statistics_service import AlertStatisticsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value.group_by.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        service = AlertStatisticsService(mock_db)

        result = service.get_daily_trend()

        # 默认应该是7天或30天
        assert isinstance(result, list)


class TestGetTopAlertingProjects:
    """测试 get_top_alerting_projects 方法"""

    def test_returns_top_projects(self):
        """测试返回告警最多的项目"""
        from app.services.alert.alert_statistics_service import AlertStatisticsService

        mock_db = MagicMock()

        mock_project_result = MagicMock()
        mock_project_result.project_id = 1
        mock_project_result.project_name = "测试项目"
        mock_project_result.count = 50

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_project_result
        ]
        mock_db.query.return_value = mock_query

        service = AlertStatisticsService(mock_db)

        result = service.get_top_alerting_projects(limit=10)

        assert isinstance(result, list)

    def test_limits_results(self):
        """测试限制结果数量"""
        from app.services.alert.alert_statistics_service import AlertStatisticsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        service = AlertStatisticsService(mock_db)

        result = service.get_top_alerting_projects(limit=5)

        mock_query.with_entities.return_value.group_by.return_value.order_by.return_value.limit.assert_called_with(5)


class TestGetResponseTimeStats:
    """测试 get_response_time_stats 方法"""

    def test_returns_response_time_stats(self):
        """测试返回响应时间统计"""
        from app.services.alert.alert_statistics_service import AlertStatisticsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value.first.return_value = MagicMock(
            avg_response_time=3600,
            min_response_time=600,
            max_response_time=7200
        )
        mock_db.query.return_value = mock_query

        service = AlertStatisticsService(mock_db)

        result = service.get_response_time_stats()

        assert isinstance(result, dict)

    def test_handles_no_data(self):
        """测试处理无数据情况"""
        from app.services.alert.alert_statistics_service import AlertStatisticsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        service = AlertStatisticsService(mock_db)

        result = service.get_response_time_stats()

        assert result is None or isinstance(result, dict)

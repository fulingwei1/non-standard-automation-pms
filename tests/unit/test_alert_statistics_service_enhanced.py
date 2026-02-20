# -*- coding: utf-8 -*-
"""
AlertStatisticsService 增强测试 - 提升覆盖率到60%+
目标：补充统计计算、趋势分析、指标计算等核心功能测试
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime, timezone, timedelta

from app.services.alert.alert_statistics_service import AlertStatisticsService
from app.models.alert import AlertRecord, AlertRule


@pytest.fixture
def mock_db():
    """Mock 数据库会话"""
    return MagicMock()


@pytest.fixture
def service(mock_db):
    """创建服务实例"""
    return AlertStatisticsService(db=mock_db)


@pytest.fixture
def mock_alert():
    """创建 Mock 告警记录"""
    def _create_alert(**kwargs):
        alert = MagicMock(spec=AlertRecord)
        alert.id = kwargs.get('id', 1)
        alert.status = kwargs.get('status', 'pending')
        alert.severity = kwargs.get('severity', 'WARNING')
        alert.alert_level = kwargs.get('alert_level', kwargs.get('severity', 'WARNING'))
        alert.created_at = kwargs.get('created_at', datetime.now(timezone.utc))
        alert.acknowledged_at = kwargs.get('acknowledged_at')
        alert.resolved_at = kwargs.get('resolved_at')
        alert.project_id = kwargs.get('project_id', 1)
        
        # Mock rule
        if 'rule_type' in kwargs:
            rule = MagicMock()
            rule.rule_type = kwargs['rule_type']
            alert.rule = rule
        else:
            alert.rule = None
            
        return alert
    return _create_alert


class TestAlertStatisticsServiceInit:
    """测试服务初始化"""

    def test_init_with_db(self, mock_db):
        """测试正常初始化"""
        service = AlertStatisticsService(db=mock_db)
        assert service.db is mock_db


class TestGetAlertStatistics:
    """测试获取告警统计信息"""

    def test_get_alert_statistics_default_date_range(self, service, mock_db):
        """测试默认日期范围"""
        # Setup
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.first.return_value = None
        
        # Execute
        result = service.get_alert_statistics()
        
        # Assert
        assert result["total_alerts"] == 0
        assert "period" in result
        assert "status_distribution" in result
        assert "severity_distribution" in result

    def test_get_alert_statistics_with_custom_date_range(self, service, mock_db):
        """测试自定义日期范围"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.join.return_value = mock_query
        
        # Mock status stats
        status_stat = MagicMock()
        status_stat.status = "pending"
        status_stat.count = 5
        mock_query.all.return_value = [status_stat]
        mock_query.first.return_value = None
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        result = service.get_alert_statistics(
            start_date=start_date,
            end_date=end_date
        )
        
        assert result["total_alerts"] == 10
        assert result["period"]["start_date"] == "2024-01-01"
        assert result["period"]["end_date"] == "2024-01-31"

    def test_get_alert_statistics_with_project_filter(self, service, mock_db):
        """测试项目筛选"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.first.return_value = None
        
        result = service.get_alert_statistics(project_id=10)
        
        assert result["total_alerts"] == 5
        # 验证 project_id 过滤被调用
        assert any("project_id" in str(call) for call in mock_query.filter.call_args_list)

    def test_get_alert_statistics_status_distribution(self, service, mock_db):
        """测试状态分布统计"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 15
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.join.return_value = mock_query
        
        # Mock status stats
        status_stats = [
            MagicMock(status="pending", count=5),
            MagicMock(status="acknowledged", count=3),
            MagicMock(status="resolved", count=7),
        ]
        
        def mock_all_side_effect():
            # 第一次调用返回 status_stats，后续返回空列表
            if mock_query.all.call_count == 1:
                return status_stats
            return []
        
        mock_query.all.side_effect = mock_all_side_effect
        mock_query.first.return_value = None
        
        result = service.get_alert_statistics()
        
        assert result["status_distribution"]["pending"] == 5
        assert result["status_distribution"]["acknowledged"] == 3
        assert result["status_distribution"]["resolved"] == 7

    def test_get_alert_statistics_response_metrics(self, service, mock_db):
        """测试响应时间指标"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.all.return_value = []
        
        # Mock response time stats
        response_stat = MagicMock()
        response_stat.avg_response_seconds = 3600  # 1小时
        response_stat.min_response_seconds = 1800  # 30分钟
        response_stat.max_response_seconds = 7200  # 2小时
        
        mock_query.first.return_value = response_stat
        
        result = service.get_alert_statistics()
        
        assert "response_metrics" in result
        assert "1小时" in result["response_metrics"]["average_response_time"]


class TestGetAlertTrends:
    """测试获取告警趋势数据"""

    def test_get_alert_trends_daily(self, service, mock_db):
        """测试每日趋势"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        
        # Mock trend data
        trend_item = MagicMock()
        trend_item.period = date(2024, 1, 1)
        trend_item.status = "pending"
        trend_item.count = 5
        mock_query.all.return_value = [trend_item]
        
        result = service.get_alert_trends(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            period="daily"
        )
        
        assert result["period"]["granularity"] == "daily"
        assert "2024-01-01" in result["trend_data"]

    def test_get_alert_trends_weekly(self, service, mock_db):
        """测试每周趋势"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        result = service.get_alert_trends(period="weekly")
        
        assert result["period"]["granularity"] == "weekly"

    def test_get_alert_trends_monthly(self, service, mock_db):
        """测试每月趋势"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        result = service.get_alert_trends(period="monthly")
        
        assert result["period"]["granularity"] == "monthly"


class TestGetAlertDashboardData:
    """测试获取告警仪表板数据"""

    @patch('app.services.alert.alert_statistics_service.AlertStatisticsService._get_week_trend')
    @patch('app.services.alert.alert_statistics_service.AlertStatisticsService._calculate_efficiency_metrics')
    @patch('app.services.alert.alert_statistics_service.joinedload')
    def test_get_alert_dashboard_data_basic(self, mock_joinedload, mock_calc_efficiency,
                                           mock_get_week_trend, service, mock_db):
        """测试基础仪表板数据"""
        # Setup today stats query
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_get_week_trend.return_value = []
        mock_calc_efficiency.return_value = {
            "resolution_rate": 75.0,
            "average_response_time": "1小时30分钟",
            "average_resolution_time": "3小时",
            "total_processed": 100
        }
        
        result = service.get_alert_dashboard_data()
        
        assert "today_summary" in result
        assert "week_trend" in result
        assert "critical_alerts" in result
        assert "efficiency_metrics" in result

    @patch('app.services.alert.alert_statistics_service.AlertStatisticsService._get_week_trend')
    @patch('app.services.alert.alert_statistics_service.AlertStatisticsService._calculate_efficiency_metrics')
    @patch('app.services.alert.alert_statistics_service.joinedload')
    def test_get_alert_dashboard_data_with_project_filter(self, mock_joinedload, mock_calc_efficiency,
                                                          mock_get_week_trend, service, mock_db):
        """测试带项目筛选的仪表板数据"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_get_week_trend.return_value = []
        mock_calc_efficiency.return_value = {}
        
        result = service.get_alert_dashboard_data(project_id=10)
        
        assert result is not None


class TestGetResponseMetrics:
    """测试获取响应时间指标"""

    def test_get_response_metrics_empty_data(self, service, mock_db):
        """测试空数据"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        result = service.get_response_metrics()
        
        assert result["total_responded"] == 0
        assert result["response_time_distribution"] == {}

    def test_get_response_metrics_with_data(self, service, mock_db):
        """测试有数据的响应指标"""
        # Create mock alerts with response times
        mock_alerts = []
        base_time = datetime(2024, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
        
        for i in range(5):
            alert = MagicMock()
            alert.created_at = base_time
            alert.acknowledged_at = base_time + timedelta(minutes=30 * (i + 1))
            mock_alerts.append(alert)
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_alerts
        
        result = service.get_response_metrics(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        assert result["total_responded"] == 5
        assert "response_time_distribution" in result
        assert "percentile_metrics" in result

    def test_get_response_metrics_distribution(self, service, mock_db):
        """测试响应时间分布"""
        mock_alerts = []
        base_time = datetime(2024, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
        
        # 创建不同时间范围的告警
        # <5分钟
        alert1 = MagicMock()
        alert1.created_at = base_time
        alert1.acknowledged_at = base_time + timedelta(minutes=3)
        mock_alerts.append(alert1)
        
        # <30分钟
        alert2 = MagicMock()
        alert2.created_at = base_time
        alert2.acknowledged_at = base_time + timedelta(minutes=15)
        mock_alerts.append(alert2)
        
        # <1小时
        alert3 = MagicMock()
        alert3.created_at = base_time
        alert3.acknowledged_at = base_time + timedelta(minutes=45)
        mock_alerts.append(alert3)
        
        # >24小时
        alert4 = MagicMock()
        alert4.created_at = base_time
        alert4.acknowledged_at = base_time + timedelta(hours=30)
        mock_alerts.append(alert4)
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_alerts
        
        result = service.get_response_metrics()
        
        distribution = result["response_time_distribution"]
        assert distribution["within_5min"] >= 1
        assert distribution["within_30min"] >= 1
        assert distribution["over_24hours"] >= 1


class TestGetEfficiencyMetrics:
    """测试获取效率指标"""

    @patch('app.services.alert.alert_statistics_service.AlertStatisticsService._calculate_efficiency_metrics')
    def test_get_efficiency_metrics(self, mock_calc, service, mock_db):
        """测试获取效率指标"""
        mock_calc.return_value = {
            "resolution_rate": 80.0,
            "average_response_time": "2小时",
            "average_resolution_time": "5小时",
            "total_processed": 50
        }
        
        result = service.get_efficiency_metrics()
        
        assert result["resolution_rate"] == 80.0
        assert "average_response_time" in result


class TestCalculateEfficiencyMetrics:
    """测试效率指标计算"""

    def test_calculate_efficiency_metrics_basic(self, service, mock_db):
        """测试基础效率指标计算"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 100
        mock_query.with_entities.return_value = mock_query
        mock_query.scalar.return_value = 3600  # 1小时
        
        result = service._calculate_efficiency_metrics()
        
        assert "resolution_rate" in result
        assert "average_response_time" in result
        assert "total_processed" in result

    def test_calculate_efficiency_metrics_zero_alerts(self, service, mock_db):
        """测试无告警时的效率指标"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.with_entities.return_value = mock_query
        mock_query.scalar.return_value = None
        
        result = service._calculate_efficiency_metrics()
        
        assert result["resolution_rate"] == 0
        assert result["total_processed"] == 0


class TestGetWeekTrend:
    """测试获取周趋势数据"""

    def test_get_week_trend_basic(self, service, mock_db):
        """测试基础周趋势"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        week_start = date(2024, 1, 1)
        result = service._get_week_trend(week_start)
        
        assert len(result) == 7
        assert all("date" in item for item in result)
        assert all("total" in item for item in result)

    def test_get_week_trend_with_project(self, service, mock_db):
        """测试带项目筛选的周趋势"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        week_start = date(2024, 1, 1)
        result = service._get_week_trend(week_start, project_id=10)
        
        assert len(result) == 7


class TestFormatSeconds:
    """测试时间格式化"""

    def test_format_seconds_none(self, service):
        """测试 None 值"""
        assert service._format_seconds(None) is None

    def test_format_seconds_zero(self, service):
        """测试 0 秒"""
        result = service._format_seconds(0)
        assert result is None

    def test_format_seconds_only_minutes(self, service):
        """测试仅分钟"""
        result = service._format_seconds(300)  # 5分钟
        assert "5分钟" in result

    def test_format_seconds_hours_and_minutes(self, service):
        """测试小时和分钟"""
        result = service._format_seconds(3660)  # 1小时1分钟
        assert "小时" in result
        assert "分钟" in result

    def test_format_seconds_large_value(self, service):
        """测试大时间值"""
        result = service._format_seconds(36000)  # 10小时
        assert "10小时" in result


class TestGetPercentile:
    """测试百分位数计算"""

    def test_get_percentile_empty_list(self, service):
        """测试空列表"""
        assert service._get_percentile([], 50) == 0

    def test_get_percentile_single_value(self, service):
        """测试单个值"""
        result = service._get_percentile([5.0], 50)
        assert result == 5.0

    def test_get_percentile_median(self, service):
        """测试中位数"""
        result = service._get_percentile([1.0, 2.0, 3.0, 4.0, 5.0], 50)
        assert result in [2.0, 3.0]  # 中间值

    def test_get_percentile_90th(self, service):
        """测试90%分位数"""
        data = list(range(1, 101))  # 1-100
        result = service._get_percentile(data, 90)
        assert result >= 85

    def test_get_percentile_99th(self, service):
        """测试99%分位数"""
        data = list(range(1, 101))
        result = service._get_percentile(data, 99)
        assert result >= 95

    def test_get_percentile_100th(self, service):
        """测试100%分位数（最大值）"""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = service._get_percentile(data, 100)
        assert result == 5.0

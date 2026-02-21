# -*- coding: utf-8 -*-
"""
告警统计服务单元测试

参考 test_condition_parser_rewrite.py 的策略：
- 只mock外部依赖（db.query, db.add, db.commit等）
- 让业务逻辑真正执行
- 覆盖主要方法和边界情况
- 目标覆盖率：70%+
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from datetime import date, datetime, timedelta, timezone

from app.services.alert.alert_statistics_service import AlertStatisticsService
from app.models.alert import AlertRecord, AlertRule


class TestAlertStatisticsService(unittest.TestCase):
    """测试告警统计服务主要功能"""

    def setUp(self):
        """初始化测试环境"""
        self.db = MagicMock()
        self.service = AlertStatisticsService(self.db)

    # ========== get_alert_statistics() 测试 ==========

    def test_get_alert_statistics_with_defaults(self):
        """测试使用默认参数获取统计"""
        # Mock query chain
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        
        # Mock filter返回
        mock_query.filter.return_value = mock_query
        
        # Mock count
        mock_query.count.return_value = 100
        
        # Mock status stats
        status_result = [
            Mock(status="PENDING", count=30),
            Mock(status="ACKNOWLEDGED", count=40),
            Mock(status="RESOLVED", count=30),
        ]
        
        # Mock severity stats
        severity_result = [
            Mock(severity="low", count=50),
            Mock(severity="medium", count=30),
            Mock(severity="high", count=15),
            Mock(severity="critical", count=5),
        ]
        
        # Mock rule type stats
        rule_type_result = [
            Mock(rule_type="threshold", count=60),
            Mock(rule_type="anomaly", count=40),
        ]
        
        # Mock response time stats
        response_stats = Mock(
            avg_response_seconds=1800.0,  # 30分钟
            min_response_seconds=300.0,   # 5分钟
            max_response_seconds=7200.0   # 2小时
        )
        
        # Mock resolution time stats
        resolution_stats = Mock(
            avg_resolution_seconds=14400.0,  # 4小时
            min_resolution_seconds=3600.0,   # 1小时
            max_resolution_seconds=86400.0   # 24小时
        )
        
        # 配置不同的mock行为
        def mock_with_entities_func(*args):
            nonlocal entity_call_count
            entity_call_count += 1
            result_mock = MagicMock()
            result_mock.group_by.return_value = result_mock
            
            if entity_call_count == 1:  # status stats
                result_mock.all.return_value = status_result
            elif entity_call_count == 2:  # severity stats
                result_mock.all.return_value = severity_result
            elif entity_call_count == 3:  # response time stats
                result_mock.first.return_value = response_stats
            elif entity_call_count == 4:  # resolution time stats
                result_mock.first.return_value = resolution_stats
            else:
                result_mock.all.return_value = []
                result_mock.first.return_value = None
            
            return result_mock
        
        entity_call_count = 0
        
        # Mock join for rule type stats
        mock_join = MagicMock()
        mock_query.join.return_value = mock_join
        mock_join.with_entities.return_value = mock_join
        mock_join.group_by.return_value = mock_join
        mock_join.all.return_value = rule_type_result
        
        mock_query.with_entities.side_effect = mock_with_entities_func
        
        # 执行测试
        result = self.service.get_alert_statistics()
        
        # 验证结果
        self.assertEqual(result["total_alerts"], 100)
        self.assertEqual(result["status_distribution"]["PENDING"], 30)
        self.assertEqual(result["status_distribution"]["RESOLVED"], 30)
        self.assertEqual(result["severity_distribution"]["critical"], 5)
        self.assertEqual(result["rule_type_distribution"]["threshold"], 60)
        
        # 验证时间格式化
        self.assertIn("response_metrics", result)
        self.assertIn("resolution_metrics", result)

    def test_get_alert_statistics_with_project_filter(self):
        """测试带项目过滤的统计"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 50
        
        # Mock empty results
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_join = MagicMock()
        mock_query.join.return_value = mock_join
        mock_join.with_entities.return_value = mock_join
        mock_join.group_by.return_value = mock_join
        mock_join.all.return_value = []
        
        mock_query.first.return_value = None
        
        result = self.service.get_alert_statistics(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            project_id=123
        )
        
        self.assertEqual(result["total_alerts"], 50)
        self.assertIn("period", result)
        self.assertEqual(result["period"]["start_date"], "2026-01-01")

    def test_get_alert_statistics_no_data(self):
        """测试无数据情况"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        
        # Mock empty results
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_join = MagicMock()
        mock_query.join.return_value = mock_join
        mock_join.with_entities.return_value = mock_join
        mock_join.group_by.return_value = mock_join
        mock_join.all.return_value = []
        
        mock_query.first.return_value = None
        
        result = self.service.get_alert_statistics()
        
        self.assertEqual(result["total_alerts"], 0)
        self.assertEqual(result["status_distribution"], {})
        self.assertIsNone(result["response_metrics"]["average_response_time"])

    # ========== get_alert_trends() 测试 ==========

    def test_get_alert_trends_daily(self):
        """测试每日趋势"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        
        trend_data = [
            Mock(period=date(2026, 1, 1), status="PENDING", count=10),
            Mock(period=date(2026, 1, 1), status="RESOLVED", count=5),
            Mock(period=date(2026, 1, 2), status="PENDING", count=8),
        ]
        mock_query.all.return_value = trend_data
        
        result = self.service.get_alert_trends(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            period="daily"
        )
        
        self.assertIn("period", result)
        self.assertEqual(result["period"]["granularity"], "daily")
        self.assertIn("trend_data", result)
        self.assertIn("2026-01-01", result["trend_data"])
        self.assertEqual(result["trend_data"]["2026-01-01"]["PENDING"], 10)

    def test_get_alert_trends_weekly(self):
        """测试每周趋势"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.service.get_alert_trends(period="weekly")
        
        self.assertEqual(result["period"]["granularity"], "weekly")

    def test_get_alert_trends_monthly(self):
        """测试每月趋势"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.service.get_alert_trends(period="monthly", project_id=456)
        
        self.assertEqual(result["period"]["granularity"], "monthly")

    # ========== get_alert_dashboard_data() 测试 ==========

    def test_get_alert_dashboard_data(self):
        """测试仪表板数据"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Mock today stats
        today_stats = [
            Mock(status="PENDING", count=5),
            Mock(status="ACKNOWLEDGED", count=3),
            Mock(status="RESOLVED", count=10),
        ]
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = today_stats
        
        # Mock critical alerts
        mock_alert1 = Mock(
            id=1,
            alert_title="Critical Alert 1",
            severity="critical",
            status="PENDING",
            handler_id=1,
            created_at=datetime.now(timezone.utc)
        )
        mock_alert1.project = Mock(name="Project A")
        
        mock_options = MagicMock()
        mock_query.options.return_value = mock_options
        mock_options.filter.return_value = mock_options
        mock_options.order_by.return_value = mock_options
        mock_options.limit.return_value = mock_options
        mock_options.all.return_value = [mock_alert1]
        
        # Mock efficiency metrics
        mock_query.count.return_value = 100
        mock_query.scalar.return_value = 1800.0
        
        result = self.service.get_alert_dashboard_data()
        
        self.assertIn("today_summary", result)
        self.assertEqual(result["today_summary"]["total"], 8)  # pending + acknowledged
        self.assertEqual(result["today_summary"]["pending"], 5)
        self.assertIn("week_trend", result)
        self.assertIn("critical_alerts", result)
        self.assertIn("efficiency_metrics", result)

    def test_get_alert_dashboard_data_with_project(self):
        """测试带项目过滤的仪表板"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_options = MagicMock()
        mock_query.options.return_value = mock_options
        mock_options.filter.return_value = mock_options
        mock_options.order_by.return_value = mock_options
        mock_options.limit.return_value = mock_options
        mock_options.all.return_value = []
        
        mock_query.count.return_value = 0
        mock_query.scalar.return_value = None
        
        result = self.service.get_alert_dashboard_data(project_id=789)
        
        self.assertEqual(result["today_summary"]["total"], 0)
        self.assertEqual(len(result["critical_alerts"]), 0)

    # ========== get_response_metrics() 测试 ==========

    def test_get_response_metrics_with_data(self):
        """测试响应时间指标（有数据）"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Mock alerts with response times
        alert1 = Mock()
        alert1.created_at = datetime(2026, 1, 1, 10, 0, 0)
        alert1.acknowledged_at = datetime(2026, 1, 1, 10, 3, 0)  # 3分钟
        
        alert2 = Mock()
        alert2.created_at = datetime(2026, 1, 1, 11, 0, 0)
        alert2.acknowledged_at = datetime(2026, 1, 1, 11, 20, 0)  # 20分钟
        
        alert3 = Mock()
        alert3.created_at = datetime(2026, 1, 1, 12, 0, 0)
        alert3.acknowledged_at = datetime(2026, 1, 1, 13, 30, 0)  # 1.5小时
        
        mock_query.all.return_value = [alert1, alert2, alert3]
        
        result = self.service.get_response_metrics()
        
        self.assertEqual(result["total_responded"], 3)
        self.assertIn("response_time_distribution", result)
        self.assertIn("percentile_metrics", result)
        
        # 验证时间分布
        dist = result["response_time_distribution"]
        self.assertEqual(dist["within_5min"], 1)  # alert1
        self.assertEqual(dist["within_30min"], 1)  # alert2
        self.assertEqual(dist["within_4hours"], 1)  # alert3

    def test_get_response_metrics_no_data(self):
        """测试响应时间指标（无数据）"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.service.get_response_metrics()
        
        self.assertEqual(result["total_responded"], 0)
        self.assertEqual(result["response_time_distribution"], {})
        self.assertEqual(result["percentile_metrics"], {})

    def test_get_response_metrics_with_project_filter(self):
        """测试带项目过滤的响应指标"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        alert1 = Mock()
        alert1.created_at = datetime(2026, 1, 1, 10, 0, 0)
        alert1.acknowledged_at = datetime(2026, 1, 1, 10, 10, 0)  # 10分钟
        
        mock_query.all.return_value = [alert1]
        
        result = self.service.get_response_metrics(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            project_id=123
        )
        
        self.assertEqual(result["total_responded"], 1)

    # ========== get_efficiency_metrics() 测试 ==========

    def test_get_efficiency_metrics(self):
        """测试效率指标"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 100
        
        # Mock with_entities for different queries
        def mock_with_entities_side_effect(*args):
            mock_result = MagicMock()
            mock_result.scalar.return_value = 1800.0  # 30分钟
            return mock_result
        
        mock_query.with_entities.side_effect = mock_with_entities_side_effect
        
        result = self.service.get_efficiency_metrics()
        
        self.assertIn("resolution_rate", result)
        self.assertIn("average_response_time", result)
        self.assertIn("average_resolution_time", result)
        self.assertEqual(result["total_processed"], 100)

    def test_get_efficiency_metrics_with_date_range(self):
        """测试指定日期范围的效率指标"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 50
        mock_query.with_entities.return_value = mock_query
        mock_query.scalar.return_value = None
        
        result = self.service.get_efficiency_metrics(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            project_id=999
        )
        
        self.assertEqual(result["total_processed"], 50)

    # ========== 辅助方法测试 ==========

    def test_format_seconds_hours_and_minutes(self):
        """测试秒数格式化（小时+分钟）"""
        result = self.service._format_seconds(7260)  # 2小时1分钟
        self.assertEqual(result, "2小时1分钟")

    def test_format_seconds_only_minutes(self):
        """测试秒数格式化（仅分钟）"""
        result = self.service._format_seconds(1800)  # 30分钟
        self.assertEqual(result, "30分钟")

    def test_format_seconds_zero_minutes(self):
        """测试秒数格式化（0分钟）"""
        result = self.service._format_seconds(30)  # 30秒
        self.assertEqual(result, "0分钟")

    def test_format_seconds_none(self):
        """测试None值格式化"""
        result = self.service._format_seconds(None)
        self.assertIsNone(result)

    def test_get_percentile_normal(self):
        """测试百分位数计算（正常情况）"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        # 百分位数计算：index = int(len * percentile / 100)
        # 50% -> index = int(10 * 50 / 100) = 5 -> data[5] = 6
        result_50 = self.service._get_percentile(data, 50)
        self.assertEqual(result_50, 6)
        
        # 90% -> index = int(10 * 90 / 100) = 9 -> data[9] = 10
        result_90 = self.service._get_percentile(data, 90)
        self.assertEqual(result_90, 10)

    def test_get_percentile_empty_list(self):
        """测试空列表的百分位数"""
        result = self.service._get_percentile([], 50)
        self.assertEqual(result, 0)

    def test_get_percentile_single_value(self):
        """测试单值列表"""
        result = self.service._get_percentile([100], 99)
        self.assertEqual(result, 100)

    def test_get_week_trend(self):
        """测试周趋势数据"""
        week_start = date(2026, 1, 5)  # 假设是周一
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        
        # Mock每天的统计
        mock_query.all.side_effect = [
            [Mock(status="PENDING", count=5), Mock(status="RESOLVED", count=3)],  # Day 1
            [Mock(status="PENDING", count=7)],  # Day 2
            [],  # Day 3
            [Mock(status="RESOLVED", count=10)],  # Day 4
            [Mock(status="PENDING", count=2), Mock(status="RESOLVED", count=4)],  # Day 5
            [],  # Day 6
            [Mock(status="PENDING", count=1)],  # Day 7
        ]
        
        result = self.service._get_week_trend(week_start, project_id=None)
        
        self.assertEqual(len(result), 7)
        self.assertEqual(result[0]["date"], "2026-01-05")
        self.assertEqual(result[0]["total"], 8)
        self.assertEqual(result[0]["pending"], 5)
        self.assertEqual(result[0]["resolved"], 3)

    def test_calculate_efficiency_metrics_with_data(self):
        """测试计算效率指标（有数据）"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Total alerts
        mock_query.count.return_value = 100
        
        # Mock with_entities for avg times
        mock_entity_query = MagicMock()
        mock_query.with_entities.return_value = mock_entity_query
        mock_entity_query.scalar.return_value = 3600.0  # 1小时
        
        result = self.service._calculate_efficiency_metrics(
            project_id=123,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31)
        )
        
        self.assertIn("resolution_rate", result)
        self.assertIn("average_response_time", result)
        self.assertEqual(result["total_processed"], 100)

    def test_calculate_efficiency_metrics_zero_alerts(self):
        """测试计算效率指标（零告警）"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        
        mock_query.with_entities.return_value = mock_query
        mock_query.scalar.return_value = None
        
        result = self.service._calculate_efficiency_metrics()
        
        self.assertEqual(result["resolution_rate"], 0)
        self.assertEqual(result["total_processed"], 0)

    # ========== 边界情况测试 ==========

    def test_response_metrics_time_distribution_boundaries(self):
        """测试响应时间分布边界值"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # 边界值测试：正好5分钟、30分钟、1小时等
        alert_5min = Mock()
        alert_5min.created_at = datetime(2026, 1, 1, 10, 0, 0)
        alert_5min.acknowledged_at = datetime(2026, 1, 1, 10, 5, 0)  # 正好5分钟
        
        alert_30min = Mock()
        alert_30min.created_at = datetime(2026, 1, 1, 11, 0, 0)
        alert_30min.acknowledged_at = datetime(2026, 1, 1, 11, 30, 0)  # 正好30分钟
        
        alert_1hour = Mock()
        alert_1hour.created_at = datetime(2026, 1, 1, 12, 0, 0)
        alert_1hour.acknowledged_at = datetime(2026, 1, 1, 13, 0, 0)  # 正好1小时
        
        alert_24hours = Mock()
        alert_24hours.created_at = datetime(2026, 1, 1, 0, 0, 0)
        alert_24hours.acknowledged_at = datetime(2026, 1, 2, 0, 0, 0)  # 正好24小时
        
        alert_over_24 = Mock()
        alert_over_24.created_at = datetime(2026, 1, 1, 0, 0, 0)
        alert_over_24.acknowledged_at = datetime(2026, 1, 3, 0, 0, 0)  # 超过24小时
        
        mock_query.all.return_value = [alert_5min, alert_30min, alert_1hour, alert_24hours, alert_over_24]
        
        result = self.service.get_response_metrics()
        
        dist = result["response_time_distribution"]
        self.assertEqual(dist["within_5min"], 1)
        self.assertEqual(dist["within_30min"], 1)
        self.assertEqual(dist["within_1hour"], 1)
        self.assertEqual(dist["within_24hours"], 1)
        self.assertEqual(dist["over_24hours"], 1)

    def test_percentile_calculation_edge_cases(self):
        """测试百分位数计算边界情况"""
        # 测试100%百分位
        data = [1, 2, 3, 4, 5]
        result = self.service._get_percentile(data, 100)
        self.assertEqual(result, 5)
        
        # 测试0%百分位
        result = self.service._get_percentile(data, 0)
        self.assertEqual(result, 1)

    def test_get_alert_statistics_resolution_rate_100_percent(self):
        """测试100%解决率情况"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # 总数100，全部resolved
        call_counter = {"count": 0}
        
        def mock_count_side_effect():
            call_counter["count"] += 1
            if call_counter["count"] == 1:
                return 100  # total
            elif call_counter["count"] == 2:
                return 100  # resolved
            return 0
        
        mock_query.count.side_effect = mock_count_side_effect
        
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [Mock(status="RESOLVED", count=100)]
        
        mock_join = MagicMock()
        mock_query.join.return_value = mock_join
        mock_join.with_entities.return_value = mock_join
        mock_join.group_by.return_value = mock_join
        mock_join.all.return_value = []
        
        mock_query.first.return_value = None
        mock_query.scalar.return_value = None
        
        result = self.service.get_alert_statistics()
        self.assertEqual(result["total_alerts"], 100)


class TestAlertStatisticsServiceIntegration(unittest.TestCase):
    """集成测试：测试多个方法协作"""

    def setUp(self):
        self.db = MagicMock()
        self.service = AlertStatisticsService(self.db)

    def test_dashboard_integrates_multiple_metrics(self):
        """测试仪表板整合多个指标"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Mock today stats
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [
            Mock(status="PENDING", count=10),
            Mock(status="RESOLVED", count=20)
        ]
        
        # Mock critical alerts
        mock_options = MagicMock()
        mock_query.options.return_value = mock_options
        mock_options.filter.return_value = mock_options
        mock_options.order_by.return_value = mock_options
        mock_options.limit.return_value = mock_options
        mock_options.all.return_value = []
        
        # Mock efficiency
        mock_query.count.return_value = 100
        mock_query.scalar.return_value = 1800.0
        
        result = self.service.get_alert_dashboard_data(project_id=123)
        
        # 验证各个部分都存在
        self.assertIn("today_summary", result)
        self.assertIn("week_trend", result)
        self.assertIn("critical_alerts", result)
        self.assertIn("efficiency_metrics", result)
        
        # 验证今日汇总
        self.assertEqual(result["today_summary"]["total"], 10)
        self.assertEqual(result["today_summary"]["resolved"], 20)


if __name__ == "__main__":
    unittest.main()

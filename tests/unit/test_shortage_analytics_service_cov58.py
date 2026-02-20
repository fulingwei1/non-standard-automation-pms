# -*- coding: utf-8 -*-
"""
ShortageAnalyticsService 单元测试
覆盖目标: 58%+ (至少8个测试用例)
"""
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.shortage_analytics import ShortageAnalyticsService


class TestShortageAnalyticsService(unittest.TestCase):
    """ShortageAnalyticsService 测试套件"""

    def setUp(self):
        """每个测试前的准备工作"""
        self.mock_db = MagicMock()
        self.service = ShortageAnalyticsService(self.mock_db)

    def test_init(self):
        """测试服务初始化"""
        self.assertIsNotNone(self.service)
        self.assertEqual(self.service.db, self.mock_db)

    def test_get_dashboard_data_without_project_filter(self):
        """测试获取看板数据（无项目筛选）"""
        # Mock 查询结果
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = self.service.get_dashboard_data()

        # 验证返回结构
        self.assertIn("reports", result)
        self.assertIn("alerts", result)
        self.assertIn("arrivals", result)
        self.assertIn("substitutions", result)
        self.assertIn("transfers", result)
        self.assertIn("recent_reports", result)

    def test_get_dashboard_data_with_project_filter(self):
        """测试获取看板数据（带项目筛选）"""
        project_id = 1
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = self.service.get_dashboard_data(project_id)

        # 验证 filter 被调用
        self.assertTrue(mock_query.filter.called)
        self.assertIsInstance(result, dict)

    def test_get_recent_reports(self):
        """测试获取最近上报列表"""
        # Mock ShortageReport 数据
        mock_report = MagicMock()
        mock_report.id = 1
        mock_report.report_no = "SR-001"
        mock_report.project_id = 1
        mock_report.material_name = "测试物料"
        mock_report.shortage_qty = Decimal("10.5")
        mock_report.urgent_level = "URGENT"
        mock_report.status = "REPORTED"
        mock_report.report_time = datetime(2026, 2, 20, 10, 0, 0)

        # Mock Project 数据
        mock_project = MagicMock()
        mock_project.project_name = "测试项目"

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_report]
        mock_query.first.return_value = mock_project

        result = self.service._get_recent_reports()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[0]["material_name"], "测试物料")
        self.assertEqual(result[0]["project_name"], "测试项目")

    def test_get_daily_report_default_date(self):
        """测试获取日报（默认今天）"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = self.service.get_daily_report()

        # 验证默认使用今天日期
        self.assertEqual(result["report_date"], str(date.today()))
        self.assertEqual(result["total_reports"], 0)

    def test_get_daily_report_with_data(self):
        """测试获取日报（有数据）"""
        report_date = date(2026, 2, 20)

        # Mock ShortageReport
        mock_report1 = MagicMock()
        mock_report1.material_id = 1
        mock_report1.material_name = "物料A"
        mock_report1.urgent_level = "URGENT"
        mock_report1.status = "REPORTED"
        mock_report1.shortage_qty = Decimal("15.0")
        mock_report1.project_id = 1

        mock_report2 = MagicMock()
        mock_report2.material_id = 2
        mock_report2.material_name = "物料B"
        mock_report2.urgent_level = "NORMAL"
        mock_report2.status = "CONFIRMED"
        mock_report2.shortage_qty = Decimal("20.0")
        mock_report2.project_id = 1

        # Mock Project
        mock_project = MagicMock()
        mock_project.project_name = "项目A"

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_report1, mock_report2]
        mock_query.first.return_value = mock_project

        result = self.service.get_daily_report(report_date)

        self.assertEqual(result["total_reports"], 2)
        self.assertEqual(result["by_urgent"]["URGENT"], 1)
        self.assertEqual(result["by_urgent"]["NORMAL"], 1)
        self.assertEqual(result["by_status"]["REPORTED"], 1)
        self.assertEqual(result["by_status"]["CONFIRMED"], 1)

    def test_get_latest_daily_report_no_data(self):
        """测试获取最新日报（无数据）"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.scalar.return_value = None

        result = self.service.get_latest_daily_report()

        self.assertIsNone(result)

    def test_get_latest_daily_report_with_data(self):
        """测试获取最新日报（有数据）"""
        latest_date = date(2026, 2, 20)

        # Mock ShortageDailyReport
        mock_report = MagicMock()
        mock_report.report_date = latest_date
        mock_report.new_alerts = 5
        mock_report.resolved_alerts = 3
        mock_report.pending_alerts = 2
        mock_report.overdue_alerts = 1
        mock_report.level1_count = 1
        mock_report.level2_count = 2
        mock_report.level3_count = 3
        mock_report.level4_count = 4
        mock_report.new_reports = 10
        mock_report.resolved_reports = 5
        mock_report.total_work_orders = 100
        mock_report.kit_complete_count = 80
        mock_report.kit_rate = Decimal("0.8")
        mock_report.expected_arrivals = 20
        mock_report.actual_arrivals = 18
        mock_report.delayed_arrivals = 2
        mock_report.on_time_rate = Decimal("0.9")
        mock_report.avg_response_minutes = 30
        mock_report.avg_resolve_hours = Decimal("2.5")
        mock_report.stoppage_count = 3
        mock_report.stoppage_hours = Decimal("5.5")

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.scalar.return_value = latest_date
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_report

        result = self.service.get_latest_daily_report()

        self.assertIsNotNone(result)
        self.assertEqual(result["date"], latest_date.isoformat())
        self.assertEqual(result["alerts"]["new"], 5)
        self.assertEqual(result["reports"]["new"], 10)

    def test_get_daily_report_by_date_not_found(self):
        """测试按日期获取日报（未找到）"""
        report_date = date(2026, 2, 20)

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = self.service.get_daily_report_by_date(report_date)

        self.assertIsNone(result)

    def test_get_shortage_trends(self):
        """测试趋势分析"""
        days = 7

        # Mock ShortageReport 查询
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2  # 每天2条新增和2条解决

        result = self.service.get_shortage_trends(days)

        self.assertIn("period", result)
        self.assertIn("summary", result)
        self.assertIn("daily", result)
        self.assertEqual(result["period"]["days"], days)
        self.assertEqual(len(result["daily"]), days + 1)  # 包含开始和结束日期

    def test_get_shortage_trends_with_project_filter(self):
        """测试趋势分析（带项目筛选）"""
        days = 14
        project_id = 1

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1

        result = self.service.get_shortage_trends(days, project_id)

        # 验证 filter 被调用（项目筛选）
        self.assertTrue(mock_query.filter.called)
        self.assertIsInstance(result, dict)

    def test_build_shortage_daily_report(self):
        """测试日报序列化方法"""
        # Mock ShortageDailyReport
        mock_report = MagicMock()
        mock_report.report_date = date(2026, 2, 20)
        mock_report.new_alerts = 5
        mock_report.resolved_alerts = 3
        mock_report.pending_alerts = 2
        mock_report.overdue_alerts = 1
        mock_report.level1_count = 1
        mock_report.level2_count = 2
        mock_report.level3_count = 3
        mock_report.level4_count = 4
        mock_report.new_reports = 10
        mock_report.resolved_reports = 5
        mock_report.total_work_orders = 100
        mock_report.kit_complete_count = 80
        mock_report.kit_rate = Decimal("0.8")
        mock_report.expected_arrivals = 20
        mock_report.actual_arrivals = 18
        mock_report.delayed_arrivals = 2
        mock_report.on_time_rate = Decimal("0.9")
        mock_report.avg_response_minutes = 30
        mock_report.avg_resolve_hours = Decimal("2.5")
        mock_report.stoppage_count = 3
        mock_report.stoppage_hours = Decimal("5.5")

        result = ShortageAnalyticsService._build_shortage_daily_report(mock_report)

        self.assertEqual(result["date"], "2026-02-20")
        self.assertEqual(result["alerts"]["new"], 5)
        self.assertEqual(result["alerts"]["levels"]["level1"], 1)
        self.assertEqual(result["kit"]["kit_rate"], 0.8)
        self.assertEqual(result["arrivals"]["on_time_rate"], 0.9)
        self.assertEqual(result["response"]["avg_resolve_hours"], 2.5)


if __name__ == "__main__":
    unittest.main()

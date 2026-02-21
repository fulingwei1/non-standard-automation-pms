# -*- coding: utf-8 -*-
"""
增强版 ShortageAnalyticsService 单元测试
覆盖所有核心方法和边界条件
"""
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.services.shortage_analytics.shortage_analytics_service import ShortageAnalyticsService


class TestShortageAnalyticsServiceInit(unittest.TestCase):
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        mock_db = MagicMock()
        service = ShortageAnalyticsService(db=mock_db)
        self.assertEqual(service.db, mock_db)

    def test_init_stores_db_reference(self):
        """测试初始化存储数据库引用"""
        mock_db = MagicMock()
        service = ShortageAnalyticsService(mock_db)
        self.assertIsNotNone(service.db)


class TestGetDashboardData(unittest.TestCase):
    """测试获取看板数据"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = ShortageAnalyticsService(self.mock_db)

    def test_get_dashboard_data_without_project_filter(self):
        """测试不带项目过滤的看板数据"""
        # Mock 所有查询
        mock_report_query = MagicMock()
        mock_report_query.count.return_value = 100
        mock_report_query.filter.return_value = mock_report_query
        
        mock_alert_query = MagicMock()
        mock_alert_query.count.return_value = 50
        mock_alert_query.filter.return_value = mock_alert_query
        
        mock_arrival_query = MagicMock()
        mock_arrival_query.count.return_value = 30
        mock_arrival_query.filter.return_value = mock_arrival_query
        
        mock_sub_query = MagicMock()
        mock_sub_query.count.return_value = 20
        mock_sub_query.filter.return_value = mock_sub_query
        
        mock_transfer_query = MagicMock()
        mock_transfer_query.count.return_value = 10
        mock_transfer_query.filter.return_value = mock_transfer_query
        
        self.mock_db.query.side_effect = [
            mock_report_query, mock_report_query, mock_report_query, 
            mock_report_query, mock_report_query, mock_report_query,
            mock_alert_query, mock_alert_query, mock_alert_query,
            mock_arrival_query, mock_arrival_query, mock_arrival_query,
            mock_sub_query, mock_sub_query,
            mock_transfer_query, mock_transfer_query
        ]
        
        # Mock _get_recent_reports
        with patch.object(self.service, '_get_recent_reports', return_value=[]):
            result = self.service.get_dashboard_data()
        
        self.assertIn('reports', result)
        self.assertIn('alerts', result)
        self.assertIn('arrivals', result)
        self.assertIn('substitutions', result)
        self.assertIn('transfers', result)
        self.assertIn('recent_reports', result)

    def test_get_dashboard_data_with_project_filter(self):
        """测试带项目过滤的看板数据"""
        mock_query = MagicMock()
        mock_query.count.return_value = 10
        mock_query.filter.return_value = mock_query
        
        self.mock_db.query.return_value = mock_query
        
        with patch.object(self.service, '_get_recent_reports', return_value=[]):
            result = self.service.get_dashboard_data(project_id=1)
        
        self.assertIsNotNone(result)
        # 验证 filter 被调用（检查项目过滤）
        self.assertTrue(mock_query.filter.called)

    def test_get_dashboard_data_reports_statistics(self):
        """测试缺料上报统计正确性"""
        # ShortageReport query - 一个对象，count() 被多次调用
        mock_report_query = MagicMock()
        # 设置 count side_effect: total, reported, confirmed, handling, resolved, urgent
        mock_report_query.count.side_effect = [100, 20, 30, 25, 25, 15]
        mock_report_query.filter.return_value = mock_report_query
        
        # 为其他查询设置默认值
        mock_other_queries = []
        for _ in range(10):
            q = MagicMock()
            q.count.return_value = 0
            q.filter.return_value = q
            mock_other_queries.append(q)
        
        # db.query 的 side_effect: 第一个是 ShortageReport query
        self.mock_db.query.side_effect = [mock_report_query] + mock_other_queries
        
        with patch.object(self.service, '_get_recent_reports', return_value=[]):
            result = self.service.get_dashboard_data()
        
        self.assertEqual(result['reports']['total'], 100)
        self.assertEqual(result['reports']['reported'], 20)
        self.assertEqual(result['reports']['confirmed'], 30)
        self.assertEqual(result['reports']['handling'], 25)
        self.assertEqual(result['reports']['resolved'], 25)
        self.assertEqual(result['reports']['urgent'], 15)

    def test_get_dashboard_data_alerts_statistics(self):
        """测试系统预警统计正确性"""
        # ShortageReport query - count 被调用 6 次，都返回 0
        mock_report_query = MagicMock()
        mock_report_query.count.return_value = 0
        mock_report_query.filter.return_value = mock_report_query
        
        # MaterialShortage query - count 被调用 3 次
        mock_alert_query = MagicMock()
        mock_alert_query.count.side_effect = [80, 60, 25]  # total, unresolved, critical
        mock_alert_query.filter.return_value = mock_alert_query
        
        # 创建其他查询的 mocks
        other_queries = []
        for _ in range(7):
            q = MagicMock()
            q.count.return_value = 0
            q.filter.return_value = q
            other_queries.append(q)
        
        # db.query 的 side_effect: ShortageReport, MaterialShortage, 然后其他查询
        self.mock_db.query.side_effect = [mock_report_query, mock_alert_query] + other_queries
        
        with patch.object(self.service, '_get_recent_reports', return_value=[]):
            result = self.service.get_dashboard_data()
        
        self.assertEqual(result['alerts']['total'], 80)
        self.assertEqual(result['alerts']['unresolved'], 60)
        self.assertEqual(result['alerts']['critical'], 25)

    def test_get_dashboard_data_empty_database(self):
        """测试空数据库情况"""
        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.filter.return_value = mock_query
        
        self.mock_db.query.return_value = mock_query
        
        with patch.object(self.service, '_get_recent_reports', return_value=[]):
            result = self.service.get_dashboard_data()
        
        self.assertEqual(result['reports']['total'], 0)
        self.assertEqual(result['alerts']['total'], 0)
        self.assertEqual(result['arrivals']['total'], 0)
        self.assertEqual(result['substitutions']['total'], 0)
        self.assertEqual(result['transfers']['total'], 0)
        self.assertEqual(len(result['recent_reports']), 0)


class TestGetRecentReports(unittest.TestCase):
    """测试获取最近上报"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = ShortageAnalyticsService(self.mock_db)

    def test_get_recent_reports_without_project(self):
        """测试不带项目过滤获取最近上报"""
        mock_report = MagicMock()
        mock_report.id = 1
        mock_report.report_no = "SR-001"
        mock_report.project_id = 10
        mock_report.material_name = "Material A"
        mock_report.shortage_qty = Decimal("100.5")
        mock_report.urgent_level = "URGENT"
        mock_report.status = "REPORTED"
        mock_report.report_time = datetime(2026, 1, 15, 10, 0, 0)
        
        mock_project = MagicMock()
        mock_project.project_name = "Project X"
        
        # Mock ShortageReport query
        mock_report_query = MagicMock()
        mock_report_query.order_by.return_value.limit.return_value.all.return_value = [mock_report]
        
        # Mock Project query
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = mock_project
        
        self.mock_db.query.side_effect = [mock_report_query, mock_project_query]
        
        result = self.service._get_recent_reports()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 1)
        self.assertEqual(result[0]['report_no'], "SR-001")
        self.assertEqual(result[0]['project_name'], "Project X")
        self.assertEqual(result[0]['shortage_qty'], 100.5)

    def test_get_recent_reports_with_project(self):
        """测试带项目过滤获取最近上报"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.limit.return_value.all.return_value = []
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service._get_recent_reports(project_id=5)
        
        self.assertEqual(len(result), 0)
        mock_query.filter.assert_called()

    def test_get_recent_reports_limit_10(self):
        """测试最多返回10条记录"""
        mock_reports = [MagicMock(
            id=i,
            report_no=f"SR-{i:03d}",
            project_id=1,
            material_name=f"Material {i}",
            shortage_qty=Decimal("10"),
            urgent_level="NORMAL",
            status="REPORTED",
            report_time=datetime.now()
        ) for i in range(15)]
        
        mock_project = MagicMock()
        mock_project.project_name = "Test Project"
        
        mock_query = MagicMock()
        mock_query.order_by.return_value.limit.return_value.all.return_value = mock_reports[:10]
        
        project_queries = [MagicMock(first=lambda: mock_project) for _ in range(10)]
        self.mock_db.query.side_effect = [mock_query] + project_queries
        
        result = self.service._get_recent_reports()
        
        self.assertEqual(len(result), 10)

    def test_get_recent_reports_no_project_found(self):
        """测试项目未找到的情况"""
        mock_report = MagicMock()
        mock_report.id = 1
        mock_report.report_no = "SR-001"
        mock_report.project_id = 999
        mock_report.material_name = "Material A"
        mock_report.shortage_qty = Decimal("50")
        mock_report.urgent_level = "NORMAL"
        mock_report.status = "REPORTED"
        mock_report.report_time = None  # 测试空时间
        
        # Mock ShortageReport query
        mock_report_query = MagicMock()
        mock_report_query.order_by.return_value.limit.return_value.all.return_value = [mock_report]
        
        # Mock Project query - 项目未找到
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = None
        
        self.mock_db.query.side_effect = [mock_report_query, mock_project_query]
        
        result = self.service._get_recent_reports()
        
        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0]['project_name'])
        self.assertIsNone(result[0]['report_time'])


class TestGetDailyReport(unittest.TestCase):
    """测试获取缺料日报（实时计算）"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = ShortageAnalyticsService(self.mock_db)

    def test_get_daily_report_default_today(self):
        """测试默认使用今天日期"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_daily_report()
        
        self.assertEqual(result['report_date'], str(date.today()))
        self.assertEqual(result['total_reports'], 0)

    def test_get_daily_report_specific_date(self):
        """测试指定日期"""
        test_date = date(2026, 1, 15)
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_daily_report(report_date=test_date)
        
        self.assertEqual(result['report_date'], '2026-01-15')

    def test_get_daily_report_by_urgent_level(self):
        """测试按紧急程度统计"""
        mock_report1 = MagicMock(urgent_level='URGENT', status='REPORTED', 
                                 material_id=1, material_name='Mat A',
                                 project_id=1, shortage_qty=Decimal('10'))
        mock_report2 = MagicMock(urgent_level='CRITICAL', status='HANDLING',
                                 material_id=2, material_name='Mat B',
                                 project_id=2, shortage_qty=Decimal('20'))
        mock_report3 = MagicMock(urgent_level='URGENT', status='RESOLVED',
                                 material_id=3, material_name='Mat C',
                                 project_id=1, shortage_qty=Decimal('15'))
        
        mock_project1 = MagicMock(project_name="Project A")
        mock_project2 = MagicMock(project_name="Project B")
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_report1, mock_report2, mock_report3]
        
        self.mock_db.query.side_effect = [
            mock_query,
            MagicMock(first=lambda: mock_project1),
            MagicMock(first=lambda: mock_project2)
        ]
        
        result = self.service.get_daily_report()
        
        self.assertEqual(result['total_reports'], 3)
        self.assertEqual(result['by_urgent']['URGENT'], 2)
        self.assertEqual(result['by_urgent']['CRITICAL'], 1)

    def test_get_daily_report_by_status(self):
        """测试按状态统计"""
        reports = [
            MagicMock(urgent_level='NORMAL', status='REPORTED', material_id=1, 
                     material_name='M1', project_id=1, shortage_qty=Decimal('5')),
            MagicMock(urgent_level='NORMAL', status='REPORTED', material_id=2,
                     material_name='M2', project_id=1, shortage_qty=Decimal('5')),
            MagicMock(urgent_level='NORMAL', status='HANDLING', material_id=3,
                     material_name='M3', project_id=1, shortage_qty=Decimal('5'))
        ]
        
        mock_project = MagicMock(project_name="Test Project")
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = reports
        
        self.mock_db.query.side_effect = [mock_query] + [MagicMock(first=lambda: mock_project)]
        
        result = self.service.get_daily_report()
        
        self.assertEqual(result['by_status']['REPORTED'], 2)
        self.assertEqual(result['by_status']['HANDLING'], 1)

    def test_get_daily_report_by_material(self):
        """测试按物料统计"""
        reports = [
            MagicMock(urgent_level='NORMAL', status='REPORTED', material_id=1, 
                     material_name='Material X', project_id=1, shortage_qty=Decimal('10')),
            MagicMock(urgent_level='NORMAL', status='HANDLING', material_id=1,
                     material_name='Material X', project_id=1, shortage_qty=Decimal('15')),
            MagicMock(urgent_level='NORMAL', status='REPORTED', material_id=2,
                     material_name='Material Y', project_id=1, shortage_qty=Decimal('20'))
        ]
        
        mock_project = MagicMock(project_name="Test")
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = reports
        
        self.mock_db.query.side_effect = [mock_query] + [MagicMock(first=lambda: mock_project)]
        
        result = self.service.get_daily_report()
        
        materials = result['by_material']
        self.assertEqual(len(materials), 2)
        
        # 查找 Material X 的统计
        mat_x = next((m for m in materials if m['material_name'] == 'Material X'), None)
        self.assertIsNotNone(mat_x)
        self.assertEqual(mat_x['count'], 2)
        self.assertEqual(mat_x['total_shortage_qty'], 25.0)

    def test_get_daily_report_by_project(self):
        """测试按项目统计"""
        reports = [
            MagicMock(urgent_level='CRITICAL', status='REPORTED', material_id=1, 
                     material_name='M1', project_id=1, shortage_qty=Decimal('10')),
            MagicMock(urgent_level='URGENT', status='HANDLING', material_id=2,
                     material_name='M2', project_id=1, shortage_qty=Decimal('20')),
            MagicMock(urgent_level='NORMAL', status='REPORTED', material_id=3,
                     material_name='M3', project_id=2, shortage_qty=Decimal('30'))
        ]
        
        mock_project1 = MagicMock(project_name="Project 1")
        mock_project2 = MagicMock(project_name="Project 2")
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = reports
        
        self.mock_db.query.side_effect = [
            mock_query,
            MagicMock(first=lambda: mock_project1),
            MagicMock(first=lambda: mock_project2)
        ]
        
        result = self.service.get_daily_report()
        
        projects = result['by_project']
        self.assertEqual(len(projects), 2)
        
        proj1 = next((p for p in projects if p['project_id'] == 1), None)
        self.assertEqual(proj1['shortage_count'], 2)
        self.assertEqual(proj1['total_shortage_qty'], 30.0)
        self.assertEqual(proj1['critical_count'], 2)  # URGENT + CRITICAL

    def test_get_daily_report_with_project_filter(self):
        """测试带项目过滤的日报"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_daily_report(project_id=5)
        
        self.assertIsNotNone(result)
        # 验证 filter 被调用两次（日期 + 项目）
        self.assertEqual(mock_query.filter.call_count, 2)


class TestGetLatestDailyReport(unittest.TestCase):
    """测试获取最新日报（预生成）"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = ShortageAnalyticsService(self.mock_db)

    def test_get_latest_daily_report_exists(self):
        """测试获取存在的最新日报"""
        mock_report = MagicMock()
        mock_report.report_date = date(2026, 1, 15)
        mock_report.new_alerts = 10
        mock_report.resolved_alerts = 5
        mock_report.pending_alerts = 15
        mock_report.overdue_alerts = 3
        mock_report.level1_count = 2
        mock_report.level2_count = 3
        mock_report.level3_count = 5
        mock_report.level4_count = 5
        mock_report.new_reports = 8
        mock_report.resolved_reports = 4
        mock_report.total_work_orders = 100
        mock_report.kit_complete_count = 85
        mock_report.kit_rate = Decimal('0.85')
        mock_report.expected_arrivals = 20
        mock_report.actual_arrivals = 18
        mock_report.delayed_arrivals = 2
        mock_report.on_time_rate = Decimal('0.90')
        mock_report.avg_response_minutes = 45
        mock_report.avg_resolve_hours = Decimal('12.5')
        mock_report.stoppage_count = 2
        mock_report.stoppage_hours = Decimal('4.0')
        
        # Mock max query
        mock_max_query = MagicMock()
        mock_max_query.scalar.return_value = date(2026, 1, 15)
        
        # Mock report query
        mock_report_query = MagicMock()
        mock_report_query.filter.return_value.first.return_value = mock_report
        
        self.mock_db.query.side_effect = [mock_max_query, mock_report_query]
        
        result = self.service.get_latest_daily_report()
        
        self.assertIsNotNone(result)
        self.assertEqual(result['date'], '2026-01-15')
        self.assertEqual(result['alerts']['new'], 10)
        self.assertEqual(result['kit']['kit_rate'], 0.85)

    def test_get_latest_daily_report_no_data(self):
        """测试无日报数据"""
        mock_query = MagicMock()
        mock_query.scalar.return_value = None
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_latest_daily_report()
        
        self.assertIsNone(result)

    def test_get_latest_daily_report_date_exists_but_no_report(self):
        """测试日期存在但报表不存在"""
        mock_max_query = MagicMock()
        mock_max_query.scalar.return_value = date(2026, 1, 15)
        
        mock_report_query = MagicMock()
        mock_report_query.filter.return_value.first.return_value = None
        
        self.mock_db.query.side_effect = [mock_max_query, mock_report_query]
        
        result = self.service.get_latest_daily_report()
        
        self.assertIsNone(result)


class TestGetDailyReportByDate(unittest.TestCase):
    """测试按日期获取日报（预生成）"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = ShortageAnalyticsService(self.mock_db)

    def test_get_daily_report_by_date_exists(self):
        """测试获取存在的日报"""
        test_date = date(2026, 1, 10)
        
        mock_report = MagicMock()
        mock_report.report_date = test_date
        mock_report.new_alerts = 5
        mock_report.resolved_alerts = 2
        mock_report.pending_alerts = 10
        mock_report.overdue_alerts = 1
        mock_report.level1_count = 1
        mock_report.level2_count = 2
        mock_report.level3_count = 3
        mock_report.level4_count = 4
        mock_report.new_reports = 3
        mock_report.resolved_reports = 1
        mock_report.total_work_orders = 50
        mock_report.kit_complete_count = 40
        mock_report.kit_rate = Decimal('0.80')
        mock_report.expected_arrivals = 10
        mock_report.actual_arrivals = 9
        mock_report.delayed_arrivals = 1
        mock_report.on_time_rate = Decimal('0.90')
        mock_report.avg_response_minutes = 30
        mock_report.avg_resolve_hours = Decimal('10.0')
        mock_report.stoppage_count = 1
        mock_report.stoppage_hours = Decimal('2.0')
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_report
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_daily_report_by_date(test_date)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['date'], '2026-01-10')

    def test_get_daily_report_by_date_not_exists(self):
        """测试获取不存在的日报"""
        test_date = date(2026, 1, 1)
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_daily_report_by_date(test_date)
        
        self.assertIsNone(result)


class TestGetShortageTrends(unittest.TestCase):
    """测试获取缺料趋势分析"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = ShortageAnalyticsService(self.mock_db)

    def test_get_shortage_trends_default_30_days(self):
        """测试默认30天趋势"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_shortage_trends()
        
        self.assertEqual(result['period']['days'], 30)
        self.assertEqual(len(result['daily']), 31)  # 包含开始和结束日期

    def test_get_shortage_trends_custom_days(self):
        """测试自定义天数趋势"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_shortage_trends(days=7)
        
        self.assertEqual(result['period']['days'], 7)
        self.assertEqual(len(result['daily']), 8)

    def test_get_shortage_trends_with_data(self):
        """测试有数据的趋势分析"""
        # Mock queries with varying counts
        def mock_count_side_effect(*args, **kwargs):
            # 交替返回新增和解决的计数
            counts = [5, 3, 8, 4, 6, 2]  # 3天的数据（新增，解决）* 2（两次查询每天）
            return counts.pop(0) if counts else 0
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.side_effect = mock_count_side_effect
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_shortage_trends(days=2)
        
        self.assertEqual(len(result['daily']), 3)
        self.assertIn('summary', result)
        self.assertIn('avg_daily_new', result['summary'])
        self.assertIn('avg_daily_resolved', result['summary'])

    def test_get_shortage_trends_with_project_filter(self):
        """测试带项目过滤的趋势"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_shortage_trends(days=7, project_id=3)
        
        self.assertIsNotNone(result)
        # 每天会调用 filter 多次（日期过滤 + 项目过滤）
        self.assertTrue(mock_query.filter.called)

    def test_get_shortage_trends_summary_calculation(self):
        """测试汇总统计计算正确性"""
        # 模拟5天的数据，每天新增10个，解决8个
        call_count = [0]
        
        def mock_count():
            call_count[0] += 1
            # 奇数次调用返回新增数，偶数次返回解决数
            return 10 if call_count[0] % 2 == 1 else 8
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count = mock_count
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_shortage_trends(days=4)
        
        summary = result['summary']
        self.assertEqual(summary['total_new'], 50)  # 5天 * 10
        self.assertEqual(summary['total_resolved'], 40)  # 5天 * 8
        self.assertEqual(summary['avg_daily_new'], 12.5)  # 50 / 4
        self.assertEqual(summary['avg_daily_resolved'], 10.0)  # 40 / 4


class TestBuildShortageDailyReport(unittest.TestCase):
    """测试构建日报数据（静态方法）"""

    def test_build_shortage_daily_report_complete(self):
        """测试完整的日报数据构建"""
        mock_report = MagicMock()
        mock_report.report_date = date(2026, 1, 20)
        mock_report.new_alerts = 12
        mock_report.resolved_alerts = 8
        mock_report.pending_alerts = 20
        mock_report.overdue_alerts = 5
        mock_report.level1_count = 3
        mock_report.level2_count = 4
        mock_report.level3_count = 7
        mock_report.level4_count = 6
        mock_report.new_reports = 10
        mock_report.resolved_reports = 7
        mock_report.total_work_orders = 150
        mock_report.kit_complete_count = 120
        mock_report.kit_rate = Decimal('0.80')
        mock_report.expected_arrivals = 25
        mock_report.actual_arrivals = 22
        mock_report.delayed_arrivals = 3
        mock_report.on_time_rate = Decimal('0.88')
        mock_report.avg_response_minutes = 60
        mock_report.avg_resolve_hours = Decimal('15.5')
        mock_report.stoppage_count = 3
        mock_report.stoppage_hours = Decimal('6.5')
        
        result = ShortageAnalyticsService._build_shortage_daily_report(mock_report)
        
        self.assertEqual(result['date'], '2026-01-20')
        self.assertEqual(result['alerts']['new'], 12)
        self.assertEqual(result['alerts']['levels']['level1'], 3)
        self.assertEqual(result['kit']['kit_rate'], 0.80)
        self.assertEqual(result['arrivals']['on_time_rate'], 0.88)
        self.assertEqual(result['response']['avg_resolve_hours'], 15.5)
        self.assertEqual(result['stoppage']['hours'], 6.5)

    def test_build_shortage_daily_report_with_none_values(self):
        """测试包含 None 值的日报"""
        mock_report = MagicMock()
        mock_report.report_date = date(2026, 1, 20)
        mock_report.new_alerts = 0
        mock_report.resolved_alerts = 0
        mock_report.pending_alerts = 0
        mock_report.overdue_alerts = 0
        mock_report.level1_count = 0
        mock_report.level2_count = 0
        mock_report.level3_count = 0
        mock_report.level4_count = 0
        mock_report.new_reports = 0
        mock_report.resolved_reports = 0
        mock_report.total_work_orders = 0
        mock_report.kit_complete_count = 0
        mock_report.kit_rate = None
        mock_report.expected_arrivals = 0
        mock_report.actual_arrivals = 0
        mock_report.delayed_arrivals = 0
        mock_report.on_time_rate = None
        mock_report.avg_response_minutes = 0
        mock_report.avg_resolve_hours = None
        mock_report.stoppage_count = 0
        mock_report.stoppage_hours = None
        
        result = ShortageAnalyticsService._build_shortage_daily_report(mock_report)
        
        self.assertEqual(result['kit']['kit_rate'], 0.0)
        self.assertEqual(result['arrivals']['on_time_rate'], 0.0)
        self.assertEqual(result['response']['avg_resolve_hours'], 0.0)
        self.assertEqual(result['stoppage']['hours'], 0.0)


if __name__ == '__main__':
    unittest.main()

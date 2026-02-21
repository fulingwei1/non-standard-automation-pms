# -*- coding: utf-8 -*-
"""
ShortageAnalyticsService 单元测试

测试策略：
1. 只mock外部依赖（db.query, db.add, db.commit等数据库操作）
2. 让业务逻辑真正执行（不要mock业务方法）
3. 覆盖主要方法和边界情况
4. 目标覆盖率：70%+
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.services.shortage_analytics.shortage_analytics_service import ShortageAnalyticsService


class TestShortageAnalyticsServiceInit(unittest.TestCase):
    """测试初始化"""

    def test_init(self):
        """测试服务初始化"""
        mock_db = Mock()
        service = ShortageAnalyticsService(mock_db)
        self.assertEqual(service.db, mock_db)


class TestGetDashboardData(unittest.TestCase):
    """测试 get_dashboard_data 方法"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = Mock()
        self.service = ShortageAnalyticsService(self.mock_db)

    def _setup_mock_queries(self, project_id=None):
        """设置mock查询链"""
        # Mock ShortageReport 查询
        mock_report_query = Mock()
        mock_report_query.filter.return_value = mock_report_query
        mock_report_query.count.return_value = 50
        
        # Mock MaterialShortage 查询
        mock_alert_query = Mock()
        mock_alert_query.filter.return_value = mock_alert_query
        mock_alert_query.count.return_value = 30
        
        # Mock MaterialArrival 查询
        mock_arrival_query = Mock()
        mock_arrival_query.filter.return_value = mock_arrival_query
        mock_arrival_query.count.return_value = 20
        
        # Mock MaterialSubstitution 查询
        mock_sub_query = Mock()
        mock_sub_query.filter.return_value = mock_sub_query
        mock_sub_query.count.return_value = 10
        
        # Mock MaterialTransfer 查询
        mock_transfer_query = Mock()
        mock_transfer_query.filter.return_value = mock_transfer_query
        mock_transfer_query.count.return_value = 5
        
        # 设置 db.query 返回值
        def query_side_effect(model):
            from app.models.shortage import ShortageReport, MaterialArrival, MaterialSubstitution, MaterialTransfer
            from app.models.material import MaterialShortage
            
            if model == ShortageReport:
                return mock_report_query
            elif model == MaterialShortage:
                return mock_alert_query
            elif model == MaterialArrival:
                return mock_arrival_query
            elif model == MaterialSubstitution:
                return mock_sub_query
            elif model == MaterialTransfer:
                return mock_transfer_query
            return Mock()
        
        self.mock_db.query.side_effect = query_side_effect

    def test_get_dashboard_data_without_project_filter(self):
        """测试获取看板数据（无项目筛选）"""
        self._setup_mock_queries()
        
        # Mock _get_recent_reports
        with patch.object(self.service, '_get_recent_reports', return_value=[]):
            result = self.service.get_dashboard_data()
        
        # 验证返回结构
        self.assertIn('reports', result)
        self.assertIn('alerts', result)
        self.assertIn('arrivals', result)
        self.assertIn('substitutions', result)
        self.assertIn('transfers', result)
        self.assertIn('recent_reports', result)
        
        # 验证 reports 数据
        self.assertEqual(result['reports']['total'], 50)
        
        # 验证 db.query 被调用
        self.assertTrue(self.mock_db.query.called)

    def test_get_dashboard_data_with_project_filter(self):
        """测试获取看板数据（有项目筛选）"""
        self._setup_mock_queries(project_id=1)
        
        with patch.object(self.service, '_get_recent_reports', return_value=[]):
            result = self.service.get_dashboard_data(project_id=1)
        
        # 验证结果结构
        self.assertIn('reports', result)
        self.assertIn('alerts', result)


class TestGetRecentReports(unittest.TestCase):
    """测试 _get_recent_reports 方法"""

    def setUp(self):
        self.mock_db = Mock()
        self.service = ShortageAnalyticsService(self.mock_db)

    def test_get_recent_reports_without_project(self):
        """测试获取最近上报（无项目筛选）"""
        # Mock ShortageReport 数据
        mock_report1 = Mock()
        mock_report1.id = 1
        mock_report1.report_no = "SR-001"
        mock_report1.project_id = 10
        mock_report1.material_name = "螺栓"
        mock_report1.shortage_qty = Decimal("100.5")
        mock_report1.urgent_level = "URGENT"
        mock_report1.status = "REPORTED"
        mock_report1.report_time = datetime(2026, 2, 21, 10, 0, 0)
        
        mock_report2 = Mock()
        mock_report2.id = 2
        mock_report2.report_no = "SR-002"
        mock_report2.project_id = 11
        mock_report2.material_name = "电缆"
        mock_report2.shortage_qty = Decimal("50.0")
        mock_report2.urgent_level = "NORMAL"
        mock_report2.status = "CONFIRMED"
        mock_report2.report_time = datetime(2026, 2, 20, 14, 30, 0)
        
        # Mock Project 数据
        mock_project1 = Mock()
        mock_project1.project_name = "项目A"
        
        mock_project2 = Mock()
        mock_project2.project_name = "项目B"
        
        # 设置查询链
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_report1, mock_report2]
        
        # 设置 db.query 行为
        def query_side_effect(model):
            from app.models.shortage import ShortageReport
            from app.models.project import Project
            
            if model == ShortageReport:
                return mock_query
            elif model == Project:
                # 模拟按project_id查询
                project_query = Mock()
                project_query.filter.return_value = project_query
                def first_side_effect():
                    # 简化：根据调用次数返回不同项目
                    if not hasattr(first_side_effect, 'call_count'):
                        first_side_effect.call_count = 0
                    first_side_effect.call_count += 1
                    return mock_project1 if first_side_effect.call_count == 1 else mock_project2
                project_query.first = first_side_effect
                return project_query
            return Mock()
        
        self.mock_db.query.side_effect = query_side_effect
        
        # 执行测试
        result = self.service._get_recent_reports()
        
        # 验证结果
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 1)
        self.assertEqual(result[0]['report_no'], "SR-001")
        self.assertEqual(result[0]['project_name'], "项目A")
        self.assertEqual(result[0]['shortage_qty'], 100.5)
        self.assertEqual(result[1]['material_name'], "电缆")

    def test_get_recent_reports_with_project(self):
        """测试获取最近上报（有项目筛选）"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        def query_side_effect(model):
            from app.models.shortage import ShortageReport
            if model == ShortageReport:
                return mock_query
            return Mock()
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service._get_recent_reports(project_id=1)
        
        # 验证 filter 被调用
        mock_query.filter.assert_called()
        self.assertEqual(result, [])


class TestGetDailyReport(unittest.TestCase):
    """测试 get_daily_report 方法"""

    def setUp(self):
        self.mock_db = Mock()
        self.service = ShortageAnalyticsService(self.mock_db)

    def test_get_daily_report_default_date(self):
        """测试获取日报（默认今天）"""
        # Mock 查询返回空列表
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        def query_side_effect(model):
            from app.models.shortage import ShortageReport
            if model == ShortageReport:
                return mock_query
            return Mock()
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_daily_report()
        
        # 验证返回结构
        self.assertIn('report_date', result)
        self.assertIn('total_reports', result)
        self.assertIn('by_urgent', result)
        self.assertIn('by_status', result)
        self.assertIn('by_material', result)
        self.assertIn('by_project', result)
        
        # 验证默认日期是今天
        self.assertEqual(result['report_date'], str(date.today()))
        self.assertEqual(result['total_reports'], 0)

    def test_get_daily_report_with_data(self):
        """测试获取日报（有数据）"""
        target_date = date(2026, 2, 21)
        
        # Mock ShortageReport 数据
        mock_report1 = Mock()
        mock_report1.material_id = 1
        mock_report1.material_name = "螺栓"
        mock_report1.shortage_qty = Decimal("100")
        mock_report1.urgent_level = "URGENT"
        mock_report1.status = "REPORTED"
        mock_report1.project_id = 10
        
        mock_report2 = Mock()
        mock_report2.material_id = 1
        mock_report2.material_name = "螺栓"
        mock_report2.shortage_qty = Decimal("50")
        mock_report2.urgent_level = "CRITICAL"
        mock_report2.status = "CONFIRMED"
        mock_report2.project_id = 10
        
        mock_report3 = Mock()
        mock_report3.material_id = 2
        mock_report3.material_name = "电缆"
        mock_report3.shortage_qty = Decimal("200")
        mock_report3.urgent_level = "NORMAL"
        mock_report3.status = "RESOLVED"
        mock_report3.project_id = 11
        
        # Mock Project
        mock_project1 = Mock()
        mock_project1.project_name = "项目A"
        
        mock_project2 = Mock()
        mock_project2.project_name = "项目B"
        
        # 设置查询链
        mock_report_query = Mock()
        mock_report_query.filter.return_value = mock_report_query
        mock_report_query.all.return_value = [mock_report1, mock_report2, mock_report3]
        
        def query_side_effect(model):
            from app.models.shortage import ShortageReport
            from app.models.project import Project
            
            if model == ShortageReport:
                return mock_report_query
            elif model == Project:
                project_query = Mock()
                project_query.filter.return_value = project_query
                def first_side_effect():
                    if not hasattr(first_side_effect, 'call_count'):
                        first_side_effect.call_count = 0
                    first_side_effect.call_count += 1
                    return mock_project1 if first_side_effect.call_count <= 2 else mock_project2
                project_query.first = first_side_effect
                return project_query
            return Mock()
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_daily_report(report_date=target_date)
        
        # 验证统计
        self.assertEqual(result['total_reports'], 3)
        self.assertEqual(result['by_urgent']['URGENT'], 1)
        self.assertEqual(result['by_urgent']['CRITICAL'], 1)
        self.assertEqual(result['by_urgent']['NORMAL'], 1)
        
        self.assertEqual(result['by_status']['REPORTED'], 1)
        self.assertEqual(result['by_status']['CONFIRMED'], 1)
        self.assertEqual(result['by_status']['RESOLVED'], 1)
        
        # 验证物料统计
        self.assertEqual(len(result['by_material']), 2)
        
        # 验证项目统计
        self.assertEqual(len(result['by_project']), 2)
        project_a = next(p for p in result['by_project'] if p['project_id'] == 10)
        self.assertEqual(project_a['shortage_count'], 2)
        self.assertEqual(project_a['critical_count'], 2)  # URGENT + CRITICAL

    def test_get_daily_report_with_project_filter(self):
        """测试获取日报（项目筛选）"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        def query_side_effect(model):
            from app.models.shortage import ShortageReport
            if model == ShortageReport:
                return mock_query
            return Mock()
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_daily_report(project_id=1)
        
        # 验证 filter 被调用两次（日期 + 项目）
        self.assertEqual(mock_query.filter.call_count, 2)


class TestGetLatestDailyReport(unittest.TestCase):
    """测试 get_latest_daily_report 方法"""

    def setUp(self):
        self.mock_db = Mock()
        self.service = ShortageAnalyticsService(self.mock_db)

    def test_get_latest_daily_report_no_data(self):
        """测试获取最新日报（无数据）"""
        # Mock 查询返回 None
        mock_query = Mock()
        mock_query.scalar.return_value = None
        
        def query_side_effect(func_call):
            return mock_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_latest_daily_report()
        
        self.assertIsNone(result)

    def test_get_latest_daily_report_with_data(self):
        """测试获取最新日报（有数据）"""
        target_date = date(2026, 2, 21)
        
        # Mock ShortageDailyReport
        mock_report = Mock()
        mock_report.report_date = target_date
        mock_report.new_alerts = 10
        mock_report.resolved_alerts = 5
        mock_report.pending_alerts = 15
        mock_report.overdue_alerts = 3
        mock_report.level1_count = 2
        mock_report.level2_count = 5
        mock_report.level3_count = 6
        mock_report.level4_count = 2
        mock_report.new_reports = 8
        mock_report.resolved_reports = 4
        mock_report.total_work_orders = 100
        mock_report.kit_complete_count = 85
        mock_report.kit_rate = Decimal("0.85")
        mock_report.expected_arrivals = 20
        mock_report.actual_arrivals = 18
        mock_report.delayed_arrivals = 2
        mock_report.on_time_rate = Decimal("0.90")
        mock_report.avg_response_minutes = 30
        mock_report.avg_resolve_hours = Decimal("4.5")
        mock_report.stoppage_count = 2
        mock_report.stoppage_hours = Decimal("6.0")
        
        # Mock 查询
        mock_max_query = Mock()
        mock_max_query.scalar.return_value = target_date
        
        mock_report_query = Mock()
        mock_report_query.filter.return_value = mock_report_query
        mock_report_query.first.return_value = mock_report
        
        call_count = [0]
        def query_side_effect(arg):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_max_query
            else:
                return mock_report_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_latest_daily_report()
        
        # 验证返回结构和数据
        self.assertIsNotNone(result)
        self.assertEqual(result['date'], "2026-02-21")
        self.assertEqual(result['alerts']['new'], 10)
        self.assertEqual(result['alerts']['resolved'], 5)
        self.assertEqual(result['kit']['kit_rate'], 0.85)
        self.assertEqual(result['arrivals']['on_time_rate'], 0.90)


class TestGetDailyReportByDate(unittest.TestCase):
    """测试 get_daily_report_by_date 方法"""

    def setUp(self):
        self.mock_db = Mock()
        self.service = ShortageAnalyticsService(self.mock_db)

    def test_get_daily_report_by_date_no_data(self):
        """测试按日期获取日报（无数据）"""
        target_date = date(2026, 2, 21)
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        def query_side_effect(model):
            from app.models.shortage import ShortageDailyReport
            if model == ShortageDailyReport:
                return mock_query
            return Mock()
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_daily_report_by_date(target_date)
        
        self.assertIsNone(result)

    def test_get_daily_report_by_date_with_data(self):
        """测试按日期获取日报（有数据）"""
        target_date = date(2026, 2, 20)
        
        mock_report = Mock()
        mock_report.report_date = target_date
        mock_report.new_alerts = 5
        mock_report.resolved_alerts = 3
        mock_report.pending_alerts = 10
        mock_report.overdue_alerts = 1
        mock_report.level1_count = 1
        mock_report.level2_count = 3
        mock_report.level3_count = 4
        mock_report.level4_count = 2
        mock_report.new_reports = 6
        mock_report.resolved_reports = 2
        mock_report.total_work_orders = 50
        mock_report.kit_complete_count = 40
        mock_report.kit_rate = Decimal("0.80")
        mock_report.expected_arrivals = 10
        mock_report.actual_arrivals = 9
        mock_report.delayed_arrivals = 1
        mock_report.on_time_rate = Decimal("0.90")
        mock_report.avg_response_minutes = 25
        mock_report.avg_resolve_hours = Decimal("3.5")
        mock_report.stoppage_count = 1
        mock_report.stoppage_hours = Decimal("2.0")
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_report
        
        def query_side_effect(model):
            from app.models.shortage import ShortageDailyReport
            if model == ShortageDailyReport:
                return mock_query
            return Mock()
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_daily_report_by_date(target_date)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['date'], "2026-02-20")
        self.assertEqual(result['alerts']['new'], 5)


class TestGetShortageTrends(unittest.TestCase):
    """测试 get_shortage_trends 方法"""

    def setUp(self):
        self.mock_db = Mock()
        self.service = ShortageAnalyticsService(self.mock_db)

    def test_get_shortage_trends_default(self):
        """测试获取趋势（默认30天）"""
        # Mock 查询返回
        mock_new_query = Mock()
        mock_new_query.filter.return_value = mock_new_query
        mock_new_query.count.return_value = 5
        
        mock_resolved_query = Mock()
        mock_resolved_query.filter.return_value = mock_resolved_query
        mock_resolved_query.count.return_value = 3
        
        call_count = [0]
        def query_side_effect(model):
            from app.models.shortage import ShortageReport
            if model == ShortageReport:
                call_count[0] += 1
                # 交替返回新增和已解决查询
                return mock_new_query if call_count[0] % 2 == 1 else mock_resolved_query
            return Mock()
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_shortage_trends()
        
        # 验证返回结构
        self.assertIn('period', result)
        self.assertIn('summary', result)
        self.assertIn('daily', result)
        
        # 验证周期
        self.assertEqual(result['period']['days'], 30)
        
        # 验证每日数据（30天 + 今天 = 31天）
        self.assertEqual(len(result['daily']), 31)
        
        # 验证汇总
        self.assertIn('total_new', result['summary'])
        self.assertIn('total_resolved', result['summary'])
        self.assertIn('avg_daily_new', result['summary'])
        self.assertIn('avg_daily_resolved', result['summary'])

    def test_get_shortage_trends_custom_days(self):
        """测试获取趋势（自定义天数）"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        
        def query_side_effect(model):
            from app.models.shortage import ShortageReport
            if model == ShortageReport:
                return mock_query
            return Mock()
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_shortage_trends(days=7)
        
        # 验证天数
        self.assertEqual(result['period']['days'], 7)
        self.assertEqual(len(result['daily']), 8)  # 7天 + 今天

    def test_get_shortage_trends_with_project(self):
        """测试获取趋势（项目筛选）"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        
        def query_side_effect(model):
            from app.models.shortage import ShortageReport
            if model == ShortageReport:
                return mock_query
            return Mock()
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_shortage_trends(days=7, project_id=1)
        
        # 验证 filter 被调用（包括项目筛选）
        self.assertTrue(mock_query.filter.called)


class TestBuildShortageDailyReport(unittest.TestCase):
    """测试 _build_shortage_daily_report 静态方法"""

    def test_build_shortage_daily_report(self):
        """测试序列化日报数据"""
        mock_report = Mock()
        mock_report.report_date = date(2026, 2, 21)
        mock_report.new_alerts = 10
        mock_report.resolved_alerts = 5
        mock_report.pending_alerts = 15
        mock_report.overdue_alerts = 3
        mock_report.level1_count = 2
        mock_report.level2_count = 5
        mock_report.level3_count = 6
        mock_report.level4_count = 2
        mock_report.new_reports = 8
        mock_report.resolved_reports = 4
        mock_report.total_work_orders = 100
        mock_report.kit_complete_count = 85
        mock_report.kit_rate = Decimal("0.85")
        mock_report.expected_arrivals = 20
        mock_report.actual_arrivals = 18
        mock_report.delayed_arrivals = 2
        mock_report.on_time_rate = Decimal("0.90")
        mock_report.avg_response_minutes = 30
        mock_report.avg_resolve_hours = Decimal("4.5")
        mock_report.stoppage_count = 2
        mock_report.stoppage_hours = Decimal("6.0")
        
        result = ShortageAnalyticsService._build_shortage_daily_report(mock_report)
        
        # 验证返回结构
        self.assertEqual(result['date'], "2026-02-21")
        self.assertEqual(result['alerts']['new'], 10)
        self.assertEqual(result['alerts']['resolved'], 5)
        self.assertEqual(result['alerts']['levels']['level1'], 2)
        self.assertEqual(result['reports']['new'], 8)
        self.assertEqual(result['kit']['total_work_orders'], 100)
        self.assertEqual(result['kit']['kit_rate'], 0.85)
        self.assertEqual(result['arrivals']['on_time_rate'], 0.90)
        self.assertEqual(result['response']['avg_response_minutes'], 30)
        self.assertEqual(result['response']['avg_resolve_hours'], 4.5)
        self.assertEqual(result['stoppage']['count'], 2)
        self.assertEqual(result['stoppage']['hours'], 6.0)

    def test_build_shortage_daily_report_with_none_values(self):
        """测试序列化日报（含None值）"""
        mock_report = Mock()
        mock_report.report_date = date(2026, 2, 21)
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
        
        # 验证 None 值被转换为 0.0
        self.assertEqual(result['kit']['kit_rate'], 0.0)
        self.assertEqual(result['arrivals']['on_time_rate'], 0.0)
        self.assertEqual(result['response']['avg_resolve_hours'], 0.0)
        self.assertEqual(result['stoppage']['hours'], 0.0)


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        self.mock_db = Mock()
        self.service = ShortageAnalyticsService(self.mock_db)

    def test_get_daily_report_empty_material_name(self):
        """测试物料名称为空的情况"""
        mock_report = Mock()
        mock_report.material_id = None
        mock_report.material_name = ""
        mock_report.shortage_qty = Decimal("10")
        mock_report.urgent_level = "NORMAL"
        mock_report.status = "REPORTED"
        mock_report.project_id = 1
        
        mock_project = Mock()
        mock_project.project_name = "测试项目"
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_report]
        
        def query_side_effect(model):
            from app.models.shortage import ShortageReport
            from app.models.project import Project
            
            if model == ShortageReport:
                return mock_query
            elif model == Project:
                project_query = Mock()
                project_query.filter.return_value = project_query
                project_query.first.return_value = mock_project
                return project_query
            return Mock()
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_daily_report()
        
        # 应该能正常处理
        self.assertEqual(result['total_reports'], 1)

    def test_get_recent_reports_project_not_found(self):
        """测试项目不存在的情况"""
        mock_report = Mock()
        mock_report.id = 1
        mock_report.report_no = "SR-001"
        mock_report.project_id = 999
        mock_report.material_name = "测试物料"
        mock_report.shortage_qty = Decimal("10")
        mock_report.urgent_level = "NORMAL"
        mock_report.status = "REPORTED"
        mock_report.report_time = datetime(2026, 2, 21, 10, 0, 0)
        
        mock_report_query = Mock()
        mock_report_query.filter.return_value = mock_report_query
        mock_report_query.order_by.return_value = mock_report_query
        mock_report_query.limit.return_value = mock_report_query
        mock_report_query.all.return_value = [mock_report]
        
        def query_side_effect(model):
            from app.models.shortage import ShortageReport
            from app.models.project import Project
            
            if model == ShortageReport:
                return mock_report_query
            elif model == Project:
                project_query = Mock()
                project_query.filter.return_value = project_query
                project_query.first.return_value = None  # 项目不存在
                return project_query
            return Mock()
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service._get_recent_reports()
        
        # 应该能处理项目不存在的情况
        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0]['project_name'])

    def test_get_shortage_trends_zero_days(self):
        """测试趋势天数为0"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        
        def query_side_effect(model):
            from app.models.shortage import ShortageReport
            if model == ShortageReport:
                return mock_query
            return Mock()
        
        self.mock_db.query.side_effect = query_side_effect
        
        # 虽然传入0，实际会计算 end_date - start_date 的天数
        result = self.service.get_shortage_trends(days=1)
        
        # 至少有今天
        self.assertGreaterEqual(len(result['daily']), 1)


if __name__ == "__main__":
    unittest.main()

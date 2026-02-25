# -*- coding: utf-8 -*-
"""
缺料管理 Dashboard 适配器单元测试

目标：
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率: 70%+
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.schemas.dashboard import (
    DashboardListItem,
    DashboardStatCard,
    DashboardWidget,
    DetailedDashboardResponse,
)
from app.services.dashboard_adapters.shortage import ShortageDashboardAdapter


class TestShortageDashboardAdapter(unittest.TestCase):
    """测试缺料管理 Dashboard 适配器"""

    def setUp(self):
        """每个测试前初始化"""
        # Mock database session
        self.mock_db = MagicMock()
        
        # Mock current user
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.username = "test_user"
        self.mock_user.role = "admin"
        
        # 创建适配器实例
        self.adapter = ShortageDashboardAdapter(
            db=self.mock_db,
            current_user=self.mock_user
        )

    # ========== 基础属性测试 ==========
    
    def test_module_id(self):
        """测试模块ID"""
        self.assertEqual(self.adapter.module_id, "shortage")

    def test_module_name(self):
        """测试模块名称"""
        self.assertEqual(self.adapter.module_name, "缺料管理")

    def test_supported_roles(self):
        """测试支持的角色"""
        expected_roles = ["procurement", "production", "pmo", "admin"]
        self.assertEqual(self.adapter.supported_roles, expected_roles)

    # ========== get_stats() 测试 ==========
    
    def test_get_stats_with_data(self):
        """测试获取统计数据（有数据）"""
        # Mock ShortageReport query
        mock_report_query = MagicMock()
        mock_report_query.count.return_value = 50
        
        # Mock filter chains for different statuses
        mock_reported = MagicMock()
        mock_reported.count.return_value = 10
        
        mock_confirmed = MagicMock()
        mock_confirmed.count.return_value = 15
        
        mock_handling = MagicMock()
        mock_handling.count.return_value = 20
        
        mock_resolved = MagicMock()
        mock_resolved.count.return_value = 5
        
        mock_urgent = MagicMock()
        mock_urgent.count.return_value = 8
        
        # Setup filter behavior
        def report_filter_side_effect(*args, **kwargs):
            # 通过检查调用参数判断返回哪个mock
            filter_expr = args[0] if args else None
            if filter_expr is not None:
                filter_str = str(filter_expr)
                if "REPORTED" in filter_str:
                    return mock_reported
                elif "CONFIRMED" in filter_str:
                    return mock_confirmed
                elif "HANDLING" in filter_str:
                    return mock_handling
                elif "RESOLVED" in filter_str:
                    return mock_resolved
                elif "urgent_level" in filter_str or "URGENT" in filter_str or "CRITICAL" in filter_str:
                    return mock_urgent
            return mock_report_query
        
        mock_report_query.filter.side_effect = report_filter_side_effect
        
        # Mock MaterialShortage query
        mock_alert_query = MagicMock()
        mock_alert_query.count.return_value = 30
        
        mock_unresolved_alerts = MagicMock()
        mock_unresolved_alerts.count.return_value = 12
        
        mock_critical_alerts = MagicMock()
        mock_critical_alerts.count.return_value = 3
        
        def alert_filter_side_effect(*args, **kwargs):
            filter_expr = args[0] if args else None
            if filter_expr is not None:
                filter_str = str(filter_expr)
                if "CRITICAL" in filter_str and "alert_level" in filter_str:
                    return mock_critical_alerts
                elif "status" in filter_str and "!=" in filter_str:
                    return mock_unresolved_alerts
            return mock_alert_query
        
        mock_alert_query.filter.side_effect = alert_filter_side_effect
        
        # Mock MaterialArrival query
        mock_arrival_query = MagicMock()
        mock_arrival_query.count.return_value = 40
        
        mock_pending_arrivals = MagicMock()
        mock_pending_arrivals.count.return_value = 15
        
        mock_delayed_arrivals = MagicMock()
        mock_delayed_arrivals.count.return_value = 6
        
        def arrival_filter_side_effect(*args, **kwargs):
            filter_expr = args[0] if args else None
            if filter_expr is not None:
                filter_str = str(filter_expr)
                if "PENDING" in filter_str:
                    return mock_pending_arrivals
                elif "is_delayed" in filter_str:
                    return mock_delayed_arrivals
            return mock_arrival_query
        
        mock_arrival_query.filter.side_effect = arrival_filter_side_effect
        
        # Setup db.query behavior
        def query_side_effect(model):
            model_name = model.__name__ if hasattr(model, '__name__') else str(model)
            if "ShortageReport" in model_name:
                return mock_report_query
            elif "MaterialShortage" in model_name:
                return mock_alert_query
            elif "MaterialArrival" in model_name:
                return mock_arrival_query
            return MagicMock()
        
        self.mock_db.query.side_effect = query_side_effect
        
        # 执行
        stats = self.adapter.get_stats()
        
        # 验证
        self.assertIsInstance(stats, list)
        self.assertEqual(len(stats), 6)
        
        # 验证每个统计卡片
        stat_dict = {card.key: card for card in stats}
        
        self.assertIn("total_reports", stat_dict)
        self.assertEqual(stat_dict["total_reports"].value, 50)
        self.assertEqual(stat_dict["total_reports"].label, "缺料上报")
        self.assertEqual(stat_dict["total_reports"].unit, "项")
        self.assertEqual(stat_dict["total_reports"].icon, "report")
        self.assertEqual(stat_dict["total_reports"].color, "blue")
        
        self.assertIn("urgent_reports", stat_dict)
        self.assertEqual(stat_dict["urgent_reports"].value, 8)
        self.assertEqual(stat_dict["urgent_reports"].label, "紧急缺料")
        self.assertEqual(stat_dict["urgent_reports"].color, "red")
        
        self.assertIn("unresolved_alerts", stat_dict)
        self.assertEqual(stat_dict["unresolved_alerts"].value, 12)
        self.assertEqual(stat_dict["unresolved_alerts"].label, "未解决预警")
        
        self.assertIn("pending_arrivals", stat_dict)
        self.assertEqual(stat_dict["pending_arrivals"].value, 15)
        
        self.assertIn("delayed_arrivals", stat_dict)
        self.assertEqual(stat_dict["delayed_arrivals"].value, 6)
        
        self.assertIn("resolved_reports", stat_dict)
        self.assertEqual(stat_dict["resolved_reports"].value, 5)

    def test_get_stats_empty_database(self):
        """测试获取统计数据（空数据库）"""
        # Mock empty queries
        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.filter.return_value = mock_query
        
        self.mock_db.query.return_value = mock_query
        
        # 执行
        stats = self.adapter.get_stats()
        
        # 验证
        self.assertEqual(len(stats), 6)
        for card in stats:
            self.assertEqual(card.value, 0)

    # ========== get_widgets() 测试 ==========
    
    def test_get_widgets_with_data(self):
        """测试获取Widget（有数据）"""
        # Mock ShortageReport data
        mock_report1 = MagicMock()
        mock_report1.id = 1
        mock_report1.material_name = "物料A"
        mock_report1.project_id = 101
        mock_report1.status = "REPORTED"
        mock_report1.urgent_level = "HIGH"
        mock_report1.report_time = datetime(2026, 2, 20, 10, 0, 0)
        mock_report1.report_no = "SR-20260220-001"
        mock_report1.shortage_qty = Decimal("100.50")
        
        mock_report2 = MagicMock()
        mock_report2.id = 2
        mock_report2.material_name = "物料B"
        mock_report2.project_id = 102
        mock_report2.status = "HANDLING"
        mock_report2.urgent_level = "URGENT"
        mock_report2.report_time = datetime(2026, 2, 19, 14, 30, 0)
        mock_report2.report_no = "SR-20260219-002"
        mock_report2.shortage_qty = Decimal("50.25")
        
        # Mock Project data
        mock_project1 = MagicMock()
        mock_project1.id = 101
        mock_project1.project_name = "项目甲"
        
        mock_project2 = MagicMock()
        mock_project2.id = 102
        mock_project2.project_name = "项目乙"
        
        # Mock query chains
        mock_report_query = MagicMock()
        mock_ordered = MagicMock()
        mock_limited = MagicMock()
        mock_limited.all.return_value = [mock_report1, mock_report2]
        mock_ordered.limit.return_value = mock_limited
        mock_report_query.order_by.return_value = mock_ordered
        
        # Mock MaterialSubstitution query
        mock_sub_query = MagicMock()
        mock_sub_query.count.return_value = 10
        mock_sub_pending = MagicMock()
        mock_sub_pending.count.return_value = 3
        mock_sub_query.filter.return_value = mock_sub_pending
        
        # Mock MaterialTransfer query
        mock_transfer_query = MagicMock()
        mock_transfer_query.count.return_value = 15
        mock_transfer_pending = MagicMock()
        mock_transfer_pending.count.return_value = 5
        mock_transfer_query.filter.return_value = mock_transfer_pending
        
        # Setup db.query behavior
        def query_side_effect(model):
            model_name = model.__name__ if hasattr(model, '__name__') else str(model)
            if "ShortageReport" in model_name:
                return mock_report_query
            elif "Project" in model_name:
                # Return different projects based on filter
                return MagicMock()
            elif "MaterialSubstitution" in model_name:
                return mock_sub_query
            elif "MaterialTransfer" in model_name:
                return mock_transfer_query
            return MagicMock()
        
        self.mock_db.query.side_effect = query_side_effect
        
        # Mock Project.filter().first() calls
        def project_filter_side_effect(*args):
            filter_expr = str(args[0]) if args else ""
            mock_filtered = MagicMock()
            if "101" in filter_expr:
                mock_filtered.first.return_value = mock_project1
            elif "102" in filter_expr:
                mock_filtered.first.return_value = mock_project2
            else:
                mock_filtered.first.return_value = None
            return mock_filtered
        
        # Patch Project query specifically
        with patch.object(self.mock_db, 'query') as mock_query_method:
            def enhanced_query_side_effect(model):
                model_name = model.__name__ if hasattr(model, '__name__') else str(model)
                if "Project" in model_name:
                    mock_proj_query = MagicMock()
                    mock_proj_query.filter.side_effect = project_filter_side_effect
                    return mock_proj_query
                elif "ShortageReport" in model_name:
                    return mock_report_query
                elif "MaterialSubstitution" in model_name:
                    return mock_sub_query
                elif "MaterialTransfer" in model_name:
                    return mock_transfer_query
                return MagicMock()
            
            mock_query_method.side_effect = enhanced_query_side_effect
            
            # 执行
            widgets = self.adapter.get_widgets()
        
        # 验证
        self.assertIsInstance(widgets, list)
        self.assertEqual(len(widgets), 2)
        
        # 验证第一个widget（最近缺料上报）
        recent_widget = widgets[0]
        self.assertEqual(recent_widget.widget_id, "recent_reports")
        self.assertEqual(recent_widget.widget_type, "list")
        self.assertEqual(recent_widget.title, "最近缺料上报")
        self.assertEqual(recent_widget.order, 1)
        self.assertEqual(recent_widget.span, 16)
        
        self.assertIsInstance(recent_widget.data, list)
        self.assertEqual(len(recent_widget.data), 2)
        
        # 验证列表项
        item1 = recent_widget.data[0]
        self.assertIsInstance(item1, DashboardListItem)
        self.assertEqual(item1.id, 1)
        self.assertEqual(item1.title, "物料A")
        self.assertEqual(item1.subtitle, "项目甲")
        self.assertEqual(item1.status, "REPORTED")
        self.assertEqual(item1.priority, "HIGH")
        self.assertEqual(item1.extra["report_no"], "SR-20260220-001")
        self.assertEqual(item1.extra["shortage_qty"], 100.50)
        
        # 验证第二个widget（操作统计）
        stats_widget = widgets[1]
        self.assertEqual(stats_widget.widget_id, "operation_stats")
        self.assertEqual(stats_widget.widget_type, "stats")
        self.assertEqual(stats_widget.title, "处理操作统计")
        self.assertEqual(stats_widget.order, 2)
        self.assertEqual(stats_widget.span, 8)
        
        self.assertIsInstance(stats_widget.data, dict)
        self.assertEqual(stats_widget.data["substitutions"]["total"], 10)
        self.assertEqual(stats_widget.data["substitutions"]["pending"], 3)
        self.assertEqual(stats_widget.data["transfers"]["total"], 15)
        self.assertEqual(stats_widget.data["transfers"]["pending"], 5)

    def test_get_widgets_empty_reports(self):
        """测试获取Widget（无缺料上报）"""
        # Mock empty reports
        mock_report_query = MagicMock()
        mock_ordered = MagicMock()
        mock_limited = MagicMock()
        mock_limited.all.return_value = []
        mock_ordered.limit.return_value = mock_limited
        mock_report_query.order_by.return_value = mock_ordered
        
        # Mock empty stats
        mock_sub_query = MagicMock()
        mock_sub_query.count.return_value = 0
        mock_sub_query.filter.return_value.count.return_value = 0
        
        mock_transfer_query = MagicMock()
        mock_transfer_query.count.return_value = 0
        mock_transfer_query.filter.return_value.count.return_value = 0
        
        def query_side_effect(model):
            model_name = model.__name__ if hasattr(model, '__name__') else str(model)
            if "ShortageReport" in model_name:
                return mock_report_query
            elif "MaterialSubstitution" in model_name:
                return mock_sub_query
            elif "MaterialTransfer" in model_name:
                return mock_transfer_query
            return MagicMock()
        
        self.mock_db.query.side_effect = query_side_effect
        
        # 执行
        widgets = self.adapter.get_widgets()
        
        # 验证
        self.assertEqual(len(widgets), 2)
        self.assertEqual(len(widgets[0].data), 0)
        self.assertEqual(widgets[1].data["substitutions"]["total"], 0)

    def test_get_widgets_project_not_found(self):
        """测试获取Widget（项目不存在）"""
        # Mock report without project
        mock_report = MagicMock()
        mock_report.id = 1
        mock_report.material_name = "物料X"
        mock_report.project_id = 999
        mock_report.status = "REPORTED"
        mock_report.urgent_level = "LOW"
        mock_report.report_time = datetime(2026, 2, 21, 10, 0, 0)
        mock_report.report_no = "SR-20260221-999"
        mock_report.shortage_qty = Decimal("10.0")
        
        mock_report_query = MagicMock()
        mock_ordered = MagicMock()
        mock_limited = MagicMock()
        mock_limited.all.return_value = [mock_report]
        mock_ordered.limit.return_value = mock_limited
        mock_report_query.order_by.return_value = mock_ordered
        
        # Mock other queries
        mock_sub_query = MagicMock()
        mock_sub_query.count.return_value = 0
        mock_sub_query.filter.return_value.count.return_value = 0
        
        mock_transfer_query = MagicMock()
        mock_transfer_query.count.return_value = 0
        mock_transfer_query.filter.return_value.count.return_value = 0
        
        with patch.object(self.mock_db, 'query') as mock_query_method:
            def enhanced_query_side_effect(model):
                model_name = model.__name__ if hasattr(model, '__name__') else str(model)
                if "Project" in model_name:
                    mock_proj_query = MagicMock()
                    mock_filtered = MagicMock()
                    mock_filtered.first.return_value = None  # Project not found
                    mock_proj_query.filter.return_value = mock_filtered
                    return mock_proj_query
                elif "ShortageReport" in model_name:
                    return mock_report_query
                elif "MaterialSubstitution" in model_name:
                    return mock_sub_query
                elif "MaterialTransfer" in model_name:
                    return mock_transfer_query
                return MagicMock()
            
            mock_query_method.side_effect = enhanced_query_side_effect
            
            # 执行
            widgets = self.adapter.get_widgets()
        
        # 验证
        self.assertEqual(len(widgets), 2)
        self.assertEqual(len(widgets[0].data), 1)
        
        item = widgets[0].data[0]
        self.assertEqual(item.subtitle, None)  # No project name

    def test_get_widgets_material_name_none(self):
        """测试获取Widget（物料名称为空）"""
        # Mock report with None material_name
        mock_report = MagicMock()
        mock_report.id = 1
        mock_report.material_name = None
        mock_report.project_id = 101
        mock_report.status = "REPORTED"
        mock_report.urgent_level = "LOW"
        mock_report.report_time = datetime(2026, 2, 21, 10, 0, 0)
        mock_report.report_no = "SR-20260221-001"
        mock_report.shortage_qty = Decimal("10.0")
        
        mock_report_query = MagicMock()
        mock_ordered = MagicMock()
        mock_limited = MagicMock()
        mock_limited.all.return_value = [mock_report]
        mock_ordered.limit.return_value = mock_limited
        mock_report_query.order_by.return_value = mock_ordered
        
        # Mock project
        mock_project = MagicMock()
        mock_project.project_name = "测试项目"
        
        # Mock other queries
        mock_sub_query = MagicMock()
        mock_sub_query.count.return_value = 0
        mock_sub_query.filter.return_value.count.return_value = 0
        
        mock_transfer_query = MagicMock()
        mock_transfer_query.count.return_value = 0
        mock_transfer_query.filter.return_value.count.return_value = 0
        
        with patch.object(self.mock_db, 'query') as mock_query_method:
            def enhanced_query_side_effect(model):
                model_name = model.__name__ if hasattr(model, '__name__') else str(model)
                if "Project" in model_name:
                    mock_proj_query = MagicMock()
                    mock_filtered = MagicMock()
                    mock_filtered.first.return_value = mock_project
                    mock_proj_query.filter.return_value = mock_filtered
                    return mock_proj_query
                elif "ShortageReport" in model_name:
                    return mock_report_query
                elif "MaterialSubstitution" in model_name:
                    return mock_sub_query
                elif "MaterialTransfer" in model_name:
                    return mock_transfer_query
                return MagicMock()
            
            mock_query_method.side_effect = enhanced_query_side_effect
            
            # 执行
            widgets = self.adapter.get_widgets()
        
        # 验证
        self.assertEqual(len(widgets[0].data), 1)
        item = widgets[0].data[0]
        self.assertEqual(item.title, "未知物料")

    # ========== get_detailed_data() 测试 ==========
    
    def test_get_detailed_data(self):
        """测试获取详细数据"""
        # Mock queries for get_stats
        mock_query = MagicMock()
        mock_query.count.return_value = 100
        mock_query.filter.return_value = mock_query
        self.mock_db.query.return_value = mock_query
        
        # 执行
        result = self.adapter.get_detailed_data()
        
        # 验证
        self.assertIsInstance(result, DetailedDashboardResponse)
        self.assertEqual(result.module, "shortage")
        self.assertEqual(result.module_name, "缺料管理")
        self.assertIsInstance(result.summary, dict)
        self.assertIsInstance(result.details, dict)
        self.assertIsInstance(result.generated_at, datetime)
        
        # 验证summary包含所有stats的key
        self.assertIn("total_reports", result.summary)
        self.assertIn("urgent_reports", result.summary)
        self.assertIn("unresolved_alerts", result.summary)
        self.assertIn("pending_arrivals", result.summary)
        self.assertIn("delayed_arrivals", result.summary)
        self.assertIn("resolved_reports", result.summary)
        
        # 验证details结构
        self.assertIn("by_status", result.details)
        self.assertIn("by_urgent", result.details)
        
        # 验证by_status包含所有状态
        by_status = result.details["by_status"]
        self.assertIn("REPORTED", by_status)
        self.assertIn("CONFIRMED", by_status)
        self.assertIn("HANDLING", by_status)
        self.assertIn("RESOLVED", by_status)
        
        # 验证by_urgent包含所有紧急程度
        by_urgent = result.details["by_urgent"]
        self.assertIn("LOW", by_urgent)
        self.assertIn("MEDIUM", by_urgent)
        self.assertIn("HIGH", by_urgent)
        self.assertIn("URGENT", by_urgent)
        self.assertIn("CRITICAL", by_urgent)

    def test_get_detailed_data_with_real_counts(self):
        """测试获取详细数据（真实计数）"""
        # Mock different counts for different statuses
        status_counts = {
            "REPORTED": 10,
            "CONFIRMED": 20,
            "HANDLING": 15,
            "RESOLVED": 5,
        }
        
        urgent_counts = {
            "LOW": 5,
            "MEDIUM": 10,
            "HIGH": 15,
            "URGENT": 8,
            "CRITICAL": 2,
        }
        
        def create_mock_filter(count_value):
            mock = MagicMock()
            mock.count.return_value = count_value
            return mock
        
        # Setup complex filter behavior
        def query_filter_side_effect(*args):
            if not args:
                mock = MagicMock()
                mock.count.return_value = 40  # Total
                return mock
            
            filter_expr = str(args[0])
            
            # Check status filters
            for status, count in status_counts.items():
                if status in filter_expr:
                    return create_mock_filter(count)
            
            # Check urgent level filters
            for level, count in urgent_counts.items():
                if level in filter_expr:
                    return create_mock_filter(count)
            
            # Default
            mock = MagicMock()
            mock.count.return_value = 0
            return mock
        
        mock_query = MagicMock()
        mock_query.count.return_value = 40
        mock_query.filter.side_effect = query_filter_side_effect
        
        self.mock_db.query.return_value = mock_query
        
        # 执行
        result = self.adapter.get_detailed_data()
        
        # 验证计数
        for status, expected_count in status_counts.items():
            self.assertEqual(result.details["by_status"][status], expected_count)
        
        for level, expected_count in urgent_counts.items():
            self.assertEqual(result.details["by_urgent"][level], expected_count)

    # ========== 边界情况测试 ==========
    
    def test_shortage_qty_decimal_to_float_conversion(self):
        """测试shortage_qty从Decimal转float"""
        # Mock report with Decimal shortage_qty
        mock_report = MagicMock()
        mock_report.id = 1
        mock_report.material_name = "物料测试"
        mock_report.project_id = 1
        mock_report.status = "REPORTED"
        mock_report.urgent_level = "LOW"
        mock_report.report_time = datetime.now()
        mock_report.report_no = "SR-TEST-001"
        mock_report.shortage_qty = Decimal("123.456")
        
        mock_report_query = MagicMock()
        mock_ordered = MagicMock()
        mock_limited = MagicMock()
        mock_limited.all.return_value = [mock_report]
        mock_ordered.limit.return_value = mock_limited
        mock_report_query.order_by.return_value = mock_ordered
        
        mock_project = MagicMock()
        mock_project.project_name = "测试"
        
        mock_sub_query = MagicMock()
        mock_sub_query.count.return_value = 0
        mock_sub_query.filter.return_value.count.return_value = 0
        
        mock_transfer_query = MagicMock()
        mock_transfer_query.count.return_value = 0
        mock_transfer_query.filter.return_value.count.return_value = 0
        
        with patch.object(self.mock_db, 'query') as mock_query_method:
            def enhanced_query_side_effect(model):
                model_name = model.__name__ if hasattr(model, '__name__') else str(model)
                if "Project" in model_name:
                    mock_proj_query = MagicMock()
                    mock_filtered = MagicMock()
                    mock_filtered.first.return_value = mock_project
                    mock_proj_query.filter.return_value = mock_filtered
                    return mock_proj_query
                elif "ShortageReport" in model_name:
                    return mock_report_query
                elif "MaterialSubstitution" in model_name:
                    return mock_sub_query
                elif "MaterialTransfer" in model_name:
                    return mock_transfer_query
                return MagicMock()
            
            mock_query_method.side_effect = enhanced_query_side_effect
            
            widgets = self.adapter.get_widgets()
        
        # 验证Decimal正确转换为float
        item = widgets[0].data[0]
        self.assertEqual(item.extra["shortage_qty"], 123.456)
        self.assertIsInstance(item.extra["shortage_qty"], float)

    def test_multiple_reports_ordering(self):
        """测试多个报告的排序"""
        # Create reports with different timestamps
        reports = []
        for i in range(3):
            mock_report = MagicMock()
            mock_report.id = i + 1
            mock_report.material_name = f"物料{i+1}"
            mock_report.project_id = 1
            mock_report.status = "REPORTED"
            mock_report.urgent_level = "LOW"
            mock_report.report_time = datetime(2026, 2, 20 + i, 10, 0, 0)
            mock_report.report_no = f"SR-2026022{i}-00{i+1}"
            mock_report.shortage_qty = Decimal("10.0")
            reports.append(mock_report)
        
        mock_report_query = MagicMock()
        mock_ordered = MagicMock()
        mock_limited = MagicMock()
        mock_limited.all.return_value = reports
        mock_ordered.limit.return_value = mock_limited
        mock_report_query.order_by.return_value = mock_ordered
        
        mock_project = MagicMock()
        mock_project.project_name = "项目"
        
        mock_sub_query = MagicMock()
        mock_sub_query.count.return_value = 0
        mock_sub_query.filter.return_value.count.return_value = 0
        
        mock_transfer_query = MagicMock()
        mock_transfer_query.count.return_value = 0
        mock_transfer_query.filter.return_value.count.return_value = 0
        
        with patch.object(self.mock_db, 'query') as mock_query_method:
            def enhanced_query_side_effect(model):
                model_name = model.__name__ if hasattr(model, '__name__') else str(model)
                if "Project" in model_name:
                    mock_proj_query = MagicMock()
                    mock_filtered = MagicMock()
                    mock_filtered.first.return_value = mock_project
                    mock_proj_query.filter.return_value = mock_filtered
                    return mock_proj_query
                elif "ShortageReport" in model_name:
                    return mock_report_query
                elif "MaterialSubstitution" in model_name:
                    return mock_sub_query
                elif "MaterialTransfer" in model_name:
                    return mock_transfer_query
                return MagicMock()
            
            mock_query_method.side_effect = enhanced_query_side_effect
            
            widgets = self.adapter.get_widgets()
        
        # 验证返回了3条记录
        self.assertEqual(len(widgets[0].data), 3)
        
        # 验证order_by被调用
        self.assertTrue(mock_report_query.order_by.called)


if __name__ == "__main__":
    unittest.main()

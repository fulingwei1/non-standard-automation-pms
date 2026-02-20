# -*- coding: utf-8 -*-
"""
项目统计服务增强测试
覆盖 project_statistics_service.py 的所有核心方法
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.services.project_statistics_service import (
    CostStatisticsService,
    ProjectStatisticsServiceBase,
    TimesheetStatisticsService,
    WorkLogStatisticsService,
    build_project_statistics,
    calculate_customer_statistics,
    calculate_health_statistics,
    calculate_monthly_statistics,
    calculate_pm_statistics,
    calculate_stage_statistics,
    calculate_status_statistics,
)


class TestCalculateStatusStatistics(unittest.TestCase):
    """测试状态统计函数"""

    def test_empty_query(self):
        """测试空查询"""
        query = MagicMock()
        query.all.return_value = []
        result = calculate_status_statistics(query)
        self.assertEqual(result, {})

    def test_single_status(self):
        """测试单个状态"""
        project = MagicMock()
        project.status = "ACTIVE"
        query = MagicMock()
        query.all.return_value = [project]
        result = calculate_status_statistics(query)
        self.assertEqual(result, {"ACTIVE": 1})

    def test_multiple_statuses(self):
        """测试多个状态"""
        p1 = MagicMock(status="ACTIVE")
        p2 = MagicMock(status="ACTIVE")
        p3 = MagicMock(status="CLOSED")
        query = MagicMock()
        query.all.return_value = [p1, p2, p3]
        result = calculate_status_statistics(query)
        self.assertEqual(result, {"ACTIVE": 2, "CLOSED": 1})

    def test_none_status(self):
        """测试None状态"""
        p1 = MagicMock(status=None)
        p2 = MagicMock(status="ACTIVE")
        query = MagicMock()
        query.all.return_value = [p1, p2]
        result = calculate_status_statistics(query)
        self.assertEqual(result, {"ACTIVE": 1})


class TestCalculateStageStatistics(unittest.TestCase):
    """测试阶段统计函数"""

    def test_empty_query(self):
        """测试空查询"""
        query = MagicMock()
        query.all.return_value = []
        result = calculate_stage_statistics(query)
        self.assertEqual(result, {})

    def test_multiple_stages(self):
        """测试多个阶段"""
        p1 = MagicMock(stage="PLANNING")
        p2 = MagicMock(stage="EXECUTION")
        p3 = MagicMock(stage="PLANNING")
        query = MagicMock()
        query.all.return_value = [p1, p2, p3]
        result = calculate_stage_statistics(query)
        self.assertEqual(result, {"PLANNING": 2, "EXECUTION": 1})

    def test_none_stage(self):
        """测试None阶段"""
        p1 = MagicMock(stage=None)
        query = MagicMock()
        query.all.return_value = [p1]
        result = calculate_stage_statistics(query)
        self.assertEqual(result, {})


class TestCalculateHealthStatistics(unittest.TestCase):
    """测试健康度统计函数"""

    def test_empty_query(self):
        """测试空查询"""
        query = MagicMock()
        query.all.return_value = []
        result = calculate_health_statistics(query)
        self.assertEqual(result, {})

    def test_multiple_health_levels(self):
        """测试多个健康度"""
        p1 = MagicMock(health="GREEN")
        p2 = MagicMock(health="YELLOW")
        p3 = MagicMock(health="GREEN")
        query = MagicMock()
        query.all.return_value = [p1, p2, p3]
        result = calculate_health_statistics(query)
        self.assertEqual(result, {"GREEN": 2, "YELLOW": 1})


class TestCalculatePmStatistics(unittest.TestCase):
    """测试项目经理统计函数"""

    def test_empty_query(self):
        """测试空查询"""
        query = MagicMock()
        query.all.return_value = []
        result = calculate_pm_statistics(query)
        self.assertEqual(result, [])

    def test_single_pm(self):
        """测试单个PM"""
        p1 = MagicMock(pm_id=1, pm_name="张三")
        query = MagicMock()
        query.all.return_value = [p1]
        result = calculate_pm_statistics(query)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["pm_id"], 1)
        self.assertEqual(result[0]["pm_name"], "张三")
        self.assertEqual(result[0]["count"], 1)

    def test_multiple_pms(self):
        """测试多个PM"""
        p1 = MagicMock(pm_id=1, pm_name="张三")
        p2 = MagicMock(pm_id=2, pm_name="李四")
        p3 = MagicMock(pm_id=1, pm_name="张三")
        query = MagicMock()
        query.all.return_value = [p1, p2, p3]
        result = calculate_pm_statistics(query)
        self.assertEqual(len(result), 2)
        pm_dict = {r["pm_id"]: r for r in result}
        self.assertEqual(pm_dict[1]["count"], 2)
        self.assertEqual(pm_dict[2]["count"], 1)

    def test_none_pm_name(self):
        """测试PM名字为None"""
        p1 = MagicMock(pm_id=1, pm_name=None)
        query = MagicMock()
        query.all.return_value = [p1]
        result = calculate_pm_statistics(query)
        self.assertEqual(result[0]["pm_name"], "未知")

    def test_none_pm_id(self):
        """测试PM ID为None"""
        p1 = MagicMock(pm_id=None, pm_name="张三")
        query = MagicMock()
        query.all.return_value = [p1]
        result = calculate_pm_statistics(query)
        self.assertEqual(result, [])


class TestCalculateCustomerStatistics(unittest.TestCase):
    """测试客户统计函数"""

    def test_empty_query(self):
        """测试空查询"""
        query = MagicMock()
        query.all.return_value = []
        result = calculate_customer_statistics(query)
        self.assertEqual(result, [])

    def test_single_customer(self):
        """测试单个客户"""
        p1 = MagicMock(customer_id=1, customer_name="客户A", contract_amount=100000)
        query = MagicMock()
        query.all.return_value = [p1]
        result = calculate_customer_statistics(query)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["customer_id"], 1)
        self.assertEqual(result[0]["customer_name"], "客户A")
        self.assertEqual(result[0]["count"], 1)
        self.assertEqual(result[0]["total_amount"], 100000.0)

    def test_multiple_customers(self):
        """测试多个客户"""
        p1 = MagicMock(customer_id=1, customer_name="客户A", contract_amount=100000)
        p2 = MagicMock(customer_id=2, customer_name="客户B", contract_amount=200000)
        p3 = MagicMock(customer_id=1, customer_name="客户A", contract_amount=50000)
        query = MagicMock()
        query.all.return_value = [p1, p2, p3]
        result = calculate_customer_statistics(query)
        self.assertEqual(len(result), 2)
        cust_dict = {r["customer_id"]: r for r in result}
        self.assertEqual(cust_dict[1]["count"], 2)
        self.assertEqual(cust_dict[1]["total_amount"], 150000.0)

    def test_none_customer_id(self):
        """测试客户ID为None"""
        p1 = MagicMock(customer_id=None, customer_name=None, contract_amount=100000)
        query = MagicMock()
        query.all.return_value = [p1]
        result = calculate_customer_statistics(query)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["customer_id"], 0)
        self.assertEqual(result[0]["customer_name"], "未知客户")

    def test_none_contract_amount(self):
        """测试合同金额为None"""
        p1 = MagicMock(customer_id=1, customer_name="客户A", contract_amount=None)
        query = MagicMock()
        query.all.return_value = [p1]
        result = calculate_customer_statistics(query)
        self.assertEqual(result[0]["total_amount"], 0.0)


class TestCalculateMonthlyStatistics(unittest.TestCase):
    """测试月度统计函数"""

    def test_empty_query(self):
        """测试空查询"""
        query = MagicMock()
        query.all.return_value = []
        result = calculate_monthly_statistics(query)
        self.assertEqual(result, [])

    def test_single_month(self):
        """测试单个月份"""
        p1 = MagicMock(
            created_at=datetime(2024, 1, 15, 10, 0, 0), contract_amount=100000
        )
        query = MagicMock()
        query.all.return_value = [p1]
        result = calculate_monthly_statistics(query)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["year"], 2024)
        self.assertEqual(result[0]["month"], 1)
        self.assertEqual(result[0]["month_label"], "2024-01")
        self.assertEqual(result[0]["count"], 1)
        self.assertEqual(result[0]["total_amount"], 100000.0)

    def test_multiple_months_sorted(self):
        """测试多个月份排序"""
        p1 = MagicMock(
            created_at=datetime(2024, 3, 15, 10, 0, 0), contract_amount=100000
        )
        p2 = MagicMock(
            created_at=datetime(2024, 1, 20, 10, 0, 0), contract_amount=200000
        )
        p3 = MagicMock(
            created_at=datetime(2024, 2, 10, 10, 0, 0), contract_amount=150000
        )
        query = MagicMock()
        query.all.return_value = [p1, p2, p3]
        result = calculate_monthly_statistics(query)
        self.assertEqual(len(result), 3)
        # 应该按时间排序
        self.assertEqual(result[0]["month"], 1)
        self.assertEqual(result[1]["month"], 2)
        self.assertEqual(result[2]["month"], 3)

    def test_none_created_at(self):
        """测试创建时间为None"""
        p1 = MagicMock(created_at=None, contract_amount=100000)
        query = MagicMock()
        query.all.return_value = [p1]
        result = calculate_monthly_statistics(query)
        self.assertEqual(result, [])

    def test_date_filter(self):
        """测试日期过滤"""
        p1 = MagicMock(
            created_at=datetime(2024, 6, 15, 10, 0, 0), contract_amount=100000
        )
        query = MagicMock()
        query.all.return_value = [p1]
        query.filter.return_value = query
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        result = calculate_monthly_statistics(query, start_date, end_date)
        
        # 应该有结果
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["month"], 6)


class TestBuildProjectStatistics(unittest.TestCase):
    """测试综合统计构建函数"""

    def test_basic_statistics(self):
        """测试基础统计"""
        p1 = MagicMock(
            status="ACTIVE",
            stage="PLANNING",
            health="GREEN",
            progress_pct=50,
            pm_id=1,
            pm_name="张三",
            customer_id=1,
            customer_name="客户A",
            contract_amount=100000,
            created_at=datetime(2024, 1, 15),
        )
        query = MagicMock()
        query.all.return_value = [p1]
        
        db = MagicMock()
        result = build_project_statistics(db, query)
        
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["average_progress"], 50)
        self.assertIn("by_status", result)
        self.assertIn("by_stage", result)
        self.assertIn("by_health", result)
        self.assertIn("by_pm", result)

    def test_empty_projects(self):
        """测试空项目列表"""
        query = MagicMock()
        query.all.return_value = []
        
        db = MagicMock()
        result = build_project_statistics(db, query)
        
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["average_progress"], 0)

    def test_group_by_customer(self):
        """测试按客户分组"""
        p1 = MagicMock(
            status="ACTIVE",
            stage="PLANNING",
            health="GREEN",
            progress_pct=50,
            pm_id=1,
            pm_name="张三",
            customer_id=1,
            customer_name="客户A",
            contract_amount=100000,
        )
        query = MagicMock()
        query.all.return_value = [p1]
        
        db = MagicMock()
        result = build_project_statistics(db, query, group_by="customer")
        
        self.assertIn("by_customer", result)

    def test_group_by_month(self):
        """测试按月份分组"""
        p1 = MagicMock(
            status="ACTIVE",
            stage="PLANNING",
            health="GREEN",
            progress_pct=50,
            pm_id=1,
            pm_name="张三",
            created_at=datetime(2024, 1, 15),
            contract_amount=100000,
        )
        query = MagicMock()
        query.all.return_value = [p1]
        
        db = MagicMock()
        result = build_project_statistics(
            db, query, group_by="month", start_date=date(2024, 1, 1)
        )
        
        self.assertIn("by_month", result)


class TestProjectStatisticsServiceBase(unittest.TestCase):
    """测试项目统计服务基类"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        
        # 创建一个具体实现类用于测试
        class TestService(ProjectStatisticsServiceBase):
            def get_model(self):
                return MagicMock()
            
            def get_project_id_field(self):
                return "project_id"
            
            def get_summary(self, project_id, start_date=None, end_date=None):
                return {}
        
        self.service = TestService(self.db)

    def test_get_project_success(self):
        """测试获取项目成功"""
        mock_project = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = (
            mock_project
        )
        
        result = self.service.get_project(1)
        
        self.assertEqual(result, mock_project)

    def test_get_project_not_found(self):
        """测试项目不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.get_project(999)
        
        self.assertIn("项目不存在", str(context.exception))

    def test_build_base_query(self):
        """测试构建基础查询"""
        mock_model = MagicMock()
        self.service.get_model = MagicMock(return_value=mock_model)
        
        result = self.service.build_base_query(1)
        
        self.db.query.assert_called_once_with(mock_model)

    def test_apply_date_filter_with_start_date(self):
        """测试应用开始日期过滤"""
        query = MagicMock()
        mock_model = MagicMock()
        # Mock 一个支持比较的属性
        mock_date_attr = MagicMock()
        mock_date_attr.__ge__ = MagicMock(return_value=True)
        mock_model.created_at = mock_date_attr
        self.service.get_model = MagicMock(return_value=mock_model)
        
        start_date = date(2024, 1, 1)
        result = self.service.apply_date_filter(query, start_date=start_date)
        
        query.filter.assert_called_once()

    def test_apply_date_filter_with_end_date(self):
        """测试应用结束日期过滤"""
        query = MagicMock()
        mock_model = MagicMock()
        # Mock 一个支持比较的属性
        mock_date_attr = MagicMock()
        mock_date_attr.__le__ = MagicMock(return_value=True)
        mock_model.created_at = mock_date_attr
        self.service.get_model = MagicMock(return_value=mock_model)
        
        end_date = date(2024, 12, 31)
        result = self.service.apply_date_filter(query, end_date=end_date)
        
        query.filter.assert_called_once()

    def test_group_by_field_with_count(self):
        """测试按字段分组统计（计数）"""
        query = MagicMock()
        query.with_entities.return_value.group_by.return_value.all.return_value = [
            ("TYPE_A", 5),
            ("TYPE_B", 3),
        ]
        
        mock_model = MagicMock()
        self.service.get_model = MagicMock(return_value=mock_model)
        
        result = self.service.group_by_field(query, "test_field")
        
        self.assertEqual(result, {"TYPE_A": 5, "TYPE_B": 3})

    def test_group_by_field_with_sum(self):
        """测试按字段分组统计（求和）"""
        from sqlalchemy import func
        
        query = MagicMock()
        query.with_entities.return_value.group_by.return_value.all.return_value = [
            ("TYPE_A", Decimal("1000.50")),
            ("TYPE_B", Decimal("2000.75")),
        ]
        
        mock_model = MagicMock()
        self.service.get_model = MagicMock(return_value=mock_model)
        
        result = self.service.group_by_field(
            query, "test_field", func.sum, "amount"
        )
        
        self.assertEqual(result, {"TYPE_A": 1000.50, "TYPE_B": 2000.75})

    def test_group_by_field_not_exist(self):
        """测试字段不存在"""
        query = MagicMock()
        mock_model = MagicMock()
        mock_model.test_field = None
        delattr(mock_model, "test_field")
        self.service.get_model = MagicMock(return_value=mock_model)
        
        result = self.service.group_by_field(query, "nonexistent_field")
        
        self.assertEqual(result, {})

    def test_calculate_total(self):
        """测试计算总和"""
        query = MagicMock()
        query.with_entities.return_value.scalar.return_value = Decimal("5000.00")
        
        mock_model = MagicMock()
        self.service.get_model = MagicMock(return_value=mock_model)
        
        result = self.service.calculate_total(query, "amount")
        
        self.assertEqual(result, 5000.0)

    def test_calculate_total_none(self):
        """测试计算总和返回None"""
        query = MagicMock()
        query.with_entities.return_value.scalar.return_value = None
        
        mock_model = MagicMock()
        self.service.get_model = MagicMock(return_value=mock_model)
        
        result = self.service.calculate_total(query, "amount")
        
        self.assertEqual(result, 0.0)

    def test_calculate_avg(self):
        """测试计算平均值"""
        query = MagicMock()
        query.with_entities.return_value.scalar.return_value = Decimal("75.5")
        
        mock_model = MagicMock()
        self.service.get_model = MagicMock(return_value=mock_model)
        
        result = self.service.calculate_avg(query, "score")
        
        self.assertEqual(result, 75.5)

    def test_calculate_avg_none(self):
        """测试计算平均值返回None"""
        query = MagicMock()
        query.with_entities.return_value.scalar.return_value = None
        
        mock_model = MagicMock()
        self.service.get_model = MagicMock(return_value=mock_model)
        
        result = self.service.calculate_avg(query, "score")
        
        self.assertEqual(result, 0.0)

    def test_count_distinct(self):
        """测试计算不重复数量"""
        query = MagicMock()
        query.with_entities.return_value.scalar.return_value = 10
        
        mock_model = MagicMock()
        self.service.get_model = MagicMock(return_value=mock_model)
        
        result = self.service.count_distinct(query, "user_id")
        
        self.assertEqual(result, 10)

    def test_count_distinct_none(self):
        """测试计算不重复数量返回None"""
        query = MagicMock()
        query.with_entities.return_value.scalar.return_value = None
        
        mock_model = MagicMock()
        self.service.get_model = MagicMock(return_value=mock_model)
        
        result = self.service.count_distinct(query, "user_id")
        
        self.assertEqual(result, 0)


class TestCostStatisticsService(unittest.TestCase):
    """测试成本统计服务"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = CostStatisticsService(self.db)

    def test_get_model(self):
        """测试获取模型"""
        from app.models.project import ProjectCost
        result = self.service.get_model()
        self.assertEqual(result, ProjectCost)

    def test_get_project_id_field(self):
        """测试获取项目ID字段"""
        result = self.service.get_project_id_field()
        self.assertEqual(result, "project_id")

    def test_get_summary_basic(self):
        """测试获取基本汇总"""
        # Mock项目
        mock_project = MagicMock()
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = Decimal("100000")
        
        # 创建一个复杂的query mock链
        project_query = MagicMock()
        project_query.filter.return_value.first.return_value = mock_project
        
        cost_query = MagicMock()
        cost_query.filter.return_value = cost_query
        
        def query_side_effect(model):
            from app.models.project import Project
            if model == Project:
                return project_query
            else:
                return cost_query
        
        self.db.query.side_effect = query_side_effect
        
        # Mock group_by_field
        self.service.group_by_field = MagicMock(
            return_value={"人工": 30000, "设备": 20000}
        )
        self.service.calculate_total = MagicMock(return_value=50000.0)
        
        result = self.service.get_summary(1)
        
        self.assertEqual(result["project_id"], 1)
        self.assertEqual(result["project_name"], "测试项目")
        self.assertEqual(result["total_cost"], 50000.0)
        self.assertEqual(result["by_type"], {"人工": 30000, "设备": 20000})
        self.assertEqual(result["budget"], 100000.0)
        self.assertEqual(result["budget_used_pct"], 50.0)

    def test_get_summary_no_budget(self):
        """测试无预算情况"""
        mock_project = MagicMock()
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = None
        
        project_query = MagicMock()
        project_query.filter.return_value.first.return_value = mock_project
        
        cost_query = MagicMock()
        cost_query.filter.return_value = cost_query
        
        def query_side_effect(model):
            from app.models.project import Project
            if model == Project:
                return project_query
            else:
                return cost_query
        
        self.db.query.side_effect = query_side_effect
        
        self.service.group_by_field = MagicMock(return_value={})
        self.service.calculate_total = MagicMock(return_value=0.0)
        
        result = self.service.get_summary(1)
        
        self.assertIsNone(result["budget"])
        self.assertIsNone(result["budget_used_pct"])


class TestTimesheetStatisticsService(unittest.TestCase):
    """测试工时统计服务"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = TimesheetStatisticsService(self.db)

    def test_get_model(self):
        """测试获取模型"""
        from app.models.timesheet import Timesheet
        result = self.service.get_model()
        self.assertEqual(result, Timesheet)

    def test_get_project_id_field(self):
        """测试获取项目ID字段"""
        result = self.service.get_project_id_field()
        self.assertEqual(result, "project_id")

    def test_get_summary_basic(self):
        """测试获取基本汇总"""
        from app.models.project import Project
        from app.models.user import User
        from app.models.timesheet import Timesheet
        
        # Mock项目
        mock_project = MagicMock()
        mock_project.project_name = "测试项目"
        
        # Mock用户
        mock_user_obj = MagicMock()
        mock_user_obj.real_name = "张三"
        mock_user_obj.username = "zhangsan"
        
        # 配置数据库查询Mock
        def query_side_effect(model):
            if model == Project:
                return MagicMock(
                    filter=MagicMock(
                        return_value=MagicMock(first=MagicMock(return_value=mock_project))
                    )
                )
            elif model == User:
                return MagicMock(
                    filter=MagicMock(
                        return_value=MagicMock(first=MagicMock(return_value=mock_user_obj))
                    )
                )
            else:
                # Timesheet查询
                ts1 = MagicMock(
                    user_id=1,
                    hours=8.0,
                    work_date=date(2024, 1, 15),
                    overtime_type="NORMAL",
                    status="APPROVED",
                )
                ts2 = MagicMock(
                    user_id=1,
                    hours=4.0,
                    work_date=date(2024, 1, 16),
                    overtime_type="NORMAL",
                    status="APPROVED",
                )
                
                mock_query = MagicMock()
                mock_query.filter.return_value = mock_query
                mock_query.all.return_value = [ts1, ts2]
                return mock_query
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.get_summary(1)
        
        self.assertEqual(result["project_id"], 1)
        self.assertEqual(result["project_name"], "测试项目")
        self.assertEqual(result["total_hours"], 12.0)
        self.assertEqual(result["total_participants"], 1)

    def test_get_statistics_all_statuses(self):
        """测试获取所有状态的工时统计"""
        from app.models.project import Project
        
        mock_project = MagicMock()
        mock_project.project_name = "测试项目"
        
        # Mock不同状态的工时
        ts1 = MagicMock(
            hours=8.0, work_date=date(2024, 1, 15), status="APPROVED", user_id=1
        )
        ts2 = MagicMock(
            hours=4.0, work_date=date(2024, 1, 15), status="PENDING", user_id=2
        )
        ts3 = MagicMock(
            hours=2.0, work_date=date(2024, 1, 16), status="DRAFT", user_id=1
        )
        ts4 = MagicMock(
            hours=1.0, work_date=date(2024, 1, 16), status="REJECTED", user_id=3
        )
        
        project_query = MagicMock()
        project_query.filter.return_value.first.return_value = mock_project
        
        timesheet_query = MagicMock()
        timesheet_query.filter.return_value = timesheet_query
        timesheet_query.all.return_value = [ts1, ts2, ts3, ts4]
        
        def query_side_effect(model):
            if model == Project:
                return project_query
            else:
                return timesheet_query
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.get_statistics(1)
        
        self.assertEqual(result["total_hours"], 15.0)
        self.assertEqual(result["approved_hours"], 8.0)
        self.assertEqual(result["pending_hours"], 4.0)
        self.assertEqual(result["draft_hours"], 2.0)
        self.assertEqual(result["rejected_hours"], 1.0)
        self.assertEqual(result["total_participants"], 3)
        self.assertEqual(result["unique_work_days"], 2)


class TestWorkLogStatisticsService(unittest.TestCase):
    """测试工作日志统计服务"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = WorkLogStatisticsService(self.db)

    def test_get_model(self):
        """测试获取模型"""
        from app.models.work_log import WorkLog
        result = self.service.get_model()
        self.assertEqual(result, WorkLog)

    def test_get_project_id_field(self):
        """测试获取项目ID字段"""
        result = self.service.get_project_id_field()
        self.assertEqual(result, "id")

    def test_get_summary_basic(self):
        """测试获取基本汇总"""
        from app.models.project import Project
        
        # Mock项目
        mock_project = MagicMock()
        project_query = MagicMock()
        project_query.filter.return_value.first.return_value = mock_project
        
        # Mock统计结果
        mock_stats = MagicMock()
        mock_stats.log_count = 10
        mock_stats.contributor_count = 5
        
        worklog_query = MagicMock()
        worklog_query.join.return_value = worklog_query
        worklog_query.filter.return_value = worklog_query
        worklog_query.with_entities.return_value.first.return_value = mock_stats
        
        def query_side_effect(model):
            if model == Project:
                return project_query
            else:
                return worklog_query
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.get_summary(1)
        
        self.assertEqual(result["project_id"], 1)
        self.assertEqual(result["log_count"], 10)
        self.assertEqual(result["contributor_count"], 5)

    def test_get_summary_with_custom_days(self):
        """测试自定义天数的汇总"""
        from app.models.project import Project
        
        mock_project = MagicMock()
        project_query = MagicMock()
        project_query.filter.return_value.first.return_value = mock_project
        
        mock_stats = MagicMock()
        mock_stats.log_count = 15
        mock_stats.contributor_count = 8
        
        worklog_query = MagicMock()
        worklog_query.join.return_value = worklog_query
        worklog_query.filter.return_value = worklog_query
        worklog_query.with_entities.return_value.first.return_value = mock_stats
        
        def query_side_effect(model):
            if model == Project:
                return project_query
            else:
                return worklog_query
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.get_summary(1, days=60)
        
        self.assertEqual(result["period_days"], 60)
        self.assertEqual(result["log_count"], 15)


if __name__ == "__main__":
    unittest.main()

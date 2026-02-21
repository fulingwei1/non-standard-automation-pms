# -*- coding: utf-8 -*-
"""
项目统计服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（db.query, db.add等数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from datetime import date, datetime
from decimal import Decimal

from app.services.project_statistics_service import (
    calculate_status_statistics,
    calculate_stage_statistics,
    calculate_health_statistics,
    calculate_pm_statistics,
    calculate_customer_statistics,
    calculate_monthly_statistics,
    build_project_statistics,
    ProjectStatisticsServiceBase,
    CostStatisticsService,
    TimesheetStatisticsService,
    WorkLogStatisticsService,
)


class TestCalculateFunctions(unittest.TestCase):
    """测试独立的计算函数"""

    def setUp(self):
        """准备测试数据"""
        # 创建mock项目对象
        self.mock_projects = [
            self._create_mock_project(1, "项目A", "进行中", "需求分析", "健康", 1, "张三", 1, "客户A", 100000, 50),
            self._create_mock_project(2, "项目B", "进行中", "开发", "风险", 2, "李四", 2, "客户B", 200000, 30),
            self._create_mock_project(3, "项目C", "已完成", "验收", "健康", 1, "张三", 1, "客户A", 150000, 100),
            self._create_mock_project(4, "项目D", None, None, None, None, None, None, None, None, 0),
        ]

    def _create_mock_project(
        self, id, name, status, stage, health, pm_id, pm_name, 
        customer_id, customer_name, contract_amount, progress_pct
    ):
        """创建mock项目"""
        project = MagicMock()
        project.id = id
        project.project_name = name
        project.status = status
        project.stage = stage
        project.health = health
        project.pm_id = pm_id
        project.pm_name = pm_name
        project.customer_id = customer_id
        project.customer_name = customer_name
        project.contract_amount = contract_amount
        project.progress_pct = progress_pct
        project.created_at = datetime(2024, 1, 15, 10, 0, 0)
        return project

    # ========== calculate_status_statistics 测试 ==========

    def test_calculate_status_statistics(self):
        """测试状态统计"""
        mock_query = MagicMock()
        mock_query.all.return_value = self.mock_projects
        
        result = calculate_status_statistics(mock_query)
        
        self.assertEqual(result["进行中"], 2)
        self.assertEqual(result["已完成"], 1)
        self.assertNotIn(None, result)

    def test_calculate_status_statistics_empty(self):
        """测试空项目列表"""
        mock_query = MagicMock()
        mock_query.all.return_value = []
        
        result = calculate_status_statistics(mock_query)
        self.assertEqual(result, {})

    # ========== calculate_stage_statistics 测试 ==========

    def test_calculate_stage_statistics(self):
        """测试阶段统计"""
        mock_query = MagicMock()
        mock_query.all.return_value = self.mock_projects
        
        result = calculate_stage_statistics(mock_query)
        
        self.assertEqual(result["需求分析"], 1)
        self.assertEqual(result["开发"], 1)
        self.assertEqual(result["验收"], 1)

    # ========== calculate_health_statistics 测试 ==========

    def test_calculate_health_statistics(self):
        """测试健康度统计"""
        mock_query = MagicMock()
        mock_query.all.return_value = self.mock_projects
        
        result = calculate_health_statistics(mock_query)
        
        self.assertEqual(result["健康"], 2)
        self.assertEqual(result["风险"], 1)

    # ========== calculate_pm_statistics 测试 ==========

    def test_calculate_pm_statistics(self):
        """测试项目经理统计"""
        mock_query = MagicMock()
        mock_query.all.return_value = self.mock_projects
        
        result = calculate_pm_statistics(mock_query)
        
        self.assertEqual(len(result), 2)
        
        pm1 = next(pm for pm in result if pm["pm_id"] == 1)
        self.assertEqual(pm1["pm_name"], "张三")
        self.assertEqual(pm1["count"], 2)
        
        pm2 = next(pm for pm in result if pm["pm_id"] == 2)
        self.assertEqual(pm2["pm_name"], "李四")
        self.assertEqual(pm2["count"], 1)

    def test_calculate_pm_statistics_unknown_name(self):
        """测试项目经理名称为None的情况"""
        project_with_none_name = self._create_mock_project(
            5, "项目E", "进行中", "开发", "健康", 3, None, 1, "客户A", 100000, 50
        )
        
        mock_query = MagicMock()
        mock_query.all.return_value = [project_with_none_name]
        
        result = calculate_pm_statistics(mock_query)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["pm_name"], "未知")

    # ========== calculate_customer_statistics 测试 ==========

    def test_calculate_customer_statistics(self):
        """测试客户统计"""
        mock_query = MagicMock()
        mock_query.all.return_value = self.mock_projects
        
        result = calculate_customer_statistics(mock_query)
        
        self.assertEqual(len(result), 3)  # 客户A, 客户B, None->0
        
        customer_a = next(c for c in result if c["customer_id"] == 1)
        self.assertEqual(customer_a["customer_name"], "客户A")
        self.assertEqual(customer_a["count"], 2)
        self.assertEqual(customer_a["total_amount"], 250000.0)

    def test_calculate_customer_statistics_null_customer(self):
        """测试客户为None的情况"""
        result_list = calculate_customer_statistics(
            MagicMock(all=MagicMock(return_value=[self.mock_projects[3]]))
        )
        
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["customer_id"], 0)
        self.assertEqual(result_list[0]["customer_name"], "未知客户")

    # ========== calculate_monthly_statistics 测试 ==========

    def test_calculate_monthly_statistics(self):
        """测试月度统计"""
        # 创建不同月份的项目
        projects = [
            self._create_mock_project(1, "项目1", "进行中", "开发", "健康", 1, "张三", 1, "客户A", 100000, 50),
            self._create_mock_project(2, "项目2", "进行中", "开发", "健康", 1, "张三", 1, "客户A", 200000, 50),
        ]
        projects[0].created_at = datetime(2024, 1, 15)
        projects[1].created_at = datetime(2024, 2, 20)
        
        mock_query = MagicMock()
        mock_query.all.return_value = projects
        mock_query.filter.return_value = mock_query
        
        result = calculate_monthly_statistics(mock_query)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["year"], 2024)
        self.assertEqual(result[0]["month"], 1)
        self.assertEqual(result[0]["count"], 1)
        self.assertEqual(result[0]["total_amount"], 100000.0)

    def test_calculate_monthly_statistics_with_date_filter(self):
        """测试带日期过滤的月度统计"""
        projects = [
            self._create_mock_project(1, "项目1", "进行中", "开发", "健康", 1, "张三", 1, "客户A", 100000, 50),
        ]
        projects[0].created_at = datetime(2024, 1, 15)
        
        mock_query = MagicMock()
        mock_query.all.return_value = projects
        mock_query.filter.return_value = mock_query
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        result = calculate_monthly_statistics(mock_query, start_date, end_date)
        
        # 验证filter被调用
        self.assertEqual(mock_query.filter.call_count, 2)
        self.assertEqual(len(result), 1)

    def test_calculate_monthly_statistics_empty(self):
        """测试空项目列表"""
        mock_query = MagicMock()
        mock_query.all.return_value = []
        
        result = calculate_monthly_statistics(mock_query)
        self.assertEqual(result, [])

    # ========== build_project_statistics 测试 ==========

    def test_build_project_statistics_basic(self):
        """测试基本统计构建"""
        mock_query = MagicMock()
        mock_query.all.return_value = self.mock_projects
        
        mock_db = MagicMock()
        
        result = build_project_statistics(mock_db, mock_query)
        
        self.assertEqual(result["total"], 4)
        self.assertEqual(result["average_progress"], 45.0)  # (50+30+100+0)/4
        self.assertIn("by_status", result)
        self.assertIn("by_stage", result)
        self.assertIn("by_health", result)
        self.assertIn("by_pm", result)

    def test_build_project_statistics_by_customer(self):
        """测试按客户分组"""
        mock_query = MagicMock()
        mock_query.all.return_value = self.mock_projects
        
        result = build_project_statistics(MagicMock(), mock_query, group_by="customer")
        
        self.assertIn("by_customer", result)

    def test_build_project_statistics_by_month(self):
        """测试按月度分组"""
        mock_query = MagicMock()
        mock_query.all.return_value = self.mock_projects
        mock_query.filter.return_value = mock_query
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        result = build_project_statistics(
            MagicMock(), mock_query, group_by="month", start_date=start_date, end_date=end_date
        )
        
        self.assertIn("by_month", result)

    def test_build_project_statistics_empty(self):
        """测试空项目列表"""
        mock_query = MagicMock()
        mock_query.all.return_value = []
        
        result = build_project_statistics(MagicMock(), mock_query)
        
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["average_progress"], 0)


class TestProjectStatisticsServiceBase(unittest.TestCase):
    """测试ProjectStatisticsServiceBase基类"""

    def setUp(self):
        """准备mock数据库"""
        self.mock_db = MagicMock()
        
        # 创建mock模型类
        self.mock_model = MagicMock()
        self.mock_model.created_at = MagicMock()  # 添加日期字段
        
        # 创建一个具体实现类用于测试
        class TestService(ProjectStatisticsServiceBase):
            def __init__(inner_self, db):
                super().__init__(db)
                inner_self.test_model = None
            
            def get_model(inner_self):
                return inner_self.test_model
            
            def get_project_id_field(inner_self):
                return "project_id"
            
            def get_summary(inner_self, project_id, start_date=None, end_date=None):
                return {"project_id": project_id}
        
        self.service = TestService(self.mock_db)
        self.service.test_model = self.mock_model

    # ========== get_project 测试 ==========

    def test_get_project_success(self):
        """测试成功获取项目"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_project
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_project(1)
        
        self.assertEqual(result.id, 1)
        self.assertEqual(result.project_name, "测试项目")

    def test_get_project_not_found(self):
        """测试项目不存在"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        with self.assertRaises(ValueError) as context:
            self.service.get_project(999)
        
        self.assertIn("项目不存在", str(context.exception))

    # ========== build_base_query 测试 ==========

    def test_build_base_query(self):
        """测试构建基础查询"""
        mock_model = MagicMock()
        mock_model.project_id = "project_id_field"
        
        self.service.get_model = MagicMock(return_value=mock_model)
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        
        result = self.service.build_base_query(1)
        
        self.mock_db.query.assert_called_once_with(mock_model)
        mock_query.filter.assert_called_once()

    # ========== apply_date_filter 测试 ==========

    def test_apply_date_filter_with_dates(self):
        """测试应用日期过滤（集成测试，确保方法能正常调用）"""
        # 测试模型没有日期字段的情况（getattr返回None）
        mock_model_no_field = MagicMock()
        del mock_model_no_field.created_at  # 确保属性不存在
        self.service.test_model = mock_model_no_field
        
        mock_query = MagicMock()
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        result = self.service.apply_date_filter(mock_query, start_date, end_date)
        
        # 没有日期字段时，应该返回原始query
        self.assertEqual(result, mock_query)

    def test_apply_date_filter_no_dates(self):
        """测试无日期过滤"""
        mock_query = MagicMock()
        
        result = self.service.apply_date_filter(mock_query)
        
        mock_query.filter.assert_not_called()

    # ========== group_by_field 测试 ==========

    def test_group_by_field_with_count(self):
        """测试按字段分组计数"""
        mock_model = MagicMock()
        mock_model.status = "status_field"
        self.service.get_model = MagicMock(return_value=mock_model)
        
        mock_query = MagicMock()
        mock_query.with_entities.return_value.group_by.return_value.all.return_value = [
            ("进行中", 5),
            ("已完成", 3),
        ]
        
        result = self.service.group_by_field(mock_query, "status")
        
        self.assertEqual(result["进行中"], 5)
        self.assertEqual(result["已完成"], 3)

    def test_group_by_field_with_aggregate(self):
        """测试带聚合函数的分组"""
        from sqlalchemy import func
        
        mock_model = MagicMock()
        mock_model.cost_type = "cost_type_field"
        mock_model.amount = "amount_field"
        self.service.get_model = MagicMock(return_value=mock_model)
        
        mock_query = MagicMock()
        mock_query.with_entities.return_value.group_by.return_value.all.return_value = [
            ("人工", Decimal("100000")),
            ("材料", Decimal("50000")),
        ]
        
        result = self.service.group_by_field(
            mock_query, "cost_type", func.sum, "amount"
        )
        
        self.assertEqual(result["人工"], 100000.0)
        self.assertEqual(result["材料"], 50000.0)

    def test_group_by_field_invalid_field(self):
        """测试字段不存在"""
        mock_model = MagicMock()
        mock_model.configure_mock(**{"invalid_field": None})
        del mock_model.invalid_field  # 删除属性模拟不存在
        
        self.service.get_model = MagicMock(return_value=mock_model)
        
        result = self.service.group_by_field(MagicMock(), "invalid_field")
        
        self.assertEqual(result, {})

    # ========== calculate_total 测试 ==========

    def test_calculate_total(self):
        """测试计算总和"""
        mock_model = MagicMock()
        mock_model.amount = "amount_field"
        self.service.get_model = MagicMock(return_value=mock_model)
        
        mock_query = MagicMock()
        mock_query.with_entities.return_value.scalar.return_value = Decimal("250000")
        
        result = self.service.calculate_total(mock_query, "amount")
        
        self.assertEqual(result, 250000.0)

    def test_calculate_total_none(self):
        """测试总和为None"""
        mock_model = MagicMock()
        mock_model.amount = "amount_field"
        self.service.get_model = MagicMock(return_value=mock_model)
        
        mock_query = MagicMock()
        mock_query.with_entities.return_value.scalar.return_value = None
        
        result = self.service.calculate_total(mock_query, "amount")
        
        self.assertEqual(result, 0.0)

    def test_calculate_total_invalid_field(self):
        """测试字段不存在"""
        mock_model = MagicMock()
        del mock_model.invalid_field
        self.service.get_model = MagicMock(return_value=mock_model)
        
        result = self.service.calculate_total(MagicMock(), "invalid_field")
        
        self.assertEqual(result, 0.0)

    # ========== calculate_avg 测试 ==========

    def test_calculate_avg(self):
        """测试计算平均值"""
        mock_model = MagicMock()
        mock_model.progress_pct = "progress_field"
        self.service.get_model = MagicMock(return_value=mock_model)
        
        mock_query = MagicMock()
        mock_query.with_entities.return_value.scalar.return_value = Decimal("45.5")
        
        result = self.service.calculate_avg(mock_query, "progress_pct")
        
        self.assertEqual(result, 45.5)

    def test_calculate_avg_none(self):
        """测试平均值为None"""
        mock_model = MagicMock()
        mock_model.progress_pct = "progress_field"
        self.service.get_model = MagicMock(return_value=mock_model)
        
        mock_query = MagicMock()
        mock_query.with_entities.return_value.scalar.return_value = None
        
        result = self.service.calculate_avg(mock_query, "progress_pct")
        
        self.assertEqual(result, 0.0)

    # ========== count_distinct 测试 ==========

    def test_count_distinct(self):
        """测试计算不重复数量"""
        mock_model = MagicMock()
        mock_model.user_id = "user_id_field"
        self.service.get_model = MagicMock(return_value=mock_model)
        
        mock_query = MagicMock()
        mock_query.with_entities.return_value.scalar.return_value = 5
        
        result = self.service.count_distinct(mock_query, "user_id")
        
        self.assertEqual(result, 5)

    def test_count_distinct_none(self):
        """测试不重复数量为None"""
        mock_model = MagicMock()
        mock_model.user_id = "user_id_field"
        self.service.get_model = MagicMock(return_value=mock_model)
        
        mock_query = MagicMock()
        mock_query.with_entities.return_value.scalar.return_value = None
        
        result = self.service.count_distinct(mock_query, "user_id")
        
        self.assertEqual(result, 0)


class TestCostStatisticsService(unittest.TestCase):
    """测试成本统计服务"""

    def setUp(self):
        """准备mock数据库"""
        self.mock_db = MagicMock()
        self.service = CostStatisticsService(self.mock_db)

    def test_get_model(self):
        """测试get_model返回正确的模型"""
        from app.models.project import ProjectCost
        self.assertEqual(self.service.get_model(), ProjectCost)

    def test_get_project_id_field(self):
        """测试get_project_id_field返回正确字段名"""
        self.assertEqual(self.service.get_project_id_field(), "project_id")

    def test_get_summary(self):
        """测试获取成本汇总"""
        # Mock项目
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = Decimal("500000")
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_project
        self.mock_db.query.return_value = mock_query
        
        # Mock成本查询
        with patch.object(self.service, 'build_base_query') as mock_build:
            with patch.object(self.service, 'apply_date_filter') as mock_filter:
                with patch.object(self.service, 'group_by_field') as mock_group:
                    with patch.object(self.service, 'calculate_total') as mock_total:
                        mock_build.return_value = MagicMock()
                        mock_filter.return_value = MagicMock()
                        mock_group.return_value = {"人工": 100000.0, "材料": 50000.0}
                        mock_total.return_value = 150000.0
                        
                        result = self.service.get_summary(1)
                        
                        self.assertEqual(result["project_id"], 1)
                        self.assertEqual(result["project_name"], "测试项目")
                        self.assertEqual(result["total_cost"], 150000.0)
                        self.assertEqual(result["by_type"]["人工"], 100000.0)
                        self.assertEqual(result["budget"], 500000.0)
                        self.assertEqual(result["budget_used_pct"], 30.0)

    def test_get_summary_no_budget(self):
        """测试无预算情况"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = None
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_project
        self.mock_db.query.return_value = mock_query
        
        with patch.object(self.service, 'build_base_query'):
            with patch.object(self.service, 'apply_date_filter'):
                with patch.object(self.service, 'group_by_field', return_value={}):
                    with patch.object(self.service, 'calculate_total', return_value=0.0):
                        result = self.service.get_summary(1)
                        
                        self.assertIsNone(result["budget"])
                        self.assertIsNone(result["budget_used_pct"])


class TestTimesheetStatisticsService(unittest.TestCase):
    """测试工时统计服务"""

    def setUp(self):
        """准备mock数据库"""
        self.mock_db = MagicMock()
        self.service = TimesheetStatisticsService(self.mock_db)

    def test_get_model(self):
        """测试get_model返回正确的模型"""
        from app.models.timesheet import Timesheet
        self.assertEqual(self.service.get_model(), Timesheet)

    def test_get_project_id_field(self):
        """测试get_project_id_field返回正确字段名"""
        self.assertEqual(self.service.get_project_id_field(), "project_id")

    def test_get_summary(self):
        """测试获取工时汇总"""
        # Mock项目
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"
        
        # Mock用户
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "张三"
        
        # Mock工时记录
        mock_timesheet1 = MagicMock()
        mock_timesheet1.hours = 8.0
        mock_timesheet1.user_id = 1
        mock_timesheet1.work_date = date(2024, 1, 15)
        mock_timesheet1.overtime_type = "NORMAL"
        mock_timesheet1.status = "APPROVED"
        
        mock_timesheet2 = MagicMock()
        mock_timesheet2.hours = 4.0
        mock_timesheet2.user_id = 1
        mock_timesheet2.work_date = date(2024, 1, 16)
        mock_timesheet2.overtime_type = "OVERTIME"
        mock_timesheet2.status = "APPROVED"
        
        # 配置mock
        def mock_query_side_effect(model):
            if model.__name__ == "Project":
                query = MagicMock()
                query.filter.return_value.first.return_value = mock_project
                return query
            elif model.__name__ == "User":
                query = MagicMock()
                query.filter.return_value.first.return_value = mock_user
                return query
            return MagicMock()
        
        self.mock_db.query.side_effect = mock_query_side_effect
        
        with patch.object(self.service, 'build_base_query') as mock_build:
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [mock_timesheet1, mock_timesheet2]
            mock_build.return_value = mock_query
            
            with patch.object(self.service, 'apply_date_filter', return_value=mock_query):
                result = self.service.get_summary(1)
                
                self.assertEqual(result["project_id"], 1)
                self.assertEqual(result["project_name"], "测试项目")
                self.assertEqual(result["total_hours"], 12.0)
                self.assertEqual(result["total_participants"], 1)
                self.assertEqual(len(result["by_user"]), 1)
                self.assertEqual(result["by_user"][0]["user_name"], "张三")
                self.assertEqual(result["by_user"][0]["total_hours"], 12.0)

    def test_get_statistics(self):
        """测试获取工时统计"""
        # Mock项目
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"
        
        # Mock不同状态的工时
        timesheets = []
        for status, hours in [("APPROVED", 8.0), ("PENDING", 4.0), ("DRAFT", 2.0), ("REJECTED", 1.0)]:
            ts = MagicMock()
            ts.hours = hours
            ts.status = status
            ts.user_id = 1
            ts.work_date = date(2024, 1, 15)
            timesheets.append(ts)
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_project
        self.mock_db.query.return_value = mock_query
        
        with patch.object(self.service, 'build_base_query') as mock_build:
            with patch.object(self.service, 'apply_date_filter') as mock_filter:
                mock_ts_query = MagicMock()
                mock_ts_query.all.return_value = timesheets
                mock_build.return_value = mock_ts_query
                mock_filter.return_value = mock_ts_query
                
                result = self.service.get_statistics(1)
                
                self.assertEqual(result["total_hours"], 15.0)
                self.assertEqual(result["approved_hours"], 8.0)
                self.assertEqual(result["pending_hours"], 4.0)
                self.assertEqual(result["draft_hours"], 2.0)
                self.assertEqual(result["rejected_hours"], 1.0)
                self.assertEqual(result["total_records"], 4)
                self.assertEqual(result["total_participants"], 1)


class TestWorkLogStatisticsService(unittest.TestCase):
    """测试工作日志统计服务"""

    def setUp(self):
        """准备mock数据库"""
        self.mock_db = MagicMock()
        self.service = WorkLogStatisticsService(self.mock_db)

    def test_get_model(self):
        """测试get_model返回正确的模型"""
        from app.models.work_log import WorkLog
        self.assertEqual(self.service.get_model(), WorkLog)

    def test_get_project_id_field(self):
        """测试get_project_id_field返回正确字段名"""
        self.assertEqual(self.service.get_project_id_field(), "id")

    def test_get_summary(self):
        """测试获取工作日志汇总"""
        from app.models.work_log import WorkLog, WorkLogMention
        
        # Mock项目
        mock_project = MagicMock()
        mock_project.id = 1
        
        mock_query_project = MagicMock()
        mock_query_project.filter.return_value.first.return_value = mock_project
        
        # Mock统计结果
        mock_stats = MagicMock()
        mock_stats.log_count = 10
        mock_stats.contributor_count = 3
        
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value.first.return_value = mock_stats
        
        def query_side_effect(model):
            if hasattr(model, '__name__') and model.__name__ == 'Project':
                return mock_query_project
            return mock_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_summary(1)
        
        self.assertEqual(result["project_id"], 1)
        self.assertEqual(result["log_count"], 10)
        self.assertEqual(result["contributor_count"], 3)

    def test_get_summary_with_date_range(self):
        """测试带日期范围的工作日志汇总"""
        from app.models.work_log import WorkLog, WorkLogMention
        
        mock_project = MagicMock()
        mock_project.id = 1
        
        mock_query_project = MagicMock()
        mock_query_project.filter.return_value.first.return_value = mock_project
        
        mock_stats = MagicMock()
        mock_stats.log_count = 5
        mock_stats.contributor_count = 2
        
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value.first.return_value = mock_stats
        
        def query_side_effect(model):
            if hasattr(model, '__name__') and model.__name__ == 'Project':
                return mock_query_project
            return mock_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        result = self.service.get_summary(1, start_date, end_date)
        
        self.assertEqual(result["log_count"], 5)
        # 验证filter被调用了多次（包括日期过滤）
        self.assertGreaterEqual(mock_query.filter.call_count, 2)


if __name__ == "__main__":
    unittest.main()

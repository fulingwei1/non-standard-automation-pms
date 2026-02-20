# -*- coding: utf-8 -*-
"""
PMO Cockpit Service 单元测试
覆盖率目标: 60%+
"""
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

from app.services.pmo_cockpit import PmoCockpitService


class TestPmoCockpitService(unittest.TestCase):
    """PMO驾驶舱服务测试"""

    def setUp(self):
        """测试前置准备"""
        self.mock_db = MagicMock()
        self.service = PmoCockpitService(self.mock_db)

    def test_get_dashboard_basic_stats(self):
        """测试获取驾驶舱基础统计数据"""
        # Mock 数据库查询结果
        mock_query = self.mock_db.query.return_value
        mock_query.scalar.side_effect = [
            100,  # total_projects
            80,  # active_projects
            20,  # completed_projects
            5,  # delayed_projects
            1000000.0,  # budget
            800000.0,  # cost
            15,  # total_risks
            8,  # high_risks
            3,  # critical_risks
        ]
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value.all.side_effect = [
            [("PLANNED", 30), ("IN_PROGRESS", 50), ("COMPLETED", 20)],  # by_status
            [("S1", 20), ("S5", 60), ("S9", 20)],  # by_stage
        ]
        mock_query.order_by.return_value.limit.return_value.all.return_value = []

        # 调用服务方法
        result = self.service.get_dashboard()

        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.summary.total_projects, 100)
        self.assertEqual(result.summary.active_projects, 80)
        self.assertEqual(result.summary.completed_projects, 20)
        self.assertEqual(result.summary.delayed_projects, 5)
        self.assertEqual(result.summary.total_budget, 1000000.0)
        self.assertEqual(result.summary.total_cost, 800000.0)

    def test_get_risk_wall_critical_risks(self):
        """测试获取风险墙的严重风险"""
        # Mock 风险数据
        mock_risk = MagicMock()
        mock_risk.id = 1
        mock_risk.project_id = 100
        mock_risk.risk_no = "RISK-001"
        mock_risk.risk_category = "TECHNICAL"
        mock_risk.risk_name = "技术风险"
        mock_risk.description = "测试风险"
        mock_risk.probability = "HIGH"
        mock_risk.impact = "HIGH"
        mock_risk.risk_level = "CRITICAL"
        mock_risk.response_strategy = "MITIGATE"
        mock_risk.response_plan = "缓解计划"
        mock_risk.owner_id = 1
        mock_risk.owner_name = "张三"
        mock_risk.status = "OPEN"
        mock_risk.follow_up_date = None
        mock_risk.last_update = None
        mock_risk.trigger_condition = None
        mock_risk.is_triggered = False
        mock_risk.triggered_date = None
        mock_risk.closed_date = None
        mock_risk.closed_reason = None
        mock_risk.created_at = datetime.now()
        mock_risk.updated_at = datetime.now()

        # Mock 查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.side_effect = [
            [mock_risk],  # critical_risks
            [mock_risk],  # high_risks
            [("TECHNICAL", 5), ("RESOURCE", 3)],  # by_category
            [(100, 5)],  # by_project
        ]
        mock_query.group_by.return_value = mock_query

        # Mock project 查询
        mock_project = MagicMock()
        mock_project.id = 100
        mock_project.project_code = "PRJ-001"
        mock_project.project_name = "测试项目"
        mock_query.first.return_value = mock_project

        # 调用服务方法
        result = self.service.get_risk_wall()

        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.total_risks, 10)
        self.assertEqual(len(result.critical_risks), 1)
        self.assertEqual(result.critical_risks[0].risk_level, "CRITICAL")

    def test_get_weekly_report_default_week(self):
        """测试获取周报（默认当前周）"""
        # Mock 查询结果
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        # 调用服务方法（不传week_start，使用默认值）
        result = self.service.get_weekly_report()

        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.report_date, date.today())
        self.assertIsNotNone(result.week_start)
        self.assertIsNotNone(result.week_end)
        self.assertEqual(result.new_projects, 5)

    def test_get_weekly_report_custom_week(self):
        """测试获取周报（指定周）"""
        # 指定的周开始日期
        custom_week_start = date(2026, 2, 17)  # 假设是周一

        # Mock 查询结果
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        # 调用服务方法
        result = self.service.get_weekly_report(week_start=custom_week_start)

        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.week_start, custom_week_start)
        self.assertEqual(result.week_end, custom_week_start + timedelta(days=6))

    def test_get_resource_overview(self):
        """测试获取资源负荷总览"""
        # Mock 用户查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 50  # total_resources

        # Mock 已分配资源
        mock_query.distinct.return_value.all.return_value = [(1,), (2,), (3,)]

        # Mock 资源分配
        mock_alloc = MagicMock()
        mock_alloc.resource_id = 1
        mock_alloc.allocation_percent = 150  # 超负荷
        mock_query.all.return_value = [mock_alloc]

        # Mock 部门数据
        mock_dept = MagicMock()
        mock_dept.id = 1
        mock_dept.name = "研发部"
        self.mock_db.query.return_value.all.return_value = [mock_dept]

        # Mock join查询
        mock_query.join.return_value = mock_query

        # 调用服务方法
        result = self.service.get_resource_overview()

        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.total_resources, 50)

    def test_get_projects_by_status(self):
        """测试按状态统计项目"""
        # Mock 查询结果
        mock_query = self.mock_db.query.return_value
        mock_query.group_by.return_value.all.return_value = [
            ("PLANNED", 10),
            ("IN_PROGRESS", 20),
            ("COMPLETED", 5),
        ]

        # 调用私有方法
        result = self.service._get_projects_by_status()

        # 验证结果
        self.assertEqual(result["PLANNED"], 10)
        self.assertEqual(result["IN_PROGRESS"], 20)
        self.assertEqual(result["COMPLETED"], 5)

    def test_get_projects_by_stage(self):
        """测试按阶段统计项目"""
        # Mock 查询结果
        mock_query = self.mock_db.query.return_value
        mock_query.group_by.return_value.all.return_value = [
            ("S1", 15),
            ("S5", 25),
            ("S9", 10),
        ]

        # 调用私有方法
        result = self.service._get_projects_by_stage()

        # 验证结果
        self.assertEqual(result["S1"], 15)
        self.assertEqual(result["S5"], 25)
        self.assertEqual(result["S9"], 10)

    def test_calculate_overloaded_resources_standard(self):
        """测试计算超负荷资源（标准情况）"""
        # Mock 资源分配数据
        mock_alloc1 = MagicMock()
        mock_alloc1.resource_id = 1
        mock_alloc1.allocation_percent = 100  # 正常负荷

        mock_alloc2 = MagicMock()
        mock_alloc2.resource_id = 2
        mock_alloc2.allocation_percent = 150  # 超负荷

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = [mock_alloc1, mock_alloc2]

        # 调用私有方法
        result = self.service._calculate_overloaded_resources(standard_workload=160)

        # 验证结果 - 只有resource_id=2超负荷
        self.assertEqual(result, 1)

    def test_convert_risk_to_response(self):
        """测试风险模型转换为响应对象"""
        # 创建mock风险对象
        mock_risk = MagicMock()
        mock_risk.id = 1
        mock_risk.project_id = 100
        mock_risk.risk_no = "RISK-001"
        mock_risk.risk_category = "TECHNICAL"
        mock_risk.risk_name = "技术风险"
        mock_risk.description = "测试描述"
        mock_risk.probability = "HIGH"
        mock_risk.impact = "MEDIUM"
        mock_risk.risk_level = "HIGH"
        mock_risk.response_strategy = "MITIGATE"
        mock_risk.response_plan = "缓解计划"
        mock_risk.owner_id = 1
        mock_risk.owner_name = "张三"
        mock_risk.status = "OPEN"
        mock_risk.follow_up_date = date.today()
        mock_risk.last_update = datetime.now()
        mock_risk.trigger_condition = "条件"
        mock_risk.is_triggered = False
        mock_risk.triggered_date = None
        mock_risk.closed_date = None
        mock_risk.closed_reason = None
        mock_risk.created_at = datetime.now()
        mock_risk.updated_at = datetime.now()

        # 调用转换方法
        result = self.service._convert_risk_to_response(mock_risk)

        # 验证结果
        self.assertEqual(result.id, 1)
        self.assertEqual(result.risk_no, "RISK-001")
        self.assertEqual(result.risk_level, "HIGH")
        self.assertEqual(result.owner_name, "张三")


if __name__ == "__main__":
    unittest.main()

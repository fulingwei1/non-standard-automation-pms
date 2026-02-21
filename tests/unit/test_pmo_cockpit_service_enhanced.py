# -*- coding: utf-8 -*-
"""
PMO Cockpit Service 增强单元测试
覆盖所有核心方法和边界条件
"""
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.pmo_cockpit.pmo_cockpit_service import PmoCockpitService


class TestPmoCockpitServiceInit(unittest.TestCase):
    """测试初始化"""

    def test_init(self):
        """测试服务初始化"""
        mock_db = MagicMock()
        service = PmoCockpitService(mock_db)
        self.assertEqual(service.db, mock_db)


class TestGetDashboard(unittest.TestCase):
    """测试 get_dashboard 方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = PmoCockpitService(self.mock_db)

    def test_get_dashboard_success(self):
        """测试成功获取驾驶舱数据"""
        # Mock 查询链
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 10

        # Mock 辅助方法
        self.service._get_projects_by_status = MagicMock(
            return_value={"ACTIVE": 5, "PENDING": 3}
        )
        self.service._get_projects_by_stage = MagicMock(
            return_value={"S1": 2, "S2": 4}
        )
        self.service._get_recent_risks = MagicMock(return_value=[])

        result = self.service.get_dashboard()

        self.assertIsNotNone(result)
        self.assertEqual(result.summary.total_projects, 10)
        self.mock_db.query.assert_called()

    def test_get_dashboard_no_projects(self):
        """测试无项目时的驾驶舱"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0

        self.service._get_projects_by_status = MagicMock(return_value={})
        self.service._get_projects_by_stage = MagicMock(return_value={})
        self.service._get_recent_risks = MagicMock(return_value=[])

        result = self.service.get_dashboard()

        self.assertEqual(result.summary.total_projects, 0)
        self.assertEqual(result.summary.active_projects, 0)

    def test_get_dashboard_with_delayed_projects(self):
        """测试包含延期项目的情况"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.side_effect = [10, 8, 2, 3, 1000.0, 800.0, 5, 2, 1]

        self.service._get_projects_by_status = MagicMock(return_value={})
        self.service._get_projects_by_stage = MagicMock(return_value={})
        self.service._get_recent_risks = MagicMock(return_value=[])

        result = self.service.get_dashboard()

        self.assertEqual(result.summary.delayed_projects, 3)

    def test_get_dashboard_with_budget_and_cost(self):
        """测试预算和成本统计"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.side_effect = [10, 8, 2, 3, 5000.0, 3500.0, 5, 2, 1]

        self.service._get_projects_by_status = MagicMock(return_value={})
        self.service._get_projects_by_stage = MagicMock(return_value={})
        self.service._get_recent_risks = MagicMock(return_value=[])

        result = self.service.get_dashboard()

        self.assertEqual(result.summary.total_budget, 5000.0)
        self.assertEqual(result.summary.total_cost, 3500.0)

    def test_get_dashboard_with_risks(self):
        """测试风险统计"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.side_effect = [10, 8, 2, 3, 1000.0, 800.0, 15, 5, 2]

        self.service._get_projects_by_status = MagicMock(return_value={})
        self.service._get_projects_by_stage = MagicMock(return_value={})
        self.service._get_recent_risks = MagicMock(return_value=[])

        result = self.service.get_dashboard()

        self.assertEqual(result.summary.total_risks, 15)
        self.assertEqual(result.summary.high_risks, 5)
        self.assertEqual(result.summary.critical_risks, 2)


class TestGetRiskWall(unittest.TestCase):
    """测试 get_risk_wall 方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = PmoCockpitService(self.mock_db)

    def test_get_risk_wall_success(self):
        """测试成功获取风险墙"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        self.service._get_risks_by_category = MagicMock(return_value={})
        self.service._get_risks_by_project = MagicMock(return_value=[])

        result = self.service.get_risk_wall()

        self.assertIsNotNone(result)
        self.assertEqual(result.total_risks, 10)

    def test_get_risk_wall_with_critical_risks(self):
        """测试包含严重风险的情况"""
        from app.schemas.pmo import RiskResponse
        
        mock_risk = MagicMock()
        mock_risk.id = 1
        mock_risk.risk_level = "CRITICAL"

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_risk]

        self.service._get_risks_by_category = MagicMock(return_value={})
        self.service._get_risks_by_project = MagicMock(return_value=[])
        
        # 创建一个真实的 RiskResponse 对象而不是 MagicMock
        now = datetime.now()
        mock_response = RiskResponse(
            id=1,
            project_id=10,
            risk_no="RISK-001",
            risk_category="TECHNICAL",
            risk_name="Test Risk",
            description="Test Description",
            probability="HIGH",
            impact="MEDIUM",
            risk_level="CRITICAL",
            response_strategy="MITIGATE",
            response_plan="Test Plan",
            owner_id=5,
            owner_name="John Doe",
            status="ACTIVE",
            is_triggered=False,
            created_at=now,
            updated_at=now
        )
        self.service._convert_risk_to_response = MagicMock(return_value=mock_response)

        result = self.service.get_risk_wall()

        self.assertEqual(len(result.critical_risks), 1)

    def test_get_risk_wall_no_risks(self):
        """测试无风险时的风险墙"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        self.service._get_risks_by_category = MagicMock(return_value={})
        self.service._get_risks_by_project = MagicMock(return_value=[])

        result = self.service.get_risk_wall()

        self.assertEqual(result.total_risks, 0)
        self.assertEqual(len(result.critical_risks), 0)


class TestGetWeeklyReport(unittest.TestCase):
    """测试 get_weekly_report 方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = PmoCockpitService(self.mock_db)

    @patch('app.services.pmo_cockpit.pmo_cockpit_service.date')
    def test_get_weekly_report_default_week(self, mock_date):
        """测试使用默认周的周报"""
        mock_date.today.return_value = date(2024, 1, 15)  # Monday

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5

        self.service._get_project_updates = MagicMock(return_value=[])

        result = self.service.get_weekly_report()

        self.assertIsNotNone(result)
        self.assertEqual(result.week_start, date(2024, 1, 15))

    def test_get_weekly_report_custom_week(self):
        """测试使用自定义周的周报"""
        custom_start = date(2024, 1, 8)

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3

        self.service._get_project_updates = MagicMock(return_value=[])

        result = self.service.get_weekly_report(week_start=custom_start)

        self.assertEqual(result.week_start, custom_start)
        self.assertEqual(result.week_end, date(2024, 1, 14))

    def test_get_weekly_report_with_new_projects(self):
        """测试包含新项目的周报"""
        week_start = date(2024, 1, 1)

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.side_effect = [5, 2, 1, 3, 2]

        self.service._get_project_updates = MagicMock(return_value=[])

        result = self.service.get_weekly_report(week_start=week_start)

        self.assertEqual(result.new_projects, 5)

    def test_get_weekly_report_with_risks(self):
        """测试包含风险的周报"""
        week_start = date(2024, 1, 1)

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.side_effect = [2, 3, 1, 5, 3]

        self.service._get_project_updates = MagicMock(return_value=[])

        result = self.service.get_weekly_report(week_start=week_start)

        self.assertEqual(result.new_risks, 5)
        self.assertEqual(result.resolved_risks, 3)


class TestGetResourceOverview(unittest.TestCase):
    """测试 get_resource_overview 方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = PmoCockpitService(self.mock_db)

    def test_get_resource_overview_success(self):
        """测试成功获取资源总览"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 50
        mock_query.distinct.return_value = mock_query
        mock_query.all.return_value = [(1,), (2,), (3,)]

        self.service._calculate_overloaded_resources = MagicMock(return_value=5)
        self.service._get_resources_by_department = MagicMock(return_value=[])

        result = self.service.get_resource_overview()

        self.assertEqual(result.total_resources, 50)
        self.assertEqual(result.allocated_resources, 3)
        self.assertEqual(result.available_resources, 47)
        self.assertEqual(result.overloaded_resources, 5)

    def test_get_resource_overview_all_allocated(self):
        """测试全部资源已分配的情况"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.distinct.return_value = mock_query
        mock_query.all.return_value = [(i,) for i in range(10)]

        self.service._calculate_overloaded_resources = MagicMock(return_value=0)
        self.service._get_resources_by_department = MagicMock(return_value=[])

        result = self.service.get_resource_overview()

        self.assertEqual(result.available_resources, 0)

    def test_get_resource_overview_no_resources(self):
        """测试无资源时的总览"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.distinct.return_value = mock_query
        mock_query.all.return_value = []

        self.service._calculate_overloaded_resources = MagicMock(return_value=0)
        self.service._get_resources_by_department = MagicMock(return_value=[])

        result = self.service.get_resource_overview()

        self.assertEqual(result.total_resources, 0)


class TestPrivateMethods(unittest.TestCase):
    """测试私有辅助方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = PmoCockpitService(self.mock_db)

    def test_get_projects_by_status(self):
        """测试按状态统计项目"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [("ACTIVE", 5), ("PENDING", 3)]

        result = self.service._get_projects_by_status()

        self.assertEqual(result, {"ACTIVE": 5, "PENDING": 3})

    def test_get_projects_by_stage(self):
        """测试按阶段统计项目"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [("S1", 2), ("S2", 4), ("S9", 10)]

        result = self.service._get_projects_by_stage()

        self.assertEqual(result, {"S1": 2, "S2": 4, "S9": 10})

    def test_get_recent_risks(self):
        """测试获取最近风险"""
        mock_risk = MagicMock()
        mock_risk.id = 1

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_risk]

        self.service._convert_risk_to_response = MagicMock(return_value=MagicMock())

        result = self.service._get_recent_risks(limit=5)

        self.assertEqual(len(result), 1)
        mock_query.limit.assert_called_with(5)

    def test_convert_risk_to_response(self):
        """测试风险转换为响应对象"""
        now = datetime.now()
        today = date.today()
        
        mock_risk = MagicMock()
        mock_risk.id = 1
        mock_risk.project_id = 10
        mock_risk.risk_no = "RISK-001"
        mock_risk.risk_category = "TECHNICAL"
        mock_risk.risk_name = "Test Risk"
        mock_risk.description = "Test Description"
        mock_risk.probability = "HIGH"
        mock_risk.impact = "MEDIUM"
        mock_risk.risk_level = "HIGH"
        mock_risk.response_strategy = "MITIGATE"
        mock_risk.response_plan = "Test Plan"
        mock_risk.owner_id = 5
        mock_risk.owner_name = "John Doe"
        mock_risk.status = "ACTIVE"
        mock_risk.follow_up_date = today
        mock_risk.last_update = "2024-01-01"
        mock_risk.trigger_condition = "Some condition"
        mock_risk.is_triggered = False
        mock_risk.triggered_date = None
        mock_risk.closed_date = None
        mock_risk.closed_reason = None
        mock_risk.created_at = now
        mock_risk.updated_at = now

        result = self.service._convert_risk_to_response(mock_risk)

        self.assertEqual(result.id, 1)
        self.assertEqual(result.risk_no, "RISK-001")
        self.assertEqual(result.risk_level, "HIGH")

    def test_get_risks_by_category(self):
        """测试按类别统计风险"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [
            ("TECHNICAL", 5),
            ("BUSINESS", 3),
            ("RESOURCE", 2),
        ]

        result = self.service._get_risks_by_category()

        self.assertEqual(result, {"TECHNICAL": 5, "BUSINESS": 3, "RESOURCE": 2})

    def test_get_risks_by_project(self):
        """测试按项目统计风险"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ-001"
        mock_project.project_name = "Test Project"

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [(1, 5)]
        mock_query.first.return_value = mock_project

        result = self.service._get_risks_by_project(limit=10)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["project_id"], 1)
        self.assertEqual(result[0]["risk_count"], 5)

    def test_get_risks_by_project_no_project_found(self):
        """测试按项目统计风险时项目不存在"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [(1, 5)]
        mock_query.first.return_value = None

        result = self.service._get_risks_by_project(limit=10)

        self.assertEqual(len(result), 0)

    def test_get_project_updates(self):
        """测试获取项目更新列表"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ-001"
        mock_project.project_name = "Test Project"
        mock_project.stage = "S2"
        mock_project.status = "ACTIVE"
        mock_project.progress_pct = Decimal("75.50")
        mock_project.updated_at = datetime.now()

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_project]

        week_start = date(2024, 1, 1)
        week_end = date(2024, 1, 7)

        result = self.service._get_project_updates(week_start, week_end, limit=10)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["project_code"], "PRJ-001")
        self.assertEqual(result[0]["progress"], 75.50)

    def test_get_project_updates_null_progress(self):
        """测试项目更新中进度为空的情况"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ-001"
        mock_project.project_name = "Test Project"
        mock_project.stage = "S1"
        mock_project.status = "PENDING"
        mock_project.progress_pct = None
        mock_project.updated_at = datetime.now()

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_project]

        week_start = date(2024, 1, 1)
        week_end = date(2024, 1, 7)

        result = self.service._get_project_updates(week_start, week_end, limit=10)

        self.assertEqual(result[0]["progress"], 0.0)

    def test_calculate_overloaded_resources_default(self):
        """测试计算超负荷资源（默认标准）"""
        mock_alloc1 = MagicMock()
        mock_alloc1.resource_id = 1
        mock_alloc1.allocation_percent = 80

        mock_alloc2 = MagicMock()
        mock_alloc2.resource_id = 1
        mock_alloc2.allocation_percent = 50

        mock_alloc3 = MagicMock()
        mock_alloc3.resource_id = 2
        mock_alloc3.allocation_percent = 60

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_alloc1, mock_alloc2, mock_alloc3]

        result = self.service._calculate_overloaded_resources()

        # Resource 1: (80+50)/100 * 160 = 208 > 160, overloaded
        # Resource 2: 60/100 * 160 = 96 < 160, not overloaded
        self.assertEqual(result, 1)

    def test_calculate_overloaded_resources_custom_standard(self):
        """测试计算超负荷资源（自定义标准）"""
        mock_alloc = MagicMock()
        mock_alloc.resource_id = 1
        mock_alloc.allocation_percent = 100

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_alloc]

        result = self.service._calculate_overloaded_resources(standard_workload=120)

        # Resource 1: 100/100 * 120 = 120, not overloaded (not > 120)
        self.assertEqual(result, 0)

    def test_calculate_overloaded_resources_null_allocation(self):
        """测试计算超负荷资源时分配比例为空"""
        mock_alloc = MagicMock()
        mock_alloc.resource_id = 1
        mock_alloc.allocation_percent = None

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_alloc]

        result = self.service._calculate_overloaded_resources()

        self.assertEqual(result, 0)

    def test_get_resources_by_department(self):
        """测试按部门统计资源"""
        mock_dept = MagicMock()
        mock_dept.id = 1
        mock_dept.name = "Engineering"

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.all.return_value = [mock_dept]
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.count.side_effect = [10, 6]

        result = self.service._get_resources_by_department()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["department_name"], "Engineering")
        self.assertEqual(result[0]["total_resources"], 10)
        self.assertEqual(result[0]["allocated_resources"], 6)
        self.assertEqual(result[0]["available_resources"], 4)

    def test_get_resources_by_department_no_departments(self):
        """测试无部门时的资源统计"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.all.return_value = []

        result = self.service._get_resources_by_department()

        self.assertEqual(len(result), 0)


class TestEdgeCases(unittest.TestCase):
    """测试边界条件"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = PmoCockpitService(self.mock_db)

    def test_dashboard_null_scalar_values(self):
        """测试驾驶舱中标量值为None的情况"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None

        self.service._get_projects_by_status = MagicMock(return_value={})
        self.service._get_projects_by_stage = MagicMock(return_value={})
        self.service._get_recent_risks = MagicMock(return_value=[])

        result = self.service.get_dashboard()

        self.assertEqual(result.summary.total_projects, 0)
        self.assertEqual(result.summary.total_budget, 0.0)

    @patch('app.services.pmo_cockpit.pmo_cockpit_service.date')
    def test_weekly_report_week_calculation(self, mock_date):
        """测试周报周开始日期计算（非周一）"""
        mock_date.today.return_value = date(2024, 1, 17)  # Wednesday

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0

        self.service._get_project_updates = MagicMock(return_value=[])

        result = self.service.get_weekly_report()

        # 17号是周三，周一应该是15号
        self.assertEqual(result.week_start, date(2024, 1, 15))

    def test_multiple_resources_same_id_overload(self):
        """测试同一资源多次分配导致超负荷"""
        allocations = []
        for _ in range(3):
            mock_alloc = MagicMock()
            mock_alloc.resource_id = 1
            mock_alloc.allocation_percent = 50
            allocations.append(mock_alloc)

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = allocations

        result = self.service._calculate_overloaded_resources()

        # Resource 1: 50+50+50 = 150% = 240 hours > 160
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()

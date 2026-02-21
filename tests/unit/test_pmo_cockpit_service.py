# -*- coding: utf-8 -*-
"""
PMO Cockpit Service 单元测试

测试策略：
1. 只mock外部依赖（数据库操作）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率：70%+
"""
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

from app.models.organization import Department
from app.models.pmo import PmoProjectRisk, PmoResourceAllocation
from app.models.project import Project
from app.models.user import User
from app.schemas.pmo import (
    DashboardResponse,
    ResourceOverviewResponse,
    RiskWallResponse,
    WeeklyReportResponse,
)
from app.services.pmo_cockpit.pmo_cockpit_service import PmoCockpitService


class TestPmoCockpitService(unittest.TestCase):
    """PMO驾驶舱服务测试"""

    def setUp(self):
        """设置测试环境"""
        self.db = MagicMock()
        self.service = PmoCockpitService(db=self.db)

    # ========== get_dashboard() 测试 ==========

    def test_get_dashboard_success(self):
        """测试获取驾驶舱数据 - 正常情况"""
        # Mock数据库查询
        mock_query = self.db.query.return_value
        
        # 项目统计
        mock_query.scalar.side_effect = [
            100,  # total_projects
            80,   # active_projects
            15,   # completed_projects
            5,    # delayed_projects
            1000000.0,  # budget_amount
            750000.0,   # actual_cost
            25,   # total_risks
            8,    # high_risks
            3,    # critical_risks
        ]
        
        # Mock filter chain
        mock_query.filter.return_value = mock_query
        
        # Mock 按状态和阶段统计
        mock_query.group_by.return_value.all.side_effect = [
            [("ACTIVE", 60), ("PAUSED", 20), ("COMPLETED", 15)],  # by_status
            [("S1", 10), ("S5", 50), ("S9", 15)],  # by_stage
        ]
        
        # Mock 最近风险
        mock_risk = MagicMock(spec=PmoProjectRisk)
        mock_risk.id = 1
        mock_risk.project_id = 101
        mock_risk.risk_no = "R001"
        mock_risk.risk_category = "TECHNICAL"
        mock_risk.risk_name = "技术风险"
        mock_risk.description = "测试风险"
        mock_risk.probability = "HIGH"
        mock_risk.impact = "HIGH"
        mock_risk.risk_level = "HIGH"
        mock_risk.response_strategy = "MITIGATE"
        mock_risk.response_plan = "缓解计划"
        mock_risk.owner_id = 1
        mock_risk.owner_name = "张三"
        mock_risk.status = "ACTIVE"
        mock_risk.follow_up_date = date.today()
        mock_risk.last_update = "2026-02-21"
        mock_risk.trigger_condition = None
        mock_risk.is_triggered = False
        mock_risk.triggered_date = None
        mock_risk.closed_date = None
        mock_risk.closed_reason = None
        mock_risk.created_at = datetime.now()
        mock_risk.updated_at = datetime.now()
        
        mock_query.order_by.return_value.limit.return_value.all.return_value = [mock_risk]
        
        # 执行测试
        result = self.service.get_dashboard()
        
        # 验证结果
        self.assertIsInstance(result, DashboardResponse)
        self.assertEqual(result.summary.total_projects, 100)
        self.assertEqual(result.summary.active_projects, 80)
        self.assertEqual(result.summary.completed_projects, 15)
        self.assertEqual(result.summary.delayed_projects, 5)
        self.assertEqual(result.summary.total_budget, 1000000.0)
        self.assertEqual(result.summary.total_cost, 750000.0)
        self.assertEqual(result.summary.total_risks, 25)
        self.assertEqual(result.summary.high_risks, 8)
        self.assertEqual(result.summary.critical_risks, 3)
        
        # 验证按状态统计
        self.assertEqual(len(result.projects_by_status), 3)
        self.assertEqual(result.projects_by_status["ACTIVE"], 60)
        
        # 验证按阶段统计
        self.assertEqual(len(result.projects_by_stage), 3)
        self.assertEqual(result.projects_by_stage["S1"], 10)
        
        # 验证最近风险
        self.assertEqual(len(result.recent_risks), 1)
        self.assertEqual(result.recent_risks[0].risk_no, "R001")

    def test_get_dashboard_empty_data(self):
        """测试获取驾驶舱数据 - 空数据"""
        mock_query = self.db.query.return_value
        
        # 所有统计返回0或None
        mock_query.scalar.side_effect = [
            None,  # total_projects -> 0
            None,  # active_projects -> 0
            None,  # completed_projects -> 0
            None,  # delayed_projects -> 0
            None,  # budget_amount -> 0
            None,  # actual_cost -> 0
            None,  # total_risks -> 0
            None,  # high_risks -> 0
            None,  # critical_risks -> 0
        ]
        
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value.all.side_effect = [[], []]
        mock_query.order_by.return_value.limit.return_value.all.return_value = []
        
        result = self.service.get_dashboard()
        
        self.assertIsInstance(result, DashboardResponse)
        self.assertEqual(result.summary.total_projects, 0)
        self.assertEqual(result.summary.total_budget, 0.0)
        self.assertEqual(result.projects_by_status, {})
        self.assertEqual(result.recent_risks, [])

    # ========== get_risk_wall() 测试 ==========

    def test_get_risk_wall_success(self):
        """测试获取风险墙 - 正常情况"""
        mock_query = self.db.query.return_value
        
        # Mock count
        mock_query.filter.return_value.count.return_value = 20
        
        # Mock critical risks
        mock_critical_risk = self._create_mock_risk("R001", "CRITICAL")
        mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_critical_risk]
        
        # Mock high risks
        mock_high_risk = self._create_mock_risk("R002", "HIGH")
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_high_risk]
        
        # Mock by_category
        mock_query.filter.return_value.group_by.return_value.all.side_effect = [
            [("TECHNICAL", 10), ("SCHEDULE", 5), ("COST", 3)],
        ]
        
        # Mock by_project
        mock_project = MagicMock(spec=Project)
        mock_project.id = 101
        mock_project.project_code = "P001"
        mock_project.project_name = "测试项目"
        
        mock_query.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            (101, 5),  # (project_id, risk_count)
        ]
        mock_query.filter.return_value.first.return_value = mock_project
        
        result = self.service.get_risk_wall()
        
        self.assertIsInstance(result, RiskWallResponse)
        self.assertEqual(result.total_risks, 20)
        self.assertEqual(len(result.critical_risks), 1)
        self.assertEqual(result.critical_risks[0].risk_level, "CRITICAL")
        self.assertEqual(len(result.high_risks), 1)
        self.assertEqual(result.by_category["TECHNICAL"], 10)
        self.assertEqual(len(result.by_project), 1)
        self.assertEqual(result.by_project[0]["project_code"], "P001")

    def test_get_risk_wall_no_project_found(self):
        """测试获取风险墙 - 项目不存在"""
        mock_query = self.db.query.return_value
        
        mock_query.filter.return_value.count.return_value = 5
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_query.filter.return_value.group_by.return_value.all.side_effect = [[], []]
        
        # by_project 查询返回数据，但项目不存在
        mock_query.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            (999, 3),  # 不存在的项目ID
        ]
        mock_query.filter.return_value.first.return_value = None  # 项目不存在
        
        result = self.service.get_risk_wall()
        
        # 项目不存在时，by_project应该为空列表
        self.assertEqual(result.by_project, [])

    # ========== get_weekly_report() 测试 ==========

    def test_get_weekly_report_with_week_start(self):
        """测试获取周报 - 指定周起始日期"""
        week_start = date(2026, 2, 17)  # 周一
        
        mock_query = self.db.query.return_value
        
        # Mock count
        mock_query.filter.return_value.count.side_effect = [
            3,   # new_projects
            2,   # completed_projects
            5,   # delayed_projects
            10,  # new_risks
            7,   # resolved_risks
        ]
        
        # Mock project updates
        mock_project = MagicMock(spec=Project)
        mock_project.id = 1
        mock_project.project_code = "P001"
        mock_project.project_name = "测试项目"
        mock_project.stage = "S5"
        mock_project.status = "ACTIVE"
        mock_project.progress_pct = 65.5
        mock_project.updated_at = datetime.now()
        
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_project]
        
        result = self.service.get_weekly_report(week_start=week_start)
        
        self.assertIsInstance(result, WeeklyReportResponse)
        self.assertEqual(result.week_start, week_start)
        self.assertEqual(result.week_end, week_start + timedelta(days=6))
        self.assertEqual(result.new_projects, 3)
        self.assertEqual(result.completed_projects, 2)
        self.assertEqual(result.delayed_projects, 5)
        self.assertEqual(result.new_risks, 10)
        self.assertEqual(result.resolved_risks, 7)
        self.assertEqual(len(result.project_updates), 1)
        self.assertEqual(result.project_updates[0]["project_code"], "P001")
        self.assertEqual(result.project_updates[0]["progress"], 65.5)

    def test_get_weekly_report_default_week(self):
        """测试获取周报 - 默认当前周"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.count.side_effect = [0, 0, 0, 0, 0]
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = self.service.get_weekly_report()
        
        # 验证使用当前周
        today = date.today()
        expected_week_start = today - timedelta(days=today.weekday())
        self.assertEqual(result.week_start, expected_week_start)

    def test_get_weekly_report_project_without_progress(self):
        """测试获取周报 - 项目无进度"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.count.side_effect = [0, 0, 0, 0, 0]
        
        mock_project = MagicMock(spec=Project)
        mock_project.id = 1
        mock_project.project_code = "P001"
        mock_project.project_name = "测试项目"
        mock_project.stage = "S1"
        mock_project.status = "ACTIVE"
        mock_project.progress_pct = None  # 无进度
        mock_project.updated_at = datetime.now()
        
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_project]
        
        result = self.service.get_weekly_report()
        
        self.assertEqual(result.project_updates[0]["progress"], 0.0)

    # ========== get_resource_overview() 测试 ==========

    def test_get_resource_overview_success(self):
        """测试获取资源总览 - 正常情况"""
        mock_query = self.db.query.return_value
        
        # Mock total_resources
        mock_query.filter.return_value.count.side_effect = [10, 3]  # total, dept_users, dept_allocated
        
        # Mock allocated_resources
        mock_query.filter.return_value.distinct.return_value.all.return_value = [
            (1,), (2,), (3,),  # 3个已分配的资源ID
        ]
        
        # Mock departments
        mock_dept = MagicMock(spec=Department)
        mock_dept.id = 1
        mock_dept.name = "研发部"
        mock_query.all.return_value = [mock_dept]
        
        # Mock overloaded resources (需要mock allocations)
        mock_alloc1 = MagicMock(spec=PmoResourceAllocation)
        mock_alloc1.resource_id = 1
        mock_alloc1.allocation_percent = 60
        mock_alloc1.status = "ACTIVE"
        
        mock_alloc2 = MagicMock(spec=PmoResourceAllocation)
        mock_alloc2.resource_id = 1  # 同一个资源
        mock_alloc2.allocation_percent = 50
        mock_alloc2.status = "PLANNED"
        
        mock_query.filter.return_value.all.return_value = [mock_alloc1, mock_alloc2]
        
        result = self.service.get_resource_overview()
        
        self.assertIsInstance(result, ResourceOverviewResponse)
        self.assertEqual(result.total_resources, 10)
        self.assertEqual(result.allocated_resources, 3)
        self.assertEqual(result.available_resources, 7)
        self.assertGreaterEqual(result.overloaded_resources, 0)
        self.assertIsInstance(result.by_department, list)

    def test_get_resource_overview_no_allocations(self):
        """测试获取资源总览 - 无分配"""
        mock_query = self.db.query.return_value
        
        mock_query.filter.return_value.count.side_effect = [5, 0]
        mock_query.filter.return_value.distinct.return_value.all.return_value = []
        mock_query.all.return_value = []
        mock_query.filter.return_value.all.return_value = []
        
        result = self.service.get_resource_overview()
        
        self.assertEqual(result.total_resources, 5)
        self.assertEqual(result.allocated_resources, 0)
        self.assertEqual(result.available_resources, 5)
        self.assertEqual(result.overloaded_resources, 0)

    # ========== 私有方法测试 ==========

    def test_get_projects_by_status(self):
        """测试按状态统计项目"""
        mock_query = self.db.query.return_value
        mock_query.group_by.return_value.all.return_value = [
            ("ACTIVE", 50),
            ("PAUSED", 10),
            ("COMPLETED", 20),
        ]
        
        result = self.service._get_projects_by_status()
        
        self.assertEqual(result, {"ACTIVE": 50, "PAUSED": 10, "COMPLETED": 20})

    def test_get_projects_by_stage(self):
        """测试按阶段统计项目"""
        mock_query = self.db.query.return_value
        mock_query.group_by.return_value.all.return_value = [
            ("S1", 15),
            ("S5", 40),
            ("S9", 25),
        ]
        
        result = self.service._get_projects_by_stage()
        
        self.assertEqual(result, {"S1": 15, "S5": 40, "S9": 25})

    def test_get_recent_risks(self):
        """测试获取最近风险"""
        mock_query = self.db.query.return_value
        
        mock_risk = self._create_mock_risk("R001", "HIGH")
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_risk]
        
        result = self.service._get_recent_risks(limit=5)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].risk_no, "R001")

    def test_convert_risk_to_response(self):
        """测试风险转换"""
        mock_risk = self._create_mock_risk("R001", "CRITICAL")
        
        result = self.service._convert_risk_to_response(mock_risk)
        
        self.assertEqual(result.risk_no, "R001")
        self.assertEqual(result.risk_level, "CRITICAL")
        self.assertEqual(result.owner_name, "张三")

    def test_get_risks_by_category(self):
        """测试按类别统计风险"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.group_by.return_value.all.return_value = [
            ("TECHNICAL", 12),
            ("SCHEDULE", 8),
            ("COST", 5),
        ]
        
        result = self.service._get_risks_by_category()
        
        self.assertEqual(result, {"TECHNICAL": 12, "SCHEDULE": 8, "COST": 5})

    def test_get_risks_by_project(self):
        """测试按项目统计风险"""
        mock_query = self.db.query.return_value
        
        mock_query.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            (101, 8),
            (102, 5),
        ]
        
        mock_project1 = MagicMock(spec=Project)
        mock_project1.id = 101
        mock_project1.project_code = "P001"
        mock_project1.project_name = "项目1"
        
        mock_project2 = MagicMock(spec=Project)
        mock_project2.id = 102
        mock_project2.project_code = "P002"
        mock_project2.project_name = "项目2"
        
        mock_query.filter.return_value.first.side_effect = [mock_project1, mock_project2]
        
        result = self.service._get_risks_by_project(limit=10)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["project_code"], "P001")
        self.assertEqual(result[0]["risk_count"], 8)

    def test_get_project_updates(self):
        """测试获取项目更新"""
        mock_query = self.db.query.return_value
        
        mock_project = MagicMock(spec=Project)
        mock_project.id = 1
        mock_project.project_code = "P001"
        mock_project.project_name = "测试项目"
        mock_project.stage = "S5"
        mock_project.status = "ACTIVE"
        mock_project.progress_pct = 75.0
        mock_project.updated_at = datetime.now()
        
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_project]
        
        week_start = date(2026, 2, 17)
        week_end = date(2026, 2, 23)
        result = self.service._get_project_updates(week_start, week_end, limit=5)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["project_code"], "P001")
        self.assertEqual(result[0]["progress"], 75.0)

    def test_calculate_overloaded_resources_default(self):
        """测试计算超负荷资源 - 默认标准"""
        mock_query = self.db.query.return_value
        
        # 资源1: 60% + 50% = 110% (超负荷)
        mock_alloc1 = MagicMock(spec=PmoResourceAllocation)
        mock_alloc1.resource_id = 1
        mock_alloc1.allocation_percent = 60
        
        mock_alloc2 = MagicMock(spec=PmoResourceAllocation)
        mock_alloc2.resource_id = 1
        mock_alloc2.allocation_percent = 50
        
        # 资源2: 80% (正常)
        mock_alloc3 = MagicMock(spec=PmoResourceAllocation)
        mock_alloc3.resource_id = 2
        mock_alloc3.allocation_percent = 80
        
        mock_query.filter.return_value.all.return_value = [mock_alloc1, mock_alloc2, mock_alloc3]
        
        result = self.service._calculate_overloaded_resources()
        
        # 资源1超负荷
        self.assertEqual(result, 1)

    def test_calculate_overloaded_resources_custom_standard(self):
        """测试计算超负荷资源 - 自定义标准"""
        mock_query = self.db.query.return_value
        
        # 资源1：120% 分配（超负荷）
        mock_alloc1 = MagicMock(spec=PmoResourceAllocation)
        mock_alloc1.resource_id = 1
        mock_alloc1.allocation_percent = 60
        
        mock_alloc2 = MagicMock(spec=PmoResourceAllocation)
        mock_alloc2.resource_id = 1
        mock_alloc2.allocation_percent = 60
        
        mock_query.filter.return_value.all.return_value = [mock_alloc1, mock_alloc2]
        
        # 标准工作负荷设为100小时，60%+60% = 120小时，超负荷
        result = self.service._calculate_overloaded_resources(standard_workload=100)
        
        self.assertEqual(result, 1)

    def test_calculate_overloaded_resources_no_percent(self):
        """测试计算超负荷资源 - 无分配百分比"""
        mock_query = self.db.query.return_value
        
        mock_alloc = MagicMock(spec=PmoResourceAllocation)
        mock_alloc.resource_id = 1
        mock_alloc.allocation_percent = None  # 无百分比
        
        mock_query.filter.return_value.all.return_value = [mock_alloc]
        
        result = self.service._calculate_overloaded_resources()
        
        # 无分配百分比，不计入工时
        self.assertEqual(result, 0)

    def test_get_resources_by_department(self):
        """测试按部门统计资源"""
        mock_query = self.db.query.return_value
        
        mock_dept = MagicMock(spec=Department)
        mock_dept.id = 1
        mock_dept.name = "研发部"
        
        mock_query.all.return_value = [mock_dept]
        
        # Mock User count (dept_users)
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.count.return_value = 10
        
        # Mock PmoResourceAllocation count (dept_allocated)
        mock_alloc_query = MagicMock()
        mock_alloc_query.join.return_value.filter.return_value.distinct.return_value.count.return_value = 6
        
        # db.query的第二次调用返回User查询，第三次返回PmoResourceAllocation查询
        self.db.query.side_effect = [
            mock_query,  # Department.all()
            mock_user_query,  # User count
            mock_alloc_query,  # PmoResourceAllocation count
        ]
        
        result = self.service._get_resources_by_department()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["department_name"], "研发部")
        self.assertEqual(result[0]["total_resources"], 10)
        self.assertEqual(result[0]["allocated_resources"], 6)
        self.assertEqual(result[0]["available_resources"], 4)

    # ========== 辅助方法 ==========

    def _create_mock_risk(self, risk_no: str, risk_level: str) -> MagicMock:
        """创建mock风险对象"""
        mock_risk = MagicMock(spec=PmoProjectRisk)
        mock_risk.id = 1
        mock_risk.project_id = 101
        mock_risk.risk_no = risk_no
        mock_risk.risk_category = "TECHNICAL"
        mock_risk.risk_name = "测试风险"
        mock_risk.description = "风险描述"
        mock_risk.probability = "HIGH"
        mock_risk.impact = "HIGH"
        mock_risk.risk_level = risk_level
        mock_risk.response_strategy = "MITIGATE"
        mock_risk.response_plan = "缓解计划"
        mock_risk.owner_id = 1
        mock_risk.owner_name = "张三"
        mock_risk.status = "ACTIVE"
        mock_risk.follow_up_date = date.today()
        mock_risk.last_update = "2026-02-21"  # 使用字符串
        mock_risk.trigger_condition = None
        mock_risk.is_triggered = False
        mock_risk.triggered_date = None
        mock_risk.closed_date = None
        mock_risk.closed_reason = None
        mock_risk.created_at = datetime.now()
        mock_risk.updated_at = datetime.now()
        return mock_risk


if __name__ == "__main__":
    unittest.main()

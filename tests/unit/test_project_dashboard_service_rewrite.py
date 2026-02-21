# -*- coding: utf-8 -*-
"""
项目仪表盘服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（db.query, db.add等数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from datetime import date, datetime
from decimal import Decimal

from app.services.project_dashboard_service import (
    build_basic_info,
    calculate_progress_stats,
    calculate_cost_stats,
    calculate_task_stats,
    calculate_milestone_stats,
    calculate_risk_stats,
    calculate_issue_stats,
    calculate_resource_usage,
    get_recent_activities,
    calculate_key_metrics,
)


class TestBuildBasicInfo(unittest.TestCase):
    """测试构建项目基本信息"""

    def test_build_basic_info_complete(self):
        """测试完整项目信息"""
        project = Mock()
        project.project_code = "PRJ001"
        project.project_name = "测试项目"
        project.customer_name = "测试客户"
        project.pm_name = "张三"
        project.stage = "S2"
        project.status = "ST02"
        project.health = "H1"
        project.progress_pct = Decimal("65.5")
        project.planned_start_date = date(2024, 1, 1)
        project.planned_end_date = date(2024, 6, 30)
        project.actual_start_date = date(2024, 1, 5)
        project.actual_end_date = None
        project.contract_amount = Decimal("1000000.00")
        project.budget_amount = Decimal("800000.00")

        result = build_basic_info(project)

        self.assertEqual(result["project_code"], "PRJ001")
        self.assertEqual(result["project_name"], "测试项目")
        self.assertEqual(result["customer_name"], "测试客户")
        self.assertEqual(result["pm_name"], "张三")
        self.assertEqual(result["stage"], "S2")
        self.assertEqual(result["status"], "ST02")
        self.assertEqual(result["health"], "H1")
        self.assertEqual(result["progress_pct"], 65.5)
        self.assertEqual(result["planned_start_date"], "2024-01-01")
        self.assertEqual(result["planned_end_date"], "2024-06-30")
        self.assertEqual(result["actual_start_date"], "2024-01-05")
        self.assertIsNone(result["actual_end_date"])
        self.assertEqual(result["contract_amount"], 1000000.0)
        self.assertEqual(result["budget_amount"], 800000.0)

    def test_build_basic_info_minimal(self):
        """测试最小项目信息（使用默认值）"""
        project = Mock()
        project.project_code = "PRJ002"
        project.project_name = "最小项目"
        project.customer_name = "客户B"
        project.pm_name = "李四"
        project.stage = None
        project.status = None
        project.health = None
        project.progress_pct = None
        project.planned_start_date = None
        project.planned_end_date = None
        project.actual_start_date = None
        project.actual_end_date = None
        project.contract_amount = None
        project.budget_amount = None

        result = build_basic_info(project)

        self.assertEqual(result["stage"], "S1")  # 默认值
        self.assertEqual(result["status"], "ST01")  # 默认值
        self.assertEqual(result["health"], "H1")  # 默认值
        self.assertEqual(result["progress_pct"], 0.0)
        self.assertIsNone(result["planned_start_date"])
        self.assertIsNone(result["planned_end_date"])
        self.assertEqual(result["contract_amount"], 0.0)
        self.assertEqual(result["budget_amount"], 0.0)


class TestCalculateProgressStats(unittest.TestCase):
    """测试计算进度统计"""

    def test_calculate_progress_on_schedule(self):
        """测试按计划进行的项目"""
        project = Mock()
        project.progress_pct = Decimal("50.0")
        project.planned_start_date = date(2024, 1, 1)
        project.planned_end_date = date(2024, 12, 31)  # 365天
        project.stage = "S2"

        today = date(2024, 7, 1)  # 进行到第182天，计划进度应约为50%

        result = calculate_progress_stats(project, today)

        self.assertEqual(result["actual_progress"], 50.0)
        # (182 / 365) * 100 = 50.137，允许小误差
        self.assertGreater(result["plan_progress"], 49.0)
        self.assertLess(result["plan_progress"], 51.0)
        # 进度偏差应该接近0
        self.assertAlmostEqual(result["progress_deviation"], 0.0, delta=1.0)
        self.assertEqual(result["time_deviation_days"], -183)  # 未到结束日期
        self.assertFalse(result["is_delayed"])

    def test_calculate_progress_ahead_of_schedule(self):
        """测试进度超前的项目"""
        project = Mock()
        project.progress_pct = Decimal("70.0")
        project.planned_start_date = date(2024, 1, 1)
        project.planned_end_date = date(2024, 12, 31)
        project.stage = "S2"

        today = date(2024, 7, 1)  # 计划进度约50%，实际70%

        result = calculate_progress_stats(project, today)

        self.assertEqual(result["actual_progress"], 70.0)
        self.assertGreater(result["progress_deviation"], 0)  # 正偏差

    def test_calculate_progress_delayed(self):
        """测试延期的项目"""
        project = Mock()
        project.progress_pct = Decimal("80.0")
        project.planned_start_date = date(2024, 1, 1)
        project.planned_end_date = date(2024, 6, 30)
        project.stage = "S2"

        today = date(2024, 8, 15)  # 已超过结束日期46天

        result = calculate_progress_stats(project, today)

        self.assertEqual(result["time_deviation_days"], 46)
        self.assertTrue(result["is_delayed"])

    def test_calculate_progress_completed_not_delayed(self):
        """测试已完成项目（stage=S9），即使超时也不算延期"""
        project = Mock()
        project.progress_pct = Decimal("100.0")
        project.planned_start_date = date(2024, 1, 1)
        project.planned_end_date = date(2024, 6, 30)
        project.stage = "S9"  # 已完成

        today = date(2024, 8, 15)  # 超过结束日期

        result = calculate_progress_stats(project, today)

        self.assertEqual(result["time_deviation_days"], 46)
        self.assertFalse(result["is_delayed"])  # stage=S9不算延期

    def test_calculate_progress_no_dates(self):
        """测试没有日期信息的项目"""
        project = Mock()
        project.progress_pct = Decimal("30.0")
        project.planned_start_date = None
        project.planned_end_date = None
        project.stage = "S1"

        today = date(2024, 7, 1)

        result = calculate_progress_stats(project, today)

        self.assertEqual(result["actual_progress"], 30.0)
        self.assertEqual(result["plan_progress"], 0)
        self.assertEqual(result["progress_deviation"], 30.0)

    def test_calculate_progress_zero_duration(self):
        """测试开始日期等于结束日期（总天数为0）"""
        project = Mock()
        project.progress_pct = Decimal("50.0")
        project.planned_start_date = date(2024, 7, 1)
        project.planned_end_date = date(2024, 7, 1)
        project.stage = "S1"

        today = date(2024, 7, 1)

        result = calculate_progress_stats(project, today)

        self.assertEqual(result["plan_progress"], 0)  # 总天数为0

    def test_calculate_progress_before_start(self):
        """测试项目还未开始"""
        project = Mock()
        project.progress_pct = Decimal("0.0")
        project.planned_start_date = date(2024, 8, 1)
        project.planned_end_date = date(2024, 12, 31)
        project.stage = "S1"

        today = date(2024, 7, 1)  # 在开始日期之前

        result = calculate_progress_stats(project, today)

        self.assertEqual(result["plan_progress"], 0)  # 应该为0（max(0, ...)）


class TestCalculateCostStats(unittest.TestCase):
    """测试计算成本统计"""

    @patch('app.services.cost_service.CostService')
    def test_calculate_cost_stats(self, mock_cost_service_class):
        """测试成本统计（mock CostService）"""
        mock_db = Mock()
        mock_service_instance = Mock()
        mock_service_instance.calculate_cost_stats.return_value = {
            "total_cost": 50000.0,
            "budget_amount": 100000.0,
            "cost_variance": -50000.0,
            "cost_variance_rate": -50.0,
        }
        mock_cost_service_class.return_value = mock_service_instance

        result = calculate_cost_stats(mock_db, 1, 100000.0)

        mock_cost_service_class.assert_called_once_with(mock_db)
        mock_service_instance.calculate_cost_stats.assert_called_once_with(1, 100000.0)
        self.assertEqual(result["total_cost"], 50000.0)
        self.assertEqual(result["cost_variance_rate"], -50.0)


class TestCalculateTaskStats(unittest.TestCase):
    """测试计算任务统计"""

    def test_calculate_task_stats_normal(self):
        """测试正常任务统计"""
        mock_db = Mock()

        # Mock total count
        mock_total_result = Mock()
        mock_total_result.total = 20
        
        # Mock status counts
        mock_status_counts = [
            ("COMPLETED", 8),
            ("IN_PROGRESS", 5),
            ("PENDING", 4),
            ("ACCEPTED", 2),
            ("BLOCKED", 1),
        ]
        
        # Mock average progress
        mock_avg_result = Mock()
        mock_avg_result.avg = Decimal("62.5")

        # Setup query chain
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        
        # first() calls for total and avg
        # all() call for status counts
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.first.side_effect = [mock_total_result, mock_avg_result]
        mock_query.all.return_value = mock_status_counts

        result = calculate_task_stats(mock_db, 1)

        self.assertEqual(result["total"], 20)
        self.assertEqual(result["completed"], 8)
        self.assertEqual(result["in_progress"], 5)
        self.assertEqual(result["pending"], 6)  # PENDING + ACCEPTED
        self.assertEqual(result["blocked"], 1)
        self.assertEqual(result["completion_rate"], 40.0)  # 8/20
        self.assertEqual(result["avg_progress"], 62.5)

    def test_calculate_task_stats_no_tasks(self):
        """测试没有任务的情况"""
        mock_db = Mock()

        mock_total_result = Mock()
        mock_total_result.total = 0
        
        mock_avg_result = Mock()
        mock_avg_result.avg = None

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.first.side_effect = [mock_total_result, mock_avg_result]
        mock_query.all.return_value = []

        result = calculate_task_stats(mock_db, 1)

        self.assertEqual(result["total"], 0)
        self.assertEqual(result["completed"], 0)
        self.assertEqual(result["completion_rate"], 0)
        self.assertEqual(result["avg_progress"], 0.0)

    def test_calculate_task_stats_all_completed(self):
        """测试全部完成的情况"""
        mock_db = Mock()

        mock_total_result = Mock()
        mock_total_result.total = 10
        
        mock_status_counts = [("COMPLETED", 10)]
        
        mock_avg_result = Mock()
        mock_avg_result.avg = Decimal("100.0")

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.first.side_effect = [mock_total_result, mock_avg_result]
        mock_query.all.return_value = mock_status_counts

        result = calculate_task_stats(mock_db, 1)

        self.assertEqual(result["total"], 10)
        self.assertEqual(result["completed"], 10)
        self.assertEqual(result["completion_rate"], 100.0)


class TestCalculateMilestoneStats(unittest.TestCase):
    """测试计算里程碑统计"""

    def test_calculate_milestone_stats_normal(self):
        """测试正常里程碑统计"""
        mock_db = Mock()
        today = date(2024, 7, 1)

        mock_total_result = Mock()
        mock_total_result.total = 10

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_total_result
        mock_query.scalar.side_effect = [3, 2, 5]  # completed, overdue, upcoming

        result = calculate_milestone_stats(mock_db, 1, today)

        self.assertEqual(result["total"], 10)
        self.assertEqual(result["completed"], 3)
        self.assertEqual(result["overdue"], 2)
        self.assertEqual(result["upcoming"], 5)
        self.assertEqual(result["completion_rate"], 30.0)

    def test_calculate_milestone_stats_no_milestones(self):
        """测试没有里程碑的情况"""
        mock_db = Mock()
        today = date(2024, 7, 1)

        mock_total_result = Mock()
        mock_total_result.total = 0

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_total_result
        mock_query.scalar.side_effect = [0, 0, 0]

        result = calculate_milestone_stats(mock_db, 1, today)

        self.assertEqual(result["total"], 0)
        self.assertEqual(result["completion_rate"], 0)

    def test_calculate_milestone_stats_all_completed(self):
        """测试全部完成的情况"""
        mock_db = Mock()
        today = date(2024, 7, 1)

        mock_total_result = Mock()
        mock_total_result.total = 5

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_total_result
        mock_query.scalar.side_effect = [5, 0, 0]

        result = calculate_milestone_stats(mock_db, 1, today)

        self.assertEqual(result["completion_rate"], 100.0)

    def test_calculate_milestone_stats_with_none_counts(self):
        """测试scalar返回None的情况"""
        mock_db = Mock()
        today = date(2024, 7, 1)

        mock_total_result = Mock()
        mock_total_result.total = 5

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_total_result
        mock_query.scalar.side_effect = [None, None, None]  # All None

        result = calculate_milestone_stats(mock_db, 1, today)

        self.assertEqual(result["completed"], 0)
        self.assertEqual(result["overdue"], 0)
        self.assertEqual(result["upcoming"], 0)


class TestCalculateRiskStats(unittest.TestCase):
    """测试计算风险统计"""

    @patch('app.services.project_dashboard_service.PmoProjectRisk', None)
    def test_calculate_risk_stats_model_not_available(self):
        """测试风险模型不可用的情况"""
        mock_db = Mock()
        result = calculate_risk_stats(mock_db, 1)
        self.assertIsNone(result)

    @patch('app.services.project_dashboard_service.PmoProjectRisk')
    def test_calculate_risk_stats_normal(self, mock_risk_model):
        """测试正常风险统计"""
        mock_db = Mock()

        # Mock risks
        mock_risks = [
            Mock(risk_level="HIGH", status="OPEN"),
            Mock(risk_level="CRITICAL", status="OPEN"),
            Mock(risk_level="MEDIUM", status="OPEN"),
            Mock(risk_level="HIGH", status="CLOSED"),
            Mock(risk_level="LOW", status="OPEN"),
        ]

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_risks

        result = calculate_risk_stats(mock_db, 1)

        self.assertEqual(result["total"], 5)
        self.assertEqual(result["open"], 4)  # 不包括CLOSED
        self.assertEqual(result["high"], 1)  # HIGH且非CLOSED
        self.assertEqual(result["critical"], 1)  # CRITICAL且非CLOSED

    @patch('app.services.project_dashboard_service.PmoProjectRisk')
    def test_calculate_risk_stats_no_risks(self, mock_risk_model):
        """测试没有风险的情况"""
        mock_db = Mock()

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = calculate_risk_stats(mock_db, 1)

        self.assertEqual(result["total"], 0)
        self.assertEqual(result["open"], 0)
        self.assertEqual(result["high"], 0)
        self.assertEqual(result["critical"], 0)

    @patch('app.services.project_dashboard_service.PmoProjectRisk')
    def test_calculate_risk_stats_exception(self, mock_risk_model):
        """测试异常情况"""
        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database error")

        result = calculate_risk_stats(mock_db, 1)

        self.assertIsNone(result)


class TestCalculateIssueStats(unittest.TestCase):
    """测试计算问题统计"""

    @patch('app.services.project_dashboard_service.Issue', None)
    def test_calculate_issue_stats_model_not_available(self):
        """测试问题模型不可用的情况"""
        mock_db = Mock()
        result = calculate_issue_stats(mock_db, 1)
        self.assertIsNone(result)

    @patch('app.services.project_dashboard_service.Issue')
    def test_calculate_issue_stats_normal(self, mock_issue_model):
        """测试正常问题统计"""
        mock_db = Mock()

        mock_issues = [
            Mock(status="OPEN", is_blocking=True),
            Mock(status="OPEN", is_blocking=False),
            Mock(status="PROCESSING", is_blocking=True),
            Mock(status="PROCESSING", is_blocking=False),
            Mock(status="CLOSED", is_blocking=False),
        ]

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_issues

        result = calculate_issue_stats(mock_db, 1)

        self.assertEqual(result["total"], 5)
        self.assertEqual(result["open"], 2)
        self.assertEqual(result["processing"], 2)
        self.assertEqual(result["blocking"], 2)

    @patch('app.services.project_dashboard_service.Issue')
    def test_calculate_issue_stats_no_issues(self, mock_issue_model):
        """测试没有问题的情况"""
        mock_db = Mock()

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = calculate_issue_stats(mock_db, 1)

        self.assertEqual(result["total"], 0)
        self.assertEqual(result["open"], 0)
        self.assertEqual(result["processing"], 0)
        self.assertEqual(result["blocking"], 0)

    @patch('app.services.project_dashboard_service.Issue')
    def test_calculate_issue_stats_exception(self, mock_issue_model):
        """测试异常情况"""
        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database error")

        result = calculate_issue_stats(mock_db, 1)

        self.assertIsNone(result)


class TestCalculateResourceUsage(unittest.TestCase):
    """测试计算资源使用"""

    @patch('app.services.project_dashboard_service.PmoResourceAllocation', None)
    def test_calculate_resource_usage_model_not_available(self):
        """测试资源模型不可用的情况"""
        mock_db = Mock()
        result = calculate_resource_usage(mock_db, 1)
        self.assertIsNone(result)

    @patch('app.services.project_dashboard_service.PmoResourceAllocation')
    def test_calculate_resource_usage_normal(self, mock_resource_model):
        """测试正常资源使用统计"""
        mock_db = Mock()

        mock_allocations = [
            Mock(department_name="研发部", role="开发工程师"),
            Mock(department_name="研发部", role="测试工程师"),
            Mock(department_name="产品部", role="产品经理"),
            Mock(department_name=None, role="顾问"),
        ]

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_allocations

        result = calculate_resource_usage(mock_db, 1)

        self.assertEqual(result["total_allocations"], 4)
        self.assertEqual(result["by_department"]["研发部"], 2)
        self.assertEqual(result["by_department"]["产品部"], 1)
        self.assertEqual(result["by_department"]["未分配"], 1)
        self.assertEqual(result["by_role"]["开发工程师"], 1)
        self.assertEqual(result["by_role"]["顾问"], 1)

    @patch('app.services.project_dashboard_service.PmoResourceAllocation')
    def test_calculate_resource_usage_no_allocations(self, mock_resource_model):
        """测试没有资源分配的情况"""
        mock_db = Mock()

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = calculate_resource_usage(mock_db, 1)

        self.assertIsNone(result)

    @patch('app.services.project_dashboard_service.PmoResourceAllocation')
    def test_calculate_resource_usage_exception(self, mock_resource_model):
        """测试异常情况"""
        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database error")

        result = calculate_resource_usage(mock_db, 1)

        self.assertIsNone(result)


class TestGetRecentActivities(unittest.TestCase):
    """测试获取最近活动"""

    def test_get_recent_activities_normal(self):
        """测试正常活动获取"""
        mock_db = Mock()

        # Mock status logs
        mock_status_logs = [
            Mock(
                changed_at=datetime(2024, 7, 5, 10, 0, 0),
                old_status="ST01",
                new_status="ST02",
                change_reason="项目启动"
            ),
            Mock(
                changed_at=datetime(2024, 7, 3, 14, 30, 0),
                old_status="ST02",
                new_status="ST03",
                change_reason="进入执行阶段"
            ),
        ]

        # Mock milestones
        mock_milestones = [
            Mock(
                actual_date=date(2024, 7, 4),
                milestone_name="需求评审完成",
                status="COMPLETED"
            ),
        ]

        mock_query1 = Mock()
        mock_query2 = Mock()
        
        def query_side_effect(model):
            if model.__name__ == "ProjectStatusLog":
                return mock_query1
            else:  # ProjectMilestone
                return mock_query2
        
        mock_db.query.side_effect = query_side_effect
        
        mock_query1.filter.return_value = mock_query1
        mock_query1.order_by.return_value = mock_query1
        mock_query1.limit.return_value = mock_query1
        mock_query1.all.return_value = mock_status_logs

        mock_query2.filter.return_value = mock_query2
        mock_query2.order_by.return_value = mock_query2
        mock_query2.limit.return_value = mock_query2
        mock_query2.all.return_value = mock_milestones

        result = get_recent_activities(mock_db, 1)

        self.assertLessEqual(len(result), 10)
        self.assertTrue(any(a["type"] == "STATUS_CHANGE" for a in result))
        self.assertTrue(any(a["type"] == "MILESTONE" for a in result))
        
        # 验证排序（按时间倒序）
        times = [a.get("time") for a in result if a.get("time")]
        self.assertEqual(times, sorted(times, reverse=True))

    def test_get_recent_activities_no_activities(self):
        """测试没有活动的情况"""
        mock_db = Mock()

        mock_query1 = Mock()
        mock_query2 = Mock()
        
        def query_side_effect(model):
            if model.__name__ == "ProjectStatusLog":
                return mock_query1
            else:
                return mock_query2
        
        mock_db.query.side_effect = query_side_effect
        
        mock_query1.filter.return_value = mock_query1
        mock_query1.order_by.return_value = mock_query1
        mock_query1.limit.return_value = mock_query1
        mock_query1.all.return_value = []

        mock_query2.filter.return_value = mock_query2
        mock_query2.order_by.return_value = mock_query2
        mock_query2.limit.return_value = mock_query2
        mock_query2.all.return_value = []

        result = get_recent_activities(mock_db, 1)

        self.assertEqual(len(result), 0)

    def test_get_recent_activities_none_timestamps(self):
        """测试时间戳为None的情况"""
        mock_db = Mock()

        mock_status_logs = [
            Mock(
                changed_at=None,
                old_status="ST01",
                new_status="ST02",
                change_reason="测试"
            ),
        ]

        mock_query1 = Mock()
        mock_query2 = Mock()
        
        def query_side_effect(model):
            if model.__name__ == "ProjectStatusLog":
                return mock_query1
            else:
                return mock_query2
        
        mock_db.query.side_effect = query_side_effect
        
        mock_query1.filter.return_value = mock_query1
        mock_query1.order_by.return_value = mock_query1
        mock_query1.limit.return_value = mock_query1
        mock_query1.all.return_value = mock_status_logs

        mock_query2.filter.return_value = mock_query2
        mock_query2.order_by.return_value = mock_query2
        mock_query2.limit.return_value = mock_query2
        mock_query2.all.return_value = []

        result = get_recent_activities(mock_db, 1)

        self.assertIsNone(result[0]["time"])


class TestCalculateKeyMetrics(unittest.TestCase):
    """测试计算关键指标"""

    def test_calculate_key_metrics_healthy_project(self):
        """测试健康项目的指标"""
        project = Mock()
        project.health = "H1"
        project.progress_pct = Decimal("75.0")

        result = calculate_key_metrics(
            project=project,
            progress_deviation=2.0,  # 轻微偏差
            cost_variance_rate=3.0,
            task_completed=15,
            task_total=20
        )

        self.assertEqual(result["health_score"], 100)
        self.assertEqual(result["progress_score"], 75.0)
        self.assertGreater(result["schedule_score"], 90)
        self.assertGreater(result["cost_score"], 90)
        self.assertEqual(result["quality_score"], 75.0)
        self.assertIn("overall_score", result)
        self.assertGreater(result["overall_score"], 80)

    def test_calculate_key_metrics_risky_project(self):
        """测试风险项目的指标"""
        project = Mock()
        project.health = "H3"
        project.progress_pct = Decimal("40.0")

        result = calculate_key_metrics(
            project=project,
            progress_deviation=-15.0,  # 大偏差
            cost_variance_rate=20.0,  # 大成本超支
            task_completed=5,
            task_total=20
        )

        self.assertEqual(result["health_score"], 50)
        self.assertEqual(result["progress_score"], 40.0)
        self.assertLess(result["schedule_score"], 80)
        self.assertLess(result["cost_score"], 70)
        self.assertEqual(result["quality_score"], 25.0)

    def test_calculate_key_metrics_critical_project(self):
        """测试危急项目的指标"""
        project = Mock()
        project.health = "H4"
        project.progress_pct = Decimal("20.0")

        result = calculate_key_metrics(
            project=project,
            progress_deviation=-30.0,
            cost_variance_rate=50.0,
            task_completed=2,
            task_total=30
        )

        self.assertEqual(result["health_score"], 25)
        self.assertLess(result["overall_score"], 50)

    def test_calculate_key_metrics_no_tasks(self):
        """测试没有任务的情况"""
        project = Mock()
        project.health = "H2"
        project.progress_pct = Decimal("50.0")

        result = calculate_key_metrics(
            project=project,
            progress_deviation=0.0,
            cost_variance_rate=0.0,
            task_completed=0,
            task_total=0
        )

        self.assertEqual(result["quality_score"], 100.0)  # 没有任务默认100分

    def test_calculate_key_metrics_small_deviation(self):
        """测试小偏差情况（≤5%）"""
        project = Mock()
        project.health = "H1"
        project.progress_pct = Decimal("50.0")

        result = calculate_key_metrics(
            project=project,
            progress_deviation=3.0,  # ≤5%
            cost_variance_rate=2.0,
            task_completed=10,
            task_total=10
        )

        # 小偏差使用简单公式: 100 - abs(deviation)
        expected_schedule_score = 100 - abs(3.0)
        self.assertEqual(result["schedule_score"], expected_schedule_score)

    def test_calculate_key_metrics_large_deviation(self):
        """测试大偏差情况（>5%）"""
        project = Mock()
        project.health = "H1"
        project.progress_pct = Decimal("50.0")

        result = calculate_key_metrics(
            project=project,
            progress_deviation=10.0,  # >5%
            cost_variance_rate=8.0,
            task_completed=10,
            task_total=10
        )

        # 大偏差使用加倍惩罚: 100 - abs(deviation) * 2
        expected_schedule_score = max(0, 100 - abs(10.0) * 2)
        self.assertEqual(result["schedule_score"], expected_schedule_score)

    def test_calculate_key_metrics_negative_scores(self):
        """测试确保分数不会为负数"""
        project = Mock()
        project.health = "H1"
        project.progress_pct = Decimal("10.0")

        result = calculate_key_metrics(
            project=project,
            progress_deviation=-80.0,  # 极大偏差
            cost_variance_rate=100.0,
            task_completed=1,
            task_total=100
        )

        # 确保所有分数≥0
        self.assertGreaterEqual(result["schedule_score"], 0)
        self.assertGreaterEqual(result["cost_score"], 0)


if __name__ == "__main__":
    unittest.main()

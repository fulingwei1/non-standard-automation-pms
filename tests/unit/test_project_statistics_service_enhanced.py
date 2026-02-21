# -*- coding: utf-8 -*-
"""
项目统计服务增强单元测试

测试策略：
1. Mock外部依赖（数据库session）
2. 构造真实的数据对象让业务逻辑真正执行
3. 覆盖所有核心方法和边界情况
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


# ==============================================================================
# 测试辅助类和数据构造
# ==============================================================================


class MockProject:
    """模拟Project对象"""

    def __init__(
        self,
        id=1,
        project_name="测试项目",
        status="进行中",
        stage="开发阶段",
        health="健康",
        pm_id=100,
        pm_name="张三",
        customer_id=1,
        customer_name="客户A",
        contract_amount=100000.0,
        budget_amount=50000.0,
        progress_pct=60.0,
        created_at=None,
    ):
        self.id = id
        self.project_name = project_name
        self.status = status
        self.stage = stage
        self.health = health
        self.pm_id = pm_id
        self.pm_name = pm_name
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.contract_amount = contract_amount
        self.budget_amount = budget_amount
        self.progress_pct = progress_pct
        self.created_at = created_at or datetime.now()


class MockProjectCost:
    """模拟ProjectCost对象"""

    def __init__(
        self,
        id=1,
        project_id=1,
        cost_type="人力成本",
        amount=10000.0,
        created_at=None,
    ):
        self.id = id
        self.project_id = project_id
        self.cost_type = cost_type
        self.amount = amount
        self.created_at = created_at or datetime.now()


class MockTimesheet:
    """模拟Timesheet对象"""

    def __init__(
        self,
        id=1,
        project_id=1,
        user_id=1,
        hours=8.0,
        work_date=None,
        status="APPROVED",
        overtime_type="NORMAL",
    ):
        self.id = id
        self.project_id = project_id
        self.user_id = user_id
        self.hours = hours
        self.work_date = work_date or date.today()
        self.status = status
        self.overtime_type = overtime_type


class MockUser:
    """模拟User对象"""

    def __init__(self, id=1, username="testuser", real_name="测试用户"):
        self.id = id
        self.username = username
        self.real_name = real_name


class MockWorkLog:
    """模拟WorkLog对象"""

    def __init__(self, id=1, user_id=1, work_date=None):
        self.id = id
        self.user_id = user_id
        self.work_date = work_date or date.today()


class MockWorkLogMention:
    """模拟WorkLogMention对象"""

    def __init__(self, work_log_id=1, mention_type="PROJECT", mention_id=1):
        self.work_log_id = work_log_id
        self.mention_type = mention_type
        self.mention_id = mention_id


class MockQuery:
    """模拟SQLAlchemy Query对象"""

    def __init__(self, data=None):
        self._data = data or []
        self._filters = []
        self._entities = []
        self._group_by_fields = []

    def all(self):
        return self._data

    def first(self):
        return self._data[0] if self._data else None

    def filter(self, *args):
        """记录过滤条件，返回self以支持链式调用"""
        self._filters.extend(args)
        return self

    def with_entities(self, *args):
        """记录实体字段，返回self"""
        self._entities = args
        return self

    def group_by(self, *args):
        """记录分组字段，返回self"""
        self._group_by_fields = args
        return self

    def scalar(self):
        """返回标量值，用于聚合函数"""
        # 根据entities的类型模拟返回值
        if self._data:
            return sum(getattr(item, "amount", 0) for item in self._data)
        return None

    def join(self, *args, **kwargs):
        """Mock join操作"""
        return self


# ==============================================================================
# 顶层函数测试
# ==============================================================================


class TestCalculateStatusStatistics(unittest.TestCase):
    """测试计算状态统计"""

    def test_empty_query(self):
        """测试空查询"""
        query = MockQuery([])
        result = calculate_status_statistics(query)
        self.assertEqual(result, {})

    def test_single_status(self):
        """测试单一状态"""
        projects = [MockProject(status="进行中")]
        query = MockQuery(projects)
        result = calculate_status_statistics(query)
        self.assertEqual(result, {"进行中": 1})

    def test_multiple_statuses(self):
        """测试多个状态"""
        projects = [
            MockProject(status="进行中"),
            MockProject(status="进行中"),
            MockProject(status="已完成"),
            MockProject(status="暂停"),
        ]
        query = MockQuery(projects)
        result = calculate_status_statistics(query)
        self.assertEqual(result, {"进行中": 2, "已完成": 1, "暂停": 1})

    def test_none_status(self):
        """测试空状态"""
        projects = [MockProject(status=None), MockProject(status="进行中")]
        query = MockQuery(projects)
        result = calculate_status_statistics(query)
        self.assertEqual(result, {"进行中": 1})


class TestCalculateStageStatistics(unittest.TestCase):
    """测试计算阶段统计"""

    def test_empty_query(self):
        """测试空查询"""
        query = MockQuery([])
        result = calculate_stage_statistics(query)
        self.assertEqual(result, {})

    def test_multiple_stages(self):
        """测试多个阶段"""
        projects = [
            MockProject(stage="需求分析"),
            MockProject(stage="开发阶段"),
            MockProject(stage="开发阶段"),
            MockProject(stage="测试阶段"),
        ]
        query = MockQuery(projects)
        result = calculate_stage_statistics(query)
        self.assertEqual(result, {"需求分析": 1, "开发阶段": 2, "测试阶段": 1})


class TestCalculateHealthStatistics(unittest.TestCase):
    """测试计算健康度统计"""

    def test_empty_query(self):
        """测试空查询"""
        query = MockQuery([])
        result = calculate_health_statistics(query)
        self.assertEqual(result, {})

    def test_multiple_health_levels(self):
        """测试多个健康度"""
        projects = [
            MockProject(health="健康"),
            MockProject(health="健康"),
            MockProject(health="警告"),
            MockProject(health="风险"),
        ]
        query = MockQuery(projects)
        result = calculate_health_statistics(query)
        self.assertEqual(result, {"健康": 2, "警告": 1, "风险": 1})


class TestCalculatePmStatistics(unittest.TestCase):
    """测试计算项目经理统计"""

    def test_empty_query(self):
        """测试空查询"""
        query = MockQuery([])
        result = calculate_pm_statistics(query)
        self.assertEqual(result, [])

    def test_single_pm(self):
        """测试单个PM"""
        projects = [MockProject(pm_id=100, pm_name="张三")]
        query = MockQuery(projects)
        result = calculate_pm_statistics(query)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["pm_id"], 100)
        self.assertEqual(result[0]["pm_name"], "张三")
        self.assertEqual(result[0]["count"], 1)

    def test_multiple_pms(self):
        """测试多个PM"""
        projects = [
            MockProject(pm_id=100, pm_name="张三"),
            MockProject(pm_id=100, pm_name="张三"),
            MockProject(pm_id=200, pm_name="李四"),
        ]
        query = MockQuery(projects)
        result = calculate_pm_statistics(query)
        self.assertEqual(len(result), 2)
        pm_counts = {r["pm_id"]: r["count"] for r in result}
        self.assertEqual(pm_counts[100], 2)
        self.assertEqual(pm_counts[200], 1)

    def test_none_pm(self):
        """测试空PM"""
        projects = [MockProject(pm_id=None), MockProject(pm_id=100, pm_name="张三")]
        query = MockQuery(projects)
        result = calculate_pm_statistics(query)
        self.assertEqual(len(result), 1)


class TestCalculateCustomerStatistics(unittest.TestCase):
    """测试计算客户统计"""

    def test_empty_query(self):
        """测试空查询"""
        query = MockQuery([])
        result = calculate_customer_statistics(query)
        self.assertEqual(result, [])

    def test_single_customer(self):
        """测试单个客户"""
        projects = [
            MockProject(customer_id=1, customer_name="客户A", contract_amount=100000)
        ]
        query = MockQuery(projects)
        result = calculate_customer_statistics(query)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["customer_id"], 1)
        self.assertEqual(result[0]["customer_name"], "客户A")
        self.assertEqual(result[0]["count"], 1)
        self.assertEqual(result[0]["total_amount"], 100000.0)

    def test_multiple_customers(self):
        """测试多个客户"""
        projects = [
            MockProject(customer_id=1, customer_name="客户A", contract_amount=100000),
            MockProject(customer_id=1, customer_name="客户A", contract_amount=50000),
            MockProject(customer_id=2, customer_name="客户B", contract_amount=80000),
        ]
        query = MockQuery(projects)
        result = calculate_customer_statistics(query)
        self.assertEqual(len(result), 2)
        customer_data = {r["customer_id"]: r for r in result}
        self.assertEqual(customer_data[1]["count"], 2)
        self.assertEqual(customer_data[1]["total_amount"], 150000.0)
        self.assertEqual(customer_data[2]["count"], 1)
        self.assertEqual(customer_data[2]["total_amount"], 80000.0)

    def test_none_customer(self):
        """测试空客户"""
        projects = [MockProject(customer_id=None, customer_name=None)]
        query = MockQuery(projects)
        result = calculate_customer_statistics(query)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["customer_name"], "未知客户")


class TestCalculateMonthlyStatistics(unittest.TestCase):
    """测试计算月度统计"""

    def test_empty_query(self):
        """测试空查询"""
        query = MockQuery([])
        result = calculate_monthly_statistics(query)
        self.assertEqual(result, [])

    def test_single_month(self):
        """测试单个月份"""
        created_at = datetime(2024, 1, 15)
        projects = [
            MockProject(contract_amount=100000, created_at=created_at),
            MockProject(contract_amount=50000, created_at=created_at),
        ]
        query = MockQuery(projects)
        result = calculate_monthly_statistics(query)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["year"], 2024)
        self.assertEqual(result[0]["month"], 1)
        self.assertEqual(result[0]["month_label"], "2024-01")
        self.assertEqual(result[0]["count"], 2)
        self.assertEqual(result[0]["total_amount"], 150000.0)

    def test_multiple_months_sorted(self):
        """测试多个月份排序"""
        projects = [
            MockProject(contract_amount=100000, created_at=datetime(2024, 3, 1)),
            MockProject(contract_amount=50000, created_at=datetime(2024, 1, 1)),
            MockProject(contract_amount=80000, created_at=datetime(2024, 2, 1)),
        ]
        query = MockQuery(projects)
        result = calculate_monthly_statistics(query)
        self.assertEqual(len(result), 3)
        # 验证排序
        self.assertEqual(result[0]["month"], 1)
        self.assertEqual(result[1]["month"], 2)
        self.assertEqual(result[2]["month"], 3)


class TestBuildProjectStatistics(unittest.TestCase):
    """测试构建综合统计数据"""

    def test_basic_statistics(self):
        """测试基础统计"""
        projects = [
            MockProject(
                status="进行中", stage="开发", health="健康", progress_pct=60.0
            ),
            MockProject(
                status="进行中", stage="测试", health="健康", progress_pct=80.0
            ),
        ]
        query = MockQuery(projects)
        db = Mock()

        result = build_project_statistics(db, query)

        self.assertEqual(result["total"], 2)
        self.assertEqual(result["average_progress"], 70.0)
        self.assertIn("by_status", result)
        self.assertIn("by_stage", result)
        self.assertIn("by_health", result)
        self.assertIn("by_pm", result)

    def test_with_customer_grouping(self):
        """测试按客户分组"""
        projects = [MockProject(customer_id=1, customer_name="客户A")]
        query = MockQuery(projects)
        db = Mock()

        result = build_project_statistics(db, query, group_by="customer")

        self.assertIn("by_customer", result)
        self.assertEqual(len(result["by_customer"]), 1)

    def test_with_month_grouping(self):
        """测试按月份分组"""
        projects = [MockProject(created_at=datetime(2024, 1, 1))]
        query = MockQuery(projects)
        db = Mock()

        result = build_project_statistics(db, query, group_by="month")

        self.assertIn("by_month", result)


# ==============================================================================
# 基类测试
# ==============================================================================


class TestProjectStatisticsServiceBase(unittest.TestCase):
    """测试统计服务基类"""

    def setUp(self):
        """设置测试"""
        self.db_mock = MagicMock()

        # 创建具体实现类用于测试抽象基类
        class ConcreteService(ProjectStatisticsServiceBase):
            def get_model(self):
                return MockProject

            def get_project_id_field(self):
                return "id"

            def get_summary(self, project_id, start_date=None, end_date=None):
                return {}

        self.service = ConcreteService(self.db_mock)

    def test_get_project_success(self):
        """测试成功获取项目"""
        project = MockProject(id=1, project_name="测试项目")
        query_mock = MockQuery([project])
        self.db_mock.query.return_value = query_mock

        result = self.service.get_project(1)

        self.assertEqual(result.id, 1)
        self.assertEqual(result.project_name, "测试项目")

    def test_get_project_not_found(self):
        """测试项目不存在"""
        query_mock = MockQuery([])
        self.db_mock.query.return_value = query_mock

        with self.assertRaises(ValueError) as context:
            self.service.get_project(999)

        self.assertIn("项目不存在", str(context.exception))

    def test_build_base_query(self):
        """测试构建基础查询"""
        query_mock = MockQuery()
        self.db_mock.query.return_value = query_mock

        # 创建一个带有id属性的mock类
        MockModel = type('MockModel', (), {'id': 1})
        
        with patch.object(self.service, "get_model", return_value=MockModel):
            result = self.service.build_base_query(1)
            self.assertIsNotNone(result)

    def test_apply_date_filter_with_both_dates(self):
        """测试应用日期范围筛选"""
        query = MockQuery()
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)

        result = self.service.apply_date_filter(
            query, start_date, end_date, "created_at"
        )

        # 验证filter被调用
        self.assertIsNotNone(result)

    def test_apply_date_filter_start_only(self):
        """测试仅应用开始日期"""
        query = MockQuery()
        start_date = date(2024, 1, 1)

        result = self.service.apply_date_filter(query, start_date, None, "created_at")

        self.assertIsNotNone(result)

    def test_apply_date_filter_no_dates(self):
        """测试无日期筛选"""
        query = MockQuery()

        result = self.service.apply_date_filter(query, None, None, "created_at")

        self.assertEqual(result, query)


# ==============================================================================
# 成本统计服务测试
# ==============================================================================


class TestCostStatisticsService(unittest.TestCase):
    """测试成本统计服务"""

    def setUp(self):
        """设置测试"""
        self.db_mock = MagicMock()
        self.service = CostStatisticsService(self.db_mock)

    def test_get_model(self):
        """测试获取模型"""
        from app.models.project import ProjectCost

        model = self.service.get_model()
        self.assertEqual(model, ProjectCost)

    def test_get_project_id_field(self):
        """测试获取项目ID字段"""
        field = self.service.get_project_id_field()
        self.assertEqual(field, "project_id")

    @patch("app.services.project_statistics_service.CostStatisticsService.get_project")
    @patch(
        "app.services.project_statistics_service.CostStatisticsService.build_base_query"
    )
    @patch(
        "app.services.project_statistics_service.CostStatisticsService.apply_date_filter"
    )
    @patch(
        "app.services.project_statistics_service.CostStatisticsService.group_by_field"
    )
    @patch(
        "app.services.project_statistics_service.CostStatisticsService.calculate_total"
    )
    def test_get_summary_basic(
        self,
        mock_total,
        mock_group,
        mock_filter,
        mock_query,
        mock_project,
    ):
        """测试基础成本汇总"""
        # 设置mock返回值
        project = MockProject(
            id=1, project_name="测试项目", budget_amount=50000.0, contract_amount=100000
        )
        mock_project.return_value = project

        query = MockQuery()
        mock_query.return_value = query
        mock_filter.return_value = query

        mock_group.return_value = {"人力成本": 20000.0, "设备成本": 10000.0}
        mock_total.return_value = 30000.0

        result = self.service.get_summary(1)

        self.assertEqual(result["project_id"], 1)
        self.assertEqual(result["project_name"], "测试项目")
        self.assertEqual(result["total_cost"], 30000.0)
        self.assertEqual(result["budget"], 50000.0)
        self.assertEqual(result["budget_used_pct"], 60.0)
        self.assertIn("by_type", result)

    @patch("app.services.project_statistics_service.CostStatisticsService.get_project")
    @patch(
        "app.services.project_statistics_service.CostStatisticsService.build_base_query"
    )
    @patch(
        "app.services.project_statistics_service.CostStatisticsService.apply_date_filter"
    )
    @patch(
        "app.services.project_statistics_service.CostStatisticsService.group_by_field"
    )
    @patch(
        "app.services.project_statistics_service.CostStatisticsService.calculate_total"
    )
    def test_get_summary_no_budget(
        self,
        mock_total,
        mock_group,
        mock_filter,
        mock_query,
        mock_project,
    ):
        """测试无预算情况"""
        project = MockProject(id=1, project_name="测试项目", budget_amount=None)
        mock_project.return_value = project

        query = MockQuery()
        mock_query.return_value = query
        mock_filter.return_value = query

        mock_group.return_value = {}
        mock_total.return_value = 10000.0

        result = self.service.get_summary(1)

        self.assertIsNone(result["budget"])
        self.assertIsNone(result["budget_used_pct"])


# ==============================================================================
# 工时统计服务测试
# ==============================================================================


class TestTimesheetStatisticsService(unittest.TestCase):
    """测试工时统计服务"""

    def setUp(self):
        """设置测试"""
        self.db_mock = MagicMock()
        self.service = TimesheetStatisticsService(self.db_mock)

    def test_get_model(self):
        """测试获取模型"""
        from app.models.timesheet import Timesheet

        model = self.service.get_model()
        self.assertEqual(model, Timesheet)

    def test_get_project_id_field(self):
        """测试获取项目ID字段"""
        field = self.service.get_project_id_field()
        self.assertEqual(field, "project_id")

    @patch(
        "app.services.project_statistics_service.TimesheetStatisticsService.get_project"
    )
    @patch(
        "app.services.project_statistics_service.TimesheetStatisticsService.build_base_query"
    )
    @patch(
        "app.services.project_statistics_service.TimesheetStatisticsService.apply_date_filter"
    )
    def test_get_summary_with_data(self, mock_filter, mock_query, mock_project):
        """测试工时汇总（有数据）"""
        project = MockProject(id=1, project_name="测试项目")
        mock_project.return_value = project

        # 创建工时数据
        timesheets = [
            MockTimesheet(
                user_id=1, hours=8.0, work_date=date(2024, 1, 1), status="APPROVED"
            ),
            MockTimesheet(
                user_id=1, hours=6.0, work_date=date(2024, 1, 2), status="APPROVED"
            ),
            MockTimesheet(
                user_id=2, hours=8.0, work_date=date(2024, 1, 1), status="APPROVED"
            ),
        ]

        query = MockQuery(timesheets)
        mock_query.return_value = query
        mock_filter.return_value = query

        # Mock User查询
        user1 = MockUser(id=1, real_name="用户1")
        user2 = MockUser(id=2, real_name="用户2")

        def user_query_side_effect(*args):
            user_query = MockQuery([user1])
            if hasattr(user_query, "_filter_id"):
                if user_query._filter_id == 2:
                    user_query._data = [user2]
            return user_query

        self.db_mock.query.side_effect = user_query_side_effect

        result = self.service.get_summary(1)

        self.assertEqual(result["project_id"], 1)
        self.assertEqual(result["total_hours"], 22.0)
        self.assertEqual(result["total_participants"], 2)
        self.assertIn("by_user", result)
        self.assertIn("by_date", result)
        self.assertIn("by_work_type", result)

    @patch(
        "app.services.project_statistics_service.TimesheetStatisticsService.get_project"
    )
    @patch(
        "app.services.project_statistics_service.TimesheetStatisticsService.build_base_query"
    )
    @patch(
        "app.services.project_statistics_service.TimesheetStatisticsService.apply_date_filter"
    )
    def test_get_summary_empty(self, mock_filter, mock_query, mock_project):
        """测试工时汇总（无数据）"""
        project = MockProject(id=1, project_name="测试项目")
        mock_project.return_value = project

        query = MockQuery([])
        mock_query.return_value = query
        mock_filter.return_value = query

        result = self.service.get_summary(1)

        self.assertEqual(result["total_hours"], 0.0)
        self.assertEqual(result["total_participants"], 0)
        self.assertEqual(result["by_user"], [])

    @patch(
        "app.services.project_statistics_service.TimesheetStatisticsService.get_project"
    )
    @patch(
        "app.services.project_statistics_service.TimesheetStatisticsService.build_base_query"
    )
    @patch(
        "app.services.project_statistics_service.TimesheetStatisticsService.apply_date_filter"
    )
    def test_get_statistics_all_statuses(
        self, mock_filter, mock_query, mock_project
    ):
        """测试工时统计（所有状态）"""
        project = MockProject(id=1, project_name="测试项目")
        mock_project.return_value = project

        timesheets = [
            MockTimesheet(hours=8.0, status="DRAFT", work_date=date(2024, 1, 1)),
            MockTimesheet(hours=6.0, status="PENDING", work_date=date(2024, 1, 1)),
            MockTimesheet(hours=8.0, status="APPROVED", work_date=date(2024, 1, 2)),
            MockTimesheet(hours=4.0, status="REJECTED", work_date=date(2024, 1, 2)),
        ]

        query = MockQuery(timesheets)
        mock_query.return_value = query
        mock_filter.return_value = query

        result = self.service.get_statistics(1)

        self.assertEqual(result["total_hours"], 26.0)
        self.assertEqual(result["draft_hours"], 8.0)
        self.assertEqual(result["pending_hours"], 6.0)
        self.assertEqual(result["approved_hours"], 8.0)
        self.assertEqual(result["rejected_hours"], 4.0)
        self.assertEqual(result["total_records"], 4)
        self.assertEqual(result["unique_work_days"], 2)
        self.assertEqual(result["avg_daily_hours"], 13.0)


# ==============================================================================
# 工作日志统计服务测试
# ==============================================================================


class TestWorkLogStatisticsService(unittest.TestCase):
    """测试工作日志统计服务"""

    def setUp(self):
        """设置测试"""
        self.db_mock = MagicMock()
        self.service = WorkLogStatisticsService(self.db_mock)

    def test_get_model(self):
        """测试获取模型"""
        from app.models.work_log import WorkLog

        model = self.service.get_model()
        self.assertEqual(model, WorkLog)

    def test_get_project_id_field(self):
        """测试获取项目ID字段"""
        field = self.service.get_project_id_field()
        self.assertEqual(field, "id")

    @patch(
        "app.services.project_statistics_service.WorkLogStatisticsService.get_project"
    )
    def test_get_summary_with_data(self, mock_project):
        """测试工作日志汇总（有数据）"""
        project = MockProject(id=1, project_name="测试项目")
        mock_project.return_value = project

        # Mock查询结果
        mock_stats = Mock()
        mock_stats.log_count = 10
        mock_stats.contributor_count = 3

        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.with_entities.return_value = query_mock
        query_mock.first.return_value = mock_stats

        self.db_mock.query.return_value = query_mock

        result = self.service.get_summary(1, days=30)

        self.assertEqual(result["project_id"], 1)
        self.assertEqual(result["period_days"], 30)
        self.assertEqual(result["log_count"], 10)
        self.assertEqual(result["contributor_count"], 3)

    @patch(
        "app.services.project_statistics_service.WorkLogStatisticsService.get_project"
    )
    def test_get_summary_no_data(self, mock_project):
        """测试工作日志汇总（无数据）"""
        project = MockProject(id=1, project_name="测试项目")
        mock_project.return_value = project

        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.with_entities.return_value = query_mock
        query_mock.first.return_value = None

        self.db_mock.query.return_value = query_mock

        result = self.service.get_summary(1)

        self.assertEqual(result["log_count"], 0)
        self.assertEqual(result["contributor_count"], 0)


if __name__ == "__main__":
    unittest.main()

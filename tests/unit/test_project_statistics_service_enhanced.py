# -*- coding: utf-8 -*-
"""
项目统计服务测试 - 完整覆盖
测试目标：app/services/project_statistics_service.py (518行)
测试数量：40+个测试用例
覆盖内容：项目统计、趋势分析、仪表板数据、分组聚合、指标计算
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

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


# ==================== 辅助函数测试 ====================


class TestCalculateStatusStatistics:
    """测试状态统计功能"""

    def test_calculate_empty_projects(self):
        """测试空项目列表"""
        query = Mock()
        query.all.return_value = []
        result = calculate_status_statistics(query)
        assert result == {}

    def test_calculate_single_status(self):
        """测试单一状态"""
        p1 = Mock(status="ACTIVE")
        p2 = Mock(status="ACTIVE")
        query = Mock()
        query.all.return_value = [p1, p2]
        
        result = calculate_status_statistics(query)
        assert result == {"ACTIVE": 2}

    def test_calculate_multiple_statuses(self):
        """测试多种状态"""
        p1 = Mock(status="ACTIVE")
        p2 = Mock(status="COMPLETED")
        p3 = Mock(status="ACTIVE")
        p4 = Mock(status="PAUSED")
        query = Mock()
        query.all.return_value = [p1, p2, p3, p4]
        
        result = calculate_status_statistics(query)
        assert result == {"ACTIVE": 2, "COMPLETED": 1, "PAUSED": 1}

    def test_calculate_with_none_status(self):
        """测试包含None状态"""
        p1 = Mock(status="ACTIVE")
        p2 = Mock(status=None)
        query = Mock()
        query.all.return_value = [p1, p2]
        
        result = calculate_status_statistics(query)
        assert result == {"ACTIVE": 1}


class TestCalculateStageStatistics:
    """测试阶段统计功能"""

    def test_calculate_empty_projects(self):
        """测试空项目列表"""
        query = Mock()
        query.all.return_value = []
        result = calculate_stage_statistics(query)
        assert result == {}

    def test_calculate_multiple_stages(self):
        """测试多个阶段"""
        p1 = Mock(stage="DESIGN")
        p2 = Mock(stage="DEVELOPMENT")
        p3 = Mock(stage="DESIGN")
        query = Mock()
        query.all.return_value = [p1, p2, p3]
        
        result = calculate_stage_statistics(query)
        assert result == {"DESIGN": 2, "DEVELOPMENT": 1}

    def test_calculate_with_none_stage(self):
        """测试包含None阶段"""
        p1 = Mock(stage="TESTING")
        p2 = Mock(stage=None)
        query = Mock()
        query.all.return_value = [p1, p2]
        
        result = calculate_stage_statistics(query)
        assert result == {"TESTING": 1}


class TestCalculateHealthStatistics:
    """测试健康度统计功能"""

    def test_calculate_empty_projects(self):
        """测试空项目列表"""
        query = Mock()
        query.all.return_value = []
        result = calculate_health_statistics(query)
        assert result == {}

    def test_calculate_health_distribution(self):
        """测试健康度分布"""
        p1 = Mock(health="GREEN")
        p2 = Mock(health="YELLOW")
        p3 = Mock(health="GREEN")
        p4 = Mock(health="RED")
        query = Mock()
        query.all.return_value = [p1, p2, p3, p4]
        
        result = calculate_health_statistics(query)
        assert result == {"GREEN": 2, "YELLOW": 1, "RED": 1}


class TestCalculatePmStatistics:
    """测试项目经理统计功能"""

    def test_calculate_empty_projects(self):
        """测试空项目列表"""
        query = Mock()
        query.all.return_value = []
        result = calculate_pm_statistics(query)
        assert result == []

    def test_calculate_single_pm(self):
        """测试单个项目经理"""
        p1 = Mock(pm_id=1, pm_name="张三")
        p2 = Mock(pm_id=1, pm_name="张三")
        query = Mock()
        query.all.return_value = [p1, p2]
        
        result = calculate_pm_statistics(query)
        assert len(result) == 1
        assert result[0] == {"pm_id": 1, "pm_name": "张三", "count": 2}

    def test_calculate_multiple_pms(self):
        """测试多个项目经理"""
        p1 = Mock(pm_id=1, pm_name="张三")
        p2 = Mock(pm_id=2, pm_name="李四")
        p3 = Mock(pm_id=1, pm_name="张三")
        query = Mock()
        query.all.return_value = [p1, p2, p3]
        
        result = calculate_pm_statistics(query)
        assert len(result) == 2
        pm_dict = {r["pm_id"]: r for r in result}
        assert pm_dict[1]["count"] == 2
        assert pm_dict[2]["count"] == 1

    def test_calculate_with_none_pm(self):
        """测试包含None项目经理"""
        p1 = Mock(pm_id=1, pm_name="张三")
        p2 = Mock(pm_id=None, pm_name=None)
        query = Mock()
        query.all.return_value = [p1, p2]
        
        result = calculate_pm_statistics(query)
        assert len(result) == 1


class TestCalculateCustomerStatistics:
    """测试客户统计功能"""

    def test_calculate_empty_projects(self):
        """测试空项目列表"""
        query = Mock()
        query.all.return_value = []
        result = calculate_customer_statistics(query)
        assert result == []

    def test_calculate_single_customer(self):
        """测试单个客户"""
        p1 = Mock(customer_id=1, customer_name="客户A", contract_amount=10000)
        p2 = Mock(customer_id=1, customer_name="客户A", contract_amount=20000)
        query = Mock()
        query.all.return_value = [p1, p2]
        
        result = calculate_customer_statistics(query)
        assert len(result) == 1
        assert result[0] == {
            "customer_id": 1,
            "customer_name": "客户A",
            "count": 2,
            "total_amount": 30000.0,
        }

    def test_calculate_multiple_customers(self):
        """测试多个客户"""
        p1 = Mock(customer_id=1, customer_name="客户A", contract_amount=10000)
        p2 = Mock(customer_id=2, customer_name="客户B", contract_amount=15000)
        p3 = Mock(customer_id=1, customer_name="客户A", contract_amount=5000)
        query = Mock()
        query.all.return_value = [p1, p2, p3]
        
        result = calculate_customer_statistics(query)
        assert len(result) == 2
        customer_dict = {r["customer_id"]: r for r in result}
        assert customer_dict[1]["total_amount"] == 15000.0
        assert customer_dict[2]["total_amount"] == 15000.0

    def test_calculate_with_none_customer(self):
        """测试包含None客户"""
        p1 = Mock(customer_id=None, customer_name=None, contract_amount=10000)
        query = Mock()
        query.all.return_value = [p1]
        
        result = calculate_customer_statistics(query)
        assert len(result) == 1
        assert result[0]["customer_name"] == "未知客户"


class TestCalculateMonthlyStatistics:
    """测试月度统计功能"""

    @patch("app.services.project_statistics_service.Project")
    def test_calculate_empty_projects(self, mock_project):
        """测试空项目列表"""
        query = Mock()
        query.filter.return_value = query
        query.all.return_value = []
        
        result = calculate_monthly_statistics(query)
        assert result == []

    @patch("app.services.project_statistics_service.Project")
    def test_calculate_single_month(self, mock_project):
        """测试单月统计"""
        p1 = Mock(
            created_at=datetime(2026, 2, 1),
            contract_amount=10000
        )
        p2 = Mock(
            created_at=datetime(2026, 2, 15),
            contract_amount=20000
        )
        query = Mock()
        query.filter.return_value = query
        query.all.return_value = [p1, p2]
        
        result = calculate_monthly_statistics(query)
        assert len(result) == 1
        assert result[0]["year"] == 2026
        assert result[0]["month"] == 2
        assert result[0]["count"] == 2
        assert result[0]["total_amount"] == 30000.0

    @patch("app.services.project_statistics_service.Project")
    def test_calculate_multiple_months(self, mock_project):
        """测试多月统计"""
        p1 = Mock(created_at=datetime(2026, 1, 10), contract_amount=10000)
        p2 = Mock(created_at=datetime(2026, 2, 15), contract_amount=20000)
        p3 = Mock(created_at=datetime(2026, 1, 20), contract_amount=5000)
        query = Mock()
        query.filter.return_value = query
        query.all.return_value = [p1, p2, p3]
        
        result = calculate_monthly_statistics(query)
        assert len(result) == 2
        assert result[0]["month_label"] == "2026-01"
        assert result[0]["count"] == 2
        assert result[1]["month_label"] == "2026-02"
        assert result[1]["count"] == 1

    def test_calculate_with_date_filter(self):
        """测试带日期过滤的月度统计"""
        # 创建带有实际项目数据的query
        p1 = Mock(
            created_at=datetime(2026, 2, 1),
            contract_amount=10000
        )
        p2 = Mock(
            created_at=datetime(2026, 4, 15),  # 超出范围
            contract_amount=20000
        )
        
        # Mock query
        filtered_query = Mock()
        filtered_query.filter.return_value = filtered_query
        filtered_query.all.return_value = [p1]  # 只返回范围内的项目
        
        base_query = Mock()
        base_query.filter.return_value = filtered_query
        
        start_date = date(2026, 1, 1)
        end_date = date(2026, 3, 31)
        
        result = calculate_monthly_statistics(base_query, start_date, end_date)
        
        # 验证调用了过滤方法
        assert base_query.filter.called
        # 验证返回了统计结果
        assert isinstance(result, list)


class TestBuildProjectStatistics:
    """测试综合统计构建"""

    def test_build_empty_statistics(self):
        """测试空统计"""
        db = Mock()
        query = Mock()
        query.all.return_value = []
        
        result = build_project_statistics(db, query)
        
        assert result["total"] == 0
        assert result["average_progress"] == 0
        assert result["by_status"] == {}
        assert result["by_stage"] == {}

    def test_build_basic_statistics(self):
        """测试基础统计"""
        db = Mock()
        p1 = Mock(
            status="ACTIVE",
            stage="DESIGN",
            health="GREEN",
            pm_id=1,
            pm_name="张三",
            progress_pct=30
        )
        p2 = Mock(
            status="ACTIVE",
            stage="DEVELOPMENT",
            health="YELLOW",
            pm_id=2,
            pm_name="李四",
            progress_pct=50
        )
        query = Mock()
        query.all.return_value = [p1, p2]
        
        result = build_project_statistics(db, query)
        
        assert result["total"] == 2
        assert result["average_progress"] == 40
        assert result["by_status"]["ACTIVE"] == 2
        assert len(result["by_pm"]) == 2

    def test_build_with_customer_grouping(self):
        """测试按客户分组"""
        db = Mock()
        p1 = Mock(
            status="ACTIVE",
            stage="DESIGN",
            health="GREEN",
            pm_id=1,
            pm_name="张三",
            progress_pct=30,
            customer_id=1,
            customer_name="客户A",
            contract_amount=10000
        )
        query = Mock()
        query.all.return_value = [p1]
        
        result = build_project_statistics(db, query, group_by="customer")
        
        assert "by_customer" in result
        assert len(result["by_customer"]) == 1

    @patch("app.services.project_statistics_service.calculate_monthly_statistics")
    def test_build_with_month_grouping(self, mock_monthly):
        """测试按月分组"""
        db = Mock()
        query = Mock()
        query.all.return_value = []
        mock_monthly.return_value = []
        
        start_date = date(2026, 1, 1)
        end_date = date(2026, 3, 31)
        
        result = build_project_statistics(
            db, query, group_by="month", start_date=start_date, end_date=end_date
        )
        
        assert "by_month" in result
        mock_monthly.assert_called_once()


# ==================== 基类测试 ====================


class TestProjectStatisticsServiceBase:
    """测试统计服务基类"""

    def test_get_project_success(self):
        """测试获取项目成功"""
        db = Mock()
        project = Mock(id=1, project_name="测试项目")
        db.query.return_value.filter.return_value.first.return_value = project
        
        # 创建具体实现类用于测试
        service = CostStatisticsService(db)
        result = service.get_project(1)
        
        assert result == project

    def test_get_project_not_found(self):
        """测试项目不存在"""
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None
        
        service = CostStatisticsService(db)
        
        with pytest.raises(ValueError, match="项目不存在"):
            service.get_project(999)

    def test_apply_date_filter_with_both_dates(self):
        """测试应用双日期过滤"""
        db = Mock()
        service = CostStatisticsService(db)
        
        query = Mock()
        query.filter.return_value = query
        
        start_date = date(2026, 1, 1)
        end_date = date(2026, 3, 31)
        
        result = service.apply_date_filter(query, start_date, end_date)
        
        assert query.filter.call_count == 2

    def test_apply_date_filter_with_start_only(self):
        """测试仅应用开始日期过滤"""
        db = Mock()
        service = CostStatisticsService(db)
        
        query = Mock()
        query.filter.return_value = query
        
        start_date = date(2026, 1, 1)
        
        result = service.apply_date_filter(query, start_date=start_date)
        
        assert query.filter.call_count == 1

    def test_group_by_field_count(self):
        """测试按字段分组计数"""
        db = Mock()
        service = CostStatisticsService(db)
        
        query = Mock()
        with_entities_mock = Mock()
        query.with_entities.return_value = with_entities_mock
        with_entities_mock.group_by.return_value.all.return_value = [
            ("TYPE_A", 5),
            ("TYPE_B", 3),
        ]
        
        result = service.group_by_field(query, "cost_type")
        
        assert result == {"TYPE_A": 5, "TYPE_B": 3}

    def test_group_by_field_with_aggregate(self):
        """测试按字段分组并聚合"""
        from sqlalchemy import func
        
        db = Mock()
        service = CostStatisticsService(db)
        
        query = Mock()
        with_entities_mock = Mock()
        query.with_entities.return_value = with_entities_mock
        with_entities_mock.group_by.return_value.all.return_value = [
            ("TYPE_A", Decimal("1500.50")),
            ("TYPE_B", Decimal("2300.00")),
        ]
        
        result = service.group_by_field(
            query, "cost_type", func.sum, "amount"
        )
        
        assert result == {"TYPE_A": 1500.50, "TYPE_B": 2300.0}

    def test_calculate_total(self):
        """测试计算总和"""
        db = Mock()
        service = CostStatisticsService(db)
        
        query = Mock()
        with_entities_mock = Mock()
        query.with_entities.return_value = with_entities_mock
        with_entities_mock.scalar.return_value = Decimal("5000.00")
        
        result = service.calculate_total(query, "amount")
        
        assert result == 5000.0

    def test_calculate_total_none(self):
        """测试计算总和为None"""
        db = Mock()
        service = CostStatisticsService(db)
        
        query = Mock()
        with_entities_mock = Mock()
        query.with_entities.return_value = with_entities_mock
        with_entities_mock.scalar.return_value = None
        
        result = service.calculate_total(query, "amount")
        
        assert result == 0.0

    def test_calculate_avg(self):
        """测试计算平均值"""
        db = Mock()
        service = CostStatisticsService(db)
        
        query = Mock()
        with_entities_mock = Mock()
        query.with_entities.return_value = with_entities_mock
        with_entities_mock.scalar.return_value = Decimal("2500.00")
        
        result = service.calculate_avg(query, "amount")
        
        assert result == 2500.0

    def test_count_distinct(self):
        """测试计算不重复数量"""
        db = Mock()
        service = CostStatisticsService(db)
        
        query = Mock()
        with_entities_mock = Mock()
        query.with_entities.return_value = with_entities_mock
        with_entities_mock.scalar.return_value = 5
        
        result = service.count_distinct(query, "cost_type")
        
        assert result == 5


# ==================== 成本统计服务测试 ====================


class TestCostStatisticsService:
    """测试成本统计服务"""

    def test_get_summary_basic(self):
        """测试基础成本汇总"""
        db = Mock()
        project = Mock(
            id=1,
            project_name="测试项目",
            budget_amount=Decimal("100000")
        )
        
        # 配置db.query的返回值链
        project_query = Mock()
        project_query.filter.return_value.first.return_value = project
        
        cost_query = Mock()
        cost_query.filter.return_value = cost_query
        
        # db.query根据不同参数返回不同的mock
        def query_side_effect(model):
            from app.models.project import Project, ProjectCost
            if model == Project:
                return project_query
            elif model == ProjectCost:
                return cost_query
            return Mock()
        
        db.query.side_effect = query_side_effect
        
        service = CostStatisticsService(db)
        
        # Mock group_by_field and calculate_total
        with patch.object(service, 'group_by_field', return_value={"LABOR": 30000, "MATERIAL": 20000}):
            with patch.object(service, 'calculate_total', return_value=50000.0):
                result = service.get_summary(1)
        
        assert result["project_id"] == 1
        assert result["project_name"] == "测试项目"
        assert result["total_cost"] == 50000.0
        assert result["budget"] == 100000.0
        assert result["budget_used_pct"] == 50.0

    def test_get_summary_no_budget(self):
        """测试无预算情况"""
        db = Mock()
        project = Mock(
            id=1,
            project_name="测试项目",
            budget_amount=None
        )
        
        # 配置db.query的返回值链
        project_query = Mock()
        project_query.filter.return_value.first.return_value = project
        
        cost_query = Mock()
        cost_query.filter.return_value = cost_query
        
        def query_side_effect(model):
            from app.models.project import Project, ProjectCost
            if model == Project:
                return project_query
            elif model == ProjectCost:
                return cost_query
            return Mock()
        
        db.query.side_effect = query_side_effect
        
        service = CostStatisticsService(db)
        
        with patch.object(service, 'group_by_field', return_value={}):
            with patch.object(service, 'calculate_total', return_value=0.0):
                result = service.get_summary(1)
        
        assert result["budget"] is None
        assert result["budget_used_pct"] is None

    def test_get_summary_with_date_filter(self):
        """测试带日期过滤的成本汇总"""
        db = Mock()
        project = Mock(id=1, project_name="测试项目", budget_amount=Decimal("100000"))
        
        # 配置db.query的返回值链
        project_query = Mock()
        project_query.filter.return_value.first.return_value = project
        
        cost_query = Mock()
        cost_query.filter.return_value = cost_query
        
        def query_side_effect(model):
            from app.models.project import Project, ProjectCost
            if model == Project:
                return project_query
            elif model == ProjectCost:
                return cost_query
            return Mock()
        
        db.query.side_effect = query_side_effect
        
        service = CostStatisticsService(db)
        
        start_date = date(2026, 1, 1)
        end_date = date(2026, 3, 31)
        
        with patch.object(service, 'group_by_field', return_value={}):
            with patch.object(service, 'calculate_total', return_value=0.0):
                result = service.get_summary(1, start_date, end_date)
        
        assert result["project_id"] == 1


# ==================== 工时统计服务测试 ====================


class TestTimesheetStatisticsService:
    """测试工时统计服务"""

    def test_get_summary_basic(self):
        """测试基础工时汇总"""
        db = Mock()
        project = Mock(id=1, project_name="测试项目")
        db.query.return_value.filter.return_value.first.return_value = project
        
        # Mock timesheets
        user1 = Mock(id=1, real_name="张三", username="zhangsan")
        ts1 = Mock(
            user_id=1,
            hours=8.0,
            work_date=date(2026, 2, 20),
            overtime_type="NORMAL",
            status="APPROVED"
        )
        ts2 = Mock(
            user_id=1,
            hours=4.0,
            work_date=date(2026, 2, 21),
            overtime_type="NORMAL",
            status="APPROVED"
        )
        
        service = TimesheetStatisticsService(db)
        
        # Setup query mocks
        query_chain = Mock()
        db.query.return_value = query_chain
        query_chain.filter.return_value = query_chain
        query_chain.all.return_value = [ts1, ts2]
        
        # Mock user query
        user_query = Mock()
        user_query.filter.return_value.first.return_value = user1
        db.query.side_effect = lambda model: (
            Mock(filter=lambda x: Mock(first=lambda: project))
            if "Project" in str(model)
            else user_query if "User" in str(model)
            else query_chain
        )
        
        result = service.get_summary(1)
        
        assert result["project_id"] == 1
        assert result["total_hours"] == 12.0
        assert result["total_participants"] == 1

    def test_get_statistics_all_statuses(self):
        """测试所有状态的工时统计"""
        db = Mock()
        project = Mock(id=1, project_name="测试项目")
        
        ts1 = Mock(user_id=1, hours=8.0, work_date=date(2026, 2, 20), status="APPROVED")
        ts2 = Mock(user_id=1, hours=4.0, work_date=date(2026, 2, 21), status="PENDING")
        ts3 = Mock(user_id=2, hours=2.0, work_date=date(2026, 2, 20), status="DRAFT")
        ts4 = Mock(user_id=2, hours=1.0, work_date=date(2026, 2, 22), status="REJECTED")
        
        service = TimesheetStatisticsService(db)
        
        query_chain = Mock()
        db.query.return_value = query_chain
        query_chain.filter.return_value = query_chain
        query_chain.all.return_value = [ts1, ts2, ts3, ts4]
        
        # Mock project query
        db.query.return_value.filter.return_value.first.return_value = project
        
        result = service.get_statistics(1)
        
        assert result["total_hours"] == 15.0
        assert result["approved_hours"] == 8.0
        assert result["pending_hours"] == 4.0
        assert result["draft_hours"] == 2.0
        assert result["rejected_hours"] == 1.0
        assert result["total_records"] == 4
        assert result["total_participants"] == 2
        assert result["unique_work_days"] == 3

    def test_get_statistics_avg_daily_hours(self):
        """测试平均每日工时计算"""
        db = Mock()
        project = Mock(id=1, project_name="测试项目")
        
        ts1 = Mock(user_id=1, hours=8.0, work_date=date(2026, 2, 20), status="APPROVED")
        ts2 = Mock(user_id=1, hours=8.0, work_date=date(2026, 2, 21), status="APPROVED")
        ts3 = Mock(user_id=2, hours=8.0, work_date=date(2026, 2, 20), status="APPROVED")
        
        service = TimesheetStatisticsService(db)
        
        query_chain = Mock()
        db.query.return_value = query_chain
        query_chain.filter.return_value = query_chain
        query_chain.all.return_value = [ts1, ts2, ts3]
        
        db.query.return_value.filter.return_value.first.return_value = project
        
        result = service.get_statistics(1)
        
        # 总工时24小时，2个工作日，平均12小时/天
        assert result["avg_daily_hours"] == 12.0


# ==================== 工作日志统计服务测试 ====================


class TestWorkLogStatisticsService:
    """测试工作日志统计服务"""

    def test_get_summary_basic(self):
        """测试基础工作日志汇总"""
        db = Mock()
        project = Mock(id=1, project_name="测试项目")
        db.query.return_value.filter.return_value.first.return_value = project
        
        service = WorkLogStatisticsService(db)
        
        # Mock query result
        stats = Mock(log_count=10, contributor_count=3)
        query_chain = Mock()
        db.query.return_value = query_chain
        query_chain.join.return_value = query_chain
        query_chain.filter.return_value = query_chain
        query_chain.with_entities.return_value.first.return_value = stats
        
        result = service.get_summary(1, days=30)
        
        assert result["project_id"] == 1
        assert result["period_days"] == 30
        assert result["log_count"] == 10
        assert result["contributor_count"] == 3

    def test_get_summary_with_date_range(self):
        """测试带日期范围的工作日志汇总"""
        db = Mock()
        project = Mock(id=1, project_name="测试项目")
        db.query.return_value.filter.return_value.first.return_value = project
        
        service = WorkLogStatisticsService(db)
        
        stats = Mock(log_count=5, contributor_count=2)
        query_chain = Mock()
        db.query.return_value = query_chain
        query_chain.join.return_value = query_chain
        query_chain.filter.return_value = query_chain
        query_chain.with_entities.return_value.first.return_value = stats
        
        start_date = date(2026, 2, 1)
        end_date = date(2026, 2, 28)
        
        result = service.get_summary(1, start_date=start_date, end_date=end_date)
        
        assert result["log_count"] == 5
        assert result["contributor_count"] == 2

    def test_get_summary_no_logs(self):
        """测试无工作日志情况"""
        db = Mock()
        project = Mock(id=1, project_name="测试项目")
        db.query.return_value.filter.return_value.first.return_value = project
        
        service = WorkLogStatisticsService(db)
        
        query_chain = Mock()
        db.query.return_value = query_chain
        query_chain.join.return_value = query_chain
        query_chain.filter.return_value = query_chain
        query_chain.with_entities.return_value.first.return_value = None
        
        result = service.get_summary(1)
        
        assert result["log_count"] == 0
        assert result["contributor_count"] == 0


# ==================== 集成测试 ====================


class TestStatisticsIntegration:
    """统计服务集成测试"""

    def test_cost_and_timesheet_correlation(self):
        """测试成本和工时统计关联"""
        db = Mock()
        project = Mock(id=1, project_name="项目A", budget_amount=Decimal("100000"))
        
        # 成本统计
        cost_service = CostStatisticsService(db)
        
        # 配置成本查询
        project_query = Mock()
        project_query.filter.return_value.first.return_value = project
        
        cost_query = Mock()
        cost_query.filter.return_value = cost_query
        
        from app.models.project import Project, ProjectCost
        from app.models.timesheet import Timesheet
        from app.models.user import User
        
        def query_side_effect_cost(model):
            if model == Project:
                return project_query
            elif model == ProjectCost:
                return cost_query
            return Mock()
        
        db.query.side_effect = query_side_effect_cost
        
        with patch.object(cost_service, 'group_by_field', return_value={"LABOR": 50000}):
            with patch.object(cost_service, 'calculate_total', return_value=50000.0):
                cost_result = cost_service.get_summary(1)
        
        # 工时统计
        timesheet_service = TimesheetStatisticsService(db)
        
        ts = Mock(user_id=1, hours=100.0, work_date=date(2026, 2, 20), status="APPROVED")
        
        timesheet_query = Mock()
        timesheet_query.filter.return_value = timesheet_query
        timesheet_query.all.return_value = [ts]
        
        user_query = Mock()
        user_query.filter.return_value.first.return_value = Mock(
            id=1, real_name="张三", username="zhangsan"
        )
        
        def query_side_effect_timesheet(model):
            if model == Project:
                return project_query
            elif model == Timesheet:
                return timesheet_query
            elif model == User:
                return user_query
            return Mock()
        
        db.query.side_effect = query_side_effect_timesheet
        
        timesheet_result = timesheet_service.get_summary(1)
        
        # 验证关联性
        assert cost_result["total_cost"] > 0
        assert timesheet_result["total_hours"] > 0
        assert cost_result["project_id"] == timesheet_result["project_id"]

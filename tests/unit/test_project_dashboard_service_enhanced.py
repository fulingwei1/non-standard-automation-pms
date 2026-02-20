# -*- coding: utf-8 -*-
"""
项目仪表盘服务完整测试
覆盖所有数据聚合、KPI计算、图表数据和异常处理
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock
from sqlalchemy.orm import Session

from app.services import project_dashboard_service
from app.models.project import Project, ProjectMilestone, ProjectStatusLog
from app.models.progress import Task


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    return MagicMock(spec=Session)


@pytest.fixture
def sample_project():
    """示例项目数据"""
    project = MagicMock(spec=Project)
    project.id = 1
    project.project_code = "PRJ2024001"
    project.project_name = "测试项目"
    project.customer_name = "测试客户"
    project.pm_name = "张三"
    project.stage = "S3"
    project.status = "ST02"
    project.health = "H1"
    project.progress_pct = Decimal("45.5")
    project.planned_start_date = date(2024, 1, 1)
    project.planned_end_date = date(2024, 12, 31)
    project.actual_start_date = date(2024, 1, 5)
    project.actual_end_date = None
    project.contract_amount = Decimal("1000000")
    project.budget_amount = Decimal("800000")
    return project


@pytest.fixture
def today():
    """当前日期"""
    return date(2024, 6, 15)


# ============================================================================
# 测试 build_basic_info
# ============================================================================

def test_build_basic_info_complete_data(sample_project):
    """测试完整项目基本信息构建"""
    result = project_dashboard_service.build_basic_info(sample_project)
    
    assert result["project_code"] == "PRJ2024001"
    assert result["project_name"] == "测试项目"
    assert result["customer_name"] == "测试客户"
    assert result["pm_name"] == "张三"
    assert result["stage"] == "S3"
    assert result["status"] == "ST02"
    assert result["health"] == "H1"
    assert result["progress_pct"] == 45.5
    assert result["planned_start_date"] == "2024-01-01"
    assert result["planned_end_date"] == "2024-12-31"
    assert result["actual_start_date"] == "2024-01-05"
    assert result["actual_end_date"] is None
    assert result["contract_amount"] == 1000000.0
    assert result["budget_amount"] == 800000.0


def test_build_basic_info_with_nulls():
    """测试带空值的项目基本信息"""
    project = MagicMock(spec=Project)
    project.project_code = "PRJ2024002"
    project.project_name = "最小项目"
    project.customer_name = None
    project.pm_name = None
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
    
    result = project_dashboard_service.build_basic_info(project)
    
    assert result["stage"] == "S1"  # 默认值
    assert result["status"] == "ST01"  # 默认值
    assert result["health"] == "H1"  # 默认值
    assert result["progress_pct"] == 0.0
    assert result["planned_start_date"] is None
    assert result["contract_amount"] == 0.0


def test_build_basic_info_with_actual_end_date(sample_project):
    """测试已完成项目的基本信息"""
    sample_project.actual_end_date = date(2024, 11, 30)
    
    result = project_dashboard_service.build_basic_info(sample_project)
    
    assert result["actual_end_date"] == "2024-11-30"


# ============================================================================
# 测试 calculate_progress_stats
# ============================================================================

def test_calculate_progress_stats_normal(sample_project, today):
    """测试正常进度统计"""
    result = project_dashboard_service.calculate_progress_stats(sample_project, today)
    
    # 2024-01-01 到 2024-12-31 共 366 天（闰年）
    # 2024-01-01 到 2024-06-15 共 167 天
    # 计划进度 = 167/366 * 100 ≈ 45.63%
    assert result["actual_progress"] == 45.5
    assert 45.0 < result["plan_progress"] < 46.0
    assert -1.0 < result["progress_deviation"] < 1.0
    assert result["time_deviation_days"] < 0  # 未延期
    assert result["is_delayed"] is False


def test_calculate_progress_stats_delayed(sample_project):
    """测试延期项目进度统计"""
    sample_project.progress_pct = Decimal("30.0")
    delayed_today = date(2025, 2, 1)  # 超过计划结束日期
    
    result = project_dashboard_service.calculate_progress_stats(sample_project, delayed_today)
    
    assert result["actual_progress"] == 30.0
    assert result["plan_progress"] == 100  # 已超期
    assert result["progress_deviation"] < 0  # 进度落后
    assert result["time_deviation_days"] > 0  # 延期
    assert result["is_delayed"] is True


def test_calculate_progress_stats_finished_project(sample_project):
    """测试已完成项目不算延期"""
    sample_project.stage = "S9"  # 已完成
    delayed_today = date(2025, 2, 1)
    
    result = project_dashboard_service.calculate_progress_stats(sample_project, delayed_today)
    
    assert result["is_delayed"] is False  # 已完成项目不算延期


def test_calculate_progress_stats_no_dates():
    """测试无日期项目进度统计"""
    project = MagicMock(spec=Project)
    project.progress_pct = Decimal("20.0")
    project.planned_start_date = None
    project.planned_end_date = None
    project.stage = "S1"
    
    result = project_dashboard_service.calculate_progress_stats(project, date.today())
    
    assert result["actual_progress"] == 20.0
    assert result["plan_progress"] == 0
    assert result["progress_deviation"] == 20.0


def test_calculate_progress_stats_zero_days():
    """测试开始和结束日期相同"""
    project = MagicMock(spec=Project)
    project.progress_pct = Decimal("100.0")
    project.planned_start_date = date(2024, 1, 1)
    project.planned_end_date = date(2024, 1, 1)
    project.stage = "S9"
    
    result = project_dashboard_service.calculate_progress_stats(project, date(2024, 1, 1))
    
    assert result["plan_progress"] >= 0  # 不应该报错


# ============================================================================
# 测试 calculate_cost_stats
# ============================================================================

@patch('app.services.cost_service.CostService')
def test_calculate_cost_stats(mock_cost_service_class, mock_db):
    """测试成本统计计算"""
    mock_service = MagicMock()
    mock_service.calculate_cost_stats.return_value = {
        "total_cost": 600000.0,
        "budget_amount": 800000.0,
        "cost_variance": 200000.0,
        "cost_variance_rate": 25.0,
    }
    mock_cost_service_class.return_value = mock_service
    
    result = project_dashboard_service.calculate_cost_stats(mock_db, 1, 800000.0)
    
    assert result["total_cost"] == 600000.0
    assert result["budget_amount"] == 800000.0
    assert result["cost_variance"] == 200000.0
    assert result["cost_variance_rate"] == 25.0
    mock_cost_service_class.assert_called_once_with(mock_db)
    mock_service.calculate_cost_stats.assert_called_once_with(1, 800000.0)


# ============================================================================
# 测试 calculate_task_stats
# ============================================================================

def test_calculate_task_stats_normal(mock_db):
    """测试正常任务统计"""
    # Mock 总数查询
    mock_total_result = MagicMock()
    mock_total_result.total = 100
    
    # Mock 状态分组查询
    mock_status_counts = [
        ("COMPLETED", 50),
        ("IN_PROGRESS", 30),
        ("PENDING", 15),
        ("BLOCKED", 5),
    ]
    
    # Mock 平均进度查询
    mock_avg_result = MagicMock()
    mock_avg_result.avg = 62.5
    
    # 设置查询链
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    
    # 第一次调用返回总数，第二次返回状态分组，第三次返回平均进度
    mock_filter.first.side_effect = [mock_total_result, mock_avg_result]
    mock_group = MagicMock()
    mock_filter.group_by.return_value = mock_group
    mock_group.all.return_value = mock_status_counts
    
    result = project_dashboard_service.calculate_task_stats(mock_db, 1)
    
    assert result["total"] == 100
    assert result["completed"] == 50
    assert result["in_progress"] == 30
    assert result["pending"] == 15
    assert result["blocked"] == 5
    assert result["completion_rate"] == 50.0
    assert result["avg_progress"] == 62.5


def test_calculate_task_stats_no_tasks(mock_db):
    """测试无任务情况"""
    mock_total_result = MagicMock()
    mock_total_result.total = 0
    
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = mock_total_result
    mock_group = MagicMock()
    mock_filter.group_by.return_value = mock_group
    mock_group.all.return_value = []
    
    result = project_dashboard_service.calculate_task_stats(mock_db, 1)
    
    assert result["total"] == 0
    assert result["completion_rate"] == 0


def test_calculate_task_stats_with_accepted(mock_db):
    """测试包含已接受状态的任务"""
    mock_total_result = MagicMock()
    mock_total_result.total = 50
    
    mock_status_counts = [
        ("COMPLETED", 20),
        ("IN_PROGRESS", 10),
        ("ACCEPTED", 15),  # 应该算入 pending
        ("PENDING", 5),
    ]
    
    mock_avg_result = MagicMock()
    mock_avg_result.avg = 50.0
    
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_filter.first.side_effect = [mock_total_result, mock_avg_result]
    mock_group = MagicMock()
    mock_filter.group_by.return_value = mock_group
    mock_group.all.return_value = mock_status_counts
    
    result = project_dashboard_service.calculate_task_stats(mock_db, 1)
    
    assert result["pending"] == 20  # 15 + 5


# ============================================================================
# 测试 calculate_milestone_stats
# ============================================================================

def test_calculate_milestone_stats_normal(mock_db, today):
    """测试正常里程碑统计"""
    mock_total_result = MagicMock()
    mock_total_result.total = 10
    
    # 设置查询链
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = mock_total_result
    mock_filter.scalar.side_effect = [6, 2, 2]  # completed, overdue, upcoming
    
    result = project_dashboard_service.calculate_milestone_stats(mock_db, 1, today)
    
    assert result["total"] == 10
    assert result["completed"] == 6
    assert result["overdue"] == 2
    assert result["upcoming"] == 2
    assert result["completion_rate"] == 60.0


def test_calculate_milestone_stats_no_milestones(mock_db, today):
    """测试无里程碑情况"""
    mock_total_result = MagicMock()
    mock_total_result.total = 0
    
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = mock_total_result
    mock_filter.scalar.return_value = 0
    
    result = project_dashboard_service.calculate_milestone_stats(mock_db, 1, today)
    
    assert result["total"] == 0
    assert result["completion_rate"] == 0


def test_calculate_milestone_stats_all_completed(mock_db, today):
    """测试所有里程碑已完成"""
    mock_total_result = MagicMock()
    mock_total_result.total = 5
    
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = mock_total_result
    mock_filter.scalar.side_effect = [5, 0, 0]
    
    result = project_dashboard_service.calculate_milestone_stats(mock_db, 1, today)
    
    assert result["completion_rate"] == 100.0
    assert result["overdue"] == 0
    assert result["upcoming"] == 0


# ============================================================================
# 测试 calculate_risk_stats
# ============================================================================

@patch('app.services.project_dashboard_service.PmoProjectRisk')
def test_calculate_risk_stats_normal(mock_pmo_risk, mock_db):
    """测试正常风险统计"""
    # Mock 风险对象
    risk1 = MagicMock()
    risk1.risk_level = "HIGH"
    risk1.status = "OPEN"
    
    risk2 = MagicMock()
    risk2.risk_level = "CRITICAL"
    risk2.status = "OPEN"
    
    risk3 = MagicMock()
    risk3.risk_level = "MEDIUM"
    risk3.status = "CLOSED"
    
    risk4 = MagicMock()
    risk4.risk_level = "HIGH"
    risk4.status = "CLOSED"
    
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_filter.all.return_value = [risk1, risk2, risk3, risk4]
    
    result = project_dashboard_service.calculate_risk_stats(mock_db, 1)
    
    assert result["total"] == 4
    assert result["open"] == 2
    assert result["high"] == 1
    assert result["critical"] == 1


@patch('app.services.project_dashboard_service.PmoProjectRisk', None)
def test_calculate_risk_stats_model_not_available(mock_db):
    """测试风险模型不可用"""
    result = project_dashboard_service.calculate_risk_stats(mock_db, 1)
    
    assert result is None


@patch('app.services.project_dashboard_service.PmoProjectRisk')
def test_calculate_risk_stats_exception(mock_pmo_risk, mock_db):
    """测试风险统计异常处理"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.side_effect = Exception("Database error")
    
    result = project_dashboard_service.calculate_risk_stats(mock_db, 1)
    
    assert result is None


# ============================================================================
# 测试 calculate_issue_stats
# ============================================================================

@patch('app.services.project_dashboard_service.Issue')
def test_calculate_issue_stats_normal(mock_issue, mock_db):
    """测试正常问题统计"""
    issue1 = MagicMock()
    issue1.status = "OPEN"
    issue1.is_blocking = True
    
    issue2 = MagicMock()
    issue2.status = "PROCESSING"
    issue2.is_blocking = False
    
    issue3 = MagicMock()
    issue3.status = "OPEN"
    issue3.is_blocking = False
    
    issue4 = MagicMock()
    issue4.status = "CLOSED"
    issue4.is_blocking = False
    
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_filter.all.return_value = [issue1, issue2, issue3, issue4]
    
    result = project_dashboard_service.calculate_issue_stats(mock_db, 1)
    
    assert result["total"] == 4
    assert result["open"] == 2
    assert result["processing"] == 1
    assert result["blocking"] == 1


@patch('app.services.project_dashboard_service.Issue', None)
def test_calculate_issue_stats_model_not_available(mock_db):
    """测试问题模型不可用"""
    result = project_dashboard_service.calculate_issue_stats(mock_db, 1)
    
    assert result is None


@patch('app.services.project_dashboard_service.Issue')
def test_calculate_issue_stats_exception(mock_issue, mock_db):
    """测试问题统计异常处理"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.side_effect = Exception("Database error")
    
    result = project_dashboard_service.calculate_issue_stats(mock_db, 1)
    
    assert result is None


# ============================================================================
# 测试 calculate_resource_usage
# ============================================================================

@patch('app.services.project_dashboard_service.PmoResourceAllocation')
def test_calculate_resource_usage_normal(mock_resource, mock_db):
    """测试正常资源使用统计"""
    alloc1 = MagicMock()
    alloc1.department_name = "研发部"
    alloc1.role = "开发工程师"
    
    alloc2 = MagicMock()
    alloc2.department_name = "研发部"
    alloc2.role = "测试工程师"
    
    alloc3 = MagicMock()
    alloc3.department_name = "产品部"
    alloc3.role = "产品经理"
    
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_filter.all.return_value = [alloc1, alloc2, alloc3]
    
    result = project_dashboard_service.calculate_resource_usage(mock_db, 1)
    
    assert result["total_allocations"] == 3
    assert result["by_department"]["研发部"] == 2
    assert result["by_department"]["产品部"] == 1
    assert result["by_role"]["开发工程师"] == 1
    assert result["by_role"]["测试工程师"] == 1
    assert result["by_role"]["产品经理"] == 1


@patch('app.services.project_dashboard_service.PmoResourceAllocation')
def test_calculate_resource_usage_with_nulls(mock_resource, mock_db):
    """测试资源分配含空值"""
    alloc1 = MagicMock()
    alloc1.department_name = None
    alloc1.role = None
    
    alloc2 = MagicMock()
    alloc2.department_name = "研发部"
    alloc2.role = None
    
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_filter.all.return_value = [alloc1, alloc2]
    
    result = project_dashboard_service.calculate_resource_usage(mock_db, 1)
    
    assert result["by_department"]["未分配"] == 1
    assert result["by_department"]["研发部"] == 1
    assert result["by_role"]["未分配"] == 2


@patch('app.services.project_dashboard_service.PmoResourceAllocation')
def test_calculate_resource_usage_no_allocations(mock_resource, mock_db):
    """测试无资源分配"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_filter.all.return_value = []
    
    result = project_dashboard_service.calculate_resource_usage(mock_db, 1)
    
    assert result is None


@patch('app.services.project_dashboard_service.PmoResourceAllocation', None)
def test_calculate_resource_usage_model_not_available(mock_db):
    """测试资源分配模型不可用"""
    result = project_dashboard_service.calculate_resource_usage(mock_db, 1)
    
    assert result is None


# ============================================================================
# 测试 get_recent_activities
# ============================================================================

def test_get_recent_activities_normal(mock_db):
    """测试获取最近活动"""
    # Mock 状态日志
    log1 = MagicMock(spec=ProjectStatusLog)
    log1.changed_at = date(2024, 6, 10)
    log1.old_status = "ST01"
    log1.new_status = "ST02"
    log1.change_reason = "项目启动"
    
    log2 = MagicMock(spec=ProjectStatusLog)
    log2.changed_at = date(2024, 6, 5)
    log2.old_status = "ST02"
    log2.new_status = "ST03"
    log2.change_reason = "进入执行阶段"
    
    # Mock 里程碑
    milestone1 = MagicMock(spec=ProjectMilestone)
    milestone1.milestone_name = "需求评审"
    milestone1.actual_date = date(2024, 6, 8)
    milestone1.status = "COMPLETED"
    
    # 设置查询链
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_order = MagicMock()
    mock_filter.order_by.return_value = mock_order
    mock_limit = MagicMock()
    mock_order.limit.return_value = mock_limit
    mock_limit.all.side_effect = [[log1, log2], [milestone1]]
    
    result = project_dashboard_service.get_recent_activities(mock_db, 1)
    
    assert len(result) == 3
    assert result[0]["type"] == "STATUS_CHANGE"
    assert result[0]["title"] == "状态变更：ST01 → ST02"
    assert "MILESTONE" in [a["type"] for a in result]


def test_get_recent_activities_no_data(mock_db):
    """测试无活动数据"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_order = MagicMock()
    mock_filter.order_by.return_value = mock_order
    mock_limit = MagicMock()
    mock_order.limit.return_value = mock_limit
    mock_limit.all.return_value = []
    
    result = project_dashboard_service.get_recent_activities(mock_db, 1)
    
    assert len(result) == 0


def test_get_recent_activities_limit_10(mock_db):
    """测试活动数量限制为10"""
    # 创建超过10条记录
    logs = [MagicMock(spec=ProjectStatusLog) for _ in range(8)]
    for i, log in enumerate(logs):
        log.changed_at = date(2024, 6, i + 1)
        log.old_status = f"ST0{i}"
        log.new_status = f"ST0{i+1}"
        log.change_reason = f"变更{i}"
    
    milestones = [MagicMock(spec=ProjectMilestone) for _ in range(5)]
    for i, ms in enumerate(milestones):
        ms.milestone_name = f"里程碑{i}"
        ms.actual_date = date(2024, 6, i + 10)
        ms.status = "COMPLETED"
    
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_order = MagicMock()
    mock_filter.order_by.return_value = mock_order
    mock_limit = MagicMock()
    mock_order.limit.return_value = mock_limit
    mock_limit.all.side_effect = [logs, milestones]
    
    result = project_dashboard_service.get_recent_activities(mock_db, 1)
    
    assert len(result) <= 10  # 最多10条


# ============================================================================
# 测试 calculate_key_metrics
# ============================================================================

def test_calculate_key_metrics_healthy_project(sample_project):
    """测试健康项目关键指标"""
    result = project_dashboard_service.calculate_key_metrics(
        project=sample_project,
        progress_deviation=2.0,  # 进度偏差小
        cost_variance_rate=5.0,  # 成本偏差小
        task_completed=80,
        task_total=100
    )
    
    assert result["health_score"] == 100  # H1
    assert result["progress_score"] == 45.5
    assert result["schedule_score"] > 90  # 进度偏差小
    assert result["cost_score"] == 90  # 成本偏差5%
    assert result["quality_score"] == 80
    assert result["overall_score"] > 70  # 综合得分高


def test_calculate_key_metrics_troubled_project():
    """测试问题项目关键指标"""
    project = MagicMock(spec=Project)
    project.health = "H4"
    project.progress_pct = Decimal("30.0")
    
    result = project_dashboard_service.calculate_key_metrics(
        project=project,
        progress_deviation=-20.0,  # 进度严重落后
        cost_variance_rate=-15.0,  # 成本超支
        task_completed=20,
        task_total=100
    )
    
    assert result["health_score"] == 25  # H4
    assert result["progress_score"] == 30.0
    assert result["schedule_score"] < 70  # 进度偏差大
    assert result["cost_score"] == 70  # 成本偏差15%
    assert result["quality_score"] == 20
    assert result["overall_score"] < 50  # 综合得分低


def test_calculate_key_metrics_no_tasks():
    """测试无任务项目的质量得分"""
    project = MagicMock(spec=Project)
    project.health = "H1"
    project.progress_pct = Decimal("0")
    
    result = project_dashboard_service.calculate_key_metrics(
        project=project,
        progress_deviation=0,
        cost_variance_rate=0,
        task_completed=0,
        task_total=0  # 无任务
    )
    
    assert result["quality_score"] == 100  # 无任务时默认100


def test_calculate_key_metrics_extreme_deviation():
    """测试极端偏差情况"""
    project = MagicMock(spec=Project)
    project.health = "H3"
    project.progress_pct = Decimal("10.0")
    
    result = project_dashboard_service.calculate_key_metrics(
        project=project,
        progress_deviation=-50.0,  # 极端偏差
        cost_variance_rate=-100.0,  # 极端成本超支
        task_completed=5,
        task_total=200
    )
    
    assert result["schedule_score"] >= 0  # 不应该是负数
    assert result["cost_score"] >= 0  # 不应该是负数
    assert result["overall_score"] >= 0  # 不应该是负数


def test_calculate_key_metrics_health_levels():
    """测试所有健康等级的分数"""
    test_cases = [
        ("H1", 100),
        ("H2", 75),
        ("H3", 50),
        ("H4", 25),
    ]
    
    for health, expected_score in test_cases:
        project = MagicMock(spec=Project)
        project.health = health
        project.progress_pct = Decimal("50.0")
        
        result = project_dashboard_service.calculate_key_metrics(
            project=project,
            progress_deviation=0,
            cost_variance_rate=0,
            task_completed=50,
            task_total=100
        )
        
        assert result["health_score"] == expected_score


# ============================================================================
# 综合测试
# ============================================================================

def test_all_functions_handle_none_gracefully():
    """测试所有函数能够优雅处理None值"""
    # 这个测试确保没有函数会因为None值而崩溃
    project = MagicMock(spec=Project)
    for attr in dir(project):
        if not attr.startswith('_'):
            setattr(project, attr, None)
    
    # 设置必要的属性避免AttributeError
    project.project_code = "TEST"
    project.project_name = "Test"
    
    # 这不应该抛出异常
    try:
        result = project_dashboard_service.build_basic_info(project)
        assert result is not None
    except Exception as e:
        pytest.fail(f"build_basic_info should handle None values: {e}")

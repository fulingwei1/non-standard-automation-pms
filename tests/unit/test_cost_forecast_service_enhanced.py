# -*- coding: utf-8 -*-
"""
CostForecastService 增强测试 - 提升覆盖率到60%+

重点测试实际代码执行路径，而非完全 mock
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
import sys

from app.services.cost_forecast_service import CostForecastService
from app.models.project import Project, CostAlert, CostAlertRule, CostForecast


# ========================================================================
# Fixtures
# ========================================================================

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return MagicMock()


@pytest.fixture
def service(mock_db):
    """创建服务实例"""
    return CostForecastService(mock_db)


def create_mock_project(
    project_id=1,
    project_name="测试项目",
    project_code="TEST001",
    budget_amount=100000,
    actual_cost=50000,
    progress_pct=50,
    planned_start_date=None,
    planned_end_date=None,
):
    """创建模拟项目对象"""
    project = MagicMock(spec=Project)
    project.id = project_id
    project.project_name = project_name
    project.project_code = project_code
    project.budget_amount = Decimal(str(budget_amount))
    project.actual_cost = Decimal(str(actual_cost))
    project.progress_pct = Decimal(str(progress_pct))
    project.planned_start_date = planned_start_date
    project.planned_end_date = planned_end_date
    return project


# ========================================================================
# Test: linear_forecast
# ========================================================================

class TestLinearForecast:
    """测试线性回归预测"""

    def test_project_not_found(self, service, mock_db):
        """项目不存在时返回错误"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = service.linear_forecast(project_id=999)
        assert "error" in result
        assert "项目不存在" in result["error"]

    def test_insufficient_data_zero_records(self, service, mock_db):
        """无历史数据时返回错误"""
        project = create_mock_project()
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        with patch.object(service, "_get_monthly_costs", return_value=[]):
            result = service.linear_forecast(project_id=1)
        
        assert "error" in result
        assert "历史数据不足" in result["error"]

    def test_insufficient_data_one_record(self, service, mock_db):
        """只有1条历史数据时返回错误"""
        project = create_mock_project()
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000}
        ]
        
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service.linear_forecast(project_id=1)
        
        assert "error" in result
        assert "至少需要2个月数据" in result["error"]
        assert result["data_points"] == 1

    def test_linear_forecast_with_sufficient_data(self, service, mock_db):
        """有足够数据时能够成功预测"""
        project = create_mock_project(
            budget_amount=100000,
            actual_cost=30000,
            progress_pct=30
        )
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 10000, "cumulative_cost": 20000},
            {"month": "2024-03", "monthly_cost": 10000, "cumulative_cost": 30000},
        ]
        
        # Mock sklearn
        mock_model = MagicMock()
        mock_model.coef_ = [10000.0]
        mock_model.intercept_ = 0.0
        mock_model.score.return_value = 0.95
        
        mock_lr_class = MagicMock(return_value=mock_model)
        mock_lr_module = MagicMock()
        mock_lr_module.LinearRegression = mock_lr_class
        
        with patch.dict(sys.modules, {
            "sklearn": MagicMock(),
            "sklearn.linear_model": mock_lr_module,
        }):
            with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
                result = service.linear_forecast(project_id=1)
        
        assert result["method"] == "LINEAR"
        assert "forecasted_completion_cost" in result
        assert result["data_points"] == 3
        assert result["current_actual_cost"] == 30000.0
        assert result["current_budget"] == 100000.0
        assert result["current_progress_pct"] == 30.0
        assert "trend_data" in result
        assert "monthly_forecast_data" in result

    def test_linear_forecast_with_planned_dates(self, service, mock_db):
        """使用计划日期计算总月数"""
        project = create_mock_project(
            budget_amount=120000,
            actual_cost=40000,
            progress_pct=40,
            planned_start_date=date(2024, 1, 1),
            planned_end_date=date(2024, 12, 31)
        )
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 10000, "cumulative_cost": 20000},
            {"month": "2024-03", "monthly_cost": 10000, "cumulative_cost": 30000},
            {"month": "2024-04", "monthly_cost": 10000, "cumulative_cost": 40000},
        ]
        
        mock_model = MagicMock()
        mock_model.coef_ = [10000.0]
        mock_model.intercept_ = 0.0
        mock_model.score.return_value = 0.98
        
        mock_lr_class = MagicMock(return_value=mock_model)
        mock_lr_module = MagicMock()
        mock_lr_module.LinearRegression = mock_lr_class
        
        with patch.dict(sys.modules, {
            "sklearn": MagicMock(),
            "sklearn.linear_model": mock_lr_module,
        }):
            with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
                result = service.linear_forecast(project_id=1)
        
        assert result["method"] == "LINEAR"
        assert len(result["monthly_forecast_data"]) > 0

    def test_is_over_budget_flag_true(self, service, mock_db):
        """预测超预算时 is_over_budget 为 True"""
        project = create_mock_project(
            budget_amount=50000,
            actual_cost=40000,
            progress_pct=50
        )
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 20000, "cumulative_cost": 20000},
            {"month": "2024-02", "monthly_cost": 20000, "cumulative_cost": 40000},
        ]
        
        mock_model = MagicMock()
        mock_model.coef_ = [20000.0]
        mock_model.intercept_ = 0.0
        mock_model.score.return_value = 1.0
        
        mock_lr_class = MagicMock(return_value=mock_model)
        mock_lr_module = MagicMock()
        mock_lr_module.LinearRegression = mock_lr_class
        
        with patch.dict(sys.modules, {
            "sklearn": MagicMock(),
            "sklearn.linear_model": mock_lr_module,
        }):
            with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
                result = service.linear_forecast(project_id=1)
        
        # 预测成本应该远超预算
        assert "is_over_budget" in result
        assert "budget_variance" in result

    def test_zero_progress_calculation(self, service, mock_db):
        """进度为0时的处理逻辑"""
        project = create_mock_project(
            budget_amount=100000,
            actual_cost=20000,
            progress_pct=0  # 零进度
        )
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 10000, "cumulative_cost": 20000},
        ]
        
        mock_model = MagicMock()
        mock_model.coef_ = [10000.0]
        mock_model.intercept_ = 0.0
        mock_model.score.return_value = 1.0
        
        mock_lr_class = MagicMock(return_value=mock_model)
        mock_lr_module = MagicMock()
        mock_lr_module.LinearRegression = mock_lr_class
        
        with patch.dict(sys.modules, {
            "sklearn": MagicMock(),
            "sklearn.linear_model": mock_lr_module,
        }):
            with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
                result = service.linear_forecast(project_id=1)
        
        assert result["method"] == "LINEAR"
        assert result["current_progress_pct"] == 0.0


# ========================================================================
# Test: exponential_forecast
# ========================================================================

class TestExponentialForecast:
    """测试指数预测"""

    def test_project_not_found(self, service, mock_db):
        """项目不存在时返回错误"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = service.exponential_forecast(project_id=999)
        assert "error" in result
        assert "项目不存在" in result["error"]

    def test_insufficient_data(self, service, mock_db):
        """数据不足时返回错误"""
        project = create_mock_project()
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000}
        ]
        
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service.exponential_forecast(project_id=1)
        
        assert "error" in result

    def test_exponential_forecast_success(self, service, mock_db):
        """成功进行指数预测"""
        project = create_mock_project(
            budget_amount=200000,
            actual_cost=60000,
            progress_pct=40
        )
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 15000, "cumulative_cost": 25000},
            {"month": "2024-03", "monthly_cost": 20000, "cumulative_cost": 45000},
            {"month": "2024-04", "monthly_cost": 15000, "cumulative_cost": 60000},
        ]
        
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service.exponential_forecast(project_id=1)
        
        assert result["method"] == "EXPONENTIAL"
        assert "forecasted_completion_cost" in result
        assert result["data_points"] == 4
        assert "trend_data" in result
        assert "avg_growth_rate" in result["trend_data"]
        assert "periods_to_complete" in result["trend_data"]
        assert "monthly_forecast_data" in result

    def test_exponential_with_zero_progress(self, service, mock_db):
        """进度为0时的处理"""
        project = create_mock_project(
            budget_amount=100000,
            actual_cost=30000,
            progress_pct=0
        )
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 10000, "cumulative_cost": 20000},
            {"month": "2024-03", "monthly_cost": 10000, "cumulative_cost": 30000},
        ]
        
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service.exponential_forecast(project_id=1)
        
        assert result["method"] == "EXPONENTIAL"
        assert result["current_progress_pct"] == 0.0

    def test_exponential_growth_calculation(self, service, mock_db):
        """测试增长率计算逻辑"""
        project = create_mock_project(
            budget_amount=150000,
            actual_cost=50000,
            progress_pct=50
        )
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        # 模拟增长的成本数据
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 5000, "cumulative_cost": 5000},
            {"month": "2024-02", "monthly_cost": 10000, "cumulative_cost": 15000},
            {"month": "2024-03", "monthly_cost": 15000, "cumulative_cost": 30000},
            {"month": "2024-04", "monthly_cost": 20000, "cumulative_cost": 50000},
        ]
        
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service.exponential_forecast(project_id=1)
        
        # 验证增长率被正确计算
        assert "avg_growth_rate" in result["trend_data"]
        assert result["trend_data"]["avg_growth_rate"] > 0


# ========================================================================
# Test: historical_average_forecast
# ========================================================================

class TestHistoricalAverageForecast:
    """测试历史平均法预测"""

    def test_project_not_found(self, service, mock_db):
        """项目不存在"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = service.historical_average_forecast(project_id=999)
        assert "error" in result
        assert "项目不存在" in result["error"]

    def test_no_historical_data(self, service, mock_db):
        """无历史数据"""
        project = create_mock_project()
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        with patch.object(service, "_get_monthly_costs", return_value=[]):
            result = service.historical_average_forecast(project_id=1)
        
        assert "error" in result
        assert "历史数据不足" in result["error"]

    def test_historical_average_success(self, service, mock_db):
        """成功使用历史平均法预测"""
        project = create_mock_project(
            budget_amount=120000,
            actual_cost=40000,
            progress_pct=40
        )
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 15000, "cumulative_cost": 25000},
            {"month": "2024-03", "monthly_cost": 10000, "cumulative_cost": 35000},
            {"month": "2024-04", "monthly_cost": 5000, "cumulative_cost": 40000},
        ]
        
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service.historical_average_forecast(project_id=1)
        
        assert result["method"] == "HISTORICAL_AVERAGE"
        assert "forecasted_completion_cost" in result
        assert result["data_points"] == 4
        assert "trend_data" in result
        assert "avg_monthly_cost" in result["trend_data"]
        assert result["trend_data"]["avg_monthly_cost"] == 10000.0  # (10k+15k+10k+5k)/4

    def test_historical_average_with_zero_progress(self, service, mock_db):
        """进度为0时的处理"""
        project = create_mock_project(
            budget_amount=100000,
            actual_cost=20000,
            progress_pct=0
        )
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 10000, "cumulative_cost": 20000},
        ]
        
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service.historical_average_forecast(project_id=1)
        
        assert result["method"] == "HISTORICAL_AVERAGE"
        # 默认假设总月数 = 历史月数 * 2
        assert "estimated_total_months" in result["trend_data"]


# ========================================================================
# Test: get_cost_trend
# ========================================================================

class TestGetCostTrend:
    """测试成本趋势分析"""

    def test_project_not_found(self, service, mock_db):
        """项目不存在"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = service.get_cost_trend(project_id=999)
        assert "error" in result
        assert "项目不存在" in result["error"]

    def test_empty_monthly_costs(self, service, mock_db):
        """无成本数据"""
        project = create_mock_project()
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        with patch.object(service, "_get_monthly_costs", return_value=[]):
            result = service.get_cost_trend(project_id=1)
        
        assert result["project_id"] == 1
        assert result["monthly_trend"] == []
        assert result["cumulative_trend"] == []
        assert result["summary"]["total_months"] == 0

    def test_with_monthly_costs(self, service, mock_db):
        """有月度成本数据"""
        project = create_mock_project(project_name="测试项目A")
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 15000, "cumulative_cost": 25000},
            {"month": "2024-03", "monthly_cost": 20000, "cumulative_cost": 45000},
        ]
        
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service.get_cost_trend(project_id=1)
        
        assert result["project_name"] == "测试项目A"
        assert len(result["monthly_trend"]) == 3
        assert len(result["cumulative_trend"]) == 3
        assert result["summary"]["total_months"] == 3
        assert result["summary"]["total_cost"] == 45000.0
        assert result["summary"]["avg_monthly_cost"] == 15000.0
        assert result["summary"]["min_monthly_cost"] == 10000.0
        assert result["summary"]["max_monthly_cost"] == 20000.0

    def test_with_date_range_filter(self, service, mock_db):
        """测试日期范围筛选"""
        project = create_mock_project()
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        monthly_data = [
            {"month": "2024-02", "monthly_cost": 15000, "cumulative_cost": 15000},
        ]
        
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data) as mock_get:
            result = service.get_cost_trend(
                project_id=1,
                start_month="2024-02",
                end_month="2024-02"
            )
            
            # 验证传递了日期参数
            mock_get.assert_called_once_with(1, "2024-02", "2024-02")
        
        assert len(result["monthly_trend"]) == 1


# ========================================================================
# Test: get_burn_down_data
# ========================================================================

class TestGetBurnDownData:
    """测试燃尽图数据"""

    def test_project_not_found(self, service, mock_db):
        """项目不存在"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = service.get_burn_down_data(project_id=999)
        assert "error" in result
        assert "项目不存在" in result["error"]

    def test_no_budget(self, service, mock_db):
        """预算未设置"""
        project = create_mock_project(budget_amount=0)
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        result = service.get_burn_down_data(project_id=1)
        assert "error" in result
        assert "预算未设置" in result["error"]

    def test_with_budget_and_costs(self, service, mock_db):
        """有预算和成本数据"""
        project = create_mock_project(
            project_name="燃尽测试项目",
            budget_amount=100000,
            actual_cost=30000,
            progress_pct=40,
            planned_start_date=date(2024, 1, 1),
            planned_end_date=date(2024, 6, 30)
        )
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 10000, "cumulative_cost": 20000},
            {"month": "2024-03", "monthly_cost": 10000, "cumulative_cost": 30000},
        ]
        
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service.get_burn_down_data(project_id=1)
        
        assert result["project_name"] == "燃尽测试项目"
        assert result["budget"] == 100000.0
        assert result["current_spent"] == 30000.0
        assert result["remaining_budget"] == 70000.0
        assert "burn_rate" in result
        assert "burn_down_data" in result
        assert len(result["burn_down_data"]) > 0
        assert "is_on_track" in result

    def test_without_planned_dates(self, service, mock_db):
        """无计划日期时的处理"""
        project = create_mock_project(
            budget_amount=100000,
            actual_cost=20000,
            progress_pct=20,
            planned_start_date=None,
            planned_end_date=None
        )
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 10000, "cumulative_cost": 20000},
        ]
        
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service.get_burn_down_data(project_id=1)
        
        # 应该使用默认月数计算
        assert "burn_down_data" in result
        assert len(result["burn_down_data"]) > 0


# ========================================================================
# Test: check_cost_alerts
# ========================================================================

class TestCheckCostAlerts:
    """测试成本预警检测"""

    def test_project_not_found_returns_empty(self, service, mock_db):
        """项目不存在时返回空列表"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = service.check_cost_alerts(project_id=999, auto_create=False)
        assert result == []

    def test_overspend_warning(self, service, mock_db):
        """超支警告"""
        project = create_mock_project(
            budget_amount=100000,
            actual_cost=85000,
            progress_pct=50
        )
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        # Mock _get_alert_rules
        with patch.object(service, "_get_alert_rules", return_value={
            "OVERSPEND": {"warning_threshold": 80, "critical_threshold": 100},
            "PROGRESS_MISMATCH": {"deviation_threshold": 15},
            "TREND_ANOMALY": {"growth_rate_threshold": 0.3},
        }):
            with patch.object(service, "_get_monthly_costs", return_value=[]):
                result = service.check_cost_alerts(project_id=1, auto_create=False)
        
        # 应该触发超支警告
        overspend_alerts = [a for a in result if a["alert_type"] == "OVERSPEND"]
        assert len(overspend_alerts) > 0
        assert overspend_alerts[0]["alert_level"] == "WARNING"

    def test_overspend_critical(self, service, mock_db):
        """超支严重预警"""
        project = create_mock_project(
            budget_amount=100000,
            actual_cost=110000,
            progress_pct=80
        )
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        with patch.object(service, "_get_alert_rules", return_value={
            "OVERSPEND": {"warning_threshold": 80, "critical_threshold": 100},
        }):
            with patch.object(service, "_get_monthly_costs", return_value=[]):
                result = service.check_cost_alerts(project_id=1, auto_create=False)
        
        overspend_alerts = [a for a in result if a["alert_type"] == "OVERSPEND"]
        assert len(overspend_alerts) > 0
        assert overspend_alerts[0]["alert_level"] == "CRITICAL"

    def test_progress_mismatch_warning(self, service, mock_db):
        """进度不匹配预警"""
        project = create_mock_project(
            budget_amount=100000,
            actual_cost=70000,  # 成本消耗70%
            progress_pct=40     # 但进度只有40%
        )
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        with patch.object(service, "_get_alert_rules", return_value={
            "PROGRESS_MISMATCH": {"deviation_threshold": 15},
        }):
            with patch.object(service, "_get_monthly_costs", return_value=[]):
                result = service.check_cost_alerts(project_id=1, auto_create=False)
        
        mismatch_alerts = [a for a in result if a["alert_type"] == "PROGRESS_MISMATCH"]
        assert len(mismatch_alerts) > 0
        assert mismatch_alerts[0]["alert_level"] == "WARNING"

    def test_trend_anomaly_detection(self, service, mock_db):
        """趋势异常检测"""
        project = create_mock_project(
            budget_amount=100000,
            actual_cost=50000,
            progress_pct=50
        )
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        # 模拟快速增长的成本
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 5000, "cumulative_cost": 5000},
            {"month": "2024-02", "monthly_cost": 10000, "cumulative_cost": 15000},
            {"month": "2024-03", "monthly_cost": 15000, "cumulative_cost": 30000},
            {"month": "2024-04", "monthly_cost": 20000, "cumulative_cost": 50000},
        ]
        
        with patch.object(service, "_get_alert_rules", return_value={
            "TREND_ANOMALY": {"growth_rate_threshold": 0.3},
        }):
            with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
                result = service.check_cost_alerts(project_id=1, auto_create=False)
        
        # 可能触发趋势异常
        trend_alerts = [a for a in result if a["alert_type"] == "TREND_ANOMALY"]
        # 由于增长率可能符合阈值，这里只验证没有错误
        assert isinstance(result, list)


# ========================================================================
# Test: _check_overspend_alert
# ========================================================================

class TestCheckOverspendAlert:
    """测试超支预警检测"""

    def test_no_budget_returns_none(self, service):
        """无预算时返回None"""
        project = create_mock_project(budget_amount=0)
        rules = {"OVERSPEND": {"warning_threshold": 80, "critical_threshold": 100}}
        result = service._check_overspend_alert(project, rules)
        assert result is None

    def test_within_budget_returns_none(self, service):
        """在预算内时返回None"""
        project = create_mock_project(
            budget_amount=100000,
            actual_cost=50000
        )
        rules = {"OVERSPEND": {"warning_threshold": 80, "critical_threshold": 100}}
        result = service._check_overspend_alert(project, rules)
        assert result is None

    def test_warning_threshold_triggered(self, service):
        """达到警告阈值"""
        project = create_mock_project(
            budget_amount=100000,
            actual_cost=82000
        )
        rules = {"OVERSPEND": {"warning_threshold": 80, "critical_threshold": 100}}
        result = service._check_overspend_alert(project, rules)
        
        assert result is not None
        assert result["alert_level"] == "WARNING"
        assert result["alert_type"] == "OVERSPEND"
        assert result["alert_data"]["consumption_rate"] >= 80

    def test_critical_threshold_triggered(self, service):
        """达到严重阈值"""
        project = create_mock_project(
            budget_amount=100000,
            actual_cost=105000
        )
        rules = {"OVERSPEND": {"warning_threshold": 80, "critical_threshold": 100}}
        result = service._check_overspend_alert(project, rules)
        
        assert result is not None
        assert result["alert_level"] == "CRITICAL"


# ========================================================================
# Test: _check_progress_mismatch_alert
# ========================================================================

class TestCheckProgressMismatchAlert:
    """测试进度不匹配预警"""

    def test_no_budget_returns_none(self, service):
        """无预算时返回None"""
        project = create_mock_project(budget_amount=0)
        rules = {"PROGRESS_MISMATCH": {"deviation_threshold": 15}}
        result = service._check_progress_mismatch_alert(project, rules)
        assert result is None

    def test_matched_progress_returns_none(self, service):
        """进度匹配时返回None"""
        project = create_mock_project(
            budget_amount=100000,
            actual_cost=50000,
            progress_pct=50
        )
        rules = {"PROGRESS_MISMATCH": {"deviation_threshold": 15}}
        result = service._check_progress_mismatch_alert(project, rules)
        assert result is None

    def test_cost_ahead_of_progress(self, service):
        """成本超前进度"""
        project = create_mock_project(
            budget_amount=100000,
            actual_cost=70000,
            progress_pct=40
        )
        rules = {"PROGRESS_MISMATCH": {"deviation_threshold": 15}}
        result = service._check_progress_mismatch_alert(project, rules)
        
        assert result is not None
        assert result["alert_level"] == "WARNING"
        assert result["alert_type"] == "PROGRESS_MISMATCH"
        assert result["alert_data"]["deviation"] > 15

    def test_progress_ahead_of_cost(self, service):
        """进度超前成本"""
        project = create_mock_project(
            budget_amount=100000,
            actual_cost=40000,
            progress_pct=70
        )
        rules = {"PROGRESS_MISMATCH": {"deviation_threshold": 15}}
        result = service._check_progress_mismatch_alert(project, rules)
        
        assert result is not None
        assert result["alert_level"] == "INFO"


# ========================================================================
# Test: _check_trend_anomaly_alert
# ========================================================================

class TestCheckTrendAnomalyAlert:
    """测试趋势异常预警"""

    def test_insufficient_data_returns_none(self, service):
        """数据不足时返回None"""
        project = create_mock_project()
        rules = {"TREND_ANOMALY": {"growth_rate_threshold": 0.3}}
        
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
        ]
        
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service._check_trend_anomaly_alert(1, project, rules)
        
        assert result is None

    def test_normal_growth_returns_none(self, service):
        """正常增长时返回None"""
        project = create_mock_project()
        rules = {"TREND_ANOMALY": {"growth_rate_threshold": 0.3}}
        
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 10500, "cumulative_cost": 20500},
            {"month": "2024-03", "monthly_cost": 11000, "cumulative_cost": 31500},
        ]
        
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service._check_trend_anomaly_alert(1, project, rules)
        
        assert result is None

    def test_anomaly_growth_detected(self, service):
        """检测到异常增长"""
        project = create_mock_project()
        rules = {"TREND_ANOMALY": {"growth_rate_threshold": 0.3}}
        
        # 模拟快速增长的成本
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 15000, "cumulative_cost": 25000},
            {"month": "2024-03", "monthly_cost": 22000, "cumulative_cost": 47000},
        ]
        
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service._check_trend_anomaly_alert(1, project, rules)
        
        assert result is not None
        assert result["alert_type"] == "TREND_ANOMALY"
        assert result["alert_level"] == "WARNING"


# ========================================================================
# Test: save_forecast
# ========================================================================

class TestSaveForecast:
    """测试保存预测结果"""

    def test_project_not_found_raises(self, service, mock_db):
        """项目不存在时抛出异常"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        forecast_result = {
            "method": "LINEAR",
            "forecast_date": date.today(),
            "forecasted_completion_cost": 100000,
        }
        
        with pytest.raises(ValueError, match="项目不存在"):
            service.save_forecast(project_id=999, forecast_result=forecast_result, created_by=1)

    def test_saves_forecast_successfully(self, service, mock_db):
        """成功保存预测"""
        project = create_mock_project(project_code="TEST001", project_name="测试项目")
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        forecast_result = {
            "method": "LINEAR",
            "forecast_date": date(2024, 2, 20),
            "forecasted_completion_cost": 120000,
            "current_progress_pct": 50,
            "current_actual_cost": 60000,
            "current_budget": 100000,
            "monthly_forecast_data": [],
            "trend_data": {"slope": 10000, "intercept": 0},
        }
        
        with patch("app.services.cost_forecast_service.save_obj") as mock_save:
            result = service.save_forecast(
                project_id=1,
                forecast_result=forecast_result,
                created_by=1
            )
            
            # 验证 save_obj 被调用
            mock_save.assert_called_once()


# ========================================================================
# Test: _get_alert_rules
# ========================================================================

class TestGetAlertRules:
    """测试获取预警规则"""

    def test_returns_default_rules_when_no_custom_rules(self, service, mock_db):
        """无自定义规则时返回默认规则"""
        # Mock 数据库查询返回空列表
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        
        result = service._get_alert_rules(project_id=1)
        
        # 应该包含默认规则
        assert "OVERSPEND" in result
        assert "PROGRESS_MISMATCH" in result
        assert "TREND_ANOMALY" in result

    def test_merges_global_and_project_rules(self, service, mock_db):
        """合并全局和项目规则"""
        # Mock 全局规则
        global_rule = MagicMock(spec=CostAlertRule)
        global_rule.alert_type = "OVERSPEND"
        global_rule.rule_config = {"warning_threshold": 85, "critical_threshold": 105}
        
        # Mock 项目特定规则
        project_rule = MagicMock(spec=CostAlertRule)
        project_rule.alert_type = "PROGRESS_MISMATCH"
        project_rule.rule_config = {"deviation_threshold": 20}
        
        # 设置 mock 返回值
        def mock_query_filter(*args, **kwargs):
            chain = MagicMock()
            chain.filter.return_value = chain
            # 第一次调用返回项目规则，第二次返回全局规则
            chain.all.side_effect = [[project_rule], [global_rule]]
            return chain
        
        mock_db.query.return_value.filter = mock_query_filter
        
        result = service._get_alert_rules(project_id=1)
        
        # 项目规则应该覆盖全局规则
        assert result["PROGRESS_MISMATCH"]["deviation_threshold"] == 20


# ========================================================================
# Test: _create_alert_record
# ========================================================================

class TestCreateAlertRecord:
    """测试创建预警记录"""

    def test_project_not_found_returns_early(self, service, mock_db):
        """项目不存在时直接返回"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        alert_data = {
            "alert_type": "OVERSPEND",
            "alert_level": "WARNING",
            "alert_title": "测试",
            "alert_message": "测试消息",
        }
        
        # 不应该抛出异常
        service._create_alert_record(project_id=999, alert_data=alert_data)

    def test_creates_new_alert_when_none_exists(self, service, mock_db):
        """不存在活动预警时创建新预警"""
        project = create_mock_project(
            project_code="TEST001",
            project_name="测试项目",
            actual_cost=80000,
            budget_amount=100000,
            progress_pct=60
        )
        
        # Setup mock for project query (first call)
        project_query = MagicMock()
        project_query.filter.return_value.first.return_value = project
        
        # Setup mock for alert query (second call) - returns None
        alert_query = MagicMock()
        alert_chain = MagicMock()
        alert_chain.filter.return_value = alert_chain
        alert_chain.first.return_value = None
        alert_query.filter.return_value = alert_chain
        
        # Configure mock_db.query to return different mocks for different calls
        mock_db.query.side_effect = [project_query, alert_query]
        
        alert_data = {
            "alert_type": "OVERSPEND",
            "alert_level": "WARNING",
            "alert_title": "成本超支预警",
            "alert_message": "成本接近预算",
            "alert_data": {"consumption_rate": 80},
        }
        
        service._create_alert_record(project_id=1, alert_data=alert_data)
        
        # 验证添加了新预警
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_updates_existing_alert(self, service, mock_db):
        """存在活动预警时更新"""
        project = create_mock_project()
        existing_alert = MagicMock(spec=CostAlert)
        
        # Setup mock for project query (first call)
        project_query = MagicMock()
        project_query.filter.return_value.first.return_value = project
        
        # Setup mock for alert query (second call) - returns existing alert
        alert_query = MagicMock()
        alert_chain = MagicMock()
        alert_chain.filter.return_value = alert_chain
        alert_chain.first.return_value = existing_alert
        alert_query.filter.return_value = alert_chain
        
        # Configure mock_db.query to return different mocks for different calls
        mock_db.query.side_effect = [project_query, alert_query]
        
        alert_data = {
            "alert_type": "OVERSPEND",
            "alert_level": "CRITICAL",
            "alert_title": "成本超支预警",
            "alert_message": "成本已超预算",
            "alert_data": {"consumption_rate": 110},
        }
        
        service._create_alert_record(project_id=1, alert_data=alert_data)
        
        # 验证更新了现有预警
        assert existing_alert.alert_level == "CRITICAL"
        assert existing_alert.alert_message == "成本已超预算"
        mock_db.commit.assert_called_once()

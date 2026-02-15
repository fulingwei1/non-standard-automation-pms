# -*- coding: utf-8 -*-
"""
成本预测和趋势分析测试

测试覆盖：
1. 数据模型测试（3个测试）
2. 预测算法测试（6个测试）
3. 趋势分析测试（3个测试）
4. 预警检测测试（5个测试）
5. API端点测试（6个测试）

总计：23个测试用例
"""

import json
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.project import (
    CostAlert,
    CostAlertRule,
    CostForecast,
    FinancialProjectCost,
    Project,
    ProjectCost,
)
from app.models.user import User
from app.services.cost_forecast_service import CostForecastService


# ============================================================================
# 测试夹具（Fixtures）
# ============================================================================


@pytest.fixture
def test_project(db: Session, test_user: User) -> Project:
    """创建测试项目"""
    project = Project(
        project_code="TEST-FORECAST-001",
        project_name="成本预测测试项目",
        customer_name="测试客户",
        budget_amount=Decimal("1000000.00"),
        actual_cost=Decimal("0.00"),
        progress_pct=Decimal("0.00"),
        planned_start_date=date.today() - timedelta(days=180),
        planned_end_date=date.today() + timedelta(days=180),
        pm_id=test_user.id,
        created_by=test_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture
def test_project_with_costs(
    db: Session, test_project: Project, test_user: User
) -> Project:
    """创建带有成本数据的测试项目"""
    # 创建6个月的成本数据
    base_date = date.today() - timedelta(days=180)

    for i in range(6):
        month_date = base_date + timedelta(days=30 * i)
        cost_month = month_date.strftime("%Y-%m")

        # 项目成本（逐月递增）
        cost1 = ProjectCost(
            project_id=test_project.id,
            cost_type="MATERIAL",
            cost_category="物料成本",
            amount=Decimal(str(50000 + i * 10000)),
            cost_date=month_date,
            created_by=test_user.id,
        )
        db.add(cost1)

        # 财务成本
        cost2 = FinancialProjectCost(
            project_id=test_project.id,
            project_code=test_project.project_code,
            cost_type="LABOR",
            cost_category="人工费",
            amount=Decimal(str(30000 + i * 5000)),
            cost_date=month_date,
            cost_month=cost_month,
            uploaded_by=test_user.id,
        )
        db.add(cost2)

    # 更新项目实际成本
    total_cost = sum([50000 + i * 10000 + 30000 + i * 5000 for i in range(6)])
    test_project.actual_cost = Decimal(str(total_cost))
    test_project.progress_pct = Decimal("50.00")

    db.commit()
    db.refresh(test_project)
    return test_project


@pytest.fixture
def cost_forecast_service(db: Session) -> CostForecastService:
    """创建成本预测服务实例"""
    return CostForecastService(db)


# ============================================================================
# 1. 数据模型测试（3个测试）
# ============================================================================


def test_cost_forecast_model_creation(
    db: Session, test_project: Project, test_user: User
):
    """测试成本预测模型创建"""
    forecast = CostForecast(
        project_id=test_project.id,
        project_code=test_project.project_code,
        project_name=test_project.project_name,
        forecast_method="LINEAR",
        forecast_date=date.today(),
        forecast_month=date.today().strftime("%Y-%m"),
        forecasted_completion_cost=Decimal("950000.00"),
        current_progress_pct=Decimal("50.00"),
        current_actual_cost=Decimal("480000.00"),
        current_budget=Decimal("1000000.00"),
        monthly_forecast_data=[],
        trend_data={"slope": 50000, "intercept": 100000, "r_squared": 0.95},
        created_by=test_user.id,
    )

    db.add(forecast)
    db.commit()
    db.refresh(forecast)

    assert forecast.id is not None
    assert forecast.project_id == test_project.id
    assert forecast.forecast_method == "LINEAR"
    assert forecast.forecasted_completion_cost == Decimal("950000.00")


def test_cost_alert_model_creation(
    db: Session, test_project: Project, test_user: User
):
    """测试成本预警模型创建"""
    alert = CostAlert(
        project_id=test_project.id,
        project_code=test_project.project_code,
        alert_type="OVERSPEND",
        alert_level="WARNING",
        alert_date=date.today(),
        alert_title="超支预警",
        alert_message="成本接近预算",
        current_cost=Decimal("850000.00"),
        budget_amount=Decimal("1000000.00"),
        threshold=Decimal("80.00"),
        status="ACTIVE",
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    assert alert.id is not None
    assert alert.alert_type == "OVERSPEND"
    assert alert.alert_level == "WARNING"


def test_cost_alert_rule_model_creation(db: Session, test_user: User):
    """测试成本预警规则模型创建"""
    rule = CostAlertRule(
        rule_code="TEST_RULE_001",
        rule_name="测试预警规则",
        alert_type="OVERSPEND",
        rule_config={"warning_threshold": 80, "critical_threshold": 100},
        is_enabled=True,
        priority=10,
        created_by=test_user.id,
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)

    assert rule.id is not None
    assert rule.rule_code == "TEST_RULE_001"
    assert rule.is_enabled is True


# ============================================================================
# 2. 预测算法测试（6个测试）
# ============================================================================


def test_linear_forecast_basic(
    db: Session,
    test_project_with_costs: Project,
    cost_forecast_service: CostForecastService,
):
    """测试线性回归预测（基本功能）"""
    result = cost_forecast_service.linear_forecast(test_project_with_costs.id)

    assert "error" not in result
    assert result["method"] == "LINEAR"
    assert "forecasted_completion_cost" in result
    assert result["forecasted_completion_cost"] > 0
    assert "trend_data" in result
    assert "slope" in result["trend_data"]
    assert "r_squared" in result["trend_data"]
    assert result["data_points"] == 6


def test_linear_forecast_insufficient_data(
    db: Session, test_project: Project, cost_forecast_service: CostForecastService
):
    """测试线性回归预测（数据不足）"""
    # 只创建1个月的数据
    cost = ProjectCost(
        project_id=test_project.id,
        cost_type="MATERIAL",
        amount=Decimal("50000.00"),
        cost_date=date.today(),
    )
    db.add(cost)
    db.commit()

    result = cost_forecast_service.linear_forecast(test_project.id)

    assert "error" in result
    assert "历史数据不足" in result["error"]


def test_exponential_forecast(
    db: Session,
    test_project_with_costs: Project,
    cost_forecast_service: CostForecastService,
):
    """测试指数预测"""
    result = cost_forecast_service.exponential_forecast(test_project_with_costs.id)

    assert "error" not in result
    assert result["method"] == "EXPONENTIAL"
    assert "forecasted_completion_cost" in result
    assert "trend_data" in result
    assert "avg_growth_rate" in result["trend_data"]
    assert result["data_points"] == 6


def test_historical_average_forecast(
    db: Session,
    test_project_with_costs: Project,
    cost_forecast_service: CostForecastService,
):
    """测试历史平均法预测"""
    result = cost_forecast_service.historical_average_forecast(
        test_project_with_costs.id
    )

    assert "error" not in result
    assert result["method"] == "HISTORICAL_AVERAGE"
    assert "forecasted_completion_cost" in result
    assert "trend_data" in result
    assert "avg_monthly_cost" in result["trend_data"]


def test_forecast_monthly_data_generation(
    db: Session,
    test_project_with_costs: Project,
    cost_forecast_service: CostForecastService,
):
    """测试月度预测数据生成"""
    result = cost_forecast_service.linear_forecast(test_project_with_costs.id)

    assert "monthly_forecast_data" in result
    monthly_data = result["monthly_forecast_data"]
    assert len(monthly_data) > 6  # 应该有历史+未来数据

    # 检查数据结构
    for item in monthly_data:
        assert "month" in item
        assert "type" in item  # actual or forecast
        assert item["type"] in ["actual", "forecast"]
        assert "monthly_cost" in item or "cumulative_cost" in item


def test_forecast_budget_comparison(
    db: Session,
    test_project_with_costs: Project,
    cost_forecast_service: CostForecastService,
):
    """测试预测结果与预算对比"""
    result = cost_forecast_service.linear_forecast(test_project_with_costs.id)

    assert "is_over_budget" in result
    assert "budget_variance" in result
    assert isinstance(result["is_over_budget"], bool)


# ============================================================================
# 3. 趋势分析测试（3个测试）
# ============================================================================


def test_get_cost_trend(
    db: Session,
    test_project_with_costs: Project,
    cost_forecast_service: CostForecastService,
):
    """测试成本趋势获取"""
    result = cost_forecast_service.get_cost_trend(test_project_with_costs.id)

    assert "error" not in result
    assert "monthly_trend" in result
    assert "cumulative_trend" in result
    assert "summary" in result

    # 验证月度趋势
    assert len(result["monthly_trend"]) == 6
    for item in result["monthly_trend"]:
        assert "month" in item
        assert "cost" in item

    # 验证累计趋势
    assert len(result["cumulative_trend"]) == 6


def test_get_cost_trend_with_date_range(
    db: Session,
    test_project_with_costs: Project,
    cost_forecast_service: CostForecastService,
):
    """测试带时间范围的成本趋势"""
    start_month = (date.today() - timedelta(days=120)).strftime("%Y-%m")
    end_month = (date.today() - timedelta(days=30)).strftime("%Y-%m")

    result = cost_forecast_service.get_cost_trend(
        test_project_with_costs.id, start_month, end_month
    )

    assert "error" not in result
    # 应该返回指定时间范围内的数据


def test_burn_down_data(
    db: Session,
    test_project_with_costs: Project,
    cost_forecast_service: CostForecastService,
):
    """测试成本燃尽图数据"""
    result = cost_forecast_service.get_burn_down_data(test_project_with_costs.id)

    assert "error" not in result
    assert "budget" in result
    assert "current_spent" in result
    assert "remaining_budget" in result
    assert "burn_rate" in result
    assert "burn_down_data" in result
    assert "is_on_track" in result

    # 验证燃尽数据
    burn_down_data = result["burn_down_data"]
    assert len(burn_down_data) > 0
    for item in burn_down_data:
        assert "month" in item
        assert "ideal_remaining" in item


# ============================================================================
# 4. 预警检测测试（5个测试）
# ============================================================================


def test_check_overspend_alert(
    db: Session,
    test_project_with_costs: Project,
    cost_forecast_service: CostForecastService,
):
    """测试超支预警检测"""
    # 设置项目成本接近预算
    test_project_with_costs.actual_cost = Decimal("850000.00")
    db.commit()

    alerts = cost_forecast_service.check_cost_alerts(
        test_project_with_costs.id, auto_create=False
    )

    # 应该检测到超支预警
    overspend_alerts = [a for a in alerts if a["alert_type"] == "OVERSPEND"]
    assert len(overspend_alerts) > 0
    assert overspend_alerts[0]["alert_level"] in ["WARNING", "CRITICAL"]


def test_check_progress_mismatch_alert(
    db: Session,
    test_project_with_costs: Project,
    cost_forecast_service: CostForecastService,
):
    """测试进度不匹配预警"""
    # 设置成本消耗与进度不匹配
    test_project_with_costs.actual_cost = Decimal("700000.00")  # 70%
    test_project_with_costs.progress_pct = Decimal("40.00")  # 40%
    db.commit()

    alerts = cost_forecast_service.check_cost_alerts(
        test_project_with_costs.id, auto_create=False
    )

    # 应该检测到进度不匹配预警
    progress_alerts = [a for a in alerts if a["alert_type"] == "PROGRESS_MISMATCH"]
    assert len(progress_alerts) > 0


def test_check_trend_anomaly_alert(
    db: Session,
    test_project_with_costs: Project,
    test_user: User,
    cost_forecast_service: CostForecastService,
):
    """测试趋势异常预警"""
    # 添加3个月的异常增长数据
    base_date = date.today() - timedelta(days=90)

    for i in range(3):
        month_date = base_date + timedelta(days=30 * i)
        # 成本急剧增长（模拟异常）
        cost = ProjectCost(
            project_id=test_project_with_costs.id,
            cost_type="MATERIAL",
            amount=Decimal(str(100000 * (i + 2))),  # 200k, 300k, 400k
            cost_date=month_date,
        )
        db.add(cost)

    db.commit()

    alerts = cost_forecast_service.check_cost_alerts(
        test_project_with_costs.id, auto_create=False
    )

    # 可能检测到趋势异常预警（取决于数据）
    # 这个测试主要验证逻辑不报错
    assert isinstance(alerts, list)


def test_alert_auto_creation(
    db: Session,
    test_project_with_costs: Project,
    cost_forecast_service: CostForecastService,
):
    """测试预警自动创建"""
    # 设置触发预警的条件
    test_project_with_costs.actual_cost = Decimal("850000.00")
    db.commit()

    # 清空之前的预警
    db.query(CostAlert).filter(
        CostAlert.project_id == test_project_with_costs.id
    ).delete()
    db.commit()

    # 检测预警并自动创建记录
    alerts = cost_forecast_service.check_cost_alerts(
        test_project_with_costs.id, auto_create=True
    )

    # 验证数据库中创建了预警记录
    db_alerts = (
        db.query(CostAlert)
        .filter(CostAlert.project_id == test_project_with_costs.id)
        .all()
    )
    assert len(db_alerts) > 0


def test_alert_rules_loading(
    db: Session, test_project: Project, cost_forecast_service: CostForecastService
):
    """测试预警规则加载"""
    # 创建自定义规则
    rule = CostAlertRule(
        rule_code="TEST_CUSTOM_RULE",
        rule_name="测试自定义规则",
        project_id=test_project.id,
        alert_type="OVERSPEND",
        rule_config={"warning_threshold": 70, "critical_threshold": 90},
        is_enabled=True,
    )
    db.add(rule)
    db.commit()

    # 获取规则（内部方法）
    rules = cost_forecast_service._get_alert_rules(test_project.id)

    assert "OVERSPEND" in rules
    # 项目规则应该覆盖全局规则
    assert rules["OVERSPEND"]["warning_threshold"] == 70


# ============================================================================
# 5. API端点测试（6个测试）
# ============================================================================


def test_api_get_forecast_linear(
    client, test_project_with_costs: Project, auth_headers
):
    """测试获取线性预测API"""
    response = client.get(
        f"/api/v1/projects/{test_project_with_costs.id}/costs/forecast?method=LINEAR",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    assert data["data"]["method"] == "LINEAR"


def test_api_get_forecast_exponential(
    client, test_project_with_costs: Project, auth_headers
):
    """测试获取指数预测API"""
    response = client.get(
        f"/api/v1/projects/{test_project_with_costs.id}/costs/forecast?method=EXPONENTIAL",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["method"] == "EXPONENTIAL"


def test_api_get_trend(client, test_project_with_costs: Project, auth_headers):
    """测试获取成本趋势API"""
    response = client.get(
        f"/api/v1/projects/{test_project_with_costs.id}/costs/trend",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "monthly_trend" in data["data"]
    assert "cumulative_trend" in data["data"]


def test_api_get_burn_down(client, test_project_with_costs: Project, auth_headers):
    """测试获取燃尽图API"""
    response = client.get(
        f"/api/v1/projects/{test_project_with_costs.id}/costs/burn-down",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "burn_down_data" in data["data"]
    assert "budget" in data["data"]


def test_api_get_alerts(client, test_project_with_costs: Project, auth_headers):
    """测试获取成本预警API"""
    # 设置触发预警的条件
    test_project_with_costs.actual_cost = Decimal("850000.00")

    response = client.get(
        f"/api/v1/projects/{test_project_with_costs.id}/costs/alerts",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data["data"]


def test_api_compare_methods(client, test_project_with_costs: Project, auth_headers):
    """测试对比预测方法API"""
    response = client.get(
        f"/api/v1/projects/{test_project_with_costs.id}/costs/compare-methods",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "methods" in data["data"]
    assert "comparison" in data["data"]
    assert "LINEAR" in data["data"]["methods"]


# ============================================================================
# 6. 集成测试
# ============================================================================


def test_full_forecast_workflow(
    db: Session,
    test_project_with_costs: Project,
    test_user: User,
    cost_forecast_service: CostForecastService,
):
    """测试完整预测工作流"""
    # 1. 执行预测
    linear_result = cost_forecast_service.linear_forecast(test_project_with_costs.id)
    assert "error" not in linear_result

    # 2. 保存预测结果
    forecast = cost_forecast_service.save_forecast(
        test_project_with_costs.id, linear_result, test_user.id
    )
    assert forecast.id is not None

    # 3. 检查预警
    alerts = cost_forecast_service.check_cost_alerts(
        test_project_with_costs.id, auto_create=True
    )
    assert isinstance(alerts, list)

    # 4. 获取趋势
    trend = cost_forecast_service.get_cost_trend(test_project_with_costs.id)
    assert "monthly_trend" in trend

    # 5. 获取燃尽图
    burn_down = cost_forecast_service.get_burn_down_data(test_project_with_costs.id)
    assert "burn_down_data" in burn_down

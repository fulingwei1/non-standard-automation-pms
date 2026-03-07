# -*- coding: utf-8 -*-
"""
成本预测服务模块分支测试
目标：将分支覆盖率从0%提升到80%以上

包含以下服务的分支测试：
1. CostForecastService (app/services/cost/cost_forecast_service.py) - 成本预测服务
2. EVMService (app/services/evm_service.py) - EVM挣值管理服务
3. CostCollectionService (app/services/cost_collection_service.py) - 成本采集服务
"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date, datetime, timedelta

# 标记：如果导入失败则跳过所有测试
pytestmark = pytest.mark.skipif(
    False,  # 稍后会设置
    reason="成本预测相关模块未找到"
)

HAS_MODULE = True
CostForecastService = None
EVMCalculator = None
EVMService = None
CostCollectionService = None

try:
    from app.services.cost.cost_forecast_service import CostForecastService as _CFS
    CostForecastService = _CFS
except Exception as e:
    print(f"Failed to import CostForecastService: {e}")
    HAS_MODULE = False

try:
    from app.services.evm_service import EVMCalculator as _EC, EVMService as _ES
    EVMCalculator = _EC
    EVMService = _ES
except Exception as e:
    print(f"Failed to import EVM services: {e}")
    HAS_MODULE = False

try:
    from app.services.cost_collection_service import CostCollectionService as _CCS
    CostCollectionService = _CCS
except Exception as e:
    print(f"Failed to import CostCollectionService: {e}")
    HAS_MODULE = False

# 更新 pytestmark
pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="成本预测相关模块未找到")


# ============================================================================
# 测试数据工厂
# ============================================================================

def make_project(
    project_id=1,
    name="Test Project",
    budget=100000,
    actual_cost=0,
    progress_pct=0,
    planned_start=None,
    planned_end=None
):
    """创建模拟项目对象"""
    p = MagicMock()
    p.id = project_id
    p.project_code = f"PJ{project_id:05d}"
    p.project_name = name
    p.budget_amount = Decimal(str(budget))
    p.actual_cost = Decimal(str(actual_cost))
    p.progress_pct = Decimal(str(progress_pct))
    p.planned_start_date = planned_start or date(2024, 1, 1)
    p.planned_end_date = planned_end or date(2024, 12, 31)
    return p


def make_monthly_costs(months_count=3, base_cost=5000):
    """生成月度成本数据"""
    monthly_costs = []
    cumulative = 0
    for i in range(months_count):
        monthly = base_cost * (1 + i * 0.1)  # 每月增长10%
        cumulative += monthly
        monthly_costs.append({
            "month": f"2024-{i+1:02d}",
            "monthly_cost": Decimal(str(monthly)),
            "cumulative_cost": Decimal(str(cumulative))
        })
    return monthly_costs


# ============================================================================
# CostForecastService 分支测试
# ============================================================================

class TestCostForecastLinearForecast:
    """测试线性回归预测的所有分支"""

    def test_forecast_project_not_found(self):
        """分支: 项目不存在"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = CostForecastService(db)

        result = svc.linear_forecast(999)

        assert "error" in result
        assert result["error"] == "项目不存在"

    def test_forecast_insufficient_data(self):
        """分支: 历史数据不足（少于2个月）"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = make_project()
        svc = CostForecastService(db)

        with patch.object(svc, "_get_monthly_costs", return_value=[
            {"month": "2024-01", "monthly_cost": Decimal("5000"), "cumulative_cost": Decimal("5000")}
        ]):
            result = svc.linear_forecast(1)

            assert "error" in result
            assert "历史数据不足" in result["error"]
            assert result["data_points"] == 1

    def test_forecast_with_sufficient_data(self):
        """分支: 数据充足，执行线性回归"""
        db = MagicMock()
        project = make_project(budget=100000, progress_pct=30)
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)

        monthly_costs = make_monthly_costs(months_count=3, base_cost=5000)
        with patch.object(svc, "_get_monthly_costs", return_value=monthly_costs):
            result = svc.linear_forecast(1)

            assert result["method"] == "LINEAR"
            assert "forecasted_completion_cost" in result
            assert "trend_data" in result
            assert "r_squared" in result["trend_data"]

    def test_forecast_with_no_planned_dates(self):
        """分支: 项目无计划日期，使用进度推算"""
        db = MagicMock()
        project = make_project(progress_pct=40)
        project.planned_start_date = None
        project.planned_end_date = None
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)

        monthly_costs = make_monthly_costs(months_count=4, base_cost=6000)
        with patch.object(svc, "_get_monthly_costs", return_value=monthly_costs):
            result = svc.linear_forecast(1)

            assert "forecasted_completion_cost" in result

    def test_forecast_with_zero_progress(self):
        """分支: 进度为0时的处理"""
        db = MagicMock()
        project = make_project(progress_pct=0)
        project.planned_start_date = None
        project.planned_end_date = None
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)

        monthly_costs = make_monthly_costs(months_count=2, base_cost=5000)
        with patch.object(svc, "_get_monthly_costs", return_value=monthly_costs):
            result = svc.linear_forecast(1)

            assert "forecasted_completion_cost" in result

    def test_forecast_is_over_budget(self):
        """分支: 预测成本超预算"""
        db = MagicMock()
        project = make_project(budget=50000, progress_pct=50)
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)

        # 高成本月度数据
        monthly_costs = make_monthly_costs(months_count=3, base_cost=20000)
        with patch.object(svc, "_get_monthly_costs", return_value=monthly_costs):
            result = svc.linear_forecast(1)

            assert result["is_over_budget"] is True
            assert result["budget_variance"] > 0


class TestCostForecastExponentialForecast:
    """测试指数预测的所有分支"""

    def test_exponential_project_not_found(self):
        """分支: 项目不存在"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = CostForecastService(db)

        result = svc.exponential_forecast(999)

        assert "error" in result
        assert result["error"] == "项目不存在"

    def test_exponential_insufficient_data(self):
        """分支: 历史数据不足"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = make_project()
        svc = CostForecastService(db)

        with patch.object(svc, "_get_monthly_costs", return_value=[
            {"month": "2024-01", "monthly_cost": Decimal("5000"), "cumulative_cost": Decimal("5000")}
        ]):
            result = svc.exponential_forecast(1)

            assert "error" in result

    def test_exponential_with_zero_progress(self):
        """分支: 进度为0"""
        db = MagicMock()
        project = make_project(progress_pct=0)
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)

        monthly_costs = make_monthly_costs(months_count=3, base_cost=5000)
        with patch.object(svc, "_get_monthly_costs", return_value=monthly_costs):
            result = svc.exponential_forecast(1)

            assert result["method"] == "EXPONENTIAL"

    def test_exponential_with_positive_progress(self):
        """分支: 进度大于0"""
        db = MagicMock()
        project = make_project(progress_pct=60)
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)

        monthly_costs = make_monthly_costs(months_count=3, base_cost=5000)
        with patch.object(svc, "_get_monthly_costs", return_value=monthly_costs):
            result = svc.exponential_forecast(1)

            assert "avg_growth_rate" in result["trend_data"]


class TestCostForecastHistoricalAverage:
    """测试历史平均法预测的所有分支"""

    def test_historical_no_data(self):
        """分支: 无历史数据"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = make_project()
        svc = CostForecastService(db)

        with patch.object(svc, "_get_monthly_costs", return_value=[]):
            result = svc.historical_average_forecast(1)

            assert "error" in result

    def test_historical_with_data(self):
        """分支: 有历史数据"""
        db = MagicMock()
        project = make_project(progress_pct=40)
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)

        monthly_costs = make_monthly_costs(months_count=4, base_cost=5000)
        with patch.object(svc, "_get_monthly_costs", return_value=monthly_costs):
            result = svc.historical_average_forecast(1)

            assert result["method"] == "HISTORICAL_AVERAGE"
            assert "avg_monthly_cost" in result["trend_data"]


class TestCostForecastTrend:
    """测试成本趋势分析的所有分支"""

    def test_trend_no_data(self):
        """分支: 无月度成本数据"""
        db = MagicMock()
        project = make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)

        with patch.object(svc, "_get_monthly_costs", return_value=[]):
            result = svc.get_cost_trend(1)

            assert result["monthly_trend"] == []
            assert result["summary"]["total_months"] == 0

    def test_trend_with_data(self):
        """分支: 有月度成本数据"""
        db = MagicMock()
        project = make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)

        monthly_costs = make_monthly_costs(months_count=6, base_cost=5000)
        with patch.object(svc, "_get_monthly_costs", return_value=monthly_costs):
            result = svc.get_cost_trend(1)

            assert len(result["monthly_trend"]) == 6
            assert result["summary"]["total_months"] == 6


class TestCostForecastBurnDown:
    """测试成本燃尽图的所有分支"""

    def test_burndown_no_budget(self):
        """分支: 预算为0"""
        db = MagicMock()
        project = make_project(budget=0)
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)

        result = svc.get_burn_down_data(1)

        assert "error" in result

    def test_burndown_with_budget(self):
        """分支: 有预算"""
        db = MagicMock()
        project = make_project(budget=100000, actual_cost=30000, progress_pct=40)
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)

        monthly_costs = make_monthly_costs(months_count=4, base_cost=7500)
        with patch.object(svc, "_get_monthly_costs", return_value=monthly_costs):
            result = svc.get_burn_down_data(1)

            assert "burn_down_data" in result
            assert result["budget"] == 100000


class TestCostForecastAlerts:
    """测试成本预警检测的所有分支"""

    def test_alerts_no_rules(self):
        """分支: 无预警规则"""
        db = MagicMock()
        project = make_project(budget=100000, actual_cost=85000)
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)

        with patch.object(svc, "_get_alert_rules", return_value={}):
            with patch.object(svc, "_get_monthly_costs", return_value=make_monthly_costs()):
                alerts = svc.check_cost_alerts(1, auto_create=False)

                assert isinstance(alerts, list)

    def test_overspend_warning(self):
        """分支: 成本超支预警（警告级别）"""
        db = MagicMock()
        project = make_project(budget=100000, actual_cost=82000)
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)

        with patch.object(svc, "_get_alert_rules", return_value={
            "OVERSPEND": {"warning_threshold": 80, "critical_threshold": 100}
        }):
            with patch.object(svc, "_get_monthly_costs", return_value=make_monthly_costs()):
                alerts = svc.check_cost_alerts(1, auto_create=False)

                overspend_alerts = [a for a in alerts if a["alert_type"] == "OVERSPEND"]
                assert len(overspend_alerts) > 0
                assert overspend_alerts[0]["alert_level"] == "WARNING"

    def test_overspend_critical(self):
        """分支: 成本超支预警（严重级别）"""
        db = MagicMock()
        project = make_project(budget=100000, actual_cost=105000)
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)

        with patch.object(svc, "_get_alert_rules", return_value={
            "OVERSPEND": {"warning_threshold": 80, "critical_threshold": 100}
        }):
            with patch.object(svc, "_get_monthly_costs", return_value=make_monthly_costs()):
                alerts = svc.check_cost_alerts(1, auto_create=False)

                overspend_alerts = [a for a in alerts if a["alert_type"] == "OVERSPEND"]
                assert overspend_alerts[0]["alert_level"] == "CRITICAL"

    def test_progress_mismatch_cost_ahead(self):
        """分支: 成本消耗超前进度"""
        db = MagicMock()
        project = make_project(budget=100000, actual_cost=60000, progress_pct=40)
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)

        with patch.object(svc, "_get_alert_rules", return_value={
            "PROGRESS_MISMATCH": {"deviation_threshold": 15}
        }):
            with patch.object(svc, "_get_monthly_costs", return_value=make_monthly_costs()):
                alerts = svc.check_cost_alerts(1, auto_create=False)

                mismatch_alerts = [a for a in alerts if a["alert_type"] == "PROGRESS_MISMATCH"]
                assert len(mismatch_alerts) > 0

    def test_trend_anomaly(self):
        """分支: 成本增长率异常"""
        db = MagicMock()
        project = make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)

        # 创建增长率超过30%的月度数据
        high_growth_costs = [
            {"month": "2024-01", "monthly_cost": Decimal("5000"), "cumulative_cost": Decimal("5000")},
            {"month": "2024-02", "monthly_cost": Decimal("7000"), "cumulative_cost": Decimal("12000")},
            {"month": "2024-03", "monthly_cost": Decimal("10000"), "cumulative_cost": Decimal("22000")},
        ]

        with patch.object(svc, "_get_alert_rules", return_value={
            "TREND_ANOMALY": {"growth_rate_threshold": 0.3}
        }):
            with patch.object(svc, "_get_monthly_costs", return_value=high_growth_costs):
                alerts = svc.check_cost_alerts(1, auto_create=False)

                trend_alerts = [a for a in alerts if a["alert_type"] == "TREND_ANOMALY"]
                assert len(trend_alerts) > 0


# ============================================================================
# EVMCalculator 和 EVMService 分支测试
# ============================================================================

class TestEVMCalculatorBranches:
    """测试EVM计算器的所有分支"""

    def test_spi_with_zero_pv(self):
        """分支: PV=0时SPI返回None"""
        spi = EVMCalculator.calculate_schedule_performance_index(
            Decimal("10000"), Decimal("0")
        )
        assert spi is None

    def test_spi_normal(self):
        """分支: PV>0时正常计算SPI"""
        spi = EVMCalculator.calculate_schedule_performance_index(
            Decimal("12000"), Decimal("10000")
        )
        assert spi > Decimal("1.0")

    def test_cpi_with_zero_ac(self):
        """分支: AC=0时CPI返回None"""
        cpi = EVMCalculator.calculate_cost_performance_index(
            Decimal("10000"), Decimal("0")
        )
        assert cpi is None

    def test_cpi_normal(self):
        """分支: AC>0时正常计算CPI"""
        cpi = EVMCalculator.calculate_cost_performance_index(
            Decimal("12000"), Decimal("10000")
        )
        assert cpi > Decimal("1.0")

    def test_eac_with_none_cpi(self):
        """分支: CPI为None时使用简化公式"""
        eac = EVMCalculator.calculate_estimate_at_completion(
            Decimal("100000"), Decimal("50000"), Decimal("60000"), cpi=None
        )
        # 简化公式: EAC = AC + (BAC - EV) = 60000 + (100000 - 50000) = 110000
        assert eac == Decimal("110000.0000")

    def test_eac_with_zero_cpi(self):
        """分支: CPI=0时使用简化公式"""
        eac = EVMCalculator.calculate_estimate_at_completion(
            Decimal("100000"), Decimal("50000"), Decimal("60000"), cpi=Decimal("0")
        )
        assert eac == Decimal("110000.0000")

    def test_eac_with_positive_cpi(self):
        """分支: CPI>0时使用标准公式"""
        eac = EVMCalculator.calculate_estimate_at_completion(
            Decimal("100000"), Decimal("50000"), Decimal("60000"), cpi=Decimal("0.8")
        )
        # 标准公式: EAC = AC + (BAC - EV) / CPI = 60000 + 50000/0.8 = 122500
        assert eac == Decimal("122500.0000")

    def test_tcpi_with_zero_funds_remaining(self):
        """分支: 剩余资金为0时返回None"""
        tcpi = EVMCalculator.calculate_to_complete_performance_index(
            Decimal("100000"), Decimal("100000"), Decimal("100000")
        )
        assert tcpi is None

    def test_tcpi_based_on_bac(self):
        """分支: 基于BAC计算TCPI"""
        tcpi = EVMCalculator.calculate_to_complete_performance_index(
            Decimal("100000"), Decimal("50000"), Decimal("60000")
        )
        # TCPI = (BAC - EV) / (BAC - AC) = 50000 / 40000 = 1.25
        assert tcpi == Decimal("1.250000")

    def test_tcpi_based_on_eac(self):
        """分支: 基于EAC计算TCPI"""
        tcpi = EVMCalculator.calculate_to_complete_performance_index(
            Decimal("100000"), Decimal("50000"), Decimal("60000"),
            eac=Decimal("120000")
        )
        # TCPI = (BAC - EV) / (EAC - AC) = 50000 / 60000 = 0.833333
        assert tcpi == Decimal("0.833333")

    def test_percent_complete_with_zero_bac(self):
        """分支: BAC=0时返回None"""
        percent = EVMCalculator.calculate_percent_complete(
            Decimal("50000"), Decimal("0")
        )
        assert percent is None

    def test_percent_complete_normal(self):
        """分支: BAC>0时正常计算"""
        percent = EVMCalculator.calculate_percent_complete(
            Decimal("50000"), Decimal("100000")
        )
        assert percent == Decimal("50.00")


class TestEVMServiceBranches:
    """测试EVM服务的所有分支"""

    def test_create_evm_data_project_not_found(self):
        """分支: 项目不存在"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = EVMService(db)

        with pytest.raises(ValueError, match="项目不存在"):
            svc.create_evm_data(
                project_id=999,
                period_type="MONTH",
                period_date=date(2024, 1, 31),
                pv=Decimal("10000"),
                ev=Decimal("8000"),
                ac=Decimal("9000"),
                bac=Decimal("100000")
            )

    def test_create_evm_data_success(self):
        """分支: 成功创建EVM数据"""
        db = MagicMock()
        project = make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        svc = EVMService(db)

        result = svc.create_evm_data(
            project_id=1,
            period_type="MONTH",
            period_date=date(2024, 1, 31),
            pv=Decimal("10000"),
            ev=Decimal("12000"),
            ac=Decimal("9000"),
            bac=Decimal("100000")
        )

        assert result.period_type == "MONTH"
        assert result.schedule_variance > 0  # EV > PV
        assert result.cost_variance > 0  # EV > AC

    def test_period_label_week(self):
        """分支: 周期类型为WEEK"""
        db = MagicMock()
        svc = EVMService(db)

        label = svc._generate_period_label("WEEK", date(2024, 2, 15))
        assert "W" in label

    def test_period_label_month(self):
        """分支: 周期类型为MONTH"""
        db = MagicMock()
        svc = EVMService(db)

        label = svc._generate_period_label("MONTH", date(2024, 2, 15))
        assert label == "2024-02"

    def test_period_label_quarter(self):
        """分支: 周期类型为QUARTER"""
        db = MagicMock()
        svc = EVMService(db)

        label = svc._generate_period_label("QUARTER", date(2024, 5, 15))
        assert "Q2" in label

    def test_analyze_performance_excellent(self):
        """分支: 绩效优秀"""
        db = MagicMock()
        svc = EVMService(db)

        evm_data = MagicMock()
        evm_data.schedule_performance_index = Decimal("1.15")
        evm_data.cost_performance_index = Decimal("1.2")

        result = svc.analyze_performance(evm_data)

        assert result["overall_status"] == "EXCELLENT"
        assert result["schedule_status"] == "EXCELLENT"
        assert result["cost_status"] == "EXCELLENT"

    def test_analyze_performance_critical(self):
        """分支: 绩效严重"""
        db = MagicMock()
        svc = EVMService(db)

        evm_data = MagicMock()
        evm_data.schedule_performance_index = Decimal("0.7")
        evm_data.cost_performance_index = Decimal("0.75")

        result = svc.analyze_performance(evm_data)

        assert result["overall_status"] == "CRITICAL"
        assert result["schedule_status"] == "CRITICAL"
        assert result["cost_status"] == "CRITICAL"

    def test_analyze_performance_warning(self):
        """分支: 绩效警告"""
        db = MagicMock()
        svc = EVMService(db)

        evm_data = MagicMock()
        evm_data.schedule_performance_index = Decimal("0.85")
        evm_data.cost_performance_index = Decimal("0.9")

        result = svc.analyze_performance(evm_data)

        assert result["overall_status"] == "WARNING"


# ============================================================================
# CostCollectionService 分支测试
# ============================================================================

class TestCostCollectionPurchaseOrder:
    """测试采购订单成本采集的所有分支"""

    def test_collect_order_not_found(self):
        """分支: 采购订单不存在"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = CostCollectionService.collect_from_purchase_order(db, 999)

        assert result is None

    def test_collect_order_no_project(self):
        """分支: 订单未关联项目"""
        db = MagicMock()
        order = MagicMock()
        order.id = 1
        order.project_id = None
        db.query.return_value.filter.return_value.first.return_value = order

        result = CostCollectionService.collect_from_purchase_order(db, 1)

        assert result is None

    def test_collect_existing_cost_update(self):
        """分支: 更新已存在的成本记录"""
        db = MagicMock()

        # 模拟订单
        order = MagicMock()
        order.id = 1
        order.project_id = 10
        order.total_amount = Decimal("50000")
        order.tax_amount = Decimal("6500")
        order.created_at = datetime.now()

        # 模拟已存在的成本记录
        existing_cost = MagicMock()
        existing_cost.amount = Decimal("40000")

        # 模拟项目
        project = make_project(project_id=10)

        # 设置查询返回值
        def query_side_effect(model):
            mock = MagicMock()
            if model.__name__ == "PurchaseOrder":
                mock.filter.return_value.first.return_value = order
            elif model.__name__ == "ProjectCost":
                # 第一次查询返回existing_cost，第二次返回空列表
                mock.filter.return_value.first.return_value = existing_cost
                mock.filter.return_value.all.return_value = [existing_cost]
            elif model.__name__ == "Project":
                mock.filter.return_value.first.return_value = project
            return mock

        db.query.side_effect = query_side_effect

        result = CostCollectionService.collect_from_purchase_order(db, 1)

        assert result == existing_cost
        assert existing_cost.amount == Decimal("50000")

    def test_collect_new_cost_creation(self):
        """分支: 创建新的成本记录"""
        db = MagicMock()

        # 模拟订单
        order = MagicMock()
        order.id = 1
        order.project_id = 10
        order.order_no = "PO001"
        order.order_title = "测试采购"
        order.total_amount = Decimal("50000")
        order.tax_amount = Decimal("6500")
        order.order_date = date(2024, 1, 15)

        # 模拟项目
        project = make_project(project_id=10)

        # 设置查询返回值
        def query_side_effect(model):
            mock = MagicMock()
            if model.__name__ == "PurchaseOrder":
                mock.filter.return_value.first.return_value = order
            elif model.__name__ == "ProjectCost":
                mock.filter.return_value.first.return_value = None  # 不存在
            elif model.__name__ == "Project":
                mock.filter.return_value.first.return_value = project
            return mock

        db.query.side_effect = query_side_effect

        with patch("app.services.cost_collection_service.CostAlertService.check_budget_execution"):
            result = CostCollectionService.collect_from_purchase_order(db, 1, created_by=1)

        assert db.add.called


class TestCostCollectionOutsourcingOrder:
    """测试外协订单成本采集的所有分支"""

    def test_collect_outsourcing_no_project(self):
        """分支: 外协订单未关联项目"""
        db = MagicMock()
        order = MagicMock()
        order.id = 1
        order.project_id = None
        db.query.return_value.filter.return_value.first.return_value = order

        result = CostCollectionService.collect_from_outsourcing_order(db, 1)

        assert result is None

    def test_collect_outsourcing_with_machine(self):
        """分支: 外协订单关联机台"""
        db = MagicMock()

        order = MagicMock()
        order.id = 1
        order.project_id = 10
        order.machine_id = 5
        order.order_no = "OS001"
        order.total_amount = Decimal("30000")
        order.tax_amount = Decimal("3900")
        order.created_at = datetime.now()

        project = make_project(project_id=10)

        def query_side_effect(model):
            mock = MagicMock()
            if model.__name__ == "OutsourcingOrder":
                mock.filter.return_value.first.return_value = order
            elif model.__name__ == "ProjectCost":
                mock.filter.return_value.first.return_value = None
            elif model.__name__ == "Project":
                mock.filter.return_value.first.return_value = project
            return mock

        db.query.side_effect = query_side_effect

        with patch("app.services.cost_collection_service.CostAlertService.check_budget_execution"):
            result = CostCollectionService.collect_from_outsourcing_order(db, 1)

        assert db.add.called


class TestCostCollectionECN:
    """测试ECN成本采集的所有分支"""

    def test_collect_ecn_not_found(self):
        """分支: ECN不存在"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = CostCollectionService.collect_from_ecn(db, 999)

        assert result is None

    def test_collect_ecn_no_cost_impact(self):
        """分支: ECN无成本影响"""
        db = MagicMock()
        ecn = MagicMock()
        ecn.id = 1
        ecn.cost_impact = Decimal("0")
        db.query.return_value.filter.return_value.first.return_value = ecn

        result = CostCollectionService.collect_from_ecn(db, 1)

        assert result is None

    def test_collect_ecn_negative_cost_impact(self):
        """分支: ECN成本影响为负"""
        db = MagicMock()
        ecn = MagicMock()
        ecn.id = 1
        ecn.cost_impact = Decimal("-1000")
        db.query.return_value.filter.return_value.first.return_value = ecn

        result = CostCollectionService.collect_from_ecn(db, 1)

        assert result is None

    def test_collect_ecn_no_project(self):
        """分支: ECN未关联项目"""
        db = MagicMock()
        ecn = MagicMock()
        ecn.id = 1
        ecn.project_id = None
        ecn.cost_impact = Decimal("5000")

        def query_side_effect(model):
            mock = MagicMock()
            if model.__name__ == "Ecn":
                mock.filter.return_value.first.return_value = ecn
            elif model.__name__ == "ProjectCost":
                mock.filter.return_value.first.return_value = None
            return mock

        db.query.side_effect = query_side_effect

        result = CostCollectionService.collect_from_ecn(db, 1)

        assert result is None

    def test_collect_ecn_success(self):
        """分支: 成功采集ECN成本"""
        db = MagicMock()

        ecn = MagicMock()
        ecn.id = 1
        ecn.project_id = 10
        ecn.machine_id = 5
        ecn.ecn_no = "ECN001"
        ecn.ecn_title = "设计变更"
        ecn.cost_impact = Decimal("5000")

        project = make_project(project_id=10)

        def query_side_effect(model):
            mock = MagicMock()
            if model.__name__ == "Ecn":
                mock.filter.return_value.first.return_value = ecn
            elif model.__name__ == "ProjectCost":
                mock.filter.return_value.first.return_value = None
            elif model.__name__ == "Project":
                mock.filter.return_value.first.return_value = project
            return mock

        db.query.side_effect = query_side_effect

        with patch("app.services.cost_collection_service.CostAlertService.check_budget_execution"):
            result = CostCollectionService.collect_from_ecn(db, 1)

        assert db.add.called


class TestCostCollectionBOM:
    """测试BOM成本采集的所有分支"""

    def test_collect_bom_not_found(self):
        """分支: BOM不存在"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="BOM不存在"):
            CostCollectionService.collect_from_bom(db, 999)

    def test_collect_bom_no_project(self):
        """分支: BOM未关联项目"""
        db = MagicMock()
        bom = MagicMock()
        bom.id = 1
        bom.project_id = None
        db.query.return_value.filter.return_value.first.return_value = bom

        with pytest.raises(ValueError, match="BOM未关联项目"):
            CostCollectionService.collect_from_bom(db, 1)

    def test_collect_bom_not_released(self):
        """分支: BOM未发布"""
        db = MagicMock()
        bom = MagicMock()
        bom.id = 1
        bom.project_id = 10
        bom.status = "DRAFT"
        db.query.return_value.filter.return_value.first.return_value = bom

        with pytest.raises(ValueError, match="只有已发布的BOM才能归集成本"):
            CostCollectionService.collect_from_bom(db, 1)

    def test_collect_bom_zero_amount(self):
        """分支: BOM总成本为0，删除已存在的成本记录"""
        db = MagicMock()

        bom = MagicMock()
        bom.id = 1
        bom.project_id = 10
        bom.status = "RELEASED"
        bom.total_amount = None

        existing_cost = MagicMock()
        existing_cost.amount = Decimal("1000")

        project = make_project(project_id=10, actual_cost=1000)

        def query_side_effect(model):
            mock = MagicMock()
            if model.__name__ == "BomHeader":
                mock.filter.return_value.first.return_value = bom
            elif model.__name__ == "ProjectCost":
                mock.filter.return_value.first.return_value = existing_cost
            elif model.__name__ == "BomItem":
                mock.filter.return_value.all.return_value = []  # 无BOM项
            elif model.__name__ == "Project":
                mock.filter.return_value.first.return_value = project
            return mock

        db.query.side_effect = query_side_effect

        with patch("app.services.cost_collection_service.delete_obj"):
            result = CostCollectionService.collect_from_bom(db, 1)

        assert result is None

    def test_collect_bom_success(self):
        """分支: 成功采集BOM成本"""
        db = MagicMock()

        bom = MagicMock()
        bom.id = 1
        bom.project_id = 10
        bom.machine_id = 5
        bom.status = "RELEASED"
        bom.bom_no = "BOM001"
        bom.bom_name = "测试BOM"
        bom.total_amount = Decimal("50000")

        # 模拟BOM项
        bom_item1 = MagicMock()
        bom_item1.amount = Decimal("20000")
        bom_item2 = MagicMock()
        bom_item2.amount = Decimal("30000")

        project = make_project(project_id=10)

        def query_side_effect(model):
            mock = MagicMock()
            if model.__name__ == "BomHeader":
                mock.filter.return_value.first.return_value = bom
            elif model.__name__ == "ProjectCost":
                mock.filter.return_value.first.return_value = None
            elif model.__name__ == "BomItem":
                mock.filter.return_value.all.return_value = [bom_item1, bom_item2]
            elif model.__name__ == "Project":
                mock.filter.return_value.first.return_value = project
            return mock

        db.query.side_effect = query_side_effect

        with patch("app.services.cost_collection_service.CostAlertService.check_budget_execution"):
            result = CostCollectionService.collect_from_bom(db, 1)

        assert db.add.called


class TestCostCollectionRemove:
    """测试成本记录删除的所有分支"""

    def test_remove_cost_not_found(self):
        """分支: 成本记录不存在"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = CostCollectionService.remove_cost_from_source(
            db, "PURCHASE", "PURCHASE_ORDER", 999
        )

        assert result is False

    def test_remove_cost_success(self):
        """分支: 成功删除成本记录"""
        db = MagicMock()

        cost = MagicMock()
        cost.project_id = 10
        cost.amount = Decimal("5000")

        project = make_project(project_id=10, actual_cost=50000)

        def query_side_effect(model):
            mock = MagicMock()
            if model.__name__ == "ProjectCost":
                mock.filter.return_value.first.return_value = cost
            elif model.__name__ == "Project":
                mock.filter.return_value.first.return_value = project
            return mock

        db.query.side_effect = query_side_effect

        result = CostCollectionService.remove_cost_from_source(
            db, "PURCHASE", "PURCHASE_ORDER", 1
        )

        assert result is True
        assert db.delete.called

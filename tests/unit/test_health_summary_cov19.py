# -*- coding: utf-8 -*-
"""
第十九批 - 战略健康度汇总单元测试
注意：health_calculator 为相对导入，使用 sys.modules patch
"""
import sys
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.strategy.review.health_summary")

_HC_MOD_KEY = "app.services.strategy.review.health_calculator"


def _make_dimension_detail(dim="FINANCE"):
    return {
        "dimension": dim,
        "dimension_name": "财务",
        "score": 75.0,
        "health_level": "GOOD",
        "csf_count": 3,
        "kpi_count": 10,
        "kpi_completion_rate": 0.8,
        "kpi_on_track": 7,
        "kpi_at_risk": 2,
        "kpi_off_track": 1,
    }


def _make_hc_mock(score=78.0, level="GOOD", dims=None, trend=None):
    hc = MagicMock()
    hc.calculate_strategy_health.return_value = score
    hc.get_health_level.return_value = level
    hc.get_dimension_health_details.return_value = dims or []
    hc.get_health_trend.return_value = trend or []
    return hc


@pytest.fixture(autouse=True)
def inject_hc_mock(request):
    """自动注入 health_calculator mock 到 sys.modules"""
    hc = _make_hc_mock()
    with patch.dict(sys.modules, {_HC_MOD_KEY: hc}):
        # 重新导入以刷新模块缓存中的函数引用
        request.node._hc_mock = hc
        yield hc


def test_get_health_score_summary_basic(inject_hc_mock):
    """基本调用返回 HealthScoreResponse"""
    from app.services.strategy.review import health_summary
    import importlib; importlib.reload(health_summary)
    inject_hc_mock.calculate_strategy_health.return_value = 78.0
    inject_hc_mock.get_health_level.return_value = "GOOD"
    inject_hc_mock.get_dimension_health_details.return_value = [_make_dimension_detail()]
    inject_hc_mock.get_health_trend.return_value = []

    db = MagicMock()
    result = health_summary.get_health_score_summary(db, strategy_id=1)
    assert result.strategy_id == 1
    assert result.overall_score == 78.0
    assert result.overall_level == "GOOD"


def test_get_health_score_summary_dimensions(inject_hc_mock):
    """维度详情正确映射"""
    from app.services.strategy.review import health_summary
    import importlib; importlib.reload(health_summary)
    inject_hc_mock.calculate_strategy_health.return_value = 65.0
    inject_hc_mock.get_health_level.return_value = "FAIR"
    inject_hc_mock.get_dimension_health_details.return_value = [
        _make_dimension_detail("FINANCE"),
        _make_dimension_detail("CUSTOMER"),
    ]
    inject_hc_mock.get_health_trend.return_value = []

    db = MagicMock()
    result = health_summary.get_health_score_summary(db, strategy_id=2)
    assert len(result.dimensions) == 2
    dims = [d.dimension for d in result.dimensions]
    assert "FINANCE" in dims
    assert "CUSTOMER" in dims


def test_get_health_score_summary_no_score(inject_hc_mock):
    """无评分时 overall_level 为 None"""
    from app.services.strategy.review import health_summary
    import importlib; importlib.reload(health_summary)
    inject_hc_mock.calculate_strategy_health.return_value = None
    inject_hc_mock.get_dimension_health_details.return_value = []
    inject_hc_mock.get_health_trend.return_value = []

    db = MagicMock()
    result = health_summary.get_health_score_summary(db, strategy_id=99)
    assert result.overall_score is None
    assert result.overall_level is None


def test_get_health_score_summary_trend(inject_hc_mock):
    """趋势数据正确传递"""
    from app.services.strategy.review import health_summary
    import importlib; importlib.reload(health_summary)
    trend = [{"date": "2024-01", "score": 75}]
    inject_hc_mock.calculate_strategy_health.return_value = 80.0
    inject_hc_mock.get_health_level.return_value = "GOOD"
    inject_hc_mock.get_dimension_health_details.return_value = []
    inject_hc_mock.get_health_trend.return_value = trend

    db = MagicMock()
    result = health_summary.get_health_score_summary(db, strategy_id=3)
    assert result.trend == trend


def test_get_health_score_summary_calculated_at(inject_hc_mock):
    """calculated_at 字段为 datetime 类型"""
    from app.services.strategy.review import health_summary
    import importlib; importlib.reload(health_summary)
    inject_hc_mock.calculate_strategy_health.return_value = 55.0
    inject_hc_mock.get_health_level.return_value = "POOR"
    inject_hc_mock.get_dimension_health_details.return_value = []
    inject_hc_mock.get_health_trend.return_value = []

    db = MagicMock()
    result = health_summary.get_health_score_summary(db, strategy_id=4)
    assert isinstance(result.calculated_at, datetime)


def test_get_health_score_summary_kpi_fields(inject_hc_mock):
    """维度 KPI 字段正确映射"""
    from app.services.strategy.review import health_summary
    import importlib; importlib.reload(health_summary)
    detail = _make_dimension_detail()
    detail["kpi_on_track"] = 5
    detail["kpi_at_risk"] = 3
    detail["kpi_off_track"] = 2
    inject_hc_mock.calculate_strategy_health.return_value = 70.0
    inject_hc_mock.get_health_level.return_value = "GOOD"
    inject_hc_mock.get_dimension_health_details.return_value = [detail]
    inject_hc_mock.get_health_trend.return_value = []

    db = MagicMock()
    result = health_summary.get_health_score_summary(db, strategy_id=5)
    dim = result.dimensions[0]
    assert dim.kpi_on_track == 5
    assert dim.kpi_at_risk == 3
    assert dim.kpi_off_track == 2

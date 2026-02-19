# -*- coding: utf-8 -*-
"""
第四十七批覆盖测试 - win_rate_prediction_service/base.py
"""
import pytest

pytest.importorskip("app.services.win_rate_prediction_service.base")

from unittest.mock import MagicMock

from app.services.win_rate_prediction_service.base import WinRatePredictionService


def test_init_stores_db():
    db = MagicMock()
    svc = WinRatePredictionService(db)
    assert svc.db is db


def test_dimension_weights_sum_to_one():
    db = MagicMock()
    svc = WinRatePredictionService(db)
    total = sum(svc.DIMENSION_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9


def test_dimension_weights_keys():
    db = MagicMock()
    svc = WinRatePredictionService(db)
    expected_keys = {
        "requirement_maturity",
        "technical_feasibility",
        "business_feasibility",
        "delivery_risk",
        "customer_relationship",
    }
    assert set(svc.DIMENSION_WEIGHTS.keys()) == expected_keys


def test_probability_thresholds_coverage():
    from app.models.enums import WinProbabilityLevelEnum
    db = MagicMock()
    svc = WinRatePredictionService(db)
    # 每个枚举值都应该有对应阈值
    for level in WinProbabilityLevelEnum:
        assert level in svc.PROBABILITY_THRESHOLDS


def test_probability_thresholds_ordered():
    from app.models.enums import WinProbabilityLevelEnum
    db = MagicMock()
    svc = WinRatePredictionService(db)
    values = list(svc.PROBABILITY_THRESHOLDS.values())
    # 阈值应该是单调非递增的
    assert values == sorted(values, reverse=True)


def test_service_is_class():
    assert isinstance(WinRatePredictionService, type)

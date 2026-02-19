# -*- coding: utf-8 -*-
"""
第四十七批覆盖测试 - win_rate_prediction_service/analysis.py
"""
import pytest

pytest.importorskip("app.services.win_rate_prediction_service.analysis")

from unittest.mock import MagicMock, PropertyMock

from app.services.win_rate_prediction_service.analysis import (
    get_win_rate_distribution,
    validate_model_accuracy,
)


def _make_service(projects):
    svc = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = projects
    svc.db.query.return_value = q
    return svc


def _make_project(rate, outcome):
    p = MagicMock()
    p.predicted_win_rate = rate
    p.outcome = outcome
    return p


def test_distribution_empty():
    svc = _make_service([])
    result = get_win_rate_distribution(svc)
    for level_data in result.values():
        assert level_data["count"] == 0


def test_distribution_very_high():
    from app.models.enums import LeadOutcomeEnum, WinProbabilityLevelEnum
    p = _make_project(0.85, LeadOutcomeEnum.WON.value)
    svc = _make_service([p])
    result = get_win_rate_distribution(svc)
    assert result[WinProbabilityLevelEnum.VERY_HIGH.value]["count"] == 1
    assert result[WinProbabilityLevelEnum.VERY_HIGH.value]["won"] == 1


def test_distribution_actual_win_rate_calculation():
    from app.models.enums import LeadOutcomeEnum, WinProbabilityLevelEnum
    won_p = _make_project(0.65, LeadOutcomeEnum.WON.value)
    lost_p = _make_project(0.61, LeadOutcomeEnum.LOST.value)
    svc = _make_service([won_p, lost_p])
    result = get_win_rate_distribution(svc)
    high = result[WinProbabilityLevelEnum.HIGH.value]
    assert high["actual_win_rate"] == 0.5


def test_validate_model_no_data():
    svc = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = []
    svc.db.query.return_value = q
    result = validate_model_accuracy(svc)
    assert "error" in result


def test_validate_model_accuracy_correct():
    from app.models.enums import LeadOutcomeEnum
    p_won = _make_project(0.75, LeadOutcomeEnum.WON.value)
    p_lost = _make_project(0.30, LeadOutcomeEnum.LOST.value)
    svc = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = [p_won, p_lost]
    svc.db.query.return_value = q
    result = validate_model_accuracy(svc)
    assert result["accuracy"] == 1.0
    assert result["total_samples"] == 2


def test_validate_brier_score():
    from app.models.enums import LeadOutcomeEnum
    # 完美预测：predicted=1.0, actual=WON → error=0
    p = _make_project(1.0, LeadOutcomeEnum.WON.value)
    svc = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = [p]
    svc.db.query.return_value = q
    result = validate_model_accuracy(svc)
    assert result["brier_score"] == 0.0

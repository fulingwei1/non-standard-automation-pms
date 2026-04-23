# -*- coding: utf-8 -*-
"""win_rate_prediction_service.analysis 深度测试"""

from types import SimpleNamespace

from app.models.enums import LeadOutcomeEnum, WinProbabilityLevelEnum
from app.services.win_rate_prediction_service.analysis import (
    get_win_rate_distribution,
    validate_model_accuracy,
)


class FakeQuery:
    def __init__(self, items):
        self.items = items

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self.items


class FakeDB:
    def __init__(self, items):
        self.items = items

    def query(self, *args, **kwargs):
        return FakeQuery(self.items)


class TestWinRateAnalysisDeep:
    def test_get_win_rate_distribution_groups_levels_and_actual_rate(self):
        projects = [
            SimpleNamespace(predicted_win_rate=0.85, outcome=LeadOutcomeEnum.WON.value),
            SimpleNamespace(predicted_win_rate=0.65, outcome=LeadOutcomeEnum.LOST.value),
            SimpleNamespace(predicted_win_rate=0.45, outcome=LeadOutcomeEnum.WON.value),
            SimpleNamespace(predicted_win_rate=0.25, outcome=LeadOutcomeEnum.LOST.value),
            SimpleNamespace(predicted_win_rate=0.10, outcome=LeadOutcomeEnum.LOST.value),
        ]
        service = SimpleNamespace(db=FakeDB(projects))

        result = get_win_rate_distribution(service)

        assert result[WinProbabilityLevelEnum.VERY_HIGH.value]["count"] == 1
        assert result[WinProbabilityLevelEnum.VERY_HIGH.value]["won"] == 1
        assert result[WinProbabilityLevelEnum.VERY_HIGH.value]["actual_win_rate"] == 1.0
        assert result[WinProbabilityLevelEnum.HIGH.value]["count"] == 1
        assert result[WinProbabilityLevelEnum.MEDIUM.value]["won"] == 1
        assert result[WinProbabilityLevelEnum.LOW.value]["count"] == 1
        assert result[WinProbabilityLevelEnum.VERY_LOW.value]["count"] == 1

    def test_get_win_rate_distribution_zero_count_rate_is_zero(self):
        service = SimpleNamespace(db=FakeDB([]))

        result = get_win_rate_distribution(service)

        assert result[WinProbabilityLevelEnum.VERY_HIGH.value]["actual_win_rate"] == 0
        assert result[WinProbabilityLevelEnum.LOW.value]["actual_win_rate"] == 0

    def test_validate_model_accuracy_returns_metrics(self):
        projects = [
            SimpleNamespace(predicted_win_rate=0.8, outcome=LeadOutcomeEnum.WON.value),
            SimpleNamespace(predicted_win_rate=0.7, outcome=LeadOutcomeEnum.LOST.value),
            SimpleNamespace(predicted_win_rate=0.3, outcome=LeadOutcomeEnum.LOST.value),
            SimpleNamespace(predicted_win_rate=0.2, outcome=LeadOutcomeEnum.WON.value),
        ]
        service = SimpleNamespace(db=FakeDB(projects))

        result = validate_model_accuracy(service, lookback_months=6)

        assert result["total_samples"] == 4
        assert result["accuracy"] == 0.5
        assert result["brier_score"] == 0.315
        assert result["period_months"] == 6

    def test_validate_model_accuracy_returns_error_without_projects(self):
        service = SimpleNamespace(db=FakeDB([]))

        result = validate_model_accuracy(service)

        assert result == {"error": "无足够数据进行验证"}

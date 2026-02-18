# -*- coding: utf-8 -*-
"""第二十六批 - performance_integration_service 单元测试"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

pytest.importorskip("app.services.performance_integration_service")

from app.services.performance_integration_service import PerformanceIntegrationService


class TestPerformanceIntegrationDefaults:
    def test_default_base_weight(self):
        assert PerformanceIntegrationService.DEFAULT_BASE_PERFORMANCE_WEIGHT == 0.70

    def test_default_qualification_weight(self):
        assert PerformanceIntegrationService.DEFAULT_QUALIFICATION_WEIGHT == 0.30

    def test_weights_sum_to_one(self):
        total = (
            PerformanceIntegrationService.DEFAULT_BASE_PERFORMANCE_WEIGHT
            + PerformanceIntegrationService.DEFAULT_QUALIFICATION_WEIGHT
        )
        assert abs(total - 1.0) < 1e-9

    def test_get_qualification_weight_config_returns_dict(self):
        config = PerformanceIntegrationService.get_qualification_weight_config()
        assert isinstance(config, dict)
        assert "base_weight" in config
        assert "qualification_weight" in config

    def test_get_qualification_weight_config_values(self):
        config = PerformanceIntegrationService.get_qualification_weight_config()
        assert config["base_weight"] == 0.70
        assert config["qualification_weight"] == 0.30


class TestCalculateIntegratedScore:
    def setup_method(self):
        self.db = MagicMock()

    def test_returns_none_when_no_base_score(self):
        with patch.object(
            PerformanceIntegrationService,
            "_get_base_performance_score",
            return_value=None,
        ):
            result = PerformanceIntegrationService.calculate_integrated_score(
                self.db, user_id=1, period="2024-01"
            )
        assert result is None

    def test_calculates_with_qualification_data(self):
        # Production code mixes Decimal and float; mock both as float to avoid TypeError
        with patch.object(
            PerformanceIntegrationService,
            "_get_base_performance_score",
            return_value=80.0,
        ), patch.object(
            PerformanceIntegrationService,
            "_get_qualification_score",
            return_value={"score": 70.0, "level_code": "P3", "level_name": "中级"},
        ):
            result = PerformanceIntegrationService.calculate_integrated_score(
                self.db, user_id=1, period="2024-01"
            )
        assert result is not None
        assert "integrated_score" in result
        # 80 * 0.70 + 70 * 0.30 = 56 + 21 = 77
        assert abs(result["integrated_score"] - 77.0) < 0.01

    def test_calculates_without_qualification_data(self):
        with patch.object(
            PerformanceIntegrationService,
            "_get_base_performance_score",
            return_value=85.0,
        ), patch.object(
            PerformanceIntegrationService,
            "_get_qualification_score",
            return_value=None,
        ):
            result = PerformanceIntegrationService.calculate_integrated_score(
                self.db, user_id=1, period="2024-01"
            )
        assert result is not None
        # No qualification → integrated = base score
        assert abs(result["integrated_score"] - 85.0) < 0.01
        assert result["qualification_score"] == 0.0

    def test_result_contains_required_keys(self):
        with patch.object(
            PerformanceIntegrationService,
            "_get_base_performance_score",
            return_value=90.0,
        ), patch.object(
            PerformanceIntegrationService,
            "_get_qualification_score",
            return_value={"score": 80.0, "level_code": "P4"},
        ):
            result = PerformanceIntegrationService.calculate_integrated_score(
                self.db, user_id=1, period="2024-01"
            )
        required_keys = [
            "base_score",
            "qualification_score",
            "integrated_score",
            "base_weight",
            "qualification_weight",
            "qualification_level",
            "details",
        ]
        for key in required_keys:
            assert key in result

    def test_qualification_level_populated(self):
        with patch.object(
            PerformanceIntegrationService,
            "_get_base_performance_score",
            return_value=75.0,
        ), patch.object(
            PerformanceIntegrationService,
            "_get_qualification_score",
            return_value={"score": 65.0, "level_code": "P2"},
        ):
            result = PerformanceIntegrationService.calculate_integrated_score(
                self.db, user_id=1, period="2024-01"
            )
        assert result["qualification_level"] == "P2"

    def test_qualification_level_none_when_no_qualification(self):
        with patch.object(
            PerformanceIntegrationService,
            "_get_base_performance_score",
            return_value=75.0,
        ), patch.object(
            PerformanceIntegrationService,
            "_get_qualification_score",
            return_value=None,
        ):
            result = PerformanceIntegrationService.calculate_integrated_score(
                self.db, user_id=1, period="2024-01"
            )
        assert result["qualification_level"] is None

    def test_details_contain_calculation(self):
        with patch.object(
            PerformanceIntegrationService,
            "_get_base_performance_score",
            return_value=80.0,
        ), patch.object(
            PerformanceIntegrationService,
            "_get_qualification_score",
            return_value={"score": 70.0, "level_code": "P3"},
        ):
            result = PerformanceIntegrationService.calculate_integrated_score(
                self.db, user_id=1, period="2024-01"
            )
        assert "calculation" in result["details"]
        assert "formula" in result["details"]["calculation"]


class TestGetBasePerformanceScore:
    def setup_method(self):
        self.db = MagicMock()

    def test_returns_none_when_no_summary(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = PerformanceIntegrationService._get_base_performance_score(
            self.db, user_id=1, period="2024-01"
        )
        assert result is None

    def test_returns_none_when_no_evaluations(self):
        summary = MagicMock(id=10)
        self.db.query.return_value.filter.return_value.first.return_value = summary
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = PerformanceIntegrationService._get_base_performance_score(
            self.db, user_id=1, period="2024-01"
        )
        assert result is None


class TestGetQualificationScore:
    def setup_method(self):
        self.db = MagicMock()

    def test_returns_none_when_no_user(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = PerformanceIntegrationService._get_qualification_score(
            self.db, user_id=999
        )
        assert result is None

    def test_returns_none_when_user_has_no_employee_id(self):
        user = MagicMock(employee_id=None)
        self.db.query.return_value.filter.return_value.first.return_value = user
        result = PerformanceIntegrationService._get_qualification_score(
            self.db, user_id=1
        )
        assert result is None


class TestUpdateQualificationInEvaluation:
    def setup_method(self):
        self.db = MagicMock()

    def test_raises_when_evaluation_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="评价记录 99 不存在"):
            PerformanceIntegrationService.update_qualification_in_evaluation(
                self.db, evaluation_id=99, qualification_data={}
            )

    def test_updates_qualification_fields(self):
        evaluation = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = evaluation
        qual_data = {"level_id": 5, "scores": {"tech": 90}}
        PerformanceIntegrationService.update_qualification_in_evaluation(
            self.db, evaluation_id=1, qualification_data=qual_data
        )
        assert evaluation.qualification_level_id == 5
        assert evaluation.qualification_score == {"tech": 90}
        self.db.commit.assert_called_once()


class TestGetIntegratedPerformanceForPeriod:
    def setup_method(self):
        self.db = MagicMock()

    def test_returns_none_when_period_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = PerformanceIntegrationService.get_integrated_performance_for_period(
            self.db, user_id=1, period_id=999
        )
        assert result is None

    def test_returns_none_when_no_finalized_period(self):
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = PerformanceIntegrationService.get_integrated_performance_for_period(
            self.db, user_id=1, period_id=None
        )
        assert result is None

    def test_calls_calculate_with_period_str(self):
        from datetime import date
        period = MagicMock()
        period.start_date = date(2024, 1, 1)
        self.db.query.return_value.filter.return_value.first.return_value = period
        with patch.object(
            PerformanceIntegrationService,
            "calculate_integrated_score",
            return_value={"integrated_score": 85.0},
        ) as mock_calc:
            result = PerformanceIntegrationService.get_integrated_performance_for_period(
                self.db, user_id=1, period_id=10
            )
        mock_calc.assert_called_once_with(self.db, 1, "2024-01")
        assert result == {"integrated_score": 85.0}

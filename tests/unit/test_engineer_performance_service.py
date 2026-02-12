# -*- coding: utf-8 -*-
"""Tests for engineer_performance/engineer_performance_service.py"""

from unittest.mock import MagicMock, patch

import pytest


class TestEngineerPerformanceService:
    def setup_method(self):
        self.db = MagicMock()

    @patch("app.services.engineer_performance.engineer_performance_service.ProfileService")
    @patch("app.services.engineer_performance.engineer_performance_service.DimensionConfigService")
    @patch("app.services.engineer_performance.engineer_performance_service.PerformanceCalculator")
    @patch("app.services.engineer_performance.engineer_performance_service.RankingService")
    def test_init(self, mock_rank, mock_calc, mock_dim, mock_prof):
        from app.services.engineer_performance.engineer_performance_service import EngineerPerformanceService
        svc = EngineerPerformanceService(self.db)
        assert svc.db == self.db

    @patch("app.services.engineer_performance.engineer_performance_service.ProfileService")
    @patch("app.services.engineer_performance.engineer_performance_service.DimensionConfigService")
    @patch("app.services.engineer_performance.engineer_performance_service.PerformanceCalculator")
    @patch("app.services.engineer_performance.engineer_performance_service.RankingService")
    def test_get_engineer_profile(self, mock_rank, mock_calc, mock_dim, mock_prof):
        from app.services.engineer_performance.engineer_performance_service import EngineerPerformanceService
        svc = EngineerPerformanceService(self.db)
        profile = MagicMock()
        svc.profile_service.get_profile.return_value = profile
        result = svc.get_engineer_profile(1)
        svc.profile_service.get_profile.assert_called_once_with(1)

    @patch("app.services.engineer_performance.engineer_performance_service.ProfileService")
    @patch("app.services.engineer_performance.engineer_performance_service.DimensionConfigService")
    @patch("app.services.engineer_performance.engineer_performance_service.PerformanceCalculator")
    @patch("app.services.engineer_performance.engineer_performance_service.RankingService")
    def test_calculate_grade(self, mock_rank, mock_calc, mock_dim, mock_prof):
        from app.services.engineer_performance.engineer_performance_service import EngineerPerformanceService
        from decimal import Decimal
        svc = EngineerPerformanceService(self.db)
        svc.performance_calculator.calculate_grade.return_value = "A"
        grade = svc.calculate_grade(Decimal("85"))
        assert grade == "A"
        svc.performance_calculator.calculate_grade.assert_called_once_with(Decimal("85"))

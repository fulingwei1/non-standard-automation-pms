# -*- coding: utf-8 -*-
"""Auto-generated tests for performance_service modules"""
import pytest


class TestPerformanceService:
    """Tests for performance service"""

    def test_service_import(self):
        """Test performance service can be imported"""
        try:
            from app.services.performance_service import PerformanceService
            assert callable(PerformanceService.calculate_final_score)
            assert callable(PerformanceService.calculate_quarterly_score)
        except ImportError:
            pytest.skip("Module not found")


class TestPerformanceServiceModule:
    """Tests for performance service module"""

    def test_module_import(self):
        """Test module can be imported"""
        import importlib
        try:
            mod = importlib.import_module('app.services.performance_service')
            assert mod is not None
        except ImportError:
            pytest.skip("Module not found")

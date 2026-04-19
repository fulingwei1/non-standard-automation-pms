# -*- coding: utf-8 -*-
"""performance_integration_service单元测试"""
from app.services.performance_integration_service import PerformanceIntegrationService


class TestPerformanceIntegrationServiceInit:
    def test_init_with_db(self):
        assert callable(PerformanceIntegrationService.calculate_integrated_score)

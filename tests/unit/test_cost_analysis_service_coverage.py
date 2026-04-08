# -*- coding: utf-8 -*-
"""cost_analysis_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.production.material_tracking.cost_analysis_service import CostAnalysisService

class TestCostAnalysisServiceInit:
    def test_init(self):
        service = CostAnalysisService(Mock())
        assert service is not None

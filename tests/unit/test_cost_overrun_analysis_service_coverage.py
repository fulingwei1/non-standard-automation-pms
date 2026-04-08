# -*- coding: utf-8 -*-
"""cost_overrun_analysis_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.cost.cost_overrun_analysis_service import CostOverrunAnalysisService

class TestCostOverrunAnalysisServiceInit:
    def test_init(self):
        service = CostOverrunAnalysisService(Mock())
        assert service is not None

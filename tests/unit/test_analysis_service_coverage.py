# -*- coding: utf-8 -*-
"""analysis_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.inventory.analysis_service import AnalysisService

class TestAnalysisServiceInit:
    def test_init(self):
        service = AnalysisService(Mock())
        assert service is not None

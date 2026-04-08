# -*- coding: utf-8 -*-
"""loss_deep_analysis_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.loss_deep_analysis_service import LossDeepAnalysisService

class TestLossDeepAnalysisServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = LossDeepAnalysisService(mock_db)
        assert hasattr(service, 'db')

# -*- coding: utf-8 -*-
"""information_gap_analysis_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.information_gap_analysis_service import InformationGapAnalysisService

class TestInformationGapAnalysisServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = InformationGapAnalysisService(mock_db)
        assert hasattr(service, 'db')

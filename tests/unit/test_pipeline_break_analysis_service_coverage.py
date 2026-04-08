# -*- coding: utf-8 -*-
"""pipeline_break_analysis_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.pipeline_break_analysis_service import PipelineBreakAnalysisService

class TestPipelineBreakAnalysisServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PipelineBreakAnalysisService(mock_db)
        assert hasattr(service, 'db')

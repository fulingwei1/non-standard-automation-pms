# -*- coding: utf-8 -*-
"""pipeline_accountability_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.pipeline_accountability_service import PipelineAccountabilityService

class TestPipelineAccountabilityServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PipelineAccountabilityService(mock_db)
        assert hasattr(service, 'db')

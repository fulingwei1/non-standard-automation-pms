# -*- coding: utf-8 -*-
"""pipeline_health_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.pipeline_health_service import PipelineHealthService

class TestPipelineHealthServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PipelineHealthService(mock_db)
        assert hasattr(service, 'db')

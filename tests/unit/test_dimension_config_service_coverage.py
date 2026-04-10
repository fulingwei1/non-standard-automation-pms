# -*- coding: utf-8 -*-
"""dimension_config_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.engineer_performance.dimension_config_service import DimensionConfigService

class TestDimensionConfigServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = DimensionConfigService(mock_db)
        assert hasattr(service, 'db')

# -*- coding: utf-8 -*-
"""assembly_kit_service_enhanced单元测试"""
import pytest
from unittest.mock import Mock
from app.services.assembly_kit_service_enhanced import AssemblyKitServiceEnhanced

class TestAssemblyKitServiceEnhancedInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = AssemblyKitServiceEnhanced(mock_db)
        assert hasattr(service, 'db')

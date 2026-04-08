# -*- coding: utf-8 -*-
"""assembly_kit_optimizer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.assembly_kit_optimizer import AssemblyKitOptimizer

class TestAssemblyKitOptimizerInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = AssemblyKitOptimizer(mock_db)
        assert hasattr(service, 'db')

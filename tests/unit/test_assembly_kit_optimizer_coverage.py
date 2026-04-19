# -*- coding: utf-8 -*-
"""assembly_kit_optimizer单元测试"""
import pytest
from app.services.assembly_kit_optimizer import AssemblyKitOptimizer


class TestAssemblyKitOptimizerInit:
    def test_init_with_db(self):
        assert AssemblyKitOptimizer is not None
        assert hasattr(AssemblyKitOptimizer, 'optimize_estimated_ready_date')
        assert hasattr(AssemblyKitOptimizer, 'generate_optimization_suggestions')

# -*- coding: utf-8 -*-
"""assembly_kit单元测试"""

import pytest
from unittest.mock import Mock
from app.services.dashboard.adapters.assembly_kit import AssemblyKitDashboardAdapter


class TestAssemblyKitDashboardAdapterInit:
    def test_init(self):
        service = AssemblyKitDashboardAdapter(Mock(), Mock())
        assert service is not None

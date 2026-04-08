# -*- coding: utf-8 -*-
"""inventory_analysis_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.inventory_analysis_service import InventoryAnalysisService

class TestInventoryAnalysisServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = InventoryAnalysisService(mock_db)
        assert hasattr(service, 'db')

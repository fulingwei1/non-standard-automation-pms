# -*- coding: utf-8 -*-
"""production_progress_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.production_progress_service import ProductionProgressService

class TestProductionProgressServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ProductionProgressService(mock_db)
        assert hasattr(service, 'db')

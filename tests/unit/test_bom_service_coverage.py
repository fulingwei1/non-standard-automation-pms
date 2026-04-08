# -*- coding: utf-8 -*-
"""bom_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.bom_service import BomService

class TestBomServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = BomService(mock_db)
        assert hasattr(service, 'db')

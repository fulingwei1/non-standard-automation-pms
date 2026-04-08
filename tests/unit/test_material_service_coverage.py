# -*- coding: utf-8 -*-
"""material_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.material_service import MaterialService

class TestMaterialServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = MaterialService(mock_db)
        assert hasattr(service, 'db')

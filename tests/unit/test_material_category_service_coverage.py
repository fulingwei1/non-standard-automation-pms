# -*- coding: utf-8 -*-
"""material_category_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.material_category_service import MaterialCategoryService

class TestMaterialCategoryServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = MaterialCategoryService(mock_db)
        assert hasattr(service, 'db')

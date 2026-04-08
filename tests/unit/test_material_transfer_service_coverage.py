# -*- coding: utf-8 -*-
"""material_transfer_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.material_transfer_service import MaterialTransferService

class TestMaterialTransferServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = MaterialTransferService(mock_db)
        assert hasattr(service, 'db')

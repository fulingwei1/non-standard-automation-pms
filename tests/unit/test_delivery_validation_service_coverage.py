# -*- coding: utf-8 -*-
"""delivery_validation_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.delivery_validation_service import DeliveryValidationService

class TestDeliveryValidationServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = DeliveryValidationService(mock_db)
        assert hasattr(service, 'db')

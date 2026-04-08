# -*- coding: utf-8 -*-
"""payment_adjustment_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.payment_adjustment_service import PaymentAdjustmentService

class TestPaymentAdjustmentServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PaymentAdjustmentService(mock_db)
        assert hasattr(service, 'db')

# -*- coding: utf-8 -*-
"""payment_plan_service单元测试"""
import pytest
from unittest.mock import Mock
from services/sales/payment_plan_service import PaymentPlanService

class TestPaymentPlanServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PaymentPlanService(mock_db)
        assert hasattr(service, 'db')

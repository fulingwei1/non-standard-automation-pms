# -*- coding: utf-8 -*-
"""business_rules单元测试"""
import pytest
from unittest.mock import Mock
from app.services.business_rules import PaymentMilestone

class TestPaymentMilestoneInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PaymentMilestone(mock_db)
        assert hasattr(service, 'db')

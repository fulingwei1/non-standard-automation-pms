# -*- coding: utf-8 -*-
"""account_lockout_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.account_lockout_service import AccountLockoutService

class TestAccountLockoutServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = AccountLockoutService(mock_db)
        assert hasattr(service, 'db')

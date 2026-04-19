# -*- coding: utf-8 -*-
"""account_lockout_service单元测试"""

from app.services.account_lockout_service import AccountLockoutService


class TestAccountLockoutServiceInit:
    def test_static_api_available(self):
        assert AccountLockoutService is not None
        assert hasattr(AccountLockoutService, "check_lockout")
        assert hasattr(AccountLockoutService, "record_failed_login")

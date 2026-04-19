# -*- coding: utf-8 -*-
"""two_factor_service单元测试"""
from app.services.two_factor_service import TwoFactorService


class TestTwoFactorServiceInit:
    def test_init(self):
        service = TwoFactorService()
        assert service is not None
        assert service.fernet is not None

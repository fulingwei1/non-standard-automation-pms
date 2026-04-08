# -*- coding: utf-8 -*-
"""tenant_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.tenant_service import TenantService

class TestTenantServiceInit:
    def test_init(self):
        service = TenantService(Mock())
        assert service is not None

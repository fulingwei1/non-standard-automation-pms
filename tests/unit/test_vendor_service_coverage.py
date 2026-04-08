# -*- coding: utf-8 -*-
"""vendor_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.vendor_service import VendorService

class TestVendorServiceInit:
    def test_init(self):
        service = VendorService(Mock())
        assert service is not None

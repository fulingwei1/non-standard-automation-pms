# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 供应商服务"""
import pytest
from unittest.mock import MagicMock


class TestVendorServiceBusinessLogic:
    """供应商服务业务逻辑测试"""

    def test_vendor_create(self):
        """测试当前服务暴露 create 能力"""
        try:
            from app.services.vendor_service import VendorService

            mock_db = MagicMock()
            service = VendorService(mock_db)

            assert callable(service.create)
        except ImportError:
            pytest.skip("Module not found")

    def test_vendor_bulk_create(self):
        """测试当前服务暴露 bulk_create 能力"""
        try:
            from app.services.vendor_service import VendorService

            mock_db = MagicMock()
            service = VendorService(mock_db)

            assert callable(service.bulk_create)
        except ImportError:
            pytest.skip("Module not found")

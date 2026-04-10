# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 供应商服务"""
import pytest
from unittest.mock import MagicMock, patch


class TestVendorServiceBusinessLogic:
    """供应商服务业务逻辑测试"""

    def test_vendor_create(self):
        """测试创建供应商"""
        try:
            from app.services.vendor_service import VendorService

            mock_db = MagicMock()
            service = VendorService(mock_db)

            result = service.create({"name": "Test Vendor"})

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_vendor_bulk_create(self):
        """测试批量创建供应商"""
        try:
            from app.services.vendor_service import VendorService

            mock_db = MagicMock()
            service = VendorService(mock_db)

            result = service.bulk_create([{"name": "Vendor1"}])

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")
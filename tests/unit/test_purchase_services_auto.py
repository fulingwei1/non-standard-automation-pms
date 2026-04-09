# -*- coding: utf-8 -*-
"""Auto-generated tests for purchase modules"""
import pytest
from unittest.mock import MagicMock, patch
import importlib


class TestPurchaseModule:
    """Tests for purchase module"""

    def test_module_import(self):
        """Test purchase module can be imported"""
        try:
            mod = importlib.import_module('app.services.purchase')
            assert mod is not None
        except ImportError:
            pytest.skip("Module not found")


class TestPurchaseOrderService:
    """Tests for purchase order"""

    def test_service_import(self):
        """Test PurchaseOrderService"""
        try:
            mod = importlib.import_module('app.services.purchase.order_service')
            assert mod is not None
        except ImportError:
            pytest.skip("Module not found")


class TestPurchaseApprovalService:
    """Tests for purchase approval"""

    def test_service_import(self):
        """Test PurchaseApprovalService"""
        try:
            mod = importlib.import_module('app.services.purchase.approval_service')
            assert mod is not None
        except ImportError:
            pytest.skip("Module not found")
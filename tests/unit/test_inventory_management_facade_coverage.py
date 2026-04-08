# -*- coding: utf-8 -*-
"""inventory_management_facade单元测试"""
import pytest
from unittest.mock import Mock
from app.services.inventory.inventory_management_facade import InventoryManagementService

class TestInventoryManagementServiceInit:
    def test_init(self):
        service = InventoryManagementService(Mock())
        assert service is not None

# -*- coding: utf-8 -*-
"""stock_update_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.inventory.stock_update_service import InsufficientStockError

class TestInsufficientStockErrorInit:
    def test_init(self):
        service = InsufficientStockError(Mock())
        assert service is not None

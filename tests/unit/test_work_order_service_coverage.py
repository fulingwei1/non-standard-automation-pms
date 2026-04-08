# -*- coding: utf-8 -*-
"""work_order_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.production.work_order_service import WorkOrderService

class TestWorkOrderServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = WorkOrderService(mock_db)
        assert hasattr(service, 'db')

# -*- coding: utf-8 -*-
"""operation_log_service单元测试"""
import pytest
from unittest.mock import Mock
from services/sales/operation_log_service import SalesOperationLogService

class TestSalesOperationLogServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = SalesOperationLogService(mock_db)
        assert hasattr(service, 'db')

# -*- coding: utf-8 -*-
"""data_audit_service单元测试"""
import pytest
from unittest.mock import Mock
from services/sales/data_audit_service import SalesDataAuditService

class TestSalesDataAuditServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = SalesDataAuditService(mock_db)
        assert hasattr(service, 'db')

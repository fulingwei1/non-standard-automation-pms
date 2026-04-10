# -*- coding: utf-8 -*-
"""permission_audit_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.permission_management.permission_audit_service import PermissionAuditService

class TestPermissionAuditServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PermissionAuditService(mock_db)
        assert hasattr(service, 'db')

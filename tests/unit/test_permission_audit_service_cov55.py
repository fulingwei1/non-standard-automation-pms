# -*- coding: utf-8 -*-
"""
Tests for app/services/permission_audit_service.py
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.permission_audit_service import PermissionAuditService
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


@pytest.fixture
def mock_db():
    return MagicMock()


def test_log_audit_creates_record(mock_db):
    """log_audit 应创建并保存审计记录"""
    with patch("app.services.permission_audit_service.save_obj") as mock_save, \
         patch("app.services.permission_audit_service.PermissionAudit") as MockAudit:
        mock_instance = MagicMock()
        MockAudit.return_value = mock_instance
        result = PermissionAuditService.log_audit(
            db=mock_db,
            operator_id=1,
            action="USER_CREATED",
            target_type="user",
            target_id=5
        )
        MockAudit.assert_called_once()
        mock_save.assert_called_once_with(mock_db, mock_instance)


def test_log_audit_serializes_detail(mock_db):
    """detail 字典应被序列化为 JSON 字符串"""
    with patch("app.services.permission_audit_service.save_obj"), \
         patch("app.services.permission_audit_service.PermissionAudit") as MockAudit:
        detail = {"role_ids": [1, 2, 3]}
        PermissionAuditService.log_audit(
            db=mock_db, operator_id=1, action="ROLE_ASSIGNED",
            target_type="user", target_id=2, detail=detail
        )
        call_kwargs = MockAudit.call_args[1]
        assert '"role_ids"' in call_kwargs.get("detail", "")


def test_log_user_role_assignment(mock_db):
    """log_user_role_assignment 应调用 log_audit"""
    with patch.object(PermissionAuditService, "log_audit") as mock_log:
        PermissionAuditService.log_user_role_assignment(
            db=mock_db, operator_id=1, user_id=2, role_ids=[3, 4]
        )
        mock_log.assert_called_once()
        call_kwargs = mock_log.call_args[1]
        assert call_kwargs["target_type"] == "user"
        assert call_kwargs["target_id"] == 2


def test_log_role_permission_assignment(mock_db):
    """log_role_permission_assignment 应调用 log_audit"""
    with patch.object(PermissionAuditService, "log_audit") as mock_log:
        PermissionAuditService.log_role_permission_assignment(
            db=mock_db, operator_id=1, role_id=10, permission_ids=[20, 21]
        )
        mock_log.assert_called_once()
        call_kwargs = mock_log.call_args[1]
        assert call_kwargs["target_type"] == "role"
        assert call_kwargs["target_id"] == 10


def test_log_user_operation(mock_db):
    """log_user_operation 应调用 log_audit"""
    with patch.object(PermissionAuditService, "log_audit") as mock_log:
        PermissionAuditService.log_user_operation(
            db=mock_db, operator_id=1, user_id=3, action="USER_UPDATED"
        )
        mock_log.assert_called_once()
        call_kwargs = mock_log.call_args[1]
        assert call_kwargs["action"] == "USER_UPDATED"


def test_log_role_operation(mock_db):
    """log_role_operation 应调用 log_audit"""
    with patch.object(PermissionAuditService, "log_audit") as mock_log:
        PermissionAuditService.log_role_operation(
            db=mock_db, operator_id=1, role_id=5, action="ROLE_UPDATED"
        )
        mock_log.assert_called_once()
        call_kwargs = mock_log.call_args[1]
        assert call_kwargs["target_type"] == "role"


def test_action_constants():
    """验证操作常量已定义"""
    assert PermissionAuditService.ACTION_USER_CREATED == "USER_CREATED"
    assert PermissionAuditService.ACTION_ROLE_CREATED == "ROLE_CREATED"
    assert PermissionAuditService.ACTION_PERMISSION_CREATED == "PERMISSION_CREATED"

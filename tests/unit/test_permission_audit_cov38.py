# -*- coding: utf-8 -*-
"""
Unit tests for PermissionAuditService (第三十八批)
"""
import json
import pytest

pytest.importorskip("app.services.permission_audit_service", reason="导入失败，跳过")

from unittest.mock import MagicMock, patch, call

try:
    from app.services.permission_audit_service import PermissionAuditService
except ImportError:
    pytestmark = pytest.mark.skip(reason="permission_audit_service 不可用")
    PermissionAuditService = None


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_audit():
    audit = MagicMock()
    audit.id = 1
    audit.operator_id = 42
    audit.action = "USER_CREATED"
    audit.target_type = "user"
    audit.target_id = 10
    return audit


class TestPermissionAuditServiceConstants:
    """测试操作类型常量定义"""

    def test_user_action_constants(self):
        assert PermissionAuditService.ACTION_USER_CREATED == "USER_CREATED"
        assert PermissionAuditService.ACTION_USER_UPDATED == "USER_UPDATED"
        assert PermissionAuditService.ACTION_USER_DELETED == "USER_DELETED"

    def test_role_action_constants(self):
        assert PermissionAuditService.ACTION_ROLE_CREATED == "ROLE_CREATED"
        assert PermissionAuditService.ACTION_ROLE_UPDATED == "ROLE_UPDATED"
        assert PermissionAuditService.ACTION_ROLE_DELETED == "ROLE_DELETED"

    def test_permission_action_constants(self):
        assert PermissionAuditService.ACTION_PERMISSION_CREATED == "PERMISSION_CREATED"
        assert PermissionAuditService.ACTION_PERMISSION_UPDATED == "PERMISSION_UPDATED"
        assert PermissionAuditService.ACTION_PERMISSION_DELETED == "PERMISSION_DELETED"

    def test_user_role_action_constants(self):
        assert PermissionAuditService.ACTION_USER_ROLE_ASSIGNED == "USER_ROLE_ASSIGNED"
        assert PermissionAuditService.ACTION_USER_ROLE_REVOKED == "USER_ROLE_REVOKED"


class TestLogAudit:
    """测试 log_audit 静态方法"""

    def test_log_audit_basic(self, mock_db, mock_audit):
        """基本审计记录"""
        with patch("app.services.permission_audit_service.PermissionAudit") as MockAudit, \
             patch("app.services.permission_audit_service.save_obj") as mock_save:
            MockAudit.return_value = mock_audit
            result = PermissionAuditService.log_audit(
                db=mock_db,
                operator_id=42,
                action="USER_CREATED",
                target_type="user",
                target_id=10
            )
            MockAudit.assert_called_once()
            mock_save.assert_called_once_with(mock_db, mock_audit)
            assert result == mock_audit

    def test_log_audit_with_detail(self, mock_db, mock_audit):
        """带 detail 信息的审计记录"""
        detail = {"username": "test_user", "email": "test@example.com"}
        with patch("app.services.permission_audit_service.PermissionAudit") as MockAudit, \
             patch("app.services.permission_audit_service.save_obj"):
            MockAudit.return_value = mock_audit
            PermissionAuditService.log_audit(
                db=mock_db,
                operator_id=42,
                action="USER_CREATED",
                target_type="user",
                target_id=10,
                detail=detail
            )
            call_kwargs = MockAudit.call_args[1]
            assert call_kwargs["detail"] == json.dumps(detail, ensure_ascii=False)

    def test_log_audit_with_ip_and_user_agent(self, mock_db, mock_audit):
        """带 IP 和 User-Agent 的审计记录"""
        with patch("app.services.permission_audit_service.PermissionAudit") as MockAudit, \
             patch("app.services.permission_audit_service.save_obj"):
            MockAudit.return_value = mock_audit
            PermissionAuditService.log_audit(
                db=mock_db,
                operator_id=1,
                action="ROLE_DELETED",
                target_type="role",
                target_id=5,
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0"
            )
            call_kwargs = MockAudit.call_args[1]
            assert call_kwargs["ip_address"] == "192.168.1.1"
            assert call_kwargs["user_agent"] == "Mozilla/5.0"

    def test_log_audit_no_detail(self, mock_db, mock_audit):
        """无 detail 时 detail 字段为 None"""
        with patch("app.services.permission_audit_service.PermissionAudit") as MockAudit, \
             patch("app.services.permission_audit_service.save_obj"):
            MockAudit.return_value = mock_audit
            PermissionAuditService.log_audit(
                db=mock_db,
                operator_id=1,
                action="USER_ACTIVATED",
                target_type="user",
                target_id=7
            )
            call_kwargs = MockAudit.call_args[1]
            assert call_kwargs["detail"] is None

    def test_log_audit_returns_audit_object(self, mock_db, mock_audit):
        """返回创建的审计对象"""
        with patch("app.services.permission_audit_service.PermissionAudit") as MockAudit, \
             patch("app.services.permission_audit_service.save_obj"):
            MockAudit.return_value = mock_audit
            result = PermissionAuditService.log_audit(
                db=mock_db,
                operator_id=1,
                action="PERMISSION_CREATED",
                target_type="permission",
                target_id=99
            )
            assert result is mock_audit

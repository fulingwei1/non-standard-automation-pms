# -*- coding: utf-8 -*-
"""
权限审计服务测试
测试 PermissionAuditService 的各项功能
"""

import pytest
from unittest.mock import Mock, patch


@pytest.fixture
def mock_db_session():
    """创建模拟数据库会话"""
    db = Mock()
    db.add = Mock()
    db.flush = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    return db


@pytest.fixture
def mock_audit_context():
    """创建模拟审计上下文"""
    return {
        "operator_id": 1,
        "client_ip": "127.0.0.1",
        "user_agent": "Mozilla/5.0",
        "detail": {},
        "tenant_id": 1,
    }


class TestPermissionAuditService:
    """权限审计服务测试类"""

    def test_constants_defined(self):
        """测试常量定义正确"""
        from app.services.permission_management.permission_audit_service import PermissionAuditService
        
        # 验证用户操作常量
        assert PermissionAuditService.ACTION_USER_CREATED == "USER_CREATED"
        assert PermissionAuditService.ACTION_USER_UPDATED == "USER_UPDATED"
        assert PermissionAuditService.ACTION_USER_DELETED == "USER_DELETED"
        assert PermissionAuditService.ACTION_USER_ACTIVATED == "USER_ACTIVATED"
        assert PermissionAuditService.ACTION_USER_DEACTIVATED == "USER_DEACTIVATED"
        assert PermissionAuditService.ACTION_USER_ROLE_ASSIGNED == "USER_ROLE_ASSIGNED"
        assert PermissionAuditService.ACTION_USER_ROLE_REVOKED == "USER_ROLE_REVOKED"
        
        # 验证角色操作常量
        assert PermissionAuditService.ACTION_ROLE_CREATED == "ROLE_CREATED"
        assert PermissionAuditService.ACTION_ROLE_UPDATED == "ROLE_UPDATED"
        assert PermissionAuditService.ACTION_ROLE_DELETED == "ROLE_DELETED"
        assert PermissionAuditService.ACTION_ROLE_ACTIVATED == "ROLE_ACTIVATED"
        assert PermissionAuditService.ACTION_ROLE_DEACTIVATED == "ROLE_DEACTIVATED"
        assert PermissionAuditService.ACTION_ROLE_PERMISSION_ASSIGNED == "ROLE_PERMISSION_ASSIGNED"
        assert PermissionAuditService.ACTION_ROLE_PERMISSION_REVOKED == "ROLE_PERMISSION_REVOKED"
        
        # 验证权限操作常量
        assert PermissionAuditService.ACTION_PERMISSION_CREATED == "PERMISSION_CREATED"
        assert PermissionAuditService.ACTION_PERMISSION_UPDATED == "PERMISSION_UPDATED"
        assert PermissionAuditService.ACTION_PERMISSION_DELETED == "PERMISSION_DELETED"

    def test_log_audit_basic(self, mock_db_session, mock_audit_context):
        """测试基本的审计日志记录"""
        with patch('app.common.context.get_audit_context', return_value=mock_audit_context), \
             patch('app.services.permission_management.permission_audit_service.save_obj'):
            from app.services.permission_management.permission_audit_service import PermissionAuditService
            
            # 调用日志记录 - 验证不报错
            PermissionAuditService.log_audit(
                db=mock_db_session,
                operator_id=1,
                action="USER_CREATED",
                target_type="user",
                target_id=100,
                detail={"username": "test_user"},
            )

    def test_log_audit_with_ip_and_useragent(self, mock_db_session):
        """测试带IP和User-Agent的审计日志"""
        mock_context = {
            "operator_id": 1,
            "client_ip": "",
            "user_agent": "",
            "detail": {},
            "tenant_id": 1,
        }
        with patch('app.common.context.get_audit_context', return_value=mock_context), \
             patch('app.services.permission_management.permission_audit_service.save_obj'):
            from app.services.permission_management.permission_audit_service import PermissionAuditService
            
            # 调用日志记录 - 验证不报错
            PermissionAuditService.log_audit(
                db=mock_db_session,
                operator_id=1,
                action="ROLE_UPDATED",
                target_type="role",
                target_id=200,
                ip_address="192.168.1.1",
                user_agent="TestAgent/1.0",
            )

    def test_log_user_role_assignment(self, mock_db_session, mock_audit_context):
        """测试用户角色分配日志"""
        with patch('app.common.context.get_audit_context', return_value=mock_audit_context), \
             patch('app.services.permission_management.permission_audit_service.save_obj'):
            from app.services.permission_management.permission_audit_service import PermissionAuditService
            
            # 调用日志记录 - 验证不报错
            PermissionAuditService.log_user_role_assignment(
                db=mock_db_session,
                operator_id=1,
                user_id=100,
                role_ids=[1, 2, 3],
            )

    def test_log_role_permission_assignment(self, mock_db_session, mock_audit_context):
        """测试角色权限分配日志"""
        with patch('app.common.context.get_audit_context', return_value=mock_audit_context), \
             patch('app.services.permission_management.permission_audit_service.save_obj'):
            from app.services.permission_management.permission_audit_service import PermissionAuditService
            
            PermissionAuditService.log_role_permission_assignment(
                db=mock_db_session,
                operator_id=1,
                role_id=50,
                permission_ids=[10, 20, 30],
            )

    def test_log_user_operation(self, mock_db_session, mock_audit_context):
        """测试用户操作日志"""
        with patch('app.common.context.get_audit_context', return_value=mock_audit_context), \
             patch('app.services.permission_management.permission_audit_service.save_obj'):
            from app.services.permission_management.permission_audit_service import PermissionAuditService
            
            changes = {"email": "new@example.com", "phone": "1234567890"}
            
            PermissionAuditService.log_user_operation(
                db=mock_db_session,
                operator_id=1,
                user_id=100,
                action="USER_UPDATED",
                changes=changes,
            )

    def test_log_role_operation(self, mock_db_session, mock_audit_context):
        """测试角色操作日志"""
        with patch('app.common.context.get_audit_context', return_value=mock_audit_context), \
             patch('app.services.permission_management.permission_audit_service.save_obj'):
            from app.services.permission_management.permission_audit_service import PermissionAuditService
            
            changes = {"role_name": "新角色名", "is_active": True}
            
            PermissionAuditService.log_role_operation(
                db=mock_db_session,
                operator_id=1,
                role_id=50,
                action="ROLE_UPDATED",
                changes=changes,
            )
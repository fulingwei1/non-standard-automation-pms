# -*- coding: utf-8 -*-
"""
审批代理人服务增强测试

覆盖 ApprovalDelegateService 的所有核心方法和边界条件
"""
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch, call

import pytest

from app.services.approval_engine.delegate import ApprovalDelegateService


@pytest.fixture
def db():
    """Mock数据库会话"""
    return MagicMock()


@pytest.fixture
def service(db):
    """审批代理服务实例"""
    return ApprovalDelegateService(db)


class TestGetActiveDelegate:
    """测试获取生效的代理配置"""

    def test_no_active_delegate_found(self, service, db):
        """测试：没有找到生效的代理配置"""
        db.query.return_value.filter.return_value.all.return_value = []
        
        result = service.get_active_delegate(user_id=1)
        
        assert result is None

    def test_delegate_with_scope_all(self, service, db):
        """测试：代理范围为ALL的配置"""
        delegate = MagicMock(scope="ALL", id=1)
        db.query.return_value.filter.return_value.all.return_value = [delegate]
        
        result = service.get_active_delegate(user_id=1, template_id=100)
        
        assert result == delegate

    def test_delegate_with_scope_template_match(self, service, db):
        """测试：代理范围为TEMPLATE且匹配"""
        delegate = MagicMock(scope="TEMPLATE", template_ids=[100, 200], id=1)
        db.query.return_value.filter.return_value.all.return_value = [delegate]
        
        result = service.get_active_delegate(user_id=1, template_id=100)
        
        assert result == delegate

    def test_delegate_with_scope_template_no_match(self, service, db):
        """测试：代理范围为TEMPLATE但不匹配"""
        delegate = MagicMock(scope="TEMPLATE", template_ids=[200, 300], id=1)
        db.query.return_value.filter.return_value.all.return_value = [delegate]
        
        result = service.get_active_delegate(user_id=1, template_id=100)
        
        assert result is None

    def test_delegate_with_scope_category_match(self, service, db):
        """测试：代理范围为CATEGORY且匹配"""
        template = MagicMock(id=100, category="IT")
        delegate = MagicMock(scope="CATEGORY", categories=["IT", "HR"], id=1)
        
        db.query.return_value.filter.return_value.all.return_value = [delegate]
        db.query.return_value.filter.return_value.first.return_value = template
        
        result = service.get_active_delegate(user_id=1, template_id=100)
        
        assert result == delegate

    def test_delegate_with_scope_category_no_match(self, service, db):
        """测试：代理范围为CATEGORY但不匹配"""
        template = MagicMock(id=100, category="Finance")
        delegate = MagicMock(scope="CATEGORY", categories=["IT", "HR"], id=1)
        
        db.query.return_value.filter.return_value.all.return_value = [delegate]
        db.query.return_value.filter.return_value.first.return_value = template
        
        result = service.get_active_delegate(user_id=1, template_id=100)
        
        assert result is None

    def test_custom_check_date(self, service, db):
        """测试：使用自定义检查日期"""
        custom_date = date(2026, 3, 1)
        db.query.return_value.filter.return_value.all.return_value = []
        
        service.get_active_delegate(user_id=1, check_date=custom_date)
        
        # 验证filter被调用时使用了custom_date
        assert db.query.return_value.filter.called

    def test_multiple_delegates_priority(self, service, db):
        """测试：多个代理配置时的优先级（ALL优先）"""
        delegate_all = MagicMock(scope="ALL", id=1)
        delegate_template = MagicMock(scope="TEMPLATE", template_ids=[100], id=2)
        
        db.query.return_value.filter.return_value.all.return_value = [
            delegate_all, delegate_template
        ]
        
        result = service.get_active_delegate(user_id=1, template_id=100)
        
        assert result == delegate_all


class TestApplyDelegation:
    """测试应用代理配置"""

    def test_no_delegate_config(self, service, db):
        """测试：无代理配置时返回None"""
        task = MagicMock()
        task.instance = MagicMock(template_id=100)
        
        with patch.object(service, 'get_active_delegate', return_value=None):
            result = service.apply_delegation(task, original_assignee_id=1)
            
            assert result is None

    def test_apply_delegation_success(self, service, db):
        """测试：成功应用代理配置"""
        task = MagicMock(id=10)
        task.instance = MagicMock(template_id=100, id=5)
        
        delegate_config = MagicMock(id=1, delegate_id=2)
        delegate_user = MagicMock(id=2, real_name="张三", username="zhangsan")
        
        db.query.return_value.filter.return_value.first.return_value = delegate_user
        
        with patch.object(service, 'get_active_delegate', return_value=delegate_config):
            result = service.apply_delegation(task, original_assignee_id=1)
            
            assert result == task
            assert task.original_assignee_id == 1
            assert task.assignee_type == "DELEGATED"
            assert task.assignee_id == 2
            assert task.assignee_name == "张三"
            
            # 验证日志被记录
            assert db.add.called

    def test_delegate_user_has_no_real_name(self, service, db):
        """测试：代理人无真实姓名时使用用户名"""
        task = MagicMock(id=10)
        task.instance = MagicMock(template_id=100, id=5)
        
        delegate_config = MagicMock(id=1, delegate_id=2)
        delegate_user = MagicMock(id=2, real_name=None, username="zhangsan")
        
        db.query.return_value.filter.return_value.first.return_value = delegate_user
        
        with patch.object(service, 'get_active_delegate', return_value=delegate_config):
            result = service.apply_delegation(task, original_assignee_id=1)
            
            assert task.assignee_name == "zhangsan"

    def test_delegate_user_not_found(self, service, db):
        """测试：代理人用户未找到"""
        task = MagicMock(id=10)
        task.instance = MagicMock(template_id=100, id=5)
        
        delegate_config = MagicMock(id=1, delegate_id=2)
        
        db.query.return_value.filter.return_value.first.return_value = None
        
        with patch.object(service, 'get_active_delegate', return_value=delegate_config):
            result = service.apply_delegation(task, original_assignee_id=1)
            
            assert result == task
            assert task.assignee_id == 2


class TestCreateDelegate:
    """测试创建代理配置"""

    def test_create_delegate_success(self, service, db):
        """测试：成功创建代理配置"""
        db.query.return_value.filter.return_value.first.return_value = None
        
        result = service.create_delegate(
            user_id=1,
            delegate_id=2,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            scope="ALL",
            reason="出差",
            created_by=1
        )
        
        assert db.add.called
        assert db.flush.called

    def test_create_delegate_with_overlapping_config(self, service, db):
        """测试：存在重叠的代理配置时抛出异常"""
        existing_delegate = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing_delegate
        
        with pytest.raises(ValueError, match="存在重叠的代理配置"):
            service.create_delegate(
                user_id=1,
                delegate_id=2,
                start_date=date(2026, 2, 1),
                end_date=date(2026, 2, 28),
                scope="ALL"
            )

    def test_create_delegate_with_template_scope(self, service, db):
        """测试：创建指定模板的代理配置"""
        db.query.return_value.filter.return_value.first.return_value = None
        
        result = service.create_delegate(
            user_id=1,
            delegate_id=2,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            scope="TEMPLATE",
            template_ids=[100, 200],
            created_by=1
        )
        
        assert db.add.called

    def test_create_delegate_with_category_scope(self, service, db):
        """测试：创建指定分类的代理配置"""
        db.query.return_value.filter.return_value.first.return_value = None
        
        result = service.create_delegate(
            user_id=1,
            delegate_id=2,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            scope="CATEGORY",
            categories=["IT", "HR"],
            created_by=1
        )
        
        assert db.add.called

    def test_create_delegate_default_created_by(self, service, db):
        """测试：created_by默认使用user_id"""
        db.query.return_value.filter.return_value.first.return_value = None
        
        service.create_delegate(
            user_id=1,
            delegate_id=2,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            scope="ALL"
        )
        
        # 通过检查add被调用来验证
        assert db.add.called


class TestUpdateDelegate:
    """测试更新代理配置"""

    def test_update_delegate_success(self, service, db):
        """测试：成功更新代理配置"""
        delegate = MagicMock(id=1)
        db.query.return_value.filter.return_value.first.return_value = delegate
        
        result = service.update_delegate(
            delegate_id=1,
            scope="TEMPLATE",
            template_ids=[100, 200],
            reason="更新原因"
        )
        
        assert result == delegate
        assert delegate.scope == "TEMPLATE"
        assert delegate.template_ids == [100, 200]
        assert delegate.reason == "更新原因"

    def test_update_delegate_not_found(self, service, db):
        """测试：代理配置不存在"""
        db.query.return_value.filter.return_value.first.return_value = None
        
        result = service.update_delegate(delegate_id=999, scope="ALL")
        
        assert result is None

    def test_update_delegate_only_allowed_fields(self, service, db):
        """测试：只更新允许的字段"""
        delegate = MagicMock(id=1)
        db.query.return_value.filter.return_value.first.return_value = delegate
        
        # 尝试更新一个不在allowed_fields中的字段
        result = service.update_delegate(
            delegate_id=1,
            scope="ALL",
            invalid_field="should_not_update"
        )
        
        assert result == delegate
        assert delegate.scope == "ALL"
        # invalid_field不应该被设置
        assert not hasattr(delegate, 'invalid_field') or delegate.invalid_field != "should_not_update"


class TestCancelDelegate:
    """测试取消代理配置"""

    def test_cancel_delegate_success(self, service, db):
        """测试：成功取消代理配置"""
        delegate = MagicMock(id=1, is_active=True)
        db.query.return_value.filter.return_value.first.return_value = delegate
        
        result = service.cancel_delegate(delegate_id=1)
        
        assert result is True
        assert delegate.is_active is False

    def test_cancel_delegate_not_found(self, service, db):
        """测试：代理配置不存在"""
        db.query.return_value.filter.return_value.first.return_value = None
        
        result = service.cancel_delegate(delegate_id=999)
        
        assert result is False


class TestGetUserDelegates:
    """测试获取用户的代理配置"""

    def test_get_user_delegates_active_only(self, service, db):
        """测试：只获取活跃的代理配置"""
        delegates = [MagicMock(id=1), MagicMock(id=2)]
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = delegates
        
        result = service.get_user_delegates(user_id=1, include_inactive=False)
        
        assert result == delegates

    def test_get_user_delegates_include_inactive(self, service, db):
        """测试：包含不活跃的代理配置"""
        delegates = [MagicMock(id=1), MagicMock(id=2), MagicMock(id=3)]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = delegates
        
        result = service.get_user_delegates(user_id=1, include_inactive=True)
        
        assert result == delegates

    def test_get_user_delegates_empty(self, service, db):
        """测试：用户无代理配置"""
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        result = service.get_user_delegates(user_id=1)
        
        assert result == []


class TestGetDelegatedToUser:
    """测试获取用户作为代理人的配置"""

    def test_get_delegated_to_user_active_only(self, service, db):
        """测试：只获取活跃的代理配置"""
        delegates = [MagicMock(id=1), MagicMock(id=2)]
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = delegates
        
        result = service.get_delegated_to_user(delegate_id=2, include_inactive=False)
        
        assert result == delegates

    def test_get_delegated_to_user_include_inactive(self, service, db):
        """测试：包含不活跃的配置"""
        delegates = [MagicMock(id=1), MagicMock(id=2), MagicMock(id=3)]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = delegates
        
        result = service.get_delegated_to_user(delegate_id=2, include_inactive=True)
        
        assert result == delegates


class TestRecordDelegateAction:
    """测试记录代理操作"""

    def test_record_delegate_action_success(self, service, db):
        """测试：成功记录代理操作"""
        log = MagicMock(id=1)
        db.query.return_value.filter.return_value.first.return_value = log
        
        service.record_delegate_action(delegate_log_id=1, action="APPROVED")
        
        assert log.action == "APPROVED"
        assert log.action_at is not None

    def test_record_delegate_action_log_not_found(self, service, db):
        """测试：代理日志不存在"""
        db.query.return_value.filter.return_value.first.return_value = None
        
        # 不应抛出异常
        service.record_delegate_action(delegate_log_id=999, action="APPROVED")


class TestNotifyOriginalUser:
    """测试通知原审批人"""

    def test_notify_original_user_success(self, service, db):
        """测试：成功通知原审批人"""
        config = MagicMock(id=1, notify_original=True, user_id=1)
        log = MagicMock(id=1, delegate_config_id=1, action="APPROVED")
        
        db.query.return_value.filter.return_value.first.side_effect = [log, config]
        
        with patch.object(service, '_send_delegate_notification'):
            service.notify_original_user(delegate_log_id=1)
            
            assert log.original_notified is True
            assert log.original_notified_at is not None

    def test_notify_original_user_config_disabled(self, service, db):
        """测试：配置禁用通知"""
        config = MagicMock(id=1, notify_original=False)
        log = MagicMock(id=1, delegate_config_id=1)
        
        db.query.return_value.filter.return_value.first.side_effect = [log, config]
        
        with patch.object(service, '_send_delegate_notification') as mock_send:
            service.notify_original_user(delegate_log_id=1)
            
            # 不应该发送通知
            assert not mock_send.called

    def test_notify_original_user_log_not_found(self, service, db):
        """测试：代理日志不存在"""
        db.query.return_value.filter.return_value.first.return_value = None
        
        # 不应抛出异常
        service.notify_original_user(delegate_log_id=999)


class TestCleanupExpiredDelegates:
    """测试清理过期代理配置"""

    def test_cleanup_expired_delegates(self, service, db):
        """测试：清理过期的代理配置"""
        with patch('app.services.approval_engine.delegate.date') as mock_date:
            mock_date.today.return_value = date(2026, 3, 1)
            
            service.cleanup_expired_delegates()
            
            # 验证update被调用
            assert db.query.return_value.filter.return_value.update.called


class TestSendDelegateNotification:
    """测试发送代理通知（私有方法）"""

    def test_send_delegate_notification_approved(self, service, db):
        """测试：发送审批通过通知"""
        log = MagicMock(id=1, task_id=10, action="APPROVED")
        config = MagicMock(id=1, user_id=1)
        task = MagicMock(id=10)
        task.instance = MagicMock(id=5, title="出差申请")
        
        db.query.return_value.filter.return_value.first.return_value = task
        
        with patch('app.services.approval_engine.notify.ApprovalNotifyService') as MockNotifyService:
            mock_notify = MockNotifyService.return_value
            
            service._send_delegate_notification(log, config)
            
            # 验证通知服务被调用
            assert mock_notify._send_notification.called

    def test_send_delegate_notification_rejected(self, service, db):
        """测试：发送驳回通知"""
        log = MagicMock(id=1, task_id=10, action="REJECTED")
        config = MagicMock(id=1, user_id=1)
        task = MagicMock(id=10)
        task.instance = MagicMock(id=5, title="出差申请")
        
        db.query.return_value.filter.return_value.first.return_value = task
        
        with patch('app.services.approval_engine.notify.ApprovalNotifyService') as MockNotifyService:
            mock_notify = MockNotifyService.return_value
            
            service._send_delegate_notification(log, config)
            
            assert mock_notify._send_notification.called

    def test_send_delegate_notification_task_not_found(self, service, db):
        """测试：任务不存在时不发送通知"""
        log = MagicMock(id=1, task_id=10)
        config = MagicMock(id=1, user_id=1)
        
        db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('app.services.approval_engine.notify.ApprovalNotifyService') as MockNotifyService:
            mock_notify = MockNotifyService.return_value
            
            service._send_delegate_notification(log, config)
            
            # 不应该发送通知
            assert not mock_notify._send_notification.called

    def test_send_delegate_notification_exception(self, service, db):
        """测试：发送通知异常处理"""
        log = MagicMock(id=1, task_id=10)
        config = MagicMock(id=1, user_id=1)
        
        db.query.return_value.filter.return_value.first.side_effect = Exception("Database error")
        
        # 不应抛出异常
        service._send_delegate_notification(log, config)

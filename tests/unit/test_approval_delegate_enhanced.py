# -*- coding: utf-8 -*-
"""
审批代理人服务增强测试
补充覆盖核心业务逻辑和异常场景,提升覆盖率到60%+
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime, timedelta

from app.services.approval_engine.delegate import ApprovalDelegateService


@pytest.fixture
def db_mock():
    """数据库mock"""
    return MagicMock()


@pytest.fixture
def service(db_mock):
    """服务实例"""
    return ApprovalDelegateService(db_mock)


@pytest.fixture
def sample_delegate_config():
    """示例代理配置"""
    config = MagicMock()
    config.id = 1
    config.user_id = 100
    config.delegate_id = 200
    config.scope = "ALL"
    config.template_ids = None
    config.categories = None
    config.start_date = date.today() - timedelta(days=1)
    config.end_date = date.today() + timedelta(days=7)
    config.is_active = True
    config.reason = "出差"
    config.notify_original = True
    config.notify_delegate = True
    config.created_by = 100
    return config


@pytest.fixture
def sample_task():
    """示例审批任务"""
    task = MagicMock()
    task.id = 10
    task.instance_id = 50
    task.node_id = 5
    task.status = "PENDING"
    task.assignee_id = 100
    task.assignee_name = "张三"
    task.assignee_type = "NORMAL"
    task.original_assignee_id = None
    task.due_at = datetime.now() + timedelta(hours=24)
    task.is_countersign = False
    task.task_type = "APPROVAL"
    task.task_order = 1
    
    task.instance = MagicMock()
    task.instance.id = 50
    task.instance.template_id = 5
    task.instance.title = "测试审批"
    
    task.node = MagicMock()
    task.node.id = 5
    task.node.can_transfer = True
    task.node.can_add_approver = True
    
    return task


class TestGetActiveDelegate:
    """测试获取生效的代理配置"""
    
    def test_get_active_delegate_all_scope(self, service, db_mock, sample_delegate_config):
        """测试ALL范围的代理"""
        db_mock.query.return_value.filter.return_value.all.return_value = [sample_delegate_config]
        
        result = service.get_active_delegate(user_id=100)
        
        assert result == sample_delegate_config
    
    def test_get_active_delegate_template_scope_match(self, service, db_mock, sample_delegate_config):
        """测试TEMPLATE范围匹配"""
        sample_delegate_config.scope = "TEMPLATE"
        sample_delegate_config.template_ids = [1, 5, 10]
        db_mock.query.return_value.filter.return_value.all.return_value = [sample_delegate_config]
        
        result = service.get_active_delegate(user_id=100, template_id=5)
        
        assert result == sample_delegate_config
    
    def test_get_active_delegate_template_scope_no_match(self, service, db_mock, sample_delegate_config):
        """测试TEMPLATE范围不匹配"""
        sample_delegate_config.scope = "TEMPLATE"
        sample_delegate_config.template_ids = [1, 2, 3]
        db_mock.query.return_value.filter.return_value.all.return_value = [sample_delegate_config]
        
        result = service.get_active_delegate(user_id=100, template_id=5)
        
        assert result is None
    
    def test_get_active_delegate_category_scope_match(self, service, db_mock, sample_delegate_config):
        """测试CATEGORY范围匹配"""
        sample_delegate_config.scope = "CATEGORY"
        sample_delegate_config.categories = ["PROCUREMENT", "FINANCE"]
        
        # Mock模板查询
        template = MagicMock()
        template.category = "PROCUREMENT"
        
        db_mock.query.return_value.filter.side_effect = [
            MagicMock(all=lambda: [sample_delegate_config]),  # 代理配置查询
            MagicMock(first=lambda: template)  # 模板查询
        ]
        
        result = service.get_active_delegate(user_id=100, template_id=5)
        
        assert result == sample_delegate_config
    
    def test_get_active_delegate_no_active_config(self, service, db_mock):
        """测试没有生效的配置"""
        db_mock.query.return_value.filter.return_value.all.return_value = []
        
        result = service.get_active_delegate(user_id=100)
        
        assert result is None
    
    def test_get_active_delegate_custom_check_date(self, service, db_mock, sample_delegate_config):
        """测试自定义检查日期"""
        check_date = date(2024, 3, 15)
        sample_delegate_config.start_date = date(2024, 3, 10)
        sample_delegate_config.end_date = date(2024, 3, 20)
        
        db_mock.query.return_value.filter.return_value.all.return_value = [sample_delegate_config]
        
        result = service.get_active_delegate(user_id=100, check_date=check_date)
        
        assert result == sample_delegate_config


class TestApplyDelegation:
    """测试应用代理"""
    
    def test_apply_delegation_success(self, service, db_mock, sample_task, sample_delegate_config):
        """测试成功应用代理"""
        with patch.object(service, 'get_active_delegate', return_value=sample_delegate_config):
            # Mock代理人用户
            delegate_user = MagicMock()
            delegate_user.real_name = "李四"
            delegate_user.username = "lisi"
            
            db_mock.query.return_value.filter.return_value.first.return_value = delegate_user
            
            result = service.apply_delegation(sample_task, original_assignee_id=100)
            
            assert result == sample_task
            assert sample_task.original_assignee_id == 100
            assert sample_task.assignee_type == "DELEGATED"
            assert sample_task.assignee_id == 200
            assert sample_task.assignee_name == "李四"
    
    def test_apply_delegation_no_delegate_config(self, service, db_mock, sample_task):
        """测试无代理配置"""
        with patch.object(service, 'get_active_delegate', return_value=None):
            result = service.apply_delegation(sample_task, original_assignee_id=100)
            
            assert result is None
    
    def test_apply_delegation_creates_log(self, service, db_mock, sample_task, sample_delegate_config):
        """测试创建代理日志"""
        with patch.object(service, 'get_active_delegate', return_value=sample_delegate_config):
            delegate_user = MagicMock()
            delegate_user.real_name = "李四"
            db_mock.query.return_value.filter.return_value.first.return_value = delegate_user
            
            service.apply_delegation(sample_task, original_assignee_id=100)
            
            # 验证添加了日志
            assert db_mock.add.called


class TestCreateDelegate:
    """测试创建代理配置"""
    
    def test_create_delegate_success(self, service, db_mock):
        """测试成功创建代理"""
        db_mock.query.return_value.filter.return_value.first.return_value = None  # 无重叠配置
        
        result = service.create_delegate(
            user_id=100,
            delegate_id=200,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            scope="ALL",
            reason="出差"
        )
        
        assert result.user_id == 100
        assert result.delegate_id == 200
        assert result.scope == "ALL"
        assert result.is_active is True
        db_mock.add.assert_called_once()
        db_mock.flush.assert_called_once()
    
    def test_create_delegate_with_template_ids(self, service, db_mock):
        """测试创建指定模板的代理"""
        db_mock.query.return_value.filter.return_value.first.return_value = None
        
        result = service.create_delegate(
            user_id=100,
            delegate_id=200,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            scope="TEMPLATE",
            template_ids=[1, 2, 3]
        )
        
        assert result.scope == "TEMPLATE"
        assert result.template_ids == [1, 2, 3]
    
    def test_create_delegate_overlapping_raises_error(self, service, db_mock, sample_delegate_config):
        """测试重叠配置抛出异常"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_delegate_config
        
        with pytest.raises(ValueError, match="存在重叠的代理配置"):
            service.create_delegate(
                user_id=100,
                delegate_id=200,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=7)
            )


class TestUpdateDelegate:
    """测试更新代理配置"""
    
    def test_update_delegate_success(self, service, db_mock, sample_delegate_config):
        """测试成功更新代理"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_delegate_config
        
        result = service.update_delegate(
            delegate_id=1,
            reason="延长出差",
            end_date=date.today() + timedelta(days=14)
        )
        
        assert result.reason == "延长出差"
        assert result.end_date == date.today() + timedelta(days=14)
    
    def test_update_delegate_not_found(self, service, db_mock):
        """测试更新不存在的配置"""
        db_mock.query.return_value.filter.return_value.first.return_value = None
        
        result = service.update_delegate(delegate_id=999, reason="test")
        
        assert result is None
    
    def test_update_delegate_filters_allowed_fields(self, service, db_mock, sample_delegate_config):
        """测试只更新允许的字段"""
        original_id = sample_delegate_config.id
        db_mock.query.return_value.filter.return_value.first.return_value = sample_delegate_config
        
        result = service.update_delegate(
            delegate_id=1,
            id=999,  # 不应该更新
            reason="测试"  # 应该更新
        )
        
        assert result.id == original_id  # ID未变
        assert result.reason == "测试"  # reason已更新


class TestCancelDelegate:
    """测试取消代理配置"""
    
    def test_cancel_delegate_success(self, service, db_mock, sample_delegate_config):
        """测试成功取消代理"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_delegate_config
        
        result = service.cancel_delegate(delegate_id=1)
        
        assert result is True
        assert sample_delegate_config.is_active is False
    
    def test_cancel_delegate_not_found(self, service, db_mock):
        """测试取消不存在的配置"""
        db_mock.query.return_value.filter.return_value.first.return_value = None
        
        result = service.cancel_delegate(delegate_id=999)
        
        assert result is False


class TestGetUserDelegates:
    """测试获取用户的代理配置"""
    
    def test_get_user_delegates_active_only(self, service, db_mock, sample_delegate_config):
        """测试只获取活跃配置"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = [sample_delegate_config]
        db_mock.query.return_value = mock_query
        
        result = service.get_user_delegates(user_id=100, include_inactive=False)
        
        assert len(result) == 1
        assert result[0] == sample_delegate_config
    
    def test_get_user_delegates_include_inactive(self, service, db_mock, sample_delegate_config):
        """测试包含失效配置"""
        inactive_config = MagicMock()
        inactive_config.is_active = False
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = [sample_delegate_config, inactive_config]
        db_mock.query.return_value = mock_query
        
        result = service.get_user_delegates(user_id=100, include_inactive=True)
        
        assert len(result) == 2


class TestGetDelegatedToUser:
    """测试获取用户作为代理人的配置"""
    
    def test_get_delegated_to_user(self, service, db_mock, sample_delegate_config):
        """测试获取代理给我的配置"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = [sample_delegate_config]
        db_mock.query.return_value = mock_query
        
        result = service.get_delegated_to_user(delegate_id=200)
        
        assert len(result) == 1
        assert result[0] == sample_delegate_config


class TestRecordDelegateAction:
    """测试记录代理操作"""
    
    def test_record_delegate_action(self, service, db_mock):
        """测试记录审批操作"""
        log = MagicMock()
        log.id = 1
        log.action = None
        log.action_at = None
        
        db_mock.query.return_value.filter.return_value.first.return_value = log
        
        service.record_delegate_action(delegate_log_id=1, action="APPROVE")
        
        assert log.action == "APPROVE"
        assert log.action_at is not None


class TestNotifyOriginalUser:
    """测试通知原审批人"""
    
    @patch('app.services.approval_engine.delegate.ApprovalNotifyService')
    def test_notify_original_user_success(self, mock_notify_service, service, db_mock):
        """测试成功通知原审批人"""
        # Mock日志
        log = MagicMock()
        log.id = 1
        log.delegate_config_id = 1
        log.task_id = 10
        log.instance_id = 50
        log.action = "APPROVE"
        log.original_notified = False
        log.original_notified_at = None
        
        # Mock配置
        config = MagicMock()
        config.id = 1
        config.user_id = 100
        config.notify_original = True
        
        # Mock任务
        task = MagicMock()
        task.id = 10
        task.instance = MagicMock()
        task.instance.title = "测试审批"
        task.instance.id = 50
        
        db_mock.query.return_value.filter.return_value.first.side_effect = [log, config, task]
        
        service.notify_original_user(delegate_log_id=1)
        
        assert log.original_notified is True
        assert log.original_notified_at is not None
    
    def test_notify_original_user_log_not_found(self, service, db_mock):
        """测试日志不存在"""
        db_mock.query.return_value.filter.return_value.first.return_value = None
        
        # 不应该抛出异常
        service.notify_original_user(delegate_log_id=999)


class TestCleanupExpiredDelegates:
    """测试清理过期配置"""
    
    def test_cleanup_expired_delegates(self, service, db_mock):
        """测试清理过期的代理配置"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.update.return_value = 3  # 3个配置被更新
        db_mock.query.return_value = mock_query
        
        service.cleanup_expired_delegates()
        
        # 验证update被调用
        mock_query.update.assert_called_once_with(
            {"is_active": False},
            synchronize_session=False
        )

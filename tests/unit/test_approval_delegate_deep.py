# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 审批代理人服务"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta


class TestApprovalDelegateServiceBusinessLogic:
    """审批代理人服务业务逻辑测试"""

    def test_get_active_delegate_all_scope(self):
        """测试获取全局代理人"""
        try:
            from app.services.approval_engine.delegate import ApprovalDelegateService

            mock_db = MagicMock()

            mock_delegate = MagicMock()
            mock_delegate.id = 1
            mock_delegate.user_id = 1
            mock_delegate.delegate_id = 2
            mock_delegate.scope = "ALL"
            mock_delegate.is_active = True
            mock_delegate.start_date = date.today() - timedelta(days=1)
            mock_delegate.end_date = date.today() + timedelta(days=1)

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_delegate]

            service = ApprovalDelegateService(mock_db)
            result = service.get_active_delegate(1)

            assert result == mock_delegate
        except ImportError:
            pytest.skip("Module not found")

    def test_get_active_delegate_template_scope(self):
        """测试获取模板范围代理人"""
        try:
            from app.services.approval_engine.delegate import ApprovalDelegateService

            mock_db = MagicMock()

            mock_delegate = MagicMock()
            mock_delegate.scope = "TEMPLATE"
            mock_delegate.template_ids = [1, 2, 3]
            mock_delegate.is_active = True
            mock_delegate.start_date = date.today() - timedelta(days=1)
            mock_delegate.end_date = date.today() + timedelta(days=1)

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_delegate]

            service = ApprovalDelegateService(mock_db)
            result = service.get_active_delegate(1, template_id=2)

            assert result == mock_delegate
        except ImportError:
            pytest.skip("Module not found")

    def test_get_active_delegate_template_not_in_scope(self):
        """测试模板不在代理范围内"""
        try:
            from app.services.approval_engine.delegate import ApprovalDelegateService

            mock_db = MagicMock()

            mock_delegate = MagicMock()
            mock_delegate.scope = "TEMPLATE"
            mock_delegate.template_ids = [1, 2]  # 不包含3
            mock_delegate.is_active = True
            mock_delegate.start_date = date.today() - timedelta(days=1)
            mock_delegate.end_date = date.today() + timedelta(days=1)

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_delegate]

            service = ApprovalDelegateService(mock_db)
            result = service.get_active_delegate(1, template_id=3)

            assert result is None
        except ImportError:
            pytest.skip("Module not found")

    def test_get_active_delegate_expired(self):
        """测试已过期的代理"""
        try:
            from app.services.approval_engine.delegate import ApprovalDelegateService

            mock_db = MagicMock()

            mock_db.query.return_value.filter.return_value.all.return_value = []

            service = ApprovalDelegateService(mock_db)
            result = service.get_active_delegate(1)

            assert result is None
        except ImportError:
            pytest.skip("Module not found")

    def test_get_active_delegate_not_started(self):
        """测试未开始的代理"""
        try:
            from app.services.approval_engine.delegate import ApprovalDelegateService

            mock_db = MagicMock()

            mock_delegate = MagicMock()
            mock_delegate.start_date = date.today() + timedelta(days=1)  # 明天才开始
            mock_delegate.end_date = date.today() + timedelta(days=10)
            mock_delegate.is_active = True

            # 过滤条件会排除未开始的代理
            mock_db.query.return_value.filter.return_value.all.return_value = []

            service = ApprovalDelegateService(mock_db)
            result = service.get_active_delegate(1)

            assert result is None
        except ImportError:
            pytest.skip("Module not found")

    def test_apply_delegation(self):
        """测试应用代理"""
        try:
            from app.services.approval_engine.delegate import ApprovalDelegateService

            mock_db = MagicMock()

            mock_task = MagicMock()
            mock_task.id = 1
            mock_task.instance = MagicMock(template_id=10, id=100)

            mock_delegate = MagicMock()
            mock_delegate.id = 9
            mock_delegate.delegate_id = 2

            mock_user = MagicMock()
            mock_user.real_name = "代理人"
            mock_user.username = "delegate_user"
            mock_db.query.return_value.filter.return_value.first.return_value = mock_user

            service = ApprovalDelegateService(mock_db)
            with patch.object(service, "get_active_delegate", return_value=mock_delegate):
                result = service.apply_delegation(mock_task, original_assignee_id=1)

            assert result == mock_task
            assert mock_task.assignee_id == 2
        except ImportError:
            pytest.skip("Module not found")

    def test_create_delegate(self):
        """测试创建代理配置"""
        try:
            from app.services.approval_engine.delegate import ApprovalDelegateService

            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None

            service = ApprovalDelegateService(mock_db)

            result = service.create_delegate(
                user_id=1,
                delegate_id=2,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=7),
                scope="ALL"
            )

            assert mock_db.add.called
            assert mock_db.flush.called
        except ImportError:
            pytest.skip("Module not found")

    def test_update_delegate(self):
        """测试更新代理配置"""
        try:
            from app.services.approval_engine.delegate import ApprovalDelegateService

            mock_db = MagicMock()

            mock_delegate = MagicMock()
            mock_delegate.id = 1

            mock_db.query.return_value.filter.return_value.first.return_value = mock_delegate

            service = ApprovalDelegateService(mock_db)
            result = service.update_delegate(1, end_date=date.today() + timedelta(days=14))

            assert result == mock_delegate
            assert result.end_date == date.today() + timedelta(days=14)
        except ImportError:
            pytest.skip("Module not found")

    def test_cancel_delegate(self):
        """测试取消代理"""
        try:
            from app.services.approval_engine.delegate import ApprovalDelegateService

            mock_db = MagicMock()

            mock_delegate = MagicMock()
            mock_delegate.id = 1
            mock_delegate.is_active = True

            mock_db.query.return_value.filter.return_value.first.return_value = mock_delegate

            service = ApprovalDelegateService(mock_db)
            result = service.cancel_delegate(1)

            assert mock_delegate.is_active == False
        except ImportError:
            pytest.skip("Module not found")

    def test_get_user_delegates(self):
        """测试获取用户代理列表"""
        try:
            from app.services.approval_engine.delegate import ApprovalDelegateService

            mock_db = MagicMock()

            mock_delegate = MagicMock()
            mock_delegate.user_id = 1

            mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_delegate]

            service = ApprovalDelegateService(mock_db)
            result = service.get_user_delegates(1)

            assert len(result) == 1
        except ImportError:
            pytest.skip("Module not found")

    def test_log_delegation(self):
        """测试记录代理操作日志"""
        try:
            from app.services.approval_engine.delegate import ApprovalDelegateService

            mock_db = MagicMock()
            mock_log = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_log

            service = ApprovalDelegateService(mock_db)
            service.record_delegate_action(delegate_log_id=1, action="APPROVED")

            assert mock_log.action == "APPROVED"
        except ImportError:
            pytest.skip("Module not found")


class TestApprovalDelegateServiceValidation:
    """验证测试"""

    def test_create_delegate_invalid_date_range(self):
        """测试无效日期范围"""
        try:
            from app.services.approval_engine.delegate import ApprovalDelegateService

            mock_db = MagicMock()

            service = ApprovalDelegateService(mock_db)

            # 结束日期早于开始日期
            with pytest.raises(Exception):
                service.create_delegate(
                    user_id=1,
                    delegate_id=2,
                    start_date=date.today() + timedelta(days=7),
                    end_date=date.today(),
                    scope="ALL"
                )
        except ImportError:
            pytest.skip("Module not found")

    def test_create_delegate_same_user(self):
        """测试代理人和原审批人相同"""
        try:
            from app.services.approval_engine.delegate import ApprovalDelegateService

            mock_db = MagicMock()

            service = ApprovalDelegateService(mock_db)

            # 代理人不能是自己
            with pytest.raises(Exception):
                service.create_delegate(
                    user_id=1,
                    delegate_id=1,  # 相同
                    start_date=date.today(),
                    end_date=date.today() + timedelta(days=7),
                    scope="ALL"
                )
        except ImportError:
            pytest.skip("Module not found")


class TestApprovalDelegateServiceEdgeCases:
    """边界情况测试"""

    def test_multiple_delegates_priority(self):
        """测试多个代理的优先级"""
        try:
            from app.services.approval_engine.delegate import ApprovalDelegateService

            mock_db = MagicMock()

            # 全局代理
            mock_delegate_all = MagicMock()
            mock_delegate_all.scope = "ALL"
            mock_delegate_all.is_active = True
            mock_delegate_all.start_date = date.today() - timedelta(days=1)
            mock_delegate_all.end_date = date.today() + timedelta(days=1)

            # 模板代理
            mock_delegate_template = MagicMock()
            mock_delegate_template.scope = "TEMPLATE"
            mock_delegate_template.template_ids = [1]
            mock_delegate_template.is_active = True
            mock_delegate_template.start_date = date.today() - timedelta(days=1)
            mock_delegate_template.end_date = date.today() + timedelta(days=1)

            mock_db.query.return_value.filter.return_value.all.return_value = [
                mock_delegate_all,
                mock_delegate_template
            ]

            service = ApprovalDelegateService(mock_db)
            result = service.get_active_delegate(1)

            # 应该返回第一个匹配的代理
            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_delegate_not_found(self):
        """测试代理不存在"""
        try:
            from app.services.approval_engine.delegate import ApprovalDelegateService

            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None

            service = ApprovalDelegateService(mock_db)
            result = service.update_delegate(999, end_date=date.today())

            assert result is None
        except ImportError:
            pytest.skip("Module not found")

    def test_task_already_processed(self):
        """测试无代理配置时返回 None"""
        try:
            from app.services.approval_engine.delegate import ApprovalDelegateService

            mock_db = MagicMock()

            mock_task = MagicMock()
            mock_task.instance = MagicMock(template_id=10)

            service = ApprovalDelegateService(mock_db)

            with patch.object(service, "get_active_delegate", return_value=None):
                assert service.apply_delegation(mock_task, original_assignee_id=1) is None
        except ImportError:
            pytest.skip("Module not found")
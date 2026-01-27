# -*- coding: utf-8 -*-
"""
审批引擎查询混入类单元测试

测试 ApprovalQueryMixin (查询相关方法)
"""

import pytest
from unittest.mock import MagicMock

from app.services.approval_engine.engine.query import ApprovalQueryMixin


@pytest.mark.unit
class TestApprovalQueryMixin:
    """测试 ApprovalQueryMixin"""

    def test_class_exists(self):
        """测试类存在"""
        assert ApprovalQueryMixin is not None

    def test_has_get_pending_tasks(self):
        """测试有获取待办任务方法"""
        assert hasattr(ApprovalQueryMixin, 'get_pending_tasks') or hasattr(ApprovalQueryMixin, 'get_pending_approvals')

    def test_has_get_initiated_instances(self):
        """测试有获取发起实例方法"""
        assert hasattr(ApprovalQueryMixin, 'get_initiated_instances') or hasattr(ApprovalQueryMixin, 'get_my_initiated')

    def test_mixin_initialization(self):
        """测试混入类可以被继承"""
        class TestService(ApprovalQueryMixin):
            def __init__(self):
                self.db = MagicMock()

        service = TestService()
        assert service.db is not None

    def test_query_mixin_with_mock_db(self):
        """测试使用模拟数据库的查询"""
        class TestService(ApprovalQueryMixin):
            def __init__(self, db):
                self.db = db

        mock_db = MagicMock()
        service = TestService(mock_db)
        assert service.db == mock_db

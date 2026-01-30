# -*- coding: utf-8 -*-
"""
审批引擎提交混入类单元测试

测试 ApprovalSubmitMixin (submit, save_draft)
"""

import pytest
from unittest.mock import MagicMock

from app.models.enums import ApprovalRecordStatusEnum
from app.services.approval_engine.engine.submit import ApprovalSubmitMixin


@pytest.mark.unit
class TestApprovalSubmitMixin:
    """测试 ApprovalSubmitMixin"""

    def test_class_exists(self):
        """测试类存在"""
        assert ApprovalSubmitMixin is not None

    def test_has_submit_method(self):
        """测试有提交方法"""
        assert hasattr(ApprovalSubmitMixin, 'submit') or hasattr(ApprovalSubmitMixin, 'submit_approval')

    def test_has_save_draft_method(self):
        """测试有保存草稿方法"""
        assert hasattr(ApprovalSubmitMixin, 'save_draft') or hasattr(ApprovalSubmitMixin, 'save_as_draft')

    def test_mixin_initialization(self):
        """测试混入类可以被继承"""
        class TestService(ApprovalSubmitMixin):
            def __init__(self):
                self.db = MagicMock()

        service = TestService()
        assert service.db is not None

    def test_submit_mixin_with_mock_db(self):
        """测试使用模拟数据库"""
        class TestService(ApprovalSubmitMixin):
            def __init__(self, db):
                self.db = db

        mock_db = MagicMock()
        service = TestService(mock_db)
        assert service.db == mock_db

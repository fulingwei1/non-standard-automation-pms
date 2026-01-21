# -*- coding: utf-8 -*-
"""
approval_workflow/helpers.py 单元测试

测试审批辅助方法
"""

import pytest
from unittest.mock import MagicMock

from app.services.approval_workflow.helpers import ApprovalHelpersMixin


class TestApprovalHelpersService(ApprovalHelpersMixin):
    """测试用的服务类，继承混入类"""

    def __init__(self, db):
        self.db = db


@pytest.mark.unit
class TestValidateApprover:
    """测试 _validate_approver 方法"""

    def test_validate_superuser(self):
        """测试超级用户"""
        mock_db = MagicMock()
        service = TestApprovalHelpersService(db=mock_db)

        mock_user = MagicMock()
        mock_user.is_active = True
        mock_user.is_superuser = True

        mock_step = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user
        mock_db.query.return_value = mock_query

        result = service._validate_approver(mock_step, 10)

        assert result is True

    def test_validate_designated_approver(self):
        """测试指定审批人"""
        mock_db = MagicMock()
        service = TestApprovalHelpersService(db=mock_db)

        mock_user = MagicMock()
        mock_user.is_active = True
        mock_user.is_superuser = False

        mock_step = MagicMock()
        mock_step.approver_id = 10

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user
        mock_db.query.return_value = mock_query

        result = service._validate_approver(mock_step, 10)

        assert result is True

    def test_validate_role_match(self):
        """测试角色匹配"""
        mock_db = MagicMock()
        service = TestApprovalHelpersService(db=mock_db)

        mock_user = MagicMock()
        mock_user.is_active = True
        mock_user.is_superuser = False

        mock_step = MagicMock()
        mock_step.approver_id = None
        mock_step.approver_role = "APPROVER"

        mock_role = MagicMock()
        mock_role.role_code = "APPROVER"

        mock_user_role = MagicMock()
        mock_user_role.role = mock_role

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_user_role]
        mock_query.first.side_effect = [mock_user, mock_user_role]
        mock_db.query.return_value = mock_query

        result = service._validate_approver(mock_step, 10)

        assert result is True

    def test_validate_delegation(self):
        """测试委托权限"""
        mock_db = MagicMock()
        service = TestApprovalHelpersService(db=mock_db)

        mock_user = MagicMock()
        mock_user.is_active = True
        mock_user.is_superuser = False

        mock_step = MagicMock()
        mock_step.approver_id = 20
        mock_step.step_order = 1

        mock_history = MagicMock()
        mock_history.approver_id = 20
        mock_history.delegate_to_id = 10

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        mock_and_query = MagicMock()
        mock_and_query.first.return_value = mock_history
        mock_and_query.filter.return_value = mock_and_query

        result = service._validate_approver(mock_step, 10)

        assert result is True

    def test_validate_user_not_found(self):
        """测试用户不存在"""
        mock_db = MagicMock()
        service = TestApprovalHelpersService(db=mock_db)

        mock_step = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        result = service._validate_approver(mock_step, 10)

        assert result is False

    def test_validate_user_inactive(self):
        """测试用户未激活"""
        mock_db = MagicMock()
        service = TestApprovalHelpersService(db=mock_db)

        mock_user = MagicMock()
        mock_user.is_active = False
        mock_user.is_superuser = False

        mock_step = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user
        mock_db.query.return_value = mock_query

        result = service._validate_approver(mock_step, 10)

        assert result is False

    def test_validate_no_permission(self):
        """测试无权限"""
        mock_db = MagicMock()
        service = TestApprovalHelpersService(db=mock_db)

        mock_user = MagicMock()
        mock_user.is_active = True
        mock_user.is_superuser = False

        mock_step = MagicMock()
        mock_step.approver_id = 20
        mock_step.approver_role = "MANAGER"

        mock_user_role = MagicMock()
        mock_user_role.role = MagicMock()
        mock_user_role.role.role_code = "USER"

        # Create separate mock queries for each call
        user_query = MagicMock()
        user_query.filter.return_value = user_query
        user_query.first.return_value = mock_user

        user_role_query = MagicMock()
        user_role_query.filter.return_value = user_role_query
        user_role_query.all.return_value = [mock_user_role]

        # Mock delegation history to return None
        delegation_query = MagicMock()
        delegation_query.filter.return_value = delegation_query
        delegation_query.first.return_value = None

        mock_db.query.side_effect = [user_query, user_role_query, delegation_query]

        result = service._validate_approver(mock_step, 10)

        assert result is False

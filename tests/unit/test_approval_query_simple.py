# -*- coding: utf-8 -*-
"""
approval_engine/engine/query.py 单元测试

测试审批查询功能
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestApprovalQueryMixin:
    """测试 ApprovalQueryMixin 查询方法"""

    def test_get_pending_tasks_basic(self):
        """测试获取待审批任务基本功能"""
        from app.services.approval_engine.engine.query import ApprovalQueryMixin

        mock_db = MagicMock()
        mock_core = MagicMock()
        mock_core.db = mock_db

        mixin = ApprovalQueryMixin(mock_core)

        mock_tasks = [MagicMock(id=1), MagicMock(id=2)]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_tasks

        mock_db.query.return_value = mock_query

        result = mixin.get_pending_tasks(user_id=100, page=1, page_size=20)

        assert result["total"] == 2
        assert result["page"] == 1
        assert result["items"] == mock_tasks

    def test_get_initiated_instances_with_status(self):
        """测试获取指定状态的发起审批"""
        from app.services.approval_engine.engine.query import ApprovalQueryMixin

        mock_db = MagicMock()
        mock_core = MagicMock()
        mock_core.db = mock_db

        mixin = ApprovalQueryMixin(mock_core)

        mock_instances = [MagicMock(id=1), MagicMock(id=2)]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.offset.return_value.limit.return_value.all.return_value = (
        mock_instances
        )

        mock_db.query.return_value = mock_query

        result = mixin.get_initiated_instances(
        user_id=100, status="PENDING", page=1, page_size=20
        )

        assert result["total"] == 5
        assert len(result["items"]) == 2

    def test_get_cc_records_unread_only(self):
        """测试获取未读抄送记录"""
        from app.services.approval_engine.engine.query import ApprovalQueryMixin

        mock_db = MagicMock()
        mock_core = MagicMock()
        mock_core.db = mock_db

        mixin = ApprovalQueryMixin(mock_core)

        mock_records = [MagicMock(id=1)]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value.limit.return_value.all.return_value = (
        mock_records
        )

        mock_db.query.return_value = mock_query

        result = mixin.get_cc_records(user_id=100, is_read=False, page=1)

        assert result["total"] == 1
        assert len(result["items"]) == 1

    def test_mark_cc_as_read_success(self):
        """测试成功标记抄送为已读"""
        from app.services.approval_engine.engine.query import ApprovalQueryMixin

        mock_db = MagicMock()
        mock_core = MagicMock()
        mock_core.db = mock_db

        mixin = ApprovalQueryMixin(mock_core)

        mock_cc = MagicMock()
        mock_cc.id = 100
        mock_cc.instance_id = 200
        mock_cc.is_read = False

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_cc
        mock_db.query.return_value = mock_query

        mock_log_action = MagicMock()

        with patch.object(mixin, "_log_action", mock_log_action):
            result = mixin.mark_cc_as_read(cc_id=100, user_id=100)

            assert result is True
            assert mock_cc.is_read is True
            assert isinstance(mock_cc.read_at, datetime)
            mock_log_action.assert_called_once()
            mock_db.commit.assert_called_once()

    def test_mark_cc_as_read_not_found(self):
        """测试抄送记录不存在"""
        from app.services.approval_engine.engine.query import ApprovalQueryMixin

        mock_db = MagicMock()
        mock_core = MagicMock()
        mock_core.db = mock_db

        mixin = ApprovalQueryMixin(mock_core)

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = mixin.mark_cc_as_read(cc_id=999, user_id=100)

        assert result is False

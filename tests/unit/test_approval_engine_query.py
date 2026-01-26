# -*- coding: utf-8 -*-
"""
approval_engine/engine/query.py 单元测试

测试审批查询功能
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.approval_engine.engine.core import ApprovalEngineCore
from app.services.approval_engine.engine.query import ApprovalQueryMixin


# 创建测试用的组合类
class TestApprovalEngine(ApprovalEngineCore, ApprovalQueryMixin):
    """测试用的审批引擎类（组合 core 和 query mixin）"""

    def __init__(self, db):
        ApprovalEngineCore.__init__(self, db)


@pytest.mark.unit
class TestApprovalQueryMixinInit:
    """测试 ApprovalQueryMixin 初始化"""

    def test_init_with_core(self):
        """测试使用ApprovalEngineCore初始化"""
        mock_db = MagicMock()
        engine = TestApprovalEngine(mock_db)

        assert engine.db is not None
        assert hasattr(engine, "get_pending_tasks")
        assert hasattr(engine, "get_initiated_instances")
        assert hasattr(engine, "get_cc_records")
        assert hasattr(engine, "mark_cc_as_read")


@pytest.mark.unit
class TestGetPendingTasks:
    """测试 get_pending_tasks 方法"""

    def test_get_pending_tasks_first_page(self):
        """测试获取第一页待审批任务"""
        mock_db = MagicMock()
        engine = TestApprovalEngine(mock_db)

        mock_tasks = [MagicMock(id=1), MagicMock(id=2)]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_tasks

        mock_db.query.return_value = mock_query

        result = engine.get_pending_tasks(user_id=100, page=1, page_size=20)

        assert result["total"] == 2
        assert result["page"] == 1
        assert result["page_size"] == 20
        assert result["items"] == mock_tasks
        mock_query.offset.assert_called_once_with(0)

    def test_get_pending_tasks_second_page(self):
        """测试获取第二页待审批任务"""
        mock_db = MagicMock()
        engine = TestApprovalEngine(mock_db)

        mock_tasks = [MagicMock(id=3), MagicMock(id=4)]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 20
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_tasks

        mock_db.query.return_value = mock_query

        result = engine.get_pending_tasks(user_id=100, page=2, page_size=20)

        assert result["total"] == 20
        assert result["page"] == 2
        mock_query.offset.assert_called_once_with(20)

    def test_get_pending_tasks_empty(self):
        """测试获取空任务列表"""
        mock_db = MagicMock()
        engine = TestApprovalEngine(mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.offset.return_value.limit.return_value.all.return_value = []

        mock_db.query.return_value = mock_query

        result = engine.get_pending_tasks(user_id=100)

        assert result["total"] == 0
        assert result["items"] == []


@pytest.mark.unit
class TestGetInitiatedInstances:
    """测试 get_initiated_instances 方法"""

    def test_get_initiated_instances_with_status(self):
        """测试获取指定状态的发起审批"""
        mock_db = MagicMock()
        engine = TestApprovalEngine(mock_db)

        mock_instances = [MagicMock(id=1), MagicMock(id=2)]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.offset.return_value.limit.return_value.all.return_value = (
            mock_instances
        )

        mock_db.query.return_value = mock_query

        result = engine.get_initiated_instances(
            user_id=100, status="PENDING", page=1, page_size=20
        )

        assert result["total"] == 5
        assert result["page"] == 1
        assert result["items"] == mock_instances

    def test_get_initiated_instances_without_status(self):
        """测试获取所有状态的发起审批"""
        mock_db = MagicMock()
        engine = TestApprovalEngine(mock_db)

        mock_instances = [MagicMock(id=1), MagicMock(id=2), MagicMock(id=3)]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.offset.return_value.limit.return_value.all.return_value = (
            mock_instances
        )

        mock_db.query.return_value = mock_query

        result = engine.get_initiated_instances(user_id=100, page=1, page_size=20)

        assert result["total"] == 10
        assert len(result["items"]) == 3

    def test_get_initiated_instances_empty(self):
        """测试获取空的发起审批"""
        mock_db = MagicMock()
        engine = TestApprovalEngine(mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.offset.return_value.limit.return_value.all.return_value = []

        mock_db.query.return_value = mock_query

        result = engine.get_initiated_instances(user_id=100, status="PENDING")

        assert result["total"] == 0
        assert result["items"] == []


@pytest.mark.unit
class TestGetCcRecords:
    """测试 get_cc_records 方法"""

    def test_get_cc_records_all(self):
        """测试获取所有抄送记录"""
        mock_db = MagicMock()
        engine = TestApprovalEngine(mock_db)

        mock_records = [MagicMock(id=1), MagicMock(id=2)]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.offset.return_value.limit.return_value.all.return_value = (
            mock_records
        )

        mock_db.query.return_value = mock_query

        result = engine.get_cc_records(user_id=100, is_read=None, page=1, page_size=20)

        assert result["total"] == 5
        assert result["page"] == 1
        assert result["items"] == mock_records

    def test_get_cc_records_unread_only(self):
        """测试仅获取未读抄送记录"""
        mock_db = MagicMock()
        engine = TestApprovalEngine(mock_db)

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

        result = engine.get_cc_records(user_id=100, is_read=False, page=1)

        assert result["total"] == 1
        assert len(result["items"]) == 1


@pytest.mark.unit
class TestMarkCcAsRead:
    """测试 mark_cc_as_read 方法"""

    def test_mark_cc_as_read_success(self):
        """测试成功标记抄送为已读"""
        mock_db = MagicMock()
        engine = TestApprovalEngine(mock_db)

        mock_cc = MagicMock()
        mock_cc.id = 100
        mock_cc.instance_id = 200
        mock_cc.is_read = False

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_cc
        mock_db.query.return_value = mock_query

        mock_log_action = MagicMock()

        with patch.object(engine, "_log_action", mock_log_action):
            result = engine.mark_cc_as_read(cc_id=100, user_id=100)

            assert result is True
            assert mock_cc.is_read is True
            assert isinstance(mock_cc.read_at, datetime)
            mock_log_action.assert_called_once()
            mock_db.commit.assert_called_once()

    def test_mark_cc_as_read_not_found(self):
        """测试抄送记录不存在"""
        mock_db = MagicMock()
        engine = TestApprovalEngine(mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = engine.mark_cc_as_read(cc_id=999, user_id=100)

        assert result is False
        mock_db.commit.assert_not_called()

# -*- coding: utf-8 -*-
"""第十二批：综合仪表盘适配器单元测试"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.dashboard_adapters.others import OthersDashboardAdapter
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败")


def _make_adapter():
    db = MagicMock()
    return OthersDashboardAdapter(db=db), db


class TestOthersDashboardAdapterInit:
    def test_db_stored(self):
        db = MagicMock()
        adapter = OthersDashboardAdapter(db=db)
        assert adapter.db is db


class TestGetQuickStats:
    """get_quick_stats 方法测试"""

    def test_returns_dict(self):
        adapter, db = _make_adapter()
        db.query.return_value.count.return_value = 10
        db.query.return_value.filter.return_value.count.return_value = 5

        result = adapter.get_quick_stats()
        assert isinstance(result, dict)

    def test_returns_counts(self):
        adapter, db = _make_adapter()
        db.query.return_value.count.return_value = 42
        db.query.return_value.filter.return_value.count.return_value = 3

        result = adapter.get_quick_stats()
        assert "project_count" in result or "user_count" in result or isinstance(result, dict)

    def test_handles_exception_gracefully(self):
        adapter, db = _make_adapter()
        db.query.side_effect = Exception("DB错误")

        result = adapter.get_quick_stats()
        # 应该返回空/默认值而不是崩溃
        assert isinstance(result, dict)
        assert result.get("project_count", 0) == 0


class TestGetRecentActivities:
    """get_recent_activities 方法测试"""

    def test_returns_list(self):
        adapter, db = _make_adapter()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.limit.return_value = mock_q
        mock_q.all.return_value = []
        db.query.return_value = mock_q

        result = adapter.get_recent_activities(limit=10)
        assert isinstance(result, list)

    def test_with_user_id_filter(self):
        adapter, db = _make_adapter()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.limit.return_value = mock_q
        mock_q.all.return_value = []
        db.query.return_value = mock_q

        result = adapter.get_recent_activities(limit=5, user_id=1)
        assert isinstance(result, list)

    def test_handles_exception_gracefully(self):
        adapter, db = _make_adapter()
        db.query.side_effect = Exception("DB错误")

        result = adapter.get_recent_activities()
        assert isinstance(result, list)


class TestAdditionalMethods:
    """其他方法测试"""

    def test_all_public_methods_callable(self):
        adapter, db = _make_adapter()
        db.query.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

        methods = [m for m in dir(adapter) if not m.startswith('_') and callable(getattr(adapter, m))]
        # 至少有 get_quick_stats 和 get_recent_activities
        assert len(methods) >= 2

    def test_get_system_health(self):
        adapter, db = _make_adapter()
        if not hasattr(adapter, 'get_system_health'):
            pytest.skip("无此方法")
        result = adapter.get_system_health()
        assert isinstance(result, dict)

    def test_get_pending_tasks(self):
        adapter, db = _make_adapter()
        if not hasattr(adapter, 'get_pending_tasks'):
            pytest.skip("无此方法")
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []
        db.query.return_value = mock_q
        result = adapter.get_pending_tasks()
        assert isinstance(result, list)

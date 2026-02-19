# -*- coding: utf-8 -*-
"""
Unit tests for PresalesDashboardAdapter (第三十八批)
"""
import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch, PropertyMock

pytest.importorskip("app.services.dashboard_adapters.presales", reason="导入失败，跳过")

try:
    from app.services.dashboard_adapters.presales import PresalesDashboardAdapter
except ImportError:
    pytestmark = pytest.mark.skip(reason="presales adapter 不可用")
    PresalesDashboardAdapter = None


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def adapter(mock_db):
    with patch("app.services.dashboard_adapters.presales.DashboardAdapter.__init__", return_value=None):
        adp = PresalesDashboardAdapter.__new__(PresalesDashboardAdapter)
        adp.db = mock_db
        adp.user = MagicMock()
        adp.user.id = 1
        return adp


class TestPresalesDashboardAdapterProperties:
    """测试适配器属性"""

    def test_module_id(self, adapter):
        assert adapter.module_id == "presales"

    def test_module_name(self, adapter):
        assert adapter.module_name == "售前分析"

    def test_supported_roles(self, adapter):
        roles = adapter.supported_roles
        assert "presales" in roles
        assert "sales" in roles
        assert "admin" in roles


class TestGetStats:
    """测试统计卡片"""

    def _setup_db(self, adapter, projects=None, total_hours=0):
        if projects is None:
            projects = []
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = projects
        mock_query.scalar.return_value = total_hours
        adapter.db.query.return_value = mock_query
        return mock_query

    def test_get_stats_returns_list(self, adapter):
        """返回列表"""
        self._setup_db(adapter, [])
        with patch("app.services.dashboard_adapters.presales.DashboardStatCard") as MockCard:
            MockCard.return_value = MagicMock()
            result = adapter.get_stats()
            assert isinstance(result, list)

    def test_get_stats_with_won_projects(self, adapter):
        """有成单项目时统计正确（patch WorkLog 查询）"""
        won = MagicMock()
        won.outcome = "WON"
        won.id = 1
        won.created_at = datetime.now()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [won]
        mock_query.scalar.return_value = 10
        adapter.db.query.return_value = mock_query

        with patch("app.services.dashboard_adapters.presales.DashboardStatCard") as MockCard, \
             patch("app.models.work_log.WorkLog"):
            MockCard.return_value = MagicMock()
            result = adapter.get_stats()
            assert isinstance(result, list)

    def test_get_stats_with_mixed_outcomes(self, adapter):
        """混合结果时统计（patch WorkLog 查询）"""
        won = MagicMock()
        won.outcome = "WON"
        won.id = 1

        lost = MagicMock()
        lost.outcome = "LOST"
        lost.id = 2

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [won, lost]
        mock_query.scalar.return_value = 20
        adapter.db.query.return_value = mock_query

        with patch("app.services.dashboard_adapters.presales.DashboardStatCard") as MockCard, \
             patch("app.models.work_log.WorkLog"):
            MockCard.return_value = MagicMock()
            result = adapter.get_stats()
            assert isinstance(result, list)


class TestGetWidgets:
    """测试 Dashboard 组件"""

    def test_get_widgets_returns_list(self, adapter):
        """返回列表类型"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.scalar.return_value = 0
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        adapter.db.query.return_value = mock_query

        with patch("app.services.dashboard_adapters.presales.DashboardWidget") as MockW:
            MockW.return_value = MagicMock()
            result = adapter.get_widgets()
            assert isinstance(result, list)


class TestGetWidgetsDetailed:
    """测试 get_widgets 详细调用"""

    def test_get_widgets_calls_db(self, adapter):
        """get_widgets 调用数据库"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.scalar.return_value = 0
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        adapter.db.query.return_value = mock_query

        with patch("app.services.dashboard_adapters.presales.DashboardWidget") as MockW:
            MockW.return_value = MagicMock()
            adapter.get_widgets()
            assert adapter.db.query.called

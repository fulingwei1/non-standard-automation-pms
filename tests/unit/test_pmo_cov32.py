# -*- coding: utf-8 -*-
"""
第三十二批覆盖率测试 - PMO Dashboard 适配器
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.dashboard_adapters.pmo import PmoDashboardAdapter
    HAS_PMO = True
except Exception:
    HAS_PMO = False

pytestmark = pytest.mark.skipif(not HAS_PMO, reason="pmo 导入失败")


def make_adapter():
    db = MagicMock()
    user = MagicMock()
    user.id = 1
    adapter = PmoDashboardAdapter.__new__(PmoDashboardAdapter)
    adapter.db = db
    adapter.current_user = user
    return adapter, db


class TestPmoDashboardAdapterProperties:
    def test_module_id(self):
        adapter, _ = make_adapter()
        assert adapter.module_id == "pmo"

    def test_module_name(self):
        adapter, _ = make_adapter()
        assert adapter.module_name == "项目管理办公室"

    def test_supported_roles(self):
        adapter, _ = make_adapter()
        roles = adapter.supported_roles
        assert "pmo" in roles
        assert "admin" in roles

    def test_supported_roles_type(self):
        adapter, _ = make_adapter()
        roles = adapter.supported_roles
        assert isinstance(roles, list)


class TestPmoDashboardAdapterGetStats:
    @patch("app.services.data_scope_service.DataScopeService")
    @patch("app.services.dashboard_adapters.pmo.DashboardStatCard")
    def test_get_stats_empty_projects(self, MockCard, mock_dss):
        """无项目时应生成5个统计卡片"""
        adapter, db = make_adapter()
        mock_dss.apply_data_scope.return_value = db.query.return_value.filter.return_value
        db.query.return_value.filter.return_value.all.return_value = []
        MockCard.return_value = MagicMock()

        result = adapter.get_stats()
        assert isinstance(result, list)
        assert len(result) == 5

    @patch("app.services.data_scope_service.DataScopeService")
    @patch("app.services.dashboard_adapters.pmo.DashboardStatCard")
    def test_get_stats_counts_health_h1(self, MockCard, mock_dss):
        """H1健康度项目正确统计"""
        adapter, db = make_adapter()

        projects = []
        for health in ["H1", "H1", "H2", "H3", "H4"]:
            p = MagicMock()
            p.health = health
            p.is_active = True
            projects.append(p)

        mock_dss.apply_data_scope.return_value = db.query.return_value.filter.return_value
        db.query.return_value.filter.return_value.all.return_value = projects

        # Capture keyword args used to create DashboardStatCard
        created_cards = []
        MockCard.side_effect = lambda **kw: created_cards.append(kw) or MagicMock()

        adapter.get_stats()

        # 总数应为5
        total_kw = next((c for c in created_cards if c.get("key") == "active_projects"), None)
        assert total_kw is not None
        assert total_kw["value"] == 5

    @patch("app.services.data_scope_service.DataScopeService")
    @patch("app.services.dashboard_adapters.pmo.DashboardStatCard")
    def test_get_stats_at_risk_count(self, MockCard, mock_dss):
        """H2风险项目正确统计"""
        adapter, db = make_adapter()

        projects = [MagicMock(health="H2"), MagicMock(health="H2"), MagicMock(health="H1")]
        mock_dss.apply_data_scope.return_value = db.query.return_value.filter.return_value
        db.query.return_value.filter.return_value.all.return_value = projects

        created_cards = []
        MockCard.side_effect = lambda **kw: created_cards.append(kw) or MagicMock()

        adapter.get_stats()

        at_risk_kw = next((c for c in created_cards if c.get("key") == "at_risk"), None)
        assert at_risk_kw is not None
        assert at_risk_kw["value"] == 2

    @patch("app.services.data_scope_service.DataScopeService")
    @patch("app.services.dashboard_adapters.pmo.DashboardStatCard")
    def test_get_stats_delayed_count(self, MockCard, mock_dss):
        """H3延期项目正确统计"""
        adapter, db = make_adapter()

        projects = [MagicMock(health="H3")]
        mock_dss.apply_data_scope.return_value = db.query.return_value.filter.return_value
        db.query.return_value.filter.return_value.all.return_value = projects

        created_cards = []
        MockCard.side_effect = lambda **kw: created_cards.append(kw) or MagicMock()

        adapter.get_stats()

        delayed_kw = next((c for c in created_cards if c.get("key") == "delayed"), None)
        assert delayed_kw is not None
        assert delayed_kw["value"] == 1


class TestPmoDashboardAdapterGetWidgets:
    @patch("app.services.data_scope_service.DataScopeService")
    @patch("app.services.dashboard_adapters.pmo.DashboardWidget")
    def test_get_widgets_returns_list(self, MockWidget, mock_dss):
        adapter, db = make_adapter()
        mock_widget = MagicMock()
        MockWidget.return_value = mock_widget
        mock_dss.apply_data_scope.return_value = db.query.return_value.filter.return_value
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = []

        result = adapter.get_widgets()
        assert isinstance(result, list)
        assert len(result) == 1

    @patch("app.services.data_scope_service.DataScopeService")
    @patch("app.services.dashboard_adapters.pmo.DashboardWidget")
    def test_get_widgets_passes_risk_project_data(self, MockWidget, mock_dss):
        """风险项目数据传入Widget"""
        adapter, db = make_adapter()
        p = MagicMock()
        p.id = 10
        p.project_code = "PRJ-001"
        p.project_name = "测试项目"
        p.health = "H2"
        p.current_stage = "S3"

        mock_dss.apply_data_scope.return_value = db.query.return_value.filter.return_value
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = [p]

        captured = {}
        MockWidget.side_effect = lambda **kw: captured.update(kw) or MagicMock()

        adapter.get_widgets()
        assert "data" in captured
        assert len(captured["data"]) == 1
        assert captured["data"][0]["project_code"] == "PRJ-001"


class TestPmoDashboardAdapterGetDetailedData:
    @patch("app.services.data_scope_service.DataScopeService")
    @patch("app.services.dashboard_adapters.pmo.DashboardStatCard")
    @patch("app.services.dashboard_adapters.pmo.DetailedDashboardResponse")
    def test_get_detailed_data_calls_get_stats(self, MockResponse, MockCard, mock_dss):
        """get_detailed_data 调用 get_stats"""
        adapter, db = make_adapter()
        mock_dss.apply_data_scope.return_value = db.query.return_value.filter.return_value
        db.query.return_value.filter.return_value.all.return_value = []
        MockCard.return_value = MagicMock(key="active_projects", value=0)
        MockResponse.return_value = MagicMock(module="pmo", details={"by_stage": []})

        with patch.object(adapter, "get_stats", return_value=[]) as mock_stats:
            result = adapter.get_detailed_data()
        mock_stats.assert_called_once()

    @patch("app.services.data_scope_service.DataScopeService")
    @patch("app.services.dashboard_adapters.pmo.DashboardStatCard")
    @patch("app.services.dashboard_adapters.pmo.DetailedDashboardResponse")
    def test_get_detailed_data_groups_by_stage(self, MockResponse, MockCard, mock_dss):
        """get_detailed_data 按阶段分组项目"""
        adapter, db = make_adapter()
        stages = ["S1", "S1", "S2"]
        projects = [MagicMock(health="H1", current_stage=s) for s in stages]

        mock_dss.apply_data_scope.return_value = db.query.return_value.filter.return_value
        db.query.return_value.filter.return_value.all.return_value = projects

        MockCard.return_value = MagicMock(key="active_projects", value=3)

        # Capture what's passed to DetailedDashboardResponse
        captured = {}
        MockResponse.side_effect = lambda **kw: captured.update(kw) or MagicMock()

        with patch.object(adapter, "get_stats", return_value=[MockCard.return_value]):
            adapter.get_detailed_data()

        # by_stage should be grouped
        by_stage = captured.get("details", {}).get("by_stage", [])
        total = sum(item["count"] for item in by_stage)
        assert total == 3

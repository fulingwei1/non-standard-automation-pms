# -*- coding: utf-8 -*-
"""
售前分析 Dashboard 适配器单元测试
"""

import unittest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, Mock

from app.models.enums import LeadOutcomeEnum
from app.schemas.dashboard import (
    DashboardStatCard,
    DashboardWidget,
    DetailedDashboardResponse,
)
from app.services.dashboard.adapters.presales import PresalesDashboardAdapter


class TestPresalesDashboardAdapterProperties(unittest.TestCase):
    """测试适配器基本属性"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.adapter = PresalesDashboardAdapter(self.mock_db, self.mock_user)

    def test_module_id(self):
        self.assertEqual(self.adapter.module_id, "presales")

    def test_module_name(self):
        self.assertEqual(self.adapter.module_name, "售前分析")

    def test_supported_roles(self):
        roles = self.adapter.supported_roles
        self.assertIsInstance(roles, list)
        self.assertIn("presales", roles)
        self.assertIn("sales", roles)
        self.assertIn("admin", roles)
        self.assertEqual(len(roles), 3)


class TestPresalesDashboardAdapterGetStats(unittest.TestCase):
    """测试 get_stats() 方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.adapter = PresalesDashboardAdapter(self.mock_db, self.mock_user)
        self.today = date.today()
        self.year_start = date(self.today.year, 1, 1)

    def _create_mock_project(self, outcome, loss_reason=None, created_at=None):
        project = Mock()
        project.id = 1
        project.outcome = outcome
        project.loss_reason = loss_reason
        project.created_at = created_at or datetime.now()
        return project

    def test_get_stats_empty_data(self):
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query

        stats = self.adapter.get_stats()

        self.assertEqual(len(stats), 6)
        self.assertIsInstance(stats[0], DashboardStatCard)

        stats_dict = {card.key: card for card in stats}
        self.assertEqual(stats_dict["total_leads_ytd"].value, 0)
        self.assertEqual(stats_dict["won_leads_ytd"].value, 0)
        self.assertEqual(stats_dict["overall_win_rate"].value, "0.0%")
        self.assertEqual(stats_dict["avg_investment"].value, "0.0")
        self.assertEqual(stats_dict["waste_rate"].value, "0.0%")

    def test_get_stats_with_won_and_lost_projects(self):
        projects = [
            self._create_mock_project(LeadOutcomeEnum.WON.value),
            self._create_mock_project(LeadOutcomeEnum.WON.value),
            self._create_mock_project(LeadOutcomeEnum.LOST.value, loss_reason="PRICE"),
            self._create_mock_project(LeadOutcomeEnum.LOST.value, loss_reason="COMPETITOR"),
        ]

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 10

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        stats = self.adapter.get_stats()
        stats_dict = {card.key: card for card in stats}

        self.assertEqual(stats_dict["total_leads_ytd"].value, 4)
        self.assertEqual(stats_dict["won_leads_ytd"].value, 2)
        self.assertEqual(stats_dict["overall_win_rate"].value, "50.0%")
        self.assertEqual(stats_dict["avg_investment"].value, "10.0")
        self.assertEqual(stats_dict["waste_rate"].value, "50.0%")

    def test_get_stats_with_abandoned_projects(self):
        projects = [
            self._create_mock_project(LeadOutcomeEnum.WON.value),
            self._create_mock_project(LeadOutcomeEnum.LOST.value),
            self._create_mock_project(LeadOutcomeEnum.ABANDONED.value),
        ]

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 10

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        stats = self.adapter.get_stats()
        stats_dict = {card.key: card for card in stats}

        self.assertEqual(stats_dict["waste_rate"].value, "66.7%")

    def test_get_stats_wasted_cost_calculation(self):
        projects = [
            self._create_mock_project(LeadOutcomeEnum.LOST.value),
        ]

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 100

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        stats = self.adapter.get_stats()
        stats_dict = {card.key: card for card in stats}

        wasted_cost = stats_dict["wasted_cost"].value
        self.assertIn("30,000", wasted_cost)
        self.assertIn("¥", wasted_cost)

    def test_get_stats_zero_hours_projects(self):
        projects = [
            self._create_mock_project(LeadOutcomeEnum.WON.value),
            self._create_mock_project(LeadOutcomeEnum.LOST.value),
        ]

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = None

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        stats = self.adapter.get_stats()
        stats_dict = {card.key: card for card in stats}

        self.assertEqual(stats_dict["avg_investment"].value, "0.0")
        self.assertEqual(stats_dict["waste_rate"].value, "0.0%")

    def test_get_stats_only_won_projects(self):
        projects = [
            self._create_mock_project(LeadOutcomeEnum.WON.value),
            self._create_mock_project(LeadOutcomeEnum.WON.value),
            self._create_mock_project(LeadOutcomeEnum.WON.value),
        ]

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 10

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        stats = self.adapter.get_stats()
        stats_dict = {card.key: card for card in stats}

        self.assertEqual(stats_dict["overall_win_rate"].value, "100.0%")
        self.assertEqual(stats_dict["waste_rate"].value, "0.0%")
        self.assertEqual(stats_dict["wasted_cost"].value, "¥0")

    def test_get_stats_card_structure(self):
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query

        stats = self.adapter.get_stats()

        for card in stats:
            self.assertIsNotNone(card.key)
            self.assertIsNotNone(card.label)
            self.assertIsNotNone(card.value)
            self.assertIsNotNone(card.icon)
            self.assertIsNotNone(card.color)

        keys = [card.key for card in stats]
        expected_keys = [
            "total_leads_ytd",
            "won_leads_ytd",
            "overall_win_rate",
            "avg_investment",
            "waste_rate",
            "wasted_cost",
        ]
        for key in expected_keys:
            self.assertIn(key, keys)


class TestPresalesDashboardAdapterGetWidgets(unittest.TestCase):
    """测试 get_widgets() 方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.adapter = PresalesDashboardAdapter(self.mock_db, self.mock_user)
        self.today = date.today()

    def _create_mock_project(self, outcome, loss_reason=None, created_at=None):
        project = Mock()
        project.id = 1
        project.outcome = outcome
        project.loss_reason = loss_reason
        project.created_at = created_at or datetime.now()
        return project

    def test_get_widgets_empty_data(self):
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query

        widgets = self.adapter.get_widgets()

        self.assertEqual(len(widgets), 2)
        self.assertIsInstance(widgets[0], DashboardWidget)

        widget_ids = [w.widget_id for w in widgets]
        self.assertIn("loss_reasons", widget_ids)
        self.assertIn("monthly_trend", widget_ids)

    def test_get_widgets_loss_reasons_distribution(self):
        projects = [
            self._create_mock_project(LeadOutcomeEnum.LOST.value, loss_reason="PRICE"),
            self._create_mock_project(LeadOutcomeEnum.LOST.value, loss_reason="PRICE"),
            self._create_mock_project(LeadOutcomeEnum.LOST.value, loss_reason="COMPETITOR"),
            self._create_mock_project(LeadOutcomeEnum.ABANDONED.value, loss_reason="TIMING"),
            self._create_mock_project(LeadOutcomeEnum.WON.value),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = projects
        self.mock_db.query.return_value = mock_query

        widgets = self.adapter.get_widgets()
        loss_widget = next(w for w in widgets if w.widget_id == "loss_reasons")

        self.assertEqual(loss_widget.data["PRICE"], 2)
        self.assertEqual(loss_widget.data["COMPETITOR"], 1)
        self.assertEqual(loss_widget.data["TIMING"], 1)
        self.assertNotIn("WON", loss_widget.data)

    def test_get_widgets_loss_reasons_with_none(self):
        projects = [
            self._create_mock_project(LeadOutcomeEnum.LOST.value, loss_reason=None),
            self._create_mock_project(LeadOutcomeEnum.LOST.value, loss_reason="PRICE"),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = projects
        self.mock_db.query.return_value = mock_query

        widgets = self.adapter.get_widgets()
        loss_widget = next(w for w in widgets if w.widget_id == "loss_reasons")

        self.assertEqual(loss_widget.data["OTHER"], 1)
        self.assertEqual(loss_widget.data["PRICE"], 1)

    def test_get_widgets_monthly_trend(self):
        now = datetime.now()

        projects = [
            self._create_mock_project(LeadOutcomeEnum.WON.value, created_at=now),
            self._create_mock_project(LeadOutcomeEnum.LOST.value, created_at=now),
            self._create_mock_project(
                LeadOutcomeEnum.WON.value,
                created_at=now - timedelta(days=35),
            ),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = projects
        self.mock_db.query.return_value = mock_query

        widgets = self.adapter.get_widgets()
        trend_widget = next(w for w in widgets if w.widget_id == "monthly_trend")

        self.assertEqual(len(trend_widget.data), 6)

        for month_data in trend_widget.data:
            self.assertIn("month", month_data)
            self.assertIn("total", month_data)
            self.assertIn("won", month_data)
            self.assertIn("lost", month_data)
            self.assertIn("win_rate", month_data)

    def test_get_widgets_monthly_trend_win_rate_calculation(self):
        now = datetime.now()

        projects = [
            self._create_mock_project(LeadOutcomeEnum.WON.value, created_at=now),
            self._create_mock_project(LeadOutcomeEnum.WON.value, created_at=now),
            self._create_mock_project(LeadOutcomeEnum.LOST.value, created_at=now),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = projects
        self.mock_db.query.return_value = mock_query

        widgets = self.adapter.get_widgets()
        trend_widget = next(w for w in widgets if w.widget_id == "monthly_trend")

        current_month_key = now.strftime("%Y-%m")
        current_month_data = next(m for m in trend_widget.data if m["month"] == current_month_key)

        self.assertEqual(current_month_data["total"], 3)
        self.assertEqual(current_month_data["won"], 2)
        self.assertEqual(current_month_data["lost"], 1)
        self.assertAlmostEqual(current_month_data["win_rate"], 0.667, places=3)

    def test_get_widgets_monthly_trend_zero_projects(self):
        old_date = datetime.now() - timedelta(days=365)
        projects = [
            self._create_mock_project(LeadOutcomeEnum.WON.value, created_at=old_date),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = projects
        self.mock_db.query.return_value = mock_query

        widgets = self.adapter.get_widgets()
        trend_widget = next(w for w in widgets if w.widget_id == "monthly_trend")

        for month_data in trend_widget.data:
            if month_data["total"] == 0:
                self.assertEqual(month_data["won"], 0)
                self.assertEqual(month_data["lost"], 0)
                self.assertEqual(month_data["win_rate"], 0)

    def test_get_widgets_structure(self):
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query

        widgets = self.adapter.get_widgets()

        for widget in widgets:
            self.assertIsNotNone(widget.widget_id)
            self.assertIsNotNone(widget.widget_type)
            self.assertIsNotNone(widget.title)
            self.assertIsNotNone(widget.data)
            self.assertIsNotNone(widget.order)
            self.assertIsNotNone(widget.span)

        for widget in widgets:
            self.assertEqual(widget.widget_type, "chart")


class TestPresalesDashboardAdapterGetDetailedData(unittest.TestCase):
    """测试 get_detailed_data() 方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.adapter = PresalesDashboardAdapter(self.mock_db, self.mock_user)

    def _create_mock_project(self, outcome, created_at=None):
        project = Mock()
        project.id = 1
        project.outcome = outcome
        project.loss_reason = None
        project.created_at = created_at or datetime.now()
        return project

    def test_get_detailed_data_structure(self):
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = []

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 0

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        result = self.adapter.get_detailed_data()

        self.assertIsInstance(result, DetailedDashboardResponse)
        self.assertEqual(result.module, "presales")
        self.assertEqual(result.module_name, "售前分析")
        self.assertIsNotNone(result.summary)
        self.assertIsNotNone(result.details)
        self.assertIsInstance(result.generated_at, datetime)

    def test_get_detailed_data_summary_from_stats(self):
        projects = [
            self._create_mock_project(LeadOutcomeEnum.WON.value),
            self._create_mock_project(LeadOutcomeEnum.LOST.value),
        ]

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 10

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        result = self.adapter.get_detailed_data()

        expected_keys = [
            "total_leads_ytd",
            "won_leads_ytd",
            "overall_win_rate",
            "avg_investment",
            "waste_rate",
            "wasted_cost",
        ]
        for key in expected_keys:
            self.assertIn(key, result.summary)

    def test_get_detailed_data_monthly_stats_12_months(self):
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = []

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 0

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        result = self.adapter.get_detailed_data()

        self.assertIn("monthly_stats", result.details)
        monthly_stats = result.details["monthly_stats"]
        self.assertEqual(len(monthly_stats), 12)

    def test_get_detailed_data_monthly_stats_structure(self):
        now = datetime.now()
        projects = [
            self._create_mock_project(LeadOutcomeEnum.WON.value, created_at=now),
            self._create_mock_project(LeadOutcomeEnum.LOST.value, created_at=now),
        ]

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 10

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        result = self.adapter.get_detailed_data()
        monthly_stats = result.details["monthly_stats"]

        for month_data in monthly_stats:
            self.assertIn("month", month_data)
            self.assertIn("total", month_data)
            self.assertIn("won", month_data)
            self.assertIn("lost", month_data)
            self.assertIn("win_rate", month_data)

    def test_get_detailed_data_monthly_stats_values(self):
        now = datetime.now()
        projects = [
            self._create_mock_project(LeadOutcomeEnum.WON.value, created_at=now),
            self._create_mock_project(LeadOutcomeEnum.WON.value, created_at=now),
            self._create_mock_project(LeadOutcomeEnum.LOST.value, created_at=now),
        ]

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 10

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        result = self.adapter.get_detailed_data()
        monthly_stats = result.details["monthly_stats"]

        current_month_key = now.strftime("%Y-%m")
        current_month_data = next(m for m in monthly_stats if m["month"] == current_month_key)

        self.assertEqual(current_month_data["total"], 3)
        self.assertEqual(current_month_data["won"], 2)
        self.assertEqual(current_month_data["lost"], 1)
        self.assertAlmostEqual(current_month_data["win_rate"], 0.667, places=3)


class TestPresalesDashboardAdapterEdgeCases(unittest.TestCase):
    """测试边界情况和异常处理"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.adapter = PresalesDashboardAdapter(self.mock_db, self.mock_user)

    def test_project_with_none_created_at(self):
        project = Mock()
        project.id = 1
        project.outcome = LeadOutcomeEnum.WON.value
        project.loss_reason = None
        project.created_at = None

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = [project]

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 10

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        widgets = self.adapter.get_widgets()
        self.assertIsNotNone(widgets)

    def test_divide_by_zero_protection(self):
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query

        stats = self.adapter.get_stats()
        stats_dict = {card.key: card for card in stats}

        self.assertEqual(stats_dict["avg_investment"].value, "0.0")

    def test_all_pending_projects(self):
        project1 = Mock()
        project1.id = 1
        project1.outcome = None
        project1.loss_reason = None
        project1.created_at = datetime.now()

        project2 = Mock()
        project2.id = 2
        project2.outcome = ""
        project2.loss_reason = None
        project2.created_at = datetime.now()

        projects = [project1, project2]

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 10

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        stats = self.adapter.get_stats()
        stats_dict = {card.key: card for card in stats}

        self.assertEqual(stats_dict["overall_win_rate"].value, "0.0%")

    def test_large_numbers_formatting(self):
        projects = [self._create_mock_project(LeadOutcomeEnum.LOST.value)]

        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.all.return_value = projects

        mock_worklog_query = MagicMock()
        mock_worklog_query.filter.return_value.scalar.return_value = 10000

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            return mock_worklog_query

        self.mock_db.query.side_effect = query_side_effect

        stats = self.adapter.get_stats()
        stats_dict = {card.key: card for card in stats}

        wasted_cost = stats_dict["wasted_cost"].value
        self.assertIn(",", wasted_cost)

    def _create_mock_project(self, outcome):
        project = Mock()
        project.id = 1
        project.outcome = outcome
        project.loss_reason = None
        project.created_at = datetime.now()
        return project


if __name__ == "__main__":
    unittest.main()

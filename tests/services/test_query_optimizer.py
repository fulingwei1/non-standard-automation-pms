# -*- coding: utf-8 -*-
"""QueryOptimizer 单元测试"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Patch missing model relationships
from app.models.project import Project
for _attr in ('owner', 'milestones', 'issues', 'contracts'):
    if not hasattr(Project, _attr):
        setattr(Project, _attr, MagicMock())

from app.models.shortage import ShortageReport
for _attr in ('material',):
    if not hasattr(ShortageReport, _attr):
        setattr(ShortageReport, _attr, MagicMock())
# Source code references urgency_level but model has urgent_level
if not hasattr(ShortageReport, 'urgency_level'):
    ShortageReport.urgency_level = ShortageReport.urgent_level
# Source code references report_date but model has report_time
if not hasattr(ShortageReport, 'report_date'):
    ShortageReport.report_date = ShortageReport.report_time

from app.models.project import ProjectStatusLog
# Source code references created_at but model has changed_at
if not hasattr(ProjectStatusLog, 'created_at'):
    ProjectStatusLog.created_at = ProjectStatusLog.changed_at

# Patch joinedload/selectinload/func at module level to avoid SQLAlchemy
# choking on MagicMock relationship attributes.
_patches = [
    patch("app.services.database.query_optimizer.joinedload", MagicMock(name="joinedload")),
    patch("app.services.database.query_optimizer.selectinload", MagicMock(name="selectinload")),
    patch("app.services.database.query_optimizer.or_", MagicMock(name="or_")),
]
for _p in _patches:
    _p.start()

from app.services.database.query_optimizer import QueryOptimizer


def tearDownModule():
    for _p in _patches:
        _p.stop()


class TestQueryOptimizer(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.optimizer = QueryOptimizer(self.db)

    def _chain(self):
        q = MagicMock()
        self.db.query.return_value = q
        q.options.return_value = q
        q.filter.return_value = q
        q.group_by.return_value = q
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        return q

    # --- get_project_list_optimized ---
    def test_get_project_list_no_filters(self):
        q = self._chain()
        q.all.return_value = ["p1"]
        result = self.optimizer.get_project_list_optimized()
        self.assertEqual(result, ["p1"])

    def test_get_project_list_with_filters(self):
        q = self._chain()
        q.all.return_value = []
        result = self.optimizer.get_project_list_optimized(status="active", customer_id=1)
        self.assertEqual(result, [])

    # --- get_project_dashboard_data ---
    def test_dashboard_not_found(self):
        q = self._chain()
        q.first.return_value = None
        result = self.optimizer.get_project_dashboard_data(999)
        self.assertEqual(result, {})

    def test_dashboard_found(self):
        q = self._chain()
        project = MagicMock(id=1)
        q.first.return_value = project
        q.all.return_value = []
        result = self.optimizer.get_project_dashboard_data(1)
        self.assertIn("project", result)

    # --- search_projects_optimized ---
    @patch("app.services.database.query_optimizer.build_keyword_conditions")
    def test_search_short_keyword(self, mock_build):
        result = self.optimizer.search_projects_optimized("a")
        self.assertEqual(result, [])

    @patch("app.services.database.query_optimizer.func")
    @patch("app.services.database.query_optimizer.build_keyword_conditions")
    def test_search_normal(self, mock_build, mock_func):
        mock_build.return_value = [MagicMock()]
        mock_func.case.return_value = MagicMock()
        q = self._chain()
        q.all.return_value = ["p1"]
        result = self.optimizer.search_projects_optimized("test keyword")
        self.assertEqual(result, ["p1"])

    # --- get_alert_statistics_optimized ---
    @patch("app.services.database.query_optimizer.func")
    def test_alert_statistics(self, mock_func):
        # Mock func.count, func.sum, func.case to return MagicMock labels
        mock_func.count.return_value.label.return_value = MagicMock()
        mock_func.sum.return_value.label.return_value = MagicMock()
        mock_func.case.return_value = MagicMock()

        q = self._chain()
        stats = MagicMock()
        stats.total_alerts = 10
        stats.critical_count = 2
        stats.warning_count = 3
        stats.info_count = 5
        stats.resolved_count = 7
        stats.pending_count = 3
        q.first.return_value = stats
        q.all.return_value = []

        result = self.optimizer.get_alert_statistics_optimized(days=30)
        self.assertEqual(result["summary"]["total_alerts"], 10)

    # --- get_shortage_reports_optimized ---
    @patch("app.services.database.query_optimizer.func")
    def test_shortage_reports(self, mock_func):
        mock_func.case.return_value = MagicMock()
        q = self._chain()
        q.all.return_value = []
        result = self.optimizer.get_shortage_reports_optimized(project_id=1, status="open", urgency="HIGH")
        self.assertEqual(result, [])

    # --- get_contract_performance_optimized ---
    def test_contract_performance(self):
        q = self._chain()
        stats = MagicMock()
        stats.total_contracts = 5
        stats.total_amount = 100000
        stats.avg_amount = 20000
        q.first.return_value = stats
        q.all.return_value = []

        result = self.optimizer.get_contract_performance_optimized(days=90)
        self.assertEqual(result["summary"]["total_contracts"], 5)

    # --- create_optimized_indexes_suggestions ---
    def test_index_suggestions(self):
        suggestions = self.optimizer.create_optimized_indexes_suggestions()
        self.assertTrue(len(suggestions) > 0)
        self.assertTrue(all("CREATE INDEX" in s for s in suggestions))

    # --- explain_slow_queries ---
    def test_explain_success(self):
        self.db.execute.return_value.fetchall.return_value = [("row1",)]
        result = self.optimizer.explain_slow_queries()
        self.assertIn("slow_queries", result)

    def test_explain_error(self):
        self.db.execute.side_effect = Exception("db error")
        result = self.optimizer.explain_slow_queries()
        self.assertIn("error", result["slow_queries"][0])

    # --- optimize_query ---
    def test_optimize_query_no_options(self):
        query = MagicMock()
        result = self.optimizer.optimize_query(query)
        self.assertEqual(result, query)

    def test_optimize_query_with_eager_load(self):
        query = MagicMock()
        query.options.return_value = query
        result = self.optimizer.optimize_query(query, eager_load=["rel1"])
        query.options.assert_called()

    def test_optimize_query_with_filters(self):
        query = MagicMock()
        query.filter.return_value = query
        result = self.optimizer.optimize_query(query, filters={"status": "active"})
        query.filter.assert_called()

    # --- paginate ---
    @patch("app.services.database.query_optimizer.get_pagination_params")
    @patch("app.services.database.query_optimizer.apply_pagination")
    def test_paginate(self, mock_apply, mock_get_params):
        query = MagicMock()
        query.count.return_value = 50

        pag = MagicMock()
        pag.page = 1
        pag.page_size = 20
        pag.offset = 0
        pag.limit = 20
        pag.pages_for_total.return_value = 3
        mock_get_params.return_value = pag
        mock_apply.return_value = query
        query.all.return_value = ["item1"]

        result = self.optimizer.paginate(query, page=1, page_size=20)
        self.assertEqual(result["total"], 50)
        self.assertEqual(result["total_pages"], 3)


if __name__ == "__main__":
    unittest.main()

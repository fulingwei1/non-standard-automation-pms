# -*- coding: utf-8 -*-
"""Compatibility tests for the historical management rhythm test path."""

import unittest
from datetime import date, datetime
from unittest.mock import MagicMock

from app.models.enums import ActionItemStatus
from app.services.dashboard_adapters.management_rhythm import ManagementRhythmDashboardAdapter


class TestManagementRhythmDashboardAdapter(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.current_user = MagicMock(id=1)
        self.adapter = ManagementRhythmDashboardAdapter(self.db, self.current_user)

    @staticmethod
    def _snapshot_query(snapshot=None):
        query = MagicMock()
        query.filter.return_value.order_by.return_value.first.return_value = snapshot
        return query

    @staticmethod
    def _count_query(count):
        query = MagicMock()
        query.filter.return_value.count.return_value = count
        query.count.return_value = count
        return query

    @staticmethod
    def _list_query(items):
        query = MagicMock()
        query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = items
        return query

    def test_get_stats_with_snapshot_data(self):
        strategic_snapshot = MagicMock(health_status="GREEN")
        self.db.query.side_effect = [
            self._snapshot_query(strategic_snapshot),
            self._snapshot_query(None),
            self._count_query(10),
            self._count_query(50),
            self._count_query(35),
            self._count_query(5),
        ]

        result = self.adapter.get_stats()
        stats = {card.key: card for card in result}

        self.assertEqual(len(result), 6)
        self.assertEqual(stats["total_meetings"].value, 10)
        self.assertEqual(stats["total_action_items"].value, 50)
        self.assertEqual(stats["completed_action_items"].value, 35)
        self.assertEqual(stats["completion_rate"].value, 70.0)
        self.assertEqual(stats["strategic_health"].value, "GREEN")

    def test_get_stats_without_snapshot(self):
        self.db.query.side_effect = [
            self._snapshot_query(None),
            self._snapshot_query(None),
            self._count_query(0),
            self._count_query(0),
            self._count_query(0),
            self._count_query(0),
        ]

        result = self.adapter.get_stats()
        stats = {card.key: card.value for card in result}

        self.assertEqual(stats["completion_rate"], 0)
        self.assertEqual(stats["strategic_health"], "N/A")

    def test_get_stats_completion_rate_calculation(self):
        self.db.query.side_effect = [
            self._snapshot_query(None),
            self._snapshot_query(None),
            self._count_query(5),
            self._count_query(20),
            self._count_query(20),
            self._count_query(0),
        ]

        result = self.adapter.get_stats()
        stats = {card.key: card.value for card in result}

        self.assertEqual(stats["completion_rate"], 100.0)

    def test_get_stats_with_partial_data(self):
        self.db.query.side_effect = [
            self._snapshot_query(None),
            self._snapshot_query(None),
            self._count_query(5),
            self._count_query(0),
            self._count_query(0),
            self._count_query(0),
        ]

        result = self.adapter.get_stats()
        stats = {card.key: card.value for card in result}

        self.assertEqual(stats["total_meetings"], 5)
        self.assertEqual(stats["completion_rate"], 0)

    def test_get_stats_card_properties(self):
        self.db.query.side_effect = [
            self._snapshot_query(None),
            self._snapshot_query(None),
            self._count_query(1),
            self._count_query(1),
            self._count_query(1),
            self._count_query(0),
        ]

        result = self.adapter.get_stats()

        for card in result:
            self.assertIsNotNone(card.key)
            self.assertIsNotNone(card.title)
            self.assertIsNotNone(card.value)

    def test_get_widgets_with_data(self):
        today = date.today()
        meetings = [
            MagicMock(id=1, title="战略研讨会", rhythm_level="STRATEGIC", meeting_date=today, status="SCHEDULED"),
            MagicMock(id=2, title="运营例会", rhythm_level="OPERATIONAL", meeting_date=today, status="ONGOING"),
        ]
        action_items = [
            MagicMock(id=11, title="完成方案设计", due_date=today, status=ActionItemStatus.IN_PROGRESS.value, priority="HIGH"),
            MagicMock(id=12, title="提交报告", due_date=today, status=ActionItemStatus.TODO.value, priority="NORMAL"),
        ]
        meetings_query = self._list_query(meetings)
        actions_query = self._list_query(action_items)
        self.db.query.side_effect = [meetings_query, actions_query]

        result = self.adapter.get_widgets()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].widget_id, "upcoming_meetings")
        self.assertEqual(result[1].widget_id, "my_action_items")
        self.assertEqual(result[0].data[0]["title"], "战略研讨会")
        self.assertEqual(result[1].data[0]["title"], "完成方案设计")

    def test_get_widgets_empty_data(self):
        meetings_query = self._list_query([])
        actions_query = self._list_query([])
        self.db.query.side_effect = [meetings_query, actions_query]

        result = self.adapter.get_widgets()

        self.assertEqual(len(result[0].data), 0)
        self.assertEqual(len(result[1].data), 0)

    def test_get_widgets_uses_current_user(self):
        meetings_query = self._list_query([])
        actions_query = self._list_query([])
        self.db.query.side_effect = [meetings_query, actions_query]

        result = self.adapter.get_widgets()

        self.assertEqual(len(result), 2)
        self.assertTrue(actions_query.filter.called)

    def test_get_widgets_widget_order(self):
        meetings_query = self._list_query([])
        actions_query = self._list_query([])
        self.db.query.side_effect = [meetings_query, actions_query]

        result = self.adapter.get_widgets()

        self.assertEqual(result[0].order, 1)
        self.assertEqual(result[1].order, 2)
        self.assertEqual(result[0].span, 12)
        self.assertEqual(result[1].span, 12)

    def test_get_detailed_data_complete(self):
        strategic_snapshot = MagicMock(health_status="YELLOW")
        self.db.query.side_effect = [
            self._snapshot_query(strategic_snapshot),
            self._snapshot_query(None),
            self._count_query(15),
            self._count_query(60),
            self._count_query(40),
            self._count_query(8),
            self._count_query(5),
            self._count_query(3),
            self._count_query(4),
            self._count_query(2),
            self._count_query(3),
            self._count_query(1),
            self._count_query(3),
            self._count_query(1),
        ]

        result = self.adapter.get_detailed_data()

        self.assertEqual(result.module_id, "management_rhythm")
        self.assertEqual(result.module_name, "管理节律")
        self.assertEqual(result.summary["total_meetings"], 15)
        self.assertEqual(len(result.details["level_stats"]), 4)
        self.assertEqual(result.details["level_stats"][0]["level"], "STRATEGIC")
        self.assertIsInstance(result.generated_at, datetime)

    def test_get_detailed_data_summary_keys(self):
        self.db.query.side_effect = [
            self._snapshot_query(None),
            self._snapshot_query(None),
            self._count_query(1),
            self._count_query(1),
            self._count_query(1),
            self._count_query(1),
            self._count_query(1),
            self._count_query(1),
            self._count_query(1),
            self._count_query(1),
            self._count_query(1),
            self._count_query(1),
            self._count_query(1),
            self._count_query(1),
        ]

        result = self.adapter.get_detailed_data()

        expected_keys = {
            "total_meetings",
            "total_action_items",
            "completed_action_items",
            "overdue_action_items",
            "completion_rate",
            "strategic_health",
        }
        self.assertTrue(expected_keys.issubset(result.summary.keys()))

    def test_get_detailed_data_zero_counts(self):
        self.db.query.side_effect = [
            self._snapshot_query(None),
            self._snapshot_query(None),
            self._count_query(0),
            self._count_query(0),
            self._count_query(0),
            self._count_query(0),
            self._count_query(0),
            self._count_query(0),
            self._count_query(0),
            self._count_query(0),
            self._count_query(0),
            self._count_query(0),
            self._count_query(0),
            self._count_query(0),
        ]

        result = self.adapter.get_detailed_data()

        self.assertEqual(result.summary["total_meetings"], 0)
        self.assertEqual(len(result.details["level_stats"]), 4)
        self.assertTrue(all(item["meetings_count"] == 0 for item in result.details["level_stats"]))

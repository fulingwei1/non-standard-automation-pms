# -*- coding: utf-8 -*-
from unittest.mock import MagicMock
from datetime import date
from app.services.performance_collector.design_collector import DesignCollector


class TestDesignCollector:
    def setup_method(self):
        self.db = MagicMock()
        self.collector = DesignCollector(self.db)

    def test_no_reviews(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = self.collector.collect_design_review_data(1, date(2024, 1, 1), date(2024, 3, 1))
        assert result["total_reviews"] == 0
        assert result["first_pass_rate"] == 0.0

    def test_with_reviews(self):
        r1 = MagicMock(); r1.is_first_pass = True
        r2 = MagicMock(); r2.is_first_pass = False
        self.db.query.return_value.filter.return_value.all.return_value = [r1, r2]
        result = self.collector.collect_design_review_data(1, date(2024, 1, 1), date(2024, 3, 1))
        assert result["total_reviews"] == 2
        assert result["first_pass_rate"] == 50.0

    def test_no_debug_issues(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = self.collector.collect_debug_issue_data(1, date(2024, 1, 1), date(2024, 3, 1))
        assert result["mechanical_issues"] == 0
        assert result["test_bugs"] == 0

    def test_with_bugs(self):
        bug1 = MagicMock(); bug1.status = "resolved"; bug1.fix_duration_hours = 4.0
        bug2 = MagicMock(); bug2.status = "open"; bug2.fix_duration_hours = None
        self.db.query.return_value.filter.return_value.all.side_effect = [
            [],  # mechanical issues
            [bug1, bug2],  # test bugs
        ]
        result = self.collector.collect_debug_issue_data(1, date(2024, 1, 1), date(2024, 3, 1))
        assert result["test_bugs"] == 2
        assert result["resolved_bugs"] == 1
        assert result["avg_fix_time"] == 4.0

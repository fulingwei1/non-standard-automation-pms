# -*- coding: utf-8 -*-
"""设计评审数据收集器单元测试 - 第三十六批"""

import pytest
from datetime import date
from unittest.mock import MagicMock

pytest.importorskip("app.services.performance_collector.design_collector")

try:
    from app.services.performance_collector.design_collector import DesignCollector
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    DesignCollector = None


def make_collector(reviews=None, mechanical_issues=None, test_bugs=None):
    db = MagicMock()
    mock_query = db.query.return_value.filter.return_value

    def side_effect_reviews(*args, **kwargs):
        return reviews or []

    def side_effect_bugs(*args, **kwargs):
        return test_bugs or []

    def side_effect_mech(*args, **kwargs):
        return mechanical_issues or []

    mock_query.all.return_value = reviews or []

    collector = DesignCollector.__new__(DesignCollector)
    collector.db = db
    return collector, db


START = date(2024, 1, 1)
END = date(2024, 1, 31)


class TestCollectDesignReviewData:
    def test_no_reviews_returns_zeros(self):
        collector, db = make_collector()
        db.query.return_value.filter.return_value.all.return_value = []
        result = collector.collect_design_review_data(1, START, END)
        assert result["total_reviews"] == 0
        assert result["first_pass_rate"] == 0.0

    def test_all_first_pass(self):
        r1 = MagicMock(); r1.is_first_pass = True
        r2 = MagicMock(); r2.is_first_pass = True
        collector, db = make_collector()
        db.query.return_value.filter.return_value.all.return_value = [r1, r2]
        result = collector.collect_design_review_data(1, START, END)
        assert result["total_reviews"] == 2
        assert result["first_pass_rate"] == 100.0

    def test_partial_first_pass(self):
        r1 = MagicMock(); r1.is_first_pass = True
        r2 = MagicMock(); r2.is_first_pass = False
        collector, db = make_collector()
        db.query.return_value.filter.return_value.all.return_value = [r1, r2]
        result = collector.collect_design_review_data(1, START, END)
        assert result["first_pass_rate"] == 50.0

    def test_exception_returns_defaults(self):
        collector, db = make_collector()
        db.query.side_effect = Exception("DB error")
        result = collector.collect_design_review_data(1, START, END)
        assert "error" in result
        assert result["total_reviews"] == 0


class TestCollectDebugIssueData:
    def test_no_data_returns_zeros(self):
        collector, db = make_collector()
        db.query.return_value.filter.return_value.all.return_value = []
        result = collector.collect_debug_issue_data(1, START, END)
        assert result["mechanical_issues"] == 0
        assert result["test_bugs"] == 0

    def test_exception_returns_defaults(self):
        collector, db = make_collector()
        db.query.side_effect = Exception("DB error")
        result = collector.collect_debug_issue_data(1, START, END)
        assert "error" in result
        assert result["avg_fix_time"] == 0.0

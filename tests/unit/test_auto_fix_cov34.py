# -*- coding: utf-8 -*-
"""自动修复模块单元测试 - 第三十四批"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.data_integrity.auto_fix")

try:
    from app.services.data_integrity.auto_fix import AutoFixMixin
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    AutoFixMixin = None


def make_mixin(report=None):
    mixin = AutoFixMixin.__new__(AutoFixMixin)
    mixin.db = MagicMock()
    if report is not None:
        mixin.check_data_completeness = MagicMock(return_value=report)
    return mixin


DEFAULT_REPORT = {
    "collab_ratings_count": 0,
    "work_logs_count": 0,
    "warnings": [],
    "missing_items": [],
}


class TestSuggestAutoFixes:
    def test_low_collab_suggests_auto_select(self):
        mixin = make_mixin(report=DEFAULT_REPORT)
        suggestions = mixin.suggest_auto_fixes(engineer_id=1, period_id=1)
        types = [s["type"] for s in suggestions]
        assert "auto_select_collaborators" in types

    def test_zero_work_log_suggests_reminder(self):
        mixin = make_mixin(report=DEFAULT_REPORT)
        suggestions = mixin.suggest_auto_fixes(engineer_id=1, period_id=1)
        types = [s["type"] for s in suggestions]
        assert "remind_work_log" in types

    def test_sufficient_collab_no_auto_select(self):
        report = {**DEFAULT_REPORT, "collab_ratings_count": 5, "work_logs_count": 10}
        mixin = make_mixin(report=report)
        suggestions = mixin.suggest_auto_fixes(engineer_id=1, period_id=1)
        types = [s["type"] for s in suggestions]
        assert "auto_select_collaborators" not in types

    def test_all_suggestions_have_required_keys(self):
        mixin = make_mixin(report=DEFAULT_REPORT)
        suggestions = mixin.suggest_auto_fixes(engineer_id=1, period_id=1)
        for s in suggestions:
            assert "type" in s
            assert "action" in s
            assert "can_auto_fix" in s


class TestAutoFixDataIssues:
    def test_returns_dict_with_expected_keys(self):
        report = {**DEFAULT_REPORT, "collab_ratings_count": 3, "work_logs_count": 1}
        mixin = make_mixin(report=report)
        result = mixin.auto_fix_data_issues(engineer_id=1, period_id=1)
        assert "fixes_applied" in result
        assert "fixes_failed" in result
        assert "total_applied" in result
        assert "total_failed" in result

    def test_engineer_id_in_result(self):
        report = {**DEFAULT_REPORT, "collab_ratings_count": 3, "work_logs_count": 1}
        mixin = make_mixin(report=report)
        result = mixin.auto_fix_data_issues(engineer_id=99, period_id=1)
        assert result["engineer_id"] == 99

    def test_fix_types_filter_applied(self):
        """传入 fix_types 时，只修复指定类型"""
        report = {**DEFAULT_REPORT}  # collab < 3
        mixin = make_mixin(report=report)
        # Pass a type that doesn't exist
        result = mixin.auto_fix_data_issues(
            engineer_id=1, period_id=1, fix_types=["nonexistent_type"]
        )
        assert result["total_applied"] == 0

    def test_auto_fix_with_no_fixable_types(self):
        """fix_types 传入不可修复的类型时，结果应为空"""
        report = {**DEFAULT_REPORT, "collab_ratings_count": 1}
        mixin = make_mixin(report=report)
        # 'remind_work_log' 的 can_auto_fix=False，不应被执行
        result = mixin.auto_fix_data_issues(
            engineer_id=1, period_id=1,
            fix_types=["remind_work_log"]
        )
        assert result["total_applied"] == 0

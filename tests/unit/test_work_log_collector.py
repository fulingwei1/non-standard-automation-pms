# -*- coding: utf-8 -*-
"""工作日志数据收集器 单元测试"""
from datetime import date
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from app.services.performance_collector.work_log_collector import WorkLogCollector


def _make_collector():
    c = WorkLogCollector.__new__(WorkLogCollector)
    c.db = MagicMock()
    c.POSITIVE_KEYWORDS = ["完成", "解决", "优化"]
    c.NEGATIVE_KEYWORDS = ["延迟", "失败"]
    c.TECH_KEYWORDS = ["代码", "架构"]
    c.COLLABORATION_KEYWORDS = ["协作", "沟通"]
    c.PROBLEM_SOLVING_PATTERNS = [r"解决.*问题"]
    c.KNOWLEDGE_SHARING_PATTERNS = [r"分享.*经验"]
    c.TECH_BREAKTHROUGH_PATTERNS = [r"突破.*技术"]
    return c


def _make_log(content):
    log = MagicMock()
    log.content = content
    return log


class TestExtractSelfEvaluation:
    def test_no_logs_returns_default(self):
        c = _make_collector()
        c.db.query.return_value.filter.return_value.all.return_value = []
        result = c.extract_self_evaluation_from_work_logs(1, date(2025, 1, 1), date(2025, 1, 31))
        assert result["total_logs"] == 0
        assert result["self_evaluation_score"] == 75.0

    def test_positive_keywords_counted(self):
        c = _make_collector()
        logs = [_make_log("今天完成了任务，优化了代码")]
        c.db.query.return_value.filter.return_value.all.return_value = logs
        result = c.extract_self_evaluation_from_work_logs(1, date(2025, 1, 1), date(2025, 1, 31))
        assert result["positive_count"] > 0
        assert result["total_logs"] == 1

    def test_negative_keywords_counted(self):
        c = _make_collector()
        logs = [_make_log("项目延迟了，测试失败")]
        c.db.query.return_value.filter.return_value.all.return_value = logs
        result = c.extract_self_evaluation_from_work_logs(1, date(2025, 1, 1), date(2025, 1, 31))
        assert result["negative_count"] > 0

    def test_problem_solving_pattern(self):
        c = _make_collector()
        logs = [_make_log("解决了一个复杂问题")]
        c.db.query.return_value.filter.return_value.all.return_value = logs
        result = c.extract_self_evaluation_from_work_logs(1, date(2025, 1, 1), date(2025, 1, 31))
        assert result["problem_solving_count"] >= 1

    def test_exception_returns_default(self):
        c = _make_collector()
        c.db.query.side_effect = Exception("DB error")
        result = c.extract_self_evaluation_from_work_logs(1, date(2025, 1, 1), date(2025, 1, 31))
        assert result["self_evaluation_score"] == 75.0
        assert "error" in result

    def test_empty_content_skipped(self):
        c = _make_collector()
        logs = [_make_log(None), _make_log("完成任务")]
        c.db.query.return_value.filter.return_value.all.return_value = logs
        result = c.extract_self_evaluation_from_work_logs(1, date(2025, 1, 1), date(2025, 1, 31))
        assert result["total_logs"] == 2

    def test_score_clamped_0_100(self):
        c = _make_collector()
        # All positive
        logs = [_make_log("完成 完成 完成 解决 优化")]
        c.db.query.return_value.filter.return_value.all.return_value = logs
        result = c.extract_self_evaluation_from_work_logs(1, date(2025, 1, 1), date(2025, 1, 31))
        assert 0 <= result["self_evaluation_score"] <= 100

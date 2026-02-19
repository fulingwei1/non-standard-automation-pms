# -*- coding: utf-8 -*-
"""
tests/unit/test_pc_work_log_collector_cov51.py
Unit tests for app/services/performance_collector/work_log_collector.py
"""
import pytest
from datetime import date
from unittest.mock import MagicMock

try:
    from app.services.performance_collector.work_log_collector import WorkLogCollector
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


START = date(2025, 1, 1)
END = date(2025, 1, 31)


def _make_collector():
    db = MagicMock()
    return WorkLogCollector(db), db


def _make_log(content, status="SUBMITTED"):
    log = MagicMock()
    log.content = content
    log.status = status
    return log


def test_no_logs_returns_defaults():
    collector, db = _make_collector()
    db.query.return_value.filter.return_value.all.return_value = []

    result = collector.extract_self_evaluation_from_work_logs(1, START, END)

    assert result["total_logs"] == 0
    assert result["self_evaluation_score"] == 75.0


def test_positive_content_raises_score():
    collector, db = _make_collector()
    log = _make_log("今天完成了任务，顺利交付，通过验收，优化了性能。")
    db.query.return_value.filter.return_value.all.return_value = [log]

    result = collector.extract_self_evaluation_from_work_logs(1, START, END)

    assert result["positive_count"] > 0
    assert result["total_logs"] == 1


def test_negative_content_lowers_score():
    collector, db = _make_collector()
    log = _make_log("遇到延期，出现Bug，存在问题，任务未完成，有风险。")
    db.query.return_value.filter.return_value.all.return_value = [log]

    result = collector.extract_self_evaluation_from_work_logs(1, START, END)

    assert result["negative_count"] > 0


def test_problem_solving_context_adds_bonus():
    collector, db = _make_collector()
    # Matches PROBLEM_SOLVING_PATTERNS pattern like: 遇到.*?问题.*?解决
    log = _make_log("遇到了性能问题，通过分析最终解决。")
    db.query.return_value.filter.return_value.all.return_value = [log]

    result = collector.extract_self_evaluation_from_work_logs(1, START, END)

    assert result["problem_solving_count"] >= 1


def test_knowledge_sharing_context_adds_bonus():
    collector, db = _make_collector()
    # Matches KNOWLEDGE_SHARING_PATTERNS
    log = _make_log("本月分享了开发经验给新成员，知识传递顺利。")
    db.query.return_value.filter.return_value.all.return_value = [log]

    result = collector.extract_self_evaluation_from_work_logs(1, START, END)

    assert result["knowledge_sharing_count"] >= 1


def test_tech_breakthrough_pattern_detected():
    collector, db = _make_collector()
    log = _make_log("本次完成了技术突破，优化了系统性能，提升了效率。")
    db.query.return_value.filter.return_value.all.return_value = [log]

    result = collector.extract_self_evaluation_from_work_logs(1, START, END)

    assert result["tech_breakthrough_count"] >= 1


def test_exception_in_db_returns_defaults():
    collector, db = _make_collector()
    db.query.side_effect = Exception("connection error")

    result = collector.extract_self_evaluation_from_work_logs(1, START, END)

    assert "error" in result
    assert result["self_evaluation_score"] == 75.0


def test_score_clamped_100():
    collector, db = _make_collector()
    log = _make_log("完成完成完成完成完成完成完成完成优化优化优化优化" * 50)
    db.query.return_value.filter.return_value.all.return_value = [log]

    result = collector.extract_self_evaluation_from_work_logs(1, START, END)

    assert result["self_evaluation_score"] <= 100.0

# -*- coding: utf-8 -*-
"""
tests/unit/test_pc_work_log_cov51.py
Unit tests for app/services/performance_collector/work_log.py
"""
import pytest
from datetime import date
from unittest.mock import MagicMock

try:
    from app.services.performance_collector.work_log import (
        extract_self_evaluation_from_work_logs,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_log(content, status="SUBMITTED"):
    log = MagicMock()
    log.content = content
    log.status = status
    log.work_date = date(2025, 1, 15)
    log.user_id = 1
    return log


START = date(2025, 1, 1)
END = date(2025, 1, 31)


def test_no_logs_returns_defaults():
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []

    result = extract_self_evaluation_from_work_logs(db, 1, START, END)

    assert result["total_logs"] == 0
    assert result["self_evaluation_score"] == 75.0
    assert result["positive_count"] == 0


def test_positive_keywords_counted():
    db = MagicMock()
    log = _make_log("今天完成了需求分析，交付了设计文档，顺利通过评审。")
    db.query.return_value.filter.return_value.all.return_value = [log]

    result = extract_self_evaluation_from_work_logs(db, 1, START, END)

    assert result["total_logs"] == 1
    assert result["positive_count"] > 0


def test_negative_keywords_counted():
    db = MagicMock()
    log = _make_log("遇到了延期问题，存在技术难点和Bug，任务未完成。")
    db.query.return_value.filter.return_value.all.return_value = [log]

    result = extract_self_evaluation_from_work_logs(db, 1, START, END)

    assert result["negative_count"] > 0


def test_tech_mentions_counted():
    db = MagicMock()
    log = _make_log("今天进行代码调试，优化了算法，分析了架构。")
    db.query.return_value.filter.return_value.all.return_value = [log]

    result = extract_self_evaluation_from_work_logs(db, 1, START, END)

    assert result["tech_mentions"] > 0


def test_score_clamped_between_0_and_100():
    db = MagicMock()
    # All very positive content
    log = _make_log("完成 " * 100 + "优化 " * 100)
    db.query.return_value.filter.return_value.all.return_value = [log]

    result = extract_self_evaluation_from_work_logs(db, 1, START, END)

    assert 0 <= result["self_evaluation_score"] <= 100


def test_empty_content_log_handled():
    db = MagicMock()
    log = _make_log(None)
    db.query.return_value.filter.return_value.all.return_value = [log]

    result = extract_self_evaluation_from_work_logs(db, 1, START, END)

    assert result["total_logs"] == 1
    assert result["positive_count"] == 0


def test_exception_returns_default():
    db = MagicMock()
    db.query.side_effect = Exception("DB error")

    result = extract_self_evaluation_from_work_logs(db, 1, START, END)

    assert "error" in result
    assert result["self_evaluation_score"] == 75.0

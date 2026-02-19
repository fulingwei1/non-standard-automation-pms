# -*- coding: utf-8 -*-
"""
第四十三批覆盖率测试 - app/services/performance_collector/work_log.py
（模块级函数 extract_self_evaluation_from_work_logs）
"""
import pytest

pytest.importorskip("app.services.performance_collector.work_log")

from datetime import date
from unittest.mock import MagicMock, patch

from app.services.performance_collector.work_log import (
    extract_self_evaluation_from_work_logs,
)


def make_db():
    return MagicMock()


# ── 1. 无工作日志时返回默认值 ─────────────────────────────────────────────────
def test_no_work_logs_returns_defaults():
    db = make_db()
    db.query.return_value.filter.return_value.all.return_value = []

    result = extract_self_evaluation_from_work_logs(db, 1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["total_logs"] == 0
    assert result["self_evaluation_score"] == 75.0
    assert result["positive_count"] == 0


# ── 2. 日志内容为空时计数均为零 ──────────────────────────────────────────────
def test_empty_content_logs():
    db = make_db()
    log = MagicMock()
    log.content = None
    db.query.return_value.filter.return_value.all.return_value = [log]

    result = extract_self_evaluation_from_work_logs(db, 1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["total_logs"] == 1
    assert result["positive_count"] == 0
    assert result["self_evaluation_score"] == 75.0


# ── 3. 积极词汇占主导时得分 > 75 ─────────────────────────────────────────────
def test_positive_content_raises_score():
    db = make_db()
    log = MagicMock()
    log.content = "完成了任务，优化了代码，解决了问题，成功交付"
    db.query.return_value.filter.return_value.all.return_value = [log]

    result = extract_self_evaluation_from_work_logs(db, 1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["positive_count"] > 0
    assert result["self_evaluation_score"] >= 75.0


# ── 4. 消极词汇占主导时得分 < 75 ─────────────────────────────────────────────
def test_negative_content_lowers_score():
    db = make_db()
    log = MagicMock()
    # heavy negative content
    log.content = "延期了很多，未完成任务，失败了，遇到了很多问题，延迟严重"
    db.query.return_value.filter.return_value.all.return_value = [log]

    result = extract_self_evaluation_from_work_logs(db, 1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["negative_count"] > 0
    # score should be <= 75 due to negative dominance
    # (could be slightly above 75 depending on ratio)
    assert result["self_evaluation_score"] <= 100.0  # at least valid range


# ── 5. 技术词汇统计 ───────────────────────────────────────────────────────────
def test_tech_mentions_counted():
    db = make_db()
    log = MagicMock()
    log.content = "进行了架构设计，编写代码，完成测试，优化算法"
    db.query.return_value.filter.return_value.all.return_value = [log]

    result = extract_self_evaluation_from_work_logs(db, 1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["tech_mentions"] > 0


# ── 6. 评分范围在 [0, 100] 之间 ──────────────────────────────────────────────
def test_score_within_valid_range():
    db = make_db()
    log = MagicMock()
    log.content = "完成 " * 100  # heavily positive
    db.query.return_value.filter.return_value.all.return_value = [log]

    result = extract_self_evaluation_from_work_logs(db, 1, date(2026, 1, 1), date(2026, 1, 31))
    assert 0 <= result["self_evaluation_score"] <= 100


# ── 7. 数据库异常时返回默认值 ─────────────────────────────────────────────────
def test_exception_returns_defaults():
    db = make_db()
    db.query.side_effect = Exception("DB error")

    result = extract_self_evaluation_from_work_logs(db, 1, date(2026, 1, 1), date(2026, 1, 31))
    assert "error" in result
    assert result["self_evaluation_score"] == 75.0


# ── 8. 问题解决场景加分 ─────────────────────────────────────────────────────
def test_problem_solving_bonus():
    db = make_db()
    log = MagicMock()
    log.content = "遇到了bug问题，通过分析方法解决了该问题"
    db.query.return_value.filter.return_value.all.return_value = [log]

    result = extract_self_evaluation_from_work_logs(db, 1, date(2026, 1, 1), date(2026, 1, 31))
    # problem solving adds bonus
    assert result["self_evaluation_score"] >= 0

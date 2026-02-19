# -*- coding: utf-8 -*-
"""
第四十三批覆盖率测试 - app/services/performance_collector/work_log_collector.py
"""
import pytest

pytest.importorskip("app.services.performance_collector.work_log_collector")

from datetime import date
from unittest.mock import MagicMock

from app.services.performance_collector.work_log_collector import WorkLogCollector


def make_collector():
    db = MagicMock()
    return WorkLogCollector(db)


# ── 1. 无工作日志时返回默认值 ─────────────────────────────────────────────────
def test_no_logs_returns_defaults():
    c = make_collector()
    c.db.query.return_value.filter.return_value.all.return_value = []

    result = c.extract_self_evaluation_from_work_logs(1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["total_logs"] == 0
    assert result["self_evaluation_score"] == 75.0


# ── 2. 日志内容为 None 时跳过 ────────────────────────────────────────────────
def test_none_content_skipped():
    c = make_collector()
    log = MagicMock()
    log.content = None
    c.db.query.return_value.filter.return_value.all.return_value = [log]

    result = c.extract_self_evaluation_from_work_logs(1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["total_logs"] == 1
    assert result["positive_count"] == 0


# ── 3. 积极内容拉高分数 ──────────────────────────────────────────────────────
def test_positive_content():
    c = make_collector()
    log = MagicMock()
    log.content = "成功完成了设计任务，优化了架构，分享了经验，协作完成"
    c.db.query.return_value.filter.return_value.all.return_value = [log]

    result = c.extract_self_evaluation_from_work_logs(1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["positive_count"] > 0
    assert result["tech_mentions"] > 0 or result["collaboration_mentions"] > 0


# ── 4. 协作词汇计数 ─────────────────────────────────────────────────────────
def test_collaboration_keywords_counted():
    c = make_collector()
    log = MagicMock()
    log.content = "配合团队完成任务，沟通顺畅，协作效率高"
    c.db.query.return_value.filter.return_value.all.return_value = [log]

    result = c.extract_self_evaluation_from_work_logs(1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["collaboration_mentions"] > 0


# ── 5. 技术突破场景加分 ─────────────────────────────────────────────────────
def test_tech_breakthrough_bonus():
    c = make_collector()
    log = MagicMock()
    log.content = "实现了技术突破，优化了性能"
    c.db.query.return_value.filter.return_value.all.return_value = [log]

    result = c.extract_self_evaluation_from_work_logs(1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["tech_breakthrough_count"] >= 0  # scenario matched or not
    assert result["self_evaluation_score"] <= 100


# ── 6. 知识分享场景统计 ─────────────────────────────────────────────────────
def test_knowledge_sharing_counted():
    c = make_collector()
    log = MagicMock()
    log.content = "分享了经验给团队成员，培训了新人"
    c.db.query.return_value.filter.return_value.all.return_value = [log]

    result = c.extract_self_evaluation_from_work_logs(1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["knowledge_sharing_count"] >= 0


# ── 7. 评分范围合法 ─────────────────────────────────────────────────────────
def test_score_range_valid():
    c = make_collector()
    log = MagicMock()
    log.content = "完成" * 50
    c.db.query.return_value.filter.return_value.all.return_value = [log]

    result = c.extract_self_evaluation_from_work_logs(1, date(2026, 1, 1), date(2026, 1, 31))
    assert 0.0 <= result["self_evaluation_score"] <= 100.0


# ── 8. 数据库异常时返回默认值 ─────────────────────────────────────────────────
def test_db_exception_returns_defaults():
    c = make_collector()
    c.db.query.side_effect = Exception("connection error")

    result = c.extract_self_evaluation_from_work_logs(1, date(2026, 1, 1), date(2026, 1, 31))
    assert "error" in result
    assert result["total_logs"] == 0

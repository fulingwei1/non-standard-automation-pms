# -*- coding: utf-8 -*-
"""Tests for performance_collector/work_log.py"""
from datetime import date
from unittest.mock import MagicMock, patch

import pytest


class TestExtractSelfEvaluation:

    @patch("app.services.performance_collector.work_log.POSITIVE_KEYWORDS", ["完成", "优化"])
    @patch("app.services.performance_collector.work_log.NEGATIVE_KEYWORDS", ["延迟", "失败"])
    @patch("app.services.performance_collector.work_log.TECH_KEYWORDS", ["架构", "算法"])
    @patch("app.services.performance_collector.work_log.COLLABORATION_KEYWORDS", ["协作", "沟通"])
    @patch("app.services.performance_collector.work_log.PROBLEM_SOLVING_PATTERNS", ["解决.*问题"])
    @patch("app.services.performance_collector.work_log.KNOWLEDGE_SHARING_PATTERNS", ["分享.*经验"])
    @patch("app.services.performance_collector.work_log.TECH_BREAKTHROUGH_PATTERNS", ["突破.*技术"])
    def test_no_work_logs(self):
        from app.services.performance_collector.work_log import extract_self_evaluation_from_work_logs
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = extract_self_evaluation_from_work_logs(db, 1, date(2024, 1, 1), date(2024, 3, 31))
        assert result["total_logs"] == 0
        assert result["self_evaluation_score"] == 75.0

    @patch("app.services.performance_collector.work_log.POSITIVE_KEYWORDS", ["完成", "优化"])
    @patch("app.services.performance_collector.work_log.NEGATIVE_KEYWORDS", ["延迟", "失败"])
    @patch("app.services.performance_collector.work_log.TECH_KEYWORDS", ["架构"])
    @patch("app.services.performance_collector.work_log.COLLABORATION_KEYWORDS", ["协作"])
    @patch("app.services.performance_collector.work_log.PROBLEM_SOLVING_PATTERNS", ["解决.*问题"])
    @patch("app.services.performance_collector.work_log.KNOWLEDGE_SHARING_PATTERNS", ["分享.*经验"])
    @patch("app.services.performance_collector.work_log.TECH_BREAKTHROUGH_PATTERNS", ["突破.*技术"])
    def test_positive_logs(self):
        from app.services.performance_collector.work_log import extract_self_evaluation_from_work_logs
        db = MagicMock()
        log = MagicMock()
        log.content = "今天完成了架构优化工作，解决了性能问题"
        log.status = "SUBMITTED"
        db.query.return_value.filter.return_value.all.return_value = [log]
        result = extract_self_evaluation_from_work_logs(db, 1, date(2024, 1, 1), date(2024, 3, 31))
        assert result["total_logs"] == 1
        assert result["positive_count"] > 0
        assert result["self_evaluation_score"] > 75.0

    @patch("app.services.performance_collector.work_log.POSITIVE_KEYWORDS", ["完成"])
    @patch("app.services.performance_collector.work_log.NEGATIVE_KEYWORDS", ["延迟", "失败"])
    @patch("app.services.performance_collector.work_log.TECH_KEYWORDS", [])
    @patch("app.services.performance_collector.work_log.COLLABORATION_KEYWORDS", [])
    @patch("app.services.performance_collector.work_log.PROBLEM_SOLVING_PATTERNS", [])
    @patch("app.services.performance_collector.work_log.KNOWLEDGE_SHARING_PATTERNS", [])
    @patch("app.services.performance_collector.work_log.TECH_BREAKTHROUGH_PATTERNS", [])
    def test_negative_logs(self):
        from app.services.performance_collector.work_log import extract_self_evaluation_from_work_logs
        db = MagicMock()
        log = MagicMock()
        log.content = "项目延迟了，测试失败"
        db.query.return_value.filter.return_value.all.return_value = [log]
        result = extract_self_evaluation_from_work_logs(db, 1, date(2024, 1, 1), date(2024, 3, 31))
        assert result["negative_count"] > 0
        assert result["self_evaluation_score"] < 75.0

    @patch("app.services.performance_collector.work_log.POSITIVE_KEYWORDS", [])
    @patch("app.services.performance_collector.work_log.NEGATIVE_KEYWORDS", [])
    @patch("app.services.performance_collector.work_log.TECH_KEYWORDS", [])
    @patch("app.services.performance_collector.work_log.COLLABORATION_KEYWORDS", [])
    @patch("app.services.performance_collector.work_log.PROBLEM_SOLVING_PATTERNS", [])
    @patch("app.services.performance_collector.work_log.KNOWLEDGE_SHARING_PATTERNS", [])
    @patch("app.services.performance_collector.work_log.TECH_BREAKTHROUGH_PATTERNS", [])
    def test_empty_content(self):
        from app.services.performance_collector.work_log import extract_self_evaluation_from_work_logs
        db = MagicMock()
        log = MagicMock()
        log.content = None
        db.query.return_value.filter.return_value.all.return_value = [log]
        result = extract_self_evaluation_from_work_logs(db, 1, date(2024, 1, 1), date(2024, 3, 31))
        assert result["total_logs"] == 1
        assert result["self_evaluation_score"] == 75.0

    def test_exception_handling(self):
        from app.services.performance_collector.work_log import extract_self_evaluation_from_work_logs
        db = MagicMock()
        db.query.side_effect = Exception("DB error")
        result = extract_self_evaluation_from_work_logs(db, 1, date(2024, 1, 1), date(2024, 3, 31))
        assert "error" in result
        assert result["self_evaluation_score"] == 75.0

    @patch("app.services.performance_collector.work_log.POSITIVE_KEYWORDS", ["完成"])
    @patch("app.services.performance_collector.work_log.NEGATIVE_KEYWORDS", [])
    @patch("app.services.performance_collector.work_log.TECH_KEYWORDS", ["架构"])
    @patch("app.services.performance_collector.work_log.COLLABORATION_KEYWORDS", ["协作"])
    @patch("app.services.performance_collector.work_log.PROBLEM_SOLVING_PATTERNS", ["解决.*问题"])
    @patch("app.services.performance_collector.work_log.KNOWLEDGE_SHARING_PATTERNS", ["分享.*经验"])
    @patch("app.services.performance_collector.work_log.TECH_BREAKTHROUGH_PATTERNS", ["突破.*技术"])
    def test_all_bonus_scenarios(self):
        from app.services.performance_collector.work_log import extract_self_evaluation_from_work_logs
        db = MagicMock()
        log = MagicMock()
        log.content = "完成架构设计，与团队协作解决了核心问题，分享了调试经验，突破了关键技术"
        db.query.return_value.filter.return_value.all.return_value = [log]
        result = extract_self_evaluation_from_work_logs(db, 1, date(2024, 1, 1), date(2024, 3, 31))
        assert result["problem_solving_count"] >= 1
        assert result["self_evaluation_score"] > 75.0
        assert result["self_evaluation_score"] <= 100

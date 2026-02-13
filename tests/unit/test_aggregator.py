# -*- coding: utf-8 -*-
"""PerformanceDataAggregator 单元测试"""
from datetime import date
from unittest.mock import MagicMock, patch
import pytest

from app.services.performance_collector.aggregator import PerformanceDataAggregator


class TestPerformanceDataAggregator:
    def setup_method(self):
        self.db = MagicMock()
        with patch("app.services.performance_collector.aggregator.WorkLogCollector"), \
             patch("app.services.performance_collector.aggregator.ProjectCollector"), \
             patch("app.services.performance_collector.aggregator.EcnCollector"), \
             patch("app.services.performance_collector.aggregator.BomCollector"), \
             patch("app.services.performance_collector.aggregator.DesignCollector"), \
             patch("app.services.performance_collector.aggregator.KnowledgeCollector"):
            self.agg = PerformanceDataAggregator(self.db)

    def test_collect_all_data_success(self):
        # Mock all collectors to return empty dicts
        self.agg.work_log_collector.extract_self_evaluation_from_work_logs = MagicMock(return_value={"total_logs": 1})
        self.agg.project_collector.collect_task_completion_data = MagicMock(return_value={})
        self.agg.project_collector.collect_project_participation_data = MagicMock(return_value={})
        self.agg.ecn_collector.collect_ecn_responsibility_data = MagicMock(return_value={})
        self.agg.bom_collector.collect_bom_data = MagicMock(return_value={})
        self.agg.design_collector.collect_design_review_data = MagicMock(return_value={})
        self.agg.design_collector.collect_debug_issue_data = MagicMock(return_value={})
        self.agg.knowledge_collector.collect_knowledge_contribution_data = MagicMock(return_value={})

        result = self.agg.collect_all_data(1, date(2024, 1, 1), date(2024, 3, 31))
        assert "data" in result
        assert "statistics" in result
        assert result["statistics"]["success_count"] == 8

    def test_collect_all_data_with_failures(self):
        self.agg.work_log_collector.extract_self_evaluation_from_work_logs = MagicMock(side_effect=Exception("fail"))
        self.agg.project_collector.collect_task_completion_data = MagicMock(return_value={})
        self.agg.project_collector.collect_project_participation_data = MagicMock(return_value={})
        self.agg.ecn_collector.collect_ecn_responsibility_data = MagicMock(return_value={})
        self.agg.bom_collector.collect_bom_data = MagicMock(return_value={})
        self.agg.design_collector.collect_design_review_data = MagicMock(return_value={})
        self.agg.design_collector.collect_debug_issue_data = MagicMock(return_value={})
        self.agg.knowledge_collector.collect_knowledge_contribution_data = MagicMock(return_value={})

        result = self.agg.collect_all_data(1, date(2024, 1, 1), date(2024, 3, 31))
        assert result["statistics"]["failure_count"] == 1
        assert result["statistics"]["success_count"] == 7

    def test_generate_collection_report(self):
        # Mock all collectors
        self.agg.work_log_collector.extract_self_evaluation_from_work_logs = MagicMock(return_value={"total_logs": 0})
        self.agg.project_collector.collect_task_completion_data = MagicMock(return_value={"total_tasks": 0})
        self.agg.project_collector.collect_project_participation_data = MagicMock(return_value={"total_projects": 0})
        self.agg.ecn_collector.collect_ecn_responsibility_data = MagicMock(return_value={})
        self.agg.bom_collector.collect_bom_data = MagicMock(return_value={})
        self.agg.design_collector.collect_design_review_data = MagicMock(return_value={"total_reviews": 0})
        self.agg.design_collector.collect_debug_issue_data = MagicMock(return_value={})
        self.agg.knowledge_collector.collect_knowledge_contribution_data = MagicMock(return_value={})

        report = self.agg.generate_collection_report(1, date(2024, 1, 1), date(2024, 3, 31))
        assert "suggestions" in report
        assert "data_completeness" in report

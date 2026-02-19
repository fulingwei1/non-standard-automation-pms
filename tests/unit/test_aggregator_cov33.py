# -*- coding: utf-8 -*-
"""
第三十三批覆盖率测试 - 绩效数据聚合器 (PerformanceDataAggregator)
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date

try:
    from app.services.performance_collector.aggregator import PerformanceDataAggregator
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="aggregator 导入失败")


def _make_aggregator():
    """构造带 mock 子收集器的聚合器（绕过__init__）"""
    aggregator = object.__new__(PerformanceDataAggregator)
    aggregator.db = MagicMock()

    # 直接设置 mock 收集器
    aggregator.work_log_collector = MagicMock()
    aggregator.project_collector = MagicMock()
    aggregator.ecn_collector = MagicMock()
    aggregator.bom_collector = MagicMock()
    aggregator.design_collector = MagicMock()
    aggregator.knowledge_collector = MagicMock()
    return aggregator


def _setup_all_collectors(aggregator, self_eval=None, task=None, project=None,
                           ecn=None, bom=None, design_review=None,
                           debug=None, knowledge=None):
    """为所有收集器设置返回值"""
    aggregator.work_log_collector.extract_self_evaluation_from_work_logs.return_value = self_eval or {}
    aggregator.project_collector.collect_task_completion_data.return_value = task or {}
    aggregator.project_collector.collect_project_participation_data.return_value = project or {}
    aggregator.ecn_collector.collect_ecn_responsibility_data.return_value = ecn or {}
    aggregator.bom_collector.collect_bom_data.return_value = bom or {}
    aggregator.design_collector.collect_design_review_data.return_value = design_review or {}
    aggregator.design_collector.collect_debug_issue_data.return_value = debug or {}
    aggregator.knowledge_collector.collect_knowledge_contribution_data.return_value = knowledge or {}


class TestCollectAllData:
    def test_returns_required_keys(self):
        """结果包含必要的顶层键"""
        aggregator = _make_aggregator()
        _setup_all_collectors(aggregator)

        result = aggregator.collect_all_data(
            engineer_id=1,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31)
        )

        assert "data" in result
        assert "statistics" in result
        assert "engineer_id" in result
        assert result["engineer_id"] == 1

    def test_success_rate_calculation(self):
        """所有收集器成功时成功率为100%"""
        aggregator = _make_aggregator()
        _setup_all_collectors(
            aggregator,
            self_eval={"total_logs": 5},
            task={"total_tasks": 3},
            project={"total_projects": 2},
        )

        result = aggregator.collect_all_data(
            engineer_id=2,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31)
        )

        stats = result["statistics"]
        assert stats["success_rate"] == 100.0
        assert stats["success_count"] == 8

    def test_exception_in_collector_captured(self):
        """某个收集器抛出异常时不影响其他收集器"""
        aggregator = _make_aggregator()
        aggregator.work_log_collector.extract_self_evaluation_from_work_logs.side_effect = RuntimeError("DB连接失败")
        aggregator.project_collector.collect_task_completion_data.return_value = {"total_tasks": 1}
        aggregator.project_collector.collect_project_participation_data.return_value = {}
        aggregator.ecn_collector.collect_ecn_responsibility_data.return_value = {}
        aggregator.bom_collector.collect_bom_data.return_value = {}
        aggregator.design_collector.collect_design_review_data.return_value = {}
        aggregator.design_collector.collect_debug_issue_data.return_value = {}
        aggregator.knowledge_collector.collect_knowledge_contribution_data.return_value = {}

        result = aggregator.collect_all_data(
            engineer_id=3,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31)
        )

        stats = result["statistics"]
        assert stats["failure_count"] == 1
        assert len(stats["errors"]) == 1
        assert stats["errors"][0]["source"] == "self_evaluation"

    def test_empty_result_added_to_missing(self):
        """返回空dict的数据源被加入missing列表"""
        aggregator = _make_aggregator()
        _setup_all_collectors(aggregator)  # 全部返回空dict

        result = aggregator.collect_all_data(
            engineer_id=4,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31)
        )

        stats = result["statistics"]
        assert len(stats["missing_data_sources"]) == 8  # 全部为空

    def test_date_range_included_in_result(self):
        """结果包含日期范围"""
        aggregator = _make_aggregator()
        _setup_all_collectors(aggregator)

        result = aggregator.collect_all_data(
            engineer_id=5,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31)
        )

        assert result["start_date"] == "2026-01-01"
        assert result["end_date"] == "2026-01-31"


class TestGenerateCollectionReport:
    def test_report_has_required_keys(self):
        """采集报告包含必要的键"""
        aggregator = _make_aggregator()
        _setup_all_collectors(
            aggregator,
            self_eval={"total_logs": 0},
            task={"total_tasks": 0},
            project={"total_projects": 0},
            design_review={"total_reviews": 0},
        )

        report = aggregator.generate_collection_report(
            engineer_id=5,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31)
        )

        assert "engineer_id" in report
        assert "period" in report
        assert "data_completeness" in report
        assert "suggestions" in report
        assert "missing_data_analysis" in report

    def test_report_suggestions_when_no_logs(self):
        """无工作日志时生成建议"""
        aggregator = _make_aggregator()
        _setup_all_collectors(
            aggregator,
            self_eval={"total_logs": 0},
            task={"total_tasks": 2},
            project={"total_projects": 1},
            design_review={"total_reviews": 1},
        )

        report = aggregator.generate_collection_report(
            engineer_id=6,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31)
        )

        assert len(report["suggestions"]) > 0
        assert any("工作日志" in s for s in report["suggestions"])

    def test_data_completeness_score_non_zero(self):
        """有数据时完整性分数不为0"""
        aggregator = _make_aggregator()
        _setup_all_collectors(
            aggregator,
            self_eval={"total_logs": 5},
            task={"total_tasks": 3},
            project={"total_projects": 2},
            ecn={"total_ecns": 1},
        )

        report = aggregator.generate_collection_report(
            engineer_id=7,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31)
        )

        assert report["data_completeness"]["score"] > 0

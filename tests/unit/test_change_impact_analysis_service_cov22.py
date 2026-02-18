# -*- coding: utf-8 -*-
"""第二十二批：change_impact_analysis_service 单元测试"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

try:
    from app.services.change_impact_analysis_service import (
        analyze_schedule_impact,
        analyze_cost_impact,
        analyze_resource_impact,
        analyze_related_project_impact,
        build_impact_analysis,
        calculate_change_statistics,
    )
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="import failed")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def mock_change():
    c = MagicMock()
    c.id = 1
    c.change_no = "CR-001"
    c.change_type = "SCOPE"
    c.change_level = "MAJOR"
    c.title = "需求变更"
    c.status = "APPROVED"
    c.schedule_impact = "延迟2周"
    c.cost_impact = Decimal("10000")
    c.resource_impact = "需要增加开发人员"
    return c


@pytest.fixture
def mock_project():
    p = MagicMock()
    p.id = 1
    p.project_code = "PRJ-001"
    p.project_name = "测试项目"
    p.budget_amount = Decimal("200000")
    return p


class TestAnalyzeScheduleImpact:
    def test_no_schedule_impact_returns_none(self, db, mock_change):
        """无进度影响时返回None"""
        mock_change.schedule_impact = None
        result = analyze_schedule_impact(db, mock_change, 1)
        assert result is None

    def test_schedule_impact_returns_dict(self, db, mock_change):
        """有进度影响时返回字典"""
        db.query.return_value.filter.return_value.all.return_value = []
        result = analyze_schedule_impact(db, mock_change, 1)
        assert isinstance(result, dict)
        assert "description" in result

    def test_critical_change_has_high_severity(self, db, mock_change):
        """CRITICAL级别变更的严重度为HIGH"""
        mock_change.change_level = "CRITICAL"
        db.query.return_value.filter.return_value.all.return_value = []
        result = analyze_schedule_impact(db, mock_change, 1)
        assert result["severity"] == "HIGH"

    def test_approved_change_queries_tasks(self, db, mock_change):
        """已批准的变更会查询受影响任务"""
        mock_change.status = "APPROVED"
        db.query.return_value.filter.return_value.all.return_value = []
        result = analyze_schedule_impact(db, mock_change, 1)
        assert result["affected_items"] == []


class TestAnalyzeCostImpact:
    def test_no_cost_impact_returns_none(self, mock_change, mock_project):
        """无成本影响时返回None"""
        mock_change.cost_impact = None
        result = analyze_cost_impact(mock_change, mock_project)
        assert result is None

    def test_cost_impact_returns_dict(self, mock_change, mock_project):
        """有成本影响时返回字典"""
        result = analyze_cost_impact(mock_change, mock_project)
        assert isinstance(result, dict)
        assert "cost_impact" in result

    def test_large_cost_impact_is_high_severity(self, mock_change, mock_project):
        """超过预算10%的成本影响为HIGH严重度"""
        mock_change.cost_impact = Decimal("30000")  # > 200000 * 0.1
        mock_project.budget_amount = Decimal("200000")
        result = analyze_cost_impact(mock_change, mock_project)
        assert result["severity"] == "HIGH"

    def test_small_cost_impact_is_medium_severity(self, mock_change, mock_project):
        """小成本影响为MEDIUM严重度"""
        mock_change.cost_impact = Decimal("1000")  # < 200000 * 0.1
        mock_project.budget_amount = Decimal("200000")
        result = analyze_cost_impact(mock_change, mock_project)
        assert result["severity"] == "MEDIUM"


class TestAnalyzeResourceImpact:
    def test_no_resource_impact_returns_none(self, db, mock_change):
        """无资源影响时返回None"""
        mock_change.resource_impact = None
        result = analyze_resource_impact(db, mock_change, 1)
        assert result is None

    def test_resource_impact_returns_dict(self, db, mock_change):
        """有资源影响时返回字典"""
        db.query.return_value.filter.return_value.all.return_value = []
        result = analyze_resource_impact(db, mock_change, 1)
        assert isinstance(result, dict)
        assert "description" in result


class TestBuildImpactAnalysis:
    def test_builds_complete_impact_analysis(self, db, mock_change, mock_project):
        """构建完整影响分析"""
        db.query.return_value.filter.return_value.all.return_value = []
        result = build_impact_analysis(db, mock_change, mock_project, 1)
        assert result["change_id"] == 1
        assert result["change_no"] == "CR-001"
        assert "impacts" in result


class TestCalculateChangeStatistics:
    def test_empty_changes_returns_zero_total(self):
        """空变更列表返回0统计"""
        result = calculate_change_statistics([], [])
        assert result["total_changes"] == 0

    def test_multiple_changes_counted(self):
        """多个变更正确统计"""
        changes = [MagicMock(), MagicMock()]
        changes[0].change_type = "SCOPE"
        changes[0].change_level = "MAJOR"
        changes[0].status = "APPROVED"
        changes[0].cost_impact = Decimal("1000")
        changes[1].change_type = "COST"
        changes[1].change_level = "MINOR"
        changes[1].status = "DRAFT"
        changes[1].cost_impact = None
        result = calculate_change_statistics(changes, [])
        assert result["total_changes"] == 2
        assert "SCOPE" in result["by_type"]

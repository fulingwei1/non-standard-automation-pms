# -*- coding: utf-8 -*-
"""
ChangeImpactAnalysisService 综合单元测试

测试覆盖:
- analyze_schedule_impact: 分析进度影响
- analyze_cost_impact: 分析成本影响
- analyze_resource_impact: 分析资源影响
- analyze_related_project_impact: 分析关联项目影响
- build_impact_analysis: 构建变更影响分析
- calculate_change_statistics: 计算变更统计信息
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestAnalyzeScheduleImpact:
    """测试 analyze_schedule_impact 函数"""

    def test_returns_none_when_no_schedule_impact(self):
        """测试无进度影响时返回None"""
        from app.services.change_impact_analysis_service import analyze_schedule_impact

        mock_db = MagicMock()
        mock_change = MagicMock()
        mock_change.schedule_impact = None

        result = analyze_schedule_impact(mock_db, mock_change, project_id=1)

        assert result is None

    def test_returns_impact_when_schedule_impact_exists(self):
        """测试有进度影响时返回结果"""
        from app.services.change_impact_analysis_service import analyze_schedule_impact

        mock_db = MagicMock()
        mock_change = MagicMock()
        mock_change.schedule_impact = "预计延期2周"
        mock_change.change_level = "CRITICAL"
        mock_change.status = "DRAFT"

        result = analyze_schedule_impact(mock_db, mock_change, project_id=1)

        assert result is not None
        assert result["description"] == "预计延期2周"
        assert result["severity"] == "HIGH"

    def test_returns_high_severity_for_critical_change(self):
        """测试关键变更返回高严重性"""
        from app.services.change_impact_analysis_service import analyze_schedule_impact

        mock_db = MagicMock()
        mock_change = MagicMock()
        mock_change.schedule_impact = "测试影响"
        mock_change.change_level = "CRITICAL"
        mock_change.status = "DRAFT"

        result = analyze_schedule_impact(mock_db, mock_change, project_id=1)

        assert result["severity"] == "HIGH"

    def test_returns_medium_severity_for_non_critical_change(self):
        """测试非关键变更返回中等严重性"""
        from app.services.change_impact_analysis_service import analyze_schedule_impact

        mock_db = MagicMock()
        mock_change = MagicMock()
        mock_change.schedule_impact = "测试影响"
        mock_change.change_level = "MINOR"
        mock_change.status = "DRAFT"

        result = analyze_schedule_impact(mock_db, mock_change, project_id=1)

        assert result["severity"] == "MEDIUM"

    def test_includes_affected_tasks_when_approved(self):
        """测试已批准时包含受影响任务"""
        from app.services.change_impact_analysis_service import analyze_schedule_impact

        mock_db = MagicMock()
        mock_change = MagicMock()
        mock_change.schedule_impact = "测试影响"
        mock_change.change_level = "MINOR"
        mock_change.status = "APPROVED"

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.task_name = "任务1"
        mock_task.plan_start = date.today()
        mock_task.plan_end = date.today()

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_task]

        result = analyze_schedule_impact(mock_db, mock_change, project_id=1)

        assert len(result["affected_items"]) == 1
        assert result["affected_items"][0]["task_id"] == 1


class TestAnalyzeCostImpact:
    """测试 analyze_cost_impact 函数"""

    def test_returns_none_when_no_cost_impact(self):
        """测试无成本影响时返回None"""
        from app.services.change_impact_analysis_service import analyze_cost_impact

        mock_change = MagicMock()
        mock_change.cost_impact = None

        mock_project = MagicMock()

        result = analyze_cost_impact(mock_change, mock_project)

        assert result is None

    def test_returns_impact_when_cost_impact_exists(self):
        """测试有成本影响时返回结果"""
        from app.services.change_impact_analysis_service import analyze_cost_impact

        mock_change = MagicMock()
        mock_change.cost_impact = Decimal("50000")

        mock_project = MagicMock()
        mock_project.budget_amount = Decimal("100000")

        result = analyze_cost_impact(mock_change, mock_project)

        assert result is not None
        assert result["cost_impact"] == 50000.0

    def test_returns_high_severity_for_large_impact(self):
        """测试大额影响返回高严重性"""
        from app.services.change_impact_analysis_service import analyze_cost_impact

        mock_change = MagicMock()
        mock_change.cost_impact = Decimal("20000")  # 超过预算的10%

        mock_project = MagicMock()
        mock_project.budget_amount = Decimal("100000")

        result = analyze_cost_impact(mock_change, mock_project)

        assert result["severity"] == "HIGH"

    def test_returns_medium_severity_for_small_impact(self):
        """测试小额影响返回中等严重性"""
        from app.services.change_impact_analysis_service import analyze_cost_impact

        mock_change = MagicMock()
        mock_change.cost_impact = Decimal("5000")  # 小于预算的10%

        mock_project = MagicMock()
        mock_project.budget_amount = Decimal("100000")

        result = analyze_cost_impact(mock_change, mock_project)

        assert result["severity"] == "MEDIUM"


class TestAnalyzeResourceImpact:
    """测试 analyze_resource_impact 函数"""

    def test_returns_none_when_no_resource_impact(self):
        """测试无资源影响时返回None"""
        from app.services.change_impact_analysis_service import analyze_resource_impact

        mock_db = MagicMock()
        mock_change = MagicMock()
        mock_change.resource_impact = None

        result = analyze_resource_impact(mock_db, mock_change, project_id=1)

        assert result is None

    def test_returns_impact_when_resource_impact_exists(self):
        """测试有资源影响时返回结果"""
        from app.services.change_impact_analysis_service import analyze_resource_impact

        mock_db = MagicMock()
        mock_change = MagicMock()
        mock_change.resource_impact = "需要增加2名开发人员"
        mock_change.status = "DRAFT"

        result = analyze_resource_impact(mock_db, mock_change, project_id=1)

        assert result is not None
        assert result["description"] == "需要增加2名开发人员"
        assert result["severity"] == "MEDIUM"

    def test_includes_affected_resources_when_approved(self):
        """测试已批准时包含受影响资源"""
        from app.services.change_impact_analysis_service import analyze_resource_impact

        mock_db = MagicMock()
        mock_change = MagicMock()
        mock_change.resource_impact = "测试影响"
        mock_change.status = "APPROVED"

        mock_allocation = MagicMock()
        mock_allocation.id = 1
        mock_allocation.resource_name = "张三"
        mock_allocation.allocation_percent = 50
        mock_allocation.start_date = date.today()
        mock_allocation.end_date = date.today()

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_allocation]

        result = analyze_resource_impact(mock_db, mock_change, project_id=1)

        assert len(result["affected_resources"]) == 1
        assert result["affected_resources"][0]["resource_name"] == "张三"


class TestAnalyzeRelatedProjectImpact:
    """测试 analyze_related_project_impact 函数"""

    def test_returns_empty_when_no_resource_impact(self):
        """测试无资源影响时返回空"""
        from app.services.change_impact_analysis_service import analyze_related_project_impact

        mock_db = MagicMock()
        mock_change = MagicMock()
        mock_change.resource_impact = None
        mock_change.status = "APPROVED"

        result = analyze_related_project_impact(mock_db, mock_change, project_id=1)

        assert result["affected_projects"] == []
        assert result["count"] == 0

    def test_returns_empty_when_not_approved(self):
        """测试未批准时返回空"""
        from app.services.change_impact_analysis_service import analyze_related_project_impact

        mock_db = MagicMock()
        mock_change = MagicMock()
        mock_change.resource_impact = "测试影响"
        mock_change.status = "DRAFT"

        result = analyze_related_project_impact(mock_db, mock_change, project_id=1)

        assert result["affected_projects"] == []

    def test_finds_related_projects_with_shared_resources(self):
        """测试找到共享资源的关联项目"""
        from app.services.change_impact_analysis_service import analyze_related_project_impact

        mock_db = MagicMock()
        mock_change = MagicMock()
        mock_change.resource_impact = "测试影响"
        mock_change.status = "APPROVED"

        # Mock project resources
        mock_allocation = MagicMock()
        mock_allocation.resource_id = 1

        # Mock shared projects
        mock_related_project = MagicMock()
        mock_related_project.id = 2
        mock_related_project.project_code = "PJ002"
        mock_related_project.project_name = "关联项目"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_allocation]
        mock_db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [(2,)]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_related_project

        result = analyze_related_project_impact(mock_db, mock_change, project_id=1)

        assert len(result["affected_projects"]) == 1
        assert result["affected_projects"][0]["project_name"] == "关联项目"


class TestBuildImpactAnalysis:
    """测试 build_impact_analysis 函数"""

    def test_builds_complete_impact_analysis(self):
        """测试构建完整的影响分析"""
        from app.services.change_impact_analysis_service import build_impact_analysis

        mock_db = MagicMock()
        mock_change = MagicMock()
        mock_change.id = 1
        mock_change.change_no = "CHG001"
        mock_change.change_type = "SCOPE"
        mock_change.change_level = "CRITICAL"
        mock_change.title = "测试变更"
        mock_change.status = "DRAFT"
        mock_change.schedule_impact = "延期1周"
        mock_change.cost_impact = Decimal("10000")
        mock_change.resource_impact = "增加1人"

        mock_project = MagicMock()
        mock_project.budget_amount = Decimal("100000")

        result = build_impact_analysis(mock_db, mock_change, mock_project, project_id=1)

        assert result["change_id"] == 1
        assert result["change_no"] == "CHG001"
        assert "impacts" in result

    def test_includes_schedule_impact_when_present(self):
        """测试包含进度影响"""
        from app.services.change_impact_analysis_service import build_impact_analysis

        mock_db = MagicMock()
        mock_change = MagicMock()
        mock_change.id = 1
        mock_change.change_no = "CHG001"
        mock_change.change_type = "SCOPE"
        mock_change.change_level = "MINOR"
        mock_change.title = "测试变更"
        mock_change.status = "DRAFT"
        mock_change.schedule_impact = "延期1周"
        mock_change.cost_impact = None
        mock_change.resource_impact = None

        mock_project = MagicMock()

        result = build_impact_analysis(mock_db, mock_change, mock_project, project_id=1)

        assert "schedule" in result["impacts"]

    def test_excludes_impacts_when_not_present(self):
        """测试不包含空影响"""
        from app.services.change_impact_analysis_service import build_impact_analysis

        mock_db = MagicMock()
        mock_change = MagicMock()
        mock_change.id = 1
        mock_change.change_no = "CHG001"
        mock_change.change_type = "SCOPE"
        mock_change.change_level = "MINOR"
        mock_change.title = "测试变更"
        mock_change.status = "DRAFT"
        mock_change.schedule_impact = None
        mock_change.cost_impact = None
        mock_change.resource_impact = None

        mock_project = MagicMock()

        result = build_impact_analysis(mock_db, mock_change, mock_project, project_id=1)

        assert "schedule" not in result["impacts"]
        assert "cost" not in result["impacts"]
        assert "resource" not in result["impacts"]


class TestCalculateChangeStatistics:
    """测试 calculate_change_statistics 函数"""

    def test_returns_zero_statistics_when_no_changes(self):
        """测试无变更时返回零统计"""
        from app.services.change_impact_analysis_service import calculate_change_statistics

        result = calculate_change_statistics([], [])

        assert result["total_changes"] == 0
        assert result["total_cost_impact"] == 0

    def test_counts_changes_by_type(self):
        """测试按类型统计变更"""
        from app.services.change_impact_analysis_service import calculate_change_statistics

        mock_change1 = MagicMock()
        mock_change1.change_type = "SCOPE"
        mock_change1.change_level = "MINOR"
        mock_change1.status = "APPROVED"
        mock_change1.cost_impact = None

        mock_change2 = MagicMock()
        mock_change2.change_type = "SCOPE"
        mock_change2.change_level = "MAJOR"
        mock_change2.status = "DRAFT"
        mock_change2.cost_impact = None

        mock_change3 = MagicMock()
        mock_change3.change_type = "SCHEDULE"
        mock_change3.change_level = "MINOR"
        mock_change3.status = "APPROVED"
        mock_change3.cost_impact = None

        changes = [mock_change1, mock_change2, mock_change3]

        result = calculate_change_statistics(changes, [])

        assert result["by_type"]["SCOPE"] == 2
        assert result["by_type"]["SCHEDULE"] == 1

    def test_counts_changes_by_level(self):
        """测试按级别统计变更"""
        from app.services.change_impact_analysis_service import calculate_change_statistics

        mock_change1 = MagicMock()
        mock_change1.change_type = "SCOPE"
        mock_change1.change_level = "MINOR"
        mock_change1.status = "APPROVED"
        mock_change1.cost_impact = None

        mock_change2 = MagicMock()
        mock_change2.change_type = "SCOPE"
        mock_change2.change_level = "MAJOR"
        mock_change2.status = "DRAFT"
        mock_change2.cost_impact = None

        changes = [mock_change1, mock_change2]

        result = calculate_change_statistics(changes, [])

        assert result["by_level"]["MINOR"] == 1
        assert result["by_level"]["MAJOR"] == 1

    def test_counts_changes_by_status(self):
        """测试按状态统计变更"""
        from app.services.change_impact_analysis_service import calculate_change_statistics

        mock_change1 = MagicMock()
        mock_change1.change_type = "SCOPE"
        mock_change1.change_level = "MINOR"
        mock_change1.status = "APPROVED"
        mock_change1.cost_impact = None

        mock_change2 = MagicMock()
        mock_change2.change_type = "SCOPE"
        mock_change2.change_level = "MINOR"
        mock_change2.status = "DRAFT"
        mock_change2.cost_impact = None

        mock_change3 = MagicMock()
        mock_change3.change_type = "SCOPE"
        mock_change3.change_level = "MINOR"
        mock_change3.status = "APPROVED"
        mock_change3.cost_impact = None

        changes = [mock_change1, mock_change2, mock_change3]

        result = calculate_change_statistics(changes, [])

        assert result["by_status"]["APPROVED"] == 2
        assert result["by_status"]["DRAFT"] == 1

    def test_sums_total_cost_impact(self):
        """测试汇总总成本影响"""
        from app.services.change_impact_analysis_service import calculate_change_statistics

        mock_change1 = MagicMock()
        mock_change1.change_type = "SCOPE"
        mock_change1.change_level = "MINOR"
        mock_change1.status = "APPROVED"
        mock_change1.cost_impact = Decimal("10000")

        mock_change2 = MagicMock()
        mock_change2.change_type = "SCOPE"
        mock_change2.change_level = "MINOR"
        mock_change2.status = "APPROVED"
        mock_change2.cost_impact = Decimal("-5000")

        mock_change3 = MagicMock()
        mock_change3.change_type = "SCOPE"
        mock_change3.change_level = "MINOR"
        mock_change3.status = "APPROVED"
        mock_change3.cost_impact = None

        changes = [mock_change1, mock_change2, mock_change3]

        result = calculate_change_statistics(changes, [])

        assert result["total_cost_impact"] == 15000  # 10000 + 5000 (abs)

    def test_counts_affected_projects(self):
        """测试统计受影响项目数"""
        from app.services.change_impact_analysis_service import calculate_change_statistics

        mock_change = MagicMock()
        mock_change.change_type = "SCOPE"
        mock_change.change_level = "MINOR"
        mock_change.status = "APPROVED"
        mock_change.cost_impact = None

        impact_analysis = [
            {
                "impacts": {
                    "related_projects": {
                        "affected_projects": [
                            {"project_id": 1},
                            {"project_id": 2},
                        ]
                    }
                }
            },
            {
                "impacts": {
                    "related_projects": {
                        "affected_projects": [
                            {"project_id": 2},  # Duplicate
                            {"project_id": 3},
                        ]
                    }
                }
            },
        ]

        result = calculate_change_statistics([mock_change], impact_analysis)

        assert result["affected_projects_count"] == 3  # Unique: 1, 2, 3

    def test_handles_missing_fields(self):
        """测试处理缺失字段"""
        from app.services.change_impact_analysis_service import calculate_change_statistics

        mock_change = MagicMock()
        mock_change.change_type = None
        mock_change.change_level = None
        mock_change.status = None
        mock_change.cost_impact = None

        result = calculate_change_statistics([mock_change], [])

        assert result["by_type"]["OTHER"] == 1
        assert result["by_level"]["MINOR"] == 1
        assert result["by_status"]["DRAFT"] == 1

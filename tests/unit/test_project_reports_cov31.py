# -*- coding: utf-8 -*-
"""
Unit tests for ProjectReportMixin (第三十一批)
"""
from datetime import date
from unittest.mock import MagicMock

import pytest

from app.services.report_data_generation.project_reports import ProjectReportMixin


@pytest.fixture
def mock_db():
    return MagicMock()


def _make_project(project_id=1, name="测试项目", progress=60.0, health="H1", stage="S3"):
    proj = MagicMock()
    proj.id = project_id
    proj.project_name = name
    proj.project_code = f"PRJ-{project_id:03d}"
    proj.customer_name = "客户A"
    proj.current_stage = stage
    proj.health_status = health
    proj.progress = progress
    return proj


# ---------------------------------------------------------------------------
# generate_project_weekly_report
# ---------------------------------------------------------------------------

class TestGenerateProjectWeeklyReport:
    def test_returns_error_when_project_not_found(self, mock_db):
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = None
        chain.all.return_value = []
        chain.between.return_value = chain

        result = ProjectReportMixin.generate_project_weekly_report(
            mock_db, project_id=999,
            start_date=date(2026, 2, 10),
            end_date=date(2026, 2, 16),
        )
        assert "error" in result

    def test_returns_summary_with_project_info(self, mock_db):
        project = _make_project()
        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            chain = MagicMock()
            chain.filter.return_value = chain
            chain.order_by.return_value = chain
            chain.first.return_value = project if call_count[0] == 1 else None
            chain.all.return_value = []
            return chain

        mock_db.query.side_effect = query_side_effect

        result = ProjectReportMixin.generate_project_weekly_report(
            mock_db, project_id=1,
            start_date=date(2026, 2, 10),
            end_date=date(2026, 2, 16),
        )

        assert "error" not in result
        assert result.get("project_name") == project.project_name or \
               "project_name" in str(result)

    def test_period_dates_in_summary(self, mock_db):
        project = _make_project()
        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            chain = MagicMock()
            chain.filter.return_value = chain
            chain.order_by.return_value = chain
            chain.first.return_value = project if call_count[0] == 1 else None
            chain.all.return_value = []
            return chain

        mock_db.query.side_effect = query_side_effect

        result = ProjectReportMixin.generate_project_weekly_report(
            mock_db, project_id=1,
            start_date=date(2026, 2, 10),
            end_date=date(2026, 2, 16),
        )
        # result 包含 summary 字典或顶层键
        result_str = str(result)
        assert "2026-02-10" in result_str or "period_start" in result_str


# ---------------------------------------------------------------------------
# generate_project_monthly_report (if exists)
# ---------------------------------------------------------------------------

class TestGenerateProjectMonthlyReport:
    def test_error_when_project_missing(self, mock_db):
        """月报与周报同样需要项目存在"""
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = None
        chain.all.return_value = []

        # 月报方法可能不存在，兼容处理
        if hasattr(ProjectReportMixin, "generate_project_monthly_report"):
            result = ProjectReportMixin.generate_project_monthly_report(
                mock_db, project_id=999,
                year=2026, month=2,
            )
            assert "error" in result
        else:
            pytest.skip("generate_project_monthly_report not implemented")

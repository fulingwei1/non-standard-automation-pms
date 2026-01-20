# -*- coding: utf-8 -*-
"""
Tests for template_report_service
Covers: app/services/template_report_service.py
Coverage Target: 0% -> 60%+
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session


class TestTemplateReportService:
    """模板报表服务测试"""

    @pytest.fixture
    def mock_template(self):
        """模拟报表模板"""
        mock = MagicMock()
        mock.id = 1
        mock.template_code = "TPL001"
        mock.template_name = "项目周报模板"
        mock.report_type = "PROJECT_WEEKLY"
        mock.sections = {"summary": True, "milestones": True}
        mock.metrics_config = {"cost": True, "progress": True}
        return mock

    def test_generate_from_template_project_weekly(
        self, db_session: Session, mock_template
    ):
        """测试生成项目周报"""
        from app.services.template_report_service import TemplateReportService

        with patch.object(
            TemplateReportService, '_generate_project_weekly',
            return_value={"sections": {"summary": {}}, "metrics": {}, "charts": []}
        ):
            result = TemplateReportService.generate_from_template(
                db_session, mock_template,
                project_id=1,
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 31)
            )

            assert result is not None
            assert result["template_id"] == 1
            assert result["template_code"] == "TPL001"
            assert result["report_type"] == "PROJECT_WEEKLY"

    def test_generate_from_template_project_monthly(
        self, db_session: Session, mock_template
    ):
        """测试生成项目月报"""
        from app.services.template_report_service import TemplateReportService

        mock_template.report_type = "PROJECT_MONTHLY"

        with patch.object(
            TemplateReportService, '_generate_project_monthly',
            return_value={"sections": {"summary": {}}, "metrics": {}, "charts": []}
        ):
            result = TemplateReportService.generate_from_template(
                db_session, mock_template,
                project_id=1,
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 31)
            )

            assert result is not None
            assert result["report_type"] == "PROJECT_MONTHLY"

    def test_generate_from_template_cost_report(
        self, db_session: Session, mock_template
    ):
        """测试生成成本报表"""
        from app.services.template_report_service import TemplateReportService

        mock_template.report_type = "COST_REPORT"

        with patch.object(
            TemplateReportService, '_generate_cost_report',
            return_value={"sections": {"cost": {}}, "metrics": {}, "charts": []}
        ):
            result = TemplateReportService.generate_from_template(
                db_session, mock_template,
                project_id=1,
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 31)
            )

            assert result is not None
            assert result["report_type"] == "COST_REPORT"

    def test_generate_from_template_with_department(
        self, db_session: Session, mock_template
    ):
        """测试带部门参数的报表生成"""
        from app.services.template_report_service import TemplateReportService

        with patch.object(
            TemplateReportService, '_generate_project_weekly',
            return_value={"sections": {}, "metrics": {}, "charts": []}
        ):
            result = TemplateReportService.generate_from_template(
                db_session, mock_template,
                department_id=1,
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 31)
            )

            assert result is not None

    def test_generate_from_template_with_filters(
        self, db_session: Session, mock_template
    ):
        """测试带过滤条件的报表生成"""
        from app.services.template_report_service import TemplateReportService

        filters = {"status": "IN_PROGRESS", "priority": "HIGH"}

        with patch.object(
            TemplateReportService, '_generate_project_weekly',
            return_value={"sections": {}, "metrics": {}, "charts": []}
        ):
            result = TemplateReportService.generate_from_template(
                db_session, mock_template,
                filters=filters,
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 31)
            )

            assert result is not None

    def test_generate_from_template_default_dates(
        self, db_session: Session, mock_template
    ):
        """测试默认日期范围"""
        from app.services.template_report_service import TemplateReportService

        with patch.object(
            TemplateReportService, '_generate_project_weekly',
            return_value={"sections": {}, "metrics": {}, "charts": []}
        ):
            result = TemplateReportService.generate_from_template(
                db_session, mock_template,
                project_id=1
            )

            assert result is not None
            assert "period" in result
            assert "start_date" in result["period"]
            assert "end_date" in result["period"]

    def test_get_template_list(self, db_session: Session):
        """测试获取模板列表"""
        from app.services.template_report_service import TemplateReportService

        mock_templates = [MagicMock(id=1), MagicMock(id=2)]

        db_session.query.return_value.filter.return_value.all.return_value = mock_templates

        result = TemplateReportService.get_template_list(db_session)

        assert result == mock_templates
        db_session.query.assert_called()

    def test_get_template_by_id(self, db_session: Session, mock_template):
        """测试按ID获取模板"""
        from app.services.template_report_service import TemplateReportService

        db_session.query.return_value.filter.return_value.first.return_value = mock_template

        result = TemplateReportService.get_template_by_id(db_session, 1)

        assert result == mock_template

    def test_get_template_by_id_not_found(self, db_session: Session):
        """测试模板不存在"""
        from app.services.template_report_service import TemplateReportService

        db_session.query.return_value.filter.return_value.first.return_value = None

        result = TemplateReportService.get_template_by_id(db_session, 999)

        assert result is None


class TestTemplateReportServiceHelpers:
    """模板报表服务辅助方法测试"""

    def test_generate_project_weekly_structure(self, db_session: Session):
        """测试项目周报结构"""
        from app.services.template_report_service import TemplateReportService

        sections_config = {"summary": True, "milestones": True}
        metrics_config = {"cost": True, "progress": True}

        with patch('app.services.template_report_service.db.query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = None
            mock_query.return_value.join.return_value.filter.return_value.all.return_value = []

            result = TemplateReportService._generate_project_weekly(
                db_session, 1, date(2025, 1, 1), date(2025, 1, 31),
                sections_config, metrics_config
            )

            assert result is not None
            assert "sections" in result
            assert "metrics" in result
            assert "charts" in result

    def test_generate_project_monthly_structure(self, db_session: Session):
        """测试项目月报结构"""
        from app.services.template_report_service import TemplateReportService

        with patch('app.services.template_report_service.db.query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = None
            mock_query.return_value.join.return_value.filter.return_value.all.return_value = []

            result = TemplateReportService._generate_project_monthly(
                db_session, 1, date(2025, 1, 1), date(2025, 1, 31), {}, {}
            )

            assert result is not None
            assert "sections" in result

    def test_generate_cost_report_structure(self, db_session: Session):
        """测试成本报表结构"""
        from app.services.template_report_service import TemplateReportService

        with patch('app.services.template_report_service.db.query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = None
            mock_query.return_value.join.return_value.filter.return_value.all.return_value = []

            result = TemplateReportService._generate_cost_report(
                db_session, 1, date(2025, 1, 1), date(2025, 1, 31), {}, {}
            )

            assert result is not None

    def test_get_report_types(self, db_session: Session):
        """测试获取报表类型列表"""
        from app.services.template_report_service import TemplateReportService

        result = TemplateReportService.get_report_types()

        assert isinstance(result, list)
        assert len(result) > 0
        assert any(rt["type"] == "PROJECT_WEEKLY" for rt in result)
        assert any(rt["type"] == "PROJECT_MONTHLY" for rt in result)
        assert any(rt["type"] == "COST_REPORT" for rt in result)

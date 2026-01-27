# -*- coding: utf-8 -*-
"""
Tests for TemplateReportDataService
"""

from datetime import date
from unittest.mock import patch

from app.models.report_center import ReportTemplate
from app.services.template_report_data_service import TemplateReportDataService


def _create_template(db_session) -> ReportTemplate:
    template = ReportTemplate(
        template_code="TPL-CTX-001",
        template_name="上下文测试模板",
        report_type="PROJECT_WEEKLY",
        is_active=True,
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


def test_build_context_with_mocked_report(db_session):
    """确保数据服务能正确转换模板报表数据"""
    template = _create_template(db_session)
    service = TemplateReportDataService(db_session)

    fake_report = {
        "template_id": template.id,
        "template_code": template.template_code,
        "template_name": template.template_name,
        "report_type": template.report_type,
        "period": {"start_date": "2026-01-01", "end_date": "2026-01-31"},
        "metrics": {
        "total_hours": 120.5,
        "active_members": 8,
        },
        "sections": {
        "milestones": {
        "title": "里程碑",
        "type": "table",
        "data": [
        {"name": "M1", "status": "COMPLETED"},
        {"name": "M2", "status": "IN_PROGRESS"},
        ],
        },
        "timesheet": {
        "title": "工时汇总",
        "type": "summary",
        "data": {"total": 120},
        },
        },
        "charts": [
        {"title": "趋势", "type": "line", "data": [{"week": 1, "value": 10}]},
        ],
    }

    with patch.object(
        TemplateReportDataService,
        "_get_template",
        return_value=template,
    ), patch(
        "app.services.template_report.core.TemplateReportCore.generate_from_template",
        return_value=fake_report,
    ):
        context = service.build_context(
        template_id=template.id,
        project_id=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 15),
        )

    assert context["template_info"]["template_id"] == template.id
    assert len(context["metrics_list"]) == 2
    assert context["sections_overview"][0]["section_id"] == "milestones"
    assert context["section_rows"], "应包含区块数据"
    assert context["charts_overview"][0]["data_points"] == 1

# -*- coding: utf-8 -*-
"""RPT-07: template report generation has one live implementation."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.report_framework.adapters.template import TemplateReportAdapter
from app.services.template_report_service import TemplateReportService


def _template(report_type: str = "PROJECT_WEEKLY"):
    return SimpleNamespace(
        id=7,
        template_code="TPL-7",
        template_name="模板报表",
        report_type=report_type,
        sections={},
        metrics_config={},
        is_active=True,
    )


def test_template_report_adapter_uses_core_service_not_broken_import():
    db = MagicMock()
    template = _template()
    db.query.return_value.filter.return_value.first.return_value = template
    adapter = TemplateReportAdapter(db)

    with patch(
        "app.services.template_report.core.TemplateReportCore.generate_from_template",
        return_value={"template_id": 7, "sections": {"ok": []}},
    ) as generate:
        result = adapter.generate_data(
            {
                "template_id": 7,
                "project_id": 10,
                "start_date": date(2026, 7, 1),
                "end_date": date(2026, 7, 31),
                "filters": {"scope": "real"},
            }
        )

    assert result == {"template_id": 7, "sections": {"ok": []}}
    generate.assert_called_once_with(
        db=db,
        template=template,
        project_id=10,
        department_id=None,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 31),
        filters={"scope": "real"},
    )


def test_legacy_template_report_service_delegates_to_core():
    db = MagicMock()
    template = _template("CUSTOM_REPORT")

    with patch(
        "app.services.template_report.core.TemplateReportCore.generate_from_template",
        return_value={"template_id": 7, "via": "core"},
    ) as generate:
        result = TemplateReportService.generate_from_template(
            db,
            template,
            project_id=11,
            department_id=22,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
            filters={"x": 1},
        )

    assert result == {"template_id": 7, "via": "core"}
    generate.assert_called_once_with(
        db=db,
        template=template,
        project_id=11,
        department_id=22,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 31),
        filters={"x": 1},
    )

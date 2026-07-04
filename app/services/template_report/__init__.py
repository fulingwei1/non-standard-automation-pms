# -*- coding: utf-8 -*-
"""Template report package compatibility helpers."""

from typing import Any, Dict


class _TemplateReportServiceProxy:
    @staticmethod
    def generate_from_template(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        from app.services.template_report_service import TemplateReportService

        return TemplateReportService.generate_from_template(*args, **kwargs)


template_report_service = _TemplateReportServiceProxy()

__all__ = ["template_report_service"]

# -*- coding: utf-8 -*-
"""
模板报表生成服务兼容入口。

真实生成逻辑统一收敛在 app.services.template_report.core.TemplateReportCore。
"""

from datetime import date
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.services.template_report.core import TemplateReportCore


class TemplateReportService:
    """Backward-compatible wrapper around TemplateReportCore."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    @staticmethod
    def generate_from_template(
        db: Session,
        template: Any,
        project_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return TemplateReportCore.generate_from_template(
            db=db,
            template=template,
            project_id=project_id,
            department_id=department_id,
            start_date=start_date,
            end_date=end_date,
            filters=kwargs.get("filters"),
        )

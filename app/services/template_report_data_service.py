# -*- coding: utf-8 -*-
"""
模板报表数据服务

提供统一报表框架所需的上下文数据
"""

import json
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.report_center import ReportTemplate
from app.services.template_report.core import TemplateReportCore


class TemplateReportDataService:
    """
    模板报表数据服务

    将模板报表生成结果转换为统一报表框架可消费的上下文
    """

    def __init__(self, db: Session):
        self.db = db

    def build_context(
        self,
        template_id: int,
        project_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        filters: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        构建模板报表上下文

        Args:
            template_id: 模板ID
            project_id: 项目ID
            department_id: 部门ID
            start_date: 开始日期
            end_date: 结束日期
            filters: 过滤条件（字典或JSON字符串）

        Returns:
            报表上下文字典
        """
        template = self._get_template(template_id)
        parsed_filters = self._parse_filters(filters)

        start, end = self._normalize_dates(start_date, end_date)

        report_data = TemplateReportCore.generate_from_template(
            db=self.db,
            template=template,
            project_id=project_id,
            department_id=department_id,
            start_date=start,
            end_date=end,
            filters=parsed_filters,
        )

        sections = report_data.get("sections") or {}
        metrics = report_data.get("metrics") or {}
        charts = report_data.get("charts") or []

        return {
            "template_info": self._build_template_info(template, report_data),
            "metrics_list": self._build_metrics_list(metrics),
            "sections_overview": self._build_sections_overview(sections),
            "section_rows": self._build_section_rows(sections),
            "charts_overview": self._build_charts_overview(charts),
        }

    # === Helpers ===

    def _get_template(self, template_id: int) -> ReportTemplate:
        template = (
            self.db.query(ReportTemplate)
            .filter(ReportTemplate.id == template_id)
            .first()
        )
        if not template:
            raise ValueError(f"报表模板不存在: {template_id}")
        if template.is_active is False:
            raise ValueError("报表模板已停用")
        return template

    def _parse_filters(self, filters: Optional[Any]) -> Dict[str, Any]:
        if not filters:
            return {}
        if isinstance(filters, dict):
            return filters
        if isinstance(filters, str):
            try:
                return json.loads(filters)
            except json.JSONDecodeError:
                return {}
        return {}

    def _normalize_dates(
        self,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> (date, date):
        today = date.today()
        end = end_date or today
        start = start_date or (end - timedelta(days=30))
        if start > end:
            start, end = end, start
        return start, end

    def _build_template_info(
        self,
        template: ReportTemplate,
        report_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        period = report_data.get("period") or {}
        return {
            "template_id": template.id,
            "template_code": template.template_code,
            "template_name": template.template_name,
            "report_type": report_data.get("report_type", template.report_type),
            "period_start": period.get("start_date"),
            "period_end": period.get("end_date"),
        }

    def _build_metrics_list(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        for key, value in metrics.items():
            result.append(
                {
                    "label": self._humanize_label(key),
                    "value": value,
                }
            )
        return result

    def _build_sections_overview(
        self,
        sections: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        overview: List[Dict[str, Any]] = []
        for section_id, section in sections.items():
            data = section.get("data")
            if isinstance(data, list):
                items = len(data)
            elif isinstance(data, dict):
                items = len(data)
            else:
                items = 1 if data else 0

            overview.append(
                {
                    "section_id": section_id,
                    "title": section.get("title") or section_id,
                    "section_type": section.get("type", "table"),
                    "item_count": items,
                    "has_summary": bool(section.get("summary")),
                }
            )
        return overview

    def _build_section_rows(
        self,
        sections: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for section_id, section in sections.items():
            section_title = section.get("title") or section_id
            section_type = section.get("type", "table")
            data = section.get("data")

            if isinstance(data, list):
                for idx, item in enumerate(data, start=1):
                    rows.append(
                        {
                            "section_id": section_id,
                            "section_title": section_title,
                            "section_type": section_type,
                            "row_index": idx,
                            "data_preview": self._to_json(item),
                        }
                    )
            elif isinstance(data, dict):
                rows.append(
                    {
                        "section_id": section_id,
                        "section_title": section_title,
                        "section_type": section_type,
                        "row_index": 1,
                        "data_preview": self._to_json(data),
                    }
                )
            elif data is not None:
                rows.append(
                    {
                        "section_id": section_id,
                        "section_title": section_title,
                        "section_type": section_type,
                        "row_index": 1,
                        "data_preview": str(data),
                    }
                )
        return rows

    def _build_charts_overview(
        self,
        charts: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        for chart in charts:
            data = chart.get("data")
            data_count = len(data) if isinstance(data, list) else 0
            result.append(
                {
                    "chart_title": chart.get("title", "图表"),
                    "chart_type": chart.get("type", "chart"),
                    "data_points": data_count,
                }
            )
        return result

    @staticmethod
    def _humanize_label(label: str) -> str:
        return label.replace("_", " ").title()

    @staticmethod
    def _to_json(value: Any) -> str:
        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return str(value)

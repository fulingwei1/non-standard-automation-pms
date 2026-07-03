# -*- coding: utf-8 -*-
"""
报表适配器基类

用于将现有报表服务适配到统一报表框架
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.report_framework.engine import ReportEngine


class BaseReportAdapter(ABC):
    """报表适配器基类"""

    def __init__(self, db: Session):
        self.db = db
        self.engine = ReportEngine(db)

    @abstractmethod
    def get_report_code(self) -> str:
        """返回报表代码"""
        pass

    @abstractmethod
    def generate_data(
        self,
        params: Dict[str, Any],
        user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        生成报表数据

        Args:
            params: 报表参数
            user: 当前用户

        Returns:
            报表数据字典
        """
        pass

    def generate(
        self,
        params: Dict[str, Any],
        format: str = "json",
        user: Optional[User] = None,
        skip_cache: bool = False,
    ) -> Any:
        """
        生成报表（使用统一报表框架）

        Args:
            params: 报表参数
            format: 导出格式（json, pdf, excel, word）
            user: 当前用户
            skip_cache: 是否跳过缓存

        Returns:
            报表结果
        """
        # 如果报表已迁移到YAML配置，直接使用ReportEngine
        try:
            return self.engine.generate(
                report_code=self.get_report_code(),
                params=params,
                format=format,
                user=user,
                skip_cache=skip_cache,
            )
        except Exception:
            # 如果YAML配置不存在，使用适配器方法生成数据
            data = self.generate_data(params, user)

            # 转换为统一报表框架格式
            return self._convert_to_report_result(data, format)

    def _convert_to_report_result(
        self,
        data: Dict[str, Any],
        format: str = "json",
    ) -> Any:
        """
        将数据转换为统一报表框架格式

        Args:
            data: 报表数据
            format: 导出格式

        Returns:
            报表结果
        """
        from app.services.report_framework.renderers import JsonRenderer

        normalized_format = "excel" if format == "xlsx" else format
        if normalized_format == "json":
            renderer = JsonRenderer()
        elif normalized_format == "excel":
            from app.services.report_framework.renderers import ExcelRenderer

            renderer = ExcelRenderer()
        elif normalized_format == "pdf":
            from app.services.report_framework.renderers import PdfRenderer

            renderer = PdfRenderer()
        elif normalized_format == "word":
            from app.services.report_framework.renderers import WordRenderer

            renderer = WordRenderer()
        else:
            raise ValueError(f"不支持的导出格式: {format}")

        sections = []

        # 转换数据为sections
        if "summary" in data:
            sections.append(
                {
                    "id": "summary",
                    "title": "汇总",
                    "type": "metrics",
                    "items": [
                        {"label": key, "value": value} for key, value in data["summary"].items()
                    ],
                }
            )

        if "details" in data:
            details = data["details"] or []
            columns = (
                [{"field": key, "label": key} for key in details[0].keys()]
                if details and isinstance(details[0], dict)
                else []
            )
            sections.append(
                {
                    "id": "details",
                    "title": "明细",
                    "type": "table",
                    "data": details,
                    "columns": columns,
                }
            )

        metadata = {
            "code": self.get_report_code(),
            "name": data.get("title", "报表"),
            "parameters": {},
        }

        return renderer.render(sections, metadata)

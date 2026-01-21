# -*- coding: utf-8 -*-
"""
JSON 渲染器

将报告数据渲染为 JSON 格式
"""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List

from app.services.report_framework.renderers.base import Renderer, ReportResult, RenderError


class CustomJSONEncoder(json.JSONEncoder):
    """自定义 JSON 编码器"""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)


class JsonRenderer(Renderer):
    """
    JSON 渲染器

    将报告数据渲染为 JSON 格式
    """

    @property
    def format_name(self) -> str:
        return "json"

    @property
    def content_type(self) -> str:
        return "application/json"

    def render(
        self,
        sections: List[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> ReportResult:
        """
        渲染报告为 JSON

        Args:
            sections: 渲染后的 section 数据
            metadata: 报告元数据

        Returns:
            ReportResult: JSON 格式的报告结果
        """
        try:
            # 构建报告数据结构
            report_data = {
                "meta": {
                    "report_code": metadata.get("code", ""),
                    "report_name": metadata.get("name", ""),
                    "generated_at": datetime.now().isoformat(),
                    "parameters": metadata.get("parameters", {}),
                },
                "sections": sections,
            }

            return ReportResult(
                data=report_data,
                format=self.format_name,
                content_type=self.content_type,
                metadata=metadata,
            )

        except Exception as e:
            raise RenderError(f"JSON rendering failed: {e}")

    def to_json_string(self, result: ReportResult, indent: int = 2) -> str:
        """
        将结果转换为 JSON 字符串

        Args:
            result: 报告结果
            indent: 缩进空格数

        Returns:
            JSON 字符串
        """
        return json.dumps(
            result.data,
            cls=CustomJSONEncoder,
            ensure_ascii=False,
            indent=indent,
        )

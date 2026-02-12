# -*- coding: utf-8 -*-
"""
统一导入导出引擎

提供通用的 Excel/PDF 处理入口，减少各模块重复实现。
"""

from __future__ import annotations

import io
from typing import Any, Dict, Iterable, List, Optional

from fastapi import HTTPException

from app.services.excel_export_service import ExcelExportService


class ExcelExportEngine:
    """Excel 导出引擎（封装 ExcelExportService）"""

    @staticmethod
    def _get_exporter() -> ExcelExportService:
        try:
            return ExcelExportService()
        except ImportError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @classmethod
    def export_table(
        cls,
        *,
        data: List[Dict[str, Any]],
        columns: Optional[List[Dict[str, Any]]] = None,
        sheet_name: str = "Sheet1",
        title: Optional[str] = None,
    ) -> io.BytesIO:
        """导出单表数据为 Excel"""
        exporter = cls._get_exporter()
        return exporter.export_to_excel(
            data=data,
            columns=columns,
            sheet_name=sheet_name,
            title=title,
        )

    @classmethod
    def export_multi_sheet(
        cls,
        sheets: List[Dict[str, Any]],
        *,
        sheet_post_process=None,
    ) -> io.BytesIO:
        """导出多 Sheet Excel"""
        exporter = cls._get_exporter()
        return exporter.export_multisheet(sheets, sheet_post_process=sheet_post_process)

    @staticmethod
    def build_columns(
        labels: Iterable[str],
        *,
        widths: Optional[Iterable[int]] = None,
    ) -> List[Dict[str, Any]]:
        """按标签和宽度构建列配置"""
        labels_list = list(labels)
        widths_list = list(widths) if widths is not None else []
        columns = []
        for idx, label in enumerate(labels_list):
            col = {"key": label, "label": label}
            if idx < len(widths_list):
                col["width"] = widths_list[idx]
            columns.append(col)
        return columns


class ImportExportEngine:
    """导入导出统一入口"""

    REQUIRED_COLUMNS = {
        "PROJECT": ["项目编码*", "项目名称*"],
        "USER": ["姓名"],
        "TIMESHEET": ["工作日期*", "人员姓名*", "工时(小时)*"],
        "TASK": ["任务名称*", "项目编码*"],
        "MATERIAL": ["物料编码*", "物料名称*"],
        "BOM": ["BOM编码*", "项目编码*", "物料编码*", "用量*"],
    }

    @staticmethod
    def parse_excel(file_content: bytes, **kwargs):
        """读取 Excel 文件为 DataFrame"""
        try:
            import pandas as pd
        except ImportError as exc:
            raise HTTPException(
                status_code=500, detail="Excel处理库未安装，请安装pandas和openpyxl"
            ) from exc

        df = pd.read_excel(io.BytesIO(file_content), **kwargs)
        df = df.dropna(how="all")
        return df

    @classmethod
    def get_required_columns(cls, template_type: str) -> List[str]:
        """获取模板类型所需的必填列"""
        return cls.REQUIRED_COLUMNS.get(template_type.upper(), [])

    @staticmethod
    def find_missing_columns(df, required_columns: List[str]) -> List[str]:
        """检查缺失列"""
        missing = []
        for req_col in required_columns:
            if req_col not in df.columns and req_col.replace("*", "") not in df.columns:
                missing.append(req_col)
        return missing

    @staticmethod
    def import_data(*, db, file_content: bytes, filename: str, template_type: str, current_user_id: int, update_existing: bool = False) -> Dict[str, Any]:
        """统一导入入口（委托给 unified_import_service）"""
        from app.services.unified_import import unified_import_service

        return unified_import_service.import_data(
            db=db,
            file_content=file_content,
            filename=filename,
            template_type=template_type,
            current_user_id=current_user_id,
            update_existing=update_existing,
        )


__all__ = [
    "ExcelExportEngine",
    "ImportExportEngine",
]

# -*- coding: utf-8 -*-
"""
统一数据导入服务 - 基础工具方法
包含：文件验证、解析、辅助函数
"""

from datetime import date, datetime
from typing import List

import pandas as pd
from fastapi import HTTPException

from app.services.import_export_engine import ImportExportEngine


class ImportBase:
    """导入服务基类 - 包含通用工具方法"""

    @staticmethod
    def validate_file(filename: str) -> None:
        """验证Excel文件类型"""
        if not filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="只支持Excel文件(.xlsx, .xls)")

    @staticmethod
    def parse_file(file_content: bytes) -> pd.DataFrame:
        """解析Excel文件"""
        try:
            df = ImportExportEngine.parse_excel(file_content)
            if len(df) == 0:
                raise HTTPException(status_code=400, detail="文件中没有数据")
            return df
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Excel文件解析失败: {str(e)}")

    @staticmethod
    def check_required_columns(df: pd.DataFrame, required_columns: List[str]) -> List[str]:
        """检查必需列是否存在，返回缺失列列表"""
        missing = []
        for col in required_columns:
            if col not in df.columns and col.replace('*', '') not in df.columns:
                missing.append(col)
        return missing

    @staticmethod
    def parse_work_date(work_date_val) -> date:
        """解析工作日期"""
        if isinstance(work_date_val, datetime):
            return work_date_val.date()
        elif isinstance(work_date_val, date):
            return work_date_val
        else:
            return pd.to_datetime(work_date_val).date()

    @staticmethod
    def parse_hours(hours_val) -> float:
        """解析工时，返回None表示无效"""
        hours = float(hours_val)
        if hours <= 0 or hours > 24:
            return None
        return hours

    @staticmethod
    def parse_progress(row: pd.Series, column_name: str) -> float:
        """解析进度百分比"""
        val = row.get(column_name)
        if pd.isna(val):
            return None
        try:
            progress = float(val)
            if 0 <= progress <= 100:
                return progress
        except (ValueError, TypeError):
            pass
        return None

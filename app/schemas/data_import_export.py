# -*- coding: utf-8 -*-
"""
数据导入导出 Schema
"""

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== 数据导入 ====================

class ImportTemplateTypeResponse(BaseModel):
    """导入模板类型响应"""
    types: List[Dict[str, Any]] = Field(description="模板类型列表")


class ImportPreviewRequest(BaseModel):
    """预览导入数据请求"""
    template_type: str = Field(description="模板类型")
    file_url: Optional[str] = Field(None, description="文件URL（直接上传文件请使用 /import/preview 端点的 UploadFile 参数）")


class ImportPreviewResponse(BaseModel):
    """预览导入数据响应"""
    total_rows: int
    valid_rows: int
    invalid_rows: int
    preview_data: List[Dict[str, Any]] = Field(description="预览数据（前10行）")
    errors: List[Dict[str, Any]] = Field(default=[], description="错误信息")


class ImportValidateRequest(BaseModel):
    """验证导入数据请求"""
    template_type: str
    data: List[Dict[str, Any]] = Field(description="待验证数据")


class ImportValidateResponse(BaseModel):
    """验证导入数据响应"""
    is_valid: bool
    valid_count: int
    invalid_count: int
    errors: List[Dict[str, Any]] = Field(description="验证错误列表")


class ImportUploadRequest(BaseModel):
    """上传并导入数据请求"""
    template_type: str
    file_url: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    options: Optional[Dict[str, Any]] = Field(default={}, description="导入选项")


class ImportUploadResponse(BaseModel):
    """上传并导入数据响应"""
    task_id: int
    task_code: str
    status: str
    message: str


# ==================== 数据导出 ====================

class ExportProjectListRequest(BaseModel):
    """导出项目列表请求"""
    filters: Optional[Dict[str, Any]] = Field(default={}, description="过滤条件")
    columns: Optional[List[str]] = Field(default=[], description="导出列")


class ExportProjectDetailRequest(BaseModel):
    """导出项目详情请求"""
    project_id: int
    include_tasks: bool = Field(default=True, description="包含任务")
    include_costs: bool = Field(default=True, description="包含成本")


class ExportTaskListRequest(BaseModel):
    """导出任务列表请求"""
    project_id: Optional[int] = None
    filters: Optional[Dict[str, Any]] = Field(default={})


class ExportTimesheetRequest(BaseModel):
    """导出工时数据请求"""
    start_date: date
    end_date: date
    user_id: Optional[int] = None
    project_id: Optional[int] = None


class ExportWorkloadRequest(BaseModel):
    """导出负荷数据请求"""
    start_date: date
    end_date: date
    department_id: Optional[int] = None

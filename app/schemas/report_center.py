# -*- coding: utf-8 -*-
"""
报表中心 Schema
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .common import BaseSchema, PaginatedResponse, TimestampSchema

# ==================== 报表配置 ====================

class ReportRoleResponse(BaseModel):
    """支持角色列表响应"""
    roles: List[Dict[str, Any]] = Field(description="角色列表")


class ReportTypeResponse(BaseModel):
    """报表类型列表响应"""
    types: List[Dict[str, Any]] = Field(description="报表类型列表")


class RoleReportMatrixResponse(BaseModel):
    """角色-报表权限矩阵响应"""
    matrix: Dict[str, List[str]] = Field(description="权限矩阵：角色 -> 报表类型列表")


# ==================== 报表生成 ====================

class ReportGenerateRequest(BaseModel):
    """生成报表请求"""
    report_type: str = Field(description="报表类型")
    role: Optional[str] = Field(None, description="角色视角")
    project_id: Optional[int] = None
    department_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    filters: Optional[Dict[str, Any]] = Field(default={}, description="过滤条件")


class ReportGenerateResponse(BaseModel):
    """生成报表响应"""
    report_id: int
    report_code: str
    report_name: str
    report_type: str
    generated_at: datetime
    data: Dict[str, Any] = Field(description="报表数据")


class ReportPreviewResponse(BaseModel):
    """预览报表响应"""
    report_type: str
    preview_data: Dict[str, Any] = Field(description="预览数据")


class ReportCompareRequest(BaseModel):
    """比较角色视角请求"""
    report_type: str
    roles: List[str] = Field(description="角色列表")
    project_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ReportCompareResponse(BaseModel):
    """比较角色视角响应"""
    report_type: str
    comparison_data: Dict[str, Any] = Field(description="对比数据")


class ReportExportRequest(BaseModel):
    """导出报表请求"""
    report_id: int
    export_format: str = Field(description="导出格式：XLSX/PDF/HTML")
    options: Optional[Dict[str, Any]] = Field(default={}, description="导出选项")


# ==================== 报表模板 ====================

class ReportTemplateResponse(TimestampSchema):
    """报表模板响应"""
    id: int
    template_code: str
    template_name: str
    report_type: str
    description: Optional[str] = None
    is_system: bool = False
    is_active: bool = True
    use_count: int = 0


class ReportTemplateListResponse(PaginatedResponse):
    """报表模板列表响应"""
    items: List[ReportTemplateResponse]


class ApplyTemplateRequest(BaseModel):
    """应用报表模板请求"""
    template_id: int
    report_name: str
    project_id: Optional[int] = None
    department_id: Optional[int] = None
    customizations: Optional[Dict[str, Any]] = Field(default={}, description="自定义配置")

# -*- coding: utf-8 -*-
"""
项目报告自动生成 — Schema 定义
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== 周报 ====================


class WeeklyReportGenerateRequest(BaseModel):
    """生成项目周报请求"""

    project_id: int = Field(description="项目ID")
    report_date: Optional[date] = Field(None, description="报告日期（默认今天，自动算本周范围）")
    template_id: Optional[int] = Field(None, description="报告模板ID（可选，控制包含哪些板块）")


class WeeklyReportResponse(BaseModel):
    """周报响应"""

    report_id: int
    report_type: str = "PROJECT_WEEKLY"
    project_id: int
    project_code: str
    project_name: str
    period: Dict[str, Any]
    generated_at: str
    summary: Dict[str, Any]
    sections: Dict[str, Any]


# ==================== 月报 ====================


class MonthlyReportGenerateRequest(BaseModel):
    """生成项目月报请求"""

    project_id: int = Field(description="项目ID")
    year: Optional[int] = Field(None, description="年份（默认当年）")
    month: Optional[int] = Field(None, description="月份（默认当月）")
    template_id: Optional[int] = Field(None, description="报告模板ID")


class MonthlyReportResponse(BaseModel):
    """月报响应"""

    report_id: int
    report_type: str = "PROJECT_MONTHLY"
    project_id: int
    project_code: str
    project_name: str
    period: Dict[str, Any]
    generated_at: str
    summary: Dict[str, Any]
    sections: Dict[str, Any]


# ==================== 编辑 ====================


class ReportEditRequest(BaseModel):
    """编辑报告请求（手动修改后再发送）"""

    report_id: int = Field(description="报告ID")
    summary: Optional[Dict[str, Any]] = Field(None, description="更新摘要（合并式更新）")
    sections: Optional[Dict[str, Any]] = Field(None, description="更新板块（合并式更新）")
    extra: Optional[Dict[str, Any]] = Field(None, description="其他附加数据")


class ReportEditResponse(BaseModel):
    """编辑结果"""

    report_id: int
    status: str
    updated_data: Dict[str, Any]


# ==================== 推送 ====================


class ReportPushRequest(BaseModel):
    """推送报告请求"""

    report_id: int = Field(description="报告ID")
    recipient_user_ids: Optional[List[int]] = Field(None, description="额外接收人ID列表")
    channels: Optional[List[str]] = Field(None, description="通知渠道（默认 system+email）")
    export_formats: Optional[List[str]] = Field(
        None, description="导出格式列表，如 ['PDF', 'XLSX']"
    )
    send_to_pm: bool = Field(True, description="是否发送给项目经理")
    send_to_stakeholders: bool = Field(True, description="是否发送给干系人")


class RecipientInfo(BaseModel):
    user_id: int
    user_name: str


class ExportInfo(BaseModel):
    format: str
    success: bool
    path: Optional[str] = None
    filename: Optional[str] = None
    error: Optional[str] = None


class NotificationSummary(BaseModel):
    total: int
    success: int
    failed: int


class ReportPushResponse(BaseModel):
    """推送结果"""

    success: bool
    message: str
    report_id: int
    recipients: List[RecipientInfo]
    exports: List[ExportInfo]
    notification_summary: NotificationSummary


# ==================== 导出 ====================


class ReportExportRequest(BaseModel):
    """仅导出请求"""

    report_id: int
    formats: List[str] = Field(description="导出格式列表: PDF, XLSX")


class ReportExportResponse(BaseModel):
    """导出结果"""

    exports: List[ExportInfo]

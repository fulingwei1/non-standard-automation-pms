# -*- coding: utf-8 -*-
"""
验收单跟踪 Schema
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from ...schemas.common import TimestampSchema


class AcceptanceTrackingCreate(BaseModel):
    """创建验收单跟踪记录"""

    acceptance_order_id: int = Field(description="验收单ID")
    contract_id: Optional[int] = Field(default=None, description="合同ID")
    sales_person_id: Optional[int] = Field(default=None, description="业务员ID")
    remark: Optional[str] = Field(default=None, description="备注")


class AcceptanceTrackingUpdate(BaseModel):
    """更新验收单跟踪记录"""

    condition_check_status: Optional[str] = None
    condition_check_result: Optional[str] = None
    tracking_status: Optional[str] = None
    received_date: Optional[date] = None
    report_status: Optional[str] = None
    warranty_start_date: Optional[date] = None
    warranty_end_date: Optional[date] = None
    remark: Optional[str] = None


class AcceptanceTrackingResponse(TimestampSchema):
    """验收单跟踪响应"""

    id: int
    acceptance_order_id: int
    acceptance_order_no: Optional[str] = None
    project_id: int
    project_code: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    condition_check_status: Optional[str] = None
    condition_check_result: Optional[str] = None
    condition_check_date: Optional[datetime] = None
    condition_checker_id: Optional[int] = None
    tracking_status: Optional[str] = None
    reminder_count: Optional[int] = None
    last_reminder_date: Optional[datetime] = None
    last_reminder_by: Optional[int] = None
    received_date: Optional[date] = None
    signed_file_id: Optional[int] = None
    report_status: Optional[str] = None
    report_generated_date: Optional[datetime] = None
    report_signed_date: Optional[datetime] = None
    report_archived_date: Optional[datetime] = None
    warranty_start_date: Optional[date] = None
    warranty_end_date: Optional[date] = None
    warranty_status: Optional[str] = None
    warranty_expiry_reminded: Optional[bool] = None
    contract_id: Optional[int] = None
    contract_no: Optional[str] = None
    sales_person_id: Optional[int] = None
    sales_person_name: Optional[str] = None
    support_person_id: Optional[int] = None
    remark: Optional[str] = None
    tracking_records: Optional[List[dict]] = None


class ConditionCheckRequest(BaseModel):
    """验收条件检查请求"""

    condition_check_status: str = Field(description="检查状态：met/not_met")
    condition_check_result: str = Field(description="检查结果")
    remark: Optional[str] = Field(default=None, description="备注")


class ReminderRequest(BaseModel):
    """催签请求"""

    reminder_content: Optional[str] = Field(default=None, description="催签内容")
    remark: Optional[str] = Field(default=None, description="备注")


class AcceptanceTrackingRecordResponse(TimestampSchema):
    """验收单跟踪记录明细响应"""

    id: int
    tracking_id: int
    record_type: str
    record_content: Optional[str] = None
    record_date: datetime
    operator_id: int
    operator_name: Optional[str] = None
    result: Optional[str] = None
    remark: Optional[str] = None

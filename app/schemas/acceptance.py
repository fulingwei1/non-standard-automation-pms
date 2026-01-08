# -*- coding: utf-8 -*-
"""
验收管理 Schema
"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal

from .common import BaseSchema, TimestampSchema


# ==================== 验收模板 ====================

class TemplateCheckItemCreate(BaseModel):
    """模板检查项创建"""
    item_code: str = Field(max_length=50)
    item_name: str = Field(max_length=200)
    check_method: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    standard_value: Optional[str] = None
    tolerance_min: Optional[str] = None
    tolerance_max: Optional[str] = None
    unit: Optional[str] = None
    is_required: bool = True
    is_key_item: bool = False
    sort_order: int = 0


class TemplateCategoryCreate(BaseModel):
    """模板分类创建"""
    category_code: str = Field(max_length=20)
    category_name: str = Field(max_length=100)
    weight: Decimal = Field(default=0, ge=0, le=100)
    sort_order: int = 0
    is_required: bool = True
    description: Optional[str] = None
    check_items: List[TemplateCheckItemCreate] = []


class AcceptanceTemplateCreate(BaseModel):
    """创建验收模板"""
    template_code: str = Field(max_length=50)
    template_name: str = Field(max_length=200)
    acceptance_type: str = Field(description="FAT/SAT/FINAL")
    equipment_type: Optional[str] = None
    version: str = Field(default="1.0")
    description: Optional[str] = None
    categories: List[TemplateCategoryCreate] = []


class AcceptanceTemplateResponse(TimestampSchema):
    """验收模板响应"""
    id: int
    template_code: str
    template_name: str
    acceptance_type: str
    equipment_type: Optional[str] = None
    version: str
    is_system: bool = False
    is_active: bool = True


# ==================== 验收单 ====================

class AcceptanceOrderCreate(BaseModel):
    """创建验收单"""
    project_id: int = Field(description="项目ID")
    machine_id: Optional[int] = None
    acceptance_type: str = Field(description="FAT/SAT/FINAL")
    template_id: Optional[int] = None
    planned_date: Optional[date] = None
    location: Optional[str] = None


class AcceptanceOrderUpdate(BaseModel):
    """更新验收单"""
    planned_date: Optional[date] = None
    location: Optional[str] = None
    conclusion: Optional[str] = None
    conditions: Optional[str] = None


class AcceptanceOrderStart(BaseModel):
    """开始验收"""
    location: Optional[str] = None


class AcceptanceOrderComplete(BaseModel):
    """完成验收"""
    overall_result: str = Field(description="PASSED/FAILED/CONDITIONAL")
    conclusion: str = Field(description="验收结论")
    conditions: Optional[str] = None


class AcceptanceOrderResponse(TimestampSchema):
    """验收单响应"""
    id: int
    order_no: str
    project_id: int
    project_name: Optional[str] = None
    machine_id: Optional[int] = None
    machine_name: Optional[str] = None
    acceptance_type: str
    template_id: Optional[int] = None
    template_name: Optional[str] = None
    planned_date: Optional[date] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    location: Optional[str] = None
    status: str = "DRAFT"
    total_items: int = 0
    passed_items: int = 0
    failed_items: int = 0
    na_items: int = 0
    pass_rate: Decimal = 0
    overall_result: Optional[str] = None
    conclusion: Optional[str] = None
    conditions: Optional[str] = None
    customer_signed_file_path: Optional[str] = None
    is_officially_completed: bool = False
    officially_completed_at: Optional[datetime] = None


class AcceptanceOrderListResponse(BaseSchema):
    """验收单列表响应"""
    id: int
    order_no: str
    project_name: Optional[str] = None
    machine_name: Optional[str] = None
    acceptance_type: str
    planned_date: Optional[date] = None
    status: str
    overall_result: Optional[str] = None
    pass_rate: Decimal = 0
    open_issues: int = 0
    is_officially_completed: bool = False


# ==================== 检查项结果 ====================

class CheckItemResultUpdate(BaseModel):
    """更新检查项结果"""
    result_status: str = Field(description="PASSED/FAILED/NA/CONDITIONAL")
    actual_value: Optional[str] = None
    deviation: Optional[str] = None
    remark: Optional[str] = None


class CheckItemResultResponse(BaseSchema):
    """检查项结果响应"""
    id: int
    category_code: str
    category_name: str
    item_code: str
    item_name: str
    check_method: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    standard_value: Optional[str] = None
    tolerance_min: Optional[str] = None
    tolerance_max: Optional[str] = None
    unit: Optional[str] = None
    is_required: bool = True
    is_key_item: bool = False
    result_status: str = "PENDING"
    actual_value: Optional[str] = None
    deviation: Optional[str] = None
    remark: Optional[str] = None
    checked_by: Optional[int] = None
    checked_at: Optional[datetime] = None


# ==================== 验收问题 ====================

class AcceptanceIssueCreate(BaseModel):
    """创建验收问题"""
    order_id: int = Field(description="验收单ID")
    order_item_id: Optional[int] = None
    issue_type: str = Field(description="DEFECT/DEVIATION/SUGGESTION")
    severity: str = Field(description="CRITICAL/MAJOR/MINOR")
    title: str = Field(max_length=200)
    description: str
    is_blocking: bool = False
    assigned_to: Optional[int] = None
    due_date: Optional[date] = None
    attachments: Optional[List[Any]] = None


class AcceptanceIssueUpdate(BaseModel):
    """更新验收问题"""
    severity: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    is_blocking: Optional[bool] = None
    assigned_to: Optional[int] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    solution: Optional[str] = None


class AcceptanceIssueResponse(TimestampSchema):
    """验收问题响应"""
    id: int
    issue_no: str
    order_id: int
    order_item_id: Optional[int] = None
    issue_type: str
    severity: str
    title: str
    description: str
    found_at: Optional[datetime] = None
    found_by: Optional[int] = None
    found_by_name: Optional[str] = None
    status: str = "OPEN"
    assigned_to: Optional[int] = None
    assigned_to_name: Optional[str] = None
    due_date: Optional[date] = None
    solution: Optional[str] = None
    resolved_at: Optional[datetime] = None
    is_blocking: bool = False


# ==================== 签字 ====================

class AcceptanceSignatureCreate(BaseModel):
    """创建签字"""
    order_id: int
    signer_type: str = Field(description="QA/PM/CUSTOMER/WITNESS")
    signer_role: Optional[str] = None
    signer_name: str = Field(max_length=100)
    signer_company: Optional[str] = None
    signature_data: Optional[str] = None


class AcceptanceSignatureResponse(BaseSchema):
    """签字响应"""
    id: int
    order_id: int
    signer_type: str
    signer_role: Optional[str] = None
    signer_name: str
    signer_company: Optional[str] = None
    signed_at: datetime
    ip_address: Optional[str] = None


# ==================== 验收报告 ====================

class AcceptanceReportGenerateRequest(BaseModel):
    """生成验收报告请求"""
    report_type: str = Field(description="FAT/SAT/FINAL")
    version: Optional[int] = Field(default=1, description="版本号")
    include_signatures: bool = Field(default=True, description="是否包含签字")


class AcceptanceReportResponse(TimestampSchema):
    """验收报告响应"""
    id: int
    order_id: int
    report_no: str
    report_type: str
    version: int = 1
    report_content: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    generated_at: Optional[datetime] = None
    generated_by: Optional[int] = None
    generated_by_name: Optional[str] = None

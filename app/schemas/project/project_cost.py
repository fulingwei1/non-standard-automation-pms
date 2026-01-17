# -*- coding: utf-8 -*-
"""
项目成本和收款 Schema
包含项目成本、收款计划等财务管理相关的 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from ..common import TimestampSchema


class ProjectCostCreate(BaseModel):
    """创建成本记录"""

    project_id: int
    machine_id: Optional[int] = None
    cost_type: str = Field(max_length=50)
    cost_category: str = Field(max_length=50)
    source_module: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    source_no: Optional[str] = None
    amount: Decimal
    tax_amount: Optional[Decimal] = 0
    description: Optional[str] = None
    cost_date: date


class ProjectCostUpdate(BaseModel):
    """更新成本记录"""

    machine_id: Optional[int] = None
    cost_type: Optional[str] = None
    cost_category: Optional[str] = None
    source_module: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    source_no: Optional[str] = None
    amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    description: Optional[str] = None
    cost_date: Optional[date] = None


class ProjectCostResponse(TimestampSchema):
    """成本记录响应"""

    id: int
    project_id: int
    machine_id: Optional[int] = None
    cost_type: str
    cost_category: str
    source_module: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    source_no: Optional[str] = None
    amount: Decimal
    tax_amount: Decimal
    description: Optional[str] = None
    cost_date: date
    is_financial_correction: Optional[bool] = False  # 是否为财务修正数据
    upload_batch_no: Optional[str] = None  # 上传批次号（财务上传）

    class Config:
        from_attributes = True


class FinancialProjectCostCreate(BaseModel):
    """创建财务项目成本"""

    project_id: int = Field(description="项目ID")
    project_code: Optional[str] = Field(default=None, max_length=50, description="项目编号")
    project_name: Optional[str] = Field(default=None, max_length=200, description="项目名称")
    machine_id: Optional[int] = Field(default=None, description="设备ID")
    cost_type: str = Field(max_length=50, description="成本类型：LABOR/TRAVEL/ENTERTAINMENT/OTHER")
    cost_category: str = Field(max_length=50, description="成本分类")
    cost_item: Optional[str] = Field(default=None, max_length=200, description="成本项名称")
    amount: Decimal = Field(description="金额")
    tax_amount: Optional[Decimal] = Field(default=0, description="税额")
    currency: Optional[str] = Field(default="CNY", max_length=10, description="币种")
    cost_date: date = Field(description="发生日期")
    cost_month: Optional[str] = Field(default=None, max_length=7, description="成本月份(YYYY-MM)")
    description: Optional[str] = Field(default=None, description="费用说明")
    location: Optional[str] = Field(default=None, max_length=200, description="地点")
    participants: Optional[str] = Field(default=None, max_length=500, description="参与人员")
    purpose: Optional[str] = Field(default=None, max_length=500, description="用途/目的")
    user_id: Optional[int] = Field(default=None, description="人员ID（人工费用）")
    user_name: Optional[str] = Field(default=None, max_length=50, description="人员姓名")
    hours: Optional[Decimal] = Field(default=None, description="工时")
    hourly_rate: Optional[Decimal] = Field(default=None, description="时薪")
    source_no: Optional[str] = Field(default=None, max_length=100, description="来源单号")
    invoice_no: Optional[str] = Field(default=None, max_length=100, description="发票号")


class FinancialProjectCostResponse(TimestampSchema):
    """财务项目成本响应"""

    id: int
    project_id: int
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    machine_id: Optional[int] = None
    cost_type: str
    cost_category: str
    cost_item: Optional[str] = None
    amount: Decimal
    tax_amount: Decimal = 0
    currency: str = "CNY"
    cost_date: date
    cost_month: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    participants: Optional[str] = None
    purpose: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    hours: Optional[Decimal] = None
    hourly_rate: Optional[Decimal] = None
    source_type: str = "FINANCIAL_UPLOAD"
    source_no: Optional[str] = None
    invoice_no: Optional[str] = None
    upload_batch_no: Optional[str] = None
    uploaded_by: int
    uploaded_by_name: Optional[str] = None
    is_verified: bool = False
    verified_by: Optional[int] = None
    verified_by_name: Optional[str] = None
    verified_at: Optional[datetime] = None


class FinancialProjectCostUploadRequest(BaseModel):
    """财务成本批量上传请求"""

    costs: List[FinancialProjectCostCreate] = Field(description="成本列表")
    upload_batch_no: Optional[str] = Field(default=None, description="上传批次号")


# ==================== 项目收款计划 ====================


class ProjectPaymentPlanCreate(BaseModel):
    """创建收款计划"""

    project_id: int
    contract_id: Optional[int] = None
    payment_no: int
    payment_name: str = Field(max_length=100)
    payment_type: str = Field(max_length=20)  # ADVANCE/DELIVERY/ACCEPTANCE/WARRANTY
    payment_ratio: Optional[Decimal] = None
    planned_amount: Decimal
    planned_date: Optional[date] = None
    milestone_id: Optional[int] = None
    trigger_milestone: Optional[str] = None
    trigger_condition: Optional[str] = None
    remark: Optional[str] = None


class ProjectPaymentPlanUpdate(BaseModel):
    """更新收款计划"""

    payment_name: Optional[str] = None
    payment_type: Optional[str] = None
    payment_ratio: Optional[Decimal] = None
    planned_amount: Optional[Decimal] = None
    actual_amount: Optional[Decimal] = None
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    milestone_id: Optional[int] = None
    trigger_milestone: Optional[str] = None
    trigger_condition: Optional[str] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class ProjectPaymentPlanResponse(TimestampSchema):
    """收款计划响应"""

    id: int
    project_id: int
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    contract_id: Optional[int] = None
    contract_code: Optional[str] = None
    payment_no: int
    payment_name: str
    payment_type: str
    payment_ratio: Optional[Decimal] = None
    planned_amount: Decimal
    actual_amount: Decimal = Decimal("0")
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    milestone_id: Optional[int] = None
    milestone_code: Optional[str] = None
    milestone_name: Optional[str] = None
    trigger_milestone: Optional[str] = None
    trigger_condition: Optional[str] = None
    status: str
    invoice_id: Optional[int] = None
    invoice_no: Optional[str] = None
    invoice_date: Optional[date] = None
    invoice_amount: Optional[Decimal] = None
    remark: Optional[str] = None

    class Config:
        from_attributes = True

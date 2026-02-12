# -*- coding: utf-8 -*-
"""
研发项目管理 Schema
包含：研发项目、项目分类、研发费用、费用类型、费用分摊规则、报表记录
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from .common import TimestampSchema

# ==================== 研发项目分类 ====================

class RdProjectCategoryCreate(BaseModel):
    """创建研发项目分类"""
    category_code: str = Field(max_length=20, description="分类编码")
    category_name: str = Field(max_length=50, description="分类名称")
    category_type: str = Field(description="分类类型：SELF/ENTRUST/COOPERATION")
    description: Optional[str] = None
    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)


class RdProjectCategoryUpdate(BaseModel):
    """更新研发项目分类"""
    category_name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class RdProjectCategoryResponse(TimestampSchema):
    """研发项目分类响应"""
    id: int
    category_code: str
    category_name: str
    category_type: str
    description: Optional[str] = None
    sort_order: int
    is_active: bool

    class Config:
        from_attributes = True


# ==================== 研发项目 ====================

class RdProjectCreate(BaseModel):
    """创建研发项目"""
    project_name: str = Field(max_length=200, description="研发项目名称")
    category_id: Optional[int] = None
    category_type: str = Field(description="项目类型：SELF/ENTRUST/COOPERATION")
    initiation_date: date = Field(description="立项日期")
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    project_manager_id: Optional[int] = None
    initiation_reason: Optional[str] = None
    research_goal: Optional[str] = None
    research_content: Optional[str] = None
    expected_result: Optional[str] = None
    budget_amount: Decimal = Field(default=0)
    linked_project_id: Optional[int] = None
    remark: Optional[str] = None


class RdProjectUpdate(BaseModel):
    """更新研发项目"""
    project_name: Optional[str] = None
    category_id: Optional[int] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    project_manager_id: Optional[int] = None
    initiation_reason: Optional[str] = None
    research_goal: Optional[str] = None
    research_content: Optional[str] = None
    expected_result: Optional[str] = None
    budget_amount: Optional[Decimal] = None
    linked_project_id: Optional[int] = None
    remark: Optional[str] = None


class RdProjectResponse(TimestampSchema):
    """研发项目响应"""
    id: int
    project_no: str
    project_name: str
    category_id: Optional[int] = None
    category_type: str
    initiation_date: date
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    project_manager_id: Optional[int] = None
    project_manager_name: Optional[str] = None
    initiation_reason: Optional[str] = None
    research_goal: Optional[str] = None
    research_content: Optional[str] = None
    expected_result: Optional[str] = None
    budget_amount: Decimal
    linked_project_id: Optional[int] = None
    status: str
    approval_status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    approval_remark: Optional[str] = None
    close_date: Optional[date] = None
    close_reason: Optional[str] = None
    close_result: Optional[str] = None
    total_cost: Decimal
    total_hours: Decimal
    participant_count: int
    remark: Optional[str] = None

    class Config:
        from_attributes = True


class RdProjectApproveRequest(BaseModel):
    """研发项目审批请求"""
    approved: bool = Field(description="是否批准")
    approval_remark: Optional[str] = Field(default=None, description="审批意见")


class RdProjectCloseRequest(BaseModel):
    """研发项目结项请求"""
    close_reason: str = Field(description="结项原因")
    close_result: str = Field(description="结项成果")


class RdProjectLinkRequest(BaseModel):
    """关联非标项目请求"""
    linked_project_id: int = Field(description="关联的非标项目ID")


# ==================== 研发费用类型 ====================

class RdCostTypeCreate(BaseModel):
    """创建研发费用类型"""
    type_code: str = Field(max_length=20, description="费用类型编码")
    type_name: str = Field(max_length=50, description="费用类型名称")
    category: str = Field(description="费用大类：LABOR/MATERIAL/DEPRECIATION/OTHER")
    description: Optional[str] = None
    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    is_deductible: bool = Field(default=True)
    deduction_rate: Decimal = Field(default=100.00)


class RdCostTypeResponse(TimestampSchema):
    """研发费用类型响应"""
    id: int
    type_code: str
    type_name: str
    category: str
    description: Optional[str] = None
    sort_order: int
    is_active: bool
    is_deductible: bool
    deduction_rate: Decimal

    class Config:
        from_attributes = True


# ==================== 研发费用 ====================

class RdCostCreate(BaseModel):
    """创建研发费用"""
    rd_project_id: int = Field(description="研发项目ID")
    cost_type_id: int = Field(description="费用类型ID")
    cost_date: date = Field(description="费用发生日期")
    cost_amount: Decimal = Field(description="费用金额")
    cost_description: Optional[str] = None
    # 人工费用相关
    user_id: Optional[int] = None
    hours: Optional[Decimal] = None
    hourly_rate: Optional[Decimal] = None
    # 材料费用相关
    material_id: Optional[int] = None
    material_qty: Optional[Decimal] = None
    material_price: Optional[Decimal] = None
    # 折旧费用相关
    equipment_id: Optional[int] = None
    depreciation_period: Optional[str] = None
    # 来源信息
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    # 分摊信息
    is_allocated: bool = Field(default=False)
    allocation_rule_id: Optional[int] = None
    allocation_rate: Optional[Decimal] = None
    # 加计扣除
    deductible_amount: Optional[Decimal] = None
    remark: Optional[str] = None


class RdCostUpdate(BaseModel):
    """更新研发费用"""
    cost_date: Optional[date] = None
    cost_amount: Optional[Decimal] = None
    cost_description: Optional[str] = None
    user_id: Optional[int] = None
    hours: Optional[Decimal] = None
    hourly_rate: Optional[Decimal] = None
    material_id: Optional[int] = None
    material_qty: Optional[Decimal] = None
    material_price: Optional[Decimal] = None
    equipment_id: Optional[int] = None
    depreciation_period: Optional[str] = None
    deductible_amount: Optional[Decimal] = None
    remark: Optional[str] = None


class RdCostResponse(TimestampSchema):
    """研发费用响应"""
    id: int
    cost_no: str
    rd_project_id: int
    cost_type_id: int
    cost_date: date
    cost_amount: Decimal
    cost_description: Optional[str] = None
    user_id: Optional[int] = None
    hours: Optional[Decimal] = None
    hourly_rate: Optional[Decimal] = None
    material_id: Optional[int] = None
    material_qty: Optional[Decimal] = None
    material_price: Optional[Decimal] = None
    equipment_id: Optional[int] = None
    depreciation_period: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    is_allocated: bool
    allocation_rule_id: Optional[int] = None
    allocation_rate: Optional[Decimal] = None
    deductible_amount: Optional[Decimal] = None
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    remark: Optional[str] = None

    class Config:
        from_attributes = True


class RdCostCalculateLaborRequest(BaseModel):
    """人工费用自动计算请求"""
    rd_project_id: int = Field(description="研发项目ID")
    user_id: int = Field(description="人员ID")
    start_date: date = Field(description="开始日期")
    end_date: date = Field(description="结束日期")
    hourly_rate: Optional[Decimal] = Field(default=None, description="时薪（如不提供则使用默认值）")


class RdCostSummaryResponse(BaseModel):
    """项目费用汇总响应"""
    rd_project_id: int
    rd_project_name: str
    total_cost: Decimal
    labor_cost: Decimal
    material_cost: Decimal
    depreciation_cost: Decimal
    other_cost: Decimal
    deductible_amount: Decimal
    cost_by_type: List[dict] = Field(default_factory=list, description="按类型汇总")


# ==================== 费用分摊规则 ====================

class RdCostAllocationRuleCreate(BaseModel):
    """创建费用分摊规则"""
    rule_name: str = Field(max_length=100, description="规则名称")
    rule_type: str = Field(description="分摊类型：PROPORTION/MANUAL")
    allocation_basis: str = Field(description="分摊依据：HOURS/REVENUE/HEADCOUNT")
    allocation_formula: Optional[dict] = None
    cost_type_ids: Optional[List[int]] = None
    project_ids: Optional[List[int]] = None
    is_active: bool = Field(default=True)
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    remark: Optional[str] = None


class RdCostAllocationRuleResponse(TimestampSchema):
    """费用分摊规则响应"""
    id: int
    rule_name: str
    rule_type: str
    allocation_basis: str
    allocation_formula: Optional[dict] = None
    cost_type_ids: Optional[List[int]] = None
    project_ids: Optional[List[int]] = None
    is_active: bool
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    remark: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== 报表记录 ====================

class RdReportRecordResponse(TimestampSchema):
    """研发报表记录响应"""
    id: int
    report_no: str
    report_type: str
    report_name: str
    report_params: Optional[dict] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    project_ids: Optional[List[int]] = None
    generated_by: int
    generated_at: datetime
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    status: str
    remark: Optional[str] = None

    class Config:
        from_attributes = True




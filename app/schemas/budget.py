# -*- coding: utf-8 -*-
"""
项目预算管理模块 Schema
"""

from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime
from pydantic import BaseModel, Field

from app.schemas.common import TimestampSchema


class ProjectBudgetItemCreate(BaseModel):
    """创建预算明细"""
    item_no: int = Field(..., description="行号")
    cost_category: str = Field(..., max_length=50, description="成本类别")
    cost_item: str = Field(..., max_length=200, description="成本项")
    description: Optional[str] = Field(None, description="说明")
    budget_amount: Decimal = Field(..., description="预算金额")
    machine_id: Optional[int] = Field(None, description="机台ID（可选）")
    remark: Optional[str] = Field(None, description="备注")


class ProjectBudgetItemUpdate(BaseModel):
    """更新预算明细"""
    cost_category: Optional[str] = Field(None, max_length=50, description="成本类别")
    cost_item: Optional[str] = Field(None, max_length=200, description="成本项")
    description: Optional[str] = Field(None, description="说明")
    budget_amount: Optional[Decimal] = Field(None, description="预算金额")
    machine_id: Optional[int] = Field(None, description="机台ID")
    remark: Optional[str] = Field(None, description="备注")


class ProjectBudgetItemResponse(TimestampSchema):
    """预算明细响应"""
    id: int
    budget_id: int
    item_no: int
    cost_category: str
    cost_item: str
    description: Optional[str] = None
    budget_amount: Decimal
    machine_id: Optional[int] = None
    remark: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProjectBudgetCreate(BaseModel):
    """创建项目预算"""
    project_id: int = Field(..., description="项目ID")
    budget_name: str = Field(..., max_length=200, description="预算名称")
    budget_type: str = Field(default="INITIAL", description="预算类型：INITIAL/REVISED/SUPPLEMENT")
    total_amount: Decimal = Field(..., description="预算总额")
    budget_breakdown: Optional[dict] = Field(None, description="预算明细（JSON格式）")
    effective_date: Optional[date] = Field(None, description="生效日期")
    expiry_date: Optional[date] = Field(None, description="失效日期")
    remark: Optional[str] = Field(None, description="备注")
    items: Optional[List[ProjectBudgetItemCreate]] = Field(default=[], description="预算明细列表")


class ProjectBudgetUpdate(BaseModel):
    """更新项目预算"""
    budget_name: Optional[str] = Field(None, max_length=200, description="预算名称")
    budget_type: Optional[str] = Field(None, description="预算类型")
    total_amount: Optional[Decimal] = Field(None, description="预算总额")
    budget_breakdown: Optional[dict] = Field(None, description="预算明细（JSON格式）")
    effective_date: Optional[date] = Field(None, description="生效日期")
    expiry_date: Optional[date] = Field(None, description="失效日期")
    remark: Optional[str] = Field(None, description="备注")


class ProjectBudgetResponse(TimestampSchema):
    """项目预算响应"""
    id: int
    budget_no: str
    project_id: int
    budget_name: str
    budget_type: str
    version: str
    total_amount: Decimal
    budget_breakdown: Optional[dict] = None
    status: str
    submitted_at: Optional[datetime] = None
    submitted_by: Optional[int] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    approval_note: Optional[str] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    is_active: bool
    remark: Optional[str] = None
    created_by: Optional[int] = None
    
    # 关联信息
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    submitter_name: Optional[str] = None
    approver_name: Optional[str] = None
    items: List[ProjectBudgetItemResponse] = []
    
    class Config:
        from_attributes = True


class ProjectBudgetApproveRequest(BaseModel):
    """预算审批请求"""
    approved: bool = Field(..., description="是否审批通过")
    approval_note: Optional[str] = Field(None, description="审批意见")


# ==================== 成本分摊规则 ====================

class ProjectCostAllocationRuleCreate(BaseModel):
    """创建成本分摊规则"""
    rule_name: str = Field(..., max_length=100, description="规则名称")
    rule_type: str = Field(..., description="分摊类型：PROPORTION/MANUAL")
    allocation_basis: str = Field(..., description="分摊依据：MACHINE_COUNT/REVENUE/MANUAL")
    allocation_formula: Optional[str] = Field(None, description="分摊公式（JSON格式）")
    cost_type: Optional[str] = Field(None, description="适用成本类型")
    cost_category: Optional[str] = Field(None, description="适用成本分类")
    project_ids: Optional[List[int]] = Field(None, description="适用项目ID列表")
    effective_date: Optional[date] = Field(None, description="生效日期")
    expiry_date: Optional[date] = Field(None, description="失效日期")
    remark: Optional[str] = Field(None, description="备注")


class ProjectCostAllocationRuleUpdate(BaseModel):
    """更新成本分摊规则"""
    rule_name: Optional[str] = Field(None, max_length=100, description="规则名称")
    rule_type: Optional[str] = Field(None, description="分摊类型")
    allocation_basis: Optional[str] = Field(None, description="分摊依据")
    allocation_formula: Optional[str] = Field(None, description="分摊公式")
    cost_type: Optional[str] = Field(None, description="适用成本类型")
    cost_category: Optional[str] = Field(None, description="适用成本分类")
    project_ids: Optional[List[int]] = Field(None, description="适用项目ID列表")
    is_active: Optional[bool] = Field(None, description="是否启用")
    effective_date: Optional[date] = Field(None, description="生效日期")
    expiry_date: Optional[date] = Field(None, description="失效日期")
    remark: Optional[str] = Field(None, description="备注")


class ProjectCostAllocationRuleResponse(TimestampSchema):
    """成本分摊规则响应"""
    id: int
    rule_name: str
    rule_type: str
    allocation_basis: str
    allocation_formula: Optional[str] = None
    cost_type: Optional[str] = None
    cost_category: Optional[str] = None
    project_ids: Optional[List[int]] = None
    is_active: bool
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    remark: Optional[str] = None
    created_by: Optional[int] = None
    
    class Config:
        from_attributes = True


class ProjectCostAllocationRequest(BaseModel):
    """成本分摊请求"""
    cost_id: int = Field(..., description="成本记录ID")
    rule_id: Optional[int] = Field(None, description="分摊规则ID（可选，使用规则分摊）")
    allocation_targets: Optional[List[dict]] = Field(None, description="分摊目标列表（手工分摊时使用）")
    # allocation_targets格式: [{"machine_id": 1, "amount": 1000}, {"machine_id": 2, "amount": 2000}]
    # 或 [{"project_id": 1, "amount": 1000}, {"project_id": 2, "amount": 2000}]







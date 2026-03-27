# -*- coding: utf-8 -*-
"""
售前费用管理 Schema
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PresaleExpenseTypeEnum(str, Enum):
    """售前费用类型"""
    TRAVEL = "TRAVEL"          # 差旅
    ENTERTAIN = "ENTERTAIN"    # 招待
    TENDER = "TENDER"          # 投标
    SOLUTION = "SOLUTION"      # 方案制作


class ExpenseApprovalStatus(str, Enum):
    """费用审批状态"""
    PENDING = "PENDING"        # 待审批
    APPROVED = "APPROVED"      # 已通过
    REJECTED = "REJECTED"      # 已驳回


# ========== 费用录入 ==========

class PresaleExpenseCreate(BaseModel):
    """费用录入请求"""
    expense_type: PresaleExpenseTypeEnum = Field(..., description="费用类型")
    amount: float = Field(..., gt=0, description="费用金额")
    expense_date: date = Field(..., description="费用发生日期")
    description: Optional[str] = Field(None, description="费用说明")

    # 关联
    ticket_id: Optional[int] = Field(None, description="关联工单ID")
    opportunity_id: Optional[int] = Field(None, description="关联商机ID")

    # 人员
    user_id: Optional[int] = Field(None, description="费用归属人员ID")
    department_id: Optional[int] = Field(None, description="部门ID")


class PresaleExpenseResponse(BaseModel):
    """费用详情响应"""
    id: int
    expense_type: str
    amount: float
    expense_date: date
    description: Optional[str] = None
    ticket_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    approval_status: str = "PENDING"
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    approval_note: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 费用列表查询 ==========

class ExpenseListQuery(BaseModel):
    """费用列表查询参数"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    expense_type: Optional[str] = None
    approval_status: Optional[str] = None
    ticket_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    user_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


# ========== 费用审批 ==========

class ExpenseApprovalRequest(BaseModel):
    """费用审批请求"""
    expense_id: int = Field(..., description="费用ID")
    action: ExpenseApprovalStatus = Field(..., description="审批动作: APPROVED/REJECTED")
    note: Optional[str] = Field(None, description="审批意见")


# ========== 费用统计 ==========

class ExpenseStatItem(BaseModel):
    """单项统计"""
    label: str
    count: int = 0
    total_amount: float = 0.0


class ExpenseStatsResponse(BaseModel):
    """费用统计响应"""
    period: Dict[str, str]
    total_count: int = 0
    total_amount: float = 0.0
    by_type: List[ExpenseStatItem] = []
    by_user: List[ExpenseStatItem] = []
    by_month: List[ExpenseStatItem] = []

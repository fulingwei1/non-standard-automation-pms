# -*- coding: utf-8 -*-
"""
奖金激励模块 Schema 定义
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import PageParams, PaginatedResponse

# ==================== 奖金规则 ====================

class BonusRuleBase(BaseModel):
    """奖金规则基础模型"""
    rule_code: str = Field(..., description="规则编码")
    rule_name: str = Field(..., description="规则名称")
    bonus_type: str = Field(..., description="奖金类型")
    calculation_formula: Optional[str] = Field(None, description="计算公式说明")
    base_amount: Optional[Decimal] = Field(None, description="基础金额")
    coefficient: Optional[Decimal] = Field(None, description="系数")
    trigger_condition: Optional[Dict[str, Any]] = Field(None, description="触发条件(JSON)")
    apply_to_roles: Optional[List[str]] = Field(None, description="适用角色列表")
    apply_to_depts: Optional[List[int]] = Field(None, description="适用部门列表")
    apply_to_projects: Optional[List[str]] = Field(None, description="适用项目类型列表")
    effective_start_date: Optional[date] = Field(None, description="生效开始日期")
    effective_end_date: Optional[date] = Field(None, description="生效结束日期")
    is_active: bool = Field(True, description="是否启用")
    priority: int = Field(0, description="优先级")
    require_approval: bool = Field(True, description="是否需要审批")
    approval_workflow: Optional[Dict[str, Any]] = Field(None, description="审批流程(JSON)")


class BonusRuleCreate(BonusRuleBase):
    """创建奖金规则"""
    pass


class BonusRuleUpdate(BaseModel):
    """更新奖金规则"""
    rule_name: Optional[str] = None
    bonus_type: Optional[str] = None
    calculation_formula: Optional[str] = None
    base_amount: Optional[Decimal] = None
    coefficient: Optional[Decimal] = None
    trigger_condition: Optional[Dict[str, Any]] = None
    apply_to_roles: Optional[List[str]] = None
    apply_to_depts: Optional[List[int]] = None
    apply_to_projects: Optional[List[str]] = None
    effective_start_date: Optional[date] = None
    effective_end_date: Optional[date] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    require_approval: Optional[bool] = None
    approval_workflow: Optional[Dict[str, Any]] = None


class BonusRuleResponse(BonusRuleBase):
    """奖金规则响应"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 奖金计算 ====================

class BonusCalculationBase(BaseModel):
    """奖金计算基础模型"""
    rule_id: int = Field(..., description="规则ID")
    period_id: Optional[int] = Field(None, description="考核周期ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    milestone_id: Optional[int] = Field(None, description="里程碑ID")
    user_id: int = Field(..., description="受益人ID")
    performance_result_id: Optional[int] = Field(None, description="绩效结果ID")
    project_contribution_id: Optional[int] = Field(None, description="项目贡献ID")
    calculated_amount: Decimal = Field(..., description="计算金额")
    calculation_detail: Optional[Dict[str, Any]] = Field(None, description="计算明细")


class BonusCalculationCreate(BonusCalculationBase):
    """创建奖金计算"""
    pass


class BonusCalculationResponse(BonusCalculationBase):
    """奖金计算响应"""
    id: int
    calculation_code: str
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    approval_comment: Optional[str] = None
    calculated_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BonusCalculationApprove(BaseModel):
    """审批奖金计算"""
    approved: bool = Field(..., description="是否批准")
    comment: Optional[str] = Field(None, description="审批意见")


# ==================== 奖金发放 ====================

class BonusDistributionBase(BaseModel):
    """奖金发放基础模型"""
    calculation_id: int = Field(..., description="计算记录ID")
    user_id: int = Field(..., description="受益人ID")
    distributed_amount: Decimal = Field(..., description="发放金额")
    distribution_date: date = Field(..., description="发放日期")
    payment_method: Optional[str] = Field(None, description="发放方式")
    voucher_no: Optional[str] = Field(None, description="凭证号")
    payment_account: Optional[str] = Field(None, description="付款账户")
    payment_remark: Optional[str] = Field(None, description="付款备注")


class BonusDistributionCreate(BonusDistributionBase):
    """创建奖金发放"""
    pass


class BonusDistributionResponse(BonusDistributionBase):
    """奖金发放响应"""
    id: int
    distribution_code: str
    status: str
    paid_by: Optional[int] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BonusDistributionPay(BaseModel):
    """确认发放"""
    voucher_no: Optional[str] = Field(None, description="凭证号")
    payment_account: Optional[str] = Field(None, description="付款账户")
    payment_remark: Optional[str] = Field(None, description="付款备注")


# ==================== 团队奖金分配 ====================

class TeamBonusAllocationBase(BaseModel):
    """团队奖金分配基础模型"""
    project_id: int = Field(..., description="项目ID")
    period_id: Optional[int] = Field(None, description="周期ID")
    total_bonus_amount: Decimal = Field(..., description="团队总奖金")
    allocation_method: str = Field(..., description="分配方式")
    allocation_detail: List[Dict[str, Any]] = Field(..., description="分配明细")


class TeamBonusAllocationCreate(TeamBonusAllocationBase):
    """创建团队奖金分配"""
    pass


class TeamBonusAllocationResponse(TeamBonusAllocationBase):
    """团队奖金分配响应"""
    id: int
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeamBonusAllocationApprove(BaseModel):
    """审批团队奖金分配"""
    approved: bool = Field(..., description="是否批准")
    comment: Optional[str] = Field(None, description="审批意见")


# ==================== 查询和统计 ====================

class BonusCalculationQuery(PageParams):
    """奖金计算查询"""
    rule_id: Optional[int] = None
    user_id: Optional[int] = None
    project_id: Optional[int] = None
    period_id: Optional[int] = None
    status: Optional[str] = None
    bonus_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class BonusDistributionQuery(PageParams):
    """奖金发放查询"""
    user_id: Optional[int] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class MyBonusResponse(BaseModel):
    """我的奖金响应"""
    total_amount: Decimal = Field(..., description="总金额")
    pending_amount: Decimal = Field(..., description="待发放金额")
    paid_amount: Decimal = Field(..., description="已发放金额")
    calculations: List[BonusCalculationResponse] = Field(default=[], description="计算记录")
    distributions: List[BonusDistributionResponse] = Field(default=[], description="发放记录")


class BonusStatisticsResponse(BaseModel):
    """奖金统计响应"""
    total_calculated: Decimal = Field(..., description="总计算金额")
    total_distributed: Decimal = Field(..., description="总发放金额")
    total_pending: Decimal = Field(..., description="待发放金额")
    calculation_count: int = Field(..., description="计算记录数")
    distribution_count: int = Field(..., description="发放记录数")
    by_type: Dict[str, Decimal] = Field(default={}, description="按类型统计")
    by_department: Dict[str, Decimal] = Field(default={}, description="按部门统计")


# ==================== 计算请求 ====================

class CalculatePerformanceBonusRequest(BaseModel):
    """计算绩效奖金请求"""
    period_id: int = Field(..., description="考核周期ID")
    user_id: Optional[int] = Field(None, description="用户ID（不提供则计算所有用户）")
    rule_id: Optional[int] = Field(None, description="规则ID（不提供则使用所有启用规则）")


class CalculateProjectBonusRequest(BaseModel):
    """计算项目奖金请求"""
    project_id: int = Field(..., description="项目ID")
    rule_id: Optional[int] = Field(None, description="规则ID")


class CalculateMilestoneBonusRequest(BaseModel):
    """计算里程碑奖金请求"""
    milestone_id: int = Field(..., description="里程碑ID")
    rule_id: Optional[int] = Field(None, description="规则ID")


class CalculateTeamBonusRequest(BaseModel):
    """计算团队奖金请求"""
    project_id: int = Field(..., description="项目ID")
    period_id: Optional[int] = Field(None, description="周期ID")
    rule_id: Optional[int] = Field(None, description="规则ID")


class CalculateSalesBonusRequest(BaseModel):
    """计算销售奖金请求"""
    contract_id: int = Field(..., description="合同ID")
    based_on: str = Field("CONTRACT", description="计算依据：CONTRACT（合同签订）/PAYMENT（回款）")
    rule_id: Optional[int] = Field(None, description="规则ID")


class CalculateSalesDirectorBonusRequest(BaseModel):
    """计算销售总监奖金请求"""
    director_id: int = Field(..., description="销售总监ID")
    period_start: date = Field(..., description="统计周期开始日期")
    period_end: date = Field(..., description="统计周期结束日期")
    rule_id: Optional[int] = Field(None, description="规则ID")


class CalculatePresaleBonusRequest(BaseModel):
    """计算售前技术支持奖金请求"""
    ticket_id: int = Field(..., description="售前支持工单ID")
    based_on: str = Field("COMPLETION", description="计算依据：COMPLETION（工单完成）/WON（中标）")
    rule_id: Optional[int] = Field(None, description="规则ID")


# ==================== 奖金分配明细表 ====================

class BonusAllocationSheetResponse(BaseModel):
    """奖金分配明细表响应"""
    id: int
    sheet_code: str
    sheet_name: str
    file_path: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    project_id: Optional[int] = None
    period_id: Optional[int] = None
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    status: str
    parse_result: Optional[Dict[str, Any]] = None
    parse_errors: Optional[Dict[str, Any]] = None
    finance_confirmed: bool = False
    hr_confirmed: bool = False
    manager_confirmed: bool = False
    confirmed_at: Optional[datetime] = None
    distributed_at: Optional[datetime] = None
    distributed_by: Optional[int] = None
    distribution_count: int = 0
    uploaded_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BonusAllocationSheetConfirm(BaseModel):
    """确认分配明细表（线下确认完成）"""
    finance_confirmed: bool = Field(False, description="财务部确认")
    hr_confirmed: bool = Field(False, description="人力资源部确认")
    manager_confirmed: bool = Field(False, description="总经理确认")


class BonusAllocationRow(BaseModel):
    """分配明细表行数据"""
    calculation_id: int = Field(..., description="计算记录ID")
    user_id: int = Field(..., description="受益人ID")
    user_name: Optional[str] = Field(None, description="受益人姓名")
    calculated_amount: Decimal = Field(..., description="计算金额")
    distributed_amount: Decimal = Field(..., description="发放金额")
    distribution_date: date = Field(..., description="发放日期")
    payment_method: Optional[str] = Field(None, description="发放方式")
    voucher_no: Optional[str] = Field(None, description="凭证号")
    payment_account: Optional[str] = Field(None, description="付款账户")
    payment_remark: Optional[str] = Field(None, description="付款备注")


# ==================== 响应类型 ====================

BonusRuleListResponse = PaginatedResponse[BonusRuleResponse]
BonusCalculationListResponse = PaginatedResponse[BonusCalculationResponse]
BonusDistributionListResponse = PaginatedResponse[BonusDistributionResponse]
TeamBonusAllocationListResponse = PaginatedResponse[TeamBonusAllocationResponse]


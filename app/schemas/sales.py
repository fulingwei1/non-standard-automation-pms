# -*- coding: utf-8 -*-
"""
销售管理模块 Schema
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal

from .common import BaseSchema, TimestampSchema


# ==================== 线索 ====================


class LeadCreate(BaseModel):
    """创建线索"""

    lead_code: str = Field(max_length=20, description="线索编码")
    source: Optional[str] = Field(default=None, max_length=50, description="来源")
    customer_name: Optional[str] = Field(default=None, max_length=100, description="客户名称")
    industry: Optional[str] = Field(default=None, max_length=50, description="行业")
    contact_name: Optional[str] = Field(default=None, max_length=50, description="联系人")
    contact_phone: Optional[str] = Field(default=None, max_length=20, description="联系电话")
    demand_summary: Optional[str] = Field(default=None, description="需求摘要")
    owner_id: Optional[int] = Field(default=None, description="负责人ID")
    status: Optional[str] = Field(default="NEW", description="状态")
    next_action_at: Optional[datetime] = Field(default=None, description="下次行动时间")


class LeadUpdate(BaseModel):
    """更新线索"""

    source: Optional[str] = None
    customer_name: Optional[str] = None
    industry: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    demand_summary: Optional[str] = None
    owner_id: Optional[int] = None
    status: Optional[str] = None
    next_action_at: Optional[datetime] = None


class LeadResponse(TimestampSchema):
    """线索响应"""

    id: int
    lead_code: str
    source: Optional[str] = None
    customer_name: Optional[str] = None
    industry: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    demand_summary: Optional[str] = None
    owner_id: Optional[int] = None
    status: str = "NEW"
    next_action_at: Optional[datetime] = None
    owner_name: Optional[str] = None


class LeadFollowUpCreate(BaseModel):
    """创建线索跟进记录"""

    follow_up_type: str = Field(max_length=20, description="跟进类型：CALL/EMAIL/VISIT/MEETING/OTHER")
    content: str = Field(description="跟进内容")
    next_action: Optional[str] = Field(default=None, description="下一步行动")
    next_action_at: Optional[datetime] = Field(default=None, description="下次行动时间")
    attachments: Optional[str] = Field(default=None, description="附件列表JSON")


class LeadFollowUpResponse(TimestampSchema):
    """线索跟进记录响应"""

    id: int
    lead_id: int
    follow_up_type: str
    content: str
    next_action: Optional[str] = None
    next_action_at: Optional[datetime] = None
    created_by: int
    attachments: Optional[str] = None
    creator_name: Optional[str] = None


# ==================== 商机 ====================


class OpportunityRequirementCreate(BaseModel):
    """创建商机需求"""

    product_object: Optional[str] = Field(default=None, max_length=100, description="产品对象")
    ct_seconds: Optional[int] = Field(default=None, description="节拍(秒)")
    interface_desc: Optional[str] = Field(default=None, description="接口/通信协议")
    site_constraints: Optional[str] = Field(default=None, description="现场约束")
    acceptance_criteria: Optional[str] = Field(default=None, description="验收依据")
    safety_requirement: Optional[str] = Field(default=None, description="安全要求")
    attachments: Optional[str] = Field(default=None, description="需求附件")
    extra_json: Optional[str] = Field(default=None, description="其他补充(JSON)")


class OpportunityRequirementResponse(TimestampSchema):
    """商机需求响应"""

    id: int
    opportunity_id: int
    product_object: Optional[str] = None
    ct_seconds: Optional[int] = None
    interface_desc: Optional[str] = None
    site_constraints: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    safety_requirement: Optional[str] = None
    attachments: Optional[str] = None
    extra_json: Optional[str] = None


class OpportunityCreate(BaseModel):
    """创建商机"""

    opp_code: str = Field(max_length=20, description="商机编码")
    lead_id: Optional[int] = Field(default=None, description="线索ID")
    customer_id: int = Field(description="客户ID")
    opp_name: str = Field(max_length=200, description="商机名称")
    project_type: Optional[str] = Field(default=None, max_length=20, description="项目类型")
    equipment_type: Optional[str] = Field(default=None, max_length=20, description="设备类型")
    stage: Optional[str] = Field(default="DISCOVERY", description="阶段")
    est_amount: Optional[Decimal] = Field(default=None, description="预估金额")
    est_margin: Optional[Decimal] = Field(default=None, description="预估毛利率")
    budget_range: Optional[str] = Field(default=None, max_length=50, description="预算范围")
    decision_chain: Optional[str] = Field(default=None, description="决策链")
    delivery_window: Optional[str] = Field(default=None, max_length=50, description="交付窗口")
    acceptance_basis: Optional[str] = Field(default=None, description="验收依据")
    score: Optional[int] = Field(default=0, description="评分")
    risk_level: Optional[str] = Field(default=None, max_length=10, description="风险等级")
    owner_id: Optional[int] = Field(default=None, description="负责人ID")
    gate_status: Optional[str] = Field(default="PENDING", description="阶段门状态")
    requirement: Optional[OpportunityRequirementCreate] = Field(default=None, description="需求信息")


class OpportunityUpdate(BaseModel):
    """更新商机"""

    opp_name: Optional[str] = None
    project_type: Optional[str] = None
    equipment_type: Optional[str] = None
    stage: Optional[str] = None
    est_amount: Optional[Decimal] = None
    est_margin: Optional[Decimal] = None
    budget_range: Optional[str] = None
    decision_chain: Optional[str] = None
    delivery_window: Optional[str] = None
    acceptance_basis: Optional[str] = None
    score: Optional[int] = None
    risk_level: Optional[str] = None
    owner_id: Optional[int] = None
    gate_status: Optional[str] = None


class OpportunityResponse(TimestampSchema):
    """商机响应"""

    id: int
    opp_code: str
    lead_id: Optional[int] = None
    customer_id: int
    customer_name: Optional[str] = None
    opp_name: str
    project_type: Optional[str] = None
    equipment_type: Optional[str] = None
    stage: str = "DISCOVERY"
    est_amount: Optional[Decimal] = None
    est_margin: Optional[Decimal] = None
    budget_range: Optional[str] = None
    decision_chain: Optional[str] = None
    delivery_window: Optional[str] = None
    acceptance_basis: Optional[str] = None
    score: int = 0
    risk_level: Optional[str] = None
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None
    gate_status: str = "PENDING"
    gate_passed_at: Optional[datetime] = None
    requirement: Optional[OpportunityRequirementResponse] = None


class GateSubmitRequest(BaseModel):
    """阶段门提交请求"""

    gate_status: str = Field(description="阶段门状态: PASS/REJECT")
    remark: Optional[str] = Field(default=None, description="备注")


# ==================== 报价 ====================


class QuoteItemCreate(BaseModel):
    """创建报价明细"""

    item_type: Optional[str] = Field(default=None, max_length=20, description="明细类型")
    item_name: Optional[str] = Field(default=None, max_length=200, description="明细名称")
    qty: Optional[Decimal] = Field(default=None, description="数量")
    unit_price: Optional[Decimal] = Field(default=None, description="单价")
    cost: Optional[Decimal] = Field(default=None, description="成本")
    lead_time_days: Optional[int] = Field(default=None, description="交期(天)")
    remark: Optional[str] = Field(default=None, description="备注")


class QuoteItemResponse(BaseSchema):
    """报价明细响应"""

    id: int
    quote_version_id: int
    item_type: Optional[str] = None
    item_name: Optional[str] = None
    qty: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    lead_time_days: Optional[int] = None
    remark: Optional[str] = None


class QuoteVersionCreate(BaseModel):
    """创建报价版本"""

    version_no: str = Field(max_length=10, description="版本号")
    total_price: Optional[Decimal] = Field(default=None, description="总价")
    cost_total: Optional[Decimal] = Field(default=None, description="成本总计")
    gross_margin: Optional[Decimal] = Field(default=None, description="毛利率")
    lead_time_days: Optional[int] = Field(default=None, description="交期(天)")
    risk_terms: Optional[str] = Field(default=None, description="风险条款")
    delivery_date: Optional[date] = Field(default=None, description="交付日期")
    items: Optional[List[QuoteItemCreate]] = Field(default=[], description="报价明细")


class QuoteVersionResponse(TimestampSchema):
    """报价版本响应"""

    id: int
    quote_id: int
    version_no: str
    total_price: Optional[Decimal] = None
    cost_total: Optional[Decimal] = None
    gross_margin: Optional[Decimal] = None
    lead_time_days: Optional[int] = None
    risk_terms: Optional[str] = None
    delivery_date: Optional[date] = None
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    approved_by: Optional[int] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    items: List[QuoteItemResponse] = []


class QuoteCreate(BaseModel):
    """创建报价"""

    quote_code: str = Field(max_length=20, description="报价编码")
    opportunity_id: int = Field(description="商机ID")
    customer_id: int = Field(description="客户ID")
    status: Optional[str] = Field(default="DRAFT", description="状态")
    valid_until: Optional[date] = Field(default=None, description="有效期至")
    owner_id: Optional[int] = Field(default=None, description="负责人ID")
    version: Optional[QuoteVersionCreate] = Field(default=None, description="初始版本")


class QuoteUpdate(BaseModel):
    """更新报价"""

    status: Optional[str] = None
    valid_until: Optional[date] = None
    owner_id: Optional[int] = None
    current_version_id: Optional[int] = None


class QuoteResponse(TimestampSchema):
    """报价响应"""

    id: int
    quote_code: str
    opportunity_id: int
    opportunity_code: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    status: str = "DRAFT"
    current_version_id: Optional[int] = None
    valid_until: Optional[date] = None
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None
    current_version: Optional[QuoteVersionResponse] = None
    versions: List[QuoteVersionResponse] = []


class QuoteApproveRequest(BaseModel):
    """报价审批请求"""

    approved: bool = Field(description="是否批准")
    remark: Optional[str] = Field(default=None, description="备注")


# ==================== 合同 ====================


class ContractDeliverableCreate(BaseModel):
    """创建合同交付物"""

    deliverable_name: Optional[str] = Field(default=None, max_length=100, description="交付物名称")
    deliverable_type: Optional[str] = Field(default=None, max_length=50, description="交付物类型")
    required_for_payment: Optional[bool] = Field(default=True, description="是否付款必需")
    template_ref: Optional[str] = Field(default=None, max_length=100, description="模板引用")


class ContractDeliverableResponse(TimestampSchema):
    """合同交付物响应"""

    id: int
    contract_id: int
    deliverable_name: Optional[str] = None
    deliverable_type: Optional[str] = None
    required_for_payment: bool = True
    template_ref: Optional[str] = None


class ContractCreate(BaseModel):
    """创建合同"""

    contract_code: str = Field(max_length=20, description="合同编码")
    opportunity_id: int = Field(description="商机ID")
    quote_version_id: Optional[int] = Field(default=None, description="报价版本ID")
    customer_id: int = Field(description="客户ID")
    contract_amount: Optional[Decimal] = Field(default=None, description="合同金额")
    signed_date: Optional[date] = Field(default=None, description="签订日期")
    status: Optional[str] = Field(default="DRAFT", description="状态")
    payment_terms_summary: Optional[str] = Field(default=None, description="付款条款摘要")
    acceptance_summary: Optional[str] = Field(default=None, description="验收摘要")
    owner_id: Optional[int] = Field(default=None, description="负责人ID")
    deliverables: Optional[List[ContractDeliverableCreate]] = Field(default=[], description="交付物清单")


class ContractUpdate(BaseModel):
    """更新合同"""

    contract_amount: Optional[Decimal] = None
    signed_date: Optional[date] = None
    status: Optional[str] = None
    payment_terms_summary: Optional[str] = None
    acceptance_summary: Optional[str] = None
    owner_id: Optional[int] = None


class ContractResponse(TimestampSchema):
    """合同响应"""

    id: int
    contract_code: str
    opportunity_id: int
    opportunity_code: Optional[str] = None
    quote_version_id: Optional[int] = None
    customer_id: int
    customer_name: Optional[str] = None
    project_id: Optional[int] = None
    project_code: Optional[str] = None
    contract_amount: Optional[Decimal] = None
    signed_date: Optional[date] = None
    status: str = "DRAFT"
    payment_terms_summary: Optional[str] = None
    acceptance_summary: Optional[str] = None
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None
    deliverables: List[ContractDeliverableResponse] = []


class ContractAmendmentCreate(BaseModel):
    """创建合同变更记录"""

    amendment_type: str = Field(max_length=20, description="变更类型：AMOUNT/DELIVERY_DATE/TERMS/OTHER")
    title: str = Field(max_length=200, description="变更标题")
    description: str = Field(description="变更描述")
    reason: Optional[str] = Field(default=None, description="变更原因")
    old_value: Optional[str] = Field(default=None, description="原值（JSON）")
    new_value: Optional[str] = Field(default=None, description="新值（JSON）")
    amount_change: Optional[Decimal] = Field(default=None, description="金额变化")
    schedule_impact: Optional[str] = Field(default=None, description="进度影响")
    other_impact: Optional[str] = Field(default=None, description="其他影响")
    request_date: date = Field(description="申请日期")
    attachments: Optional[str] = Field(default=None, description="附件列表JSON")


class ContractAmendmentResponse(TimestampSchema):
    """合同变更记录响应"""

    id: int
    contract_id: int
    amendment_no: str
    amendment_type: str
    title: str
    description: str
    reason: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    amount_change: Optional[Decimal] = None
    schedule_impact: Optional[str] = None
    other_impact: Optional[str] = None
    requestor_id: int
    requestor_name: Optional[str] = None
    request_date: date
    status: str = "PENDING"
    approver_id: Optional[int] = None
    approver_name: Optional[str] = None
    approval_date: Optional[date] = None
    approval_comment: Optional[str] = None
    attachments: Optional[str] = None


class ContractSignRequest(BaseModel):
    """合同签订请求"""

    signed_date: date = Field(description="签订日期")
    remark: Optional[str] = Field(default=None, description="备注")


class ContractProjectCreateRequest(BaseModel):
    """合同生成项目请求"""

    project_code: str = Field(max_length=50, description="项目编码")
    project_name: str = Field(max_length=200, description="项目名称")
    pm_id: Optional[int] = Field(default=None, description="项目经理ID")
    planned_start_date: Optional[date] = Field(default=None, description="计划开始日期")
    planned_end_date: Optional[date] = Field(default=None, description="计划结束日期")


# ==================== 发票 ====================


class InvoiceCreate(BaseModel):
    """创建发票"""

    invoice_code: str = Field(max_length=30, description="发票编码")
    contract_id: int = Field(description="合同ID")
    project_id: Optional[int] = Field(default=None, description="项目ID")
    payment_id: Optional[int] = Field(default=None, description="关联应收节点ID")
    invoice_type: Optional[str] = Field(default=None, max_length=20, description="发票类型")
    amount: Optional[Decimal] = Field(default=None, description="金额")
    tax_rate: Optional[Decimal] = Field(default=None, description="税率")
    status: Optional[str] = Field(default="DRAFT", description="状态")
    issue_date: Optional[date] = Field(default=None, description="开票日期")
    buyer_name: Optional[str] = Field(default=None, max_length=100, description="购买方名称")
    buyer_tax_no: Optional[str] = Field(default=None, max_length=30, description="购买方税号")


class InvoiceUpdate(BaseModel):
    """更新发票"""

    invoice_type: Optional[str] = None
    amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    status: Optional[str] = None
    issue_date: Optional[date] = None
    buyer_name: Optional[str] = None
    buyer_tax_no: Optional[str] = None


class InvoiceResponse(TimestampSchema):
    """发票响应"""

    id: int
    invoice_code: str
    contract_id: int
    contract_code: Optional[str] = None
    project_id: Optional[int] = None
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    customer_name: Optional[str] = None
    payment_id: Optional[int] = None
    invoice_type: Optional[str] = None
    amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    status: str = "DRAFT"
    payment_status: Optional[str] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    paid_amount: Optional[Decimal] = None
    paid_date: Optional[date] = None
    buyer_name: Optional[str] = None
    buyer_tax_no: Optional[str] = None
    remark: Optional[str] = None


class InvoiceIssueRequest(BaseModel):
    """发票开票请求"""

    issue_date: date = Field(description="开票日期")
    remark: Optional[str] = Field(default=None, description="备注")


# ==================== 回款争议 ====================


class ReceivableDisputeCreate(BaseModel):
    """创建回款争议"""

    payment_id: int = Field(description="付款节点ID")
    reason_code: Optional[str] = Field(default=None, max_length=30, description="原因代码")
    description: Optional[str] = Field(default=None, description="描述")
    status: Optional[str] = Field(default="OPEN", description="状态")
    responsible_dept: Optional[str] = Field(default=None, max_length=50, description="责任部门")
    responsible_id: Optional[int] = Field(default=None, description="责任人ID")
    expect_resolve_date: Optional[date] = Field(default=None, description="预期解决日期")


class ReceivableDisputeUpdate(BaseModel):
    """更新回款争议"""

    reason_code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    responsible_dept: Optional[str] = None
    responsible_id: Optional[int] = None
    expect_resolve_date: Optional[date] = None


class ReceivableDisputeResponse(TimestampSchema):
    """回款争议响应"""

    id: int
    payment_id: int
    reason_code: Optional[str] = None
    description: Optional[str] = None
    status: str = "OPEN"
    responsible_dept: Optional[str] = None
    responsible_id: Optional[int] = None
    responsible_name: Optional[str] = None
    expect_resolve_date: Optional[date] = None


# ==================== 审批相关 ====================


class QuoteApprovalResponse(TimestampSchema):
    """报价审批响应"""

    id: int
    quote_id: int
    approval_level: int
    approval_role: str
    approver_id: Optional[int] = None
    approver_name: Optional[str] = None
    approval_result: Optional[str] = None
    approval_opinion: Optional[str] = None
    status: str = "PENDING"
    approved_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    is_overdue: bool = False


class QuoteApprovalCreate(BaseModel):
    """创建报价审批"""

    quote_id: int
    approval_level: int
    approval_role: str
    approver_id: Optional[int] = None
    due_date: Optional[datetime] = None


class ContractApprovalResponse(TimestampSchema):
    """合同审批响应"""

    id: int
    contract_id: int
    approval_level: int
    approval_role: str
    approver_id: Optional[int] = None
    approver_name: Optional[str] = None
    approval_result: Optional[str] = None
    approval_opinion: Optional[str] = None
    status: str = "PENDING"
    approved_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    is_overdue: bool = False


class ContractApprovalCreate(BaseModel):
    """创建合同审批"""

    contract_id: int
    approval_level: int
    approval_role: str
    approver_id: Optional[int] = None
    due_date: Optional[datetime] = None


class InvoiceApprovalResponse(TimestampSchema):
    """发票审批响应"""

    id: int
    invoice_id: int
    approval_level: int
    approval_role: str
    approver_id: Optional[int] = None
    approver_name: Optional[str] = None
    approval_result: Optional[str] = None
    approval_opinion: Optional[str] = None
    status: str = "PENDING"
    approved_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    is_overdue: bool = False


class InvoiceApprovalCreate(BaseModel):
    """创建发票审批"""

    invoice_id: int
    approval_level: int
    approval_role: str
    approver_id: Optional[int] = None
    due_date: Optional[datetime] = None


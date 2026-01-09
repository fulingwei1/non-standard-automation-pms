# -*- coding: utf-8 -*-
"""
销售管理模块 Schema
"""

from typing import Optional, List, Dict, Any
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
    # 成本管理扩展字段
    cost_category: Optional[str] = Field(default=None, max_length=50, description="成本分类")
    cost_source: Optional[str] = Field(default=None, max_length=50, description="成本来源：TEMPLATE/MANUAL/HISTORY")
    specification: Optional[str] = Field(default=None, description="规格型号")
    unit: Optional[str] = Field(default=None, max_length=20, description="单位")


class QuoteItemUpdate(BaseModel):
    """更新报价明细"""

    id: Optional[int] = Field(default=None, description="明细ID（更新时必填）")
    item_type: Optional[str] = None
    item_name: Optional[str] = None
    qty: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    lead_time_days: Optional[int] = None
    remark: Optional[str] = None
    # 成本管理扩展字段
    cost_category: Optional[str] = None
    cost_source: Optional[str] = None
    specification: Optional[str] = None
    unit: Optional[str] = None


class QuoteItemBatchUpdate(BaseModel):
    """批量更新报价明细"""

    items: List[QuoteItemUpdate] = Field(description="报价明细列表（包含id的为更新，不包含id的为新增）")


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
    # 成本管理扩展字段
    cost_category: Optional[str] = None
    cost_source: Optional[str] = None
    specification: Optional[str] = None
    unit: Optional[str] = None


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


# ==================== 报价成本管理 ====================


class QuoteCostTemplateCreate(BaseModel):
    """创建报价成本模板"""
    
    template_code: str = Field(max_length=50, description="模板编码")
    template_name: str = Field(max_length=200, description="模板名称")
    template_type: Optional[str] = Field(default=None, max_length=50, description="模板类型：STANDARD/CUSTOM/PROJECT")
    equipment_type: Optional[str] = Field(default=None, max_length=50, description="适用设备类型")
    industry: Optional[str] = Field(default=None, max_length=50, description="适用行业")
    cost_structure: Optional[dict] = Field(default=None, description="成本结构（JSON）")
    description: Optional[str] = Field(default=None, description="模板说明")


class QuoteCostTemplateUpdate(BaseModel):
    """更新报价成本模板"""
    
    template_name: Optional[str] = Field(default=None, max_length=200)
    template_type: Optional[str] = Field(default=None, max_length=50)
    equipment_type: Optional[str] = Field(default=None, max_length=50)
    industry: Optional[str] = Field(default=None, max_length=50)
    cost_structure: Optional[dict] = Field(default=None)
    description: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class QuoteCostTemplateResponse(TimestampSchema):
    """报价成本模板响应"""
    
    id: int
    template_code: str
    template_name: str
    template_type: Optional[str] = None
    equipment_type: Optional[str] = None
    industry: Optional[str] = None
    cost_structure: Optional[dict] = None
    total_cost: Optional[Decimal] = None
    cost_categories: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    usage_count: int = 0
    created_by: Optional[int] = None
    creator_name: Optional[str] = None


class QuoteCostApprovalCreate(BaseModel):
    """创建报价成本审批"""
    
    quote_id: int = Field(description="报价ID")
    quote_version_id: int = Field(description="报价版本ID")
    approval_level: int = Field(default=1, description="审批层级")
    comment: Optional[str] = Field(default=None, description="审批意见")


class QuoteCostApprovalResponse(TimestampSchema):
    """报价成本审批响应"""
    
    id: int
    quote_id: int
    quote_version_id: int
    approval_status: str = "PENDING"
    approval_level: int = 1
    current_approver_id: Optional[int] = None
    current_approver_name: Optional[str] = None
    total_price: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    gross_margin: Optional[Decimal] = None
    margin_threshold: Decimal = 20.00
    margin_status: Optional[str] = None
    cost_complete: bool = False
    delivery_check: bool = False
    risk_terms_check: bool = False
    approval_comment: Optional[str] = None
    approved_by: Optional[int] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_reason: Optional[str] = None


class QuoteCostApprovalAction(BaseModel):
    """报价成本审批操作"""
    
    action: str = Field(description="操作：APPROVE/REJECT")
    comment: Optional[str] = Field(default=None, description="审批意见")
    reason: Optional[str] = Field(default=None, description="驳回原因（REJECT时必填）")


class CostBreakdownResponse(BaseModel):
    """成本拆解响应"""
    
    total_price: Decimal
    total_cost: Decimal
    gross_margin: Decimal
    breakdown: List[dict] = Field(description="成本明细列表")


class CostCheckResponse(BaseModel):
    """成本检查响应"""
    
    is_complete: bool
    checks: List[dict] = Field(description="检查项列表")
    total_price: Decimal
    total_cost: Decimal
    gross_margin: Decimal


class CostComparisonResponse(BaseModel):
    """成本对比响应"""
    
    current_version: Optional[Dict[str, Any]] = None
    previous_version: Optional[Dict[str, Any]] = None
    comparison: Optional[Dict[str, Any]] = None
    breakdown_comparison: Optional[List[Dict[str, Any]]] = None


# ==================== 采购物料成本清单 ====================


class PurchaseMaterialCostCreate(BaseModel):
    """创建采购物料成本"""
    
    material_code: Optional[str] = Field(default=None, max_length=50, description="物料编码")
    material_name: str = Field(max_length=200, description="物料名称")
    specification: Optional[str] = Field(default=None, max_length=500, description="规格型号")
    brand: Optional[str] = Field(default=None, max_length=100, description="品牌")
    unit: Optional[str] = Field(default="件", max_length=20, description="单位")
    material_type: Optional[str] = Field(default=None, max_length=50, description="物料类型")
    is_standard_part: bool = Field(default=True, description="是否标准件")
    unit_cost: Decimal = Field(description="单位成本")
    currency: Optional[str] = Field(default="CNY", max_length=10, description="币种")
    supplier_id: Optional[int] = Field(default=None, description="供应商ID")
    supplier_name: Optional[str] = Field(default=None, max_length=200, description="供应商名称")
    purchase_date: Optional[date] = Field(default=None, description="采购日期")
    purchase_order_no: Optional[str] = Field(default=None, max_length=50, description="采购订单号")
    purchase_quantity: Optional[Decimal] = Field(default=None, description="采购数量")
    lead_time_days: Optional[int] = Field(default=None, description="交期(天)")
    is_active: bool = Field(default=True, description="是否启用")
    match_priority: Optional[int] = Field(default=0, description="匹配优先级")
    match_keywords: Optional[str] = Field(default=None, description="匹配关键词（逗号分隔）")
    remark: Optional[str] = Field(default=None, description="备注")


class PurchaseMaterialCostUpdate(BaseModel):
    """更新采购物料成本"""
    
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    specification: Optional[str] = None
    brand: Optional[str] = None
    unit: Optional[str] = None
    material_type: Optional[str] = None
    is_standard_part: Optional[bool] = None
    unit_cost: Optional[Decimal] = None
    currency: Optional[str] = None
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_order_no: Optional[str] = None
    purchase_quantity: Optional[Decimal] = None
    lead_time_days: Optional[int] = None
    is_active: Optional[bool] = None
    match_priority: Optional[int] = None
    match_keywords: Optional[str] = None
    remark: Optional[str] = None


class PurchaseMaterialCostResponse(TimestampSchema):
    """采购物料成本响应"""
    
    id: int
    material_code: Optional[str] = None
    material_name: str
    specification: Optional[str] = None
    brand: Optional[str] = None
    unit: str = "件"
    material_type: Optional[str] = None
    is_standard_part: bool = True
    unit_cost: Decimal
    currency: str = "CNY"
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_order_no: Optional[str] = None
    purchase_quantity: Optional[Decimal] = None
    lead_time_days: Optional[int] = None
    is_active: bool = True
    match_priority: int = 0
    match_keywords: Optional[str] = None
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    remark: Optional[str] = None
    submitted_by: Optional[int] = None
    submitter_name: Optional[str] = None


class MaterialCostMatchRequest(BaseModel):
    """物料成本匹配请求"""
    
    item_name: str = Field(description="物料名称")
    specification: Optional[str] = Field(default=None, description="规格型号")
    material_type: Optional[str] = Field(default=None, description="物料类型")


class MaterialCostMatchResponse(BaseModel):
    """物料成本匹配响应"""
    
    matched: bool = Field(description="是否匹配成功")
    match_score: Optional[float] = Field(default=None, description="匹配度（0-100）")
    matched_cost: Optional[PurchaseMaterialCostResponse] = Field(default=None, description="匹配到的成本信息")
    suggestions: Optional[List[PurchaseMaterialCostResponse]] = Field(default=[], description="推荐的成本选项")


class CostComparisonResponse(BaseModel):
    """成本对比响应"""
    
    current_version: dict
    previous_version: Optional[dict] = None
    comparison: Optional[dict] = None
    breakdown_comparison: Optional[List[dict]] = None


# ==================== 采购物料成本清单 ====================


class PurchaseMaterialCostCreate(BaseModel):
    """创建采购物料成本"""
    
    material_code: Optional[str] = Field(default=None, max_length=50, description="物料编码")
    material_name: str = Field(max_length=200, description="物料名称")
    specification: Optional[str] = Field(default=None, max_length=500, description="规格型号")
    brand: Optional[str] = Field(default=None, max_length=100, description="品牌")
    unit: Optional[str] = Field(default="件", max_length=20, description="单位")
    material_type: Optional[str] = Field(default=None, max_length=50, description="物料类型")
    is_standard_part: bool = Field(default=True, description="是否标准件")
    unit_cost: Decimal = Field(description="单位成本")
    currency: Optional[str] = Field(default="CNY", max_length=10, description="币种")
    supplier_id: Optional[int] = Field(default=None, description="供应商ID")
    supplier_name: Optional[str] = Field(default=None, max_length=200, description="供应商名称")
    purchase_date: Optional[date] = Field(default=None, description="采购日期")
    purchase_order_no: Optional[str] = Field(default=None, max_length=50, description="采购订单号")
    purchase_quantity: Optional[Decimal] = Field(default=None, description="采购数量")
    lead_time_days: Optional[int] = Field(default=None, description="交期(天)")
    is_active: bool = Field(default=True, description="是否启用")
    match_priority: Optional[int] = Field(default=0, description="匹配优先级")
    match_keywords: Optional[str] = Field(default=None, description="匹配关键词（逗号分隔）")
    remark: Optional[str] = Field(default=None, description="备注")


class PurchaseMaterialCostUpdate(BaseModel):
    """更新采购物料成本"""
    
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    specification: Optional[str] = None
    brand: Optional[str] = None
    unit: Optional[str] = None
    material_type: Optional[str] = None
    is_standard_part: Optional[bool] = None
    unit_cost: Optional[Decimal] = None
    currency: Optional[str] = None
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_order_no: Optional[str] = None
    purchase_quantity: Optional[Decimal] = None
    lead_time_days: Optional[int] = None
    is_active: Optional[bool] = None
    match_priority: Optional[int] = None
    match_keywords: Optional[str] = None
    remark: Optional[str] = None


class PurchaseMaterialCostResponse(TimestampSchema):
    """采购物料成本响应"""
    
    id: int
    material_code: Optional[str] = None
    material_name: str
    specification: Optional[str] = None
    brand: Optional[str] = None
    unit: str = "件"
    material_type: Optional[str] = None
    is_standard_part: bool = True
    unit_cost: Decimal
    currency: str = "CNY"
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_order_no: Optional[str] = None
    purchase_quantity: Optional[Decimal] = None
    lead_time_days: Optional[int] = None
    is_active: bool = True
    match_priority: int = 0
    match_keywords: Optional[str] = None
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    remark: Optional[str] = None
    submitted_by: Optional[int] = None
    submitter_name: Optional[str] = None


class MaterialCostMatchRequest(BaseModel):
    """物料成本匹配请求"""
    
    item_name: str = Field(description="物料名称")
    specification: Optional[str] = Field(default=None, description="规格型号")
    material_type: Optional[str] = Field(default=None, description="物料类型")


class MaterialCostMatchResponse(BaseModel):
    """物料成本匹配响应"""
    
    matched: bool = Field(description="是否匹配成功")
    match_score: Optional[float] = Field(default=None, description="匹配度（0-100）")
    matched_cost: Optional[PurchaseMaterialCostResponse] = Field(default=None, description="匹配到的成本信息")
    suggestions: Optional[List[PurchaseMaterialCostResponse]] = Field(default=[], description="推荐的成本选项")


class CostMatchSuggestion(BaseModel):
    """成本匹配建议"""
    
    item_id: int = Field(description="报价明细项ID")
    item_name: str = Field(description="物料名称")
    current_cost: Optional[Decimal] = Field(default=None, description="当前成本")
    suggested_cost: Optional[Decimal] = Field(default=None, description="建议成本")
    match_score: Optional[float] = Field(default=None, description="匹配度（0-100）")
    suggested_specification: Optional[str] = Field(default=None, description="建议规格")
    suggested_unit: Optional[str] = Field(default=None, description="建议单位")
    suggested_lead_time_days: Optional[int] = Field(default=None, description="建议交期（天）")
    suggested_cost_category: Optional[str] = Field(default=None, description="建议成本类别")
    reason: Optional[str] = Field(default=None, description="匹配原因")
    warnings: Optional[List[str]] = Field(default_factory=list, description="警告信息")
    matched_cost_id: Optional[int] = Field(default=None, description="匹配到的成本记录ID")
    matched_cost_record: Optional[PurchaseMaterialCostResponse] = Field(default=None, description="匹配到的成本记录详情")


class CostMatchSuggestionsResponse(BaseModel):
    """成本匹配建议响应"""
    
    suggestions: List[CostMatchSuggestion] = Field(default_factory=list, description="匹配建议列表")
    total_items: int = Field(default=0, description="总项目数")
    matched_count: int = Field(default=0, description="匹配成功数量")
    unmatched_count: int = Field(default=0, description="未匹配数量")
    warnings: Optional[List[str]] = Field(default=None, description="全局警告信息")
    summary: Optional[Dict[str, Any]] = Field(default=None, description="汇总信息（总成本、毛利率等）")


class ApplyCostSuggestionsRequest(BaseModel):
    """应用成本建议请求"""
    
    suggestions: List[Dict[str, Any]] = Field(description="要应用的建议列表，每个建议包含 item_id 和要更新的字段")


class MaterialCostUpdateReminderUpdate(BaseModel):
    """更新物料成本更新提醒配置"""
    
    reminder_type: Optional[str] = Field(None, description="提醒类型：PERIODIC（定期）/MANUAL（手动）")
    reminder_interval_days: Optional[int] = Field(None, description="提醒间隔（天）")
    next_reminder_date: Optional[date] = Field(None, description="下次提醒日期")
    is_enabled: Optional[bool] = Field(None, description="是否启用提醒")
    material_type_filter: Optional[str] = Field(None, description="物料类型筛选")
    include_standard: Optional[bool] = Field(None, description="包含标准件")
    include_non_standard: Optional[bool] = Field(None, description="包含非标准件")
    notify_roles: Optional[List[str]] = Field(None, description="通知角色列表")
    notify_users: Optional[List[int]] = Field(None, description="通知用户ID列表")


class MaterialCostUpdateReminderResponse(TimestampSchema):
    """物料成本更新提醒响应"""
    
    id: int
    reminder_type: str
    reminder_interval_days: int
    last_reminder_date: Optional[date] = None
    next_reminder_date: Optional[date] = None
    is_enabled: bool
    material_type_filter: Optional[str] = None
    include_standard: bool
    include_non_standard: bool
    notify_roles: Optional[List[str]] = None
    notify_users: Optional[List[int]] = None
    reminder_count: int
    last_updated_by: Optional[int] = None
    last_updated_at: Optional[datetime] = None
    days_until_next: Optional[int] = None  # 距离下次提醒的天数
    is_due: bool = False  # 是否到期
    
    class Config:
        from_attributes = True


# ==================== 报价/合同模板 & CPQ ====================


class QuoteTemplateVersionCreate(BaseModel):
    """创建报价模板版本"""

    version_no: str = Field(max_length=20, description="版本号")
    sections: Optional[Dict[str, Any]] = Field(default_factory=dict, description="模板结构")
    pricing_rules: Optional[Dict[str, Any]] = Field(default_factory=dict, description="价格规则")
    config_schema: Optional[Dict[str, Any]] = Field(default_factory=dict, description="配置项定义")
    discount_rules: Optional[Dict[str, Any]] = Field(default_factory=dict, description="折扣规则")
    release_notes: Optional[str] = Field(default=None, description="版本说明")
    rule_set_id: Optional[int] = Field(default=None, description="关联规则集")


class QuoteTemplateCreate(BaseModel):
    """创建报价模板"""

    template_code: str = Field(max_length=50, description="模板编码")
    template_name: str = Field(max_length=200, description="模板名称")
    category: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = None
    visibility_scope: Optional[str] = Field(default="TEAM", description="可见范围")
    is_default: Optional[bool] = False
    owner_id: Optional[int] = None
    initial_version: Optional[QuoteTemplateVersionCreate] = Field(default=None, description="初始版本")


class QuoteTemplateUpdate(BaseModel):
    """更新报价模板"""

    template_name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    visibility_scope: Optional[str] = None
    is_default: Optional[bool] = None
    owner_id: Optional[int] = None
    current_version_id: Optional[int] = None


class QuoteTemplateVersionResponse(TimestampSchema):
    """报价模板版本响应"""

    id: int
    template_id: int
    version_no: str
    status: str = "DRAFT"
    sections: Optional[Dict[str, Any]] = None
    pricing_rules: Optional[Dict[str, Any]] = None
    config_schema: Optional[Dict[str, Any]] = None
    discount_rules: Optional[Dict[str, Any]] = None
    release_notes: Optional[str] = None
    rule_set_id: Optional[int] = None
    created_by: Optional[int] = None
    published_by: Optional[int] = None
    published_at: Optional[datetime] = None


class QuoteTemplateResponse(TimestampSchema):
    """报价模板响应"""

    id: int
    template_code: str
    template_name: str
    category: Optional[str] = None
    description: Optional[str] = None
    status: str = "DRAFT"
    visibility_scope: str = "TEAM"
    is_default: bool = False
    current_version_id: Optional[int] = None
    owner_id: Optional[int] = None
    versions: List[QuoteTemplateVersionResponse] = []


class ContractTemplateVersionCreate(BaseModel):
    """创建合同模板版本"""

    version_no: str = Field(max_length=20, description="版本号")
    clause_sections: Optional[Dict[str, Any]] = Field(default_factory=dict, description="条款章节")
    clause_library: Optional[Dict[str, Any]] = Field(default_factory=dict, description="条款库引用")
    attachment_refs: Optional[Dict[str, Any]] = Field(default_factory=dict, description="附件引用")
    approval_flow: Optional[Dict[str, Any]] = Field(default_factory=dict, description="审批流配置")
    release_notes: Optional[str] = Field(default=None, description="版本说明")


class ContractTemplateCreate(BaseModel):
    """创建合同模板"""

    template_code: str = Field(max_length=50, description="模板编码")
    template_name: str = Field(max_length=200, description="模板名称")
    contract_type: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = None
    visibility_scope: Optional[str] = Field(default="TEAM", description="可见范围")
    is_default: Optional[bool] = False
    owner_id: Optional[int] = None
    initial_version: Optional[ContractTemplateVersionCreate] = Field(default=None, description="初始版本")


class ContractTemplateUpdate(BaseModel):
    """更新合同模板"""

    template_name: Optional[str] = None
    contract_type: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    visibility_scope: Optional[str] = None
    is_default: Optional[bool] = None
    owner_id: Optional[int] = None
    current_version_id: Optional[int] = None


class ContractTemplateVersionResponse(TimestampSchema):
    """合同模板版本响应"""

    id: int
    template_id: int
    version_no: str
    status: str = "DRAFT"
    clause_sections: Optional[Dict[str, Any]] = None
    clause_library: Optional[Dict[str, Any]] = None
    attachment_refs: Optional[Dict[str, Any]] = None
    approval_flow: Optional[Dict[str, Any]] = None
    release_notes: Optional[str] = None
    created_by: Optional[int] = None
    published_by: Optional[int] = None
    published_at: Optional[datetime] = None


class ContractTemplateResponse(TimestampSchema):
    """合同模板响应"""

    id: int
    template_code: str
    template_name: str
    contract_type: Optional[str] = None
    description: Optional[str] = None
    status: str = "DRAFT"
    visibility_scope: str = "TEAM"
    is_default: bool = False
    current_version_id: Optional[int] = None
    owner_id: Optional[int] = None
    versions: List[ContractTemplateVersionResponse] = []


class TemplateDiffSection(BaseModel):
    """模板差异段"""

    added: List[str] = Field(default_factory=list)
    removed: List[str] = Field(default_factory=list)
    changed: List[Dict[str, Any]] = Field(default_factory=list)


class TemplateVersionDiff(BaseModel):
    """模板版本差异"""

    sections: TemplateDiffSection = Field(default_factory=TemplateDiffSection)
    pricing_rules: TemplateDiffSection = Field(default_factory=TemplateDiffSection)
    clause_sections: TemplateDiffSection = Field(default_factory=TemplateDiffSection)


class TemplateApprovalHistoryRecord(BaseModel):
    """模板版本审批/发布记录"""

    version_id: int
    version_no: str
    status: str
    published_by: Optional[int] = None
    published_at: Optional[datetime] = None
    release_notes: Optional[str] = None


class CpqRuleSetCreate(BaseModel):
    """创建CPQ规则集"""

    rule_code: str = Field(max_length=50, description="规则集编码")
    rule_name: str = Field(max_length=200, description="规则集名称")
    description: Optional[str] = None
    status: Optional[str] = Field(default="ACTIVE")
    base_price: Optional[Decimal] = Field(default=0)
    currency: Optional[str] = Field(default="CNY")
    config_schema: Optional[Dict[str, Any]] = Field(default_factory=dict, description="配置项定义")
    pricing_matrix: Optional[Dict[str, Any]] = Field(default_factory=dict, description="价格矩阵")
    approval_threshold: Optional[Dict[str, Any]] = Field(default_factory=dict, description="审批阈值")
    visibility_scope: Optional[str] = Field(default="ALL")
    is_default: Optional[bool] = False
    owner_role: Optional[str] = None


class CpqRuleSetUpdate(BaseModel):
    """更新CPQ规则集"""

    rule_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    base_price: Optional[Decimal] = None
    currency: Optional[str] = None
    config_schema: Optional[Dict[str, Any]] = None
    pricing_matrix: Optional[Dict[str, Any]] = None
    approval_threshold: Optional[Dict[str, Any]] = None
    visibility_scope: Optional[str] = None
    is_default: Optional[bool] = None
    owner_role: Optional[str] = None


class CpqRuleSetResponse(TimestampSchema):
    """CPQ规则集响应"""

    id: int
    rule_code: str
    rule_name: str
    description: Optional[str] = None
    status: str = "ACTIVE"
    base_price: Decimal = 0
    currency: str = "CNY"
    config_schema: Optional[Dict[str, Any]] = None
    pricing_matrix: Optional[Dict[str, Any]] = None
    approval_threshold: Optional[Dict[str, Any]] = None
    visibility_scope: str = "ALL"
    is_default: bool = False
    owner_role: Optional[str] = None


class CpqAdjustmentItem(BaseModel):
    """CPQ调价项"""

    key: str
    label: str
    value: Decimal = 0
    reason: Optional[str] = None


class CpqPricePreviewRequest(BaseModel):
    """CPQ价格预览请求"""

    rule_set_id: Optional[int] = Field(default=None, description="规则集ID")
    template_version_id: Optional[int] = Field(default=None, description="模板版本ID")
    selections: Dict[str, Any] = Field(default_factory=dict, description="配置项选择")
    manual_discount_pct: Optional[Decimal] = Field(default=None, description="手动折扣(%)")
    manual_markup_pct: Optional[Decimal] = Field(default=None, description="附加费用(%)")


class CpqPricePreviewResponse(BaseSchema):
    """CPQ价格预览响应"""

    base_price: Decimal = 0
    adjustment_total: Decimal = 0
    final_price: Decimal = 0
    currency: str = "CNY"
    adjustments: List[CpqAdjustmentItem] = []
    requires_approval: bool = False
    approval_reason: Optional[str] = None
    confidence_level: Optional[str] = None


class QuoteTemplateApplyResponse(BaseSchema):
    """报价模板应用响应"""

    template: QuoteTemplateResponse
    version: QuoteTemplateVersionResponse
    cpq_preview: Optional[CpqPricePreviewResponse] = None
    version_diff: Optional[TemplateVersionDiff] = None
    approval_history: List[TemplateApprovalHistoryRecord] = []


class ContractTemplateApplyResponse(BaseSchema):
    """合同模板应用响应"""

    template: ContractTemplateResponse
    version: ContractTemplateVersionResponse
    version_diff: Optional[TemplateVersionDiff] = None
    approval_history: List[TemplateApprovalHistoryRecord] = []


# ==================== 技术评估 ====================


class TechnicalAssessmentApplyRequest(BaseModel):
    """申请技术评估请求"""
    
    evaluator_id: Optional[int] = Field(default=None, description="指定评估人ID（可选）")


class TechnicalAssessmentEvaluateRequest(BaseModel):
    """执行技术评估请求"""
    
    requirement_data: Dict[str, Any] = Field(description="需求数据")
    enable_ai: bool = Field(default=False, description="是否启用AI分析")


class TechnicalAssessmentResponse(TimestampSchema):
    """技术评估响应"""
    
    id: int
    source_type: str
    source_id: int
    evaluator_id: Optional[int] = None
    status: str
    total_score: Optional[int] = None
    dimension_scores: Optional[str] = None
    veto_triggered: bool = False
    veto_rules: Optional[str] = None
    decision: Optional[str] = None
    risks: Optional[str] = None
    similar_cases: Optional[str] = None
    ai_analysis: Optional[str] = None
    conditions: Optional[str] = None
    evaluated_at: Optional[datetime] = None
    evaluator_name: Optional[str] = None


class ScoringRuleCreate(BaseModel):
    """创建评分规则"""
    
    version: str = Field(max_length=20, description="版本号")
    rules_json: str = Field(description="规则配置(JSON)")
    description: Optional[str] = Field(default=None, description="描述")


class ScoringRuleResponse(TimestampSchema):
    """评分规则响应"""
    
    id: int
    version: str
    is_active: bool
    description: Optional[str] = None
    created_by: Optional[int] = None
    creator_name: Optional[str] = None


class FailureCaseCreate(BaseModel):
    """创建失败案例"""
    
    case_code: str = Field(max_length=50, description="案例编号")
    project_name: str = Field(max_length=200, description="项目名称")
    industry: str = Field(max_length=50, description="行业")
    product_types: Optional[str] = Field(default=None, description="产品类型(JSON Array)")
    processes: Optional[str] = Field(default=None, description="工序/测试类型(JSON Array)")
    takt_time_s: Optional[int] = Field(default=None, description="节拍时间(秒)")
    annual_volume: Optional[int] = Field(default=None, description="年产量")
    budget_status: Optional[str] = Field(default=None, description="预算状态")
    customer_project_status: Optional[str] = Field(default=None, description="客户项目状态")
    spec_status: Optional[str] = Field(default=None, description="规范状态")
    price_sensitivity: Optional[str] = Field(default=None, description="价格敏感度")
    delivery_months: Optional[int] = Field(default=None, description="交付周期(月)")
    failure_tags: str = Field(description="失败标签(JSON Array)")
    core_failure_reason: str = Field(description="核心失败原因")
    early_warning_signals: str = Field(description="预警信号(JSON Array)")
    final_result: Optional[str] = Field(default=None, description="最终结果")
    lesson_learned: str = Field(description="教训总结")
    keywords: str = Field(description="关键词(JSON Array)")


class FailureCaseResponse(TimestampSchema):
    """失败案例响应"""
    
    id: int
    case_code: str
    project_name: str
    industry: str
    product_types: Optional[str] = None
    processes: Optional[str] = None
    takt_time_s: Optional[int] = None
    annual_volume: Optional[int] = None
    budget_status: Optional[str] = None
    customer_project_status: Optional[str] = None
    spec_status: Optional[str] = None
    price_sensitivity: Optional[str] = None
    delivery_months: Optional[int] = None
    failure_tags: str
    core_failure_reason: str
    early_warning_signals: str
    final_result: Optional[str] = None
    lesson_learned: str
    keywords: str
    created_by: Optional[int] = None
    creator_name: Optional[str] = None


class OpenItemCreate(BaseModel):
    """创建未决事项"""
    
    item_type: str = Field(description="问题类型")
    description: str = Field(description="问题描述")
    responsible_party: str = Field(description="责任方")
    responsible_person_id: Optional[int] = Field(default=None, description="责任人ID")
    due_date: Optional[datetime] = Field(default=None, description="截止日期")
    blocks_quotation: bool = Field(default=False, description="是否阻塞报价")


class OpenItemResponse(TimestampSchema):
    """未决事项响应"""
    
    id: int
    source_type: str
    source_id: int
    item_code: str
    item_type: str
    description: str
    responsible_party: str
    responsible_person_id: Optional[int] = None
    due_date: Optional[datetime] = None
    status: str
    close_evidence: Optional[str] = None
    blocks_quotation: bool = False
    closed_at: Optional[datetime] = None
    responsible_person_name: Optional[str] = None


# ==================== 需求详情 ====================

class LeadRequirementDetailCreate(BaseModel):
    """创建/更新需求详情"""
    
    customer_factory_location: Optional[str] = None
    target_object_type: Optional[str] = None
    application_scenario: Optional[str] = None
    delivery_mode: Optional[str] = None
    expected_delivery_date: Optional[datetime] = None
    requirement_source: Optional[str] = None
    participant_ids: Optional[str] = None  # JSON Array
    requirement_maturity: Optional[int] = Field(None, ge=1, le=5, description="需求成熟度(1-5级)")
    has_sow: Optional[bool] = None
    has_interface_doc: Optional[bool] = None
    has_drawing_doc: Optional[bool] = None
    sample_availability: Optional[str] = None  # JSON
    customer_support_resources: Optional[str] = None  # JSON
    key_risk_factors: Optional[str] = None  # JSON Array
    target_capacity_uph: Optional[float] = None
    target_capacity_daily: Optional[float] = None
    target_capacity_shift: Optional[float] = None
    cycle_time_seconds: Optional[float] = None
    workstation_count: Optional[int] = None
    changeover_method: Optional[str] = None
    yield_target: Optional[float] = None
    retest_allowed: Optional[bool] = None
    retest_max_count: Optional[int] = None
    traceability_type: Optional[str] = None
    data_retention_period: Optional[int] = None
    data_format: Optional[str] = None
    test_scope: Optional[str] = None  # JSON Array
    key_metrics_spec: Optional[str] = None  # JSON
    coverage_boundary: Optional[str] = None  # JSON
    exception_handling: Optional[str] = None  # JSON
    acceptance_method: Optional[str] = None
    acceptance_basis: Optional[str] = None
    delivery_checklist: Optional[str] = None  # JSON Array
    interface_types: Optional[str] = None  # JSON Array
    io_point_estimate: Optional[str] = None  # JSON
    communication_protocols: Optional[str] = None  # JSON Array
    upper_system_integration: Optional[str] = None  # JSON
    data_field_list: Optional[str] = None  # JSON Array
    it_security_restrictions: Optional[str] = None  # JSON
    power_supply: Optional[str] = None  # JSON
    air_supply: Optional[str] = None  # JSON
    environment: Optional[str] = None  # JSON
    safety_requirements: Optional[str] = None  # JSON
    space_and_logistics: Optional[str] = None  # JSON
    customer_site_standards: Optional[str] = None  # JSON
    customer_supplied_materials: Optional[str] = None  # JSON Array
    restricted_brands: Optional[str] = None  # JSON Array
    specified_brands: Optional[str] = None  # JSON Array
    long_lead_items: Optional[str] = None  # JSON Array
    spare_parts_requirement: Optional[str] = None  # JSON
    after_sales_support: Optional[str] = None  # JSON
    requirement_version: Optional[str] = None


class LeadRequirementDetailResponse(TimestampSchema):
    """需求详情响应"""
    
    id: int
    lead_id: int
    customer_factory_location: Optional[str] = None
    target_object_type: Optional[str] = None
    application_scenario: Optional[str] = None
    delivery_mode: Optional[str] = None
    expected_delivery_date: Optional[datetime] = None
    requirement_source: Optional[str] = None
    participant_ids: Optional[str] = None
    requirement_maturity: Optional[int] = None
    has_sow: Optional[bool] = None
    has_interface_doc: Optional[bool] = None
    has_drawing_doc: Optional[bool] = None
    sample_availability: Optional[str] = None
    customer_support_resources: Optional[str] = None
    key_risk_factors: Optional[str] = None
    veto_triggered: bool = False
    veto_reason: Optional[str] = None
    target_capacity_uph: Optional[float] = None
    target_capacity_daily: Optional[float] = None
    target_capacity_shift: Optional[float] = None
    cycle_time_seconds: Optional[float] = None
    workstation_count: Optional[int] = None
    changeover_method: Optional[str] = None
    yield_target: Optional[float] = None
    retest_allowed: Optional[bool] = None
    retest_max_count: Optional[int] = None
    traceability_type: Optional[str] = None
    data_retention_period: Optional[int] = None
    data_format: Optional[str] = None
    test_scope: Optional[str] = None
    key_metrics_spec: Optional[str] = None
    coverage_boundary: Optional[str] = None
    exception_handling: Optional[str] = None
    acceptance_method: Optional[str] = None
    acceptance_basis: Optional[str] = None
    delivery_checklist: Optional[str] = None
    interface_types: Optional[str] = None
    io_point_estimate: Optional[str] = None
    communication_protocols: Optional[str] = None
    upper_system_integration: Optional[str] = None
    data_field_list: Optional[str] = None
    it_security_restrictions: Optional[str] = None
    power_supply: Optional[str] = None
    air_supply: Optional[str] = None
    environment: Optional[str] = None
    safety_requirements: Optional[str] = None
    space_and_logistics: Optional[str] = None
    customer_site_standards: Optional[str] = None
    customer_supplied_materials: Optional[str] = None
    restricted_brands: Optional[str] = None
    specified_brands: Optional[str] = None
    long_lead_items: Optional[str] = None
    spare_parts_requirement: Optional[str] = None
    after_sales_support: Optional[str] = None
    requirement_version: Optional[str] = None
    is_frozen: bool = False
    frozen_at: Optional[datetime] = None
    frozen_by: Optional[int] = None
    frozen_by_name: Optional[str] = None


# ==================== 需求冻结 ====================

class RequirementFreezeCreate(BaseModel):
    """创建需求冻结"""
    
    freeze_type: str = Field(description="冻结点类型")
    version_number: str = Field(description="冻结版本号")
    requires_ecr: bool = Field(default=True, description="冻结后变更是否必须走ECR/ECN")
    description: Optional[str] = Field(default=None, description="冻结说明")


class RequirementFreezeResponse(TimestampSchema):
    """需求冻结响应"""
    
    id: int
    source_type: str
    source_id: int
    freeze_type: str
    freeze_time: datetime
    frozen_by: int
    version_number: str
    requires_ecr: bool
    description: Optional[str] = None
    frozen_by_name: Optional[str] = None


# ==================== AI澄清 ====================

class AIClarificationCreate(BaseModel):
    """创建AI澄清"""
    
    questions: str = Field(description="AI生成的问题(JSON Array)")
    answers: Optional[str] = Field(default=None, description="用户回答(JSON Array)")


class AIClarificationUpdate(BaseModel):
    """更新AI澄清"""
    
    answers: str = Field(description="用户回答(JSON Array)")


class AIClarificationResponse(TimestampSchema):
    """AI澄清响应"""
    
    id: int
    source_type: str
    source_id: int
    round: int
    questions: str
    answers: Optional[str] = None


# ==================== 审批工作流 ====================


class ApprovalWorkflowStepCreate(BaseModel):
    """创建审批工作流步骤"""
    
    step_order: int = Field(..., description="步骤顺序")
    step_name: str = Field(..., max_length=100, description="步骤名称")
    approver_role: Optional[str] = Field(None, max_length=50, description="审批角色")
    approver_id: Optional[int] = Field(None, description="指定审批人ID")
    is_required: bool = Field(True, description="是否必需")
    can_delegate: bool = Field(True, description="是否允许委托")
    can_withdraw: bool = Field(True, description="是否允许撤回")
    due_hours: Optional[int] = Field(None, description="审批期限（小时）")


class ApprovalWorkflowStepResponse(TimestampSchema):
    """审批工作流步骤响应"""
    
    id: int
    workflow_id: int
    step_order: int
    step_name: str
    approver_role: Optional[str] = None
    approver_id: Optional[int] = None
    approver_name: Optional[str] = None
    is_required: bool
    can_delegate: bool
    can_withdraw: bool
    due_hours: Optional[int] = None
    
    class Config:
        from_attributes = True


class ApprovalWorkflowCreate(BaseModel):
    """创建审批工作流"""
    
    workflow_type: str = Field(..., description="工作流类型：QUOTE/CONTRACT/INVOICE")
    workflow_name: str = Field(..., max_length=100, description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    routing_rules: Optional[Dict[str, Any]] = Field(None, description="审批路由规则（JSON）")
    is_active: bool = Field(True, description="是否启用")
    steps: List[ApprovalWorkflowStepCreate] = Field(default_factory=list, description="审批步骤")


class ApprovalWorkflowUpdate(BaseModel):
    """更新审批工作流"""
    
    workflow_name: Optional[str] = None
    description: Optional[str] = None
    routing_rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ApprovalWorkflowResponse(TimestampSchema):
    """审批工作流响应"""
    
    id: int
    workflow_type: str
    workflow_name: str
    description: Optional[str] = None
    routing_rules: Optional[Dict[str, Any]] = None
    is_active: bool
    steps: List[ApprovalWorkflowStepResponse] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class ApprovalHistoryResponse(TimestampSchema):
    """审批历史响应"""
    
    id: int
    approval_record_id: int
    step_order: int
    approver_id: int
    approver_name: Optional[str] = None
    action: str
    comment: Optional[str] = None
    delegate_to_id: Optional[int] = None
    delegate_to_name: Optional[str] = None
    action_at: datetime
    
    class Config:
        from_attributes = True


class ApprovalRecordResponse(TimestampSchema):
    """审批记录响应"""
    
    id: int
    entity_type: str
    entity_id: int
    workflow_id: int
    workflow_name: Optional[str] = None
    current_step: int
    status: str
    initiator_id: int
    initiator_name: Optional[str] = None
    history: List[ApprovalHistoryResponse] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class ApprovalStartRequest(BaseModel):
    """启动审批请求"""
    
    workflow_id: Optional[int] = Field(None, description="指定工作流ID（可选，不指定则根据路由规则自动选择）")
    comment: Optional[str] = Field(None, description="提交说明")


class ApprovalActionRequest(BaseModel):
    """审批操作请求"""
    
    action: str = Field(..., description="审批操作：APPROVE/REJECT/DELEGATE/WITHDRAW")
    comment: Optional[str] = Field(None, description="审批意见")
    delegate_to_id: Optional[int] = Field(None, description="委托给的用户ID（action为DELEGATE时必填）")


class ApprovalStatusResponse(BaseModel):
    """审批状态响应"""
    
    record: Optional[ApprovalRecordResponse] = None
    current_step_info: Optional[Dict[str, Any]] = None
    can_approve: bool = False
    can_reject: bool = False
    can_delegate: bool = False
    can_withdraw: bool = False


# ==================== 销售目标 ====================


class SalesTargetCreate(BaseModel):
    """创建销售目标"""
    
    target_scope: str = Field(..., description="目标范围：PERSONAL/TEAM/DEPARTMENT")
    user_id: Optional[int] = Field(None, description="用户ID（个人目标）")
    department_id: Optional[int] = Field(None, description="部门ID（部门目标）")
    team_id: Optional[int] = Field(None, description="团队ID（团队目标）")
    target_type: str = Field(..., description="目标类型：LEAD_COUNT/OPPORTUNITY_COUNT/CONTRACT_AMOUNT/COLLECTION_AMOUNT")
    target_period: str = Field(..., description="目标周期：MONTHLY/QUARTERLY/YEARLY")
    period_value: str = Field(..., description="周期标识：2025-01/2025-Q1/2025")
    target_value: Decimal = Field(..., description="目标值")
    description: Optional[str] = Field(None, description="目标描述")
    status: Optional[str] = Field("ACTIVE", description="状态：ACTIVE/COMPLETED/CANCELLED")


class SalesTargetUpdate(BaseModel):
    """更新销售目标"""
    
    target_value: Optional[Decimal] = None
    description: Optional[str] = None
    status: Optional[str] = None


class SalesTargetResponse(TimestampSchema):
    """销售目标响应"""
    
    id: int
    target_scope: str
    user_id: Optional[int] = None
    department_id: Optional[int] = None
    team_id: Optional[int] = None
    target_type: str
    target_period: str
    period_value: str
    target_value: Decimal
    description: Optional[str] = None
    status: str
    created_by: int
    # 扩展字段：实际完成值（通过统计API计算）
    actual_value: Optional[Decimal] = None
    completion_rate: Optional[float] = None
    # 扩展字段：用户/部门名称
    user_name: Optional[str] = None
    department_name: Optional[str] = None
    
    class Config:
        from_attributes = True
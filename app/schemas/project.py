# -*- coding: utf-8 -*-
"""
项目管理 Schema
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal

from .common import BaseSchema, TimestampSchema


# ==================== 客户 ====================


class CustomerCreate(BaseModel):
    """创建客户"""

    customer_code: str = Field(max_length=50, description="客户编码")
    customer_name: str = Field(max_length=200, description="客户名称")
    short_name: Optional[str] = Field(default=None, max_length=50)
    customer_type: Optional[str] = None
    industry: Optional[str] = None
    scale: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    legal_person: Optional[str] = None
    tax_no: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    payment_terms: Optional[str] = None
    remark: Optional[str] = None


class CustomerUpdate(BaseModel):
    """更新客户"""

    customer_name: Optional[str] = None
    short_name: Optional[str] = None
    customer_type: Optional[str] = None
    industry: Optional[str] = None
    scale: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    legal_person: Optional[str] = None
    tax_no: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    credit_level: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    payment_terms: Optional[str] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class CustomerResponse(TimestampSchema):
    """客户响应"""

    id: int
    customer_code: str
    customer_name: str
    short_name: Optional[str] = None
    customer_type: Optional[str] = None
    industry: Optional[str] = None
    scale: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    credit_level: str = "B"
    credit_limit: Optional[Decimal] = None
    status: str = "ACTIVE"
    legal_person: Optional[str] = None
    tax_no: Optional[str] = None

    class Config:
        from_attributes = True


class Customer360Summary(BaseModel):
    """客户360度概要"""

    total_projects: int = 0
    active_projects: int = 0
    pipeline_amount: Decimal = 0
    total_contract_amount: Decimal = 0
    open_receivables: Decimal = 0
    win_rate: float = 0
    avg_margin: Optional[Decimal] = None
    last_activity: Optional[datetime] = None


class Customer360ProjectItem(BaseModel):
    """客户项目摘要"""

    project_id: int
    project_code: str
    project_name: str
    stage: Optional[str] = None
    status: Optional[str] = None
    progress_pct: Optional[Decimal] = None
    contract_amount: Optional[Decimal] = None
    planned_end_date: Optional[date] = None


class Customer360OpportunityItem(BaseModel):
    """客户商机摘要"""

    opportunity_id: int
    opp_code: str
    opp_name: str
    stage: str
    est_amount: Optional[Decimal] = None
    owner_name: Optional[str] = None
    win_probability: Optional[float] = None
    updated_at: Optional[datetime] = None


class Customer360QuoteItem(BaseModel):
    """客户报价摘要"""

    quote_id: int
    quote_code: str
    status: str
    total_price: Optional[Decimal] = None
    gross_margin: Optional[Decimal] = None
    owner_name: Optional[str] = None
    valid_until: Optional[date] = None


class Customer360ContractItem(BaseModel):
    """客户合同摘要"""

    contract_id: int
    contract_code: str
    status: str
    contract_amount: Optional[Decimal] = None
    signed_date: Optional[date] = None
    project_code: Optional[str] = None


class Customer360InvoiceItem(BaseModel):
    """客户发票摘要"""

    invoice_id: int
    invoice_code: str
    status: str
    total_amount: Optional[Decimal] = None
    issue_date: Optional[date] = None
    paid_amount: Optional[Decimal] = None


class Customer360PaymentPlanItem(BaseModel):
    """客户收款节点"""

    plan_id: int
    project_id: Optional[int] = None
    payment_name: str
    status: str
    planned_amount: Optional[Decimal] = None
    actual_amount: Optional[Decimal] = None
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None


class Customer360CommunicationItem(BaseModel):
    """客户沟通记录摘要"""

    communication_id: int
    topic: str
    communication_type: Optional[str] = None
    communication_date: Optional[date] = None
    owner_name: Optional[str] = None
    follow_up_required: Optional[bool] = None


class Customer360Response(BaseModel):
    """客户360度视图响应"""

    basic_info: CustomerResponse
    summary: Customer360Summary
    projects: List[Customer360ProjectItem] = []
    opportunities: List[Customer360OpportunityItem] = []
    quotes: List[Customer360QuoteItem] = []
    contracts: List[Customer360ContractItem] = []
    invoices: List[Customer360InvoiceItem] = []
    payment_plans: List[Customer360PaymentPlanItem] = []
    communications: List[Customer360CommunicationItem] = []


# ==================== 项目 ====================


class ProjectCreate(BaseModel):
    """创建项目"""

    project_code: str = Field(max_length=50, description="项目编码")
    project_name: str = Field(max_length=200, description="项目名称")
    short_name: Optional[str] = Field(default=None, max_length=50)
    customer_id: Optional[int] = None
    contract_no: Optional[str] = None
    project_type: Optional[str] = None
    # product_category: Optional[str] = None
    # industry: Optional[str] = None
    # business_type & machine_count removed/mapped? Model has product_category/industry.
    # Keep it simple for now matching schema given to API logic.
    machine_count: int = Field(
        default=1, ge=1
    )  # Not in model but used in logic? check API. API commented it out.
    contract_date: Optional[date] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    # delivery_date: Optional[date] = None
    contract_amount: Optional[Decimal] = Field(default=0)
    budget_amount: Optional[Decimal] = Field(default=0)
    pm_id: Optional[int] = None
    description: Optional[str] = None
    # remark: Optional[str] = None


class ProjectUpdate(BaseModel):
    """更新项目"""

    project_name: Optional[str] = None
    short_name: Optional[str] = None
    customer_id: Optional[int] = None
    contract_no: Optional[str] = None
    project_type: Optional[str] = None
    stage: Optional[str] = None
    status: Optional[str] = None
    health: Optional[str] = None
    progress_pct: Optional[Decimal] = None
    contract_date: Optional[date] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    contract_amount: Optional[Decimal] = None
    budget_amount: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    pm_id: Optional[int] = None
    description: Optional[str] = None


class ProjectResponse(TimestampSchema):
    """项目响应"""

    id: int
    project_code: str
    project_name: str
    short_name: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    stage: str = "S1"
    status: Optional[str] = None
    health: str = "H1"
    progress_pct: Decimal = 0
    contract_date: Optional[date] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    # delivery_date: Optional[date] = None
    contract_amount: Decimal = 0
    budget_amount: Decimal = 0
    actual_cost: Decimal = 0
    pm_id: Optional[int] = None
    pm_name: Optional[str] = None
    # machine_count: int = 1
    is_active: bool = True

    class Config:
        from_attributes = True


class ProjectListResponse(BaseSchema):
    """项目列表响应"""

    id: int
    project_code: str
    project_name: str
    customer_name: Optional[str] = None
    stage: str
    health: str
    progress_pct: Decimal
    pm_name: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    """项目详情响应"""

    machines: List["MachineResponse"] = []
    milestones: List["MilestoneResponse"] = []
    members: List["ProjectMemberResponse"] = []


# ==================== 设备 ====================


class MachineCreate(BaseModel):
    """创建设备"""

    machine_code: str = Field(max_length=50, description="设备编码")
    machine_name: str = Field(max_length=200, description="设备名称")
    project_id: int = Field(description="项目ID")
    machine_no: Optional[int] = 1
    machine_type: Optional[str] = None
    specification: Optional[str] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    remark: Optional[str] = None


class MachineUpdate(BaseModel):
    """更新设备"""

    machine_name: Optional[str] = None
    machine_no: Optional[int] = None
    machine_type: Optional[str] = None
    specification: Optional[str] = None
    stage: Optional[str] = None
    status: Optional[str] = None
    health: Optional[str] = None
    progress_pct: Optional[Decimal] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    fat_date: Optional[date] = None
    fat_result: Optional[str] = None
    sat_date: Optional[date] = None
    sat_result: Optional[str] = None
    ship_date: Optional[date] = None
    ship_address: Optional[str] = None
    tracking_no: Optional[str] = None
    remark: Optional[str] = None


class MachineResponse(TimestampSchema):
    """设备响应"""

    id: int
    machine_code: str
    machine_name: str
    machine_no: int
    project_id: int
    project_name: Optional[str] = None
    machine_type: Optional[str] = None
    stage: str = "S1"
    status: str = "ST01"
    health: str = "H1"
    progress_pct: Decimal = 0
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None

    class Config:
        from_attributes = True


# ==================== 里程碑 ====================


class MilestoneCreate(BaseModel):
    """创建里程碑"""

    project_id: int = Field(description="项目ID")
    machine_id: Optional[int] = None
    milestone_code: str = Field(max_length=50, description="里程碑编码")
    milestone_name: str = Field(max_length=200, description="里程碑名称")
    milestone_type: str = Field(default="CUSTOM", description="里程碑类型")
    planned_date: date = Field(description="计划日期")
    stage_code: Optional[str] = None
    deliverables: Optional[str] = None
    owner_id: Optional[int] = None
    description: Optional[str] = None


class MilestoneUpdate(BaseModel):
    """更新里程碑"""

    milestone_name: Optional[str] = None
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    status: Optional[str] = None
    deliverables: Optional[str] = None
    owner_id: Optional[int] = None
    description: Optional[str] = None
    completion_note: Optional[str] = None


class MilestoneResponse(TimestampSchema):
    """里程碑响应"""

    id: int
    project_id: int
    machine_id: Optional[int] = None
    milestone_code: str
    milestone_name: str
    milestone_type: str
    planned_date: date
    actual_date: Optional[date] = None
    status: str = "PENDING"
    stage_code: Optional[str] = None
    owner_id: Optional[int] = None


# ==================== 项目成员 ====================


class ProjectMemberCreate(BaseModel):
    """添加项目成员"""

    project_id: int
    user_id: int
    role_code: str = Field(max_length=50)
    allocation_pct: Decimal = Field(default=100, ge=0, le=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    remark: Optional[str] = None


class ProjectMemberUpdate(BaseModel):
    """更新项目成员"""

    role_code: Optional[str] = None
    allocation_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    remark: Optional[str] = None


class ProjectMemberResponse(BaseSchema):
    """项目成员响应"""

    id: int
    project_id: int
    user_id: int
    username: str
    real_name: Optional[str] = None
    role_code: str
    allocation_pct: Decimal = 100
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = True
    remark: Optional[str] = None


# ==================== 项目阶段 ====================


class ProjectStageCreate(BaseModel):
    """创建项目阶段（配置）"""

    project_id: int
    stage_code: str = Field(max_length=20)
    stage_name: str = Field(max_length=50)
    stage_order: int
    description: Optional[str] = None
    gate_conditions: Optional[str] = None
    required_deliverables: Optional[str] = None
    default_duration_days: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class ProjectStageUpdate(BaseModel):
    """更新项目阶段"""

    stage_name: Optional[str] = None
    stage_order: Optional[int] = None
    description: Optional[str] = None
    gate_conditions: Optional[str] = None
    required_deliverables: Optional[str] = None
    default_duration_days: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectStageResponse(TimestampSchema):
    """项目阶段响应"""

    id: int
    project_id: int
    stage_code: str
    stage_name: str
    stage_order: int
    description: Optional[str] = None
    gate_conditions: Optional[str] = None
    required_deliverables: Optional[str] = None
    default_duration_days: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None

    # 计划与进度
    progress_pct: int = 0
    status: str = "PENDING"
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None

    is_active: bool

    class Config:
        from_attributes = True


# ==================== 项目状态 ====================


class ProjectStatusCreate(BaseModel):
    """创建项目状态"""

    stage_id: int
    status_code: str
    status_name: str
    status_order: int
    description: Optional[str] = None
    status_type: str = "NORMAL"
    auto_next_status: Optional[str] = None


class ProjectStatusResponse(TimestampSchema):
    """项目状态响应"""

    id: int
    stage_id: int
    status_code: str
    status_name: str
    status_order: int
    description: Optional[str] = None
    status_type: str
    auto_next_status: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


# ==================== 项目成本 ====================


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

    class Config:
        from_attributes = True


# ==================== 项目文档 ====================


class ProjectDocumentCreate(BaseModel):
    """创建文档记录"""

    project_id: Optional[int] = None
    rd_project_id: Optional[int] = None
    machine_id: Optional[int] = None
    doc_type: str = Field(max_length=50)
    doc_category: Optional[str] = None
    doc_name: str = Field(max_length=200)
    doc_no: Optional[str] = None
    version: str = "1.0"
    file_path: str
    file_name: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    description: Optional[str] = None


class ProjectDocumentUpdate(BaseModel):
    """更新文档记录"""

    machine_id: Optional[int] = None
    doc_type: Optional[str] = None
    doc_category: Optional[str] = None
    doc_name: Optional[str] = None
    doc_no: Optional[str] = None
    version: Optional[str] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


class ProjectDocumentResponse(TimestampSchema):
    """文档记录响应"""

    id: int
    project_id: Optional[int] = None
    rd_project_id: Optional[int] = None
    machine_id: Optional[int] = None
    doc_type: str
    doc_category: Optional[str] = None
    doc_name: str
    doc_no: Optional[str] = None
    version: str
    file_path: str
    file_name: str
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[date] = None
    description: Optional[str] = None
    uploaded_by: Optional[int] = None

    class Config:
        from_attributes = True


# ==================== 项目状态变更历史 ====================


class ProjectHealthDetailsResponse(BaseModel):
    """项目健康度详情响应"""
    project_id: int
    project_code: str
    current_health: str
    calculated_health: str
    status: str
    stage: str
    checks: dict
    statistics: dict
    
    class Config:
        from_attributes = True


class ProjectStatusLogResponse(BaseSchema):
    """项目状态变更历史响应"""

    id: int
    project_id: int
    machine_id: Optional[int] = None
    
    # 变更前状态
    old_stage: Optional[str] = None
    old_status: Optional[str] = None
    old_health: Optional[str] = None
    
    # 变更后状态
    new_stage: Optional[str] = None
    new_status: Optional[str] = None
    new_health: Optional[str] = None
    
    # 变更信息
    change_type: str
    change_reason: Optional[str] = None
    change_note: Optional[str] = None
    
    # 操作信息
    changed_by: Optional[int] = None
    changed_by_name: Optional[str] = None
    changed_at: datetime

    class Config:
        from_attributes = True


# ==================== 项目模板 ====================


class ProjectTemplateCreate(BaseModel):
    """创建项目模板"""

    template_code: str = Field(max_length=50, description="模板编码")
    template_name: str = Field(max_length=200, description="模板名称")
    description: Optional[str] = None
    project_type: Optional[str] = None
    product_category: Optional[str] = None
    industry: Optional[str] = None
    default_stage: Optional[str] = Field(default="S1")
    default_status: Optional[str] = Field(default="ST01")
    default_health: Optional[str] = Field(default="H1")
    template_config: Optional[str] = None  # JSON字符串
    is_active: Optional[bool] = Field(default=True)


class ProjectTemplateUpdate(BaseModel):
    """更新项目模板"""

    template_name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[str] = None
    product_category: Optional[str] = None
    industry: Optional[str] = None
    default_stage: Optional[str] = None
    default_status: Optional[str] = None
    default_health: Optional[str] = None
    template_config: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectTemplateResponse(TimestampSchema):
    """项目模板响应"""

    id: int
    template_code: str
    template_name: str
    description: Optional[str] = None
    project_type: Optional[str] = None
    product_category: Optional[str] = None
    industry: Optional[str] = None
    default_stage: Optional[str] = None
    default_status: Optional[str] = None
    default_health: Optional[str] = None
    template_config: Optional[str] = None
    is_active: bool
    usage_count: int
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


# ==================== 项目模板版本 ====================

class ProjectTemplateVersionCreate(BaseModel):
    """创建项目模板版本"""

    version_no: str = Field(..., max_length=20, description="版本号")
    status: Optional[str] = Field(default="DRAFT", description="状态：DRAFT/ACTIVE/ARCHIVED")
    template_config: Optional[str] = Field(None, description="模板配置JSON")
    release_notes: Optional[str] = Field(None, description="版本说明")


class ProjectTemplateVersionUpdate(BaseModel):
    """更新项目模板版本"""

    version_no: Optional[str] = Field(None, max_length=20, description="版本号")
    status: Optional[str] = Field(None, description="状态：DRAFT/ACTIVE/ARCHIVED")
    template_config: Optional[str] = Field(None, description="模板配置JSON")
    release_notes: Optional[str] = Field(None, description="版本说明")


class ProjectTemplateVersionResponse(TimestampSchema):
    """项目模板版本响应"""

    id: int
    template_id: int
    version_no: str
    status: str
    template_config: Optional[str] = None
    release_notes: Optional[str] = None
    created_by: Optional[int] = None
    published_by: Optional[int] = None
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectCloneRequest(BaseModel):
    """项目复制请求"""

    new_project_code: str = Field(max_length=50, description="新项目编码")
    new_project_name: str = Field(max_length=200, description="新项目名称")
    copy_machines: Optional[bool] = Field(default=True, description="是否复制机台")
    copy_milestones: Optional[bool] = Field(default=True, description="是否复制里程碑")
    copy_members: Optional[bool] = Field(default=True, description="是否复制成员")
    copy_stages: Optional[bool] = Field(default=True, description="是否复制阶段")
    customer_id: Optional[int] = Field(default=None, description="新客户ID（可选，默认使用原客户）")


class ProjectArchiveRequest(BaseModel):
    """项目归档请求"""

    archive_reason: Optional[str] = Field(default=None, max_length=500, description="归档原因")


# ==================== 资源分配优化 ====================

class ResourceConflictResponse(BaseModel):
    """资源冲突响应"""

    resource_id: int
    resource_name: str
    conflict_type: str  # OVERLOAD, OVERLAP
    conflict_projects: List[dict]
    conflict_period: dict
    suggested_solution: Optional[str] = None


class ResourceOptimizationResponse(BaseModel):
    """资源分配优化响应"""

    conflicts: List[ResourceConflictResponse]
    overloaded_resources: List[dict]
    underutilized_resources: List[dict]
    optimization_suggestions: List[str]


# ==================== 项目关联分析 ====================

class ProjectRelationResponse(BaseModel):
    """项目关联响应"""

    project_id: int
    project_code: str
    project_name: str
    relation_type: str  # SHARED_RESOURCE, DEPENDENCY, SIMILAR, CUSTOMER
    relation_strength: str  # WEAK, MEDIUM, STRONG
    related_projects: List[dict]
    shared_resources: List[dict]
    dependency_info: Optional[dict] = None


# ==================== 风险矩阵 ====================

class RiskMatrixResponse(BaseModel):
    """风险矩阵响应"""

    matrix_data: List[dict]  # [{probability, impact, count, risks: [...]}]
    risk_distribution: dict
    high_priority_risks: List[dict]
    risk_trends: Optional[List[dict]] = None


# ==================== 变更影响分析 ====================

class ChangeImpactRequest(BaseModel):
    """变更影响分析请求"""

    change_type: str  # SCOPE, SCHEDULE, COST, RESOURCE
    change_description: str
    affected_items: Optional[List[dict]] = None


class ChangeImpactResponse(BaseModel):
    """变更影响分析响应"""

    affected_projects: List[dict]
    affected_tasks: List[dict]
    affected_resources: List[dict]
    cost_impact: Optional[dict] = None
    schedule_impact: Optional[dict] = None
    risk_impact: Optional[dict] = None
    recommendations: List[str]


class ProjectSummaryResponse(BaseModel):
    """项目概览数据响应"""
    
    project_id: int
    project_code: str
    project_name: str
    customer_name: Optional[str] = None
    pm_name: Optional[str] = None
    stage: str
    status: str
    health: Optional[str] = None
    progress_pct: float
    contract_amount: Optional[Decimal] = None
    budget_amount: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    machine_count: int = 0
    milestone_count: int = 0
    completed_milestone_count: int = 0
    task_count: int = 0
    completed_task_count: int = 0
    member_count: int = 0
    alert_count: int = 0
    issue_count: int = 0
    document_count: int = 0
    cost_summary: Optional[dict] = None
    recent_activities: Optional[List[dict]] = None


class TimelineEvent(BaseModel):
    """时间线事件"""
    
    event_type: str  # STAGE_CHANGE, STATUS_CHANGE, MILESTONE, TASK, COST, DOCUMENT, etc.
    event_time: datetime
    title: str
    description: Optional[str] = None
    user_name: Optional[str] = None
    related_id: Optional[int] = None
    related_type: Optional[str] = None


class ProjectTimelineResponse(BaseModel):
    """项目时间线响应"""
    
    project_id: int
    project_code: str
    project_name: str
    events: List[TimelineEvent]
    total_events: int


class StageAdvanceRequest(BaseModel):
    """阶段推进请求"""
    
    target_stage: str = Field(..., description="目标阶段（S1-S9）")
    reason: Optional[str] = Field(None, description="推进原因")
    skip_gate_check: bool = Field(False, description="是否跳过阶段门校验（仅管理员）")


class StageAdvanceResponse(BaseModel):
    """阶段推进响应"""
    
    project_id: int
    project_code: str
    project_name: str
    old_stage: str
    new_stage: str
    new_status: Optional[str] = None
    gate_passed: bool
    gate_check_result: Optional[dict] = None
    missing_items: List[str] = []


class ProjectStatusResponse(BaseModel):
    """项目三维状态响应"""
    
    project_id: int
    project_code: str
    project_name: str
    stage: str
    stage_name: Optional[str] = None
    status: str
    status_name: Optional[str] = None
    health: Optional[str] = None
    health_name: Optional[str] = None
    progress_pct: float
    last_updated: Optional[datetime] = None


class BatchUpdateStatusRequest(BaseModel):
    """批量更新项目状态请求"""
    
    project_ids: List[int] = Field(..., description="项目ID列表")
    new_status: str = Field(..., description="新状态（ST01-ST30）")
    reason: Optional[str] = Field(None, description="变更原因")


class BatchArchiveRequest(BaseModel):
    """批量归档项目请求"""
    
    project_ids: List[int] = Field(..., description="项目ID列表")
    archive_reason: Optional[str] = Field(None, description="归档原因")


class BatchAssignPMRequest(BaseModel):
    """批量分配项目经理请求"""
    
    project_ids: List[int] = Field(..., description="项目ID列表")
    pm_id: int = Field(..., description="项目经理ID")


class BatchUpdateStageRequest(BaseModel):
    """批量更新项目阶段请求"""
    
    project_ids: List[int] = Field(..., description="项目ID列表")
    new_stage: str = Field(..., description="新阶段（S1-S9）")
    reason: Optional[str] = Field(None, description="变更原因")


class BatchOperationResponse(BaseModel):
    """批量操作响应"""
    
    success_count: int
    failed_count: int
    failed_projects: List[dict] = []


class ProjectDashboardResponse(BaseModel):
    """项目仪表盘响应"""
    
    project_id: int
    project_code: str
    project_name: str
    
    # 基本信息
    basic_info: dict
    
    # 进度统计
    progress_stats: dict
    
    # 成本统计
    cost_stats: dict
    
    # 任务统计
    task_stats: dict
    
    # 里程碑统计
    milestone_stats: dict
    
    # 风险统计
    risk_stats: Optional[dict] = None
    
    # 问题统计
    issue_stats: Optional[dict] = None
    
    # 资源使用
    resource_usage: Optional[dict] = None
    
    # 最近活动
    recent_activities: List[dict] = []
    
    # 关键指标
    key_metrics: dict

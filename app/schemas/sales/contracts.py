# -*- coding: utf-8 -*-
"""
合同管理 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ..common import TimestampSchema


class ContractDeliverableCreate(BaseModel):
    """创建合同交付物"""

    model_config = ConfigDict(populate_by_name=True)

    contract_id: int = Field(description="合同ID")
    deliverable_name: str = Field(max_length=200, description="交付物名称")
    deliverable_type: Optional[str] = Field(default=None, description="交付物类型")
    specification: Optional[str] = Field(default=None, description="规格要求")
    quantity: Optional[int] = Field(default=None, description="数量")
    unit: Optional[str] = Field(default=None, max_length=20, description="单位")
    delivery_date: Optional[date] = Field(default=None, description="交付日期")
    acceptance_criteria: Optional[str] = Field(default=None, description="验收标准")
    remark: Optional[str] = Field(default=None, description="备注")


class ContractDeliverableResponse(TimestampSchema):
    """合同交付物响应"""

    id: int = Field(description="交付物ID")
    contract_id: int = Field(description="合同ID")
    deliverable_name: str = Field(description="交付物名称")
    deliverable_type: Optional[str] = Field(default=None, description="交付物类型")
    specification: Optional[str] = Field(default=None, description="规格要求")
    quantity: Optional[int] = Field(default=None, description="数量")
    unit: Optional[str] = Field(default=None, description="单位")
    delivery_date: Optional[date] = Field(default=None, description="交付日期")
    acceptance_criteria: Optional[str] = Field(default=None, description="验收标准")
    remark: Optional[str] = Field(default=None, description="备注")


class ContractCreate(BaseModel):
    """创建合同（与 Contract ORM 字段对齐）"""

    model_config = ConfigDict(populate_by_name=True)

    contract_code: Optional[str] = Field(
        default=None, max_length=20, description="合同编码（内部）"
    )
    customer_contract_no: Optional[str] = Field(
        default=None, max_length=100, description="客户合同编号（外部）"
    )
    opportunity_id: int = Field(description="商机ID")
    quote_version_id: Optional[int] = Field(default=None, description="报价版本ID")
    customer_id: int = Field(description="客户ID")
    project_id: Optional[int] = Field(default=None, description="项目ID")
    contract_amount: Optional[Decimal] = Field(default=None, description="合同金额")
    signed_date: Optional[date] = Field(default=None, description="签订日期")
    status: Optional[str] = Field(default=None, description="状态")
    payment_terms_summary: Optional[str] = Field(
        default=None, description="付款条款摘要"
    )
    acceptance_summary: Optional[str] = Field(default=None, description="验收摘要")
    owner_id: Optional[int] = Field(default=None, description="负责人ID")
    deliverables: Optional[List[ContractDeliverableCreate]] = Field(
        default=None, description="交付物列表"
    )


class ContractUpdate(BaseModel):
    """更新合同（与 Contract ORM 字段对齐）"""

    contract_code: Optional[str] = None
    customer_contract_no: Optional[str] = None
    opportunity_id: Optional[int] = None
    quote_version_id: Optional[int] = None
    customer_id: Optional[int] = None
    project_id: Optional[int] = None
    contract_amount: Optional[Decimal] = None
    signed_date: Optional[date] = None
    status: Optional[str] = None
    payment_terms_summary: Optional[str] = None
    acceptance_summary: Optional[str] = None
    owner_id: Optional[int] = None
    deliverables: Optional[List[ContractDeliverableCreate]] = None


class ContractResponse(TimestampSchema):
    """合同响应（与 endpoint 返回字段对齐）"""

    id: int = Field(description="合同ID")
    contract_code: str = Field(description="合同编码（内部）")
    customer_contract_no: Optional[str] = Field(default=None, description="客户合同编号（外部）")
    opportunity_id: int = Field(description="商机ID")
    quote_version_id: Optional[int] = Field(default=None, description="报价版本ID")
    customer_id: int = Field(description="客户ID")
    project_id: Optional[int] = Field(default=None, description="项目ID")
    contract_amount: Optional[Decimal] = Field(default=None, description="合同金额")
    signed_date: Optional[date] = Field(default=None, description="签订日期")
    status: Optional[str] = Field(default=None, description="状态")
    payment_terms_summary: Optional[str] = Field(
        default=None, description="付款条款摘要"
    )
    acceptance_summary: Optional[str] = Field(default=None, description="验收摘要")
    owner_id: Optional[int] = Field(default=None, description="负责人ID")

    # 扩展字段
    opportunity_code: Optional[str] = Field(default=None, description="商机编码")
    customer_name: Optional[str] = Field(default=None, description="客户名称")
    project_code: Optional[str] = Field(default=None, description="项目编码")
    owner_name: Optional[str] = Field(default=None, description="负责人姓名")
    deliverables: Optional[List[ContractDeliverableResponse]] = Field(
        default=None, description="交付物列表"
    )


class ContractAmendmentCreate(BaseModel):
    """创建合同变更"""

    model_config = ConfigDict(populate_by_name=True)

    contract_id: int = Field(description="合同ID")
    amendment_type: str = Field(description="变更类型")
    amendment_reason: str = Field(description="变更原因")
    amendment_content: str = Field(description="变更内容")
    amendment_amount: Optional[Decimal] = Field(default=None, description="变更金额")
    effective_date: Optional[date] = Field(default=None, description="生效日期")
    remark: Optional[str] = Field(default=None, description="备注")


class ContractAmendmentResponse(TimestampSchema):
    """合同变更响应"""

    id: int = Field(description="变更ID")
    contract_id: int = Field(description="合同ID")
    amendment_type: str = Field(description="变更类型")
    amendment_reason: str = Field(description="变更原因")
    amendment_content: str = Field(description="变更内容")
    amendment_amount: Optional[Decimal] = Field(default=None, description="变更金额")
    effective_date: Optional[date] = Field(default=None, description="生效日期")
    remark: Optional[str] = Field(default=None, description="备注")
    created_by_name: Optional[str] = Field(default=None, description="创建人姓名")


class ContractSignRequest(BaseModel):
    """合同签订请求"""

    model_config = ConfigDict(populate_by_name=True)

    contract_id: int = Field(description="合同ID")
    sign_location: Optional[str] = Field(default=None, description="签订地点")
    sign_witness: Optional[str] = Field(default=None, description="见证人")
    remark: Optional[str] = Field(default=None, description="备注")


class ContractProjectCreateRequest(BaseModel):
    """合同项目关联请求"""

    model_config = ConfigDict(populate_by_name=True)

    contract_id: int = Field(description="合同ID")
    project_id: int = Field(description="项目ID")
    allocation_amount: Optional[Decimal] = Field(default=None, description="分配金额")
    allocation_ratio: Optional[Decimal] = Field(default=None, description="分配比例")
    remark: Optional[str] = Field(default=None, description="备注")


# ==================== 审批工作流 Schema ====================


class ApprovalWorkflowStepResponse(BaseModel):
    """审批工作流步骤响应"""

    model_config = {"populate_by_name": True}
    id: int = Field(description="步骤ID")
    workflow_id: int = Field(description="工作流ID")
    step_name: str = Field(description="步骤名称")
    step_order: int = Field(description="步骤顺序")
    step_role: str = Field(description="审批角色")
    approver_id: Optional[int] = Field(default=None, description="审批人ID")
    approver_name: Optional[str] = Field(default=None, description="审批人姓名")
    is_required: bool = Field(default=True, description="是否必需")
    timeout_hours: Optional[int] = Field(default=None, description="超时小时数")


class ApprovalWorkflowCreate(BaseModel):
    """创建审批工作流"""

    model_config = {"populate_by_name": True}
    workflow_type: str = Field(description="工作流类型")
    workflow_name: str = Field(description="工作流名称")
    entity_type: str = Field(description="实体类型")
    description: Optional[str] = Field(default=None, description="描述")
    steps: List[ApprovalWorkflowStepResponse] = Field(description="审批步骤列表")
    is_active: bool = Field(default=True, description="是否启用")


class ApprovalWorkflowUpdate(BaseModel):
    """更新审批工作流"""

    model_config = {"populate_by_name": True}
    workflow_name: Optional[str] = Field(default=None, description="工作流名称")
    description: Optional[str] = Field(default=None, description="描述")
    steps: Optional[List[ApprovalWorkflowStepResponse]] = Field(
        default=None, description="审批步骤列表"
    )
    is_active: Optional[bool] = Field(default=None, description="是否启用")


class ApprovalWorkflowResponse(TimestampSchema):
    """审批工作流响应"""

    model_config = {"populate_by_name": True}
    id: int = Field(description="工作流ID")
    workflow_type: str = Field(description="工作流类型")
    workflow_name: str = Field(description="工作流名称")
    entity_type: str = Field(description="实体类型")
    description: Optional[str] = Field(default=None, description="描述")
    steps: List[ApprovalWorkflowStepResponse] = Field(
        default=[], description="审批步骤列表"
    )
    is_active: bool = Field(description="是否启用")
    created_by: Optional[int] = Field(default=None, description="创建人ID")
    created_by_name: Optional[str] = Field(default=None, description="创建人姓名")
    updated_by: Optional[int] = Field(default=None, description="更新人ID")
    updated_by_name: Optional[str] = Field(default=None, description="更新人姓名")


class ApprovalStartRequest(BaseModel):
    """启动审批请求"""

    model_config = ConfigDict(populate_by_name=True)

    workflow_id: Optional[int] = Field(default=None, description="工作流ID")
    comment: Optional[str] = Field(default=None, description="备注")


class ApprovalActionRequest(BaseModel):
    """审批动作请求"""

    model_config = ConfigDict(populate_by_name=True)

    action: str = Field(description="审批动作：APPROVE, REJECT, RETURN")
    comment: Optional[str] = Field(default=None, description="审批意见")


class ApprovalRecordResponse(TimestampSchema):
    """审批记录响应"""

    id: int = Field(description="审批记录ID")
    step_name: Optional[str] = Field(default=None, description="步骤名称")
    approver_id: Optional[int] = Field(default=None, description="审批人ID")
    approver_name: Optional[str] = Field(default=None, description="审批人姓名")
    status: Optional[str] = Field(default=None, description="状态")
    action: Optional[str] = Field(default=None, description="审批动作")
    comment: Optional[str] = Field(default=None, description="审批意见")
    approved_at: Optional[datetime] = Field(default=None, description="审批时间")


class ApprovalStatusResponse(BaseModel):
    """审批状态响应"""

    model_config = ConfigDict(populate_by_name=True)

    entity_id: int = Field(description="实体ID")
    entity_type: str = Field(description="实体类型")
    workflow_name: Optional[str] = Field(default=None, description="工作流名称")
    current_step: Optional[str] = Field(default=None, description="当前步骤")
    current_approver: Optional[str] = Field(default=None, description="当前审批人")
    status: Optional[str] = Field(default=None, description="审批状态")
    progress: Optional[int] = Field(default=0, description="审批进度百分比")


class ApprovalHistoryResponse(BaseModel):
    """审批历史响应"""

    model_config = ConfigDict(populate_by_name=True)

    entity_id: int = Field(description="实体ID")
    entity_type: str = Field(description="实体类型")
    records: List[ApprovalRecordResponse] = Field(
        default=[], description="审批记录列表"
    )

    # 审批相关
    ("ApprovalWorkflowStepResponse",)
    ("ApprovalWorkflowCreate",)
    ("ApprovalWorkflowUpdate",)
    ("ApprovalWorkflowResponse",)
    ("ApprovalStartRequest",)
    ("ApprovalActionRequest",)
    ("ApprovalRecordResponse",)
    ("ApprovalStatusResponse",)
    ("ApprovalHistoryResponse",)


__all__ = [
    # 合同相关
    "ContractDeliverableCreate",
    "ContractDeliverableResponse",
    "ContractCreate",
    "ContractUpdate",
    "ContractResponse",
    "ContractAmendmentCreate",
    "ContractAmendmentResponse",
    "ContractSignRequest",
    "ContractProjectCreateRequest",
    # 审批相关
    "ApprovalWorkflowStepResponse",
    "ApprovalWorkflowCreate",
    "ApprovalWorkflowUpdate",
    "ApprovalWorkflowResponse",
    "ApprovalStartRequest",
    "ApprovalActionRequest",
    "ApprovalRecordResponse",
    "ApprovalStatusResponse",
    "ApprovalHistoryResponse",
]

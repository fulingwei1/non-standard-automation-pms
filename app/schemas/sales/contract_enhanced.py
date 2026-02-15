# -*- coding: utf-8 -*-
"""
合同管理增强 Schema - 完整的CRUD与审批流程
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ..common import TimestampSchema


# ========== 合同条款 Schemas ==========
class ContractTermBase(BaseModel):
    """合同条款基础"""
    model_config = ConfigDict(from_attributes=True)
    
    term_type: str = Field(..., description="条款类型: subject/price/delivery/payment/warranty/breach")
    term_content: str = Field(..., description="条款内容")


class ContractTermCreate(ContractTermBase):
    """创建合同条款"""
    pass


class ContractTermUpdate(BaseModel):
    """更新合同条款"""
    model_config = ConfigDict(from_attributes=True)
    
    term_type: Optional[str] = None
    term_content: Optional[str] = None


class ContractTermResponse(ContractTermBase, TimestampSchema):
    """合同条款响应"""
    id: int = Field(..., description="条款ID")
    contract_id: int = Field(..., description="合同ID")


# ========== 合同附件 Schemas ==========
class ContractAttachmentBase(BaseModel):
    """合同附件基础"""
    model_config = ConfigDict(from_attributes=True)
    
    file_name: str = Field(..., max_length=200, description="文件名")
    file_path: str = Field(..., max_length=500, description="文件路径")
    file_type: Optional[str] = Field(None, max_length=50, description="文件类型")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")


class ContractAttachmentCreate(ContractAttachmentBase):
    """创建合同附件"""
    pass


class ContractAttachmentResponse(ContractAttachmentBase, TimestampSchema):
    """合同附件响应"""
    id: int = Field(..., description="附件ID")
    contract_id: int = Field(..., description="合同ID")
    uploaded_by: Optional[int] = Field(None, description="上传人ID")


# ========== 合同审批 Schemas ==========
class ContractApprovalBase(BaseModel):
    """合同审批基础"""
    model_config = ConfigDict(from_attributes=True)
    
    approval_level: int = Field(..., description="审批层级")
    approval_role: str = Field(..., max_length=50, description="审批角色")
    approver_id: Optional[int] = Field(None, description="审批人ID")


class ContractApprovalCreate(ContractApprovalBase):
    """创建合同审批"""
    contract_id: int = Field(..., description="合同ID")


class ContractApprovalUpdate(BaseModel):
    """更新合同审批"""
    model_config = ConfigDict(from_attributes=True)
    
    approval_status: str = Field(..., description="审批状态: pending/approved/rejected")
    approval_opinion: Optional[str] = Field(None, description="审批意见")


class ContractApprovalResponse(ContractApprovalBase, TimestampSchema):
    """合同审批响应"""
    id: int = Field(..., description="审批ID")
    contract_id: int = Field(..., description="合同ID")
    approver_name: Optional[str] = Field(None, description="审批人姓名")
    approval_status: str = Field(..., description="审批状态")
    approval_opinion: Optional[str] = Field(None, description="审批意见")
    approved_at: Optional[datetime] = Field(None, description="审批时间")


# ========== 合同 Schemas ==========
class ContractBase(BaseModel):
    """合同基础"""
    model_config = ConfigDict(from_attributes=True)
    
    contract_name: str = Field(..., max_length=200, description="合同名称")
    contract_type: str = Field(..., description="合同类型: sales/purchase/framework")
    customer_id: int = Field(..., description="客户ID")
    total_amount: Decimal = Field(..., description="合同总额")


class ContractCreate(ContractBase):
    """创建合同"""
    contract_code: Optional[str] = Field(None, max_length=50, description="合同编号（可自动生成）")
    customer_contract_no: Optional[str] = Field(None, max_length=100, description="客户合同编号")
    opportunity_id: Optional[int] = Field(None, description="商机ID")
    quote_id: Optional[int] = Field(None, description="报价ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    
    received_amount: Decimal = Field(default=Decimal(0), description="已收款")
    
    signing_date: Optional[date] = Field(None, description="签订日期")
    effective_date: Optional[date] = Field(None, description="生效日期")
    expiry_date: Optional[date] = Field(None, description="到期日期")
    contract_period: Optional[int] = Field(None, description="合同期限（月）")
    
    contract_subject: Optional[str] = Field(None, description="合同标的")
    payment_terms: Optional[str] = Field(None, description="付款条件")
    delivery_terms: Optional[str] = Field(None, description="交付期限")
    
    sales_owner_id: Optional[int] = Field(None, description="签约销售ID")
    contract_manager_id: Optional[int] = Field(None, description="合同管理员ID")
    
    # 嵌套创建
    terms: Optional[List[ContractTermCreate]] = Field(None, description="合同条款列表")


class ContractUpdate(BaseModel):
    """更新合同"""
    model_config = ConfigDict(from_attributes=True)
    
    contract_name: Optional[str] = Field(None, max_length=200)
    contract_type: Optional[str] = None
    customer_contract_no: Optional[str] = None
    customer_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    quote_id: Optional[int] = None
    project_id: Optional[int] = None
    
    total_amount: Optional[Decimal] = None
    received_amount: Optional[Decimal] = None
    
    signing_date: Optional[date] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    contract_period: Optional[int] = None
    
    contract_subject: Optional[str] = None
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    
    status: Optional[str] = None
    sales_owner_id: Optional[int] = None
    contract_manager_id: Optional[int] = None


class ContractResponse(ContractBase, TimestampSchema):
    """合同响应"""
    id: int = Field(..., description="合同ID")
    contract_code: str = Field(..., description="合同编号")
    customer_contract_no: Optional[str] = Field(None, description="客户合同编号")
    
    opportunity_id: Optional[int] = None
    quote_id: Optional[int] = None
    project_id: Optional[int] = None
    
    received_amount: Decimal = Field(..., description="已收款")
    unreceived_amount: Optional[Decimal] = Field(None, description="未收款")
    
    signing_date: Optional[date] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    contract_period: Optional[int] = None
    
    contract_subject: Optional[str] = None
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    
    status: str = Field(..., description="状态")
    sales_owner_id: Optional[int] = None
    contract_manager_id: Optional[int] = None
    
    # 可选的关联数据
    terms: List[ContractTermResponse] = Field(default_factory=list, description="合同条款")
    approvals: List[ContractApprovalResponse] = Field(default_factory=list, description="审批记录")
    attachments: List[ContractAttachmentResponse] = Field(default_factory=list, description="附件列表")


class ContractListResponse(BaseModel):
    """合同列表响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    contract_code: str
    contract_name: str
    contract_type: str
    customer_id: int
    total_amount: Decimal
    received_amount: Decimal
    unreceived_amount: Optional[Decimal] = None
    status: str
    signing_date: Optional[date] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    created_at: datetime


# ========== 合同状态流转 Schemas ==========
class ContractSubmitApproval(BaseModel):
    """提交审批"""
    model_config = ConfigDict(from_attributes=True)
    
    comment: Optional[str] = Field(None, description="提交说明")


class ContractStatusChange(BaseModel):
    """合同状态变更"""
    model_config = ConfigDict(from_attributes=True)
    
    comment: Optional[str] = Field(None, description="变更说明")


# ========== 合同统计 Schemas ==========
class ContractStats(BaseModel):
    """合同统计"""
    model_config = ConfigDict(from_attributes=True)
    
    total_count: int = Field(..., description="合同总数")
    draft_count: int = Field(..., description="草稿数")
    approving_count: int = Field(..., description="审批中数量")
    signed_count: int = Field(..., description="已签署数量")
    executing_count: int = Field(..., description="执行中数量")
    completed_count: int = Field(..., description="已完成数量")
    voided_count: int = Field(..., description="已作废数量")
    
    total_amount: Decimal = Field(..., description="合同总金额")
    received_amount: Decimal = Field(..., description="已收款总额")
    unreceived_amount: Decimal = Field(..., description="未收款总额")

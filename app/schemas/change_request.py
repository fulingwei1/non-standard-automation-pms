# -*- coding: utf-8 -*-
"""
项目变更管理模块 Schema 定义
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.enums import (
    ChangeTypeEnum,
    ChangeSourceEnum,
    ChangeStatusEnum,
    ImpactLevelEnum,
    ApprovalDecisionEnum,
)

# ==================== 变更请求 ====================

class ChangeRequestBase(BaseModel):
    """变更请求基础模型"""
    title: str = Field(..., max_length=200, description="变更标题")
    description: Optional[str] = Field(None, description="变更描述")
    change_type: ChangeTypeEnum = Field(..., description="变更类型")
    change_source: ChangeSourceEnum = Field(..., description="变更来源")
    
    # 影响评估
    cost_impact: Optional[Decimal] = Field(None, description="成本影响（元）")
    cost_impact_level: Optional[ImpactLevelEnum] = Field(None, description="成本影响程度")
    time_impact: Optional[int] = Field(None, description="时间影响（天）")
    time_impact_level: Optional[ImpactLevelEnum] = Field(None, description="时间影响程度")
    scope_impact: Optional[str] = Field(None, description="范围影响描述")
    scope_impact_level: Optional[ImpactLevelEnum] = Field(None, description="范围影响程度")
    risk_assessment: Optional[str] = Field(None, description="风险评估")
    impact_details: Optional[Dict[str, Any]] = Field(None, description="影响评估详情")
    
    # 通知设置
    notify_customer: bool = Field(False, description="是否通知客户")
    notify_team: bool = Field(True, description="是否通知团队")
    
    # 附件
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="附件列表")


class ChangeRequestCreate(ChangeRequestBase):
    """创建变更请求"""
    project_id: int = Field(..., description="项目ID")


class ChangeRequestUpdate(BaseModel):
    """更新变更请求"""
    title: Optional[str] = Field(None, max_length=200, description="变更标题")
    description: Optional[str] = Field(None, description="变更描述")
    change_type: Optional[ChangeTypeEnum] = Field(None, description="变更类型")
    change_source: Optional[ChangeSourceEnum] = Field(None, description="变更来源")
    
    # 影响评估
    cost_impact: Optional[Decimal] = Field(None, description="成本影响（元）")
    cost_impact_level: Optional[ImpactLevelEnum] = Field(None, description="成本影响程度")
    time_impact: Optional[int] = Field(None, description="时间影响（天）")
    time_impact_level: Optional[ImpactLevelEnum] = Field(None, description="时间影响程度")
    scope_impact: Optional[str] = Field(None, description="范围影响描述")
    scope_impact_level: Optional[ImpactLevelEnum] = Field(None, description="范围影响程度")
    risk_assessment: Optional[str] = Field(None, description="风险评估")
    impact_details: Optional[Dict[str, Any]] = Field(None, description="影响评估详情")
    
    # 实施信息
    implementation_plan: Optional[str] = Field(None, description="实施计划")
    implementation_start_date: Optional[datetime] = Field(None, description="实施开始日期")
    implementation_end_date: Optional[datetime] = Field(None, description="实施结束日期")
    implementation_status: Optional[str] = Field(None, description="实施状态")
    implementation_notes: Optional[str] = Field(None, description="实施备注")
    
    # 验证信息
    verification_notes: Optional[str] = Field(None, description="验证说明")
    
    # 通知设置
    notify_customer: Optional[bool] = Field(None, description="是否通知客户")
    notify_team: Optional[bool] = Field(None, description="是否通知团队")
    
    # 附件
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="附件列表")


class ChangeRequestResponse(ChangeRequestBase):
    """变更请求响应"""
    id: int
    change_code: str
    project_id: int
    status: ChangeStatusEnum
    
    # 提交人信息
    submitter_id: int
    submitter_name: Optional[str] = None
    submit_date: Optional[datetime] = None
    
    # 审批信息
    approver_id: Optional[int] = None
    approver_name: Optional[str] = None
    approval_date: Optional[datetime] = None
    approval_decision: ApprovalDecisionEnum
    approval_comments: Optional[str] = None
    
    # 实施信息
    implementation_plan: Optional[str] = None
    implementation_start_date: Optional[datetime] = None
    implementation_end_date: Optional[datetime] = None
    implementation_status: Optional[str] = None
    implementation_notes: Optional[str] = None
    
    # 验证信息
    verification_notes: Optional[str] = None
    verification_date: Optional[datetime] = None
    verified_by_id: Optional[int] = None
    verified_by_name: Optional[str] = None
    
    # 关闭信息
    close_date: Optional[datetime] = None
    close_notes: Optional[str] = None
    
    # 时间戳
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChangeRequestListResponse(BaseModel):
    """变更请求列表响应"""
    id: int
    change_code: str
    project_id: int
    title: str
    change_type: ChangeTypeEnum
    change_source: ChangeSourceEnum
    status: ChangeStatusEnum
    submitter_name: Optional[str] = None
    submit_date: Optional[datetime] = None
    cost_impact: Optional[Decimal] = None
    time_impact: Optional[int] = None
    approval_decision: ApprovalDecisionEnum
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 审批操作 ====================

class ChangeApprovalRequest(BaseModel):
    """变更审批请求"""
    decision: ApprovalDecisionEnum = Field(..., description="审批决策")
    comments: Optional[str] = Field(None, description="审批意见")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="审批附件")


class ChangeApprovalRecordResponse(BaseModel):
    """审批记录响应"""
    id: int
    change_request_id: int
    approver_id: int
    approver_name: Optional[str] = None
    approver_role: Optional[str] = None
    approval_date: Optional[datetime] = None
    decision: ApprovalDecisionEnum
    comments: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 状态变更操作 ====================

class ChangeStatusUpdateRequest(BaseModel):
    """状态变更请求"""
    new_status: ChangeStatusEnum = Field(..., description="新状态")
    notes: Optional[str] = Field(None, description="说明")


class ChangeImplementationRequest(BaseModel):
    """实施信息更新请求"""
    implementation_plan: Optional[str] = Field(None, description="实施计划")
    implementation_start_date: Optional[datetime] = Field(None, description="实施开始日期")
    implementation_end_date: Optional[datetime] = Field(None, description="实施结束日期")
    implementation_status: Optional[str] = Field(None, description="实施状态")
    implementation_notes: Optional[str] = Field(None, description="实施备注")


class ChangeVerificationRequest(BaseModel):
    """验证信息更新请求"""
    verification_notes: str = Field(..., description="验证说明")


class ChangeCloseRequest(BaseModel):
    """关闭变更请求"""
    close_notes: Optional[str] = Field(None, description="关闭说明")


# ==================== 查询参数 ====================

class ChangeRequestQueryParams(BaseModel):
    """变更请求查询参数"""
    project_id: Optional[int] = Field(None, description="项目ID")
    change_type: Optional[ChangeTypeEnum] = Field(None, description="变更类型")
    change_source: Optional[ChangeSourceEnum] = Field(None, description="变更来源")
    status: Optional[ChangeStatusEnum] = Field(None, description="状态")
    submitter_id: Optional[int] = Field(None, description="提交人ID")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    search: Optional[str] = Field(None, description="搜索关键词（标题/描述）")


# ==================== 统计信息 ====================

class ChangeRequestStatistics(BaseModel):
    """变更请求统计信息"""
    total: int = Field(0, description="总数")
    by_status: Dict[str, int] = Field(default_factory=dict, description="按状态统计")
    by_type: Dict[str, int] = Field(default_factory=dict, description="按类型统计")
    by_source: Dict[str, int] = Field(default_factory=dict, description="按来源统计")
    pending_approval: int = Field(0, description="待审批数量")
    approved: int = Field(0, description="已批准数量")
    rejected: int = Field(0, description="已拒绝数量")
    total_cost_impact: Decimal = Field(Decimal(0), description="总成本影响")
    total_time_impact: int = Field(0, description="总时间影响（天）")

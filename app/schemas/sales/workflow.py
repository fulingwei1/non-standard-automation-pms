# -*- coding: utf-8 -*-
"""
销售工作流和目标管理 Schema
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import TimestampSchema


# ==================== 审批工作流 ====================


class ApprovalWorkflowStepBase(BaseModel):
    """审批工作流步骤基础模型"""
    step_order: int = Field(..., description="步骤顺序")
    step_name: str = Field(..., description="步骤名称")
    approver_type: str = Field(..., description="审批人类型：ROLE/USER/DEPARTMENT")
    approver_id: Optional[int] = Field(None, description="审批人ID")
    approver_role: Optional[str] = Field(None, description="审批角色")


class ApprovalWorkflowStepCreate(ApprovalWorkflowStepBase):
    """创建审批工作流步骤"""
    pass


class ApprovalWorkflowStepResponse(ApprovalWorkflowStepBase):
    """审批工作流步骤响应"""
    id: int
    workflow_id: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ApprovalWorkflowBase(BaseModel):
    """审批工作流基础模型"""
    workflow_name: str = Field(..., description="工作流名称")
    workflow_type: str = Field(..., description="工作流类型：QUOTE/CONTRACT/LEAD")
    description: Optional[str] = Field(None, description="工作流描述")
    is_active: bool = Field(True, description="是否启用")


class ApprovalWorkflowCreate(ApprovalWorkflowBase):
    """创建审批工作流"""
    steps: Optional[List[ApprovalWorkflowStepCreate]] = Field(None, description="工作流步骤")


class ApprovalWorkflowUpdate(BaseModel):
    """更新审批工作流"""
    workflow_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    steps: Optional[List[ApprovalWorkflowStepCreate]] = None


class ApprovalWorkflowResponse(ApprovalWorkflowBase):
    """审批工作流响应"""
    id: int
    steps: Optional[List[ApprovalWorkflowStepResponse]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ==================== 销售目标管理 ====================


class SalesTargetCreate(BaseModel):
    """创建销售目标"""

    model_config = {"populate_by_name": True}

    target_scope: str = Field(description="目标范围：PERSONAL/TEAM/DEPARTMENT")
    user_id: Optional[int] = Field(default=None, description="用户ID（个人目标）")
    department_id: Optional[int] = Field(default=None, description="部门ID（部门目标）")
    team_id: Optional[int] = Field(default=None, description="团队ID（团队目标）")
    target_type: str = Field(
        description="目标类型：LEAD_COUNT/OPPORTUNITY_COUNT/CONTRACT_AMOUNT/COLLECTION_AMOUNT"
    )
    target_period: str = Field(description="目标周期：MONTHLY/QUARTERLY/YEARLY")
    period_value: str = Field(description="周期标识：2025-01/2025-Q1/2025")
    target_value: Decimal = Field(gt=0, description="目标值")
    description: Optional[str] = Field(default=None, description="目标描述")
    status: Optional[str] = Field(
        default="ACTIVE", description="状态：ACTIVE/COMPLETED/CANCELLED"
    )


class SalesTargetUpdate(BaseModel):
    """更新销售目标"""

    target_value: Optional[Decimal] = Field(default=None, description="目标值")
    description: Optional[str] = Field(default=None, description="目标描述")
    status: Optional[str] = Field(
        default=None, description="状态：ACTIVE/COMPLETED/CANCELLED"
    )


class SalesTargetResponse(TimestampSchema):
    """销售目标响应"""

    id: int = Field(description="目标ID")
    target_scope: str = Field(description="目标范围：PERSONAL/TEAM/DEPARTMENT")
    user_id: Optional[int] = Field(default=None, description="用户ID")
    department_id: Optional[int] = Field(default=None, description="部门ID")
    team_id: Optional[int] = Field(default=None, description="团队ID")
    target_type: str = Field(description="目标类型")
    target_period: str = Field(description="目标周期")
    period_value: str = Field(description="周期标识")
    target_value: Decimal = Field(description="目标值")
    description: Optional[str] = Field(default=None, description="目标描述")
    status: str = Field(description="状态")
    created_by: int = Field(description="创建人ID")
    actual_value: Optional[Decimal] = Field(default=None, description="实际完成值")
    completion_rate: Optional[float] = Field(default=None, description="完成率(%)")
    user_name: Optional[str] = Field(default=None, description="用户姓名")
    department_name: Optional[str] = Field(default=None, description="部门名称")


# ==================== 销售排名配置 ====================


class RankingMetric(BaseModel):
    """排名指标配置"""

    metric_name: str = Field(description="指标名称")
    display_name: str = Field(description="显示名称")
    weight: float = Field(gt=0, description="权重(0-100)")


class SalesRankingConfigUpdateRequest(BaseModel):
    """更新销售排名权重配置请求"""

    metrics: List[RankingMetric] = Field(description="指标配置列表")


class SalesRankingConfigResponse(TimestampSchema):
    """销售排名配置响应"""

    id: int = Field(description="配置ID")
    metrics: List[RankingMetric] = Field(description="指标配置列表")
    total_weight: float = Field(description="总权重")
    created_by: Optional[int] = Field(default=None, description="创建人ID")
    updated_by: Optional[int] = Field(default=None, description="更新人ID")

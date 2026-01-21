# -*- coding: utf-8 -*-
"""
审批流程和节点 Schema
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== 流程定义 ====================

class ApprovalFlowBase(BaseModel):
    """审批流程基础字段"""
    flow_name: str = Field(..., min_length=1, max_length=100, description="流程名称")
    flow_description: Optional[str] = Field(None, description="流程描述")
    is_default: bool = Field(False, description="是否默认流程")


class ApprovalFlowCreate(ApprovalFlowBase):
    """创建审批流程"""
    template_id: int = Field(..., description="模板ID")
    nodes: Optional[List["ApprovalNodeCreate"]] = Field(None, description="节点列表")


class ApprovalFlowUpdate(BaseModel):
    """更新审批流程"""
    flow_name: Optional[str] = Field(None, min_length=1, max_length=100)
    flow_description: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class ApprovalFlowResponse(ApprovalFlowBase):
    """审批流程响应"""
    id: int
    template_id: int
    version: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    nodes: Optional[List["ApprovalNodeResponse"]] = None

    class Config:
        from_attributes = True


# ==================== 节点定义 ====================

class ApprovalNodeBase(BaseModel):
    """审批节点基础字段"""
    node_code: Optional[str] = Field(None, max_length=50, description="节点编码")
    node_name: str = Field(..., min_length=1, max_length=100, description="节点名称")
    node_order: int = Field(0, description="节点顺序")
    node_type: str = Field("APPROVAL", description="节点类型：APPROVAL/CC/CONDITION/PARALLEL/JOIN")
    approval_mode: Optional[str] = Field("SINGLE", description="审批模式：SINGLE/OR_SIGN/AND_SIGN/SEQUENTIAL")
    approver_type: Optional[str] = Field(None, description="审批人类型")
    approver_config: Optional[Dict[str, Any]] = Field(None, description="审批人配置")
    condition_expression: Optional[str] = Field(None, description="条件表达式")
    can_add_approver: bool = Field(False, description="允许加签")
    can_transfer: bool = Field(True, description="允许转审")
    can_delegate: bool = Field(True, description="允许委托")
    can_reject_to: str = Field("START", description="驳回目标")
    timeout_hours: Optional[int] = Field(None, description="超时时间（小时）")
    timeout_action: Optional[str] = Field(None, description="超时操作")
    notify_config: Optional[Dict[str, Any]] = Field(None, description="通知配置")


class ApprovalNodeCreate(ApprovalNodeBase):
    """创建审批节点"""
    flow_id: Optional[int] = Field(None, description="流程ID（批量创建时可省略）")


class ApprovalNodeUpdate(BaseModel):
    """更新审批节点"""
    node_name: Optional[str] = Field(None, min_length=1, max_length=100)
    node_order: Optional[int] = None
    approval_mode: Optional[str] = None
    approver_type: Optional[str] = None
    approver_config: Optional[Dict[str, Any]] = None
    condition_expression: Optional[str] = None
    can_add_approver: Optional[bool] = None
    can_transfer: Optional[bool] = None
    can_delegate: Optional[bool] = None
    can_reject_to: Optional[str] = None
    timeout_hours: Optional[int] = None
    timeout_action: Optional[str] = None
    notify_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ApprovalNodeResponse(ApprovalNodeBase):
    """审批节点响应"""
    id: int
    flow_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 路由规则 ====================

class ApprovalRoutingRuleBase(BaseModel):
    """路由规则基础字段"""
    rule_name: str = Field(..., min_length=1, max_length=100, description="规则名称")
    rule_order: int = Field(0, description="规则优先级")
    conditions: Optional[Dict[str, Any]] = Field(None, description="条件配置")


class ApprovalRoutingRuleCreate(ApprovalRoutingRuleBase):
    """创建路由规则"""
    template_id: int = Field(..., description="模板ID")
    flow_id: int = Field(..., description="流程ID")


class ApprovalRoutingRuleResponse(ApprovalRoutingRuleBase):
    """路由规则响应"""
    id: int
    template_id: int
    flow_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 解决循环引用
ApprovalFlowCreate.model_rebuild()
ApprovalFlowResponse.model_rebuild()

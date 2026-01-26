# -*- coding: utf-8 -*-
"""
审批实例 Schema
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ApprovalInstanceCreate(BaseModel):
    """创建审批实例（提交审批）"""
    template_code: str = Field(..., description="审批模板编码")
    entity_type: str = Field(..., description="业务实体类型")
    entity_id: int = Field(..., description="业务实体ID")
    form_data: Optional[Dict[str, Any]] = Field(None, description="表单数据")
    title: Optional[str] = Field(None, max_length=200, description="审批标题")
    summary: Optional[str] = Field(None, description="审批摘要")
    urgency: str = Field("NORMAL", description="紧急程度：NORMAL/URGENT/CRITICAL")
    cc_user_ids: Optional[List[int]] = Field(None, description="抄送人ID列表")


class ApprovalInstanceSaveDraft(BaseModel):
    """保存审批草稿"""
    template_code: str = Field(..., description="审批模板编码")
    entity_type: str = Field(..., description="业务实体类型")
    entity_id: int = Field(..., description="业务实体ID")
    form_data: Optional[Dict[str, Any]] = Field(None, description="表单数据")
    title: Optional[str] = Field(None, max_length=200, description="审批标题")


class ApprovalInstanceResponse(BaseModel):
    """审批实例响应"""
    id: int
    instance_no: str
    template_id: int
    flow_id: Optional[int] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    initiator_id: int
    initiator_name: Optional[str] = None
    initiator_dept_id: Optional[int] = None
    status: str
    current_node_id: Optional[int] = None
    urgency: str
    title: Optional[str] = None
    summary: Optional[str] = None
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApprovalTaskBrief(BaseModel):
    """审批任务简要信息"""
    id: int
    node_id: int
    node_name: Optional[str] = None
    assignee_id: int
    assignee_name: Optional[str] = None
    status: str
    action: Optional[str] = None
    comment: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ApprovalLogBrief(BaseModel):
    """审批日志简要信息"""
    id: int
    operator_id: int
    operator_name: Optional[str] = None
    action: str
    comment: Optional[str] = None
    action_at: datetime

    class Config:
        from_attributes = True


class ApprovalInstanceDetail(ApprovalInstanceResponse):
    """审批实例详情（包含任务和日志）"""
    form_data: Optional[Dict[str, Any]] = None
    template_name: Optional[str] = None
    current_node_name: Optional[str] = None
    tasks: Optional[List[ApprovalTaskBrief]] = None
    logs: Optional[List[ApprovalLogBrief]] = None


class ApprovalInstanceListResponse(BaseModel):
    """审批实例列表响应"""
    total: int
    page: int
    page_size: int
    items: List[ApprovalInstanceResponse]

# -*- coding: utf-8 -*-
"""
审批任务 Schema
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== 任务响应 ====================

class ApprovalTaskResponse(BaseModel):
    """审批任务响应"""
    id: int
    instance_id: int
    node_id: int
    task_type: str
    task_order: int
    assignee_id: int
    assignee_name: Optional[str] = None
    assignee_type: str
    original_assignee_id: Optional[int] = None
    status: str
    action: Optional[str] = None
    comment: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    eval_data: Optional[Dict[str, Any]] = None
    due_at: Optional[datetime] = None
    remind_count: int = 0
    completed_at: Optional[datetime] = None
    is_countersign: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    # 关联信息
    instance_title: Optional[str] = None
    instance_no: Optional[str] = None
    instance_urgency: Optional[str] = None
    node_name: Optional[str] = None

    class Config:
        from_attributes = True


class ApprovalTaskListResponse(BaseModel):
    """审批任务列表响应"""
    total: int
    page: int
    page_size: int
    items: List[ApprovalTaskResponse]


# ==================== 操作请求 ====================

class ApproveRequest(BaseModel):
    """审批通过请求"""
    comment: Optional[str] = Field(None, description="审批意见")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="附件列表")
    eval_data: Optional[Dict[str, Any]] = Field(None, description="评估数据（ECN场景）")


class RejectRequest(BaseModel):
    """审批驳回请求"""
    comment: str = Field(..., min_length=1, description="驳回原因（必填）")
    reject_to: str = Field("START", description="驳回目标：START/PREV/节点ID")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="附件列表")


class ReturnRequest(BaseModel):
    """退回请求"""
    target_node_id: int = Field(..., description="目标节点ID")
    comment: str = Field(..., min_length=1, description="退回原因")


class TransferRequest(BaseModel):
    """转审请求"""
    to_user_id: int = Field(..., description="转审目标用户ID")
    comment: Optional[str] = Field(None, description="转审说明")


class AddApproverRequest(BaseModel):
    """加签请求"""
    approver_ids: List[int] = Field(..., min_items=1, description="要添加的审批人ID列表")
    position: str = Field("AFTER", description="加签位置：BEFORE/AFTER")
    comment: Optional[str] = Field(None, description="加签说明")


class AddCCRequest(BaseModel):
    """加抄送请求"""
    cc_user_ids: List[int] = Field(..., min_items=1, description="抄送人ID列表")


class WithdrawRequest(BaseModel):
    """撤回请求"""
    comment: Optional[str] = Field(None, description="撤回说明")


class TerminateRequest(BaseModel):
    """终止请求"""
    comment: str = Field(..., min_length=1, description="终止原因")


class RemindRequest(BaseModel):
    """催办请求"""
    pass


# ==================== 评论 ====================

class CommentRequest(BaseModel):
    """评论请求"""
    content: str = Field(..., min_length=1, description="评论内容")
    parent_id: Optional[int] = Field(None, description="父评论ID（回复时）")
    reply_to_user_id: Optional[int] = Field(None, description="回复的用户ID")
    mentioned_user_ids: Optional[List[int]] = Field(None, description="@提及的用户ID列表")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="附件")


class CommentResponse(BaseModel):
    """评论响应"""
    id: int
    instance_id: int
    user_id: int
    user_name: Optional[str] = None
    content: str
    attachments: Optional[List[Dict[str, Any]]] = None
    parent_id: Optional[int] = None
    reply_to_user_id: Optional[int] = None
    mentioned_user_ids: Optional[List[int]] = None
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 抄送 ====================

class CarbonCopyResponse(BaseModel):
    """抄送记录响应"""
    id: int
    instance_id: int
    node_id: Optional[int] = None
    cc_user_id: int
    cc_user_name: Optional[str] = None
    cc_source: str
    added_by: Optional[int] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    # 关联信息
    instance_title: Optional[str] = None
    instance_no: Optional[str] = None
    initiator_name: Optional[str] = None

    class Config:
        from_attributes = True


class CarbonCopyListResponse(BaseModel):
    """抄送列表响应"""
    total: int
    page: int
    page_size: int
    items: List[CarbonCopyResponse]


# ==================== 代理人 ====================

class DelegateCreate(BaseModel):
    """创建代理人配置"""
    delegate_id: int = Field(..., description="代理人ID")
    start_date: str = Field(..., description="开始日期 YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期 YYYY-MM-DD")
    scope: str = Field("ALL", description="代理范围：ALL/TEMPLATE/CATEGORY")
    template_ids: Optional[List[int]] = Field(None, description="指定模板ID列表")
    categories: Optional[List[str]] = Field(None, description="指定分类列表")
    reason: Optional[str] = Field(None, max_length=200, description="代理原因")
    notify_original: bool = Field(True, description="是否通知原审批人")
    notify_delegate: bool = Field(True, description="是否通知代理人")


class DelegateUpdate(BaseModel):
    """更新代理人配置"""
    delegate_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    scope: Optional[str] = None
    template_ids: Optional[List[int]] = None
    categories: Optional[List[str]] = None
    reason: Optional[str] = None
    notify_original: Optional[bool] = None
    notify_delegate: Optional[bool] = None
    is_active: Optional[bool] = None


class DelegateResponse(BaseModel):
    """代理人配置响应"""
    id: int
    user_id: int
    delegate_id: int
    delegate_name: Optional[str] = None
    scope: str
    template_ids: Optional[List[int]] = None
    categories: Optional[List[str]] = None
    start_date: str
    end_date: str
    is_active: bool
    reason: Optional[str] = None
    notify_original: bool
    notify_delegate: bool
    created_at: datetime

    class Config:
        from_attributes = True

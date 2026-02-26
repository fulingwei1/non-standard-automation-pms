# -*- coding: utf-8 -*-
"""
审批工作流公共请求/响应模型

解决 Issue #22: 消除各业务域重复定义的 SubmitRequest、ApprovalActionRequest 等。
各端点可直接导入使用，无需重复定义。
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class OrderSubmitRequest(BaseModel):
    """通用订单提交审批请求"""

    order_ids: List[int] = Field(..., description="订单ID列表")
    urgency: str = Field("NORMAL", description="紧急程度: LOW/NORMAL/HIGH/URGENT")
    comment: Optional[str] = Field(None, description="提交备注")


class ApprovalActionRequest(BaseModel):
    """审批操作请求"""

    task_id: int = Field(..., description="审批任务ID")
    action: str = Field(..., description="操作类型: approve/reject")
    comment: Optional[str] = Field(None, description="审批意见")


class BatchApprovalRequest(BaseModel):
    """批量审批请求"""

    task_ids: List[int] = Field(..., description="审批任务ID列表")
    action: str = Field(..., description="操作类型: approve/reject")
    comment: Optional[str] = Field(None, description="审批意见")


class WithdrawRequest(BaseModel):
    """撤回请求"""

    order_id: int = Field(..., description="订单ID")
    reason: Optional[str] = Field(None, description="撤回原因")

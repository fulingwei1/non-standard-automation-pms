# -*- coding: utf-8 -*-
"""
审批系统 Schema 定义
"""

from .flow import (
    ApprovalFlowCreate,
    ApprovalFlowResponse,
    ApprovalFlowUpdate,
    ApprovalNodeCreate,
    ApprovalNodeResponse,
    ApprovalNodeUpdate,
    ApprovalRoutingRuleCreate,
    ApprovalRoutingRuleResponse,
)
from .instance import (
    ApprovalInstanceCreate,
    ApprovalInstanceResponse,
    ApprovalInstanceDetail,
    ApprovalInstanceListResponse,
)
from .task import (
    ApprovalTaskResponse,
    ApprovalTaskListResponse,
    ApproveRequest,
    RejectRequest,
    TransferRequest,
    AddApproverRequest,
    AddCCRequest,
    WithdrawRequest,
    RemindRequest,
    CommentRequest,
    CommentResponse,
)
from .template import (
    ApprovalTemplateCreate,
    ApprovalTemplateResponse,
    ApprovalTemplateUpdate,
    ApprovalTemplateListResponse,
)

__all__ = [
    # Template
    "ApprovalTemplateCreate",
    "ApprovalTemplateResponse",
    "ApprovalTemplateUpdate",
    "ApprovalTemplateListResponse",
    # Flow
    "ApprovalFlowCreate",
    "ApprovalFlowResponse",
    "ApprovalFlowUpdate",
    "ApprovalNodeCreate",
    "ApprovalNodeResponse",
    "ApprovalNodeUpdate",
    "ApprovalRoutingRuleCreate",
    "ApprovalRoutingRuleResponse",
    # Instance
    "ApprovalInstanceCreate",
    "ApprovalInstanceResponse",
    "ApprovalInstanceDetail",
    "ApprovalInstanceListResponse",
    # Task
    "ApprovalTaskResponse",
    "ApprovalTaskListResponse",
    "ApproveRequest",
    "RejectRequest",
    "TransferRequest",
    "AddApproverRequest",
    "AddCCRequest",
    "WithdrawRequest",
    "RemindRequest",
    "CommentRequest",
    "CommentResponse",
]

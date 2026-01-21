# -*- coding: utf-8 -*-
"""
统一审批系统模型

包含审批模板、流程定义、实例、任务、日志和代理人等核心模型
"""

from .delegate import ApprovalDelegate, ApprovalDelegateLog
from .flow import ApprovalFlowDefinition, ApprovalNodeDefinition, ApprovalRoutingRule
from .instance import ApprovalInstance
from .log import ApprovalActionLog, ApprovalComment
from .task import ApprovalCarbonCopy, ApprovalCountersignResult, ApprovalTask
from .template import ApprovalTemplate, ApprovalTemplateVersion

__all__ = [
    # 模板
    "ApprovalTemplate",
    "ApprovalTemplateVersion",
    # 流程定义
    "ApprovalFlowDefinition",
    "ApprovalNodeDefinition",
    "ApprovalRoutingRule",
    # 实例
    "ApprovalInstance",
    # 任务
    "ApprovalTask",
    "ApprovalCarbonCopy",
    "ApprovalCountersignResult",
    # 日志
    "ApprovalActionLog",
    "ApprovalComment",
    # 代理
    "ApprovalDelegate",
    "ApprovalDelegateLog",
]

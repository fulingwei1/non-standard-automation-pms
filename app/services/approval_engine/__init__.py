# -*- coding: utf-8 -*-
"""
审批引擎服务 - 统一审批系统

提供：
- 审批流程编排（WorkflowEngine）
- 条件路由（ConditionEvaluator）
- 节点执行（ApprovalNodeExecutor）
- 通知服务（ApprovalNotifyService）
- 代理人管理（ApprovalDelegateService）
- 路由服务（ApprovalRouterService）
- 业务适配器（各业务实体适配）
"""

from .adapters.base import ApprovalAdapter
from .adapters.contract import ContractApprovalAdapter
from .adapters.ecn import EcnApprovalAdapter
from .adapters.invoice import InvoiceApprovalAdapter
from .adapters.project import ProjectApprovalAdapter
from .adapters.quote import QuoteApprovalAdapter
from .adapters.timesheet import TimesheetApprovalAdapter
from .condition_parser import ConditionEvaluator
from .delegate import ApprovalDelegateService
from .engine import ApprovalEngineService
from .executor import ApprovalNodeExecutor
from .notify import ApprovalNotifyService
from .router import ApprovalRouterService
from .visibility import (
    ParticipantRole,
    check_can_operate_instance,
    check_can_remind,
    check_instance_visible,
    check_task_visible,
    filter_visible_instances,
    resolve_participant_role,
)
from .workflow_engine import WorkflowEngine

# 服务层导出
__all__ = [
    "WorkflowEngine",
    "ApprovalEngineService",
    "ApprovalRouterService",
    "ApprovalNodeExecutor",
    "ApprovalNotifyService",
    "ApprovalDelegateService",
    "ConditionEvaluator",
    "EcnApprovalAdapter",
    "QuoteApprovalAdapter",
    "ContractApprovalAdapter",
    "InvoiceApprovalAdapter",
    "ProjectApprovalAdapter",
    "TimesheetApprovalAdapter",
    # Visibility
    "ParticipantRole",
    "check_instance_visible",
    "check_task_visible",
    "filter_visible_instances",
    "check_can_operate_instance",
    "check_can_remind",
    "resolve_participant_role",
]

# 适配器注册表
ADAPTER_REGISTRY = {
    "ECN": EcnApprovalAdapter,
    "QUOTE": QuoteApprovalAdapter,
    "CONTRACT": ContractApprovalAdapter,
    "INVOICE": InvoiceApprovalAdapter,
    "PROJECT": ProjectApprovalAdapter,
    "TIMESHEET": TimesheetApprovalAdapter,
}

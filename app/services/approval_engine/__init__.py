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

from .delegate import ApprovalDelegateService
from .engine import ApprovalEngineService
from .executor import ApprovalNodeExecutor
from .notify import ApprovalNotifyService
from .router import ApprovalRouterService
from .condition_parser import ConditionEvaluator
from .workflow_engine import WorkflowEngine
from .adapters.base import ApprovalAdapter
from .adapters.ecn import EcnApprovalAdapter
from .adapters.quote import QuoteApprovalAdapter
from .adapters.contract import ContractApprovalAdapter
from .adapters.invoice import InvoiceApprovalAdapter
from .adapters.project import ProjectApprovalAdapter
from .adapters.timesheet import TimesheetApprovalAdapter

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

# -*- coding: utf-8 -*-
"""
审批业务适配器

将不同业务实体接入统一审批系统

支持的业务实体:
- QUOTE: 报价审批
- CONTRACT: 合同审批
- INVOICE: 发票审批
- ECN: 工程变更审批
- PROJECT: 项目审批
- TIMESHEET: 工时审批
"""

from .base import ApprovalAdapter
from .contract import ContractApprovalAdapter
from .ecn import EcnApprovalAdapter
from .invoice import InvoiceApprovalAdapter
from .project import ProjectApprovalAdapter
from .quote import QuoteApprovalAdapter
from .timesheet import TimesheetApprovalAdapter

__all__ = [
    "ApprovalAdapter",
    "QuoteApprovalAdapter",
    "ContractApprovalAdapter",
    "InvoiceApprovalAdapter",
    "EcnApprovalAdapter",
    "ProjectApprovalAdapter",
    "TimesheetApprovalAdapter",
]


# 适配器注册表
ADAPTER_REGISTRY = {
    "QUOTE": QuoteApprovalAdapter,
    "CONTRACT": ContractApprovalAdapter,
    "INVOICE": InvoiceApprovalAdapter,
    "ECN": EcnApprovalAdapter,
    "PROJECT": ProjectApprovalAdapter,
    "TIMESHEET": TimesheetApprovalAdapter,
}


def get_adapter(entity_type: str, db):
    """
    获取指定业务类型的适配器实例

    Args:
        entity_type: 业务实体类型 (QUOTE, CONTRACT, ECN, etc.)
        db: 数据库会话

    Returns:
        对应的适配器实例

    Raises:
        ValueError: 如果entity_type不支持
    """
    adapter_class = ADAPTER_REGISTRY.get(entity_type)
    if not adapter_class:
        raise ValueError(f"不支持的业务类型: {entity_type}")
    return adapter_class(db)

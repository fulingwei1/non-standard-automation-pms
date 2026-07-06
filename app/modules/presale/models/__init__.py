# -*- coding: utf-8 -*-
"""
售前管理模块 - 按业务域聚合
"""

# 核心模型（原 presale.py）
from .core import (
    DeliverableStatusEnum,
    PresaleCustomerTechProfile,
    PresaleSolution,
    PresaleSolutionCost,
    PresaleSolutionTemplate,
    PresaleSupportTicket,
    PresaleTenderRecord,
    PresaleTicketDeliverable,
    PresaleTicketProgress,
    PresaleWorkload,
    SolutionStatusEnum,
    TenderResultEnum,
    TicketStatusEnum,
    TicketTypeEnum,
    TicketUrgencyEnum,
)

# 技术参数模板
from .technical_parameter_template import (
    CostCategoryEnum,
    IndustryEnum,
    TechnicalParameterTemplate,
    TestTypeEnum,
)

__all__ = [
    # 核心模型
    "PresaleSupportTicket",
    "PresaleTicketDeliverable",
    "PresaleTicketProgress",
    "PresaleSolution",
    "PresaleSolutionCost",
    "PresaleSolutionTemplate",
    "PresaleWorkload",
    "PresaleCustomerTechProfile",
    "PresaleTenderRecord",
    # 核心枚举
    "TicketTypeEnum",
    "TicketUrgencyEnum",
    "TicketStatusEnum",
    "DeliverableStatusEnum",
    "SolutionStatusEnum",
    "TenderResultEnum",
    # 技术参数模板
    "TechnicalParameterTemplate",
    # 技术参数枚举
    "IndustryEnum",
    "TestTypeEnum",
    "CostCategoryEnum",
]

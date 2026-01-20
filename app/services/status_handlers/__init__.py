# -*- coding: utf-8 -*-
"""
状态处理器模块

按业务领域拆分的状态变更处理器：
- contract_handler: 合同签订事件处理
- material_handler: BOM和物料事件处理
- acceptance_handler: 验收事件处理
- ecn_handler: ECN变更事件处理
"""

from app.services.status_handlers.contract_handler import ContractStatusHandler
from app.services.status_handlers.material_handler import MaterialStatusHandler
from app.services.status_handlers.acceptance_handler import AcceptanceStatusHandler
from app.services.status_handlers.ecn_handler import ECNStatusHandler

__all__ = [
    "ContractStatusHandler",
    "MaterialStatusHandler",
    "AcceptanceStatusHandler",
    "ECNStatusHandler",
]

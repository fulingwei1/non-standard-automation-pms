# -*- coding: utf-8 -*-
"""
库存管理服务包
拆分自 inventory_management_service.py 单体文件
"""
from app.services.inventory.stock_query_service import StockQueryService
from app.services.inventory.transaction_service import TransactionService
from app.services.inventory.stock_update_service import InsufficientStockError, StockUpdateService
from app.services.inventory.inbound_service import InboundService
from app.services.inventory.outbound_service import OutboundService
from app.services.inventory.transfer_service import TransferService
from app.services.inventory.reservation_service import ReservationService
from app.services.inventory.analysis_service import AnalysisService
from app.services.inventory.inventory_management_facade import InventoryManagementService

__all__ = [
    "StockQueryService",
    "TransactionService",
    "StockUpdateService",
    "InboundService",
    "OutboundService",
    "TransferService",
    "ReservationService",
    "AnalysisService",
    "InventoryManagementService",
    "InsufficientStockError",
]

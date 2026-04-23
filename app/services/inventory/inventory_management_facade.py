# -*- coding: utf-8 -*-
"""
库存管理服务 - Facade (向后兼容)
保持 InventoryManagementService 的完整 API 接口，
内部委托给拆分后的子服务。所有现有消费者无需修改。
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.inventory_tracking import MaterialReservation, MaterialStock, MaterialTransaction
from app.services.inventory.stock_query_service import StockQueryService
from app.services.inventory.transaction_service import TransactionService
from app.services.inventory.stock_update_service import InsufficientStockError, StockUpdateService
from app.services.inventory.inbound_service import InboundService
from app.services.inventory.outbound_service import OutboundService
from app.services.inventory.transfer_service import TransferService
from app.services.inventory.reservation_service import ReservationService
from app.services.inventory.analysis_service import AnalysisService


class InventoryManagementService:
    """库存管理服务 Facade — 向后兼容的统一入口"""

    def __init__(self, db: Session, tenant_id: Optional[int] = None):
        self.db = db
        self.tenant_id = tenant_id
        self._query = StockQueryService(db, tenant_id) if tenant_id is not None else None
        self._tx = TransactionService(db, tenant_id) if tenant_id is not None else None
        self._stock_update = StockUpdateService(db, tenant_id) if tenant_id is not None else None
        self._inbound = InboundService(db, tenant_id) if tenant_id is not None else None
        self._outbound = OutboundService(db, tenant_id) if tenant_id is not None else None
        self._transfer = TransferService(db, tenant_id) if tenant_id is not None else None
        self._reservation = ReservationService(db, tenant_id) if tenant_id is not None else None
        self._analysis = AnalysisService(db, tenant_id) if tenant_id is not None else None

    # ---- Stock Query ----
    def get_stock(self, material_id: int, location=None, batch_number=None) -> List[MaterialStock]:
        return self._query.get_stock(material_id, location, batch_number)

    def get_available_quantity(self, material_id: int, location=None) -> Decimal:
        return self._query.get_available_quantity(material_id, location)

    def get_total_quantity(self, material_id: int) -> Decimal:
        return self._query.get_total_quantity(material_id)

    def get_all_stocks(self, location=None, status=None, limit=100) -> List[MaterialStock]:
        return self._query.get_all_stocks(location, status, limit)

    # ---- Transaction ----
    def create_transaction(self, material_id: int, transaction_type: str, quantity: Decimal, **kwargs) -> MaterialTransaction:
        return self._tx.create_transaction(material_id, transaction_type, quantity, **kwargs)

    def get_transactions(self, **kwargs) -> List[MaterialTransaction]:
        return self._tx.get_transactions(**kwargs)

    # ---- Stock Update ----
    def update_stock(self, material_id: int, quantity: Decimal, transaction_type: str, location: str, **kwargs) -> MaterialStock:
        return self._stock_update.update_stock(material_id, quantity, transaction_type, location, **kwargs)

    # ---- Inbound ----
    def purchase_in(self, material_id: int, quantity: Decimal, unit_price: Decimal, location: str, **kwargs) -> Dict:
        return self._inbound.purchase_in(material_id, quantity, unit_price, location, **kwargs)

    # ---- Outbound ----
    def issue_material(self, material_id: int, quantity: Decimal, location: str, **kwargs) -> Dict:
        return self._outbound.issue_material(material_id, quantity, location, **kwargs)

    def return_material(self, material_id: int, quantity: Decimal, location: str, **kwargs) -> Dict:
        return self._outbound.return_material(material_id, quantity, location, **kwargs)

    # ---- Transfer ----
    def transfer_stock(self, material_id: int, quantity: Decimal, from_location: str, to_location: str, **kwargs) -> Dict:
        return self._transfer.transfer_stock(material_id, quantity, from_location, to_location, **kwargs)

    # ---- Reservation ----
    def reserve_material(self, material_id: int, quantity: Decimal, **kwargs) -> MaterialReservation:
        return self._reservation.reserve_material(material_id, quantity, **kwargs)

    def cancel_reservation(self, reservation_id: int, **kwargs) -> MaterialReservation:
        return self._reservation.cancel_reservation(reservation_id, **kwargs)

    # ---- Analysis ----
    def calculate_turnover_rate(self, **kwargs) -> Dict:
        return self._analysis.calculate_turnover_rate(**kwargs)

    def analyze_aging(self, location=None) -> Dict:
        return self._analysis.analyze_aging(location)

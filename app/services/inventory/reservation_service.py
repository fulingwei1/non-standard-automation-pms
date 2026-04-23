# -*- coding: utf-8 -*-
"""物料预留服务"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.inventory_tracking import MaterialReservation, MaterialStock
from app.services.inventory.stock_query_service import StockQueryService
from app.services.inventory.stock_update_service import InsufficientStockError


class ReservationService:
    """物料预留管理"""

    def __init__(self, db: Session, tenant_id: int = 0):
        self.db = db
        self.tenant_id = tenant_id
        self._query = StockQueryService(db, tenant_id)

    def reserve_material(
        self,
        material_id: int,
        quantity: Decimal,
        project_id: Optional[int] = None,
        work_order_id: Optional[int] = None,
        expected_use_date: Optional[date] = None,
        created_by: Optional[int] = None,
        remark: Optional[str] = None,
    ) -> MaterialReservation:
        """预留物料"""
        available = self._query.get_available_quantity(material_id)
        if available < quantity:
            raise InsufficientStockError(f"可用库存不足: 需要 {quantity}, 可用 {available}")

        reservation_no = f"RSV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{material_id}"

        stocks = (
            self.db.query(MaterialStock)
            .filter(
                MaterialStock.tenant_id == self.tenant_id,
                MaterialStock.material_id == material_id,
                MaterialStock.available_quantity > 0,
            )
            .order_by(MaterialStock.last_in_date.asc())
            .all()
        )

        remaining = quantity
        reserved_stocks = []

        for stock in stocks:
            if remaining <= 0:
                break
            reserve_qty = min(stock.available_quantity, remaining)
            stock.reserved_quantity += reserve_qty
            stock.available_quantity -= reserve_qty
            reserved_stocks.append((stock, reserve_qty))
            remaining -= reserve_qty

        first_stock = reserved_stocks[0][0] if reserved_stocks else None

        reservation = MaterialReservation(
            tenant_id=self.tenant_id,
            reservation_no=reservation_no,
            material_id=material_id,
            stock_id=first_stock.id if first_stock else None,
            reserved_quantity=quantity,
            used_quantity=Decimal(0),
            remaining_quantity=quantity,
            project_id=project_id,
            work_order_id=work_order_id,
            reservation_date=datetime.now(),
            expected_use_date=expected_use_date,
            status="ACTIVE",
            created_by=created_by,
            remark=remark,
        )
        self.db.add(reservation)
        self.db.commit()
        return reservation

    def cancel_reservation(
        self,
        reservation_id: int,
        cancelled_by: Optional[int] = None,
        cancel_reason: Optional[str] = None,
    ) -> MaterialReservation:
        """取消预留"""
        reservation = (
            self.db.query(MaterialReservation)
            .filter(
                MaterialReservation.id == reservation_id,
                MaterialReservation.tenant_id == self.tenant_id,
            )
            .first()
        )
        if not reservation:
            raise ValueError(f"预留记录不存在: {reservation_id}")
        if reservation.status not in ["ACTIVE", "PARTIAL_USED"]:
            raise ValueError(f"预留状态不允许取消: {reservation.status}")

        release_qty = reservation.remaining_quantity
        stocks = (
            self.db.query(MaterialStock)
            .filter(
                MaterialStock.tenant_id == self.tenant_id,
                MaterialStock.material_id == reservation.material_id,
                MaterialStock.reserved_quantity > 0,
            )
            .all()
        )

        remaining = release_qty
        for stock in stocks:
            if remaining <= 0:
                break
            release = min(stock.reserved_quantity, remaining)
            stock.reserved_quantity -= release
            stock.available_quantity += release
            remaining -= release

        reservation.status = "CANCELLED"
        reservation.cancelled_by = cancelled_by
        reservation.cancelled_at = datetime.now()
        reservation.cancel_reason = cancel_reason
        self.db.commit()
        return reservation

    def _release_reservation(self, reservation_id: int, quantity: Decimal):
        """释放预留 (内部方法，供领料使用)"""
        reservation = self.db.query(MaterialReservation).get(reservation_id)
        if not reservation or reservation.status not in ["ACTIVE", "PARTIAL_USED"]:
            return
        reservation.used_quantity += quantity
        reservation.remaining_quantity -= quantity
        if reservation.remaining_quantity <= 0:
            reservation.status = "USED"
            reservation.actual_use_date = date.today()
        else:
            reservation.status = "PARTIAL_USED"

# -*- coding: utf-8 -*-
"""
库存管理服务
Team 2: 物料全流程跟踪系统
提供库存更新、预留、领料、退料等核心功能
"""
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from app.models.inventory_tracking import (
    MaterialTransaction,
    MaterialStock,
    MaterialReservation,
    StockAdjustment,
)
from app.models.material import Material
from app.models.production.work_order import WorkOrder
from app.models.project import Project


class InsufficientStockError(Exception):
    """库存不足异常"""
    pass


class InventoryManagementService:
    """库存管理服务"""

    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    # ============ 库存查询 ============

    def get_stock(
        self, 
        material_id: int, 
        location: Optional[str] = None,
        batch_number: Optional[str] = None
    ) -> List[MaterialStock]:
        """查询库存"""
        query = self.db.query(MaterialStock).filter(
            MaterialStock.tenant_id == self.tenant_id,
            MaterialStock.material_id == material_id
        )
        
        if location:
            query = query.filter(MaterialStock.location == location)
        
        if batch_number:
            query = query.filter(MaterialStock.batch_number == batch_number)
        
        return query.all()

    def get_available_quantity(
        self, 
        material_id: int, 
        location: Optional[str] = None
    ) -> Decimal:
        """获取可用库存数量"""
        query = self.db.query(
            func.sum(MaterialStock.available_quantity)
        ).filter(
            MaterialStock.tenant_id == self.tenant_id,
            MaterialStock.material_id == material_id
        )
        
        if location:
            query = query.filter(MaterialStock.location == location)
        
        result = query.scalar()
        return Decimal(result or 0)

    def get_total_quantity(self, material_id: int) -> Decimal:
        """获取总库存数量"""
        result = self.db.query(
            func.sum(MaterialStock.quantity)
        ).filter(
            MaterialStock.tenant_id == self.tenant_id,
            MaterialStock.material_id == material_id
        ).scalar()
        
        return Decimal(result or 0)

    # ============ 交易记录 ============

    def create_transaction(
        self,
        material_id: int,
        transaction_type: str,
        quantity: Decimal,
        unit_price: Decimal = Decimal(0),
        source_location: Optional[str] = None,
        target_location: Optional[str] = None,
        batch_number: Optional[str] = None,
        related_order_id: Optional[int] = None,
        related_order_type: Optional[str] = None,
        related_order_no: Optional[str] = None,
        operator_id: Optional[int] = None,
        remark: Optional[str] = None,
        cost_method: str = 'WEIGHTED_AVG'
    ) -> MaterialTransaction:
        """创建交易记录"""
        
        # 获取物料信息
        material = self.db.query(Material).get(material_id)
        if not material:
            raise ValueError(f"物料不存在: {material_id}")
        
        # 创建交易记录
        transaction = MaterialTransaction(
            tenant_id=self.tenant_id,
            material_id=material_id,
            material_code=material.material_code,
            material_name=material.material_name,
            transaction_type=transaction_type,
            quantity=quantity,
            unit=material.unit,
            unit_price=unit_price,
            total_amount=quantity * unit_price,
            source_location=source_location,
            target_location=target_location,
            batch_number=batch_number,
            related_order_id=related_order_id,
            related_order_type=related_order_type,
            related_order_no=related_order_no,
            transaction_date=datetime.now(),
            operator_id=operator_id,
            remark=remark,
            cost_method=cost_method
        )
        
        self.db.add(transaction)
        self.db.flush()
        
        return transaction

    def get_transactions(
        self,
        material_id: Optional[int] = None,
        transaction_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[MaterialTransaction]:
        """查询交易记录"""
        query = self.db.query(MaterialTransaction).filter(
            MaterialTransaction.tenant_id == self.tenant_id
        )
        
        if material_id:
            query = query.filter(MaterialTransaction.material_id == material_id)
        
        if transaction_type:
            query = query.filter(MaterialTransaction.transaction_type == transaction_type)
        
        if start_date:
            query = query.filter(MaterialTransaction.transaction_date >= start_date)
        
        if end_date:
            query = query.filter(MaterialTransaction.transaction_date <= end_date)
        
        return query.order_by(MaterialTransaction.transaction_date.desc()).limit(limit).all()

    # ============ 库存更新 ============

    def update_stock(
        self,
        material_id: int,
        quantity: Decimal,
        transaction_type: str,
        location: str,
        batch_number: Optional[str] = None,
        unit_price: Decimal = Decimal(0),
        **kwargs
    ) -> MaterialStock:
        """
        更新库存（基于交易记录）
        使用数据库事务保证一致性
        """
        
        # 查找或创建库存记录
        stock = self.db.query(MaterialStock).filter(
            MaterialStock.tenant_id == self.tenant_id,
            MaterialStock.material_id == material_id,
            MaterialStock.location == location,
            MaterialStock.batch_number == (batch_number or '')
        ).first()
        
        material = self.db.query(Material).get(material_id)
        
        if not stock:
            stock = MaterialStock(
                tenant_id=self.tenant_id,
                material_id=material_id,
                material_code=material.material_code,
                material_name=material.material_name,
                location=location,
                batch_number=batch_number or '',
                quantity=Decimal(0),
                available_quantity=Decimal(0),
                reserved_quantity=Decimal(0),
                unit=material.unit,
                unit_price=Decimal(0),
                total_value=Decimal(0)
            )
            self.db.add(stock)
        
        # 根据交易类型更新库存
        if transaction_type in ['PURCHASE_IN', 'TRANSFER_IN', 'RETURN']:
            # 入库
            stock.quantity += quantity
            stock.available_quantity += quantity
            stock.last_in_date = datetime.now()
            
            # 更新加权平均单价
            if transaction_type == 'PURCHASE_IN' and unit_price > 0:
                old_value = stock.quantity * stock.unit_price
                new_value = quantity * unit_price
                total_quantity = stock.quantity
                if total_quantity > 0:
                    stock.unit_price = (old_value + new_value) / total_quantity
        
        elif transaction_type in ['ISSUE', 'SCRAP']:
            # 出库
            if stock.available_quantity < quantity:
                raise InsufficientStockError(
                    f"库存不足: 物料{material.material_code}, "
                    f"需要{quantity}, 可用{stock.available_quantity}"
                )
            
            stock.quantity -= quantity
            stock.available_quantity -= quantity
            stock.last_out_date = datetime.now()
        
        elif transaction_type == 'ADJUST':
            # 调整
            stock.quantity += quantity  # quantity 可正可负
            stock.available_quantity += quantity
        
        # 更新库存总价值
        stock.total_value = stock.quantity * stock.unit_price
        stock.last_update = datetime.now()
        
        # 更新库存状态
        stock.status = self._calculate_stock_status(stock)
        
        self.db.flush()
        
        return stock

    def _calculate_stock_status(self, stock: MaterialStock) -> str:
        """计算库存状态"""
        if stock.expire_date and stock.expire_date < date.today():
            return 'EXPIRED'
        elif stock.quantity <= 0:
            return 'EMPTY'
        else:
            material = self.db.query(Material).get(stock.material_id)
            if material and material.safety_stock > 0:
                if stock.quantity < material.safety_stock:
                    return 'LOW'
        
        return 'NORMAL'

    # ============ 入库操作 ============

    def purchase_in(
        self,
        material_id: int,
        quantity: Decimal,
        unit_price: Decimal,
        location: str,
        batch_number: Optional[str] = None,
        purchase_order_id: Optional[int] = None,
        purchase_order_no: Optional[str] = None,
        operator_id: Optional[int] = None,
        production_date: Optional[date] = None,
        expire_date: Optional[date] = None,
        remark: Optional[str] = None
    ) -> Dict:
        """采购入库"""
        
        # 创建交易记录
        transaction = self.create_transaction(
            material_id=material_id,
            transaction_type='PURCHASE_IN',
            quantity=quantity,
            unit_price=unit_price,
            target_location=location,
            batch_number=batch_number,
            related_order_id=purchase_order_id,
            related_order_type='PURCHASE_ORDER',
            related_order_no=purchase_order_no,
            operator_id=operator_id,
            remark=remark
        )
        
        # 更新库存
        stock = self.update_stock(
            material_id=material_id,
            quantity=quantity,
            transaction_type='PURCHASE_IN',
            location=location,
            batch_number=batch_number,
            unit_price=unit_price
        )
        
        # 更新批次信息
        if production_date:
            stock.production_date = production_date
        if expire_date:
            stock.expire_date = expire_date
        
        self.db.commit()
        
        return {
            'transaction': transaction,
            'stock': stock,
            'message': f'入库成功: {quantity} {stock.unit}'
        }

    # ============ 出库操作 ============

    def issue_material(
        self,
        material_id: int,
        quantity: Decimal,
        location: str,
        work_order_id: Optional[int] = None,
        work_order_no: Optional[str] = None,
        project_id: Optional[int] = None,
        operator_id: Optional[int] = None,
        reservation_id: Optional[int] = None,
        remark: Optional[str] = None,
        cost_method: str = 'FIFO'
    ) -> Dict:
        """领料出库"""
        
        # 检查并释放预留
        if reservation_id:
            self._release_reservation(reservation_id, quantity)
        
        # 根据成本核算方法选择库存
        stocks = self._select_stock_for_issue(material_id, location, quantity, cost_method)
        
        transactions = []
        remaining = quantity
        
        for stock, issue_qty in stocks:
            # 创建交易记录
            transaction = self.create_transaction(
                material_id=material_id,
                transaction_type='ISSUE',
                quantity=issue_qty,
                unit_price=stock.unit_price,
                source_location=location,
                batch_number=stock.batch_number,
                related_order_id=work_order_id,
                related_order_type='WORK_ORDER',
                related_order_no=work_order_no,
                operator_id=operator_id,
                remark=remark,
                cost_method=cost_method
            )
            transactions.append(transaction)
            
            # 更新库存
            self.update_stock(
                material_id=material_id,
                quantity=issue_qty,
                transaction_type='ISSUE',
                location=location,
                batch_number=stock.batch_number
            )
            
            remaining -= issue_qty
            if remaining <= 0:
                break
        
        self.db.commit()
        
        return {
            'transactions': transactions,
            'total_quantity': quantity,
            'total_cost': sum(t.total_amount for t in transactions),
            'message': f'领料成功: {quantity}'
        }

    def _select_stock_for_issue(
        self,
        material_id: int,
        location: str,
        quantity: Decimal,
        cost_method: str
    ) -> List[tuple]:
        """根据成本核算方法选择库存"""
        
        # 查询可用库存
        query = self.db.query(MaterialStock).filter(
            MaterialStock.tenant_id == self.tenant_id,
            MaterialStock.material_id == material_id,
            MaterialStock.location == location,
            MaterialStock.available_quantity > 0
        )
        
        # 根据不同方法排序
        if cost_method == 'FIFO':  # 先进先出
            query = query.order_by(MaterialStock.last_in_date.asc())
        elif cost_method == 'LIFO':  # 后进先出
            query = query.order_by(MaterialStock.last_in_date.desc())
        else:  # 加权平均 (任意顺序)
            query = query.order_by(MaterialStock.id.asc())
        
        stocks = query.all()
        
        if not stocks:
            raise InsufficientStockError(f"物料 {material_id} 在位置 {location} 无可用库存")
        
        # 检查总可用数量
        total_available = sum(s.available_quantity for s in stocks)
        if total_available < quantity:
            raise InsufficientStockError(
                f"库存不足: 需要 {quantity}, 可用 {total_available}"
            )
        
        # 分配出库数量
        result = []
        remaining = quantity
        
        for stock in stocks:
            if remaining <= 0:
                break
            
            issue_qty = min(stock.available_quantity, remaining)
            result.append((stock, issue_qty))
            remaining -= issue_qty
        
        return result

    # ============ 退料操作 ============

    def return_material(
        self,
        material_id: int,
        quantity: Decimal,
        location: str,
        batch_number: Optional[str] = None,
        work_order_id: Optional[int] = None,
        operator_id: Optional[int] = None,
        remark: Optional[str] = None
    ) -> Dict:
        """退料入库"""
        
        # 如果没有指定批次,使用默认批次
        if not batch_number:
            batch_number = f"RETURN-{datetime.now().strftime('%Y%m%d')}"
        
        # 创建交易记录
        transaction = self.create_transaction(
            material_id=material_id,
            transaction_type='RETURN',
            quantity=quantity,
            target_location=location,
            batch_number=batch_number,
            related_order_id=work_order_id,
            related_order_type='WORK_ORDER',
            operator_id=operator_id,
            remark=remark
        )
        
        # 更新库存
        stock = self.update_stock(
            material_id=material_id,
            quantity=quantity,
            transaction_type='RETURN',
            location=location,
            batch_number=batch_number
        )
        
        self.db.commit()
        
        return {
            'transaction': transaction,
            'stock': stock,
            'message': f'退料成功: {quantity}'
        }

    # ============ 库存转移 ============

    def transfer_stock(
        self,
        material_id: int,
        quantity: Decimal,
        from_location: str,
        to_location: str,
        batch_number: Optional[str] = None,
        operator_id: Optional[int] = None,
        remark: Optional[str] = None
    ) -> Dict:
        """库存转移"""
        
        # 出库交易
        out_transaction = self.create_transaction(
            material_id=material_id,
            transaction_type='ISSUE',
            quantity=quantity,
            source_location=from_location,
            batch_number=batch_number,
            operator_id=operator_id,
            remark=f"转移至 {to_location} - {remark or ''}"
        )
        
        # 更新源库存
        from_stock = self.update_stock(
            material_id=material_id,
            quantity=quantity,
            transaction_type='ISSUE',
            location=from_location,
            batch_number=batch_number
        )
        
        # 入库交易
        in_transaction = self.create_transaction(
            material_id=material_id,
            transaction_type='TRANSFER_IN',
            quantity=quantity,
            unit_price=from_stock.unit_price,
            source_location=from_location,
            target_location=to_location,
            batch_number=batch_number,
            operator_id=operator_id,
            remark=f"从 {from_location} 转入 - {remark or ''}"
        )
        
        # 更新目标库存
        to_stock = self.update_stock(
            material_id=material_id,
            quantity=quantity,
            transaction_type='TRANSFER_IN',
            location=to_location,
            batch_number=batch_number,
            unit_price=from_stock.unit_price
        )
        
        self.db.commit()
        
        return {
            'out_transaction': out_transaction,
            'in_transaction': in_transaction,
            'from_stock': from_stock,
            'to_stock': to_stock,
            'message': f'转移成功: {from_location} -> {to_location}, {quantity}'
        }

    # ============ 物料预留 ============

    def reserve_material(
        self,
        material_id: int,
        quantity: Decimal,
        project_id: Optional[int] = None,
        work_order_id: Optional[int] = None,
        expected_use_date: Optional[date] = None,
        created_by: Optional[int] = None,
        remark: Optional[str] = None
    ) -> MaterialReservation:
        """预留物料"""
        
        # 检查可用库存
        available = self.get_available_quantity(material_id)
        if available < quantity:
            raise InsufficientStockError(
                f"可用库存不足: 需要 {quantity}, 可用 {available}"
            )
        
        # 生成预留单号
        reservation_no = f"RSV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{material_id}"
        
        # 查找库存记录进行预留
        stocks = self.db.query(MaterialStock).filter(
            MaterialStock.tenant_id == self.tenant_id,
            MaterialStock.material_id == material_id,
            MaterialStock.available_quantity > 0
        ).order_by(MaterialStock.last_in_date.asc()).all()
        
        remaining = quantity
        reserved_stocks = []
        
        for stock in stocks:
            if remaining <= 0:
                break
            
            reserve_qty = min(stock.available_quantity, remaining)
            
            # 更新库存的预留数量
            stock.reserved_quantity += reserve_qty
            stock.available_quantity -= reserve_qty
            
            reserved_stocks.append((stock, reserve_qty))
            remaining -= reserve_qty
        
        # 创建预留记录 (只保存第一个库存ID)
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
            status='ACTIVE',
            created_by=created_by,
            remark=remark
        )
        
        self.db.add(reservation)
        self.db.commit()
        
        return reservation

    def cancel_reservation(
        self,
        reservation_id: int,
        cancelled_by: Optional[int] = None,
        cancel_reason: Optional[str] = None
    ) -> MaterialReservation:
        """取消预留"""
        
        reservation = self.db.query(MaterialReservation).filter(
            MaterialReservation.id == reservation_id,
            MaterialReservation.tenant_id == self.tenant_id
        ).first()
        
        if not reservation:
            raise ValueError(f"预留记录不存在: {reservation_id}")
        
        if reservation.status not in ['ACTIVE', 'PARTIAL_USED']:
            raise ValueError(f"预留状态不允许取消: {reservation.status}")
        
        # 释放预留数量
        release_qty = reservation.remaining_quantity
        
        stocks = self.db.query(MaterialStock).filter(
            MaterialStock.tenant_id == self.tenant_id,
            MaterialStock.material_id == reservation.material_id,
            MaterialStock.reserved_quantity > 0
        ).all()
        
        remaining = release_qty
        for stock in stocks:
            if remaining <= 0:
                break
            
            release = min(stock.reserved_quantity, remaining)
            stock.reserved_quantity -= release
            stock.available_quantity += release
            remaining -= release
        
        # 更新预留状态
        reservation.status = 'CANCELLED'
        reservation.cancelled_by = cancelled_by
        reservation.cancelled_at = datetime.now()
        reservation.cancel_reason = cancel_reason
        
        self.db.commit()
        
        return reservation

    def _release_reservation(self, reservation_id: int, quantity: Decimal):
        """释放预留 (内部方法)"""
        
        reservation = self.db.query(MaterialReservation).get(reservation_id)
        if not reservation or reservation.status not in ['ACTIVE', 'PARTIAL_USED']:
            return
        
        # 更新已使用数量
        reservation.used_quantity += quantity
        reservation.remaining_quantity -= quantity
        
        if reservation.remaining_quantity <= 0:
            reservation.status = 'USED'
            reservation.actual_use_date = date.today()
        else:
            reservation.status = 'PARTIAL_USED'

    # ============ 库存分析 ============

    def calculate_turnover_rate(
        self,
        material_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """计算库存周转率"""
        
        if not start_date:
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        if not end_date:
            end_date = datetime.now()
        
        query = self.db.query(MaterialTransaction).filter(
            MaterialTransaction.tenant_id == self.tenant_id,
            MaterialTransaction.transaction_type == 'ISSUE',
            MaterialTransaction.transaction_date >= start_date,
            MaterialTransaction.transaction_date <= end_date
        )
        
        if material_id:
            query = query.filter(MaterialTransaction.material_id == material_id)
        
        # 统计出库总额
        total_issue_value = sum(
            t.total_amount for t in query.all()
        )
        
        # 计算平均库存
        stock_query = self.db.query(MaterialStock).filter(
            MaterialStock.tenant_id == self.tenant_id
        )
        if material_id:
            stock_query = stock_query.filter(MaterialStock.material_id == material_id)
        
        avg_stock_value = sum(s.total_value for s in stock_query.all())
        
        # 周转率 = 出库总额 / 平均库存
        turnover_rate = float(total_issue_value / avg_stock_value) if avg_stock_value > 0 else 0
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'total_issue_value': float(total_issue_value),
            'avg_stock_value': float(avg_stock_value),
            'turnover_rate': turnover_rate,
            'turnover_days': int(365 / turnover_rate) if turnover_rate > 0 else 0
        }

    def analyze_aging(self, location: Optional[str] = None) -> List[Dict]:
        """库龄分析"""
        
        query = self.db.query(MaterialStock).filter(
            MaterialStock.tenant_id == self.tenant_id,
            MaterialStock.quantity > 0
        )
        
        if location:
            query = query.filter(MaterialStock.location == location)
        
        stocks = query.all()
        results = []
        
        today = date.today()
        
        for stock in stocks:
            if not stock.last_in_date:
                continue
            
            days_in_stock = (datetime.now() - stock.last_in_date).days
            
            # 库龄分类
            if days_in_stock <= 30:
                aging_category = '0-30天'
            elif days_in_stock <= 90:
                aging_category = '31-90天'
            elif days_in_stock <= 180:
                aging_category = '91-180天'
            elif days_in_stock <= 365:
                aging_category = '181-365天'
            else:
                aging_category = '365天以上'
            
            results.append({
                'material_id': stock.material_id,
                'material_code': stock.material_code,
                'material_name': stock.material_name,
                'location': stock.location,
                'batch_number': stock.batch_number,
                'quantity': float(stock.quantity),
                'unit_price': float(stock.unit_price),
                'total_value': float(stock.total_value),
                'last_in_date': stock.last_in_date.isoformat() if stock.last_in_date else None,
                'days_in_stock': days_in_stock,
                'aging_category': aging_category
            })
        
        return results

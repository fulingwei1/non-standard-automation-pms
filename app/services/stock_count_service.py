# -*- coding: utf-8 -*-
"""
库存盘点服务
Team 2: 物料全流程跟踪系统
提供库存盘点、差异分析、调整审批等功能
"""
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from app.models.inventory_tracking import (
    StockCountTask,
    StockCountDetail,
    StockAdjustment,
    MaterialStock,
    MaterialTransaction,
)
from app.models.material import Material
from app.services.inventory_management_service import InventoryManagementService


class StockCountService:
    """库存盘点服务"""

    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
        self.inventory_service = InventoryManagementService(db, tenant_id)

    # ============ 盘点任务管理 ============

    def create_count_task(
        self,
        count_type: str,
        count_date: date,
        location: Optional[str] = None,
        category_id: Optional[int] = None,
        material_ids: Optional[List[int]] = None,
        created_by: Optional[int] = None,
        assigned_to: Optional[int] = None,
        remark: Optional[str] = None
    ) -> StockCountTask:
        """创建盘点任务"""
        
        # 生成盘点任务号
        task_no = f"CNT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 创建盘点任务
        task = StockCountTask(
            tenant_id=self.tenant_id,
            task_no=task_no,
            count_type=count_type,
            location=location,
            category_id=category_id,
            count_date=count_date,
            status='PENDING',
            created_by=created_by,
            assigned_to=assigned_to,
            total_items=0,
            counted_items=0,
            matched_items=0,
            diff_items=0,
            total_diff_value=Decimal(0),
            remark=remark
        )
        
        self.db.add(task)
        self.db.flush()
        
        # 创建盘点明细
        details = self._create_count_details(task, location, category_id, material_ids)
        task.total_items = len(details)
        
        self.db.commit()
        
        return task

    def _create_count_details(
        self,
        task: StockCountTask,
        location: Optional[str],
        category_id: Optional[int],
        material_ids: Optional[List[int]]
    ) -> List[StockCountDetail]:
        """创建盘点明细"""
        
        # 查询需要盘点的库存
        query = self.db.query(MaterialStock).filter(
            MaterialStock.tenant_id == self.tenant_id,
            MaterialStock.quantity > 0
        )
        
        if location:
            query = query.filter(MaterialStock.location == location)
        
        if category_id:
            query = query.join(Material).filter(Material.category_id == category_id)
        
        if material_ids:
            query = query.filter(MaterialStock.material_id.in_(material_ids))
        
        stocks = query.all()
        
        details = []
        for stock in stocks:
            detail = StockCountDetail(
                tenant_id=self.tenant_id,
                task_id=task.id,
                material_id=stock.material_id,
                material_code=stock.material_code,
                material_name=stock.material_name,
                location=stock.location,
                batch_number=stock.batch_number,
                system_quantity=stock.quantity,
                actual_quantity=None,
                difference=None,
                difference_rate=None,
                unit_price=stock.unit_price,
                diff_value=None,
                status='PENDING'
            )
            self.db.add(detail)
            details.append(detail)
        
        return details

    def get_count_tasks(
        self,
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 50
    ) -> List[StockCountTask]:
        """查询盘点任务列表"""
        
        query = self.db.query(StockCountTask).filter(
            StockCountTask.tenant_id == self.tenant_id
        )
        
        if status:
            query = query.filter(StockCountTask.status == status)
        
        if start_date:
            query = query.filter(StockCountTask.count_date >= start_date)
        
        if end_date:
            query = query.filter(StockCountTask.count_date <= end_date)
        
        return query.order_by(StockCountTask.created_at.desc()).limit(limit).all()

    def get_count_task(self, task_id: int) -> Optional[StockCountTask]:
        """获取盘点任务详情"""
        return self.db.query(StockCountTask).filter(
            StockCountTask.id == task_id,
            StockCountTask.tenant_id == self.tenant_id
        ).first()

    def start_count_task(self, task_id: int) -> StockCountTask:
        """开始盘点"""
        task = self.get_count_task(task_id)
        if not task:
            raise ValueError(f"盘点任务不存在: {task_id}")
        
        if task.status != 'PENDING':
            raise ValueError(f"盘点任务状态不允许开始: {task.status}")
        
        task.status = 'IN_PROGRESS'
        task.start_time = datetime.now()
        
        self.db.commit()
        
        return task

    def cancel_count_task(self, task_id: int) -> StockCountTask:
        """取消盘点"""
        task = self.get_count_task(task_id)
        if not task:
            raise ValueError(f"盘点任务不存在: {task_id}")
        
        if task.status == 'COMPLETED':
            raise ValueError("已完成的盘点任务不能取消")
        
        task.status = 'CANCELLED'
        
        self.db.commit()
        
        return task

    # ============ 盘点明细管理 ============

    def get_count_details(self, task_id: int) -> List[StockCountDetail]:
        """获取盘点明细列表"""
        return self.db.query(StockCountDetail).filter(
            StockCountDetail.task_id == task_id,
            StockCountDetail.tenant_id == self.tenant_id
        ).all()

    def record_actual_quantity(
        self,
        detail_id: int,
        actual_quantity: Decimal,
        counted_by: Optional[int] = None,
        remark: Optional[str] = None
    ) -> StockCountDetail:
        """录入实盘数量"""
        
        detail = self.db.query(StockCountDetail).filter(
            StockCountDetail.id == detail_id,
            StockCountDetail.tenant_id == self.tenant_id
        ).first()
        
        if not detail:
            raise ValueError(f"盘点明细不存在: {detail_id}")
        
        # 计算差异
        detail.actual_quantity = actual_quantity
        detail.difference = actual_quantity - detail.system_quantity
        
        if detail.system_quantity != 0:
            detail.difference_rate = (detail.difference / detail.system_quantity) * 100
        else:
            detail.difference_rate = Decimal(0)
        
        # 计算差异金额
        if detail.unit_price:
            detail.diff_value = detail.difference * detail.unit_price
        
        # 更新状态
        detail.status = 'COUNTED'
        detail.counted_by = counted_by
        detail.counted_at = datetime.now()
        
        if remark:
            detail.remark = remark
        
        # 更新任务统计
        self._update_task_statistics(detail.task_id)
        
        self.db.commit()
        
        return detail

    def batch_record_quantities(
        self,
        records: List[Dict],
        counted_by: Optional[int] = None
    ) -> List[StockCountDetail]:
        """批量录入实盘数量"""
        
        details = []
        for record in records:
            detail = self.record_actual_quantity(
                detail_id=record['detail_id'],
                actual_quantity=Decimal(record['actual_quantity']),
                counted_by=counted_by,
                remark=record.get('remark')
            )
            details.append(detail)
        
        return details

    def mark_for_recount(
        self,
        detail_id: int,
        recount_reason: str
    ) -> StockCountDetail:
        """标记需要复盘"""
        
        detail = self.db.query(StockCountDetail).get(detail_id)
        if not detail:
            raise ValueError(f"盘点明细不存在: {detail_id}")
        
        detail.is_recounted = True
        detail.recount_reason = recount_reason
        detail.status = 'PENDING'
        detail.actual_quantity = None
        detail.difference = None
        detail.difference_rate = None
        
        self.db.commit()
        
        return detail

    def _update_task_statistics(self, task_id: int):
        """更新盘点任务统计"""
        
        task = self.get_count_task(task_id)
        if not task:
            return
        
        details = self.get_count_details(task_id)
        
        # 统计
        task.total_items = len(details)
        task.counted_items = sum(1 for d in details if d.status in ['COUNTED', 'CONFIRMED'])
        task.matched_items = sum(1 for d in details if d.difference == 0)
        task.diff_items = sum(1 for d in details if d.difference != 0 and d.difference is not None)
        task.total_diff_value = sum(
            d.diff_value or Decimal(0) for d in details
        )

    # ============ 盘点审批和调整 ============

    def approve_adjustment(
        self,
        task_id: int,
        approved_by: int,
        auto_adjust: bool = True
    ) -> Dict:
        """批准库存调整"""
        
        task = self.get_count_task(task_id)
        if not task:
            raise ValueError(f"盘点任务不存在: {task_id}")
        
        if task.status != 'IN_PROGRESS':
            raise ValueError(f"盘点任务状态不允许审批: {task.status}")
        
        # 检查是否所有明细都已盘点
        details = self.get_count_details(task_id)
        uncounted = [d for d in details if d.status == 'PENDING']
        
        if uncounted:
            raise ValueError(f"还有 {len(uncounted)} 条明细未盘点")
        
        adjustments = []
        
        for detail in details:
            if detail.difference != 0:
                # 创建库存调整记录
                adjustment = self._create_adjustment(
                    detail=detail,
                    task=task,
                    approved_by=approved_by
                )
                adjustments.append(adjustment)
                
                # 执行库存调整
                if auto_adjust:
                    self._execute_adjustment(adjustment)
                
                detail.status = 'CONFIRMED'
        
        # 更新任务状态
        task.status = 'COMPLETED'
        task.end_time = datetime.now()
        task.approved_by = approved_by
        task.approved_at = datetime.now()
        
        self.db.commit()
        
        return {
            'task': task,
            'adjustments': adjustments,
            'total_adjustments': len(adjustments),
            'total_diff_value': float(task.total_diff_value),
            'message': f'盘点审批完成,共调整 {len(adjustments)} 条记录'
        }

    def _create_adjustment(
        self,
        detail: StockCountDetail,
        task: StockCountTask,
        approved_by: int
    ) -> StockAdjustment:
        """创建库存调整记录"""
        
        # 生成调整单号
        adjustment_no = f"ADJ-{datetime.now().strftime('%Y%m%d%H%M%S')}-{detail.id}"
        
        adjustment = StockAdjustment(
            tenant_id=self.tenant_id,
            adjustment_no=adjustment_no,
            material_id=detail.material_id,
            material_code=detail.material_code,
            material_name=detail.material_name,
            location=detail.location,
            batch_number=detail.batch_number,
            original_quantity=detail.system_quantity,
            actual_quantity=detail.actual_quantity,
            difference=detail.difference,
            difference_rate=detail.difference_rate,
            adjustment_type='INVENTORY',
            reason=f"盘点调整 - 任务号: {task.task_no}",
            adjustment_date=datetime.now(),
            operator_id=detail.counted_by,
            status='APPROVED',
            approved_by=approved_by,
            approved_at=datetime.now(),
            count_task_id=task.id,
            unit_price=detail.unit_price,
            total_impact=detail.diff_value,
            remark=detail.remark
        )
        
        self.db.add(adjustment)
        
        return adjustment

    def _execute_adjustment(self, adjustment: StockAdjustment):
        """执行库存调整"""
        
        # 创建交易记录
        self.inventory_service.create_transaction(
            material_id=adjustment.material_id,
            transaction_type='ADJUST',
            quantity=adjustment.difference,  # 可正可负
            unit_price=adjustment.unit_price or Decimal(0),
            target_location=adjustment.location,
            batch_number=adjustment.batch_number,
            related_order_id=adjustment.count_task_id,
            related_order_type='COUNT_TASK',
            related_order_no=adjustment.adjustment_no,
            operator_id=adjustment.operator_id,
            remark=adjustment.reason
        )
        
        # 更新库存
        self.inventory_service.update_stock(
            material_id=adjustment.material_id,
            quantity=adjustment.difference,
            transaction_type='ADJUST',
            location=adjustment.location,
            batch_number=adjustment.batch_number
        )

    # ============ 盘点报表和分析 ============

    def get_count_summary(self, task_id: int) -> Dict:
        """获取盘点汇总"""
        
        task = self.get_count_task(task_id)
        if not task:
            raise ValueError(f"盘点任务不存在: {task_id}")
        
        details = self.get_count_details(task_id)
        
        # 按差异类型分组统计
        profit_items = [d for d in details if d.difference and d.difference > 0]
        loss_items = [d for d in details if d.difference and d.difference < 0]
        matched_items = [d for d in details if d.difference == 0]
        
        profit_value = sum(d.diff_value or Decimal(0) for d in profit_items)
        loss_value = sum(d.diff_value or Decimal(0) for d in loss_items)
        
        return {
            'task_info': {
                'task_no': task.task_no,
                'count_type': task.count_type,
                'location': task.location,
                'count_date': task.count_date.isoformat() if task.count_date else None,
                'status': task.status
            },
            'statistics': {
                'total_items': task.total_items,
                'counted_items': task.counted_items,
                'matched_items': len(matched_items),
                'profit_items': len(profit_items),
                'loss_items': len(loss_items),
                'diff_items': task.diff_items
            },
            'value_analysis': {
                'profit_value': float(profit_value),
                'loss_value': float(loss_value),
                'net_diff_value': float(task.total_diff_value),
                'accuracy_rate': float(len(matched_items) / task.total_items * 100) if task.total_items > 0 else 0
            },
            'top_differences': self._get_top_differences(details, limit=10)
        }

    def _get_top_differences(
        self,
        details: List[StockCountDetail],
        limit: int = 10
    ) -> List[Dict]:
        """获取差异最大的物料"""
        
        # 按差异金额排序
        sorted_details = sorted(
            [d for d in details if d.diff_value],
            key=lambda x: abs(x.diff_value or Decimal(0)),
            reverse=True
        )[:limit]
        
        return [{
            'material_code': d.material_code,
            'material_name': d.material_name,
            'location': d.location,
            'system_quantity': float(d.system_quantity),
            'actual_quantity': float(d.actual_quantity or 0),
            'difference': float(d.difference or 0),
            'difference_rate': float(d.difference_rate or 0),
            'diff_value': float(d.diff_value or 0)
        } for d in sorted_details]

    def analyze_count_history(
        self,
        material_id: Optional[int] = None,
        location: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """分析历史盘点数据"""
        
        query = self.db.query(StockCountTask).filter(
            StockCountTask.tenant_id == self.tenant_id,
            StockCountTask.status == 'COMPLETED'
        )
        
        if start_date:
            query = query.filter(StockCountTask.count_date >= start_date)
        
        if end_date:
            query = query.filter(StockCountTask.count_date <= end_date)
        
        if location:
            query = query.filter(StockCountTask.location == location)
        
        tasks = query.all()
        
        total_tasks = len(tasks)
        total_items = sum(t.total_items for t in tasks)
        total_matched = sum(t.matched_items for t in tasks)
        total_diff_value = sum(t.total_diff_value or Decimal(0) for t in tasks)
        
        avg_accuracy = (total_matched / total_items * 100) if total_items > 0 else 0
        
        return {
            'period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'summary': {
                'total_count_tasks': total_tasks,
                'total_items_counted': total_items,
                'total_matched_items': total_matched,
                'total_diff_items': total_items - total_matched,
                'avg_accuracy_rate': float(avg_accuracy),
                'total_diff_value': float(total_diff_value)
            },
            'trend': [
                {
                    'count_date': t.count_date.isoformat() if t.count_date else None,
                    'accuracy_rate': float(t.matched_items / t.total_items * 100) if t.total_items > 0 else 0,
                    'diff_value': float(t.total_diff_value or 0)
                }
                for t in tasks
            ]
        }

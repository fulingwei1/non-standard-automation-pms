# -*- coding: utf-8 -*-
"""
采购分析服务 - 交期准时率分析
"""
from datetime import date
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.material import Supplier
from app.models.purchase import GoodsReceipt, PurchaseOrder


class DeliveryPerformanceAnalyzer:
    """交期准时率分析器"""

    @staticmethod
    def get_delivery_performance_data(
        db: Session,
        start_date: date,
        end_date: date,
        supplier_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取供应商交期准时率数据

        对比 promised_date 和 actual_receipt_date
        """
        # 查询收货单和订单
        query = db.query(
            Supplier.id.label('supplier_id'),
            Supplier.supplier_name,
            Supplier.supplier_code,
            GoodsReceipt.id.label('receipt_id'),
            GoodsReceipt.receipt_date,
            GoodsReceipt.receipt_no,
            PurchaseOrder.promised_date,
            PurchaseOrder.order_no,
            PurchaseOrder.id.label('order_id')
        ).join(
            PurchaseOrder, GoodsReceipt.order_id == PurchaseOrder.id
        ).join(
            Supplier, GoodsReceipt.supplier_id == Supplier.id
        ).filter(
            GoodsReceipt.receipt_date >= start_date,
            GoodsReceipt.receipt_date <= end_date
            # 注释：实际数据库中没有status列，使用inspection_status代替
            # GoodsReceipt.status == 'COMPLETED'
        )

        if supplier_id:
            query = query.filter(Supplier.id == supplier_id)

        results = query.all()

        # 按供应商统计
        supplier_stats = {}
        delayed_orders = []

        for row in results:
            sid = row.supplier_id
            if sid not in supplier_stats:
                supplier_stats[sid] = {
                    'supplier_id': sid,
                    'supplier_name': row.supplier_name,
                    'supplier_code': row.supplier_code,
                    'total_deliveries': 0,
                    'on_time_deliveries': 0,
                    'delayed_deliveries': 0,
                    'total_delay_days': 0
                }

            supplier_stats[sid]['total_deliveries'] += 1

            # 计算是否准时
            delay_days = 0
            if row.promised_date and row.receipt_date:
                delay_days = (row.receipt_date - row.promised_date).days
                if delay_days <= 0:
                    supplier_stats[sid]['on_time_deliveries'] += 1
                else:
                    supplier_stats[sid]['delayed_deliveries'] += 1
                    supplier_stats[sid]['total_delay_days'] += delay_days

                    delayed_orders.append({
                        'order_no': row.order_no,
                        'receipt_no': row.receipt_no,
                        'promised_date': row.promised_date.isoformat(),
                        'actual_date': row.receipt_date.isoformat(),
                        'delay_days': delay_days,
                        'supplier_name': row.supplier_name
                    })

        # 计算准时率和平均延期天数
        performance_list = []
        for sid, stats in supplier_stats.items():
            total = stats['total_deliveries']
            on_time_rate = (stats['on_time_deliveries'] / total * 100) if total > 0 else 0

            # 计算该供应商平均延期天数
            supplier_delays = [d['delay_days'] for d in delayed_orders if d.get('supplier_id') == sid]
            avg_delay = sum(supplier_delays) / len(supplier_delays) if supplier_delays else 0

            performance_list.append({
                'supplier_id': sid,
                'supplier_name': stats['supplier_name'],
                'supplier_code': stats['supplier_code'],
                'total_deliveries': stats['total_deliveries'],
                'on_time_deliveries': stats['on_time_deliveries'],
                'delayed_deliveries': stats['delayed_deliveries'],
                'on_time_rate': round(on_time_rate, 2),
                'avg_delay_days': round(avg_delay, 1)
            })

        # 按准时率排序
        performance_list.sort(key=lambda x: x['on_time_rate'], reverse=True)

        return {
            'supplier_performance': performance_list,
            'delayed_orders': delayed_orders[:50],  # 返回前50条延期记录
            'summary': {
                'total_suppliers': len(performance_list),
                'avg_on_time_rate': round(sum(p['on_time_rate'] for p in performance_list) / len(performance_list), 2) if performance_list else 0,
                'total_delayed_orders': len(delayed_orders)
            }
        }

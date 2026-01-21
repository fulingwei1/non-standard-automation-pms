# -*- coding: utf-8 -*-
"""
采购分析服务 - 质量合格率分析
"""
from datetime import date
from typing import Any, Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.material import Supplier
from app.models.purchase import GoodsReceipt, GoodsReceiptItem, PurchaseOrder


class QualityAnalyzer:
    """质量合格率分析器"""

    @staticmethod
    def get_quality_rate_data(
        db: Session,
        start_date: date,
        end_date: date,
        supplier_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取物料质量合格率数据

        qualified_qty / (qualified_qty + rejected_qty)
        """
        # 查询收货明细
        query = db.query(
            Supplier.id.label('supplier_id'),
            Supplier.supplier_name,
            GoodsReceiptItem.material_code,
            GoodsReceiptItem.material_name,
            func.sum(GoodsReceiptItem.qualified_qty).label('total_qualified'),
            func.sum(GoodsReceiptItem.rejected_qty).label('total_rejected'),
            # 使用received_qty作为total_inspected（实际数据库中没有inspect_qty列）
            func.sum(GoodsReceiptItem.received_qty).label('total_inspected')
        ).join(
            GoodsReceipt, GoodsReceiptItem.receipt_id == GoodsReceipt.id
        ).join(
            PurchaseOrder, GoodsReceipt.order_id == PurchaseOrder.id
        ).join(
            Supplier, PurchaseOrder.supplier_id == Supplier.id
        ).filter(
            GoodsReceipt.receipt_date >= start_date,
            GoodsReceipt.receipt_date <= end_date
            # 注释：实际数据库中是inspection_status而不是inspect_status
            # GoodsReceipt.inspect_status == 'COMPLETED'
        )

        if supplier_id:
            query = query.filter(Supplier.id == supplier_id)

        results = query.group_by(
            Supplier.id, Supplier.supplier_name,
            GoodsReceiptItem.material_code, GoodsReceiptItem.material_name
        ).all()

        # 按供应商汇总
        supplier_quality = {}
        for row in results:
            sid = row.supplier_id
            if sid not in supplier_quality:
                supplier_quality[sid] = {
                    'supplier_id': sid,
                    'supplier_name': row.supplier_name,
                    'materials': []
                }

            qualified = float(row.total_qualified or 0)
            rejected = float(row.total_rejected or 0)
            total = qualified + rejected
            pass_rate = (qualified / total * 100) if total > 0 else 100

            supplier_quality[sid]['materials'].append({
                'material_code': row.material_code,
                'material_name': row.material_name,
                'qualified_qty': qualified,
                'rejected_qty': rejected,
                'total_qty': total,
                'pass_rate': round(pass_rate, 2)
            })

        # 计算供应商综合合格率
        quality_list = []
        for sid, data in supplier_quality.items():
            total_qualified = sum(m['qualified_qty'] for m in data['materials'])
            total_rejected = sum(m['rejected_qty'] for m in data['materials'])
            total = total_qualified + total_rejected
            overall_rate = (total_qualified / total * 100) if total > 0 else 100

            quality_list.append({
                'supplier_id': sid,
                'supplier_name': data['supplier_name'],
                'materials': data['materials'],
                'total_qualified': total_qualified,
                'total_rejected': total_rejected,
                'total_qty': total,
                'overall_pass_rate': round(overall_rate, 2),
                'material_count': len(data['materials'])
            })

        quality_list.sort(key=lambda x: x['overall_pass_rate'], reverse=True)

        return {
            'supplier_quality': quality_list,
            'summary': {
                'total_suppliers': len(quality_list),
                'avg_pass_rate': round(sum(q['overall_pass_rate'] for q in quality_list) / len(quality_list), 2) if quality_list else 0,
                'high_quality_suppliers': sum(1 for q in quality_list if q['overall_pass_rate'] >= 98),
                'low_quality_suppliers': sum(1 for q in quality_list if q['overall_pass_rate'] < 90)
            }
        }

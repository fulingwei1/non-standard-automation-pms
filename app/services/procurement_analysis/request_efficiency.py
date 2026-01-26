# -*- coding: utf-8 -*-
"""
采购分析服务 - 申请处理时效分析
"""
from datetime import date, datetime
from typing import Any, Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.purchase import PurchaseOrder, PurchaseRequest


class RequestEfficiencyAnalyzer:
    """申请处理时效分析器"""

    @staticmethod
    def get_request_efficiency_data(
        db: Session,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        获取采购申请处理时效数据

        申请提交到订单创建的时间差
        """
        # 查询采购申请
        query = db.query(
            PurchaseRequest.id,
            PurchaseRequest.request_no,
            PurchaseRequest.requested_at,
            PurchaseRequest.status,
            PurchaseRequest.total_amount,
            PurchaseRequest.source_type,
            func.min(PurchaseOrder.created_at).label('order_created_at')
        ).outerjoin(
            PurchaseOrder, PurchaseRequest.id == PurchaseOrder.source_request_id
        ).filter(
            PurchaseRequest.requested_at >= start_date,
            PurchaseRequest.requested_at <= end_date
        ).group_by(
            PurchaseRequest.id
        )

        results = query.all()

        efficiency_data = []
        pending_count = 0
        processed_count = 0
        total_processing_hours = 0

        for row in results:
            requested_at = row.requested_at
            order_created_at = row.order_created_at

            if order_created_at:
                # 已处理
                processing_hours = (order_created_at - requested_at).total_seconds() / 3600
                total_processing_hours += processing_hours
                processed_count += 1

                efficiency_data.append({
                    'request_no': row.request_no,
                    'requested_at': requested_at.isoformat() if requested_at else None,
                    'order_created_at': order_created_at.isoformat() if order_created_at else None,
                    'processing_hours': round(processing_hours, 2),
                    'processing_days': round(processing_hours / 24, 1),
                    'status': row.status,
                    'amount': float(row.total_amount or 0)
                })
            else:
                # 未处理
                pending_hours = (datetime.now() - requested_at).total_seconds() / 3600
                pending_count += 1

                efficiency_data.append({
                    'request_no': row.request_no,
                    'requested_at': requested_at.isoformat() if requested_at else None,
                    'order_created_at': None,
                    'processing_hours': round(pending_hours, 2),
                    'processing_days': round(pending_hours / 24, 1),
                    'status': row.status,
                    'amount': float(row.total_amount or 0),
                    'is_pending': True
                })

        # 按处理时长排序
        efficiency_data.sort(key=lambda x: x['processing_hours'], reverse=True)

        # 计算统计数据
        avg_processing_hours = total_processing_hours / processed_count if processed_count > 0 else 0
        processed_within_24h = sum(1 for e in efficiency_data if not e.get('is_pending') and e['processing_hours'] <= 24)
        processed_within_48h = sum(1 for e in efficiency_data if not e.get('is_pending') and e['processing_hours'] <= 48)

        return {
            'efficiency_data': efficiency_data[:50],
            'summary': {
                'total_requests': len(results),
                'processed_count': processed_count,
                'pending_count': pending_count,
                'avg_processing_hours': round(avg_processing_hours, 2),
                'avg_processing_days': round(avg_processing_hours / 24, 1),
                'processed_within_24h': processed_within_24h,
                'processed_within_48h': processed_within_48h,
                'within_24h_rate': round(processed_within_24h / processed_count * 100, 2) if processed_count > 0 else 0
            }
        }

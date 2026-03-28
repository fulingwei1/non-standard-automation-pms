# -*- coding: utf-8 -*-
"""项目采购关联视图"""

from typing import Any, Dict, List
from sqlalchemy.orm import Session


def get_project_procurement_overview(db: Session, project_id: int) -> Dict[str, Any]:
    """获取项目采购总览"""
    from app.models.purchase import PurchaseRequest, PurchaseOrder
    
    requests = db.query(PurchaseRequest).filter(PurchaseRequest.project_id == project_id).all()
    orders = db.query(PurchaseOrder).filter(PurchaseOrder.project_id == project_id).all()
    
    return {
        "purchase_requests": {"total": len(requests), "approved": sum(1 for r in requests if r.status == "APPROVED")},
        "purchase_orders": {"total": len(orders), "received": sum(1 for o in orders if o.status == "RECEIVED")},
    }

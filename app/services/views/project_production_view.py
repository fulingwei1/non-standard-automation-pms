# -*- coding: utf-8 -*-
"""项目生产关联视图"""

from typing import Any, Dict, List
from sqlalchemy.orm import Session


def get_project_production_overview(db: Session, project_id: int) -> Dict[str, Any]:
    """获取项目生产总览"""
    from app.models.production import WorkOrder
    
    work_orders = db.query(WorkOrder).filter(WorkOrder.project_id == project_id).all()
    
    return {
        "total": len(work_orders),
        "completed": sum(1 for wo in work_orders if wo.status == "COMPLETED"),
        "in_progress": sum(1 for wo in work_orders if wo.status == "IN_PROGRESS"),
        "pending": sum(1 for wo in work_orders if wo.status == "PENDING"),
        "details": [
            {"id": wo.id, "status": wo.status, "planned_start": str(wo.planned_start) if wo.planned_start else None}
            for wo in work_orders
        ],
    }

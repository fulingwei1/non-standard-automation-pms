# -*- coding: utf-8 -*-
"""项目售后关联视图"""

from typing import Any, Dict, List
from sqlalchemy.orm import Session


def get_project_after_sales_overview(db: Session, project_id: int) -> Dict[str, Any]:
    """获取项目售后总览"""
    from app.models.after_sales import AfterSalesFeedback, AfterSalesMaintenance, AfterSalesSupportTicket
    
    feedbacks = db.query(AfterSalesFeedback).filter(AfterSalesFeedback.project_id == project_id).all()
    maintenance = db.query(AfterSalesMaintenance).filter(AfterSalesMaintenance.project_id == project_id).all()
    tickets = db.query(AfterSalesSupportTicket).filter(AfterSalesSupportTicket.project_id == project_id).all()
    
    return {
        "feedbacks": {"total": len(feedbacks), "pending": sum(1 for f in feedbacks if f.status == "PENDING"), "resolved": sum(1 for f in feedbacks if f.status == "RESOLVED")},
        "maintenance": {"total": len(maintenance), "scheduled": sum(1 for m in maintenance if m.status == "SCHEDULED"), "completed": sum(1 for m in maintenance if m.status == "COMPLETED")},
        "support_tickets": {"total": len(tickets), "open": sum(1 for t in tickets if t.status == "OPEN"), "resolved": sum(1 for t in tickets if t.status == "RESOLVED")},
    }

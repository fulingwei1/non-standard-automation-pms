# -*- coding: utf-8 -*-
"""项目售后关联视图 - 完整版"""

from typing import Any, Dict, List
from datetime import date
from sqlalchemy.orm import Session


def get_project_after_sales_overview(db: Session, project_id: int) -> Dict[str, Any]:
    """获取项目售后完整总览"""
    from app.models.after_sales import (
        AfterSalesFeedback,
        AfterSalesMaintenance,
        AfterSalesSupportTicket,
        AfterSalesWarranty,
        AfterSalesSparePart,
        AfterSalesFieldService,
        AfterSalesSLA,
        AfterSalesSatisfaction,
    )
    
    # 客户反馈
    feedbacks = db.query(AfterSalesFeedback).filter(AfterSalesFeedback.project_id == project_id).all()
    
    # 维修保养
    maintenance = db.query(AfterSalesMaintenance).filter(AfterSalesMaintenance.project_id == project_id).all()
    
    # 支持工单
    tickets = db.query(AfterSalesSupportTicket).filter(AfterSalesSupportTicket.project_id == project_id).all()
    
    # 质保
    warranties = db.query(AfterSalesWarranty).filter(AfterSalesWarranty.project_id == project_id).all()
    active_warranty = next((w for w in warranties if w.status == "ACTIVE"), None)
    
    # 备件
    spare_parts = db.query(AfterSalesSparePart).filter(AfterSalesSparePart.project_id == project_id).all()
    
    # 现场服务
    field_services = db.query(AfterSalesFieldService).filter(AfterSalesFieldService.project_id == project_id).all()
    
    # SLA
    sla_records = db.query(AfterSalesSLA).filter(AfterSalesSLA.project_id == project_id).all()
    sla_total = len(sla_records)
    
    # 满意度
    satisfaction = db.query(AfterSalesSatisfaction).filter(AfterSalesSatisfaction.project_id == project_id).all()
    sat_total = len(satisfaction)
    
    return {
        # 质保状态
        "warranty": {
            "has_warranty": active_warranty is not None,
            "warranty_type": active_warranty.warranty_type if active_warranty else None,
            "warranty_end": str(active_warranty.warranty_end) if active_warranty else None,
            "days_remaining": (active_warranty.warranty_end - date.today()).days if active_warranty and active_warranty.warranty_end else 0,
            "is_expired": active_warranty.warranty_end < date.today() if active_warranty and active_warranty.warranty_end else True,
        },
        
        # 客户反馈
        "feedbacks": {
            "total": len(feedbacks),
            "pending": sum(1 for f in feedbacks if f.status == "PENDING"),
            "resolved": sum(1 for f in feedbacks if f.status == "RESOLVED"),
            "complaints": sum(1 for f in feedbacks if f.feedback_type == "COMPLAINT"),
        },
        
        # 维修保养
        "maintenance": {
            "total": len(maintenance),
            "scheduled": sum(1 for m in maintenance if m.status == "SCHEDULED"),
            "completed": sum(1 for m in maintenance if m.status == "COMPLETED"),
            "overdue": sum(1 for m in maintenance if m.status == "SCHEDULED" and m.scheduled_date and m.scheduled_date < date.today()),
        },
        
        # 支持工单
        "support_tickets": {
            "total": len(tickets),
            "open": sum(1 for t in tickets if t.status == "OPEN"),
            "in_progress": sum(1 for t in tickets if t.status == "IN_PROGRESS"),
            "resolved": sum(1 for t in tickets if t.status == "RESOLVED"),
            "urgent": sum(1 for t in tickets if t.priority == "URGENT"),
        },
        
        # 备件
        "spare_parts": {
            "total": len(spare_parts),
            "in_stock": sum(1 for p in spare_parts if p.status == "IN_STOCK"),
            "low_stock": sum(1 for p in spare_parts if p.quantity <= p.min_stock and p.quantity > 0),
            "out_of_stock": sum(1 for p in spare_parts if p.quantity == 0),
        },
        
        # 现场服务
        "field_services": {
            "total": len(field_services),
            "planned": sum(1 for s in field_services if s.status == "PLANNED"),
            "completed": sum(1 for s in field_services if s.status == "COMPLETED"),
            "total_hours": sum(s.service_hours or 0 for s in field_services),
            "warranty_services": sum(1 for s in field_services if s.is_warranty),
        },
        
        # SLA
        "sla": {
            "total": sla_total,
            "response_met_rate": round(sum(1 for s in sla_records if s.response_met) / sla_total * 100, 1) if sla_total else 0,
            "resolve_met_rate": round(sum(1 for s in sla_records if s.resolve_met) / sla_total * 100, 1) if sla_total else 0,
        },
        
        # 满意度
        "satisfaction": {
            "total": sat_total,
            "avg_score": round(sum(s.overall_score or 0 for s in satisfaction) / sat_total, 1) if sat_total else 0,
            "avg_nps": round(sum(s.nps_score or 0 for s in satisfaction) / sat_total, 1) if sat_total else 0,
        },
    }

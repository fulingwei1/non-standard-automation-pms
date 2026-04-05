# -*- coding: utf-8 -*-
"""
售后服务 API

提供客户反馈、维修保养、技术支持工单的管理功能
"""

from datetime import datetime
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.after_sales import (
    AfterSalesFeedback,
    AfterSalesMaintenance,
    AfterSalesSupportTicket,
)
from app.schemas.common import ResponseModel

router = APIRouter()


# ==================== 客户反馈管理 ====================

@router.get("/projects/{project_id}/feedback", response_model=List[dict])
def get_project_feedback(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """获取项目客户反馈列表"""
    feedbacks = db.query(AfterSalesFeedback).filter(
        AfterSalesFeedback.project_id == project_id
    ).order_by(AfterSalesFeedback.created_at.desc()).all()
    
    return [
        {
            "id": f.id,
            "feedback_type": f.feedback_type,
            "feedback_content": f.feedback_content,
            "priority": f.priority,
            "status": f.status,
            "created_at": f.created_at,
            "assignee_name": f.assignee.username if f.assignee else None,
        }
        for f in feedbacks
    ]


@router.post("/projects/{project_id}/feedback", status_code=status.HTTP_201_CREATED)
def create_feedback(
    project_id: int,
    feedback_type: str = Query(..., description="反馈类型：COMPLAINT/SUGGESTION/PRAISE"),
    feedback_content: str = Query(..., description="反馈内容"),
    priority: str = Query("MEDIUM", description="优先级"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """创建客户反馈"""
    feedback = AfterSalesFeedback(
        project_id=project_id,
        feedback_type=feedback_type,
        feedback_content=feedback_content,
        priority=priority,
        status="PENDING",
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return {"id": feedback.id, "message": "反馈创建成功"}


# ==================== 维修保养管理 ====================

@router.get("/projects/{project_id}/maintenance", response_model=List[dict])
def get_project_maintenance(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """获取项目维修保养记录"""
    records = db.query(AfterSalesMaintenance).filter(
        AfterSalesMaintenance.project_id == project_id
    ).order_by(AfterSalesMaintenance.scheduled_date.desc()).all()
    
    return [
        {
            "id": r.id,
            "maintenance_type": r.maintenance_type,
            "maintenance_content": r.maintenance_content,
            "scheduled_date": r.scheduled_date,
            "status": r.status,
            "technician_name": r.technician.username if r.technician else None,
        }
        for r in records
    ]


@router.post("/projects/{project_id}/maintenance", status_code=status.HTTP_201_CREATED)
def create_maintenance(
    project_id: int,
    maintenance_type: str = Query(..., description="保养类型"),
    maintenance_content: str = Query(..., description="保养内容"),
    scheduled_date: str = Query(..., description="计划日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """创建维修保养记录"""
    record = AfterSalesMaintenance(
        project_id=project_id,
        maintenance_type=maintenance_type,
        maintenance_content=maintenance_content,
        scheduled_date=scheduled_date,
        status="SCHEDULED",
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return {"id": record.id, "message": "保养记录创建成功"}


# ==================== 技术支持工单 ====================

@router.get("/projects/{project_id}/support-tickets", response_model=List[dict])
def get_project_support_tickets(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """获取项目技术支持工单"""
    tickets = db.query(AfterSalesSupportTicket).filter(
        AfterSalesSupportTicket.project_id == project_id
    ).order_by(AfterSalesSupportTicket.created_at.desc()).all()
    
    return [
        {
            "id": t.id,
            "ticket_no": t.ticket_no,
            "subject": t.subject,
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "created_at": t.created_at,
            "assignee_name": t.assignee.username if t.assignee else None,
        }
        for t in tickets
    ]


@router.post("/projects/{project_id}/support-tickets", status_code=status.HTTP_201_CREATED)
def create_support_ticket(
    project_id: int,
    subject: str = Query(..., description="主题"),
    description: str = Query(..., description="问题描述"),
    category: str = Query("TECHNICAL", description="分类"),
    priority: str = Query("MEDIUM", description="优先级"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """创建技术支持工单"""
    ticket_no = f"SUP-{datetime.now().strftime('%Y%m%d')}-{project_id}"
    
    ticket = AfterSalesSupportTicket(
        project_id=project_id,
        ticket_no=ticket_no,
        subject=subject,
        description=description,
        category=category,
        priority=priority,
        status="OPEN",
    )
    
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    return {"id": ticket.id, "ticket_no": ticket.ticket_no, "message": "工单创建成功"}



# ==================== 质保管理 ====================

@router.get("/projects/{project_id}/warranty")
def get_warranty(project_id: int, db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """获取项目质保信息"""
    from app.models.after_sales import AfterSalesWarranty
    warranties = db.query(AfterSalesWarranty).filter(AfterSalesWarranty.project_id == project_id).all()
    return [{"id": w.id, "warranty_no": w.warranty_no, "warranty_type": w.warranty_type, "warranty_start": str(w.warranty_start), "warranty_end": str(w.warranty_end), "status": w.status, "scope": w.scope} for w in warranties]

@router.post("/projects/{project_id}/warranty", status_code=status.HTTP_201_CREATED)
def create_warranty(project_id: int, warranty_type: str = Query("STANDARD"), warranty_months: int = Query(12), scope: str = Query(""), db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """创建质保记录"""
    from app.models.after_sales import AfterSalesWarranty
    from datetime import date
    from dateutil.relativedelta import relativedelta
    start = date.today()
    end = start + relativedelta(months=warranty_months)
    w = AfterSalesWarranty(project_id=project_id, warranty_no=f"WRT-{project_id}-{start.strftime('%Y%m%d')}", warranty_type=warranty_type, warranty_start=start, warranty_end=end, warranty_months=warranty_months, scope=scope, status="ACTIVE")
    db.add(w)
    db.commit()
    return {"id": w.id, "warranty_no": w.warranty_no}


# ==================== 备件管理 ====================

@router.get("/projects/{project_id}/spare-parts")
def get_spare_parts(project_id: int, db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """获取项目备件列表"""
    from app.models.after_sales import AfterSalesSparePart
    parts = db.query(AfterSalesSparePart).filter(AfterSalesSparePart.project_id == project_id).all()
    return [{"id": p.id, "part_no": p.part_no, "part_name": p.part_name, "quantity": p.quantity, "min_stock": p.min_stock, "status": p.status, "supplier": p.supplier} for p in parts]

@router.post("/projects/{project_id}/spare-parts", status_code=status.HTTP_201_CREATED)
def create_spare_part(project_id: int, part_name: str = Query(...), part_spec: str = Query(""), quantity: int = Query(0), supplier: str = Query(""), db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """添加备件"""
    from app.models.after_sales import AfterSalesSparePart
    p = AfterSalesSparePart(project_id=project_id, part_no=f"SP-{project_id}-{datetime.now().strftime('%H%M%S')}", part_name=part_name, part_spec=part_spec, quantity=quantity, supplier=supplier, status="IN_STOCK" if quantity > 0 else "OUT_OF_STOCK")
    db.add(p)
    db.commit()
    return {"id": p.id, "part_no": p.part_no}


# ==================== 现场服务 ====================

@router.get("/projects/{project_id}/field-services")
def get_field_services(project_id: int, db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """获取项目现场服务记录"""
    from app.models.after_sales import AfterSalesFieldService
    services = db.query(AfterSalesFieldService).filter(AfterSalesFieldService.project_id == project_id).all()
    return [{"id": s.id, "service_no": s.service_no, "service_type": s.service_type, "service_content": s.service_content, "planned_date": str(s.planned_date), "engineer_name": s.engineer_name, "status": s.status, "is_warranty": s.is_warranty} for s in services]

@router.post("/projects/{project_id}/field-services", status_code=status.HTTP_201_CREATED)
def create_field_service(project_id: int, service_type: str = Query(...), service_content: str = Query(...), planned_date: str = Query(...), engineer_name: str = Query(""), db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """创建现场服务记录"""
    from app.models.after_sales import AfterSalesFieldService
    s = AfterSalesFieldService(project_id=project_id, service_no=f"FS-{project_id}-{datetime.now().strftime('%Y%m%d%H%M')}", service_type=service_type, service_content=service_content, planned_date=planned_date, engineer_name=engineer_name, status="PLANNED", is_warranty=True)
    db.add(s)
    db.commit()
    return {"id": s.id, "service_no": s.service_no}



# ==================== SLA 管理 ====================

@router.get("/projects/{project_id}/sla-stats")
def get_sla_stats(project_id: int, db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """获取项目 SLA 统计"""
    from app.models.after_sales import AfterSalesSLA
    sla_records = db.query(AfterSalesSLA).filter(AfterSalesSLA.project_id == project_id).all()
    total = len(sla_records)
    response_met = sum(1 for s in sla_records if s.response_met)
    resolve_met = sum(1 for s in sla_records if s.resolve_met)
    return {
        "total": total,
        "response_met_rate": round(response_met / total * 100, 1) if total else 0,
        "resolve_met_rate": round(resolve_met / total * 100, 1) if total else 0,
        "avg_response_hours": round(sum(s.actual_response_hours or 0 for s in sla_records) / total, 1) if total else 0,
        "avg_resolve_hours": round(sum(s.actual_resolve_hours or 0 for s in sla_records) / total, 1) if total else 0,
    }


# ==================== 客户满意度 ====================

@router.get("/projects/{project_id}/satisfaction")
def get_satisfaction(project_id: int, db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """获取项目满意度统计"""
    from app.models.after_sales import AfterSalesSatisfaction
    records = db.query(AfterSalesSatisfaction).filter(AfterSalesSatisfaction.project_id == project_id).all()
    total = len(records)
    if not total:
        return {"total": 0, "avg_overall": 0, "avg_nps": 0}
    return {
        "total": total,
        "avg_overall": round(sum(r.overall_score or 0 for r in records) / total, 1),
        "avg_response": round(sum(r.response_score or 0 for r in records) / total, 1),
        "avg_quality": round(sum(r.quality_score or 0 for r in records) / total, 1),
        "avg_attitude": round(sum(r.attitude_score or 0 for r in records) / total, 1),
        "avg_nps": round(sum(r.nps_score or 0 for r in records) / total, 1),
        "promoters": sum(1 for r in records if (r.nps_score or 0) >= 9),
        "passives": sum(1 for r in records if 7 <= (r.nps_score or 0) <= 8),
        "detractors": sum(1 for r in records if (r.nps_score or 0) <= 6),
    }

@router.post("/projects/{project_id}/satisfaction", status_code=status.HTTP_201_CREATED)
def create_satisfaction(project_id: int, overall_score: int = Query(..., ge=1, le=10), response_score: int = Query(5, ge=1, le=10), quality_score: int = Query(5, ge=1, le=10), attitude_score: int = Query(5, ge=1, le=10), nps_score: int = Query(5, ge=0, le=10), comments: str = Query(""), db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """提交满意度评价"""
    from app.models.after_sales import AfterSalesSatisfaction
    s = AfterSalesSatisfaction(project_id=project_id, overall_score=overall_score, response_score=response_score, quality_score=quality_score, attitude_score=attitude_score, nps_score=nps_score, comments=comments)
    db.add(s)
    db.commit()
    return {"id": s.id, "message": "满意度评价已提交"}


# ==================== 知识库 ====================

@router.get("/knowledge")
def search_knowledge(keyword: str = Query(""), category: str = Query(None), db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """搜索售后知识库"""
    from app.models.after_sales import AfterSalesKnowledge
    query = db.query(AfterSalesKnowledge).filter(AfterSalesKnowledge.status == "PUBLISHED")
    if keyword:
        query = query.filter(AfterSalesKnowledge.title.contains(keyword) | AfterSalesKnowledge.keywords.contains(keyword) | AfterSalesKnowledge.content.contains(keyword))
    if category:
        query = query.filter(AfterSalesKnowledge.category == category)
    results = query.order_by(AfterSalesKnowledge.view_count.desc()).limit(20).all()
    return [{"id": k.id, "title": k.title, "category": k.category, "keywords": k.keywords, "view_count": k.view_count, "helpful_count": k.helpful_count} for k in results]

@router.post("/knowledge", status_code=status.HTTP_201_CREATED)
def create_knowledge(title: str = Query(...), category: str = Query("FAQ"), content: str = Query(...), keywords: str = Query(""), project_type: str = Query(""), db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """添加知识库文章"""
    from app.models.after_sales import AfterSalesKnowledge
    k = AfterSalesKnowledge(title=title, category=category, content=content, keywords=keywords, project_type=project_type, status="PUBLISHED", created_by=current_user.id)
    db.add(k)
    db.commit()
    return {"id": k.id, "message": "知识库文章已创建"}


# ==================== 工单升级 ====================

@router.post("/projects/{project_id}/support-tickets/{ticket_id}/escalate")
def escalate_ticket(project_id: int, ticket_id: int, reason: str = Query(...), db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """工单升级"""
    ticket = db.query(AfterSalesSupportTicket).filter(AfterSalesSupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")
    # 升级优先级
    priority_order = ["LOW", "MEDIUM", "HIGH", "URGENT"]
    current_idx = priority_order.index(ticket.priority) if ticket.priority in priority_order else 0
    if current_idx < len(priority_order) - 1:
        ticket.priority = priority_order[current_idx + 1]
    ticket.status = "IN_PROGRESS"
    db.commit()
    return {"id": ticket.id, "new_priority": ticket.priority, "message": f"工单已升级为 {ticket.priority}，原因：{reason}"}

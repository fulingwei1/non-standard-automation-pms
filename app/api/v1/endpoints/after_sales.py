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

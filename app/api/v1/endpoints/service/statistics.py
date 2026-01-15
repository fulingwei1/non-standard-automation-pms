# -*- coding: utf-8 -*-
"""
客服统计 API
自动生成，从 service.py 拆分
"""

from typing import Any, List, Optional

from datetime import datetime, date, timedelta

from decimal import Decimal

import os

import uuid

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body, UploadFile, File, Form

from sqlalchemy.orm import Session

from sqlalchemy import desc, or_, func

from app.api import deps

from app.core.config import settings

from app.core import security

from app.models.user import User

from app.models.project import Project, Customer

from app.models.service import (

from app.schemas.service import (


from fastapi import APIRouter

router = APIRouter(
    prefix="/service/statistics",
    tags=["statistics"]
)

# ==================== 路由定义 ====================
# 共 1 个路由

# ==================== 客服统计（给生产总监看） ====================

@router.get("/dashboard-statistics", response_model=ServiceDashboardStatistics, status_code=status.HTTP_200_OK)
def get_service_dashboard_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    客服部统计（给生产总监看）
    """
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    
    # 服务案例统计
    active_cases = db.query(ServiceTicket).filter(
        ServiceTicket.status.in_(["PENDING", "IN_PROGRESS"])
    ).count()
    
    resolved_today = db.query(ServiceTicket).filter(
        ServiceTicket.status == "RESOLVED",
        ServiceTicket.resolved_time >= today_start
    ).count()
    
    pending_cases = db.query(ServiceTicket).filter(
        ServiceTicket.status == "PENDING"
    ).count()
    
    # 平均响应时间（从服务工单中计算：响应时间 - 报告时间）
    tickets_with_response = db.query(ServiceTicket).filter(
        ServiceTicket.response_time.isnot(None),
        ServiceTicket.reported_time.isnot(None)
    ).all()
    
    avg_response_time = 0.0
    if tickets_with_response:
        total_hours = 0
        for ticket in tickets_with_response:
            if ticket.response_time and ticket.reported_time:
                delta = ticket.response_time - ticket.reported_time
                total_hours += delta.total_seconds() / 3600.0
        avg_response_time = total_hours / len(tickets_with_response) if tickets_with_response else 0.0
    
    # 客户满意度（转换为百分制）
    completed_surveys = db.query(CustomerSatisfaction).filter(
        CustomerSatisfaction.status == "COMPLETED",
        CustomerSatisfaction.overall_score.isnot(None)
    ).all()
    
    customer_satisfaction = 0.0
    if completed_surveys:
        total_score = sum(float(s.overall_score) for s in completed_surveys)
        customer_satisfaction = (total_score / len(completed_surveys)) * 20  # 5分制转百分制
    
    # 现场服务（从服务记录中统计，使用INSTALLATION类型作为现场服务）
    on_site_services = db.query(ServiceRecord).filter(
        ServiceRecord.service_type.in_(["INSTALLATION", "REPAIR", "MAINTENANCE"]),
        ServiceRecord.status.in_(["SCHEDULED", "IN_PROGRESS"])
    ).count()
    
    # 在岗工程师（简化处理：查询有客服工程师角色的用户）
    from app.models.organization import UserRole, Role
    engineer_role = db.query(Role).filter(
        or_(
            Role.role_code == "customer_service_engineer",
            Role.role_code == "客服工程师",
            Role.role_name.like("%客服%")
        )
    ).first()
    
    total_engineers = 0
    active_engineers = 0
    if engineer_role:
        total_engineers = db.query(User).join(UserRole).filter(
            UserRole.role_id == engineer_role.id,
            User.is_active == True
        ).count()
        # 简化处理：假设所有工程师都在岗
        active_engineers = total_engineers
    else:
        # 如果没有找到角色，尝试从服务记录中统计
        engineers = db.query(ServiceRecord.service_engineer_id).distinct().all()
        total_engineers = len(engineers)
        active_engineers = total_engineers
    
    return ServiceDashboardStatistics(
        active_cases=active_cases,
        resolved_today=resolved_today,
        pending_cases=pending_cases,
        avg_response_time=avg_response_time,
        customer_satisfaction=customer_satisfaction,
        on_site_services=on_site_services,
        total_engineers=total_engineers,
        active_engineers=active_engineers,
    )




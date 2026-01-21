# -*- coding: utf-8 -*-
"""
服务工单管理 - 状态管理
"""
from datetime import datetime
from typing import Any

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.service import ServiceTicket
from app.models.user import User
from app.schemas.service import ServiceTicketClose, ServiceTicketResponse

from fastapi import APIRouter

router = APIRouter()


@router.put("/{ticket_id}/status", response_model=ServiceTicketResponse, status_code=status.HTTP_200_OK)
def update_service_ticket_status(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    status: str = Query(..., description="新状态：PENDING/IN_PROGRESS/RESOLVED/CLOSED"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新工单状态
    """
    ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="服务工单不存在")

    if status not in ["PENDING", "IN_PROGRESS", "RESOLVED", "CLOSED"]:
        raise HTTPException(status_code=400, detail="无效的状态值")

    old_status = ticket.status
    ticket.status = status

    # 如果状态变为已解决或已关闭，记录解决时间
    if status in ["RESOLVED", "CLOSED"] and not ticket.resolved_time:
        ticket.resolved_time = datetime.now()

    # 如果状态变为处理中，记录响应时间（如果还没有）
    if status == "IN_PROGRESS" and not ticket.response_time:
        ticket.response_time = datetime.now()

    # 更新时间线
    if not ticket.timeline:
        ticket.timeline = []
    ticket.timeline.append({
        "type": "STATUS_CHANGE",
        "timestamp": datetime.now().isoformat(),
        "user": current_user.real_name or current_user.username,
        "description": f"状态变更：{old_status} → {status}",
    })

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # 同步SLA监控状态
    try:
        from app.services.sla_service import sync_ticket_to_sla_monitor
        sync_ticket_to_sla_monitor(db, ticket)
    except Exception as e:
        import logging
        logging.error(f"同步SLA监控状态失败: {e}")

    return ticket


@router.put("/{ticket_id}/close", response_model=ServiceTicketResponse, status_code=status.HTTP_200_OK)
def close_service_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    close_in: ServiceTicketClose,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    关闭服务工单
    """
    ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="服务工单不存在")

    if ticket.status == "CLOSED":
        raise HTTPException(status_code=400, detail="工单已关闭")

    ticket.solution = close_in.solution
    ticket.root_cause = close_in.root_cause
    ticket.preventive_action = close_in.preventive_action
    ticket.satisfaction = close_in.satisfaction
    ticket.feedback = close_in.feedback
    ticket.resolved_time = datetime.now()
    ticket.status = "CLOSED"

    # 更新时间线
    if not ticket.timeline:
        ticket.timeline = []
    ticket.timeline.append({
        "type": "CLOSED",
        "timestamp": datetime.now().isoformat(),
        "user": current_user.real_name or current_user.username,
        "description": "工单已关闭",
    })

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # 同步SLA监控状态
    try:
        from app.services.sla_service import sync_ticket_to_sla_monitor
        sync_ticket_to_sla_monitor(db, ticket)
    except Exception as e:
        import logging
        logging.error(f"同步SLA监控状态失败: {e}")

    # 自动提取知识
    try:
        from app.services.knowledge_extraction_service import (
            auto_extract_knowledge_from_ticket,
        )
        auto_extract_knowledge_from_ticket(db, ticket, auto_publish=True)
    except Exception as e:
        import logging
        logging.error(f"自动提取知识失败: {e}")

    return ticket

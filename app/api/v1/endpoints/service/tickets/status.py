# -*- coding: utf-8 -*-
"""
服务工单管理 - 状态管理

使用统一状态更新服务重构
"""
import logging
from datetime import datetime
from typing import Any

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.service import ServiceTicket
from app.models.user import User
from app.schemas.service import ServiceTicketClose, ServiceTicketResponse
from app.services.status_update_service import StatusUpdateService

from fastapi import APIRouter

logger = logging.getLogger(__name__)
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

    使用统一状态更新服务，支持：
    - 状态值验证
    - 自动时间戳记录
    - 历史记录
    - SLA监控同步
    """
    ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="服务工单不存在")

    # 创建历史记录回调
    def history_callback(entity, old_status, new_status, operator, reason):
        """记录状态变更到时间线"""
        if not entity.timeline:
            entity.timeline = []
        entity.timeline.append({
            "type": "STATUS_CHANGE",
            "timestamp": datetime.now().isoformat(),
            "user": operator.real_name or operator.username,
            "description": f"状态变更：{old_status} → {new_status}",
        })

    # 创建更新后回调（同步SLA监控）
    def after_update_callback(entity, old_status, new_status, operator):
        """状态更新后同步SLA监控"""
        try:
            from app.services.sla_service import sync_ticket_to_sla_monitor
            sync_ticket_to_sla_monitor(db, entity)
        except Exception as e:
            logger.error(f"同步SLA监控状态失败: {e}", exc_info=True)

    # 使用统一状态更新服务
    service = StatusUpdateService(db)
    result = service.update_status(
        entity=ticket,
        new_status=status,
        operator=current_user,
        valid_statuses=["PENDING", "IN_PROGRESS", "RESOLVED", "CLOSED"],
        timestamp_fields={
            "RESOLVED": "resolved_time",
            "CLOSED": "resolved_time",
            "IN_PROGRESS": "response_time",
        },
        history_callback=history_callback,
        after_update_callback=after_update_callback,
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail="; ".join(result.errors) if result.errors else "状态更新失败",
        )

    return result.entity


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

    使用统一状态更新服务，支持：
    - 状态验证（不能重复关闭）
    - 自动记录解决时间
    - 历史记录
    - SLA监控同步
    - 知识自动提取
    """
    ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="服务工单不存在")

    if ticket.status == "CLOSED":
        raise HTTPException(status_code=400, detail="工单已关闭")

    # 更新关闭相关字段
    ticket.solution = close_in.solution
    ticket.root_cause = close_in.root_cause
    ticket.preventive_action = close_in.preventive_action
    ticket.satisfaction = close_in.satisfaction
    ticket.feedback = close_in.feedback

    # 创建历史记录回调
    def history_callback(entity, old_status, new_status, operator, reason):
        """记录关闭操作到时间线"""
        if not entity.timeline:
            entity.timeline = []
        entity.timeline.append({
            "type": "CLOSED",
            "timestamp": datetime.now().isoformat(),
            "user": operator.real_name or operator.username,
            "description": "工单已关闭",
        })

    # 创建更新后回调（同步SLA和提取知识）
    def after_update_callback(entity, old_status, new_status, operator):
        """状态更新后同步SLA监控和提取知识"""
        # 同步SLA监控状态
        try:
            from app.services.sla_service import sync_ticket_to_sla_monitor
            sync_ticket_to_sla_monitor(db, entity)
        except Exception as e:
            logger.error(f"同步SLA监控状态失败: {e}", exc_info=True)

        # 自动提取知识
        try:
            from app.services.knowledge_extraction_service import (
                auto_extract_knowledge_from_ticket,
            )
            auto_extract_knowledge_from_ticket(db, entity, auto_publish=True)
        except Exception as e:
            logger.error(f"自动提取知识失败: {e}", exc_info=True)

    # 使用统一状态更新服务
    service = StatusUpdateService(db)
    result = service.update_status(
        entity=ticket,
        new_status="CLOSED",
        operator=current_user,
        valid_statuses=["CLOSED"],  # 只允许关闭状态
        timestamp_fields={
            "CLOSED": "resolved_time",
        },
        history_callback=history_callback,
        after_update_callback=after_update_callback,
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail="; ".join(result.errors) if result.errors else "关闭工单失败",
        )

    return result.entity

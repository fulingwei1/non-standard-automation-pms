# -*- coding: utf-8 -*-
"""
服务工单管理 - 状态管理

使用统一状态更新服务重构
"""
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.service.enums import (
    ServiceTicketStatusEnum,
    get_service_ticket_transition_rules,
    normalized_service_ticket_status_value,
    validate_service_ticket_transition,
)
from app.models.user import User
from app.schemas.service import ServiceTicketClose, ServiceTicketResponse
from app.services.status_update_service import StatusUpdateService

from ..access import ensure_service_ticket_access_or_raise

logger = logging.getLogger(__name__)
router = APIRouter()


@router.put(
    "/{ticket_id}/status", response_model=ServiceTicketResponse, status_code=status.HTTP_200_OK
)
def update_service_ticket_status(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    status: str = Query(..., description="新状态：PENDING/IN_PROGRESS/RESOLVED/CLOSED"),
    current_user: User = Depends(security.require_permission("service:update")),
) -> Any:
    """
    更新工单状态

    使用统一状态更新服务，支持：
    - 状态值验证
    - 自动时间戳记录
    - 历史记录
    - SLA监控同步
    """
    ticket = ensure_service_ticket_access_or_raise(db, current_user, ticket_id)
    normalized_status = normalized_service_ticket_status_value(status)
    current_status = normalized_service_ticket_status_value(ticket.status)
    is_allowed, error_message = validate_service_ticket_transition(current_status, normalized_status)
    if not is_allowed:
        raise HTTPException(status_code=400, detail=error_message)

    if current_status == normalized_status:
        if ticket.status != current_status:
            ticket.status = current_status
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
        return ticket

    ticket.status = current_status

    # 创建历史记录回调
    def history_callback(entity, old_status, new_status, operator, reason):
        """记录状态变更到时间线"""
        if not entity.timeline:
            entity.timeline = []
        entity.timeline.append(
            {
                "type": "STATUS_CHANGE",
                "timestamp": datetime.now().isoformat(),
                "user": operator.real_name or operator.username,
                "description": f"状态变更：{old_status} → {new_status}",
            }
        )

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
        new_status=normalized_status,
        operator=current_user,
        valid_statuses=[status_enum.value for status_enum in ServiceTicketStatusEnum],
        transition_rules=get_service_ticket_transition_rules(),
        timestamp_fields={
            ServiceTicketStatusEnum.RESOLVED.value: "resolved_time",
            ServiceTicketStatusEnum.CLOSED.value: "resolved_time",
            ServiceTicketStatusEnum.IN_PROGRESS.value: "response_time",
        },
        history_callback=history_callback,
        after_update_callback=after_update_callback,
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail="; ".join(result.errors) if result.errors else "状态更新失败",
        )

    try:
        from app.services.service.service_ticket_notifications import (
            send_service_ticket_notification,
        )

        send_service_ticket_notification(
            db,
            result.entity,
            f"status_changed_to_{normalized_status}",
            actor=current_user,
        )
    except Exception as e:
        logger.error(f"发送服务工单状态变更通知失败: {e}", exc_info=True)

    return result.entity


@router.put(
    "/{ticket_id}/close", response_model=ServiceTicketResponse, status_code=status.HTTP_200_OK
)
def close_service_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    close_in: ServiceTicketClose,
    current_user: User = Depends(security.require_permission("service:update")),
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
    ticket = ensure_service_ticket_access_or_raise(db, current_user, ticket_id)
    current_status = normalized_service_ticket_status_value(ticket.status)

    if current_status == ServiceTicketStatusEnum.CLOSED.value:
        raise HTTPException(status_code=400, detail="工单已关闭")

    if current_status != ServiceTicketStatusEnum.RESOLVED.value:
        raise HTTPException(status_code=400, detail="工单必须为 RESOLVED 后才能关闭")

    ticket.status = current_status

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
        entity.timeline.append(
            {
                "type": "CLOSED",
                "timestamp": datetime.now().isoformat(),
                "user": operator.real_name or operator.username,
                "description": "工单已关闭",
            }
        )

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
        new_status=ServiceTicketStatusEnum.CLOSED.value,
        operator=current_user,
        valid_statuses=[ServiceTicketStatusEnum.CLOSED.value],  # 只允许关闭状态
        transition_rules=get_service_ticket_transition_rules(),
        timestamp_fields={
            ServiceTicketStatusEnum.CLOSED.value: "resolved_time",
        },
        history_callback=history_callback,
        after_update_callback=after_update_callback,
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail="; ".join(result.errors) if result.errors else "关闭工单失败",
        )

    try:
        from app.services.service.service_ticket_notifications import (
            send_service_ticket_notification,
        )

        send_service_ticket_notification(db, result.entity, "closed", actor=current_user)
    except Exception as e:
        logger.error(f"发送服务工单关闭通知失败: {e}", exc_info=True)

    try:
        from app.api.v1.endpoints.service.surveys import (
            create_service_ticket_satisfaction_survey,
        )

        create_service_ticket_satisfaction_survey(
            db,
            result.entity,
            current_user=current_user,
        )
    except Exception as e:
        logger.error(f"创建服务工单回访调查失败: {e}", exc_info=True)

    return result.entity

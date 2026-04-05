# -*- coding: utf-8 -*-
"""
异常升级与处理流程跟踪服务
"""
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.production import (
    EscalationLevel,
    ExceptionHandlingFlow,
    FlowStatus,
    ProductionException,
)
from app.models.user import User
from app.schemas.production.exception_enhancement import (
    ExceptionEscalateResponse,
    FlowTrackingResponse,
)
from app.utils.db_helpers import get_or_404


class EscalationService:
    def __init__(self, db: Session):
        self.db = db

    def escalate_exception(
        self,
        exception_id: int,
        escalation_level: str,
        reason: str,
        escalated_to_id: Optional[int],
    ) -> ExceptionEscalateResponse:
        """异常升级"""
        exception = get_or_404(self.db, ProductionException, exception_id, "异常不存在")

        # 查询或创建处理流程
        flow = (
            self.db.query(ExceptionHandlingFlow)
            .filter(ExceptionHandlingFlow.exception_id == exception_id)
            .first()
        )

        if not flow:
            flow = ExceptionHandlingFlow(
                exception_id=exception_id,
                status=FlowStatus.PENDING,
                pending_at=datetime.now(),
            )
            self.db.add(flow)

        # 升级逻辑
        escalation_level_map = {
            "LEVEL_1": EscalationLevel.LEVEL_1,
            "LEVEL_2": EscalationLevel.LEVEL_2,
            "LEVEL_3": EscalationLevel.LEVEL_3,
        }

        flow.escalation_level = escalation_level_map.get(escalation_level, EscalationLevel.LEVEL_1)
        flow.escalation_reason = reason
        flow.escalated_at = datetime.now()
        flow.escalated_to_id = escalated_to_id

        # 更新异常状态
        if exception.status == "REPORTED":
            exception.status = "PROCESSING"
            exception.handler_id = escalated_to_id
            flow.status = FlowStatus.PROCESSING
            flow.processing_at = datetime.now()

        self.db.commit()
        self.db.refresh(flow)

        # 构造响应
        escalated_to_name = None
        if flow.escalated_to_id:
            escalated_to = self.db.query(User).filter(User.id == flow.escalated_to_id).first()
            if escalated_to:
                escalated_to_name = escalated_to.username

        return ExceptionEscalateResponse(
            id=flow.id,
            exception_id=flow.exception_id,
            status=flow.status.value,
            escalation_level=flow.escalation_level.value,
            escalation_reason=flow.escalation_reason,
            escalated_at=flow.escalated_at,
            escalated_to_id=flow.escalated_to_id,
            escalated_to_name=escalated_to_name,
            created_at=flow.created_at,
            updated_at=flow.updated_at,
        )

    def get_exception_flow(self, exception_id: int) -> FlowTrackingResponse:
        """获取异常处理流程跟踪"""
        flow = (
            self.db.query(ExceptionHandlingFlow)
            .options(
                joinedload(ExceptionHandlingFlow.exception),
                joinedload(ExceptionHandlingFlow.escalated_to),
                joinedload(ExceptionHandlingFlow.verifier),
            )
            .filter(ExceptionHandlingFlow.exception_id == exception_id)
            .first()
        )

        if not flow:
            raise HTTPException(status_code=404, detail="未找到处理流程")

        # 计算处理时长
        self.calculate_flow_duration(flow)
        self.db.commit()
        self.db.refresh(flow)

        return FlowTrackingResponse(
            id=flow.id,
            exception_id=flow.exception_id,
            exception_no=flow.exception.exception_no if flow.exception else None,
            exception_title=flow.exception.title if flow.exception else None,
            status=flow.status.value,
            escalation_level=flow.escalation_level.value,
            escalation_reason=flow.escalation_reason,
            escalated_at=flow.escalated_at,
            escalated_to_name=flow.escalated_to.username if flow.escalated_to else None,
            pending_duration_minutes=flow.pending_duration_minutes,
            processing_duration_minutes=flow.processing_duration_minutes,
            total_duration_minutes=flow.total_duration_minutes,
            pending_at=flow.pending_at,
            processing_at=flow.processing_at,
            resolved_at=flow.resolved_at,
            verified_at=flow.verified_at,
            closed_at=flow.closed_at,
            verifier_name=flow.verifier.username if flow.verifier else None,
            verify_result=flow.verify_result,
            verify_comment=flow.verify_comment,
            created_at=flow.created_at,
            updated_at=flow.updated_at,
        )

    def calculate_flow_duration(self, flow: ExceptionHandlingFlow):
        """计算流程时长"""
        now = datetime.now()

        # 待处理时长
        if flow.pending_at:
            end_time = flow.processing_at or now
            flow.pending_duration_minutes = int((end_time - flow.pending_at).total_seconds() / 60)

        # 处理中时长
        if flow.processing_at:
            end_time = flow.resolved_at or now
            flow.processing_duration_minutes = int(
                (end_time - flow.processing_at).total_seconds() / 60
            )

        # 总时长
        if flow.pending_at:
            end_time = flow.closed_at or now
            flow.total_duration_minutes = int((end_time - flow.pending_at).total_seconds() / 60)

# -*- coding: utf-8 -*-
"""
异常事件管理服务
"""

import logging
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.common.pagination import get_pagination_params
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.models.alert import (
    ExceptionAction,
    ExceptionEscalation,
    ExceptionEvent,
)
from app.models.issue import Issue
from app.models.user import User
from app.schemas.alert import (
    ExceptionEventCreate,
    ExceptionEventResolve,
    ExceptionEventResponse,
    ExceptionEventUpdate,
    ExceptionEventVerify,
)
from app.schemas.common import PaginatedResponse


logger = logging.getLogger(__name__)


class ExceptionEventsService:
    """异常事件管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_exception_events(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        event_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        project_id: Optional[int] = None
    ) -> PaginatedResponse:
        """获取异常事件列表"""
        query = self.db.query(ExceptionEvent).options(
            joinedload(ExceptionEvent.project),
            joinedload(ExceptionEvent.reported_by_user),
            joinedload(ExceptionEvent.assigned_user),
            joinedload(ExceptionEvent.resolved_by_user)
        )

        # 搜索条件
        query = apply_keyword_filter(
            query,
            ExceptionEvent,
            keyword,
            ["title", "description"],
        )

        # 筛选条件
        if severity:
            query = query.filter(ExceptionEvent.severity == severity)

        if status:
            query = query.filter(ExceptionEvent.status == status)

        if event_type:
            query = query.filter(ExceptionEvent.event_type == event_type)

        if start_date:
            query = query.filter(ExceptionEvent.occurred_at >= start_date)

        if end_date:
            query = query.filter(ExceptionEvent.occurred_at <= end_date)

        if project_id:
            query = query.filter(ExceptionEvent.project_id == project_id)

        # 按发生时间倒序
        query = query.order_by(ExceptionEvent.occurred_at.desc())

        # 分页
        pagination = get_pagination_params(page=page, page_size=page_size)
        total = query.count()
        query = apply_pagination(query, pagination.offset, pagination.limit)
        items = query.all()

        return PaginatedResponse(
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pagination.pages_for_total(total),
            items=[ExceptionEventResponse.model_validate(item) for item in items]
        )

    def get_exception_event(self, event_id: int) -> Optional[ExceptionEvent]:
        """获取单个异常事件"""
        return self.db.query(ExceptionEvent).options(
            joinedload(ExceptionEvent.project),
            joinedload(ExceptionEvent.reported_by_user),
            joinedload(ExceptionEvent.assigned_user),
            joinedload(ExceptionEvent.resolved_by_user),
            joinedload(ExceptionEvent.actions),
            joinedload(ExceptionEvent.escalations)
        ).filter(ExceptionEvent.id == event_id).first()

    def create_exception_event(
        self,
        event_data: ExceptionEventCreate,
        current_user: User
    ) -> ExceptionEvent:
        """创建异常事件"""
        exception_event = ExceptionEvent(
            title=event_data.title,
            description=event_data.description,
            event_type=event_data.event_type,
            severity=event_data.severity,
            project_id=event_data.project_id,
            occurred_at=event_data.occurred_at or datetime.now(timezone.utc),
            location=event_data.location,
            impact_assessment=event_data.impact_assessment,
            immediate_actions=event_data.immediate_actions,
            reported_by=current_user.id,
            status="pending"
        )

        self.db.add(exception_event)
        self.db.commit()
        self.db.refresh(exception_event)

        # 自动分配处理人
        self._auto_assign_handler(exception_event)

        # 发送通知
        self._send_exception_notification(exception_event, "created")

        return exception_event

    def update_exception_event(
        self,
        event_id: int,
        event_data: ExceptionEventUpdate,
        current_user: User
    ) -> Optional[ExceptionEvent]:
        """更新异常事件"""
        exception_event = self.get_exception_event(event_id)
        if not exception_event:
            return None

        # 更新字段
        update_data = event_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field not in ['id', 'reported_by', 'created_at']:
                setattr(exception_event, field, value)

        exception_event.updated_by = current_user.id
        exception_event.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(exception_event)

        return exception_event

    def resolve_exception_event(
        self,
        event_id: int,
        resolve_data: ExceptionEventResolve,
        current_user: User
    ) -> Optional[ExceptionEvent]:
        """解决异常事件"""
        exception_event = self.get_exception_event(event_id)
        if not exception_event:
            return None

        if exception_event.status == "resolved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="异常事件已经解决"
            )

        exception_event.status = "resolved"
        exception_event.resolved_by = current_user.id
        exception_event.resolved_at = datetime.now(timezone.utc)
        exception_event.resolution_method = resolve_data.resolution_method
        exception_event.resolution_note = resolve_data.resolution_note
        exception_event.preventive_measures = resolve_data.preventive_measures
        exception_event.updated_by = current_user.id
        exception_event.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(exception_event)

        # 发送通知
        self._send_exception_notification(exception_event, "resolved")

        return exception_event

    def verify_exception_event(
        self,
        event_id: int,
        verify_data: ExceptionEventVerify,
        current_user: User
    ) -> Optional[ExceptionEvent]:
        """验证异常事件解决方案"""
        exception_event = self.get_exception_event(event_id)
        if not exception_event:
            return None

        if exception_event.status != "resolved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只能验证已解决的异常事件"
            )

        exception_event.status = "verified" if verify_data.is_verified else "reopened"
        exception_event.verified_by = current_user.id
        exception_event.verified_at = datetime.now(timezone.utc)
        exception_event.verification_note = verify_data.verification_note
        exception_event.updated_by = current_user.id
        exception_event.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(exception_event)

        return exception_event

    def add_exception_action(
        self,
        event_id: int,
        action_data: dict,
        current_user: User
    ) -> ExceptionAction:
        """添加异常事件处理动作"""
        exception_action = ExceptionAction(
            event_id=event_id,
            action_type=action_data["action_type"],
            description=action_data["description"],
            assigned_to=action_data.get("assigned_to"),
            deadline=action_data.get("deadline"),
            created_by=current_user.id,
            status="pending"
        )

        self.db.add(exception_action)
        self.db.commit()
        self.db.refresh(exception_action)

        return exception_action

    def escalate_exception_event(
        self,
        event_id: int,
        escalation_data: dict,
        current_user: User
    ) -> ExceptionEvent:
        """升级异常事件"""
        exception_event = self.get_exception_event(event_id)
        if not exception_event:
            return None

        escalation = ExceptionEscalation(
            event_id=event_id,
            escalation_level=escalation_data["escalation_level"],
            escalated_to=escalation_data["escalated_to"],
            escalation_reason=escalation_data["escalation_reason"],
            escalated_by=current_user.id
        )

        self.db.add(escalation)

        # 更新事件状态
        exception_event.status = "escalated"
        exception_event.assigned_to = escalation_data["escalated_to"]
        exception_event.updated_by = current_user.id
        exception_event.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(exception_event)

        # 发送升级通知
        self._send_escalation_notification(exception_event, escalation)

        return exception_event

    def create_exception_from_issue(
        self,
        issue_id: int,
        current_user: User
    ) -> ExceptionEvent:
        """从问题创建异常事件"""
        issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="问题不存在"
            )

        exception_event = ExceptionEvent(
            title=f"【异常】{issue.title}",
            description=issue.description,
            event_type="quality_issue",
            severity=self._determine_exception_severity(issue),
            project_id=issue.project_id,
            occurred_at=datetime.now(timezone.utc),
            reported_by=current_user.id,
            source_issue_id=issue.id,
            status="pending"
        )

        self.db.add(exception_event)
        self.db.commit()
        self.db.refresh(exception_event)

        return exception_event

    def _auto_assign_handler(self, exception_event: ExceptionEvent):
        """自动分配处理人"""
        # 根据异常类型和严重程度自动分配

        # TODO: 完善实现 - 根据 assignment_rules 查找对应角色的用户并分配
        logger.info("自动分配处理人: 暂未实现，需要配置分配规则 (event_id=%s, type=%s)",
                     exception_event.id, exception_event.exception_type)

    def _determine_exception_severity(self, issue: Issue) -> str:
        """根据问题确定异常严重程度"""
        severity_mapping = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low"
        }
        return severity_mapping.get(issue.severity, "medium")

    def _send_exception_notification(self, exception_event: ExceptionEvent, action: str):
        """发送异常事件通知"""
        # TODO: 完善实现 - 集成 NotificationDispatcher 发送通知
        logger.info("发送异常事件通知: 暂未实现 (event_id=%s, action=%s)", exception_event.id, action)

    def _send_escalation_notification(self, exception_event: ExceptionEvent, escalation: ExceptionEscalation):
        """发送升级通知"""
        # TODO: 完善实现 - 集成 NotificationDispatcher 发送升级通知
        logger.info("发送升级通知: 暂未实现 (event_id=%s, escalation_id=%s)", exception_event.id, escalation.id)

    # ------------------------------------------------------------------
    # 简化别名方法（向后兼容）
    # ------------------------------------------------------------------

    def create_event(self, event_data, current_user=None):
        """create_exception_event 的别名"""
        if current_user is not None:
            return self.create_exception_event(event_data, current_user)
        # 简化模式：event_data 包含所有信息
        return self.create_exception_event(event_data, event_data)

    def get_event(self, event_id: int):
        """get_exception_event 的别名"""
        return self.get_exception_event(event_id)

    def list_events(self, page: int = 1, page_size: int = 20, **kwargs):
        """get_exception_events 的别名"""
        return self.get_exception_events(page=page, page_size=page_size, **kwargs)

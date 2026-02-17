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
from app.utils.db_helpers import save_obj


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

        save_obj(self.db, exception_event)

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

        save_obj(self.db, exception_action)

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

        save_obj(self.db, exception_event)

        return exception_event

    def _auto_assign_handler(self, exception_event: ExceptionEvent):
        """自动分配处理人

        分配策略（按优先级）：
        1. 如果关联项目有项目经理，分配给项目经理
        2. 如果有责任部门，分配给该部门负责人
        3. 严重程度为 critical 时，额外升级通知
        """
        try:
            assigned = False

            # 策略1: 项目经理
            if exception_event.project_id and exception_event.project:
                pm_id = getattr(exception_event.project, 'pm_id', None)
                if pm_id:
                    exception_event.responsible_user_id = pm_id
                    exception_event.status = "ASSIGNED"
                    self.db.commit()
                    self.db.refresh(exception_event)
                    assigned = True
                    logger.info("异常事件已自动分配给项目经理 (event_id=%s, pm_id=%s)",
                                exception_event.id, pm_id)

            # 策略2: 按部门查找负责人
            if not assigned and exception_event.responsible_dept:
                dept_user = self.db.query(User).filter(
                    User.department == exception_event.responsible_dept,
                    User.is_active == True,
                    User.position.in_(["部门经理", "主管", "负责人", "manager"])
                ).first()
                if dept_user:
                    exception_event.responsible_user_id = dept_user.id
                    exception_event.status = "ASSIGNED"
                    self.db.commit()
                    self.db.refresh(exception_event)
                    assigned = True
                    logger.info("异常事件已自动分配给部门负责人 (event_id=%s, user_id=%s, dept=%s)",
                                exception_event.id, dept_user.id, exception_event.responsible_dept)

            if not assigned:
                logger.warning("异常事件未能自动分配处理人 (event_id=%s, type=%s, severity=%s)",
                               exception_event.id, exception_event.event_type, exception_event.severity)

        except Exception as e:
            logger.error("自动分配处理人失败 (event_id=%s): %s", exception_event.id, str(e))

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
        try:
            from app.services.unified_notification_service import get_notification_service
            from app.services.channel_handlers.base import NotificationRequest

            notification_service = get_notification_service(self.db)

            action_labels = {
                "created": "新建",
                "resolved": "已解决",
                "escalated": "已升级",
                "verified": "已验证",
            }
            action_label = action_labels.get(action, action)

            title = f"异常事件{action_label}: {exception_event.event_title or exception_event.title}"
            content = (
                f"异常编号: {getattr(exception_event, 'event_no', 'N/A')}\n"
                f"类型: {exception_event.event_type}\n"
                f"严重程度: {exception_event.severity}\n"
                f"状态: {exception_event.status}\n"
                f"描述: {getattr(exception_event, 'event_description', '') or getattr(exception_event, 'description', '')}"
            )

            # 通知责任人
            recipient_ids = set()
            if getattr(exception_event, 'responsible_user_id', None):
                recipient_ids.add(exception_event.responsible_user_id)
            if getattr(exception_event, 'reported_by', None):
                recipient_ids.add(exception_event.reported_by)
            if getattr(exception_event, 'created_by', None):
                recipient_ids.add(exception_event.created_by)

            for recipient_id in recipient_ids:
                if not recipient_id:
                    continue
                request = NotificationRequest()
                request.recipient_id = recipient_id
                request.notification_type = "exception_event"
                request.category = "alert"
                request.title = title
                request.content = content
                request.priority = "HIGH" if exception_event.severity in ("critical", "high") else "NORMAL"
                request.source_type = "exception_event"
                request.source_id = exception_event.id
                notification_service.send_notification(request)

            logger.info("异常事件通知已发送 (event_id=%s, action=%s, recipients=%s)",
                        exception_event.id, action, recipient_ids)
        except Exception as e:
            logger.error("发送异常事件通知失败 (event_id=%s, action=%s): %s",
                         exception_event.id, action, str(e))

    def _send_escalation_notification(self, exception_event: ExceptionEvent, escalation: ExceptionEscalation):
        """发送升级通知"""
        try:
            from app.services.unified_notification_service import get_notification_service
            from app.services.channel_handlers.base import NotificationRequest

            notification_service = get_notification_service(self.db)

            title = f"异常事件升级通知: {exception_event.event_title or getattr(exception_event, 'title', '')}"
            content = (
                f"异常编号: {getattr(exception_event, 'event_no', 'N/A')}\n"
                f"升级级别: {escalation.escalation_level}\n"
                f"升级原因: {escalation.escalation_reason}\n"
                f"严重程度: {exception_event.severity}\n"
                f"描述: {getattr(exception_event, 'event_description', '') or getattr(exception_event, 'description', '')}"
            )

            # 通知被升级的处理人
            if escalation.escalated_to:
                request = NotificationRequest()
                request.recipient_id = escalation.escalated_to
                request.notification_type = "exception_escalation"
                request.category = "alert"
                request.title = title
                request.content = content
                request.priority = "HIGH"
                request.source_type = "exception_event"
                request.source_id = exception_event.id
                request.force_send = True  # 升级通知强制发送
                notification_service.send_notification(request)

            logger.info("升级通知已发送 (event_id=%s, escalation_id=%s, escalated_to=%s)",
                        exception_event.id, escalation.id, escalation.escalated_to)
        except Exception as e:
            logger.error("发送升级通知失败 (event_id=%s): %s", exception_event.id, str(e))

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

# -*- coding: utf-8 -*-
"""
告警记录管理服务
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.alert import (
    AlertNotification,
    AlertRecord,
    AlertRule,
    AlertRuleTemplate,
    AlertStatistics,
    AlertSubscription,
    ExceptionAction,
    ExceptionEscalation,
    ExceptionEvent,
    ProjectHealthSnapshot,
)
from app.models.issue import Issue
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.alert import (
    AlertRecordHandle,
    AlertRecordListResponse,
    AlertRecordResponse,
    AlertRuleCreate,
    AlertRuleResponse,
    AlertRuleUpdate,
    AlertStatisticsResponse,
    AlertSubscriptionCreate,
    AlertSubscriptionResponse,
    AlertSubscriptionUpdate,
    ExceptionEventCreate,
    ExceptionEventListResponse,
    ExceptionEventResolve,
    ExceptionEventResponse,
    ExceptionEventUpdate,
    ExceptionEventVerify,
    ProjectHealthResponse,
)
from app.schemas.common import PaginatedResponse, ResponseModel


class AlertRecordsService:
    """告警记录管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_alert_records(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        rule_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        project_id: Optional[int] = None
    ) -> PaginatedResponse:
        """获取告警记录列表"""
        query = self.db.query(AlertRecord).options(
            joinedload(AlertRecord.rule),
            joinedload(AlertRecord.project),
            joinedload(AlertRecord.assigned_user)
        )

        # 搜索条件
        if keyword:
            query = query.filter(
                or_(
                    AlertRecord.title.ilike(f"%{keyword}%"),
                    AlertRecord.description.ilike(f"%{keyword}%")
                )
            )

        # 筛选条件
        if severity:
            query = query.filter(AlertRecord.severity == severity)

        if status:
            query = query.filter(AlertRecord.status == status)

        if rule_type:
            query = query.join(AlertRule).filter(AlertRule.rule_type == rule_type)

        if start_date:
            query = query.filter(AlertRecord.created_at >= start_date)

        if end_date:
            query = query.filter(AlertRecord.created_at <= end_date)

        if project_id:
            query = query.filter(AlertRecord.project_id == project_id)

        # 按创建时间倒序
        query = query.order_by(AlertRecord.created_at.desc())

        # 分页
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[AlertRecordResponse.from_orm(item) for item in items]
        )

    def get_alert_record(self, alert_id: int) -> Optional[AlertRecord]:
        """获取单个告警记录"""
        return self.db.query(AlertRecord).options(
            joinedload(AlertRecord.rule),
            joinedload(AlertRecord.project),
            joinedload(AlertRecord.assigned_user),
            joinedload(AlertRecord.handled_by_user)
        ).filter(AlertRecord.id == alert_id).first()

    def acknowledge_alert(
        self,
        alert_id: int,
        handle_data: AlertRecordHandle,
        current_user: User
    ) -> Optional[AlertRecord]:
        """确认告警"""
        alert_record = self.get_alert_record(alert_id)
        if not alert_record:
            return None

        if alert_record.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只能确认待处理状态的告警"
            )

        alert_record.status = "acknowledged"
        alert_record.acknowledged_by = current_user.id
        alert_record.acknowledged_at = datetime.now(timezone.utc)
        alert_record.acknowledgment_note = handle_data.note
        alert_record.updated_by = current_user.id
        alert_record.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(alert_record)

        # 发送通知
        self._send_alert_notification(alert_record, "acknowledged")

        return alert_record

    def resolve_alert(
        self,
        alert_id: int,
        handle_data: AlertRecordHandle,
        current_user: User
    ) -> Optional[AlertRecord]:
        """解决告警"""
        alert_record = self.get_alert_record(alert_id)
        if not alert_record:
            return None

        if alert_record.status not in ["pending", "acknowledged"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只能解决待处理或已确认状态的告警"
            )

        alert_record.status = "resolved"
        alert_record.resolved_by = current_user.id
        alert_record.resolved_at = datetime.now(timezone.utc)
        alert_record.resolution_note = handle_data.note
        alert_record.updated_by = current_user.id
        alert_record.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(alert_record)

        # 发送通知
        self._send_alert_notification(alert_record, "resolved")

        return alert_record

    def close_alert(
        self,
        alert_id: int,
        handle_data: AlertRecordHandle,
        current_user: User
    ) -> Optional[AlertRecord]:
        """关闭告警"""
        alert_record = self.get_alert_record(alert_id)
        if not alert_record:
            return None

        if alert_record.status == "closed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="告警已经关闭"
            )

        alert_record.status = "closed"
        alert_record.closed_by = current_user.id
        alert_record.closed_at = datetime.now(timezone.utc)
        alert_record.closure_reason = handle_data.note
        alert_record.updated_by = current_user.id
        alert_record.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(alert_record)

        # 发送通知
        self._send_alert_notification(alert_record, "closed")

        return alert_record

    def ignore_alert(
        self,
        alert_id: int,
        handle_data: AlertRecordHandle,
        current_user: User
    ) -> Optional[AlertRecord]:
        """忽略告警"""
        alert_record = self.get_alert_record(alert_id)
        if not alert_record:
            return None

        if alert_record.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只能忽略待处理状态的告警"
            )

        alert_record.status = "ignored"
        alert_record.ignored_by = current_user.id
        alert_record.ignored_at = datetime.now(timezone.utc)
        alert_record.ignore_reason = handle_data.note
        alert_record.updated_by = current_user.id
        alert_record.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(alert_record)

        return alert_record

    def create_alert_from_rule(
        self,
        rule: AlertRule,
        project_id: Optional[int] = None,
        target_id: Optional[int] = None,
        extra_data: Optional[dict] = None
    ) -> AlertRecord:
        """根据规则创建告警"""
        alert_record = AlertRecord(
            rule_id=rule.id,
            project_id=project_id,
            target_id=target_id,
            title=f"【{rule.severity.upper()}】{rule.rule_name}",
            description=rule.description or f"触发预警规则：{rule.rule_name}",
            severity=rule.severity,
            status="pending",
            condition_data=extra_data,
            created_by=1  # 系统自动创建
        )

        # 分配给规则指定的处理人
        if rule.notification_config and rule.notification_config.get("assignee_id"):
            alert_record.assigned_to = rule.notification_config["assignee_id"]

        self.db.add(alert_record)
        self.db.commit()
        self.db.refresh(alert_record)

        # 发送通知
        self._send_alert_notification(alert_record, "created")

        return alert_record

    def _send_alert_notification(self, alert_record: AlertRecord, action: str):
        """发送告警通知"""
        # 这里可以集成邮件、短信、钉钉等通知方式
        notification = AlertNotification(
            alert_id=alert_record.id,
            notification_type="system",
            title=f"告警{action}通知",
            content=f"告警「{alert_record.title}」已{action}",
            is_read=False,
            created_at=datetime.now(timezone.utc)
        )

        self.db.add(notification)
        self.db.commit()

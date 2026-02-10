# -*- coding: utf-8 -*-
"""
告警记录管理服务
"""

import logging
from types import SimpleNamespace

from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.alert import (
    AlertRecord,
    AlertRule,
)
from app.models.user import User
from app.schemas.alert import (
    AlertRecordHandle,
    AlertRecordResponse,
)
from app.schemas.common import PaginatedResponse


class AlertRecordsService:
    """告警记录管理服务"""

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)

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
            joinedload(AlertRecord.project)
        )

        # 搜索条件
        if keyword:
            query = query.filter(
                or_(
                    AlertRecord.alert_title.ilike(f"%{keyword}%"),
                    AlertRecord.alert_content.ilike(f"%{keyword}%")
                )
            )

        # 筛选条件
        if severity:
            query = query.filter(AlertRecord.alert_level == severity)

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
            items=[AlertRecordResponse.model_validate(item) for item in items]
        )

    def get_alert_record(self, alert_id: int) -> Optional[AlertRecord]:
        """获取单个告警记录"""
        return self.db.query(AlertRecord).options(
            joinedload(AlertRecord.rule),
            joinedload(AlertRecord.project),
            joinedload(AlertRecord.machine)
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
        handle_data: Any = None,
        current_user: Any = None,
        closer_id: Optional[int] = None,
    ) -> Optional[AlertRecord]:
        """关闭告警（兼容两种调用方式）"""
        # 兼容两种查询方式
        if closer_id is not None:
            alert_record = self.db.query(AlertRecord).filter(
                AlertRecord.id == alert_id
            ).first()
        else:
            alert_record = self.get_alert_record(alert_id)
        if not alert_record:
            return None

        if alert_record.status == "closed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="告警已经关闭"
            )

        # 兼容 closer_id 和 current_user 两种方式
        user_id = closer_id or (current_user.id if current_user and hasattr(current_user, 'id') else None)

        alert_record.status = "closed"
        alert_record.closed_by = user_id
        alert_record.closed_at = datetime.now(timezone.utc)
        if handle_data and hasattr(handle_data, 'note'):
            alert_record.closure_reason = handle_data.note
        elif handle_data and hasattr(handle_data, 'resolution'):
            alert_record.closure_reason = handle_data.resolution
        if user_id:
            alert_record.updated_by = user_id
        alert_record.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(alert_record)

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
        target_data = dict(extra_data or {})
        if project_id is not None:
            target_data.setdefault("project_id", project_id)
        if target_id is not None:
            target_data.setdefault("target_id", target_id)

        resolved_target_id = (
            target_data.get("target_id")
            if target_data.get("target_id") is not None
            else project_id
        )
        if resolved_target_id is None:
            resolved_target_id = 0

        target_type = target_data.get("target_type")
        if not target_type:
            target_type = "PROJECT" if project_id is not None else "UNKNOWN"
            target_data["target_type"] = target_type

        alert_level = (
            getattr(rule, "alert_level", None)
            or getattr(rule, "severity", None)
            or "WARNING"
        )
        rule_name = getattr(rule, "rule_name", None) or "预警规则"
        alert_title = f"【{str(alert_level).upper()}】{rule_name}"
        alert_content = (
            getattr(rule, "description", None)
            or f"触发预警规则：{rule_name}"
        )

        alert_no = None
        if getattr(rule, "rule_code", None):
            try:
                from app.services.alert_rule_engine.alert_generator import AlertGenerator

                alert_no = AlertGenerator.generate_alert_no(self.db, rule, target_data)
            except Exception:
                alert_no = None
        if not alert_no:
            alert_no = f"ALT{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        alert_record = AlertRecord(
            alert_no=alert_no,
            rule_id=rule.id,
            target_type=target_type,
            target_id=resolved_target_id,
            target_no=target_data.get("target_no"),
            target_name=target_data.get("target_name"),
            project_id=project_id,
            alert_level=alert_level,
            alert_title=alert_title,
            alert_content=alert_content,
            alert_data=target_data,
            status="PENDING",
            triggered_at=datetime.now(timezone.utc),
        )

        # 分配给规则指定的处理人
        if getattr(rule, "notification_config", None) and rule.notification_config.get("assignee_id"):
            alert_record.handler_id = rule.notification_config["assignee_id"]

        self.db.add(alert_record)
        self.db.commit()
        self.db.refresh(alert_record)

        # 发送通知
        self._send_alert_notification(alert_record, "created")

        return alert_record

    # ---- 兼容别名方法（测试中使用的简化接口） ----

    def create_alert(self, data: Any) -> AlertRecord:
        """创建告警记录（简化接口）"""
        alert_no = f"ALT{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        alert_record = AlertRecord(
            alert_no=alert_no,
            rule_id=getattr(data, 'rule_id', None),
            project_id=getattr(data, 'project_id', None),
            alert_level=getattr(data, 'severity', None) or getattr(data, 'alert_level', 'WARNING'),
            alert_title=getattr(data, 'title', None) or getattr(data, 'alert_title', '告警'),
            alert_content=getattr(data, 'content', None) or getattr(data, 'alert_content', ''),
            status='PENDING',
            target_type=getattr(data, 'target_type', 'PROJECT'),
            target_id=getattr(data, 'target_id', None) or getattr(data, 'project_id', 0) or 0,
            triggered_at=datetime.now(timezone.utc),
        )

        self.db.add(alert_record)
        self.db.commit()
        self.db.refresh(alert_record)
        return alert_record

    def get_alert(self, alert_id: int) -> Optional[AlertRecord]:
        """获取单个告警记录（别名）"""
        return self.db.query(AlertRecord).filter(
            AlertRecord.id == alert_id
        ).first()

    def list_alerts(
        self,
        page: int = 1,
        page_size: int = 20,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        handler_id: Optional[int] = None,
        **kwargs: Any,
    ) -> dict:
        """获取告警列表（简化接口）"""
        query = self.db.query(AlertRecord)

        if project_id:
            query = query.filter(AlertRecord.project_id == project_id)
        if status:
            query = query.filter(AlertRecord.status == status)
        if severity:
            query = query.filter(AlertRecord.alert_level == severity)
        if handler_id:
            query = query.filter(AlertRecord.handler_id == handler_id)

        query = query.order_by(AlertRecord.created_at.desc())

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def handle_alert(
        self,
        alert_id: int,
        handle_data: Any,
        handler_id: Optional[int] = None,
    ) -> Optional[AlertRecord]:
        """处理告警（别名）"""
        alert_record = self.db.query(AlertRecord).filter(
            AlertRecord.id == alert_id
        ).first()
        if not alert_record:
            return None

        alert_record.status = "HANDLING"
        alert_record.handler_id = handler_id
        alert_record.handled_at = datetime.now(timezone.utc)
        if hasattr(handle_data, 'comment'):
            alert_record.acknowledgment_note = handle_data.comment

        self.db.commit()
        self.db.refresh(alert_record)
        return alert_record

    def escalate_alert(
        self,
        alert_id: int,
        escalate_data: Any,
        escalator_id: Optional[int] = None,
    ) -> Optional[AlertRecord]:
        """升级告警"""
        alert_record = self.db.query(AlertRecord).filter(
            AlertRecord.id == alert_id
        ).first()
        if not alert_record:
            return None

        if hasattr(escalate_data, 'target_severity') and escalate_data.target_severity:
            alert_record.alert_level = escalate_data.target_severity
            if hasattr(alert_record, 'severity'):
                alert_record.severity = escalate_data.target_severity

        escalation_count = getattr(alert_record, 'escalation_count', 0) or 0
        alert_record.escalation_count = escalation_count + 1

        alert_record.escalated_by = escalator_id
        alert_record.escalated_at = datetime.now(timezone.utc)
        if hasattr(escalate_data, 'reason'):
            alert_record.escalation_reason = escalate_data.reason

        self.db.commit()
        self.db.refresh(alert_record)
        return alert_record

    def _send_alert_notification(self, alert_record: AlertRecord, action: str):
        """发送告警通知"""
        from app.services.notification_service import AlertNotificationService

        recipient_ids = []
        for attr in ("assigned_to", "handler_id", "acknowledged_by", "created_by", "updated_by", "assignee_id"):
            value = getattr(alert_record, attr, None)
            if value:
                recipient_ids.append(value)

        recipient_ids = list(dict.fromkeys(recipient_ids))
        if not recipient_ids:
            self.logger.warning("告警通知未发送：未找到接收人")
            return False

        title = (
            getattr(alert_record, "alert_title", None)
            or getattr(alert_record, "title", None)
            or "告警通知"
        )
        content = f"告警「{title}」已{action}"
        alert_payload = SimpleNamespace(
            id=getattr(alert_record, "id", None),
            alert_title=title,
            alert_content=content,
            alert_level=getattr(alert_record, "alert_level", None)
            or getattr(alert_record, "severity", None),
            alert_no=getattr(alert_record, "alert_no", None),
            target_type=getattr(alert_record, "target_type", None),
            target_name=getattr(alert_record, "target_name", None),
        )

        service = AlertNotificationService(self.db)
        return service.send_alert_notification(
            alert=alert_payload,
            user_ids=recipient_ids,
            channels=["SYSTEM"],
            force_send=True,
        )

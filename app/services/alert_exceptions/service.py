# -*- coding: utf-8 -*-
"""
Alert Exceptions Service - 异常告警业务逻辑层
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.alert import (
    ExceptionAction,
    ExceptionEscalation,
    ExceptionEvent,
)
from app.models.issue import Issue
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.alert import ExceptionEventCreate
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.utils.db_helpers import get_or_404


class AlertExceptionsService:
    """异常告警服务类"""

    def __init__(self, db: Session):
        """初始化服务"""
        self.db = db

    def get_exception_events(
        self,
        offset: int,
        limit: int,
        keyword: Optional[str] = None,
        project_id: Optional[int] = None,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        responsible_user_id: Optional[int] = None,
    ) -> Tuple[List[ExceptionEvent], int]:
        """
        获取异常事件列表（支持分页和筛选）

        Args:
            offset: 分页偏移量
            limit: 每页数量
            keyword: 关键词搜索
            project_id: 项目ID筛选
            event_type: 异常类型筛选
            severity: 严重程度筛选
            status: 状态筛选
            responsible_user_id: 责任人ID筛选

        Returns:
            (事件列表, 总数)
        """
        query = self.db.query(ExceptionEvent)

        # 关键词搜索
        query = apply_keyword_filter(query, ExceptionEvent, keyword, ["event_no", "event_title"])

        # 项目筛选
        if project_id:
            query = query.filter(ExceptionEvent.project_id == project_id)

        # 异常类型筛选
        if event_type:
            query = query.filter(ExceptionEvent.event_type == event_type)

        # 严重程度筛选
        if severity:
            query = query.filter(ExceptionEvent.severity == severity)

        # 状态筛选
        if status:
            query = query.filter(ExceptionEvent.status == status)

        # 责任人筛选
        if responsible_user_id:
            query = query.filter(ExceptionEvent.responsible_user_id == responsible_user_id)

        # 计算总数
        total = query.count()

        # 分页
        events = apply_pagination(
            query.order_by(ExceptionEvent.created_at.desc()), offset, limit
        ).all()

        return events, total

    def build_event_list_item(self, event: ExceptionEvent) -> Dict[str, Any]:
        """
        构建事件列表项数据

        Args:
            event: 异常事件对象

        Returns:
            事件列表项字典
        """
        discovered_by_name = None
        if event.discovered_by:
            user = self.db.query(User).filter(User.id == event.discovered_by).first()
            discovered_by_name = user.real_name if user else None

        return {
            "id": event.id,
            "event_no": event.event_no,
            "source_type": event.source_type,
            "project_id": event.project_id,
            "project_name": event.project.project_name if event.project else None,
            "machine_id": event.machine_id,
            "machine_name": event.machine.machine_name if event.machine else None,
            "event_type": event.event_type,
            "severity": event.severity,
            "event_title": event.event_title,
            "status": event.status,
            "discovered_at": event.discovered_at.isoformat() if event.discovered_at else None,
            "discovered_by_name": discovered_by_name,
            "schedule_impact": event.schedule_impact or 0,
            "cost_impact": float(event.cost_impact) if event.cost_impact else 0,
            "responsible_user_id": event.responsible_user_id,
            "due_date": event.due_date.isoformat() if event.due_date else None,
            "is_overdue": event.is_overdue or False,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }

    def create_exception_event(
        self,
        event_in: ExceptionEventCreate,
        current_user_id: int,
        event_no: str,
    ) -> ExceptionEvent:
        """
        创建异常事件

        Args:
            event_in: 异常事件创建数据
            current_user_id: 当前用户ID
            event_no: 异常编号

        Returns:
            创建的异常事件对象

        Raises:
            ValueError: 项目或设备不存在
        """
        # 验证项目
        if event_in.project_id:
            project = self.db.query(Project).filter(Project.id == event_in.project_id).first()
            if not project:
                raise ValueError("项目不存在")

        # 验证设备
        if event_in.machine_id:
            machine = self.db.query(Machine).filter(Machine.id == event_in.machine_id).first()
            if not machine:
                raise ValueError("设备不存在")

        # 创建异常事件
        event = ExceptionEvent(
            event_no=event_no,
            source_type=event_in.source_type,
            source_id=event_in.source_id,
            alert_id=event_in.alert_id,
            project_id=event_in.project_id,
            machine_id=event_in.machine_id,
            event_type=event_in.event_type,
            severity=event_in.severity,
            event_title=event_in.event_title,
            event_description=event_in.event_description,
            discovered_at=datetime.now(),
            discovered_by=current_user_id,
            discovery_location=event_in.discovery_location,
            impact_scope=event_in.impact_scope,
            impact_description=event_in.impact_description,
            schedule_impact=event_in.schedule_impact,
            cost_impact=event_in.cost_impact or 0,
            responsible_dept=event_in.responsible_dept,
            responsible_user_id=event_in.responsible_user_id,
            due_date=event_in.due_date,
            status="OPEN",
            attachments=event_in.attachments,
            created_by=current_user_id,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event

    def get_exception_event_detail(self, event_id: int) -> Dict[str, Any]:
        """
        获取异常事件详情

        Args:
            event_id: 事件ID

        Returns:
            事件详情字典
        """
        event = get_or_404(self.db, ExceptionEvent, event_id, "异常事件不存在")

        # 获取发现人姓名
        discovered_by_name = None
        if event.discovered_by:
            user = self.db.query(User).filter(User.id == event.discovered_by).first()
            discovered_by_name = user.real_name if user else None

        # 获取处理记录
        actions = event.actions.order_by(ExceptionAction.created_at.desc()).all()
        action_list = []
        for action in actions:
            action_user = self.db.query(User).filter(User.id == action.created_by).first()
            action_list.append({
                "id": action.id,
                "action_type": action.action_type,
                "action_content": action.action_content,
                "old_status": action.old_status,
                "new_status": action.new_status,
                "action_user_id": action.created_by,
                "action_user_name": action_user.real_name if action_user else None,
                "created_at": action.created_at.isoformat() if action.created_at else None,
            })

        return {
            "id": event.id,
            "event_no": event.event_no,
            "source_type": event.source_type,
            "alert_id": event.alert_id,
            "project_id": event.project_id,
            "project_name": event.project.project_name if event.project else None,
            "machine_id": event.machine_id,
            "machine_name": event.machine.machine_name if event.machine else None,
            "event_type": event.event_type,
            "severity": event.severity,
            "event_title": event.event_title,
            "event_description": event.event_description,
            "discovered_at": event.discovered_at,
            "discovered_by": event.discovered_by,
            "discovered_by_name": discovered_by_name,
            "discovery_location": event.discovery_location,
            "impact_scope": event.impact_scope,
            "impact_description": event.impact_description,
            "schedule_impact": event.schedule_impact or 0,
            "cost_impact": event.cost_impact or 0,
            "status": event.status,
            "responsible_dept": event.responsible_dept,
            "responsible_user_id": event.responsible_user_id,
            "due_date": event.due_date,
            "is_overdue": event.is_overdue or False,
            "root_cause": event.root_cause,
            "cause_category": event.cause_category,
            "solution": event.solution,
            "preventive_measures": event.preventive_measures,
            "resolved_at": event.resolved_at,
            "resolved_by": event.resolved_by,
            "resolution_note": event.resolution_note,
            "verified_at": event.verified_at,
            "verified_by": event.verified_by,
            "verification_result": event.verification_result,
            "attachments": event.attachments,
            "actions": action_list,
            "created_at": event.created_at,
            "updated_at": event.updated_at,
        }

    def update_exception_status(
        self, event_id: int, new_status: str, current_user_id: int
    ) -> ExceptionEvent:
        """
        更新异常状态

        Args:
            event_id: 事件ID
            new_status: 新状态
            current_user_id: 当前用户ID

        Returns:
            更新后的事件对象
        """
        event = get_or_404(self.db, ExceptionEvent, event_id, "异常事件不存在")

        event.status = new_status

        # 如果状态为RESOLVED，记录解决时间
        if new_status == "RESOLVED" and not event.resolved_at:
            event.resolved_at = datetime.now()
            event.resolved_by = current_user_id

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event

    def add_exception_action(
        self,
        event_id: int,
        action_type: str,
        action_content: str,
        current_user_id: int,
    ) -> ExceptionAction:
        """
        添加处理记录

        Args:
            event_id: 事件ID
            action_type: 操作类型
            action_content: 操作内容
            current_user_id: 当前用户ID

        Returns:
            创建的操作记录对象
        """
        event = get_or_404(self.db, ExceptionEvent, event_id, "异常事件不存在")

        action = ExceptionAction(
            event_id=event_id,
            action_type=action_type,
            action_content=action_content,
            old_status=event.status,
            new_status=event.status,
            created_by=current_user_id,
        )
        self.db.add(action)
        self.db.commit()

        return action

    def escalate_exception(
        self,
        event_id: int,
        escalate_to_user_id: Optional[int],
        escalate_to_dept: Optional[str],
        escalation_reason: Optional[str],
        current_user_id: int,
    ) -> ExceptionEvent:
        """
        异常升级

        Args:
            event_id: 事件ID
            escalate_to_user_id: 升级到用户ID
            escalate_to_dept: 升级到部门
            escalation_reason: 升级原因
            current_user_id: 当前用户ID

        Returns:
            更新后的事件对象
        """
        event = get_or_404(self.db, ExceptionEvent, event_id, "异常事件不存在")

        # 创建升级记录
        escalation = ExceptionEscalation(
            event_id=event_id,
            escalated_from=current_user_id,
            escalated_to=escalate_to_user_id or current_user_id,  # 如果没有指定，使用当前用户
            escalated_at=datetime.now(),
            escalation_reason=escalation_reason,
            escalation_level=1,  # 升级层级，可以根据实际情况计算
        )
        self.db.add(escalation)

        # 更新责任人
        if escalate_to_user_id:
            event.responsible_user_id = escalate_to_user_id
        if escalate_to_dept:
            event.responsible_dept = escalate_to_dept

        # 如果严重程度不是最高，可以提升严重程度
        if event.severity == "MINOR":
            event.severity = "MAJOR"
        elif event.severity == "MAJOR":
            event.severity = "CRITICAL"

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event

    def create_exception_from_issue(
        self,
        issue_id: int,
        event_type: str,
        severity: str,
        current_user_id: int,
        event_no: str,
    ) -> ExceptionEvent:
        """
        从问题创建异常事件

        Args:
            issue_id: 问题ID
            event_type: 异常类型
            severity: 严重程度
            current_user_id: 当前用户ID
            event_no: 异常编号

        Returns:
            创建的异常事件对象
        """
        issue = get_or_404(self.db, Issue, issue_id, "问题不存在")

        # 创建异常事件
        event = ExceptionEvent(
            event_no=event_no,
            source_type="ISSUE",
            source_id=issue_id,
            project_id=issue.project_id,
            machine_id=issue.machine_id,
            event_type=event_type,
            severity=severity,
            event_title=f"问题转异常：{issue.issue_title}",
            event_description=issue.issue_description or "",
            discovered_at=issue.created_at or datetime.now(),
            discovered_by=issue.reporter_id or current_user_id,
            impact_scope="LOCAL",
            schedule_impact=0,
            cost_impact=0,
            status="OPEN",
            created_by=current_user_id,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event

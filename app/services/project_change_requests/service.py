# -*- coding: utf-8 -*-
"""
项目变更请求服务层
"""

from __future__ import annotations

import logging
import json
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.common.query_filters import apply_pagination
from app.models.approval import (
    ApprovalActionLog,
    ApprovalFlowDefinition,
    ApprovalInstance,
    ApprovalTemplate,
)
from app.models.change_request import (
    ChangeRequest,
)
from app.models.enums import (
    ApprovalDecisionEnum,
    ChangeSourceEnum,
    ChangeStatusEnum,
    ChangeTypeEnum,
)
from app.models.project import Project, ProjectCost, ProjectMilestone
from app.models.user import User
from app.schemas.change_request import (
    ChangeApprovalRequest,
    ChangeCloseRequest,
    ChangeImplementationRequest,
    ChangeRequestCreate,
    ChangeRequestStatistics,
    ChangeRequestUpdate,
    ChangeStatusUpdateRequest,
    ChangeVerificationRequest,
)
from app.services.notification.channels.base import (
    NotificationChannel,
    NotificationPriority,
    NotificationRequest,
)
from app.services.notification.unified_notification_service import get_notification_service
from app.utils.db_helpers import get_or_404, save_obj

logger = logging.getLogger(__name__)

PROJECT_CHANGE_APPROVAL_ENTITY_TYPE = "PROJECT_CHANGE_REQUEST"
PROJECT_CHANGE_APPROVAL_TEMPLATE_CODES = (
    "TPL_PROJECT_CHANGE",
    "PROJECT_CHANGE_REQUEST",
    "TPL_PROJECT",
)
PROJECT_CHANGE_APPROVAL_ACTION_BY_DECISION = {
    ApprovalDecisionEnum.APPROVED: "APPROVE",
    ApprovalDecisionEnum.REJECTED: "REJECT",
    ApprovalDecisionEnum.RETURNED: "RETURN",
}
PROJECT_CHANGE_DECISION_BY_ACTION = {
    "APPROVE": ApprovalDecisionEnum.APPROVED.value,
    "REJECT": ApprovalDecisionEnum.REJECTED.value,
    "RETURN": ApprovalDecisionEnum.RETURNED.value,
}


class ProjectChangeRequestsService:
    """项目变更请求服务"""

    def __init__(self, db: Session):
        self.db = db

    def _has_real_session(self) -> bool:
        return type(self.db).__module__.startswith("sqlalchemy.orm")

    def _approval_operator_name(self, user: User) -> str:
        return user.real_name or user.username

    def _project_change_instance_no(self, change_request_id: int) -> str:
        stamp = datetime.utcnow().strftime("%y%m%d%H%M%S%f")
        return f"PCR{change_request_id}-{stamp}"[:50]

    def _find_project_change_template(self) -> tuple[ApprovalTemplate, ApprovalFlowDefinition] | None:
        templates = (
            self.db.query(ApprovalTemplate)
            .filter(
                ApprovalTemplate.template_code.in_(PROJECT_CHANGE_APPROVAL_TEMPLATE_CODES),
                ApprovalTemplate.is_active,
            )
            .all()
        )
        template_by_code = {template.template_code: template for template in templates}
        template = next(
            (
                template_by_code[code]
                for code in PROJECT_CHANGE_APPROVAL_TEMPLATE_CODES
                if code in template_by_code
            ),
            None,
        )
        if template is None:
            return None

        flow = (
            self.db.query(ApprovalFlowDefinition)
            .filter(
                ApprovalFlowDefinition.template_id == template.id,
                ApprovalFlowDefinition.is_active,
            )
            .order_by(ApprovalFlowDefinition.is_default.desc(), ApprovalFlowDefinition.id)
            .first()
        )
        if flow is None:
            return None
        return template, flow

    def _get_or_create_project_change_approval_instance(
        self,
        change_request: ChangeRequest,
        current_user: User,
    ) -> ApprovalInstance | None:
        if not self._has_real_session():
            instance = ApprovalInstance(
                instance_no=f"MOCK-{PROJECT_CHANGE_APPROVAL_ENTITY_TYPE}-{change_request.id}",
                template_id=0,
                flow_id=0,
                entity_type=PROJECT_CHANGE_APPROVAL_ENTITY_TYPE,
                entity_id=change_request.id,
                initiator_id=change_request.submitter_id or current_user.id,
                initiator_name=change_request.submitter_name or self._approval_operator_name(current_user),
                form_data={"change_request_id": change_request.id},
                status="PENDING",
                title=f"项目变更 {change_request.change_code} 审批",
                summary=change_request.title,
                submitted_at=change_request.submit_date or datetime.utcnow(),
            )
            instance.id = change_request.id
            return instance

        existing = (
            self.db.query(ApprovalInstance)
            .filter(
                ApprovalInstance.entity_type == PROJECT_CHANGE_APPROVAL_ENTITY_TYPE,
                ApprovalInstance.entity_id == change_request.id,
            )
            .order_by(ApprovalInstance.id.desc())
            .first()
        )
        if existing:
            return existing

        template_flow = self._find_project_change_template()
        if template_flow is None:
            logger.warning("项目变更审批模板/流程不存在，无法写入统一审批日志")
            return None

        template, flow = template_flow
        instance = ApprovalInstance(
            tenant_id=change_request.tenant_id,
            instance_no=self._project_change_instance_no(change_request.id),
            template_id=template.id,
            flow_id=flow.id,
            entity_type=PROJECT_CHANGE_APPROVAL_ENTITY_TYPE,
            entity_id=change_request.id,
            initiator_id=change_request.submitter_id or current_user.id,
            initiator_name=change_request.submitter_name or self._approval_operator_name(current_user),
            form_data={
                "source": "project_change_requests",
                "change_request_id": change_request.id,
                "change_code": change_request.change_code,
                "project_id": change_request.project_id,
            },
            status="PENDING",
            title=f"项目变更 {change_request.change_code} 审批",
            summary=change_request.title,
            submitted_at=change_request.submit_date or datetime.utcnow(),
        )
        self.db.add(instance)
        self.db.flush()
        return instance

    def _record_project_change_approval_log(
        self,
        *,
        change_request: ChangeRequest,
        approval_in: ChangeApprovalRequest,
        current_user: User,
        before_status: str,
    ) -> None:
        from app.services.approval_engine.engine import ApprovalEngineService

        instance = self._get_or_create_project_change_approval_instance(change_request, current_user)
        if instance is None:
            return

        action = PROJECT_CHANGE_APPROVAL_ACTION_BY_DECISION[approval_in.decision]
        action_at = change_request.approval_date or datetime.utcnow()
        if approval_in.decision == ApprovalDecisionEnum.APPROVED:
            instance.status = "APPROVED"
            instance.completed_at = action_at
            instance.final_approver_id = current_user.id
            instance.final_comment = approval_in.comments
        elif approval_in.decision == ApprovalDecisionEnum.REJECTED:
            instance.status = "REJECTED"
            instance.completed_at = action_at
            instance.final_approver_id = current_user.id
            instance.final_comment = approval_in.comments
        else:
            instance.status = "PENDING"
            instance.final_comment = approval_in.comments

        ApprovalEngineService(self.db).record_action_log(
            tenant_id=change_request.tenant_id,
            instance_id=instance.id,
            operator_id=current_user.id,
            operator_name=self._approval_operator_name(current_user),
            action=action,
            action_detail={
                "source": "project_change_requests.approve_change_request",
                "change_request_id": change_request.id,
                "change_code": change_request.change_code,
                "decision": approval_in.decision.value,
                "approver_role": "PM",
            },
            comment=approval_in.comments,
            attachments=approval_in.attachments,
            before_status=before_status,
            after_status=change_request.status.value,
            action_at=action_at,
        )

    def _json_dict(self, value) -> dict:
        if isinstance(value, dict):
            return value
        if isinstance(value, str) and value.strip():
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, dict) else {}
            except (TypeError, ValueError):
                return {}
        return {}

    def _send_change_notification(
        self,
        change_request: ChangeRequest,
        *,
        recipient_ids: set[int],
        event: str,
        title: str,
        content: str,
        priority: str = NotificationPriority.NORMAL,
    ) -> None:
        if not self._has_real_session():
            return

        recipients = sorted(recipient_id for recipient_id in recipient_ids if recipient_id)
        if not recipients:
            return

        notification_service = get_notification_service(self.db)
        for recipient_id in recipients:
            request = NotificationRequest(
                recipient_id=recipient_id,
                notification_type=f"PROJECT_CHANGE_{event}",
                category="project",
                title=title,
                content=content,
                priority=priority,
                channels=[NotificationChannel.SYSTEM],
                source_type="project_change_request",
                source_id=change_request.id,
                link_url=f"/projects/{change_request.project_id}/changes/{change_request.id}",
                extra_data={
                    "project_id": change_request.project_id,
                    "change_request_id": change_request.id,
                    "change_code": change_request.change_code,
                    "event": event,
                },
                force_send=True,
            )
            try:
                notification_service.send_notification(request)
            except Exception:
                logger.exception(
                    "项目变更通知发送失败: event=%s change_id=%s recipient_id=%s",
                    event,
                    change_request.id,
                    recipient_id,
                )

    def _project_pm_recipient_ids(self, project_id: int) -> set[int]:
        if not self._has_real_session():
            return set()
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if project and project.pm_id:
            return {project.pm_id}
        return set()

    @staticmethod
    def _decimal(value) -> Decimal:
        if value is None:
            return Decimal("0")
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal("0")

    @staticmethod
    def _impact_details(change_request: ChangeRequest) -> dict:
        if isinstance(change_request.impact_details, dict):
            return dict(change_request.impact_details)
        return {}

    def _change_delay_days(self, change_request: ChangeRequest, impact_details: dict) -> int:
        if change_request.time_impact:
            return int(change_request.time_impact)

        schedule = impact_details.get("schedule")
        if isinstance(schedule, dict):
            return int(schedule.get("delay_days") or 0)

        return 0

    def _change_cost_impact(self, change_request: ChangeRequest, impact_details: dict) -> Decimal:
        explicit_cost = self._decimal(change_request.cost_impact)
        if explicit_cost > 0:
            return explicit_cost

        cost = impact_details.get("cost")
        if isinstance(cost, dict):
            for key in ("total", "additional", "amount"):
                amount = self._decimal(cost.get(key))
                if amount > 0:
                    return amount

        return Decimal("0")

    def _affected_milestone_ids(self, impact_details: dict) -> list[int]:
        schedule = impact_details.get("schedule")
        raw_items = []
        if isinstance(schedule, dict):
            raw_items = schedule.get("affected_milestones") or []
        if not raw_items:
            raw_items = impact_details.get("affected_milestones") or []

        milestone_ids = []
        for item in raw_items:
            if isinstance(item, dict) and item.get("milestone_id"):
                milestone_ids.append(int(item["milestone_id"]))
        return milestone_ids

    def _apply_milestone_delay(
        self,
        change_request: ChangeRequest,
        delay_days: int,
        impact_details: dict,
    ) -> list[dict]:
        if delay_days <= 0:
            return []

        milestone_ids = self._affected_milestone_ids(impact_details)
        if milestone_ids:
            query = self.db.query(ProjectMilestone).filter(
                ProjectMilestone.project_id == change_request.project_id,
                ProjectMilestone.id.in_(milestone_ids),
            )
        else:
            query = self.db.query(ProjectMilestone).filter(
                ProjectMilestone.project_id == change_request.project_id,
                ProjectMilestone.status.in_(["PENDING", "IN_PROGRESS"]),
            )

        updates = []
        for milestone in query.all():
            if not milestone.planned_date:
                continue
            old_date = milestone.planned_date
            milestone.planned_date = old_date + timedelta(days=delay_days)
            self.db.add(milestone)
            updates.append(
                {
                    "milestone_id": milestone.id,
                    "name": milestone.milestone_name,
                    "old_date": old_date.isoformat(),
                    "new_date": milestone.planned_date.isoformat(),
                }
            )
        return updates

    def _record_change_cost(
        self,
        change_request: ChangeRequest,
        amount: Decimal,
        current_user_id: int,
    ) -> tuple[ProjectCost | None, bool]:
        if amount <= 0:
            return None, False

        existing = (
            self.db.query(ProjectCost)
            .filter(
                ProjectCost.project_id == change_request.project_id,
                ProjectCost.source_type == "CHANGE_REQUEST",
                ProjectCost.source_id == change_request.id,
            )
            .first()
        )
        if existing:
            return existing, False

        cost = ProjectCost(
            project_id=change_request.project_id,
            cost_type="CHANGE",
            cost_category="PROJECT_CHANGE",
            cost_basis="ACTUAL",
            source_module="project_change_request",
            source_type="CHANGE_REQUEST",
            source_id=change_request.id,
            source_no=change_request.change_code,
            amount=amount,
            cost_date=date.today(),
            description=f"项目变更成本 - {change_request.change_code}: {change_request.title}",
            created_by=current_user_id,
        )
        self.db.add(cost)
        self.db.flush()
        return cost, True

    def _apply_approved_change_to_project_baseline(
        self,
        change_request: ChangeRequest,
        current_user: User,
    ) -> None:
        if not self._has_real_session():
            return

        impact_details = self._impact_details(change_request)
        baseline_application = impact_details.get("baseline_application")
        if isinstance(baseline_application, dict) and baseline_application.get("applied"):
            return

        project = get_or_404(self.db, Project, change_request.project_id, detail="项目不存在")
        delay_days = self._change_delay_days(change_request, impact_details)
        cost_amount = self._change_cost_impact(change_request, impact_details)

        old_end_date = project.planned_end_date
        if delay_days > 0 and project.planned_end_date:
            project.planned_end_date = project.planned_end_date + timedelta(days=delay_days)
            self.db.add(project)

        milestone_updates = self._apply_milestone_delay(change_request, delay_days, impact_details)

        cost, cost_created = self._record_change_cost(change_request, cost_amount, current_user.id)
        if cost_created and cost:
            project.actual_cost = self._decimal(project.actual_cost) + self._decimal(cost.amount)
            self.db.add(project)

        impact_details["baseline_application"] = {
            "applied": True,
            "applied_at": datetime.utcnow().isoformat(),
            "applied_by": current_user.id,
            "delay_days": delay_days,
            "old_planned_end_date": old_end_date.isoformat() if old_end_date else None,
            "new_planned_end_date": (
                project.planned_end_date.isoformat() if project.planned_end_date else None
            ),
            "milestone_updates": milestone_updates,
            "cost_amount": float(cost_amount),
            "cost_id": cost.id if cost else None,
        }
        change_request.impact_details = impact_details

    def generate_change_code(self, project_id: int) -> str:
        """生成变更编号"""
        # 获取项目编号
        project = get_or_404(self.db, Project, project_id, detail="项目不存在")

        # 获取当前项目的变更数量
        count = (
            self.db.query(func.count(ChangeRequest.id))
            .filter(ChangeRequest.project_id == project_id)
            .scalar()
            or 0
        )

        # 格式: CHG-项目编码-序号 (如: CHG-PRJ001-001)
        return f"CHG-{project.project_code}-{count + 1:03d}"

    def validate_status_transition(
        self, current_status: ChangeStatusEnum, new_status: ChangeStatusEnum
    ) -> bool:
        """验证状态转换是否合法"""
        # 定义状态机转换规则
        valid_transitions = {
            ChangeStatusEnum.SUBMITTED: [ChangeStatusEnum.ASSESSING, ChangeStatusEnum.CANCELLED],
            ChangeStatusEnum.ASSESSING: [
                ChangeStatusEnum.PENDING_APPROVAL,
                ChangeStatusEnum.SUBMITTED,
                ChangeStatusEnum.CANCELLED,
            ],
            ChangeStatusEnum.PENDING_APPROVAL: [
                ChangeStatusEnum.APPROVED,
                ChangeStatusEnum.REJECTED,
                ChangeStatusEnum.ASSESSING,
                ChangeStatusEnum.CANCELLED,
            ],
            ChangeStatusEnum.APPROVED: [ChangeStatusEnum.IMPLEMENTING, ChangeStatusEnum.CANCELLED],
            ChangeStatusEnum.REJECTED: [],  # 已拒绝不能转换到其他状态
            ChangeStatusEnum.IMPLEMENTING: [ChangeStatusEnum.VERIFYING, ChangeStatusEnum.APPROVED],
            ChangeStatusEnum.VERIFYING: [ChangeStatusEnum.CLOSED, ChangeStatusEnum.IMPLEMENTING],
            ChangeStatusEnum.CLOSED: [],  # 已关闭不能转换到其他状态
            ChangeStatusEnum.CANCELLED: [],  # 已取消不能转换到其他状态
        }

        return new_status in valid_transitions.get(current_status, [])

    def create_change_request(
        self, change_in: ChangeRequestCreate, current_user: User
    ) -> ChangeRequest:
        """提交变更请求"""
        # 验证项目是否存在
        get_or_404(self.db, Project, change_in.project_id, detail="项目不存在")

        # 生成变更编号
        change_code = self.generate_change_code(change_in.project_id)

        # 创建变更请求
        change_request = ChangeRequest(
            **change_in.model_dump(exclude={"project_id"}),
            change_code=change_code,
            project_id=change_in.project_id,
            submitter_id=current_user.id,
            submitter_name=current_user.real_name or current_user.username,
            status=ChangeStatusEnum.SUBMITTED,
            approval_decision=ApprovalDecisionEnum.PENDING,
        )

        save_obj(self.db, change_request)

        if change_request.notify_team:
            self._send_change_notification(
                change_request,
                recipient_ids=self._project_pm_recipient_ids(change_request.project_id),
                event="SUBMITTED",
                title="项目变更请求已提交",
                content=f"项目变更 {change_request.change_code} 已提交：{change_request.title}",
                priority=NotificationPriority.HIGH,
            )

        return change_request

    def list_change_requests(
        self,
        offset: int,
        limit: int,
        project_id: Optional[int] = None,
        change_type: Optional[ChangeTypeEnum] = None,
        change_source: Optional[ChangeSourceEnum] = None,
        status: Optional[ChangeStatusEnum] = None,
        submitter_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> List[ChangeRequest]:
        """获取变更请求列表"""
        query = self.db.query(ChangeRequest)

        # 应用过滤条件
        if project_id:
            query = query.filter(ChangeRequest.project_id == project_id)
        if change_type:
            query = query.filter(ChangeRequest.change_type == change_type)
        if change_source:
            query = query.filter(ChangeRequest.change_source == change_source)
        if status:
            query = query.filter(ChangeRequest.status == status)
        if submitter_id:
            query = query.filter(ChangeRequest.submitter_id == submitter_id)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (ChangeRequest.title.like(search_pattern))
                | (ChangeRequest.description.like(search_pattern))
                | (ChangeRequest.change_code.like(search_pattern))
            )

        # 排序和分页
        changes = apply_pagination(
            query.order_by(desc(ChangeRequest.submit_date)), offset, limit
        ).all()

        return changes

    def get_change_request(self, change_id: int) -> ChangeRequest:
        """获取变更请求详情"""
        change_request = get_or_404(self.db, ChangeRequest, change_id, detail="变更请求不存在")
        return change_request

    def update_change_request(
        self,
        change_id: int,
        change_in: ChangeRequestUpdate,
    ) -> ChangeRequest:
        """更新变更请求"""
        change_request = get_or_404(self.db, ChangeRequest, change_id, detail="变更请求不存在")

        # 检查状态：已批准、已拒绝、已关闭的变更不能修改
        if change_request.status in [
            ChangeStatusEnum.APPROVED,
            ChangeStatusEnum.REJECTED,
            ChangeStatusEnum.CLOSED,
            ChangeStatusEnum.CANCELLED,
        ]:
            raise HTTPException(
                status_code=400, detail=f"状态为 {change_request.status.value} 的变更请求不能修改"
            )

        # 更新字段
        update_data = change_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(change_request, field, value)

        save_obj(self.db, change_request)

        return change_request

    def approve_change_request(
        self,
        change_id: int,
        approval_in: ChangeApprovalRequest,
        current_user: User,
    ) -> ChangeRequest:
        """审批变更请求"""
        change_request = get_or_404(self.db, ChangeRequest, change_id, detail="变更请求不存在")

        # 检查状态：只有待审批状态才能审批
        if change_request.status != ChangeStatusEnum.PENDING_APPROVAL:
            raise HTTPException(status_code=400, detail="只有待审批状态的变更请求才能审批")

        before_status = change_request.status.value

        # 更新审批信息
        change_request.approver_id = current_user.id
        change_request.approver_name = current_user.real_name or current_user.username
        change_request.approval_date = datetime.utcnow()
        change_request.approval_decision = approval_in.decision
        change_request.approval_comments = approval_in.comments

        # 根据审批决策更新状态
        if approval_in.decision == ApprovalDecisionEnum.APPROVED:
            change_request.status = ChangeStatusEnum.APPROVED
            self._apply_approved_change_to_project_baseline(change_request, current_user)
        elif approval_in.decision == ApprovalDecisionEnum.REJECTED:
            change_request.status = ChangeStatusEnum.REJECTED
        elif approval_in.decision == ApprovalDecisionEnum.RETURNED:
            change_request.status = ChangeStatusEnum.ASSESSING

        self._record_project_change_approval_log(
            change_request=change_request,
            approval_in=approval_in,
            current_user=current_user,
            before_status=before_status,
        )

        self.db.add(change_request)
        self.db.commit()
        self.db.refresh(change_request)

        if change_request.notify_team:
            decision = approval_in.decision.value
            self._send_change_notification(
                change_request,
                recipient_ids={change_request.submitter_id},
                event=decision,
                title="项目变更审批结果",
                content=f"项目变更 {change_request.change_code} 审批结果：{decision}",
                priority=(
                    NotificationPriority.HIGH
                    if approval_in.decision == ApprovalDecisionEnum.REJECTED
                    else NotificationPriority.NORMAL
                ),
            )

        return change_request

    def get_approval_records(self, change_id: int) -> List[dict]:
        """获取审批记录"""
        get_or_404(self.db, ChangeRequest, change_id, detail="变更请求不存在")

        rows = (
            self.db.query(ApprovalActionLog, ApprovalInstance.entity_id)
            .join(ApprovalInstance, ApprovalActionLog.instance_id == ApprovalInstance.id)
            .filter(
                ApprovalInstance.entity_type == PROJECT_CHANGE_APPROVAL_ENTITY_TYPE,
                ApprovalInstance.entity_id == change_id,
                ApprovalActionLog.action.in_(PROJECT_CHANGE_DECISION_BY_ACTION),
            )
            .order_by(ApprovalActionLog.action_at.desc(), ApprovalActionLog.id.desc())
            .all()
        )

        records = []
        for log, entity_id in rows:
            detail = self._json_dict(log.action_detail)
            decision = detail.get("decision") or PROJECT_CHANGE_DECISION_BY_ACTION.get(log.action)
            records.append(
                {
                    "id": log.id,
                    "change_request_id": entity_id,
                    "approver_id": log.operator_id,
                    "approver_name": log.operator_name,
                    "approver_role": detail.get("approver_role") or detail.get("role"),
                    "approval_date": log.action_at,
                    "decision": decision,
                    "comments": log.comment,
                    "attachments": log.attachments,
                    "created_at": log.created_at,
                }
            )

        return records

    def update_change_status(
        self,
        change_id: int,
        status_in: ChangeStatusUpdateRequest,
    ) -> tuple[ChangeRequest, str]:
        """更新变更状态，返回变更请求和旧状态"""
        change_request = get_or_404(self.db, ChangeRequest, change_id, detail="变更请求不存在")

        # 验证状态转换是否合法
        if not self.validate_status_transition(change_request.status, status_in.new_status):
            raise HTTPException(
                status_code=400,
                detail=f"不允许从 {change_request.status.value} 转换到 {status_in.new_status.value}",
            )

        # 更新状态
        old_status = change_request.status.value
        change_request.status = status_in.new_status

        # 根据新状态更新相关字段
        if status_in.new_status == ChangeStatusEnum.IMPLEMENTING:
            if not change_request.implementation_start_date:
                change_request.implementation_start_date = datetime.utcnow()
        elif status_in.new_status == ChangeStatusEnum.VERIFYING:
            if not change_request.implementation_end_date:
                change_request.implementation_end_date = datetime.utcnow()
        elif status_in.new_status == ChangeStatusEnum.CLOSED:
            change_request.close_date = datetime.utcnow()
            change_request.close_notes = status_in.notes

        save_obj(self.db, change_request)

        return change_request, old_status

    def update_implementation_info(
        self,
        change_id: int,
        impl_in: ChangeImplementationRequest,
    ) -> ChangeRequest:
        """更新实施信息"""
        change_request = get_or_404(self.db, ChangeRequest, change_id, detail="变更请求不存在")

        # 只有已批准或实施中状态才能更新实施信息
        if change_request.status not in [ChangeStatusEnum.APPROVED, ChangeStatusEnum.IMPLEMENTING]:
            raise HTTPException(status_code=400, detail="只有已批准或实施中的变更才能更新实施信息")

        # 更新实施信息
        update_data = impl_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(change_request, field, value)

        # 如果状态是已批准，自动转换为实施中
        if change_request.status == ChangeStatusEnum.APPROVED and impl_in.implementation_start_date:
            change_request.status = ChangeStatusEnum.IMPLEMENTING

        save_obj(self.db, change_request)

        return change_request

    def verify_change_request(
        self,
        change_id: int,
        verify_in: ChangeVerificationRequest,
        current_user: User,
    ) -> ChangeRequest:
        """验证变更"""
        change_request = get_or_404(self.db, ChangeRequest, change_id, detail="变更请求不存在")

        # 只有验证中状态才能验证
        if change_request.status != ChangeStatusEnum.VERIFYING:
            raise HTTPException(status_code=400, detail="只有验证中的变更才能进行验证")

        # 更新验证信息
        change_request.verification_notes = verify_in.verification_notes
        change_request.verification_date = datetime.utcnow()
        change_request.verified_by_id = current_user.id
        change_request.verified_by_name = current_user.real_name or current_user.username
        change_request.status = ChangeStatusEnum.CLOSED
        change_request.close_date = datetime.utcnow()

        save_obj(self.db, change_request)

        return change_request

    def close_change_request(
        self,
        change_id: int,
        close_in: ChangeCloseRequest,
    ) -> ChangeRequest:
        """关闭变更"""
        change_request = get_or_404(self.db, ChangeRequest, change_id, detail="变更请求不存在")

        # 检查状态
        if change_request.status in [ChangeStatusEnum.CLOSED, ChangeStatusEnum.CANCELLED]:
            raise HTTPException(status_code=400, detail="变更已经关闭或取消")

        # 关闭变更
        change_request.status = ChangeStatusEnum.CLOSED
        change_request.close_date = datetime.utcnow()
        change_request.close_notes = close_in.close_notes

        save_obj(self.db, change_request)

        return change_request

    def get_statistics(
        self,
        project_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> ChangeRequestStatistics:
        """获取变更统计信息"""
        query = self.db.query(ChangeRequest)

        # 应用过滤条件
        if project_id:
            query = query.filter(ChangeRequest.project_id == project_id)
        if start_date:
            query = query.filter(ChangeRequest.submit_date >= start_date)
        if end_date:
            query = query.filter(ChangeRequest.submit_date <= end_date)

        all_changes = query.all()

        # 统计数据
        total = len(all_changes)
        by_status: Dict[str, int] = {}
        by_type: Dict[str, int] = {}
        by_source: Dict[str, int] = {}
        total_cost_impact = Decimal(0)
        total_time_impact = 0

        for change in all_changes:
            # 按状态统计
            status_key = change.status.value
            by_status[status_key] = by_status.get(status_key, 0) + 1

            # 按类型统计
            type_key = change.change_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

            # 按来源统计
            source_key = change.change_source.value
            by_source[source_key] = by_source.get(source_key, 0) + 1

            # 累加成本和时间影响
            if change.cost_impact:
                total_cost_impact += change.cost_impact
            if change.time_impact:
                total_time_impact += change.time_impact

        # 统计审批状态
        pending_approval = by_status.get(ChangeStatusEnum.PENDING_APPROVAL.value, 0)
        approved = by_status.get(ChangeStatusEnum.APPROVED.value, 0)
        rejected = by_status.get(ChangeStatusEnum.REJECTED.value, 0)

        statistics = ChangeRequestStatistics(
            total=total,
            by_status=by_status,
            by_type=by_type,
            by_source=by_source,
            pending_approval=pending_approval,
            approved=approved,
            rejected=rejected,
            total_cost_impact=total_cost_impact,
            total_time_impact=total_time_impact,
        )

        return statistics

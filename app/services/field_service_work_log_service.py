# -*- coding: utf-8 -*-
"""外出服务工作日志自动生成服务"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Iterable, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.installation_dispatch import InstallationDispatchOrder
from app.models.work_log import WorkLog
from app.schemas.work_log import WorkLogCreate, WorkLogUpdate
from app.services.work_log_service import WorkLogService

ACTIVE_FIELD_SERVICE_STATUSES = ("ASSIGNED", "IN_PROGRESS", "COMPLETED")


def _text(value) -> str:
    return str(value or "").strip()


def _unique_ints(values: Iterable[Optional[int]]) -> list[int]:
    seen: set[int] = set()
    result: list[int] = []
    for value in values:
        if value is None:
            continue
        int_value = int(value)
        if int_value not in seen:
            seen.add(int_value)
            result.append(int_value)
    return result


def _trim_content(content: str, limit: int = 300) -> str:
    content = "；".join(part.strip("； ") for part in content.split("；") if part.strip("； "))
    if len(content) <= limit:
        return content
    return content[: limit - 1].rstrip("； ，,") + "…"


def _name_from_relation(obj, *attrs) -> str:
    if not obj:
        return ""
    for attr in attrs:
        value = getattr(obj, attr, None)
        if value:
            return str(value)
    return ""


def build_field_service_context_item(order: InstallationDispatchOrder) -> dict:
    """将安装调试派工单转换为工作日志上下文。"""
    project_name = _name_from_relation(order.project, "project_name", "name")
    machine_name = _name_from_relation(order.machine, "machine_name", "display_name", "machine_code")
    customer_name = _name_from_relation(order.customer, "customer_name", "name")
    base_parts = [
        f"{order.order_no} {project_name}/{machine_name or '未关联设备'}",
        _text(order.task_title),
    ]
    if getattr(order, "progress", None) is not None:
        base_parts.append(f"进度{order.progress}%")
    if _text(getattr(order, "execution_notes", None)):
        base_parts.append(_text(order.execution_notes))

    return {
        "dispatch_order_id": order.id,
        "order_no": order.order_no,
        "status": order.status,
        "task_type": order.task_type,
        "task_title": order.task_title,
        "task_description": getattr(order, "task_description", None),
        "project_id": order.project_id,
        "project_name": project_name,
        "machine_id": order.machine_id,
        "machine_name": machine_name,
        "customer_id": order.customer_id,
        "customer_name": customer_name,
        "scheduled_date": order.scheduled_date,
        "location": getattr(order, "location", None),
        "progress": getattr(order, "progress", None) or 0,
        "execution_notes": getattr(order, "execution_notes", None),
        "issues_found": getattr(order, "issues_found", None),
        "solution_provided": getattr(order, "solution_provided", None),
        "estimated_hours": getattr(order, "estimated_hours", None),
        "default_content": _trim_content("；".join(part for part in base_parts if part)),
    }


def build_work_log_create_from_dispatch_orders(
    orders: list[InstallationDispatchOrder],
    *,
    work_date: date,
    today_progress: Optional[str] = None,
    issues_found: Optional[str] = None,
    next_plan: Optional[str] = None,
    work_hours: Optional[Decimal] = None,
    content: Optional[str] = None,
    status: str = "SUBMITTED",
) -> WorkLogCreate:
    """从一个或多个外出派工单生成工作日志创建 payload。"""
    if not orders:
        raise ValueError("没有可生成工作日志的外出派工单")

    project_ids = _unique_ints(order.project_id for order in orders)
    machine_ids = _unique_ints(order.machine_id for order in orders)

    if content:
        final_content = _trim_content(content)
    else:
        task_parts = [
            build_field_service_context_item(order)["default_content"]
            for order in orders
        ]
        user_parts = []
        if _text(today_progress):
            user_parts.append(f"今日进展：{_text(today_progress)}")
        if _text(issues_found):
            user_parts.append(f"现场问题：{_text(issues_found)}")
        if _text(next_plan):
            user_parts.append(f"下一步：{_text(next_plan)}")
        final_content = _trim_content("；".join(task_parts + user_parts))

    return WorkLogCreate(
        work_date=work_date,
        content=final_content,
        mentioned_projects=project_ids,
        mentioned_machines=machine_ids,
        mentioned_users=[],
        status=status or "SUBMITTED",
        work_hours=work_hours,
        project_id=project_ids[0] if project_ids else None,
    )


class FieldServiceWorkLogService:
    """外出服务工作日志应用服务。"""

    def __init__(self, db: Session):
        self.db = db

    def list_context(self, user_id: int, work_date: date) -> dict:
        """获取当前用户某日负责的外出派工上下文。"""
        orders = self._query_user_dispatch_orders(user_id, work_date).all()
        existing_logs = (
            self.db.query(WorkLog)
            .filter(WorkLog.user_id == user_id, WorkLog.work_date == work_date)
            .all()
        )
        submitted = next((log for log in existing_logs if log.status == "SUBMITTED"), None)
        draft = next((log for log in existing_logs if log.status == "DRAFT"), None)

        return {
            "work_date": work_date,
            "has_submitted_log": submitted is not None,
            "submitted_log_id": submitted.id if submitted else None,
            "draft_log_id": draft.id if draft else None,
            "items": [build_field_service_context_item(order) for order in orders],
        }

    def create_from_dispatch(
        self,
        user_id: int,
        *,
        work_date: date,
        dispatch_order_ids: list[int],
        today_progress: Optional[str] = None,
        issues_found: Optional[str] = None,
        next_plan: Optional[str] = None,
        work_hours: Optional[Decimal] = None,
        content: Optional[str] = None,
        status: str = "SUBMITTED",
    ) -> WorkLog:
        """从当前用户负责的外出派工单创建或提交当天工作日志。"""
        query = self._query_user_dispatch_orders(user_id, work_date)
        if dispatch_order_ids:
            query = query.filter(InstallationDispatchOrder.id.in_(dispatch_order_ids))
        orders = query.all()
        if not orders:
            raise ValueError("没有找到当前用户当天负责的外出派工单")

        create_payload = build_work_log_create_from_dispatch_orders(
            orders,
            work_date=work_date,
            today_progress=today_progress,
            issues_found=issues_found,
            next_plan=next_plan,
            work_hours=work_hours,
            content=content,
            status=status,
        )

        existing = (
            self.db.query(WorkLog)
            .filter(WorkLog.user_id == user_id, WorkLog.work_date == work_date)
            .first()
        )
        work_log_service = WorkLogService(self.db)
        if existing:
            if existing.status != "DRAFT":
                raise ValueError("该日期已提交工作日志，请更新现有记录或选择其他日期")
            update_payload = WorkLogUpdate(
                content=create_payload.content,
                mentioned_projects=create_payload.mentioned_projects,
                mentioned_machines=create_payload.mentioned_machines,
                mentioned_users=[],
                status=create_payload.status,
                work_hours=create_payload.work_hours,
                project_id=create_payload.project_id,
            )
            return work_log_service.update_work_log(existing.id, user_id, update_payload)

        return work_log_service.create_work_log(user_id, create_payload)

    def _query_user_dispatch_orders(self, user_id: int, work_date: date):
        return (
            self.db.query(InstallationDispatchOrder)
            .options(
                joinedload(InstallationDispatchOrder.project),
                joinedload(InstallationDispatchOrder.machine),
                joinedload(InstallationDispatchOrder.customer),
            )
            .filter(
                InstallationDispatchOrder.assigned_to_id == user_id,
                InstallationDispatchOrder.scheduled_date == work_date,
                InstallationDispatchOrder.status.in_(ACTIVE_FIELD_SERVICE_STATUSES),
            )
            .order_by(InstallationDispatchOrder.id.asc())
        )

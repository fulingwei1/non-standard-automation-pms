# -*- coding: utf-8 -*-
"""
售后服务 API

提供客户反馈、维修保养、技术支持工单的管理功能
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.endpoints.installation_dispatch.utils import generate_order_no
from app.core import security
from app.models.installation_dispatch import InstallationDispatchOrder
from app.models.after_sales import (
    AfterSalesFieldService,
    AfterSalesFeedback,
    AfterSalesKnowledge,
    AfterSalesMaintenance,
    AfterSalesSLA,
    AfterSalesSatisfaction,
    AfterSalesSparePart,
    AfterSalesSupportTicket,
    AfterSalesWarranty,
)
from app.models.project import Project, ProjectWarranty
from app.models.service import ServiceTicket
from app.models.user import User
from app.models.warehouse import Inventory, Warehouse
from app.schemas.service import ServiceTicketCreate
from app.services.notification.channels.base import (
    NotificationChannel,
    NotificationPriority,
    NotificationRequest,
)
from app.services.notification.unified_notification_service import get_notification_service

router = APIRouter()
logger = logging.getLogger(__name__)

AFTER_SALES_TABLE_MODELS = (
    AfterSalesFeedback,
    AfterSalesMaintenance,
    AfterSalesSupportTicket,
    AfterSalesWarranty,
    AfterSalesSparePart,
    AfterSalesFieldService,
    AfterSalesSLA,
    AfterSalesSatisfaction,
    AfterSalesKnowledge,
)

AFTER_SALES_SPARE_WAREHOUSE_CODE = "AFTER_SALES_SPARES"
AFTER_SALES_SPARE_WAREHOUSE_NAME = "售后备件仓"


def _ensure_after_sales_tables(db: Session) -> None:
    bind = db.get_bind()
    for model in AFTER_SALES_TABLE_MODELS:
        model.__table__.create(bind=bind, checkfirst=True)
    ProjectWarranty.__table__.create(bind=bind, checkfirst=True)
    inspector = inspect(bind)
    if inspector.has_table("after_sales_field_services"):
        columns = {
            column["name"]
            for column in inspector.get_columns("after_sales_field_services")
        }
        optional_columns = {
            "dispatch_order_id": "INTEGER",
            "service_fee": "NUMERIC(12, 2) DEFAULT 0",
            "warranty_source": "VARCHAR(30)",
            "charge_required": "BOOLEAN DEFAULT 0",
            "charge_reason": "VARCHAR(50)",
            "charge_status": "VARCHAR(20) DEFAULT 'NOT_REQUIRED'",
        }
        for column_name, column_definition in optional_columns.items():
            if column_name not in columns:
                db.execute(
                    text(
                        "ALTER TABLE after_sales_field_services "
                        f"ADD COLUMN {column_name} {column_definition}"
                    )
                )
        db.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_asfs_dispatch_order "
                "ON after_sales_field_services(dispatch_order_id)"
            )
        )


def _to_decimal(value, default: str = "0") -> Decimal:
    value = _query_default(value)
    if value is None or value == "":
        return Decimal(default)
    return Decimal(str(value))


def _query_default(value):
    if value.__class__.__module__.startswith("fastapi.params"):
        return value.default
    return value


def _spare_part_status(quantity: int, min_stock: int | None = None) -> str:
    if quantity <= 0:
        return "OUT_OF_STOCK"
    if min_stock is not None and quantity <= min_stock:
        return "LOW_STOCK"
    return "IN_STOCK"


def _evaluate_project_warranty(db: Session, project: Project, planned_date: date) -> dict:
    warranty = (
        db.query(AfterSalesWarranty)
        .filter(
            AfterSalesWarranty.project_id == project.id,
            AfterSalesWarranty.status == "ACTIVE",
            AfterSalesWarranty.warranty_start <= planned_date,
            AfterSalesWarranty.warranty_end >= planned_date,
        )
        .first()
    )
    if warranty:
        return {
            "is_warranty": True,
            "warranty_source": "after_sales_warranty",
            "warranty_id": warranty.id,
        }

    project_warranties = (
        db.query(ProjectWarranty)
        .filter(ProjectWarranty.project_id == project.id)
        .all()
    )
    for project_warranty in project_warranties:
        if project_warranty.warranty_status not in {"ACTIVE", "EXTENDED"}:
            continue
        if not project_warranty.warranty_start_date or not project_warranty.warranty_end_date:
            continue
        if not (
            project_warranty.warranty_start_date
            <= planned_date
            <= project_warranty.warranty_end_date
        ):
            continue
        return {
            "is_warranty": True,
            "warranty_source": "project_warranty",
            "warranty_id": project_warranty.id,
        }

    if (
        project.warranty_start_date
        and project.warranty_end_date
        and project.warranty_start_date <= planned_date <= project.warranty_end_date
    ):
        return {
            "is_warranty": True,
            "warranty_source": "project_core",
            "warranty_id": None,
        }

    return {
        "is_warranty": False,
        "warranty_source": (
            "project_warranty"
            if project_warranties
            else
            "project_core"
            if project.warranty_start_date or project.warranty_end_date
            else None
        ),
        "warranty_id": project_warranties[0].id if project_warranties else None,
    }


def _charge_status(charge_required: bool, total_cost: Decimal) -> str:
    if not charge_required:
        return "NOT_REQUIRED"
    return "PENDING" if total_cost > 0 else "TO_BE_PRICED"


def _is_warranty_active(
    start_date: Optional[date],
    end_date: Optional[date],
    status_value: Optional[str],
    as_of: date,
) -> bool:
    if status_value not in {"ACTIVE", "EXTENDED"}:
        return False
    if not start_date or not end_date:
        return False
    return start_date <= as_of <= end_date


def _project_under_warranty(db: Session, project_id: int, planned_date: date) -> bool:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return False
    return bool(_evaluate_project_warranty(db, project, planned_date)["is_warranty"])


def _dispatch_task_type(service_type: str) -> str:
    normalized = (service_type or "OTHER").upper()
    allowed = {"INSTALLATION", "DEBUGGING", "TRAINING", "MAINTENANCE", "REPAIR", "OTHER"}
    return normalized if normalized in allowed else "OTHER"


def _create_dispatch_order_for_field_service(
    db: Session,
    *,
    project: Project,
    field_service: AfterSalesFieldService,
    current_user: User,
    priority: str = "NORMAL",
) -> InstallationDispatchOrder:
    if not project.customer_id:
        raise HTTPException(status_code=400, detail="项目缺少客户，无法生成现场服务派工单")

    assigned = field_service.engineer_id is not None
    dispatch = InstallationDispatchOrder(
        order_no=generate_order_no(db),
        project_id=project.id,
        customer_id=project.customer_id,
        task_type=_dispatch_task_type(field_service.service_type),
        task_title=f"售后现场服务：{field_service.service_type}",
        task_description=field_service.service_content,
        scheduled_date=field_service.planned_date,
        estimated_hours=_to_decimal(field_service.service_hours) if field_service.service_hours else None,
        assigned_to_id=field_service.engineer_id,
        assigned_to_name=field_service.engineer_name,
        assigned_by_id=current_user.id if assigned else None,
        assigned_by_name=(current_user.real_name or current_user.username) if assigned else None,
        assigned_time=datetime.now() if assigned else None,
        status="ASSIGNED" if assigned else "PENDING",
        priority=priority,
        remark=f"after_sales_field_service_id={field_service.id}",
    )
    db.add(dispatch)
    db.flush()
    field_service.dispatch_order_id = dispatch.id
    db.add(field_service)
    return dispatch


def _get_or_create_spare_warehouse(db: Session) -> Warehouse:
    warehouse = (
        db.query(Warehouse)
        .filter(Warehouse.warehouse_code == AFTER_SALES_SPARE_WAREHOUSE_CODE)
        .first()
    )
    if warehouse:
        return warehouse

    warehouse = Warehouse(
        warehouse_code=AFTER_SALES_SPARE_WAREHOUSE_CODE,
        warehouse_name=AFTER_SALES_SPARE_WAREHOUSE_NAME,
        warehouse_type="AFTER_SALES",
        is_active=True,
    )
    db.add(warehouse)
    db.flush()
    return warehouse


def _spare_part_batch_no(project_id: int) -> str:
    return f"AS-PROJ-{project_id}"


def _get_spare_part_inventory(
    db: Session,
    part: AfterSalesSparePart,
    *,
    create: bool,
) -> Inventory | None:
    warehouse = _get_or_create_spare_warehouse(db)
    batch_no = _spare_part_batch_no(part.project_id)
    inventory = (
        db.query(Inventory)
        .filter(
            Inventory.warehouse_id == warehouse.id,
            Inventory.material_code == part.part_no,
            Inventory.batch_no == batch_no,
        )
        .first()
    )
    if inventory or not create:
        return inventory

    inventory = Inventory(
        warehouse_id=warehouse.id,
        material_code=part.part_no,
        material_name=part.part_name,
        specification=part.part_spec,
        unit="件",
        quantity=Decimal("0"),
        available_quantity=Decimal("0"),
        reserved_quantity=Decimal("0"),
        min_stock=_to_decimal(part.min_stock),
        batch_no=batch_no,
    )
    db.add(inventory)
    db.flush()
    return inventory


def _sync_spare_part_inventory(db: Session, part: AfterSalesSparePart) -> Inventory:
    inventory = _get_spare_part_inventory(db, part, create=True)
    quantity = _to_decimal(part.quantity)
    inventory.material_name = part.part_name
    inventory.specification = part.part_spec
    inventory.quantity = quantity
    inventory.available_quantity = quantity
    inventory.min_stock = _to_decimal(part.min_stock)
    inventory.last_inbound_date = datetime.now() if quantity > 0 else inventory.last_inbound_date
    db.add(inventory)
    return inventory


def _format_legacy_support_ticket(ticket: AfterSalesSupportTicket) -> dict:
    return {
        "id": ticket.id,
        "ticket_no": ticket.ticket_no,
        "subject": ticket.subject,
        "description": ticket.description,
        "category": ticket.category,
        "priority": ticket.priority,
        "status": ticket.status,
        "created_at": ticket.created_at,
        "assignee_name": ticket.assignee.username if ticket.assignee else None,
        "source": "legacy_after_sales_support_ticket",
    }


def _format_service_ticket(ticket: ServiceTicket) -> dict:
    subject = ticket.problem_desc or ticket.problem_type or ticket.ticket_no
    return {
        "id": ticket.id,
        "ticket_no": ticket.ticket_no,
        "subject": subject,
        "description": ticket.problem_desc,
        "category": ticket.problem_type,
        "priority": ticket.urgency,
        "status": ticket.status,
        "created_at": ticket.created_at,
        "assignee_name": ticket.assigned_to_name,
        "source": "service_ticket",
    }


def _send_after_sales_notification(
    db: Session,
    *,
    project_id: int | None,
    current_user: User,
    event: str,
    title: str,
    content: str,
    source_type: str,
    source_id: int,
    priority: str = NotificationPriority.NORMAL,
) -> None:
    """Send a system notification for after-sales write-side events."""
    recipient_ids: set[int] = set()
    if project_id is not None:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project and project.pm_id:
            recipient_ids.add(project.pm_id)

    if not recipient_ids and current_user and current_user.id:
        recipient_ids.add(current_user.id)

    if not recipient_ids:
        return

    notification_service = get_notification_service(db)
    for recipient_id in sorted(recipient_ids):
        request = NotificationRequest(
            recipient_id=recipient_id,
            notification_type=f"AFTER_SALES_{event}",
            category="project",
            title=title,
            content=content,
            priority=priority,
            channels=[NotificationChannel.SYSTEM],
            source_type=source_type,
            source_id=source_id,
            link_url=(
                f"/after-sales/projects/{project_id}"
                if project_id is not None
                else "/after-sales/knowledge"
            ),
            extra_data={"project_id": project_id, "event": event},
            force_send=True,
        )
        try:
            notification_service.send_notification(request)
        except Exception:
            logger.exception(
                "售后通知发送失败: event=%s source_type=%s source_id=%s recipient_id=%s",
                event,
                source_type,
                source_id,
                recipient_id,
            )


# ==================== 客户反馈管理 ====================

@router.get("/projects/{project_id}/feedback", response_model=List[dict])
def get_project_feedback(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """获取项目客户反馈列表"""
    _ensure_after_sales_tables(db)
    feedbacks = db.query(AfterSalesFeedback).filter(
        AfterSalesFeedback.project_id == project_id
    ).order_by(AfterSalesFeedback.created_at.desc()).all()
    
    return [
        {
            "id": f.id,
            "feedback_type": f.feedback_type,
            "feedback_content": f.feedback_content,
            "priority": f.priority,
            "status": f.status,
            "created_at": f.created_at,
            "assignee_name": f.assignee.username if f.assignee else None,
        }
        for f in feedbacks
    ]


@router.post("/projects/{project_id}/feedback", status_code=status.HTTP_201_CREATED)
def create_feedback(
    project_id: int,
    feedback_type: str = Query(..., description="反馈类型：COMPLAINT/SUGGESTION/PRAISE"),
    feedback_content: str = Query(..., description="反馈内容"),
    priority: str = Query("MEDIUM", description="优先级"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """创建客户反馈"""
    _ensure_after_sales_tables(db)
    feedback = AfterSalesFeedback(
        project_id=project_id,
        feedback_type=feedback_type,
        feedback_content=feedback_content,
        priority=priority,
        status="PENDING",
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    _send_after_sales_notification(
        db,
        project_id=project_id,
        current_user=current_user,
        event="FEEDBACK_CREATED",
        title="客户反馈已创建",
        content=f"项目 {project_id} 新增客户反馈：{feedback_type}",
        source_type="after_sales_feedback",
        source_id=feedback.id,
        priority=NotificationPriority.HIGH if priority in {"HIGH", "URGENT"} else NotificationPriority.NORMAL,
    )
    
    return {"id": feedback.id, "message": "反馈创建成功"}


@router.put("/projects/{project_id}/feedback/{feedback_id}")
def update_feedback(
    project_id: int,
    feedback_id: int,
    feedback_status: Optional[str] = Query(None, alias="status"),
    resolution: str = Query(""),
    assigned_to: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """更新客户反馈处理状态。"""
    _ensure_after_sales_tables(db)
    feedback = (
        db.query(AfterSalesFeedback)
        .filter(
            AfterSalesFeedback.id == feedback_id,
            AfterSalesFeedback.project_id == project_id,
        )
        .first()
    )
    if not feedback:
        raise HTTPException(status_code=404, detail="客户反馈不存在")

    if feedback_status:
        feedback.status = feedback_status
        if feedback_status in {"RESOLVED", "CLOSED"} and not feedback.resolved_at:
            feedback.resolved_at = datetime.now()
    if resolution:
        feedback.resolution = resolution
    if assigned_to is not None:
        feedback.assigned_to = assigned_to

    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    _send_after_sales_notification(
        db,
        project_id=project_id,
        current_user=current_user,
        event="FEEDBACK_UPDATED",
        title="客户反馈已更新",
        content=f"项目 {project_id} 客户反馈状态更新为 {feedback.status}",
        source_type="after_sales_feedback",
        source_id=feedback.id,
    )
    return {
        "id": feedback.id,
        "status": feedback.status,
        "resolution": feedback.resolution,
        "resolved_at": feedback.resolved_at,
    }


# ==================== 维修保养管理 ====================

@router.get("/projects/{project_id}/maintenance", response_model=List[dict])
def get_project_maintenance(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """获取项目维修保养记录"""
    _ensure_after_sales_tables(db)
    records = db.query(AfterSalesMaintenance).filter(
        AfterSalesMaintenance.project_id == project_id
    ).order_by(AfterSalesMaintenance.scheduled_date.desc()).all()
    
    return [
        {
            "id": r.id,
            "maintenance_type": r.maintenance_type,
            "maintenance_content": r.maintenance_content,
            "scheduled_date": r.scheduled_date,
            "status": r.status,
            "technician_name": r.technician.username if r.technician else None,
        }
        for r in records
    ]


@router.post("/projects/{project_id}/maintenance", status_code=status.HTTP_201_CREATED)
def create_maintenance(
    project_id: int,
    maintenance_type: str = Query(..., description="保养类型"),
    maintenance_content: str = Query(..., description="保养内容"),
    scheduled_date: date = Query(..., description="计划日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """创建维修保养记录"""
    _ensure_after_sales_tables(db)
    record = AfterSalesMaintenance(
        project_id=project_id,
        maintenance_type=maintenance_type,
        maintenance_content=maintenance_content,
        scheduled_date=scheduled_date,
        status="SCHEDULED",
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    _send_after_sales_notification(
        db,
        project_id=project_id,
        current_user=current_user,
        event="MAINTENANCE_CREATED",
        title="维修保养记录已创建",
        content=f"项目 {project_id} 新增维修保养：{maintenance_type}",
        source_type="after_sales_maintenance",
        source_id=record.id,
    )
    
    return {"id": record.id, "message": "保养记录创建成功"}


@router.put("/projects/{project_id}/maintenance/{maintenance_id}")
def update_maintenance(
    project_id: int,
    maintenance_id: int,
    maintenance_status: Optional[str] = Query(None, alias="status"),
    completed_date: Optional[date] = Query(None),
    notes: str = Query(""),
    technician_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """更新维修保养记录状态。"""
    _ensure_after_sales_tables(db)
    record = (
        db.query(AfterSalesMaintenance)
        .filter(
            AfterSalesMaintenance.id == maintenance_id,
            AfterSalesMaintenance.project_id == project_id,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="维修保养记录不存在")

    if maintenance_status:
        record.status = maintenance_status
        if maintenance_status == "COMPLETED" and not record.completed_date:
            record.completed_date = completed_date or date.today()
    if completed_date:
        record.completed_date = completed_date
    if notes:
        record.notes = notes
    if technician_id is not None:
        record.technician_id = technician_id

    db.add(record)
    db.commit()
    db.refresh(record)
    _send_after_sales_notification(
        db,
        project_id=project_id,
        current_user=current_user,
        event="MAINTENANCE_UPDATED",
        title="维修保养记录已更新",
        content=f"项目 {project_id} 维修保养状态更新为 {record.status}",
        source_type="after_sales_maintenance",
        source_id=record.id,
    )
    return {
        "id": record.id,
        "status": record.status,
        "completed_date": record.completed_date,
        "notes": record.notes,
    }


# ==================== 技术支持工单 ====================

@router.get("/projects/{project_id}/support-tickets", response_model=List[dict])
def get_project_support_tickets(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """获取项目技术支持工单"""
    _ensure_after_sales_tables(db)
    service_tickets = (
        db.query(ServiceTicket)
        .filter(ServiceTicket.project_id == project_id)
        .order_by(ServiceTicket.created_at.desc())
        .all()
    )
    legacy_tickets = (
        db.query(AfterSalesSupportTicket)
        .filter(AfterSalesSupportTicket.project_id == project_id)
        .order_by(AfterSalesSupportTicket.created_at.desc())
        .all()
    )
    
    return [
        *[_format_service_ticket(ticket) for ticket in service_tickets],
        *[_format_legacy_support_ticket(ticket) for ticket in legacy_tickets],
    ]


@router.post("/projects/{project_id}/support-tickets", status_code=status.HTTP_201_CREATED)
def create_support_ticket(
    project_id: int,
    subject: str = Query(..., description="主题"),
    description: str = Query(..., description="问题描述"),
    category: str = Query("TECHNICAL", description="分类"),
    priority: str = Query("MEDIUM", description="优先级"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("aftersales:manage")),
):
    """创建技术支持工单"""
    _ensure_after_sales_tables(db)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目不存在 (ID: {project_id})")
    if not project.customer_id:
        raise HTTPException(status_code=400, detail="项目缺少客户，无法创建统一服务工单")

    from app.api.v1.endpoints.service.tickets.crud import (
        create_service_ticket as create_central_service_ticket,
    )

    ticket = create_central_service_ticket(
        db=db,
        ticket_in=ServiceTicketCreate(
            project_id=project_id,
            customer_id=project.customer_id,
            problem_type=category,
            problem_desc=description or subject,
            urgency=priority,
            reported_by=str(current_user.id or current_user.username),
            reported_time=datetime.now(),
        ),
        current_user=current_user,
    )
    _send_after_sales_notification(
        db,
        project_id=project_id,
        current_user=current_user,
        event="SUPPORT_TICKET_CREATED",
        title="技术支持工单已创建",
        content=f"项目 {project_id} 新增技术支持工单：{subject}",
        source_type="after_sales_support_ticket",
        source_id=ticket.id,
        priority=NotificationPriority.HIGH if priority in {"HIGH", "URGENT"} else NotificationPriority.NORMAL,
    )
    
    return {
        "id": ticket.id,
        "ticket_no": ticket.ticket_no,
        "message": "工单创建成功",
        "source": "service_ticket",
    }



# ==================== 质保管理 ====================

@router.get("/projects/{project_id}/warranty")
def get_warranty(project_id: int, as_of: Optional[date] = Query(None), db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """获取项目质保信息"""
    _ensure_after_sales_tables(db)
    as_of_date = _query_default(as_of) or date.today()
    warranties = db.query(AfterSalesWarranty).filter(AfterSalesWarranty.project_id == project_id).all()
    response = []
    for w in warranties:
        is_under_warranty = _is_warranty_active(
            w.warranty_start,
            w.warranty_end,
            w.status,
            as_of_date,
        )
        response.append(
            {
                "id": w.id,
                "source": "after_sales_warranty",
                "warranty_no": w.warranty_no,
                "warranty_type": w.warranty_type,
                "warranty_start": str(w.warranty_start),
                "warranty_end": str(w.warranty_end),
                "status": w.status,
                "scope": w.scope,
                "is_under_warranty": is_under_warranty,
                "charge_required": not is_under_warranty,
            }
        )

    project_warranties = (
        db.query(ProjectWarranty)
        .filter(ProjectWarranty.project_id == project_id)
        .all()
    )
    for w in project_warranties:
        is_under_warranty = _is_warranty_active(
            w.warranty_start_date,
            w.warranty_end_date,
            w.warranty_status,
            as_of_date,
        )
        response.append(
            {
                "id": w.id,
                "source": "project_warranty",
                "warranty_no": None,
                "warranty_type": None,
                "warranty_start": str(w.warranty_start_date),
                "warranty_end": str(w.warranty_end_date),
                "status": w.warranty_status,
                "scope": w.warranty_notes,
                "is_under_warranty": is_under_warranty,
                "charge_required": not is_under_warranty,
            }
        )

    if not response:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project and (project.warranty_start_date or project.warranty_end_date):
            is_under_warranty = _is_warranty_active(
                project.warranty_start_date,
                project.warranty_end_date,
                "ACTIVE",
                as_of_date,
            )
            response.append(
                {
                    "id": None,
                    "source": "project_core",
                    "warranty_no": None,
                    "warranty_type": None,
                    "warranty_start": str(project.warranty_start_date),
                    "warranty_end": str(project.warranty_end_date),
                    "status": "ACTIVE" if is_under_warranty else "EXPIRED",
                    "scope": None,
                    "is_under_warranty": is_under_warranty,
                    "charge_required": not is_under_warranty,
                }
            )
    return response

@router.post("/projects/{project_id}/warranty", status_code=status.HTTP_201_CREATED)
def create_warranty(project_id: int, warranty_type: str = Query("STANDARD"), warranty_months: int = Query(12), scope: str = Query(""), db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """创建质保记录"""
    _ensure_after_sales_tables(db)
    from app.models.after_sales import AfterSalesWarranty
    from dateutil.relativedelta import relativedelta
    start = date.today()
    end = start + relativedelta(months=warranty_months)
    w = AfterSalesWarranty(project_id=project_id, warranty_no=f"WRT-{project_id}-{start.strftime('%Y%m%d')}", warranty_type=warranty_type, warranty_start=start, warranty_end=end, warranty_months=warranty_months, scope=scope, status="ACTIVE")
    db.add(w)
    db.commit()
    db.refresh(w)
    _send_after_sales_notification(
        db,
        project_id=project_id,
        current_user=current_user,
        event="WARRANTY_CREATED",
        title="质保记录已创建",
        content=f"项目 {project_id} 新增质保记录：{warranty_type}",
        source_type="after_sales_warranty",
        source_id=w.id,
    )
    return {"id": w.id, "warranty_no": w.warranty_no}


# ==================== 备件管理 ====================

@router.get("/projects/{project_id}/spare-parts")
def get_spare_parts(project_id: int, db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """获取项目备件列表"""
    _ensure_after_sales_tables(db)
    parts = db.query(AfterSalesSparePart).filter(AfterSalesSparePart.project_id == project_id).all()
    response = []
    for part in parts:
        inventory = _get_spare_part_inventory(db, part, create=False)
        response.append(
            {
                "id": part.id,
                "part_no": part.part_no,
                "part_name": part.part_name,
                "quantity": part.quantity,
                "min_stock": part.min_stock,
                "unit_price": float(part.unit_price or 0),
                "status": part.status,
                "supplier": part.supplier,
                "inventory_quantity": float(inventory.quantity or 0) if inventory else None,
                "inventory_available_quantity": (
                    float(inventory.available_quantity or 0) if inventory else None
                ),
            }
        )
    return response

@router.post("/projects/{project_id}/spare-parts", status_code=status.HTTP_201_CREATED)
def create_spare_part(project_id: int, part_name: str = Query(...), part_spec: str = Query(""), quantity: int = Query(0), supplier: str = Query(""), part_no: str = Query(""), min_stock: int = Query(1), unit_price: Decimal = Query(Decimal("0")), db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """添加备件"""
    _ensure_after_sales_tables(db)
    normalized_part_no = _query_default(part_no) or f"SP-{project_id}-{datetime.now().strftime('%H%M%S')}"
    min_stock_value = int(_query_default(min_stock) or 1)
    p = AfterSalesSparePart(
        project_id=project_id,
        part_no=normalized_part_no,
        part_name=part_name,
        part_spec=part_spec,
        quantity=quantity,
        min_stock=min_stock_value,
        unit_price=_to_decimal(unit_price),
        supplier=supplier,
        status=_spare_part_status(quantity, min_stock_value),
    )
    db.add(p)
    db.flush()
    inventory = _sync_spare_part_inventory(db, p)
    db.commit()
    db.refresh(p)
    _send_after_sales_notification(
        db,
        project_id=project_id,
        current_user=current_user,
        event="SPARE_PART_CREATED",
        title="备件已添加",
        content=f"项目 {project_id} 新增备件：{part_name}",
        source_type="after_sales_spare_part",
        source_id=p.id,
    )
    return {
        "id": p.id,
        "part_no": p.part_no,
        "quantity": p.quantity,
        "inventory_available_quantity": float(inventory.available_quantity or 0),
    }


@router.post("/projects/{project_id}/spare-parts/{part_id}/issue")
def issue_spare_part(
    project_id: int,
    part_id: int,
    quantity: int = Query(..., gt=0),
    field_service_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """领用备件并同步扣减售后备件台账和库存。"""
    _ensure_after_sales_tables(db)
    part = (
        db.query(AfterSalesSparePart)
        .filter(AfterSalesSparePart.id == part_id, AfterSalesSparePart.project_id == project_id)
        .first()
    )
    if not part:
        raise HTTPException(status_code=404, detail="备件不存在")
    if (part.quantity or 0) < quantity:
        raise HTTPException(status_code=400, detail="备件库存不足")

    inventory = _get_spare_part_inventory(db, part, create=False)
    issue_quantity = _to_decimal(quantity)
    if not inventory or _to_decimal(inventory.available_quantity) < issue_quantity:
        raise HTTPException(status_code=400, detail="库存台账可用数量不足")

    part.quantity = (part.quantity or 0) - quantity
    part.status = _spare_part_status(part.quantity, part.min_stock)
    inventory.quantity = _to_decimal(inventory.quantity) - issue_quantity
    inventory.available_quantity = _to_decimal(inventory.available_quantity) - issue_quantity
    inventory.last_outbound_date = datetime.now()

    field_service = None
    if field_service_id is not None:
        field_service = (
            db.query(AfterSalesFieldService)
            .filter(
                AfterSalesFieldService.id == field_service_id,
                AfterSalesFieldService.project_id == project_id,
            )
            .first()
        )
        if not field_service:
            raise HTTPException(status_code=404, detail="现场服务记录不存在")
        field_service.parts_cost = _to_decimal(field_service.parts_cost) + (
            _to_decimal(part.unit_price) * issue_quantity
        )
        field_service.total_cost = (
            _to_decimal(field_service.travel_cost)
            + _to_decimal(field_service.parts_cost)
            + _to_decimal(field_service.service_fee)
        )
        db.add(field_service)

    db.add(part)
    db.add(inventory)
    db.commit()
    db.refresh(part)
    db.refresh(inventory)
    _send_after_sales_notification(
        db,
        project_id=project_id,
        current_user=current_user,
        event="SPARE_PART_ISSUED",
        title="备件已领用",
        content=f"项目 {project_id} 领用备件 {part.part_name} × {quantity}",
        source_type="after_sales_spare_part",
        source_id=part.id,
    )
    return {
        "id": part.id,
        "part_no": part.part_no,
        "quantity": part.quantity,
        "inventory_available_quantity": float(inventory.available_quantity or 0),
        "field_service_parts_cost": (
            float(field_service.parts_cost or 0) if field_service is not None else None
        ),
    }


# ==================== 现场服务 ====================

@router.get("/projects/{project_id}/field-services")
def get_field_services(project_id: int, db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """获取项目现场服务记录"""
    _ensure_after_sales_tables(db)
    services = db.query(AfterSalesFieldService).filter(AfterSalesFieldService.project_id == project_id).all()
    return [{"id": s.id, "service_no": s.service_no, "service_type": s.service_type, "service_content": s.service_content, "planned_date": str(s.planned_date), "engineer_name": s.engineer_name, "status": s.status, "is_warranty": s.is_warranty, "warranty_source": s.warranty_source, "charge_required": s.charge_required, "charge_reason": s.charge_reason, "charge_status": s.charge_status, "service_fee": float(s.service_fee or 0), "travel_cost": float(s.travel_cost or 0), "parts_cost": float(s.parts_cost or 0), "total_cost": float(s.total_cost or 0), "dispatch_order_id": s.dispatch_order_id} for s in services]

@router.post("/projects/{project_id}/field-services", status_code=status.HTTP_201_CREATED)
def create_field_service(project_id: int, service_type: str = Query(...), service_content: str = Query(...), planned_date: date = Query(...), engineer_name: str = Query(""), engineer_id: Optional[int] = Query(None), is_warranty: Optional[bool] = Query(None), priority: str = Query("NORMAL"), service_fee: Decimal = Query(Decimal("0")), travel_cost: Decimal = Query(Decimal("0")), parts_cost: Decimal = Query(Decimal("0")), db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """创建现场服务记录"""
    _ensure_after_sales_tables(db)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目不存在 (ID: {project_id})")

    engineer_id_value = _query_default(engineer_id)
    engineer_name_value = _query_default(engineer_name) or ""
    if engineer_id_value and not engineer_name_value:
        engineer = db.query(User).filter(User.id == engineer_id_value).first()
        if not engineer:
            raise HTTPException(status_code=404, detail="服务工程师不存在")
        engineer_name_value = engineer.real_name or engineer.username

    warranty_value = _query_default(is_warranty)
    warranty_evaluation = _evaluate_project_warranty(db, project, planned_date)
    warranty_flag = (
        bool(warranty_value)
        if warranty_value is not None
        else bool(warranty_evaluation["is_warranty"])
    )
    service_fee_value = _to_decimal(service_fee)
    travel_cost_value = _to_decimal(travel_cost)
    parts_cost_value = _to_decimal(parts_cost)
    total_cost = service_fee_value + travel_cost_value + parts_cost_value
    charge_required = not warranty_flag
    s = AfterSalesFieldService(
        project_id=project_id,
        customer_id=project.customer_id,
        service_no=f"FS-{project_id}-{datetime.now().strftime('%Y%m%d%H%M')}",
        service_type=service_type,
        service_content=service_content,
        planned_date=planned_date,
        engineer_id=engineer_id_value,
        engineer_name=engineer_name_value,
        status="PLANNED",
        is_warranty=warranty_flag,
        warranty_source=warranty_evaluation["warranty_source"],
        service_fee=service_fee_value,
        travel_cost=travel_cost_value,
        parts_cost=parts_cost_value,
        total_cost=total_cost,
        charge_required=charge_required,
        charge_reason="OUT_OF_WARRANTY" if charge_required else "WARRANTY_COVERED",
        charge_status=_charge_status(charge_required, total_cost),
    )
    db.add(s)
    db.flush()
    dispatch = _create_dispatch_order_for_field_service(
        db,
        project=project,
        field_service=s,
        current_user=current_user,
        priority=_query_default(priority) or "NORMAL",
    )
    db.commit()
    db.refresh(s)
    _send_after_sales_notification(
        db,
        project_id=project_id,
        current_user=current_user,
        event="FIELD_SERVICE_CREATED",
        title="现场服务记录已创建",
        content=f"项目 {project_id} 新增现场服务：{service_type}",
        source_type="after_sales_field_service",
        source_id=s.id,
    )
    return {
        "id": s.id,
        "service_no": s.service_no,
        "dispatch_order_id": dispatch.id,
        "is_warranty": s.is_warranty,
        "warranty_source": s.warranty_source,
        "charge_required": s.charge_required,
        "charge_status": s.charge_status,
        "total_cost": float(s.total_cost or 0),
    }


@router.put("/projects/{project_id}/field-services/{service_id}/status")
def update_field_service_status(
    project_id: int,
    service_id: int,
    service_status: str = Query(..., alias="status"),
    actual_date: Optional[date] = Query(None),
    service_hours: Optional[int] = Query(None),
    report_content: str = Query(""),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """更新现场服务状态，并同步关联安装调试派工单。"""
    _ensure_after_sales_tables(db)
    service = (
        db.query(AfterSalesFieldService)
        .filter(AfterSalesFieldService.id == service_id, AfterSalesFieldService.project_id == project_id)
        .first()
    )
    if not service:
        raise HTTPException(status_code=404, detail="现场服务记录不存在")

    next_status = _query_default(service_status)
    if next_status not in {"PLANNED", "IN_PROGRESS", "COMPLETED", "CANCELLED"}:
        raise HTTPException(status_code=400, detail="现场服务状态无效")

    dispatch = (
        db.query(InstallationDispatchOrder)
        .filter(InstallationDispatchOrder.id == service.dispatch_order_id)
        .first()
        if service.dispatch_order_id
        else None
    )
    if not dispatch:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"项目不存在 (ID: {project_id})")
        dispatch = _create_dispatch_order_for_field_service(
            db,
            project=project,
            field_service=service,
            current_user=current_user,
        )

    service.status = next_status
    actual_date_value = _query_default(actual_date)
    service_hours_value = _query_default(service_hours)
    report_content_value = _query_default(report_content) or ""

    if next_status == "IN_PROGRESS":
        dispatch.status = "IN_PROGRESS"
        dispatch.start_time = dispatch.start_time or datetime.now()
        dispatch.progress = max(dispatch.progress or 0, 10)
    elif next_status == "COMPLETED":
        service.actual_date = actual_date_value or date.today()
        if service_hours_value is not None:
            service.service_hours = service_hours_value
        if report_content_value:
            service.report_content = report_content_value
        dispatch.status = "COMPLETED"
        dispatch.end_time = dispatch.end_time or datetime.now()
        dispatch.progress = 100
        dispatch.actual_hours = (
            _to_decimal(service_hours_value)
            if service_hours_value is not None
            else _to_decimal(service.service_hours)
        )
        dispatch.execution_notes = report_content_value or dispatch.execution_notes
    elif next_status == "CANCELLED":
        dispatch.status = "CANCELLED"
    elif next_status == "PLANNED":
        dispatch.status = "ASSIGNED" if dispatch.assigned_to_id else "PENDING"
        dispatch.progress = 0

    db.add(service)
    db.add(dispatch)
    db.commit()
    db.refresh(service)
    _send_after_sales_notification(
        db,
        project_id=project_id,
        current_user=current_user,
        event="FIELD_SERVICE_UPDATED",
        title="现场服务状态已更新",
        content=f"项目 {project_id} 现场服务状态更新为 {service.status}",
        source_type="after_sales_field_service",
        source_id=service.id,
    )
    return {
        "id": service.id,
        "status": service.status,
        "dispatch_order_id": service.dispatch_order_id,
    }



# ==================== SLA 管理 ====================

@router.get("/projects/{project_id}/sla-stats")
def get_sla_stats(project_id: int, db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """获取项目 SLA 统计"""
    _ensure_after_sales_tables(db)
    from app.models.after_sales import AfterSalesSLA
    sla_records = db.query(AfterSalesSLA).filter(AfterSalesSLA.project_id == project_id).all()
    total = len(sla_records)
    response_met = sum(1 for s in sla_records if s.response_met)
    resolve_met = sum(1 for s in sla_records if s.resolve_met)
    return {
        "total": total,
        "response_met_rate": round(response_met / total * 100, 1) if total else 0,
        "resolve_met_rate": round(resolve_met / total * 100, 1) if total else 0,
        "avg_response_hours": round(sum(s.actual_response_hours or 0 for s in sla_records) / total, 1) if total else 0,
        "avg_resolve_hours": round(sum(s.actual_resolve_hours or 0 for s in sla_records) / total, 1) if total else 0,
    }


# ==================== 客户满意度 ====================

@router.get("/projects/{project_id}/satisfaction")
def get_satisfaction(project_id: int, db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """获取项目满意度统计"""
    _ensure_after_sales_tables(db)
    from app.models.after_sales import AfterSalesSatisfaction
    records = db.query(AfterSalesSatisfaction).filter(AfterSalesSatisfaction.project_id == project_id).all()
    total = len(records)
    if not total:
        return {"total": 0, "avg_overall": 0, "avg_nps": 0}
    return {
        "total": total,
        "avg_overall": round(sum(r.overall_score or 0 for r in records) / total, 1),
        "avg_response": round(sum(r.response_score or 0 for r in records) / total, 1),
        "avg_quality": round(sum(r.quality_score or 0 for r in records) / total, 1),
        "avg_attitude": round(sum(r.attitude_score or 0 for r in records) / total, 1),
        "avg_nps": round(sum(r.nps_score or 0 for r in records) / total, 1),
        "promoters": sum(1 for r in records if (r.nps_score or 0) >= 9),
        "passives": sum(1 for r in records if 7 <= (r.nps_score or 0) <= 8),
        "detractors": sum(1 for r in records if (r.nps_score or 0) <= 6),
    }

@router.post("/projects/{project_id}/satisfaction", status_code=status.HTTP_201_CREATED)
def create_satisfaction(project_id: int, overall_score: int = Query(..., ge=1, le=10), response_score: int = Query(5, ge=1, le=10), quality_score: int = Query(5, ge=1, le=10), attitude_score: int = Query(5, ge=1, le=10), nps_score: int = Query(5, ge=0, le=10), comments: str = Query(""), db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """提交满意度评价"""
    _ensure_after_sales_tables(db)
    from app.models.after_sales import AfterSalesSatisfaction
    s = AfterSalesSatisfaction(project_id=project_id, overall_score=overall_score, response_score=response_score, quality_score=quality_score, attitude_score=attitude_score, nps_score=nps_score, comments=comments)
    db.add(s)
    db.commit()
    db.refresh(s)
    _send_after_sales_notification(
        db,
        project_id=project_id,
        current_user=current_user,
        event="SATISFACTION_CREATED",
        title="满意度评价已提交",
        content=f"项目 {project_id} 新增满意度评价，综合评分 {overall_score}",
        source_type="after_sales_satisfaction",
        source_id=s.id,
    )
    return {"id": s.id, "message": "满意度评价已提交"}


# ==================== 知识库 ====================

@router.get("/knowledge")
def search_knowledge(keyword: str = Query(""), category: str = Query(None), db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """搜索售后知识库"""
    _ensure_after_sales_tables(db)
    from app.models.after_sales import AfterSalesKnowledge
    query = db.query(AfterSalesKnowledge).filter(AfterSalesKnowledge.status == "PUBLISHED")
    if keyword:
        query = query.filter(AfterSalesKnowledge.title.contains(keyword) | AfterSalesKnowledge.keywords.contains(keyword) | AfterSalesKnowledge.content.contains(keyword))
    if category:
        query = query.filter(AfterSalesKnowledge.category == category)
    results = query.order_by(AfterSalesKnowledge.view_count.desc()).limit(20).all()
    return [{"id": k.id, "title": k.title, "category": k.category, "keywords": k.keywords, "view_count": k.view_count, "helpful_count": k.helpful_count} for k in results]

@router.post("/knowledge", status_code=status.HTTP_201_CREATED)
def create_knowledge(title: str = Query(...), category: str = Query("FAQ"), content: str = Query(...), keywords: str = Query(""), project_type: str = Query(""), db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """添加知识库文章"""
    _ensure_after_sales_tables(db)
    from app.models.after_sales import AfterSalesKnowledge
    k = AfterSalesKnowledge(title=title, category=category, content=content, keywords=keywords, project_type=project_type, status="PUBLISHED", created_by=current_user.id)
    db.add(k)
    db.commit()
    db.refresh(k)
    _send_after_sales_notification(
        db,
        project_id=None,
        current_user=current_user,
        event="KNOWLEDGE_CREATED",
        title="售后知识已创建",
        content=f"新增售后知识：{title}",
        source_type="after_sales_knowledge",
        source_id=k.id,
    )
    return {"id": k.id, "message": "知识库文章已创建"}


# ==================== 工单升级 ====================

@router.post("/projects/{project_id}/support-tickets/{ticket_id}/escalate")
def escalate_ticket(project_id: int, ticket_id: int, reason: str = Query(...), db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)):
    """工单升级"""
    _ensure_after_sales_tables(db)
    ticket = db.query(AfterSalesSupportTicket).filter(AfterSalesSupportTicket.id == ticket_id).first()
    service_ticket = None
    if not ticket:
        service_ticket = (
            db.query(ServiceTicket)
            .filter(ServiceTicket.id == ticket_id, ServiceTicket.project_id == project_id)
            .first()
        )
    if not ticket and not service_ticket:
        raise HTTPException(status_code=404, detail="工单不存在")
    # 升级优先级
    priority_order = ["LOW", "MEDIUM", "HIGH", "URGENT"]
    current_priority = ticket.priority if ticket else service_ticket.urgency
    current_idx = priority_order.index(current_priority) if current_priority in priority_order else 0
    new_priority = current_priority
    if current_idx < len(priority_order) - 1:
        new_priority = priority_order[current_idx + 1]
    if ticket:
        ticket.priority = new_priority
        ticket.status = "IN_PROGRESS"
        ticket_no = ticket.ticket_no
        source_id = ticket.id
    else:
        service_ticket.urgency = new_priority
        if service_ticket.status == "PENDING":
            service_ticket.status = "IN_PROGRESS"
        ticket_no = service_ticket.ticket_no
        source_id = service_ticket.id
    db.commit()
    if ticket:
        db.refresh(ticket)
    else:
        db.refresh(service_ticket)
    _send_after_sales_notification(
        db,
        project_id=project_id,
        current_user=current_user,
        event="TICKET_ESCALATED",
        title="售后工单已升级",
        content=f"项目 {project_id} 售后工单 {ticket_no} 已升级：{reason}",
        source_type="after_sales_support_ticket",
        source_id=source_id,
        priority=NotificationPriority.HIGH,
    )
    return {"id": source_id, "new_priority": new_priority, "message": f"工单已升级为 {new_priority}，原因：{reason}"}

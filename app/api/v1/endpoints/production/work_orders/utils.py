# -*- coding: utf-8 -*-
"""
工单管理 - 工具函数
"""
from sqlalchemy.orm import Session

from app.models.production import ProcessDict, Worker, WorkOrder, Workshop, Workstation
from app.models.project import Machine, Project
from app.schemas.production import WorkOrderResponse


def get_work_order_response(db: Session, order: WorkOrder) -> WorkOrderResponse:
    """构建工单响应对象的辅助函数"""
    project_name = None
    if order.project_id:
        project = db.query(Project).filter(Project.id == order.project_id).first()
        project_name = project.project_name if project else None

    machine_name = None
    if order.machine_id:
        machine = db.query(Machine).filter(Machine.id == order.machine_id).first()
        machine_name = machine.machine_name if machine else None

    workshop_name = None
    if order.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == order.workshop_id).first()
        workshop_name = workshop.workshop_name if workshop else None

    workstation_name = None
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        workstation_name = workstation.workstation_name if workstation else None

    process_name = None
    if order.process_id:
        process = db.query(ProcessDict).filter(ProcessDict.id == order.process_id).first()
        process_name = process.process_name if process else None

    assigned_worker_name = None
    if order.assigned_to:
        worker = db.query(Worker).filter(Worker.id == order.assigned_to).first()
        assigned_worker_name = worker.worker_name if worker else None

    return WorkOrderResponse(
        id=order.id,
        work_order_no=order.work_order_no,
        task_name=order.task_name,
        task_type=order.task_type,
        project_id=order.project_id,
        project_name=project_name,
        machine_id=order.machine_id,
        machine_name=machine_name,
        production_plan_id=order.production_plan_id,
        process_id=order.process_id,
        process_name=process_name,
        workshop_id=order.workshop_id,
        workshop_name=workshop_name,
        workstation_id=order.workstation_id,
        workstation_name=workstation_name,
        material_name=order.material_name,
        specification=order.specification,
        plan_qty=order.plan_qty or 0,
        completed_qty=order.completed_qty or 0,
        qualified_qty=order.qualified_qty or 0,
        defect_qty=order.defect_qty or 0,
        standard_hours=float(order.standard_hours) if order.standard_hours else None,
        actual_hours=float(order.actual_hours) if order.actual_hours else 0,
        plan_start_date=order.plan_start_date,
        plan_end_date=order.plan_end_date,
        actual_start_time=order.actual_start_time,
        actual_end_time=order.actual_end_time,
        assigned_to=order.assigned_to,
        assigned_worker_name=assigned_worker_name,
        status=order.status,
        priority=order.priority,
        progress=order.progress or 0,
        work_content=order.work_content,
        remark=order.remark,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )

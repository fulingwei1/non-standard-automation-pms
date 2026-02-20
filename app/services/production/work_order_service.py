# -*- coding: utf-8 -*-
"""
工单管理服务

处理工单验证、创建、响应构建、派工（单个和批量）等业务逻辑。
"""
from datetime import datetime
from typing import List

from fastapi import HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.common.query_filters import apply_pagination
from app.models.production import (
    ProcessDict,
    ProductionPlan,
    Worker,
    WorkOrder,
    Workshop,
    Workstation,
)
from app.models.project import Machine, Project
from app.schemas.production import WorkOrderResponse
from app.utils.db_helpers import get_or_404, save_obj


class WorkOrderService:
    """工单管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def build_response(self, order: WorkOrder) -> WorkOrderResponse:
        """构建工单响应对象"""
        project_name = None
        if order.project_id:
            project = self.db.query(Project).filter(Project.id == order.project_id).first()
            project_name = project.project_name if project else None

        machine_name = None
        if order.machine_id:
            machine = self.db.query(Machine).filter(Machine.id == order.machine_id).first()
            machine_name = machine.machine_name if machine else None

        workshop_name = None
        if order.workshop_id:
            workshop = self.db.query(Workshop).filter(Workshop.id == order.workshop_id).first()
            workshop_name = workshop.workshop_name if workshop else None

        workstation_name = None
        if order.workstation_id:
            workstation = self.db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
            workstation_name = workstation.workstation_name if workstation else None

        process_name = None
        if order.process_id:
            process = self.db.query(ProcessDict).filter(ProcessDict.id == order.process_id).first()
            process_name = process.process_name if process else None

        assigned_worker_name = None
        if order.assigned_to:
            worker = self.db.query(Worker).filter(Worker.id == order.assigned_to).first()
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

    def list_work_orders(
        self,
        pagination,
        project_id=None,
        workshop_id=None,
        status=None,
        priority=None,
        assigned_to=None,
    ) -> dict:
        """查询工单列表"""
        query = self.db.query(WorkOrder)

        if project_id:
            query = query.filter(WorkOrder.project_id == project_id)
        if workshop_id:
            query = query.filter(WorkOrder.workshop_id == workshop_id)
        if status:
            query = query.filter(WorkOrder.status == status)
        if priority:
            query = query.filter(WorkOrder.priority == priority)
        if assigned_to:
            query = query.filter(WorkOrder.assigned_to == assigned_to)

        total = query.count()
        orders = apply_pagination(
            query.order_by(desc(WorkOrder.created_at)),
            pagination.offset,
            pagination.limit,
        ).all()

        items = [self.build_response(order) for order in orders]
        return pagination.to_response(items, total)

    def create_work_order(self, order_in, current_user_id: int) -> WorkOrderResponse:
        """创建工单"""
        from app.api.v1.endpoints.production.utils import generate_work_order_no

        # 验证关联实体
        if order_in.project_id:
            get_or_404(self.db, Project, order_in.project_id, "项目不存在")
        if order_in.machine_id:
            get_or_404(self.db, Machine, order_in.machine_id, "机台不存在")
        if order_in.production_plan_id:
            get_or_404(self.db, ProductionPlan, order_in.production_plan_id, "生产计划不存在")
        if order_in.workshop_id:
            get_or_404(self.db, Workshop, order_in.workshop_id, "车间不存在")
        if order_in.workstation_id:
            workstation = get_or_404(self.db, Workstation, order_in.workstation_id, "工位不存在")
            if workstation.workshop_id != order_in.workshop_id:
                raise HTTPException(status_code=400, detail="工位不属于该车间")

        work_order_no = generate_work_order_no(self.db)

        order = WorkOrder(
            work_order_no=work_order_no,
            status="PENDING",
            progress=0,
            completed_qty=0,
            qualified_qty=0,
            defect_qty=0,
            actual_hours=0,
            created_by=current_user_id,
            **order_in.model_dump(),
        )
        save_obj(self.db, order)

        return self.build_response(order)

    def get_work_order(self, order_id: int) -> WorkOrderResponse:
        """获取工单详情"""
        order = get_or_404(self.db, WorkOrder, order_id, detail="工单不存在")
        return self.build_response(order)

    def assign_work_order(
        self,
        order_id: int,
        assign_in,
        current_user_id: int,
    ) -> WorkOrderResponse:
        """任务派工（指派人员/工位）"""
        order = get_or_404(self.db, WorkOrder, order_id, detail="工单不存在")

        if order.status != "PENDING":
            raise HTTPException(status_code=400, detail="只有待派工状态的工单才能派工")

        # 检查工人是否存在
        get_or_404(self.db, Worker, assign_in.assigned_to, "工人不存在")

        # 检查工位是否存在
        if assign_in.workstation_id:
            workstation = get_or_404(self.db, Workstation, assign_in.workstation_id, "工位不存在")
            if order.workshop_id and workstation.workshop_id != order.workshop_id:
                raise HTTPException(status_code=400, detail="工位不属于该车间")

        order.assigned_to = assign_in.assigned_to
        order.assigned_at = datetime.now()
        order.assigned_by = current_user_id
        order.status = "ASSIGNED"

        if assign_in.workstation_id:
            order.workstation_id = assign_in.workstation_id

        save_obj(self.db, order)
        return self.build_response(order)

    def batch_assign(
        self,
        order_ids: List[int],
        assign_in,
        current_user_id: int,
    ) -> dict:
        """批量派工"""
        success_count = 0
        failed_orders = []

        for order_id in order_ids:
            try:
                order = self.db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
                if not order:
                    failed_orders.append({"order_id": order_id, "reason": "工单不存在"})
                    continue

                if order.status != "PENDING":
                    failed_orders.append(
                        {"order_id": order_id, "reason": f"工单状态为{order.status}，不能派工"}
                    )
                    continue

                # 验证工人
                if assign_in.assigned_to:
                    worker = self.db.query(Worker).filter(Worker.id == assign_in.assigned_to).first()
                    if not worker:
                        failed_orders.append({"order_id": order_id, "reason": "工人不存在"})
                        continue
                    order.assigned_to = assign_in.assigned_to
                    order.assigned_to_name = worker.worker_name

                # 验证工位
                if assign_in.workstation_id:
                    workstation = (
                        self.db.query(Workstation)
                        .filter(Workstation.id == assign_in.workstation_id)
                        .first()
                    )
                    if not workstation:
                        failed_orders.append({"order_id": order_id, "reason": "工位不存在"})
                        continue
                    order.workstation_id = assign_in.workstation_id

                order.status = "ASSIGNED"
                order.assigned_at = datetime.now()
                order.assigned_by = current_user_id

                self.db.add(order)
                success_count += 1
            except Exception as e:
                failed_orders.append({"order_id": order_id, "reason": str(e)})

        self.db.commit()

        return {
            "code": 200,
            "message": f"批量派工完成：成功 {success_count} 个，失败 {len(failed_orders)} 个",
            "data": {"success_count": success_count, "failed_orders": failed_orders},
        }

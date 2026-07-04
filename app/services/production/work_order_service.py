# -*- coding: utf-8 -*-
"""
工单管理服务

处理工单验证、创建、响应构建、派工（单个和批量）等业务逻辑。
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.common import query_filters
from app.models.production import (
    ProcessDict,
    ProductionPlan,
    Worker,
    WorkOrder,
    Workshop,
    Workstation,
)
from app.models.material import BomHeader, BomItem
from app.models.project import Machine, Project
from app.models.shortage import WorkOrderBom
from app.schemas.production import WorkOrderResponse
from app.utils import db_helpers


def get_or_404(*args, **kwargs):
    """Compatibility wrapper for older tests that patch this module directly."""
    return db_helpers.get_or_404(*args, **kwargs)


def save_obj(*args, **kwargs):
    """Compatibility wrapper for older tests that patch db_helpers.save_obj."""
    return db_helpers.save_obj(*args, **kwargs)


class WorkOrderService:
    """工单管理服务"""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _optional_int(value) -> Optional[int]:
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        return None

    @staticmethod
    def _optional_str(value) -> Optional[str]:
        if isinstance(value, str):
            return value
        return None

    # ------------------------------------------------------------------
    # Internal helpers for batch-loading related name maps
    # ------------------------------------------------------------------

    def _fetch_project_map(self, ids: List[int]) -> Dict[int, str]:
        if not ids:
            return {}
        rows = self.db.query(Project.id, Project.project_name).filter(Project.id.in_(ids)).all()
        return {r.id: r.project_name for r in rows}

    def _fetch_machine_map(self, ids: List[int]) -> Dict[int, str]:
        if not ids:
            return {}
        rows = self.db.query(Machine.id, Machine.machine_name).filter(Machine.id.in_(ids)).all()
        return {r.id: r.machine_name for r in rows}

    def _fetch_workshop_map(self, ids: List[int]) -> Dict[int, str]:
        if not ids:
            return {}
        rows = self.db.query(Workshop.id, Workshop.workshop_name).filter(Workshop.id.in_(ids)).all()
        return {r.id: r.workshop_name for r in rows}

    def _fetch_workstation_map(self, ids: List[int]) -> Dict[int, str]:
        if not ids:
            return {}
        rows = (
            self.db.query(Workstation.id, Workstation.workstation_name)
            .filter(Workstation.id.in_(ids))
            .all()
        )
        return {r.id: r.workstation_name for r in rows}

    def _fetch_process_map(self, ids: List[int]) -> Dict[int, str]:
        if not ids:
            return {}
        rows = (
            self.db.query(ProcessDict.id, ProcessDict.process_name)
            .filter(ProcessDict.id.in_(ids))
            .all()
        )
        return {r.id: r.process_name for r in rows}

    def _fetch_worker_map(self, ids: List[int]) -> Dict[int, str]:
        if not ids:
            return {}
        rows = self.db.query(Worker.id, Worker.worker_name).filter(Worker.id.in_(ids)).all()
        return {r.id: r.worker_name for r in rows}

    # ------------------------------------------------------------------
    # Response builder
    # ------------------------------------------------------------------

    def build_response(
        self,
        order: WorkOrder,
        *,
        project_map: Optional[Dict[int, str]] = None,
        machine_map: Optional[Dict[int, str]] = None,
        workshop_map: Optional[Dict[int, str]] = None,
        workstation_map: Optional[Dict[int, str]] = None,
        process_map: Optional[Dict[int, str]] = None,
        worker_map: Optional[Dict[int, str]] = None,
    ) -> WorkOrderResponse:
        """构建工单响应对象。

        当调用方传入预构建的名称映射字典时，直接从字典中查找，避免 N+1 查询。
        未传入时退回到单条查询（兼容单记录场景）。
        """
        # project_name
        if project_map is not None:
            project_name = project_map.get(order.project_id) if order.project_id else None
        else:
            project_name = None
            if order.project_id:
                project = self.db.query(Project).filter(Project.id == order.project_id).first()
                project_name = project.project_name if project else None

        # machine_name
        if machine_map is not None:
            machine_name = machine_map.get(order.machine_id) if order.machine_id else None
        else:
            machine_name = None
            if order.machine_id:
                machine = self.db.query(Machine).filter(Machine.id == order.machine_id).first()
                machine_name = machine.machine_name if machine else None

        # workshop_name
        if workshop_map is not None:
            workshop_name = workshop_map.get(order.workshop_id) if order.workshop_id else None
        else:
            workshop_name = None
            if order.workshop_id:
                workshop = self.db.query(Workshop).filter(Workshop.id == order.workshop_id).first()
                workshop_name = workshop.workshop_name if workshop else None

        # workstation_name
        if workstation_map is not None:
            workstation_name = (
                workstation_map.get(order.workstation_id) if order.workstation_id else None
            )
        else:
            workstation_name = None
            if order.workstation_id:
                workstation = (
                    self.db.query(Workstation)
                    .filter(Workstation.id == order.workstation_id)
                    .first()
                )
                workstation_name = workstation.workstation_name if workstation else None

        # process_name
        if process_map is not None:
            process_name = process_map.get(order.process_id) if order.process_id else None
        else:
            process_name = None
            if order.process_id:
                process = (
                    self.db.query(ProcessDict).filter(ProcessDict.id == order.process_id).first()
                )
                process_name = process.process_name if process else None

        # assigned_worker_name
        if worker_map is not None:
            assigned_worker_name = worker_map.get(order.assigned_to) if order.assigned_to else None
        else:
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
            bom_id=self._optional_int(getattr(order, "bom_id", None)),
            bom_no=self._optional_str(getattr(order, "bom_no", None)),
            bom_version=self._optional_str(getattr(order, "bom_version", None)),
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
        orders = query_filters.apply_pagination(
            query.order_by(desc(WorkOrder.created_at)),
            pagination.offset,
            pagination.limit,
        ).all()

        items = [self.build_response(order) for order in orders]
        return pagination.to_response(items, total)

    def create_work_order(self, order_in, current_user_id: int) -> WorkOrderResponse:
        """创建工单"""
        from app.api.v1.endpoints.production.utils import generate_work_order_no

        # 日期合法性校验：计划结束日期不能早于计划开始日期
        plan_start_date = getattr(order_in, "plan_start_date", None)
        plan_end_date = getattr(order_in, "plan_end_date", None)
        if isinstance(plan_start_date, date) and isinstance(plan_end_date, date):
            if plan_end_date < plan_start_date:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"计划结束日期（{plan_end_date}）"
                        f"不能早于计划开始日期（{plan_start_date}）。"
                    ),
                )

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

        order_data = order_in.model_dump()
        bom = None
        bom_id = order_data.get("bom_id")
        if isinstance(bom_id, int) and not isinstance(bom_id, bool):
            bom = get_or_404(self.db, BomHeader, bom_id, "BOM不存在")
            if order_in.project_id and bom.project_id != order_in.project_id:
                raise HTTPException(status_code=400, detail="BOM不属于该项目")
            if order_in.machine_id and bom.machine_id and bom.machine_id != order_in.machine_id:
                raise HTTPException(status_code=400, detail="BOM不属于该机台")
            order_data["bom_no"] = bom.bom_no
            order_data["bom_version"] = bom.version

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
            **order_data,
        )
        if bom:
            self.db.add(order)
            self.db.flush()
            self._replace_bom_snapshot(order, bom)
            self.db.commit()
            self.db.refresh(order)
        else:
            save_obj(self.db, order)

        return self.build_response(order)

    def _replace_bom_snapshot(self, order: WorkOrder, bom: BomHeader) -> None:
        """将发布时点的 BOM 明细固化为工单 BOM 快照。"""
        self.db.query(WorkOrderBom).filter(
            WorkOrderBom.work_order_id == order.id
        ).delete(synchronize_session=False)

        items = (
            self.db.query(BomItem)
            .filter(BomItem.bom_id == bom.id)
            .order_by(BomItem.item_no, BomItem.id)
            .all()
        )
        plan_qty = Decimal(str(order.plan_qty or 1))
        fallback_required_date = order.plan_start_date or order.plan_end_date or date.today()

        for item in items:
            bom_qty = Decimal(str(item.quantity or 0))
            material_type = (item.source_type or "PURCHASE").lower()
            lead_time = 0
            if item.material and item.material.lead_time_days is not None:
                lead_time = item.material.lead_time_days

            self.db.add(
                WorkOrderBom(
                    work_order_id=order.id,
                    work_order_no=order.work_order_no,
                    project_id=order.project_id,
                    material_id=item.material_id,
                    material_code=item.material_code,
                    material_name=item.material_name,
                    specification=item.specification,
                    unit=item.unit or "件",
                    bom_qty=bom_qty,
                    required_qty=bom_qty * plan_qty,
                    required_date=item.required_date or fallback_required_date,
                    material_type=material_type,
                    lead_time=lead_time,
                    is_key_material=bool(item.is_key_item),
                )
            )

    def get_work_order(self, order_id: int) -> WorkOrderResponse:
        """获取工单详情"""
        order = get_or_404(self.db, WorkOrder, order_id, detail="工单不存在")
        return self.build_response(order)

    def update_work_order(self, order_id: int, order_in) -> WorkOrderResponse:
        """更新工单（兼容前端 PUT /production/work-orders/{id}）"""
        order = get_or_404(self.db, WorkOrder, order_id, detail="工单不存在")

        update_data = order_in.model_dump(exclude_unset=True)
        snapshot_bom = None
        clear_snapshot = False

        if "workshop_id" in update_data and update_data["workshop_id"]:
            get_or_404(self.db, Workshop, update_data["workshop_id"], "车间不存在")

        if "assigned_to" in update_data and update_data["assigned_to"]:
            get_or_404(self.db, Worker, update_data["assigned_to"], "工人不存在")

        workstation_id = update_data.get("workstation_id")
        if workstation_id:
            workstation = get_or_404(self.db, Workstation, workstation_id, "工位不存在")
            target_workshop_id = update_data.get("workshop_id", order.workshop_id)
            if target_workshop_id and workstation.workshop_id != target_workshop_id:
                raise HTTPException(status_code=400, detail="工位不属于该车间")

        if "bom_id" in update_data:
            bom_id = update_data["bom_id"]
            if bom_id is None:
                update_data["bom_no"] = None
                update_data["bom_version"] = None
                clear_snapshot = True
            elif isinstance(bom_id, int) and not isinstance(bom_id, bool):
                snapshot_bom = get_or_404(self.db, BomHeader, bom_id, "BOM不存在")
                if order.project_id and snapshot_bom.project_id != order.project_id:
                    raise HTTPException(status_code=400, detail="BOM不属于该项目")
                if order.machine_id and snapshot_bom.machine_id and snapshot_bom.machine_id != order.machine_id:
                    raise HTTPException(status_code=400, detail="BOM不属于该机台")
                update_data["bom_no"] = snapshot_bom.bom_no
                update_data["bom_version"] = snapshot_bom.version
            else:
                raise HTTPException(status_code=400, detail="BOM ID格式不正确")

        for field, value in update_data.items():
            if hasattr(order, field):
                setattr(order, field, value)

        if snapshot_bom or clear_snapshot:
            self.db.add(order)
            self.db.flush()
            if clear_snapshot:
                self.db.query(WorkOrderBom).filter(
                    WorkOrderBom.work_order_id == order.id
                ).delete(synchronize_session=False)
            else:
                self._replace_bom_snapshot(order, snapshot_bom)
            self.db.commit()
            self.db.refresh(order)
        else:
            save_obj(self.db, order)
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
                    worker = (
                        self.db.query(Worker).filter(Worker.id == assign_in.assigned_to).first()
                    )
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

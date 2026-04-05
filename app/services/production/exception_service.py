# -*- coding: utf-8 -*-
"""生产异常兼容服务。"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.common.query_filters import apply_pagination
from app.models.production import Equipment, ProductionException, WorkOrder, Workshop
from app.models.project import Project
from app.models.user import User
from app.schemas.production import ProductionExceptionResponse
from app.utils.db_helpers import get_or_404, save_obj


class ProductionExceptionService:
    """生产异常 CRUD / 处理 / 关闭兼容服务。"""

    def __init__(self, db: Session):
        self.db = db

    def _generate_exception_no(self) -> str:
        return f"PEX-{datetime.now():%Y%m%d%H%M%S%f}"

    def _build_response(self, exception: ProductionException) -> ProductionExceptionResponse:
        work_order_no = None
        if exception.work_order_id:
            work_order = self.db.query(WorkOrder).filter(WorkOrder.id == exception.work_order_id).first()
            work_order_no = work_order.work_order_no if work_order else None

        project_name = None
        if exception.project_id:
            project = self.db.query(Project).filter(Project.id == exception.project_id).first()
            project_name = project.project_name if project else None

        workshop_name = None
        if exception.workshop_id:
            workshop = self.db.query(Workshop).filter(Workshop.id == exception.workshop_id).first()
            workshop_name = workshop.workshop_name if workshop else None

        equipment_name = None
        if exception.equipment_id:
            equipment = self.db.query(Equipment).filter(Equipment.id == exception.equipment_id).first()
            equipment_name = equipment.equipment_name if equipment else None

        reporter_name = None
        reporter = self.db.query(User).filter(User.id == exception.reporter_id).first()
        if reporter:
            reporter_name = reporter.real_name or reporter.username

        handler_name = None
        if exception.handler_id:
            handler = self.db.query(User).filter(User.id == exception.handler_id).first()
            handler_name = (handler.real_name or handler.username) if handler else None

        return ProductionExceptionResponse(
            id=exception.id,
            exception_no=exception.exception_no,
            exception_type=exception.exception_type,
            exception_level=exception.exception_level,
            title=exception.title,
            description=exception.description,
            work_order_id=exception.work_order_id,
            work_order_no=work_order_no,
            project_id=exception.project_id,
            project_name=project_name,
            workshop_id=exception.workshop_id,
            workshop_name=workshop_name,
            equipment_id=exception.equipment_id,
            equipment_name=equipment_name,
            reporter_id=exception.reporter_id,
            reporter_name=reporter_name,
            report_time=exception.report_time,
            status=exception.status,
            handler_id=exception.handler_id,
            handler_name=handler_name,
            handle_plan=exception.handle_plan,
            handle_result=exception.handle_result,
            handle_time=exception.handle_time,
            resolved_at=exception.resolved_at,
            impact_hours=exception.impact_hours,
            impact_cost=exception.impact_cost,
            remark=exception.remark,
            created_at=exception.created_at,
            updated_at=exception.updated_at,
        )

    def _validate_refs(self, *, work_order_id=None, project_id=None, workshop_id=None, equipment_id=None):
        if work_order_id:
            get_or_404(self.db, WorkOrder, work_order_id, "关联工单不存在")
        if project_id:
            get_or_404(self.db, Project, project_id, "关联项目不存在")
        if workshop_id:
            get_or_404(self.db, Workshop, workshop_id, "关联车间不存在")
        if equipment_id:
            get_or_404(self.db, Equipment, equipment_id, "关联设备不存在")

    def list_exceptions(
        self,
        pagination,
        *,
        search: Optional[str] = None,
        exception_type: Optional[str] = None,
        exception_level: Optional[str] = None,
        status: Optional[str] = None,
        project_id: Optional[int] = None,
        work_order_id: Optional[int] = None,
    ) -> dict:
        query = self.db.query(ProductionException)

        if search:
            like = f"%{search.strip()}%"
            query = query.filter(
                ProductionException.exception_no.ilike(like)
                | ProductionException.title.ilike(like)
                | ProductionException.description.ilike(like)
            )
        if exception_type:
            query = query.filter(ProductionException.exception_type == exception_type)
        if exception_level:
            query = query.filter(ProductionException.exception_level == exception_level)
        if status:
            query = query.filter(ProductionException.status == status)
        if project_id:
            query = query.filter(ProductionException.project_id == project_id)
        if work_order_id:
            query = query.filter(ProductionException.work_order_id == work_order_id)

        total = query.count()
        exceptions = apply_pagination(
            query.order_by(desc(ProductionException.report_time)),
            pagination.offset,
            pagination.limit,
        ).all()
        items = [self._build_response(item) for item in exceptions]
        return pagination.to_response(items, total)

    def create_exception(self, exception_in, reporter_id: int) -> ProductionExceptionResponse:
        self._validate_refs(
            work_order_id=exception_in.work_order_id,
            project_id=exception_in.project_id,
            workshop_id=exception_in.workshop_id,
            equipment_id=exception_in.equipment_id,
        )

        exception = ProductionException(
            exception_no=self._generate_exception_no(),
            exception_type=exception_in.exception_type,
            exception_level=exception_in.exception_level,
            title=exception_in.title,
            description=exception_in.description,
            work_order_id=exception_in.work_order_id,
            project_id=exception_in.project_id,
            workshop_id=exception_in.workshop_id,
            equipment_id=exception_in.equipment_id,
            reporter_id=reporter_id,
            report_time=datetime.now(),
            status="REPORTED",
            impact_hours=Decimal(str(exception_in.impact_hours)) if exception_in.impact_hours is not None else None,
            impact_cost=Decimal(str(exception_in.impact_cost)) if exception_in.impact_cost is not None else None,
            remark=exception_in.remark,
        )
        save_obj(self.db, exception)
        return self._build_response(exception)

    def get_exception(self, exception_id: int) -> ProductionExceptionResponse:
        exception = get_or_404(self.db, ProductionException, exception_id, detail="生产异常不存在")
        return self._build_response(exception)

    def handle_exception(self, exception_id: int, handle_in, current_user_id: int) -> ProductionExceptionResponse:
        exception = get_or_404(self.db, ProductionException, exception_id, detail="生产异常不存在")

        if exception.status == "CLOSED":
            raise HTTPException(status_code=400, detail="已关闭的异常不能再次处理")

        if handle_in.handle_plan is not None:
            exception.handle_plan = handle_in.handle_plan
        if handle_in.handle_result is not None:
            exception.handle_result = handle_in.handle_result

        exception.handler_id = current_user_id
        exception.handle_time = datetime.now()
        exception.status = "RESOLVED" if exception.handle_result else "IN_PROGRESS"
        if exception.status == "RESOLVED":
            exception.resolved_at = datetime.now()

        save_obj(self.db, exception)
        return self._build_response(exception)

    def resolve_exception(self, exception_id: int, handle_in, current_user_id: int) -> ProductionExceptionResponse:
        exception = get_or_404(self.db, ProductionException, exception_id, detail="生产异常不存在")

        if exception.status == "CLOSED":
            raise HTTPException(status_code=400, detail="已关闭的异常不能再次解决")

        if handle_in.handle_plan is not None:
            exception.handle_plan = handle_in.handle_plan
        if handle_in.handle_result is not None:
            exception.handle_result = handle_in.handle_result

        exception.handler_id = current_user_id
        exception.handle_time = datetime.now()
        exception.resolved_at = datetime.now()
        exception.status = "RESOLVED"

        save_obj(self.db, exception)
        return self._build_response(exception)

    def close_exception(self, exception_id: int, current_user_id: int) -> ProductionExceptionResponse:
        exception = get_or_404(self.db, ProductionException, exception_id, detail="生产异常不存在")

        if exception.status == "CLOSED":
            return self._build_response(exception)

        if exception.status not in {"RESOLVED", "IN_PROGRESS", "REPORTED"}:
            raise HTTPException(status_code=400, detail="当前状态不允许关闭")

        exception.handler_id = exception.handler_id or current_user_id
        exception.resolved_at = exception.resolved_at or datetime.now()
        exception.status = "CLOSED"

        save_obj(self.db, exception)
        return self._build_response(exception)

# -*- coding: utf-8 -*-
"""生产工人兼容服务。"""
from datetime import date
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.common.date_range import get_month_range
from app.common.query_filters import apply_pagination
from app.models.production import Worker, WorkReport, Workshop
from app.models.user import User
from app.schemas.production import WorkerResponse, WorkerPerformanceReportResponse
from app.utils.db_helpers import get_or_404, save_obj


class WorkerService:
    """工人管理兼容服务。"""

    def __init__(self, db: Session):
        self.db = db

    def _build_worker_response(self, worker: Worker) -> WorkerResponse:
        workshop_name = None
        if worker.workshop_id:
            workshop = self.db.query(Workshop).filter(Workshop.id == worker.workshop_id).first()
            workshop_name = workshop.workshop_name if workshop else None

        email = None
        if worker.user_id:
            user = self.db.query(User).filter(User.id == worker.user_id).first()
            email = user.email if user else None

        return WorkerResponse(
            id=worker.id,
            worker_code=worker.worker_no,
            worker_name=worker.worker_name,
            user_id=worker.user_id,
            workshop_id=worker.workshop_id,
            workshop_name=workshop_name,
            worker_type=worker.position,
            phone=worker.phone,
            email=email,
            skill_level=worker.skill_level,
            hire_date=worker.entry_date,
            status=worker.status,
            is_active=worker.is_active,
            remark=worker.remark,
            created_at=worker.created_at,
            updated_at=worker.updated_at,
        )

    def list_workers(
        self,
        pagination,
        *,
        search: Optional[str] = None,
        workshop_id: Optional[int] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> dict:
        query = self.db.query(Worker)

        if search:
            like = f"%{search.strip()}%"
            query = query.filter(
                Worker.worker_no.ilike(like)
                | Worker.worker_name.ilike(like)
                | Worker.phone.ilike(like)
            )

        if workshop_id:
            query = query.filter(Worker.workshop_id == workshop_id)
        if status:
            query = query.filter(Worker.status == status)
        if is_active is not None:
            query = query.filter(Worker.is_active == is_active)

        total = query.count()
        workers = apply_pagination(
            query.order_by(desc(Worker.created_at)),
            pagination.offset,
            pagination.limit,
        ).all()
        items = [self._build_worker_response(worker) for worker in workers]
        return pagination.to_response(items, total)

    def create_worker(self, worker_in) -> WorkerResponse:
        worker_code = (worker_in.worker_code or "").strip()
        if not worker_code:
            raise HTTPException(status_code=400, detail="工人编码不能为空")

        existing = self.db.query(Worker).filter(Worker.worker_no == worker_code).first()
        if existing:
            raise HTTPException(status_code=400, detail="工人编码已存在")

        if worker_in.user_id:
            get_or_404(self.db, User, worker_in.user_id, "关联用户不存在")
        if worker_in.workshop_id:
            get_or_404(self.db, Workshop, worker_in.workshop_id, "所属车间不存在")

        worker = Worker(
            worker_no=worker_code,
            worker_name=worker_in.worker_name,
            user_id=worker_in.user_id,
            workshop_id=worker_in.workshop_id,
            position=worker_in.worker_type,
            phone=worker_in.phone,
            entry_date=worker_in.hire_date,
            skill_level=worker_in.skill_level or "JUNIOR",
            status=worker_in.status or "ACTIVE",
            is_active=worker_in.is_active,
            remark=worker_in.remark,
        )
        save_obj(self.db, worker)
        return self._build_worker_response(worker)

    def get_worker(self, worker_id: int) -> WorkerResponse:
        worker = get_or_404(self.db, Worker, worker_id, detail="工人不存在")
        return self._build_worker_response(worker)

    def update_worker(self, worker_id: int, worker_in) -> WorkerResponse:
        worker = get_or_404(self.db, Worker, worker_id, detail="工人不存在")

        update_data = worker_in.model_dump(exclude_unset=True)

        if "worker_code" in update_data:
            worker_code = (update_data.pop("worker_code") or "").strip()
            if not worker_code:
                raise HTTPException(status_code=400, detail="工人编码不能为空")
            existing = (
                self.db.query(Worker)
                .filter(Worker.worker_no == worker_code, Worker.id != worker_id)
                .first()
            )
            if existing:
                raise HTTPException(status_code=400, detail="工人编码已存在")
            worker.worker_no = worker_code

        if "user_id" in update_data and update_data["user_id"]:
            get_or_404(self.db, User, update_data["user_id"], "关联用户不存在")
        if "workshop_id" in update_data and update_data["workshop_id"]:
            get_or_404(self.db, Workshop, update_data["workshop_id"], "所属车间不存在")

        if "worker_type" in update_data:
            worker.position = update_data.pop("worker_type")
        if "hire_date" in update_data:
            worker.entry_date = update_data.pop("hire_date")
        if "skill_level" in update_data:
            worker.skill_level = update_data.pop("skill_level")

        for field, value in update_data.items():
            if hasattr(worker, field):
                setattr(worker, field, value)

        save_obj(self.db, worker)
        return self._build_worker_response(worker)

    def get_worker_performance(
        self,
        worker_id: int,
        *,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
    ) -> WorkerPerformanceReportResponse:
        worker = get_or_404(self.db, Worker, worker_id, detail="工人不存在")

        if not period_start or not period_end:
            today = date.today()
            default_start, default_end = get_month_range(today)
            period_start = period_start or default_start
            period_end = period_end or default_end

        report_query = self.db.query(WorkReport).filter(WorkReport.worker_id == worker_id)
        report_query = report_query.filter(func.date(WorkReport.report_time) >= period_start)
        report_query = report_query.filter(func.date(WorkReport.report_time) <= period_end)
        reports = report_query.all()

        total_hours = sum(float(report.work_hours or 0) for report in reports)
        total_reports = len(reports)
        completed_orders = len(
            {
                report.work_order_id
                for report in reports
                if report.report_type == "COMPLETE" or (report.completed_qty or 0) > 0
            }
        )
        total_completed_qty = sum(int(report.completed_qty or 0) for report in reports)
        total_qualified_qty = sum(int(report.qualified_qty or 0) for report in reports)

        workshop_name = None
        if worker.workshop_id:
            workshop = self.db.query(Workshop).filter(Workshop.id == worker.workshop_id).first()
            workshop_name = workshop.workshop_name if workshop else None

        average_efficiency = 0.0
        if total_hours > 0:
            average_efficiency = round(total_qualified_qty / total_hours, 2)

        return WorkerPerformanceReportResponse(
            worker_id=worker.id,
            worker_code=worker.worker_no,
            worker_name=worker.worker_name,
            workshop_id=worker.workshop_id,
            workshop_name=workshop_name,
            period_start=period_start,
            period_end=period_end,
            total_hours=round(total_hours, 2),
            total_reports=total_reports,
            completed_orders=completed_orders,
            total_completed_qty=total_completed_qty,
            total_qualified_qty=total_qualified_qty,
            average_efficiency=average_efficiency,
        )

# -*- coding: utf-8 -*-
"""
车间管理服务

处理车间响应构建、产能计算、车间验证等业务逻辑。
"""
from datetime import date
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.common.date_range import get_month_range
from app.common.query_filters import apply_pagination
from app.models.production import ProductionDailyReport, WorkOrder, Workshop
from app.models.user import User
from app.schemas.production import WorkshopResponse
from app.utils.db_helpers import get_or_404, save_obj


class WorkshopService:
    """车间管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def _build_workshop_response(self, workshop: Workshop) -> WorkshopResponse:
        """构建车间响应（含主管名称查询）"""
        manager_name = None
        if workshop.manager_id:
            manager = self.db.query(User).filter(User.id == workshop.manager_id).first()
            manager_name = manager.real_name if manager else None

        return WorkshopResponse(
            id=workshop.id,
            workshop_code=workshop.workshop_code,
            workshop_name=workshop.workshop_name,
            workshop_type=workshop.workshop_type,
            manager_id=workshop.manager_id,
            manager_name=manager_name,
            location=workshop.location,
            capacity_hours=float(workshop.capacity_hours) if workshop.capacity_hours else None,
            description=workshop.description,
            is_active=workshop.is_active,
            created_at=workshop.created_at,
            updated_at=workshop.updated_at,
        )

    def list_workshops(
        self,
        pagination,
        workshop_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> dict:
        """查询车间列表"""
        query = self.db.query(Workshop)

        if workshop_type:
            query = query.filter(Workshop.workshop_type == workshop_type)
        if is_active is not None:
            query = query.filter(Workshop.is_active == is_active)

        total = query.count()
        workshops = apply_pagination(
            query.order_by(Workshop.created_at),
            pagination.offset,
            pagination.limit,
        ).all()

        items = [self._build_workshop_response(ws) for ws in workshops]
        return pagination.to_response(items, total)

    def create_workshop(self, workshop_in) -> WorkshopResponse:
        """创建车间"""
        # 检查车间编码是否已存在
        existing = (
            self.db.query(Workshop)
            .filter(Workshop.workshop_code == workshop_in.workshop_code)
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="车间编码已存在")

        # 检查车间主管是否存在
        if workshop_in.manager_id:
            get_or_404(self.db, User, workshop_in.manager_id, "车间主管不存在")

        workshop = Workshop(**workshop_in.model_dump())
        save_obj(self.db, workshop)

        return self._build_workshop_response(workshop)

    def get_workshop(self, workshop_id: int) -> WorkshopResponse:
        """获取车间详情"""
        workshop = get_or_404(self.db, Workshop, workshop_id, detail="车间不存在")
        return self._build_workshop_response(workshop)

    def update_workshop(self, workshop_id: int, workshop_in) -> WorkshopResponse:
        """更新车间"""
        workshop = get_or_404(self.db, Workshop, workshop_id, detail="车间不存在")

        # 检查车间主管是否存在
        if workshop_in.manager_id is not None:
            if workshop_in.manager_id:
                get_or_404(self.db, User, workshop_in.manager_id, "车间主管不存在")

        update_data = workshop_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workshop, field, value)

        save_obj(self.db, workshop)
        return self._build_workshop_response(workshop)

    def get_capacity(
        self,
        workshop_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """
        车间产能统计

        统计车间的产能、实际负荷、利用率等信息
        """
        workshop = get_or_404(self.db, Workshop, workshop_id, detail="车间不存在")

        # 基础产能信息
        capacity_hours = float(workshop.capacity_hours) if workshop.capacity_hours else 0.0
        worker_count = workshop.worker_count or 0

        # 如果没有指定日期范围，使用当前月
        today = date.today()
        if not start_date or not end_date:
            month_start, month_end = get_month_range(today)
            if not start_date:
                start_date = month_start
            if not end_date:
                end_date = month_end

        # 计算工作天数
        work_days = (end_date - start_date).days + 1

        # 计算总产能
        total_capacity = (
            capacity_hours * work_days
            if capacity_hours > 0
            else work_days * 8 * worker_count
        )

        # 统计该期间的工单
        work_orders = (
            self.db.query(WorkOrder)
            .filter(
                WorkOrder.workshop_id == workshop_id,
                WorkOrder.plan_start_date >= start_date,
                WorkOrder.plan_start_date <= end_date,
            )
            .all()
        )

        # 计算计划工时和实际工时
        plan_hours = sum(float(wo.standard_hours or 0) for wo in work_orders)
        actual_hours = sum(float(wo.actual_hours or 0) for wo in work_orders)

        # 从生产日报获取实际工时（更准确）
        daily_reports = (
            self.db.query(ProductionDailyReport)
            .filter(
                ProductionDailyReport.workshop_id == workshop_id,
                ProductionDailyReport.report_date >= start_date,
                ProductionDailyReport.report_date <= end_date,
            )
            .all()
        )

        if daily_reports:
            actual_hours = sum(float(dr.actual_hours or 0) for dr in daily_reports)

        # 计算负荷率和利用率
        load_rate = (plan_hours / total_capacity * 100) if total_capacity > 0 else 0
        utilization_rate = (actual_hours / total_capacity * 100) if total_capacity > 0 else 0

        # 统计工单状态
        pending_count = sum(1 for wo in work_orders if wo.status == "PENDING")
        in_progress_count = sum(
            1 for wo in work_orders if wo.status in ["ASSIGNED", "STARTED", "PAUSED"]
        )
        completed_count = sum(1 for wo in work_orders if wo.status == "COMPLETED")

        return {
            "workshop_id": workshop.id,
            "workshop_name": workshop.workshop_name,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "work_days": work_days,
            "worker_count": worker_count,
            "capacity_hours": capacity_hours,
            "total_capacity": total_capacity,
            "plan_hours": round(plan_hours, 2),
            "actual_hours": round(actual_hours, 2),
            "load_rate": round(load_rate, 2),
            "utilization_rate": round(utilization_rate, 2),
            "work_order_count": len(work_orders),
            "pending_count": pending_count,
            "in_progress_count": in_progress_count,
            "completed_count": completed_count,
        }

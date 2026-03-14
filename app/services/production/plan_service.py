# -*- coding: utf-8 -*-
"""
生产计划服务

处理生产计划的响应构建、工作流状态转换、CRUD 验证等业务逻辑。
"""
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.common.query_filters import apply_pagination
from app.models.production import ProductionPlan, WorkOrder, Workshop
from app.models.project import Project
from app.schemas.production import (
    ProductionPlanCalendarDay,
    ProductionPlanCalendarPlanItem,
    ProductionPlanCalendarResponse,
    ProductionPlanCalendarWorkOrderItem,
    ProductionPlanResponse,
)
from app.utils.db_helpers import get_or_404, save_obj


class ProductionPlanService:
    """生产计划服务"""

    def __init__(self, db: Session):
        self.db = db

    def _build_plan_response(self, plan: ProductionPlan) -> ProductionPlanResponse:
        """构建计划响应（含项目名/车间名查询）"""
        project_name = None
        if plan.project_id:
            project = self.db.query(Project).filter(Project.id == plan.project_id).first()
            project_name = project.project_name if project else None

        workshop_name = None
        if plan.workshop_id:
            workshop = self.db.query(Workshop).filter(Workshop.id == plan.workshop_id).first()
            workshop_name = workshop.workshop_name if workshop else None

        return ProductionPlanResponse(
            id=plan.id,
            plan_no=plan.plan_no,
            plan_name=plan.plan_name,
            plan_type=plan.plan_type,
            project_id=plan.project_id,
            project_name=project_name,
            workshop_id=plan.workshop_id,
            workshop_name=workshop_name,
            plan_start_date=plan.plan_start_date,
            plan_end_date=plan.plan_end_date,
            status=plan.status,
            progress=plan.progress or 0,
            description=plan.description,
            created_by=plan.created_by,
            approved_by=plan.approved_by,
            approved_at=plan.approved_at,
            remark=plan.remark,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )

    @staticmethod
    def _daterange(start_date: date, end_date: date):
        current = start_date
        while current <= end_date:
            yield current
            current += timedelta(days=1)

    def _build_calendar_response(
        self,
        plans: list[ProductionPlan],
        work_orders: list[WorkOrder],
        start_date: date,
        end_date: date,
    ) -> ProductionPlanCalendarResponse:
        project_name_cache: dict[int, Optional[str]] = {}
        workshop_name_cache: dict[int, Optional[str]] = {}
        calendar_map = defaultdict(lambda: {"plans": [], "work_orders": []})

        def get_project_name(project_id: Optional[int]) -> Optional[str]:
            if not project_id:
                return None
            if project_id not in project_name_cache:
                project = self.db.query(Project).filter(Project.id == project_id).first()
                project_name_cache[project_id] = project.project_name if project else None
            return project_name_cache[project_id]

        def get_workshop_name(workshop_id: Optional[int]) -> Optional[str]:
            if not workshop_id:
                return None
            if workshop_id not in workshop_name_cache:
                workshop = self.db.query(Workshop).filter(Workshop.id == workshop_id).first()
                workshop_name_cache[workshop_id] = workshop.workshop_name if workshop else None
            return workshop_name_cache[workshop_id]

        for plan in plans:
            item = ProductionPlanCalendarPlanItem(
                id=plan.id,
                plan_no=plan.plan_no,
                plan_name=plan.plan_name,
                plan_type=plan.plan_type,
                status=plan.status,
                project_id=plan.project_id,
                project_name=get_project_name(plan.project_id),
                workshop_id=plan.workshop_id,
                workshop_name=get_workshop_name(plan.workshop_id),
            )
            for day in self._daterange(
                max(plan.plan_start_date, start_date),
                min(plan.plan_end_date, end_date),
            ):
                calendar_map[day.isoformat()]["plans"].append(item)

        for order in work_orders:
            order_start = order.plan_start_date or start_date
            order_end = order.plan_end_date or order_start
            item = ProductionPlanCalendarWorkOrderItem(
                id=order.id,
                work_order_no=order.work_order_no,
                order_no=order.work_order_no,
                task_name=order.task_name,
                status=order.status,
                project_id=order.project_id,
                workshop_id=order.workshop_id,
                workstation_id=order.workstation_id,
                assigned_to=order.assigned_to,
                progress=order.progress or 0,
            )
            for day in self._daterange(max(order_start, start_date), min(order_end, end_date)):
                calendar_map[day.isoformat()]["work_orders"].append(item)

        days = [
            ProductionPlanCalendarDay(
                date=day,
                plans=calendar_map[day.isoformat()]["plans"],
                work_orders=calendar_map[day.isoformat()]["work_orders"],
            )
            for day in self._daterange(start_date, end_date)
        ]
        return ProductionPlanCalendarResponse(calendar=days)

    def get_calendar(
        self,
        start_date: date,
        end_date: date,
        project_id: Optional[int] = None,
        workshop_id: Optional[int] = None,
    ) -> ProductionPlanCalendarResponse:
        """获取生产计划日历视图，按日期展开计划与工单。"""
        from fastapi import HTTPException

        if start_date > end_date:
            raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")

        plans_query = self.db.query(ProductionPlan).filter(
            ProductionPlan.plan_start_date <= end_date,
            ProductionPlan.plan_end_date >= start_date,
        )
        orders_query = self.db.query(WorkOrder).filter(
            or_(WorkOrder.plan_start_date.is_(None), WorkOrder.plan_start_date <= end_date),
            or_(WorkOrder.plan_end_date.is_(None), WorkOrder.plan_end_date >= start_date),
        )

        if project_id:
            plans_query = plans_query.filter(ProductionPlan.project_id == project_id)
            orders_query = orders_query.filter(WorkOrder.project_id == project_id)
        if workshop_id:
            plans_query = plans_query.filter(ProductionPlan.workshop_id == workshop_id)
            orders_query = orders_query.filter(WorkOrder.workshop_id == workshop_id)

        plans = plans_query.order_by(ProductionPlan.plan_start_date, ProductionPlan.id).all()
        work_orders = orders_query.order_by(WorkOrder.plan_start_date, WorkOrder.id).all()
        return self._build_calendar_response(plans, work_orders, start_date, end_date)

    def list_plans(
        self,
        pagination,
        plan_type: Optional[str] = None,
        project_id: Optional[int] = None,
        workshop_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> dict:
        """查询生产计划列表"""
        query = self.db.query(ProductionPlan)

        if plan_type:
            query = query.filter(ProductionPlan.plan_type == plan_type)
        if project_id:
            query = query.filter(ProductionPlan.project_id == project_id)
        if workshop_id:
            query = query.filter(ProductionPlan.workshop_id == workshop_id)
        if status:
            query = query.filter(ProductionPlan.status == status)

        total = query.count()
        plans = apply_pagination(
            query.order_by(desc(ProductionPlan.created_at)),
            pagination.offset,
            pagination.limit,
        ).all()

        items = [self._build_plan_response(plan) for plan in plans]
        return pagination.to_response(items, total)

    def create_plan(self, plan_in, current_user_id: int) -> ProductionPlanResponse:
        """创建生产计划"""
        from app.api.v1.endpoints.production.utils import generate_plan_no

        # 检查项目是否存在
        if plan_in.project_id:
            get_or_404(self.db, Project, plan_in.project_id, "项目不存在")

        # 检查车间是否存在
        if plan_in.workshop_id:
            get_or_404(self.db, Workshop, plan_in.workshop_id, "车间不存在")

        plan_no = generate_plan_no(self.db)

        plan = ProductionPlan(
            plan_no=plan_no,
            status="DRAFT",
            progress=0,
            created_by=current_user_id,
            **plan_in.model_dump(),
        )
        save_obj(self.db, plan)

        return self._build_plan_response(plan)

    def get_plan(self, plan_id: int) -> ProductionPlanResponse:
        """获取生产计划详情"""
        plan = get_or_404(self.db, ProductionPlan, plan_id, detail="生产计划不存在")
        return self._build_plan_response(plan)

    def update_plan(self, plan_id: int, plan_in) -> ProductionPlanResponse:
        """更新生产计划"""
        from fastapi import HTTPException

        plan = get_or_404(self.db, ProductionPlan, plan_id, detail="生产计划不存在")

        if plan.status != "DRAFT":
            raise HTTPException(status_code=400, detail="只有草稿状态的计划才能更新")

        update_data = plan_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(plan, field, value)

        save_obj(self.db, plan)
        return self._build_plan_response(plan)

    def submit_plan(self, plan_id: int) -> dict:
        """提交计划审批"""
        from fastapi import HTTPException

        plan = get_or_404(self.db, ProductionPlan, plan_id, detail="生产计划不存在")

        if plan.status != "DRAFT":
            raise HTTPException(status_code=400, detail="只有草稿状态的计划才能提交")

        plan.status = "SUBMITTED"
        self.db.add(plan)
        self.db.commit()

        return {"code": 200, "message": "计划已提交审批"}

    def approve_plan(
        self,
        plan_id: int,
        approved: bool,
        approval_note: Optional[str],
        current_user_id: int,
    ) -> dict:
        """审批生产计划"""
        from fastapi import HTTPException

        plan = get_or_404(self.db, ProductionPlan, plan_id, detail="生产计划不存在")

        if plan.status != "SUBMITTED":
            raise HTTPException(status_code=400, detail="只有已提交的计划才能审批")

        if approved:
            plan.status = "APPROVED"
            plan.approved_by = current_user_id
            plan.approved_at = datetime.now()
        else:
            plan.status = "DRAFT"

        if approval_note:
            plan.remark = (plan.remark or "") + f"\n审批意见：{approval_note}"

        self.db.add(plan)
        self.db.commit()

        return {"code": 200, "message": "审批成功" if approved else "已驳回"}

    def publish_plan(self, plan_id: int) -> dict:
        """发布生产计划"""
        from fastapi import HTTPException

        plan = get_or_404(self.db, ProductionPlan, plan_id, detail="生产计划不存在")

        if plan.status != "APPROVED":
            raise HTTPException(status_code=400, detail="只有已审批的计划才能发布")

        plan.status = "PUBLISHED"
        self.db.add(plan)
        self.db.commit()

        return {"code": 200, "message": "计划已发布"}

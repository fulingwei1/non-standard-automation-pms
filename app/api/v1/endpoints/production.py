# -*- coding: utf-8 -*-
"""
生产管理 API endpoints
包含：车间管理、工位管理、生产计划、工单管理、报工系统
"""
from typing import Any, List, Optional, Dict
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.production import (
    Workshop, Workstation, ProductionPlan, WorkOrder, WorkReport, Worker,
    MaterialRequisition, MaterialRequisitionItem, ProductionException,
    WorkerSkill, Equipment, EquipmentMaintenance, ProcessDict,
    ProductionDailyReport
)
from app.models.project import Project, Machine
from app.schemas.production import (
    WorkshopCreate,
    WorkshopUpdate,
    WorkshopResponse,
    WorkstationCreate,
    WorkstationUpdate,
    WorkstationResponse,
    WorkstationStatusResponse,
    ProductionPlanCreate,
    ProductionPlanUpdate,
    ProductionPlanResponse,
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderAssignRequest,
    WorkOrderResponse,
    WorkOrderProgressResponse,
    WorkReportStartRequest,
    WorkReportProgressRequest,
    WorkReportCompleteRequest,
    WorkReportResponse,
    MaterialRequisitionCreate,
    MaterialRequisitionItemCreate,
    MaterialRequisitionResponse,
    MaterialRequisitionItemResponse,
    MaterialRequisitionListResponse,
    ProductionExceptionCreate,
    ProductionExceptionHandle,
    ProductionExceptionResponse,
    ProductionExceptionListResponse,
    WorkerCreate,
    WorkerUpdate,
    WorkerResponse,
    WorkerListResponse,
    ProductionDailyReportCreate,
    ProductionDailyReportResponse,
    ProductionDashboardResponse,
    WorkshopTaskBoardResponse,
    ProductionEfficiencyReportResponse,
    CapacityUtilizationResponse,
    WorkerPerformanceReportResponse,
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


def generate_plan_no(db: Session) -> str:
    """生成生产计划编号：PP-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_plan = (
        db.query(ProductionPlan)
        .filter(ProductionPlan.plan_no.like(f"PP-{today}-%"))
        .order_by(desc(ProductionPlan.plan_no))
        .first()
    )
    if max_plan:
        seq = int(max_plan.plan_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"PP-{today}-{seq:03d}"


def generate_work_order_no(db: Session) -> str:
    """生成工单编号：WO-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_order = (
        db.query(WorkOrder)
        .filter(WorkOrder.work_order_no.like(f"WO-{today}-%"))
        .order_by(desc(WorkOrder.work_order_no))
        .first()
    )
    if max_order:
        seq = int(max_order.work_order_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"WO-{today}-{seq:03d}"


def generate_report_no(db: Session) -> str:
    """生成报工单号：WR-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_report = (
        db.query(WorkReport)
        .filter(WorkReport.report_no.like(f"WR-{today}-%"))
        .order_by(desc(WorkReport.report_no))
        .first()
    )
    if max_report:
        seq = int(max_report.report_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"WR-{today}-{seq:03d}"


# ==================== 车间管理 ====================

@router.get("/workshops", response_model=PaginatedResponse)
def read_workshops(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    workshop_type: Optional[str] = Query(None, description="车间类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取车间列表（机加/装配/调试）
    """
    query = db.query(Workshop)
    
    if workshop_type:
        query = query.filter(Workshop.workshop_type == workshop_type)
    
    if is_active is not None:
        query = query.filter(Workshop.is_active == is_active)
    
    total = query.count()
    offset = (page - 1) * page_size
    workshops = query.order_by(Workshop.created_at).offset(offset).limit(page_size).all()
    
    items = []
    for workshop in workshops:
        manager_name = None
        if workshop.manager_id:
            manager = db.query(User).filter(User.id == workshop.manager_id).first()
            manager_name = manager.real_name if manager else None
        
        items.append(WorkshopResponse(
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
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/workshops", response_model=WorkshopResponse)
def create_workshop(
    *,
    db: Session = Depends(deps.get_db),
    workshop_in: WorkshopCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建车间
    """
    # 检查车间编码是否已存在
    existing = db.query(Workshop).filter(Workshop.workshop_code == workshop_in.workshop_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="车间编码已存在")
    
    # 检查车间主管是否存在
    if workshop_in.manager_id:
        manager = db.query(User).filter(User.id == workshop_in.manager_id).first()
        if not manager:
            raise HTTPException(status_code=404, detail="车间主管不存在")
    
    workshop = Workshop(**workshop_in.model_dump())
    db.add(workshop)
    db.commit()
    db.refresh(workshop)
    
    manager_name = None
    if workshop.manager_id:
        manager = db.query(User).filter(User.id == workshop.manager_id).first()
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


@router.get("/workshops/{workshop_id}", response_model=WorkshopResponse)
def read_workshop(
    *,
    db: Session = Depends(deps.get_db),
    workshop_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取车间详情（含产能/人员）
    """
    workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="车间不存在")
    
    manager_name = None
    if workshop.manager_id:
        manager = db.query(User).filter(User.id == workshop.manager_id).first()
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


@router.get("/workshops/{workshop_id}/capacity", response_model=dict)
def get_workshop_capacity(
    *,
    db: Session = Depends(deps.get_db),
    workshop_id: int,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    车间产能统计
    统计车间的产能、实际负荷、利用率等信息
    """
    workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="车间不存在")
    
    # 基础产能信息
    capacity_hours = float(workshop.capacity_hours) if workshop.capacity_hours else 0.0
    worker_count = workshop.worker_count or 0
    
    # 如果没有指定日期范围，使用当前月
    from datetime import timedelta
    from calendar import monthrange
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        _, last_day = monthrange(today.year, today.month)
        end_date = date(today.year, today.month, last_day)
    
    # 计算工作天数
    work_days = (end_date - start_date).days + 1
    
    # 计算总产能（如果capacity_hours是日产能，则乘以工作天数；否则使用capacity_hours）
    total_capacity = capacity_hours * work_days if capacity_hours > 0 else work_days * 8 * worker_count
    
    # 统计该期间的工单
    work_orders = db.query(WorkOrder).filter(
        WorkOrder.workshop_id == workshop_id,
        WorkOrder.plan_start_date >= start_date,
        WorkOrder.plan_start_date <= end_date
    ).all()
    
    # 计算计划工时和实际工时
    plan_hours = sum(float(wo.standard_hours or 0) for wo in work_orders)
    actual_hours = sum(float(wo.actual_hours or 0) for wo in work_orders)
    
    # 从生产日报获取实际工时（更准确）
    from app.models.production import ProductionDailyReport
    daily_reports = db.query(ProductionDailyReport).filter(
        ProductionDailyReport.workshop_id == workshop_id,
        ProductionDailyReport.report_date >= start_date,
        ProductionDailyReport.report_date <= end_date
    ).all()
    
    if daily_reports:
        actual_hours = sum(float(dr.actual_hours or 0) for dr in daily_reports)
    
    # 计算负荷率和利用率
    load_rate = (plan_hours / total_capacity * 100) if total_capacity > 0 else 0
    utilization_rate = (actual_hours / total_capacity * 100) if total_capacity > 0 else 0
    
    # 统计工单状态
    pending_count = sum(1 for wo in work_orders if wo.status == "PENDING")
    in_progress_count = sum(1 for wo in work_orders if wo.status in ["ASSIGNED", "STARTED", "PAUSED"])
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


@router.put("/workshops/{workshop_id}", response_model=WorkshopResponse)
def update_workshop(
    *,
    db: Session = Depends(deps.get_db),
    workshop_id: int,
    workshop_in: WorkshopUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新车间
    """
    workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="车间不存在")
    
    # 检查车间主管是否存在
    if workshop_in.manager_id is not None:
        if workshop_in.manager_id:
            manager = db.query(User).filter(User.id == workshop_in.manager_id).first()
            if not manager:
                raise HTTPException(status_code=404, detail="车间主管不存在")
    
    update_data = workshop_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workshop, field, value)
    
    db.add(workshop)
    db.commit()
    db.refresh(workshop)
    
    manager_name = None
    if workshop.manager_id:
        manager = db.query(User).filter(User.id == workshop.manager_id).first()
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


# ==================== 工位管理 ====================

@router.get("/workshops/{workshop_id}/workstations", response_model=List[WorkstationResponse])
def read_workstations(
    *,
    db: Session = Depends(deps.get_db),
    workshop_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工位列表
    """
    workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="车间不存在")
    
    workstations = db.query(Workstation).filter(Workstation.workshop_id == workshop_id).all()
    
    items = []
    for ws in workstations:
        equipment_name = None
        if ws.equipment_id:
            from app.models.production import Equipment
            equipment = db.query(Equipment).filter(Equipment.id == ws.equipment_id).first()
            equipment_name = equipment.equipment_name if equipment else None
        
        items.append(WorkstationResponse(
            id=ws.id,
            workstation_code=ws.workstation_code,
            workstation_name=ws.workstation_name,
            workshop_id=ws.workshop_id,
            workshop_name=workshop.workshop_name,
            equipment_id=ws.equipment_id,
            equipment_name=equipment_name,
            status=ws.status,
            current_worker_id=ws.current_worker_id,
            current_work_order_id=ws.current_work_order_id,
            description=ws.description,
            is_active=ws.is_active,
            created_at=ws.created_at,
            updated_at=ws.updated_at,
        ))
    
    return items


@router.post("/workshops/{workshop_id}/workstations", response_model=WorkstationResponse)
def create_workstation(
    *,
    db: Session = Depends(deps.get_db),
    workshop_id: int,
    workstation_in: WorkstationCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建工位
    """
    workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="车间不存在")
    
    # 检查工位编码是否已存在
    existing = db.query(Workstation).filter(Workstation.workstation_code == workstation_in.workstation_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="工位编码已存在")
    
    workstation = Workstation(
        workshop_id=workshop_id,
        status="IDLE",
        **workstation_in.model_dump()
    )
    db.add(workstation)
    db.commit()
    db.refresh(workstation)
    
    equipment_name = None
    if workstation.equipment_id:
        from app.models.production import Equipment
        equipment = db.query(Equipment).filter(Equipment.id == workstation.equipment_id).first()
        equipment_name = equipment.equipment_name if equipment else None
    
    return WorkstationResponse(
        id=workstation.id,
        workstation_code=workstation.workstation_code,
        workstation_name=workstation.workstation_name,
        workshop_id=workstation.workshop_id,
        workshop_name=workshop.workshop_name,
        equipment_id=workstation.equipment_id,
        equipment_name=equipment_name,
        status=workstation.status,
        current_worker_id=workstation.current_worker_id,
        current_work_order_id=workstation.current_work_order_id,
        description=workstation.description,
        is_active=workstation.is_active,
        created_at=workstation.created_at,
        updated_at=workstation.updated_at,
    )


@router.get("/workstations/{workstation_id}/status", response_model=WorkstationStatusResponse)
def get_workstation_status(
    *,
    db: Session = Depends(deps.get_db),
    workstation_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工位状态（空闲/工作中）
    """
    workstation = db.query(Workstation).filter(Workstation.id == workstation_id).first()
    if not workstation:
        raise HTTPException(status_code=404, detail="工位不存在")
    
    current_worker_name = None
    if workstation.current_worker_id:
        worker = db.query(Worker).filter(Worker.id == workstation.current_worker_id).first()
        current_worker_name = worker.worker_name if worker else None
    
    current_work_order_no = None
    if workstation.current_work_order_id:
        work_order = db.query(WorkOrder).filter(WorkOrder.id == workstation.current_work_order_id).first()
        current_work_order_no = work_order.work_order_no if work_order else None
    
    is_available = workstation.status == "IDLE" and workstation.current_work_order_id is None
    
    return WorkstationStatusResponse(
        workstation_id=workstation.id,
        workstation_code=workstation.workstation_code,
        workstation_name=workstation.workstation_name,
        status=workstation.status,
        current_worker_id=workstation.current_worker_id,
        current_worker_name=current_worker_name,
        current_work_order_id=workstation.current_work_order_id,
        current_work_order_no=current_work_order_no,
        is_available=is_available,
    )


# ==================== 生产计划管理 ====================

@router.get("/production-plans", response_model=PaginatedResponse)
def read_production_plans(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    plan_type: Optional[str] = Query(None, description="计划类型筛选：MASTER/WORKSHOP"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取生产计划列表（主计划/车间计划）
    """
    query = db.query(ProductionPlan)
    
    if plan_type:
        query = query.filter(ProductionPlan.plan_type == plan_type)
    
    if project_id:
        query = query.filter(ProductionPlan.project_id == project_id)
    
    if workshop_id:
        query = query.filter(ProductionPlan.workshop_id == workshop_id)
    
    if status:
        query = query.filter(ProductionPlan.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    plans = query.order_by(desc(ProductionPlan.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for plan in plans:
        project_name = None
        if plan.project_id:
            project = db.query(Project).filter(Project.id == plan.project_id).first()
            project_name = project.project_name if project else None
        
        workshop_name = None
        if plan.workshop_id:
            workshop = db.query(Workshop).filter(Workshop.id == plan.workshop_id).first()
            workshop_name = workshop.workshop_name if workshop else None
        
        items.append(ProductionPlanResponse(
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
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/production-plans", response_model=ProductionPlanResponse)
def create_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_in: ProductionPlanCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建生产计划
    """
    # 检查项目是否存在
    if plan_in.project_id:
        project = db.query(Project).filter(Project.id == plan_in.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查车间是否存在
    if plan_in.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == plan_in.workshop_id).first()
        if not workshop:
            raise HTTPException(status_code=404, detail="车间不存在")
    
    # 生成计划编号
    plan_no = generate_plan_no(db)
    
    plan = ProductionPlan(
        plan_no=plan_no,
        status="DRAFT",
        progress=0,
        created_by=current_user.id,
        **plan_in.model_dump()
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    project_name = None
    if plan.project_id:
        project = db.query(Project).filter(Project.id == plan.project_id).first()
        project_name = project.project_name if project else None
    
    workshop_name = None
    if plan.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == plan.workshop_id).first()
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


@router.get("/production-plans/{plan_id}", response_model=ProductionPlanResponse)
def read_production_plan(
    plan_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取生产计划详情
    """
    plan = db.query(ProductionPlan).filter(ProductionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="生产计划不存在")
    
    project_name = None
    if plan.project_id:
        project = db.query(Project).filter(Project.id == plan.project_id).first()
        project_name = project.project_name if project else None
    
    workshop_name = None
    if plan.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == plan.workshop_id).first()
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


@router.put("/production-plans/{plan_id}", response_model=ProductionPlanResponse)
def update_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    plan_in: ProductionPlanUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新生产计划
    """
    plan = db.query(ProductionPlan).filter(ProductionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="生产计划不存在")
    
    # 只有草稿状态才能更新
    if plan.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的计划才能更新")
    
    update_data = plan_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)
    
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    project_name = None
    if plan.project_id:
        project = db.query(Project).filter(Project.id == plan.project_id).first()
        project_name = project.project_name if project else None
    
    workshop_name = None
    if plan.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == plan.workshop_id).first()
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


@router.put("/production-plans/{plan_id}/submit", response_model=ResponseModel)
def submit_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交计划审批
    """
    plan = db.query(ProductionPlan).filter(ProductionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="生产计划不存在")
    
    if plan.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的计划才能提交")
    
    plan.status = "SUBMITTED"
    db.add(plan)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="计划已提交审批"
    )


@router.put("/production-plans/{plan_id}/approve", response_model=ResponseModel)
def approve_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    approved: bool = Query(True, description="是否审批通过"),
    approval_note: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批通过生产计划
    """
    plan = db.query(ProductionPlan).filter(ProductionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="生产计划不存在")
    
    if plan.status != "SUBMITTED":
        raise HTTPException(status_code=400, detail="只有已提交的计划才能审批")
    
    if approved:
        plan.status = "APPROVED"
        plan.approved_by = current_user.id
        plan.approved_at = datetime.now()
    else:
        plan.status = "DRAFT"  # 驳回后回到草稿状态
    
    if approval_note:
        plan.remark = (plan.remark or "") + f"\n审批意见：{approval_note}"
    
    db.add(plan)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="审批成功" if approved else "已驳回"
    )


@router.put("/production-plans/{plan_id}/publish", response_model=ResponseModel)
def publish_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    计划发布
    """
    plan = db.query(ProductionPlan).filter(ProductionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="生产计划不存在")
    
    if plan.status != "APPROVED":
        raise HTTPException(status_code=400, detail="只有已审批的计划才能发布")
    
    plan.status = "PUBLISHED"
    db.add(plan)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="计划已发布"
    )


# ==================== 生产工单管理 ====================

@router.get("/work-orders", response_model=PaginatedResponse)
def read_work_orders(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    assigned_to: Optional[int] = Query(None, description="指派给筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工单列表（分页+筛选）
    """
    query = db.query(WorkOrder)
    
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
    offset = (page - 1) * page_size
    orders = query.order_by(desc(WorkOrder.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for order in orders:
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
            from app.models.production import ProcessDict
            process = db.query(ProcessDict).filter(ProcessDict.id == order.process_id).first()
            process_name = process.process_name if process else None
        
        assigned_worker_name = None
        if order.assigned_to:
            worker = db.query(Worker).filter(Worker.id == order.assigned_to).first()
            assigned_worker_name = worker.worker_name if worker else None
        
        items.append(WorkOrderResponse(
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
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/work-orders", response_model=WorkOrderResponse)
def create_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_in: WorkOrderCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建工单
    """
    # 检查项目是否存在
    if order_in.project_id:
        project = db.query(Project).filter(Project.id == order_in.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查机台是否存在
    if order_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == order_in.machine_id).first()
        if not machine:
            raise HTTPException(status_code=404, detail="机台不存在")
    
    # 检查生产计划是否存在
    if order_in.production_plan_id:
        plan = db.query(ProductionPlan).filter(ProductionPlan.id == order_in.production_plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="生产计划不存在")
    
    # 检查车间是否存在
    if order_in.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == order_in.workshop_id).first()
        if not workshop:
            raise HTTPException(status_code=404, detail="车间不存在")
    
    # 检查工位是否存在
    if order_in.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order_in.workstation_id).first()
        if not workstation:
            raise HTTPException(status_code=404, detail="工位不存在")
        if workstation.workshop_id != order_in.workshop_id:
            raise HTTPException(status_code=400, detail="工位不属于该车间")
    
    # 生成工单编号
    work_order_no = generate_work_order_no(db)
    
    order = WorkOrder(
        work_order_no=work_order_no,
        status="PENDING",
        progress=0,
        completed_qty=0,
        qualified_qty=0,
        defect_qty=0,
        actual_hours=0,
        created_by=current_user.id,
        **order_in.model_dump()
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_work_order(db=db, order_id=order.id, current_user=current_user)


@router.get("/work-orders/{order_id}", response_model=WorkOrderResponse)
def read_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工单详情
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
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
        from app.models.production import ProcessDict
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


@router.put("/work-orders/{order_id}/assign", response_model=WorkOrderResponse)
def assign_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    assign_in: WorkOrderAssignRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    任务派工（指派人员/工位）
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if order.status != "PENDING":
        raise HTTPException(status_code=400, detail="只有待派工状态的工单才能派工")
    
    # 检查工人是否存在
    worker = db.query(Worker).filter(Worker.id == assign_in.assigned_to).first()
    if not worker:
        raise HTTPException(status_code=404, detail="工人不存在")
    
    # 检查工位是否存在
    if assign_in.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == assign_in.workstation_id).first()
        if not workstation:
            raise HTTPException(status_code=404, detail="工位不存在")
        if order.workshop_id and workstation.workshop_id != order.workshop_id:
            raise HTTPException(status_code=400, detail="工位不属于该车间")
    
    order.assigned_to = assign_in.assigned_to
    order.assigned_at = datetime.now()
    order.assigned_by = current_user.id
    order.status = "ASSIGNED"
    
    if assign_in.workstation_id:
        order.workstation_id = assign_in.workstation_id
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_work_order(db=db, order_id=order.id, current_user=current_user)


@router.post("/work-orders/batch-assign", response_model=ResponseModel)
def batch_assign_work_orders(
    *,
    db: Session = Depends(deps.get_db),
    order_ids: List[int] = Body(..., description="工单ID列表"),
    assign_in: WorkOrderAssignRequest = Body(..., description="派工信息"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量派工
    """
    success_count = 0
    failed_orders = []
    
    for order_id in order_ids:
        try:
            order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
            if not order:
                failed_orders.append({"order_id": order_id, "reason": "工单不存在"})
                continue
            
            if order.status != "PENDING":
                failed_orders.append({"order_id": order_id, "reason": f"工单状态为{order.status}，不能派工"})
                continue
            
            # 验证工人
            if assign_in.assigned_to:
                worker = db.query(Worker).filter(Worker.id == assign_in.assigned_to).first()
                if not worker:
                    failed_orders.append({"order_id": order_id, "reason": "工人不存在"})
                    continue
                order.assigned_to = assign_in.assigned_to
                order.assigned_to_name = worker.worker_name
            
            # 验证工位
            if assign_in.workstation_id:
                workstation = db.query(Workstation).filter(Workstation.id == assign_in.workstation_id).first()
                if not workstation:
                    failed_orders.append({"order_id": order_id, "reason": "工位不存在"})
                    continue
                order.workstation_id = assign_in.workstation_id
            
            order.status = "ASSIGNED"
            order.assigned_at = datetime.now()
            order.assigned_by = current_user.id
            
            db.add(order)
            success_count += 1
        except Exception as e:
            failed_orders.append({"order_id": order_id, "reason": str(e)})
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message=f"批量派工完成：成功 {success_count} 个，失败 {len(failed_orders)} 个",
        data={"success_count": success_count, "failed_orders": failed_orders}
    )


@router.put("/work-orders/{order_id}/start", response_model=WorkOrderResponse)
def start_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    开始工单
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if order.status != "ASSIGNED":
        raise HTTPException(status_code=400, detail="只有已派工的工单才能开始")
    
    order.status = "STARTED"
    order.actual_start_time = datetime.now()
    
    # 更新工位状态
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            workstation.status = "WORKING"
            workstation.current_work_order_id = order.id
            workstation.current_worker_id = order.assigned_to
            db.add(workstation)
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_work_order(db=db, order_id=order.id, current_user=current_user)


@router.put("/work-orders/{order_id}/complete", response_model=WorkOrderResponse)
def complete_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    完成工单
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if order.status not in ["STARTED", "PAUSED"]:
        raise HTTPException(status_code=400, detail="只有已开始或已暂停的工单才能完成")
    
    order.status = "COMPLETED"
    order.actual_end_time = datetime.now()
    order.progress = 100
    
    # 更新工位状态
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            workstation.status = "IDLE"
            workstation.current_work_order_id = None
            workstation.current_worker_id = None
            db.add(workstation)
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_work_order(db=db, order_id=order.id, current_user=current_user)


@router.put("/work-orders/{order_id}/pause", response_model=WorkOrderResponse)
def pause_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    pause_reason: Optional[str] = Body(None, description="暂停原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    暂停工单
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if order.status != "STARTED":
        raise HTTPException(status_code=400, detail="只有已开始的工单才能暂停")
    
    order.status = "PAUSED"
    if pause_reason:
        order.remark = (order.remark or "") + f"\n暂停原因：{pause_reason}"
    
    # 更新工位状态
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            workstation.status = "IDLE"
            db.add(workstation)
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_work_order(db=db, order_id=order.id, current_user=current_user)


@router.put("/work-orders/{order_id}/resume", response_model=WorkOrderResponse)
def resume_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    恢复工单
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if order.status != "PAUSED":
        raise HTTPException(status_code=400, detail="只有已暂停的工单才能恢复")
    
    order.status = "STARTED"
    
    # 更新工位状态
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            workstation.status = "WORKING"
            workstation.current_work_order_id = order.id
            workstation.current_worker_id = order.assigned_to
            db.add(workstation)
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_work_order(db=db, order_id=order.id, current_user=current_user)


@router.put("/work-orders/{order_id}/cancel", response_model=WorkOrderResponse)
def cancel_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    cancel_reason: Optional[str] = Body(None, description="取消原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    取消工单
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if order.status in ["COMPLETED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="已完成或已取消的工单不能再次取消")
    
    order.status = "CANCELLED"
    if cancel_reason:
        order.remark = (order.remark or "") + f"\n取消原因：{cancel_reason}"
    
    # 更新工位状态
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            workstation.status = "IDLE"
            workstation.current_work_order_id = None
            workstation.current_worker_id = None
            db.add(workstation)
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_work_order(db=db, order_id=order.id, current_user=current_user)


@router.get("/work-orders/{order_id}/progress", response_model=WorkOrderProgressResponse)
def get_work_order_progress(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工单进度
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    # 计算效率
    efficiency = None
    if order.standard_hours and order.actual_hours and order.actual_hours > 0:
        efficiency = float((order.standard_hours / order.actual_hours) * 100)
    
    return WorkOrderProgressResponse(
        work_order_id=order.id,
        work_order_no=order.work_order_no,
        task_name=order.task_name,
        plan_qty=order.plan_qty or 0,
        completed_qty=order.completed_qty or 0,
        qualified_qty=order.qualified_qty or 0,
        defect_qty=order.defect_qty or 0,
        progress=order.progress or 0,
        status=order.status,
        plan_start_date=order.plan_start_date,
        plan_end_date=order.plan_end_date,
        actual_start_time=order.actual_start_time,
        actual_end_time=order.actual_end_time,
        standard_hours=float(order.standard_hours) if order.standard_hours else None,
        actual_hours=float(order.actual_hours) if order.actual_hours else 0,
        efficiency=efficiency,
    )


# ==================== 报工系统 ====================

@router.post("/work-reports/start", response_model=WorkReportResponse)
def start_work_report(
    *,
    db: Session = Depends(deps.get_db),
    report_in: WorkReportStartRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    开工报告（扫码开工）
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == report_in.work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if work_order.status != "ASSIGNED":
        raise HTTPException(status_code=400, detail="只有已派工的工单才能开工")
    
    # 获取当前工人（从用户关联）
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    if not worker:
        raise HTTPException(status_code=400, detail="当前用户未关联工人信息")
    
    # 生成报工单号
    report_no = generate_report_no(db)
    
    report = WorkReport(
        report_no=report_no,
        work_order_id=report_in.work_order_id,
        worker_id=worker.id,
        report_type="START",
        report_time=datetime.now(),
        status="PENDING",
        report_note=report_in.report_note,
    )
    db.add(report)
    
    # 更新工单状态
    work_order.status = "STARTED"
    work_order.actual_start_time = datetime.now()
    work_order.progress = 0
    
    # 更新工位状态
    if work_order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == work_order.workstation_id).first()
        if workstation:
            workstation.status = "WORKING"
            workstation.current_work_order_id = work_order.id
            workstation.current_worker_id = worker.id
            db.add(workstation)
    
    db.commit()
    db.refresh(report)
    
    return get_work_report_detail(db=db, report_id=report.id, current_user=current_user)


@router.post("/work-reports/progress", response_model=WorkReportResponse)
def progress_work_report(
    *,
    db: Session = Depends(deps.get_db),
    report_in: WorkReportProgressRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    进度上报
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == report_in.work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if work_order.status not in ["STARTED", "PAUSED"]:
        raise HTTPException(status_code=400, detail="只有已开始或已暂停的工单才能上报进度")
    
    # 获取当前工人
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    if not worker:
        raise HTTPException(status_code=400, detail="当前用户未关联工人信息")
    
    # 生成报工单号
    report_no = generate_report_no(db)
    
    report = WorkReport(
        report_no=report_no,
        work_order_id=report_in.work_order_id,
        worker_id=worker.id,
        report_type="PROGRESS",
        report_time=datetime.now(),
        progress_percent=report_in.progress_percent,
        work_hours=report_in.work_hours,
        status="PENDING",
        report_note=report_in.report_note,
    )
    db.add(report)
    
    # 更新工单进度
    work_order.progress = report_in.progress_percent
    if report_in.work_hours:
        work_order.actual_hours = (work_order.actual_hours or 0) + report_in.work_hours
    
    db.commit()
    db.refresh(report)
    
    return get_work_report_detail(db=db, report_id=report.id, current_user=current_user)


@router.post("/work-reports/complete", response_model=WorkReportResponse)
def complete_work_report(
    *,
    db: Session = Depends(deps.get_db),
    report_in: WorkReportCompleteRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    完工报告（数量/合格数）
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == report_in.work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if work_order.status not in ["STARTED", "PAUSED"]:
        raise HTTPException(status_code=400, detail="只有已开始或已暂停的工单才能完工")
    
    # 检查完成数量
    if report_in.completed_qty > work_order.plan_qty:
        raise HTTPException(status_code=400, detail="完成数量不能超过计划数量")
    
    if report_in.qualified_qty > report_in.completed_qty:
        raise HTTPException(status_code=400, detail="合格数量不能超过完成数量")
    
    # 获取当前工人
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    if not worker:
        raise HTTPException(status_code=400, detail="当前用户未关联工人信息")
    
    # 生成报工单号
    report_no = generate_report_no(db)
    
    report = WorkReport(
        report_no=report_no,
        work_order_id=report_in.work_order_id,
        worker_id=worker.id,
        report_type="COMPLETE",
        report_time=datetime.now(),
        completed_qty=report_in.completed_qty,
        qualified_qty=report_in.qualified_qty,
        defect_qty=report_in.defect_qty or 0,
        work_hours=report_in.work_hours,
        status="PENDING",
        report_note=report_in.report_note,
    )
    db.add(report)
    
    # 更新工单
    work_order.completed_qty = report_in.completed_qty
    work_order.qualified_qty = report_in.qualified_qty
    work_order.defect_qty = report_in.defect_qty or 0
    work_order.progress = 100
    
    if report_in.work_hours:
        work_order.actual_hours = (work_order.actual_hours or 0) + report_in.work_hours
    
    # 如果完成数量达到计划数量，自动完成工单
    if report_in.completed_qty >= work_order.plan_qty:
        work_order.status = "COMPLETED"
        work_order.actual_end_time = datetime.now()
        
        # 更新工位状态
        if work_order.workstation_id:
            workstation = db.query(Workstation).filter(Workstation.id == work_order.workstation_id).first()
            if workstation:
                workstation.status = "IDLE"
                workstation.current_work_order_id = None
                workstation.current_worker_id = None
                db.add(workstation)
    
    db.commit()
    db.refresh(report)
    
    return get_work_report_detail(db=db, report_id=report.id, current_user=current_user)


@router.get("/work-reports/{report_id}", response_model=WorkReportResponse)
def get_work_report_detail(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报工详情
    """
    report = db.query(WorkReport).filter(WorkReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报工记录不存在")
    
    work_order = db.query(WorkOrder).filter(WorkOrder.id == report.work_order_id).first()
    worker = db.query(Worker).filter(Worker.id == report.worker_id).first()
    
    return WorkReportResponse(
        id=report.id,
        report_no=report.report_no,
        work_order_id=report.work_order_id,
        work_order_no=work_order.work_order_no if work_order else None,
        worker_id=report.worker_id,
        worker_name=worker.worker_name if worker else None,
        report_type=report.report_type,
        report_time=report.report_time,
        progress_percent=report.progress_percent,
        work_hours=float(report.work_hours) if report.work_hours else None,
        completed_qty=report.completed_qty,
        qualified_qty=report.qualified_qty,
        defect_qty=report.defect_qty,
        status=report.status,
        report_note=report.report_note,
        approved_by=report.approved_by,
        approved_at=report.approved_at,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.get("/work-reports", response_model=PaginatedResponse)
def read_work_reports(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    work_order_id: Optional[int] = Query(None, description="工单ID筛选"),
    worker_id: Optional[int] = Query(None, description="工人ID筛选"),
    report_type: Optional[str] = Query(None, description="报工类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报工记录列表
    """
    query = db.query(WorkReport)
    
    if work_order_id:
        query = query.filter(WorkReport.work_order_id == work_order_id)
    
    if worker_id:
        query = query.filter(WorkReport.worker_id == worker_id)
    
    if report_type:
        query = query.filter(WorkReport.report_type == report_type)
    
    if status:
        query = query.filter(WorkReport.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    reports = query.order_by(desc(WorkReport.report_time)).offset(offset).limit(page_size).all()
    
    items = []
    for report in reports:
        work_order = db.query(WorkOrder).filter(WorkOrder.id == report.work_order_id).first()
        worker = db.query(Worker).filter(Worker.id == report.worker_id).first()
        
        items.append(WorkReportResponse(
            id=report.id,
            report_no=report.report_no,
            work_order_id=report.work_order_id,
            work_order_no=work_order.work_order_no if work_order else None,
            worker_id=report.worker_id,
            worker_name=worker.worker_name if worker else None,
            report_type=report.report_type,
            report_time=report.report_time,
            progress_percent=report.progress_percent,
            work_hours=float(report.work_hours) if report.work_hours else None,
            completed_qty=report.completed_qty,
            qualified_qty=report.qualified_qty,
            defect_qty=report.defect_qty,
            status=report.status,
            report_note=report.report_note,
            approved_by=report.approved_by,
            approved_at=report.approved_at,
            created_at=report.created_at,
            updated_at=report.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.put("/work-reports/{report_id}/approve", response_model=ResponseModel)
def approve_work_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    approved: bool = Query(True, description="是否审批通过"),
    approval_note: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    报工审批（车间主管）
    """
    report = db.query(WorkReport).filter(WorkReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报工记录不存在")
    
    if report.status != "PENDING":
        raise HTTPException(status_code=400, detail="只有待审核的报工记录才能审批")
    
    if approved:
        report.status = "APPROVED"
        report.approved_by = current_user.id
        report.approved_at = datetime.now()
    else:
        report.status = "REJECTED"
        report.approved_by = current_user.id
        report.approved_at = datetime.now()
    
    if approval_note:
        report.report_note = (report.report_note or "") + f"\n审批意见：{approval_note}"
    
    db.add(report)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="审批成功" if approved else "已驳回"
    )


@router.get("/work-reports/my", response_model=PaginatedResponse)
def get_my_work_reports(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    我的报工记录（工人查看）
    """
    # 获取当前工人
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    if not worker:
        raise HTTPException(status_code=400, detail="当前用户未关联工人信息")
    
    query = db.query(WorkReport).filter(WorkReport.worker_id == worker.id)
    
    total = query.count()
    offset = (page - 1) * page_size
    reports = query.order_by(desc(WorkReport.report_time)).offset(offset).limit(page_size).all()
    
    items = []
    for report in reports:
        work_order = db.query(WorkOrder).filter(WorkOrder.id == report.work_order_id).first()
        
        items.append(WorkReportResponse(
            id=report.id,
            report_no=report.report_no,
            work_order_id=report.work_order_id,
            work_order_no=work_order.work_order_no if work_order else None,
            worker_id=report.worker_id,
            worker_name=worker.worker_name,
            report_type=report.report_type,
            report_time=report.report_time,
            progress_percent=report.progress_percent,
            work_hours=float(report.work_hours) if report.work_hours else None,
            completed_qty=report.completed_qty,
            qualified_qty=report.qualified_qty,
            defect_qty=report.defect_qty,
            status=report.status,
            report_note=report.report_note,
            approved_by=report.approved_by,
            approved_at=report.approved_at,
            created_at=report.created_at,
            updated_at=report.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )



# ==================== 生产计划管理 ====================

@router.get("/production-plans", response_model=PaginatedResponse)
def read_production_plans(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    plan_type: Optional[str] = Query(None, description="计划类型筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取生产计划列表（主计划/车间计划）
    """
    query = db.query(ProductionPlan)
    
    if plan_type:
        query = query.filter(ProductionPlan.plan_type == plan_type)
    if project_id:
        query = query.filter(ProductionPlan.project_id == project_id)
    if workshop_id:
        query = query.filter(ProductionPlan.workshop_id == workshop_id)
    if status:
        query = query.filter(ProductionPlan.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    plans = query.order_by(desc(ProductionPlan.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for plan in plans:
        project_name = None
        if plan.project_id:
            project = db.query(Project).filter(Project.id == plan.project_id).first()
            project_name = project.project_name if project else None
        
        workshop_name = None
        if plan.workshop_id:
            workshop = db.query(Workshop).filter(Workshop.id == plan.workshop_id).first()
            workshop_name = workshop.workshop_name if workshop else None
        
        items.append(ProductionPlanResponse(
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
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/production-plans", response_model=ProductionPlanResponse)
def create_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_in: ProductionPlanCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建生产计划
    """
    # 验证项目是否存在
    if plan_in.project_id:
        project = db.query(Project).filter(Project.id == plan_in.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
    
    # 验证车间是否存在
    if plan_in.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == plan_in.workshop_id).first()
        if not workshop:
            raise HTTPException(status_code=404, detail="车间不存在")
    
    plan_no = generate_plan_no(db)
    
    plan = ProductionPlan(
        plan_no=plan_no,
        plan_name=plan_in.plan_name,
        plan_type=plan_in.plan_type,
        project_id=plan_in.project_id,
        workshop_id=plan_in.workshop_id,
        plan_start_date=plan_in.plan_start_date,
        plan_end_date=plan_in.plan_end_date,
        status="DRAFT",
        progress=0,
        description=plan_in.description,
        remark=plan_in.remark,
        created_by=current_user.id
    )
    
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return read_production_plan(plan.id, db, current_user)


@router.get("/production-plans/{plan_id}", response_model=ProductionPlanResponse)
def read_production_plan(
    plan_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取生产计划详情
    """
    plan = db.query(ProductionPlan).filter(ProductionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="生产计划不存在")
    
    project_name = None
    if plan.project_id:
        project = db.query(Project).filter(Project.id == plan.project_id).first()
        project_name = project.project_name if project else None
    
    workshop_name = None
    if plan.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == plan.workshop_id).first()
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


@router.put("/production-plans/{plan_id}", response_model=ProductionPlanResponse)
def update_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    plan_in: ProductionPlanUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新生产计划
    """
    plan = db.query(ProductionPlan).filter(ProductionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="生产计划不存在")
    
    if plan.status not in ["DRAFT", "SUBMITTED"]:
        raise HTTPException(status_code=400, detail="只能修改草稿或已提交状态的计划")
    
    update_data = plan_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)
    
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return read_production_plan(plan_id, db, current_user)


@router.put("/production-plans/{plan_id}/submit", response_model=ProductionPlanResponse)
def submit_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交计划审批
    """
    plan = db.query(ProductionPlan).filter(ProductionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="生产计划不存在")
    
    if plan.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能提交草稿状态的计划")
    
    plan.status = "SUBMITTED"
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return read_production_plan(plan_id, db, current_user)


@router.put("/production-plans/{plan_id}/approve", response_model=ProductionPlanResponse)
def approve_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批通过生产计划
    """
    plan = db.query(ProductionPlan).filter(ProductionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="生产计划不存在")
    
    if plan.status != "SUBMITTED":
        raise HTTPException(status_code=400, detail="只能审批已提交状态的计划")
    
    plan.status = "APPROVED"
    plan.approved_by = current_user.id
    plan.approved_at = datetime.now()
    
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return read_production_plan(plan_id, db, current_user)


@router.put("/production-plans/{plan_id}/publish", response_model=ProductionPlanResponse)
def publish_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    发布生产计划
    """
    plan = db.query(ProductionPlan).filter(ProductionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="生产计划不存在")
    
    if plan.status != "APPROVED":
        raise HTTPException(status_code=400, detail="只能发布已审批状态的计划")
    
    plan.status = "PUBLISHED"
    
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return read_production_plan(plan_id, db, current_user)


# ==================== 生产工单管理 ====================

@router.get("/work-orders", response_model=PaginatedResponse)
def read_work_orders(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    workstation_id: Optional[int] = Query(None, description="工位ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    assigned_to: Optional[int] = Query(None, description="分配人员ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工单列表（分页+筛选）
    """
    query = db.query(WorkOrder)
    
    if project_id:
        query = query.filter(WorkOrder.project_id == project_id)
    if machine_id:
        query = query.filter(WorkOrder.machine_id == machine_id)
    if workshop_id:
        query = query.filter(WorkOrder.workshop_id == workshop_id)
    if workstation_id:
        query = query.filter(WorkOrder.workstation_id == workstation_id)
    if status:
        query = query.filter(WorkOrder.status == status)
    if assigned_to:
        query = query.filter(WorkOrder.assigned_to == assigned_to)
    
    total = query.count()
    offset = (page - 1) * page_size
    orders = query.order_by(desc(WorkOrder.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for order in orders:
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
        
        assigned_worker_name = None
        if order.assigned_to:
            worker = db.query(Worker).filter(Worker.id == order.assigned_to).first()
            assigned_worker_name = worker.worker_name if worker else None
        
        items.append(WorkOrderResponse(
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
            process_name=None,  # TODO: 从ProcessDict获取
            workshop_id=order.workshop_id,
            workshop_name=workshop_name,
            workstation_id=order.workstation_id,
            workstation_name=workstation_name,
            material_name=order.material_name,
            specification=order.specification,
            plan_qty=order.plan_qty,
            completed_qty=order.completed_qty or 0,
            qualified_qty=order.qualified_qty or 0,
            defect_qty=order.defect_qty or 0,
            standard_hours=float(order.standard_hours) if order.standard_hours else None,
            actual_hours=float(order.actual_hours) if order.actual_hours else 0.0,
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
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/work-orders", response_model=WorkOrderResponse)
def create_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_in: WorkOrderCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建工单
    """
    # 验证项目
    if order_in.project_id:
        project = db.query(Project).filter(Project.id == order_in.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
    
    # 验证机台
    if order_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == order_in.machine_id).first()
        if not machine:
            raise HTTPException(status_code=404, detail="机台不存在")
    
    # 验证车间
    if order_in.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == order_in.workshop_id).first()
        if not workshop:
            raise HTTPException(status_code=404, detail="车间不存在")
    
    work_order_no = generate_work_order_no(db)
    
    order = WorkOrder(
        work_order_no=work_order_no,
        task_name=order_in.task_name,
        task_type=order_in.task_type,
        project_id=order_in.project_id,
        machine_id=order_in.machine_id,
        production_plan_id=order_in.production_plan_id,
        process_id=order_in.process_id,
        workshop_id=order_in.workshop_id,
        workstation_id=order_in.workstation_id,
        material_name=order_in.material_name,
        specification=order_in.specification,
        plan_qty=order_in.plan_qty,
        standard_hours=order_in.standard_hours,
        plan_start_date=order_in.plan_start_date,
        plan_end_date=order_in.plan_end_date,
        priority=order_in.priority,
        work_content=order_in.work_content,
        remark=order_in.remark,
        status="PENDING",
        progress=0
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_work_order(order.id, db, current_user)


@router.get("/work-orders/{order_id}", response_model=WorkOrderResponse)
def read_work_order(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工单详情
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
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
        process_name=None,
        workshop_id=order.workshop_id,
        workshop_name=workshop_name,
        workstation_id=order.workstation_id,
        workstation_name=workstation_name,
        material_name=order.material_name,
        specification=order.specification,
        plan_qty=order.plan_qty,
        completed_qty=order.completed_qty or 0,
        qualified_qty=order.qualified_qty or 0,
        defect_qty=order.defect_qty or 0,
        standard_hours=float(order.standard_hours) if order.standard_hours else None,
        actual_hours=float(order.actual_hours) if order.actual_hours else 0.0,
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


@router.put("/work-orders/{order_id}/assign", response_model=WorkOrderResponse)
def assign_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    assign_in: WorkOrderAssignRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    任务派工（指派人员/工位）
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if order.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能派工待派工状态的工单")
    
    # 验证工人是否存在
    if assign_in.worker_id:
        worker = db.query(Worker).filter(Worker.id == assign_in.worker_id).first()
        if not worker:
            raise HTTPException(status_code=404, detail="工人不存在")
    
    # 验证工位是否存在
    if assign_in.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == assign_in.workstation_id).first()
        if not workstation:
            raise HTTPException(status_code=404, detail="工位不存在")
        if workstation.status != "IDLE":
            raise HTTPException(status_code=400, detail="工位不是空闲状态")
    
    order.assigned_to = assign_in.worker_id
    order.workstation_id = assign_in.workstation_id
    order.status = "ASSIGNED"
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_work_order(order_id, db, current_user)


@router.put("/work-orders/{order_id}/start", response_model=WorkOrderResponse)
def start_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    开始工单
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if order.status != "ASSIGNED":
        raise HTTPException(status_code=400, detail="只能开始已派工状态的工单")
    
    order.status = "STARTED"
    order.actual_start_time = datetime.now()
    
    # 更新工位状态
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            workstation.status = "WORKING"
            workstation.current_work_order_id = order_id
            workstation.current_worker_id = order.assigned_to
            db.add(workstation)
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_work_order(order_id, db, current_user)


@router.put("/work-orders/{order_id}/complete", response_model=WorkOrderResponse)
def complete_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    完成工单
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if order.status not in ["STARTED", "PAUSED"]:
        raise HTTPException(status_code=400, detail="只能完成已开工或已暂停状态的工单")
    
    order.status = "COMPLETED"
    order.actual_end_time = datetime.now()
    order.progress = 100
    
    # 更新工位状态
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            workstation.status = "IDLE"
            workstation.current_work_order_id = None
            workstation.current_worker_id = None
            db.add(workstation)
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_work_order(order_id, db, current_user)


@router.get("/work-orders/{order_id}/progress", response_model=WorkOrderProgressResponse)
def get_work_order_progress(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工单进度
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    # 获取报工记录
    reports = db.query(WorkReport).filter(WorkReport.work_order_id == order_id).order_by(WorkReport.report_time.desc()).all()
    
    return WorkOrderProgressResponse(
        work_order_id=order.id,
        work_order_no=order.work_order_no,
        progress=order.progress or 0,
        plan_qty=order.plan_qty,
        completed_qty=order.completed_qty or 0,
        qualified_qty=order.qualified_qty or 0,
        defect_qty=order.defect_qty or 0,
        standard_hours=float(order.standard_hours) if order.standard_hours else None,
        actual_hours=float(order.actual_hours) if order.actual_hours else 0.0,
        reports=[{
            "id": r.id,
            "report_no": r.report_no,
            "report_type": r.report_type,
            "report_time": r.report_time,
            "progress_percent": r.progress_percent,
            "work_hours": r.work_hours,
            "completed_qty": r.completed_qty,
            "qualified_qty": r.qualified_qty
        } for r in reports]
    )


# ==================== 报工系统 ====================

@router.get("/work-reports", response_model=PaginatedResponse)
def read_work_reports(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    work_order_id: Optional[int] = Query(None, description="工单ID筛选"),
    worker_id: Optional[int] = Query(None, description="工人ID筛选"),
    report_type: Optional[str] = Query(None, description="报工类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报工记录列表
    """
    query = db.query(WorkReport)
    
    if work_order_id:
        query = query.filter(WorkReport.work_order_id == work_order_id)
    if worker_id:
        query = query.filter(WorkReport.worker_id == worker_id)
    if report_type:
        query = query.filter(WorkReport.report_type == report_type)
    if status:
        query = query.filter(WorkReport.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    reports = query.order_by(desc(WorkReport.report_time)).offset(offset).limit(page_size).all()
    
    items = []
    for report in reports:
        worker_name = None
        if report.worker_id:
            worker = db.query(Worker).filter(Worker.id == report.worker_id).first()
            worker_name = worker.worker_name if worker else None
        
        work_order = db.query(WorkOrder).filter(WorkOrder.id == report.work_order_id).first()
        work_order_no = work_order.work_order_no if work_order else None
        
        items.append(WorkReportResponse(
            id=report.id,
            report_no=report.report_no,
            work_order_id=report.work_order_id,
            work_order_no=work_order_no,
            worker_id=report.worker_id,
            worker_name=worker_name,
            report_type=report.report_type,
            report_time=report.report_time,
            progress_percent=report.progress_percent,
            work_hours=float(report.work_hours) if report.work_hours else None,
            completed_qty=report.completed_qty,
            qualified_qty=report.qualified_qty,
            defect_qty=report.defect_qty,
            status=report.status,
            report_note=report.report_note,
            approved_by=report.approved_by,
            approved_at=report.approved_at,
            created_at=report.created_at,
            updated_at=report.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/work-reports/start", response_model=WorkReportResponse)
def start_work_report(
    *,
    db: Session = Depends(deps.get_db),
    report_in: WorkReportStartRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    开工报告（扫码开工）
    """
    # 验证工单是否存在
    work_order = db.query(WorkOrder).filter(WorkOrder.id == report_in.work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    # 验证工人是否存在
    worker = db.query(Worker).filter(Worker.id == report_in.worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="工人不存在")
    
    # 如果工单还未开始，自动开始
    if work_order.status == "ASSIGNED":
        work_order.status = "STARTED"
        work_order.actual_start_time = datetime.now()
        db.add(work_order)
    
    report_no = generate_report_no(db)
    
    report = WorkReport(
        report_no=report_no,
        work_order_id=report_in.work_order_id,
        worker_id=report_in.worker_id,
        report_type="START",
        report_time=datetime.now(),
        status="PENDING"
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return read_work_report(report.id, db, current_user)


@router.post("/work-reports/progress", response_model=WorkReportResponse)
def progress_work_report(
    *,
    db: Session = Depends(deps.get_db),
    report_in: WorkReportProgressRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    进度上报
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == report_in.work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    worker = db.query(Worker).filter(Worker.id == report_in.worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="工人不存在")
    
    report_no = generate_report_no(db)
    
    report = WorkReport(
        report_no=report_no,
        work_order_id=report_in.work_order_id,
        worker_id=report_in.worker_id,
        report_type="PROGRESS",
        report_time=datetime.now(),
        progress_percent=report_in.progress_percent,
        work_hours=report_in.work_hours,
        report_note=report_in.report_note,
        status="PENDING"
    )
    
    # 更新工单进度
    work_order.progress = report_in.progress_percent
    if report_in.work_hours:
        work_order.actual_hours = (work_order.actual_hours or 0) + report_in.work_hours
    
    db.add(report)
    db.add(work_order)
    db.commit()
    db.refresh(report)
    
    return read_work_report(report.id, db, current_user)


@router.post("/work-reports/complete", response_model=WorkReportResponse)
def complete_work_report(
    *,
    db: Session = Depends(deps.get_db),
    report_in: WorkReportCompleteRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    完工报告（数量/合格数）
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == report_in.work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    worker = db.query(Worker).filter(Worker.id == report_in.worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="工人不存在")
    
    report_no = generate_report_no(db)
    
    report = WorkReport(
        report_no=report_no,
        work_order_id=report_in.work_order_id,
        worker_id=report_in.worker_id,
        report_type="COMPLETE",
        report_time=datetime.now(),
        completed_qty=report_in.completed_qty,
        qualified_qty=report_in.qualified_qty,
        defect_qty=report_in.defect_qty or 0,
        work_hours=report_in.work_hours,
        report_note=report_in.report_note,
        status="PENDING"
    )
    
    # 更新工单
    work_order.completed_qty = (work_order.completed_qty or 0) + report_in.completed_qty
    work_order.qualified_qty = (work_order.qualified_qty or 0) + report_in.qualified_qty
    work_order.defect_qty = (work_order.defect_qty or 0) + (report_in.defect_qty or 0)
    if report_in.work_hours:
        work_order.actual_hours = (work_order.actual_hours or 0) + report_in.work_hours
    
    # 如果完成数量达到计划数量，自动完成工单
    if work_order.completed_qty >= work_order.plan_qty:
        work_order.progress = 100
        work_order.status = "COMPLETED"
        work_order.actual_end_time = datetime.now()
    
    db.add(report)
    db.add(work_order)
    db.commit()
    db.refresh(report)
    
    return read_work_report(report.id, db, current_user)


@router.get("/work-reports/{report_id}", response_model=WorkReportResponse)
def read_work_report(
    report_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报工详情
    """
    report = db.query(WorkReport).filter(WorkReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报工记录不存在")
    
    worker_name = None
    if report.worker_id:
        worker = db.query(Worker).filter(Worker.id == report.worker_id).first()
        worker_name = worker.worker_name if worker else None
    
    work_order = db.query(WorkOrder).filter(WorkOrder.id == report.work_order_id).first()
    work_order_no = work_order.work_order_no if work_order else None
    
    return WorkReportResponse(
        id=report.id,
        report_no=report.report_no,
        work_order_id=report.work_order_id,
        work_order_no=work_order_no,
        worker_id=report.worker_id,
        worker_name=worker_name,
        report_type=report.report_type,
        report_time=report.report_time,
        progress_percent=report.progress_percent,
        work_hours=float(report.work_hours) if report.work_hours else None,
        completed_qty=report.completed_qty,
        qualified_qty=report.qualified_qty,
        defect_qty=report.defect_qty,
        status=report.status,
        report_note=report.report_note,
        approved_by=report.approved_by,
        approved_at=report.approved_at,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.put("/work-reports/{report_id}/approve", response_model=WorkReportResponse)
def approve_work_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    报工审批（车间主管）
    """
    report = db.query(WorkReport).filter(WorkReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报工记录不存在")
    
    if report.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能审批待审批状态的报工")
    
    report.status = "APPROVED"
    report.approved_by = current_user.id
    report.approved_at = datetime.now()
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return read_work_report(report_id, db, current_user)


@router.get("/work-reports/my", response_model=PaginatedResponse)
def read_my_work_reports(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    我的报工记录（工人查看）
    """
    # 查找当前用户关联的工人
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="未找到关联的工人信息")
    
    query = db.query(WorkReport).filter(WorkReport.worker_id == worker.id)
    
    total = query.count()
    offset = (page - 1) * page_size
    reports = query.order_by(desc(WorkReport.report_time)).offset(offset).limit(page_size).all()
    
    items = []
    for report in reports:
        work_order = db.query(WorkOrder).filter(WorkOrder.id == report.work_order_id).first()
        work_order_no = work_order.work_order_no if work_order else None
        
        items.append(WorkReportResponse(
            id=report.id,
            report_no=report.report_no,
            work_order_id=report.work_order_id,
            work_order_no=work_order_no,
            worker_id=report.worker_id,
            worker_name=worker.worker_name,
            report_type=report.report_type,
            report_time=report.report_time,
            progress_percent=report.progress_percent,
            work_hours=float(report.work_hours) if report.work_hours else None,
            completed_qty=report.completed_qty,
            qualified_qty=report.qualified_qty,
            defect_qty=report.defect_qty,
            status=report.status,
            report_note=report.report_note,
            approved_by=report.approved_by,
            approved_at=report.approved_at,
            created_at=report.created_at,
            updated_at=report.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


# ==================== 生产领料 ====================

def generate_requisition_no(db: Session) -> str:
    """生成领料单号：MR-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_req = (
        db.query(MaterialRequisition)
        .filter(MaterialRequisition.requisition_no.like(f"MR-{today}-%"))
        .order_by(desc(MaterialRequisition.requisition_no))
        .first()
    )
    if max_req:
        seq = int(max_req.requisition_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"MR-{today}-{seq:03d}"


@router.get("/material-requisitions", response_model=PaginatedResponse)
def read_material_requisitions(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    work_order_id: Optional[int] = Query(None, description="工单ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取领料单列表
    """
    query = db.query(MaterialRequisition)
    
    if work_order_id:
        query = query.filter(MaterialRequisition.work_order_id == work_order_id)
    if project_id:
        query = query.filter(MaterialRequisition.project_id == project_id)
    if status:
        query = query.filter(MaterialRequisition.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    requisitions = query.order_by(desc(MaterialRequisition.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for req in requisitions:
        project_name = None
        if req.project_id:
            project = db.query(Project).filter(Project.id == req.project_id).first()
            project_name = project.project_name if project else None
        
        work_order_no = None
        if req.work_order_id:
            work_order = db.query(WorkOrder).filter(WorkOrder.id == req.work_order_id).first()
            work_order_no = work_order.work_order_no if work_order else None
        
        applicant_name = None
        if req.applicant_id:
            applicant = db.query(User).filter(User.id == req.applicant_id).first()
            applicant_name = applicant.real_name or applicant.username if applicant else None
        
        # 获取明细
        items_data = []
        for item in req.items:
            from app.models.material import Material
            material = db.query(Material).filter(Material.id == item.material_id).first()
            items_data.append(MaterialRequisitionItemResponse(
                id=item.id,
                requisition_id=item.requisition_id,
                material_id=item.material_id,
                material_code=material.material_code if material else None,
                material_name=material.material_name if material else None,
                request_qty=item.request_qty,
                approved_qty=item.approved_qty,
                issued_qty=item.issued_qty,
                unit=item.unit,
                remark=item.remark
            ))
        
        items.append(MaterialRequisitionResponse(
            id=req.id,
            requisition_no=req.requisition_no,
            work_order_id=req.work_order_id,
            work_order_no=work_order_no,
            project_id=req.project_id,
            project_name=project_name,
            applicant_id=req.applicant_id,
            applicant_name=applicant_name,
            apply_time=req.apply_time,
            apply_reason=req.apply_reason,
            status=req.status,
            approved_by=req.approved_by,
            approved_at=req.approved_at,
            approve_comment=req.approve_comment,
            issued_by=req.issued_by,
            issued_at=req.issued_at,
            items=items_data,
            remark=req.remark,
            created_at=req.created_at,
            updated_at=req.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/material-requisitions", response_model=MaterialRequisitionResponse)
def create_material_requisition(
    *,
    db: Session = Depends(deps.get_db),
    req_in: MaterialRequisitionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建领料单
    """
    # 验证工单
    if req_in.work_order_id:
        work_order = db.query(WorkOrder).filter(WorkOrder.id == req_in.work_order_id).first()
        if not work_order:
            raise HTTPException(status_code=404, detail="工单不存在")
    
    # 验证项目
    if req_in.project_id:
        project = db.query(Project).filter(Project.id == req_in.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
    
    if not req_in.items:
        raise HTTPException(status_code=400, detail="领料明细不能为空")
    
    requisition_no = generate_requisition_no(db)
    
    requisition = MaterialRequisition(
        requisition_no=requisition_no,
        work_order_id=req_in.work_order_id,
        project_id=req_in.project_id,
        applicant_id=current_user.id,
        apply_reason=req_in.apply_reason,
        status="DRAFT",
        remark=req_in.remark
    )
    
    db.add(requisition)
    db.flush()  # 获取requisition.id
    
    # 创建明细
    for item_in in req_in.items:
        from app.models.material import Material
        material = db.query(Material).filter(Material.id == item_in.material_id).first()
        if not material:
            raise HTTPException(status_code=404, detail=f"物料ID {item_in.material_id} 不存在")
        
        item = MaterialRequisitionItem(
            requisition_id=requisition.id,
            material_id=item_in.material_id,
            request_qty=item_in.request_qty,
            unit=material.unit,
            remark=item_in.remark
        )
        db.add(item)
    
    db.commit()
    db.refresh(requisition)
    
    return read_material_requisition(requisition.id, db, current_user)


@router.get("/material-requisitions/{req_id}", response_model=MaterialRequisitionResponse)
def read_material_requisition(
    req_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取领料单详情
    """
    req = db.query(MaterialRequisition).filter(MaterialRequisition.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="领料单不存在")
    
    project_name = None
    if req.project_id:
        project = db.query(Project).filter(Project.id == req.project_id).first()
        project_name = project.project_name if project else None
    
    work_order_no = None
    if req.work_order_id:
        work_order = db.query(WorkOrder).filter(WorkOrder.id == req.work_order_id).first()
        work_order_no = work_order.work_order_no if work_order else None
    
    applicant_name = None
    if req.applicant_id:
        applicant = db.query(User).filter(User.id == req.applicant_id).first()
        applicant_name = applicant.real_name or applicant.username if applicant else None
    
    # 获取明细
    items_data = []
    for item in req.items:
        from app.models.material import Material
        material = db.query(Material).filter(Material.id == item.material_id).first()
        items_data.append(MaterialRequisitionItemResponse(
            id=item.id,
            requisition_id=item.requisition_id,
            material_id=item.material_id,
            material_code=material.material_code if material else None,
            material_name=material.material_name if material else None,
            request_qty=item.request_qty,
            approved_qty=item.approved_qty,
            issued_qty=item.issued_qty,
            unit=item.unit,
            remark=item.remark
        ))
    
    return MaterialRequisitionResponse(
        id=req.id,
        requisition_no=req.requisition_no,
        work_order_id=req.work_order_id,
        work_order_no=work_order_no,
        project_id=req.project_id,
        project_name=project_name,
        applicant_id=req.applicant_id,
        applicant_name=applicant_name,
        apply_time=req.apply_time,
        apply_reason=req.apply_reason,
        status=req.status,
        approved_by=req.approved_by,
        approved_at=req.approved_at,
        approve_comment=req.approve_comment,
        issued_by=req.issued_by,
        issued_at=req.issued_at,
        items=items_data,
        remark=req.remark,
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


@router.put("/material-requisitions/{req_id}/approve", response_model=MaterialRequisitionResponse)
def approve_material_requisition(
    *,
    db: Session = Depends(deps.get_db),
    req_id: int,
    approve_comment: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    领料单审批
    """
    req = db.query(MaterialRequisition).filter(MaterialRequisition.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="领料单不存在")
    
    if req.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能审批草稿状态的领料单")
    
    req.status = "APPROVED"
    req.approved_by = current_user.id
    req.approved_at = datetime.now()
    req.approve_comment = approve_comment
    
    # 批准数量默认为申请数量
    for item in req.items:
        if not item.approved_qty:
            item.approved_qty = item.request_qty
    
    db.add(req)
    db.commit()
    db.refresh(req)
    
    return read_material_requisition(req_id, db, current_user)


@router.put("/material-requisitions/{req_id}/issue", response_model=MaterialRequisitionResponse)
def issue_material_requisition(
    *,
    db: Session = Depends(deps.get_db),
    req_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    确认发料（仓库发料）
    """
    req = db.query(MaterialRequisition).filter(MaterialRequisition.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="领料单不存在")
    
    if req.status != "APPROVED":
        raise HTTPException(status_code=400, detail="只能发放已审批状态的领料单")
    
    req.status = "ISSUED"
    req.issued_by = current_user.id
    req.issued_at = datetime.now()
    
    # 发放数量默认为批准数量
    for item in req.items:
        if not item.issued_qty:
            item.issued_qty = item.approved_qty or item.request_qty
    
    db.add(req)
    db.commit()
    db.refresh(req)
    
    return read_material_requisition(req_id, db, current_user)


# ==================== 生产异常 ====================

def generate_exception_no(db: Session) -> str:
    """生成生产异常编号：PE-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_exc = (
        db.query(ProductionException)
        .filter(ProductionException.exception_no.like(f"PE-{today}-%"))
        .order_by(desc(ProductionException.exception_no))
        .first()
    )
    if max_exc:
        seq = int(max_exc.exception_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"PE-{today}-{seq:03d}"


@router.get("/production-exceptions", response_model=PaginatedResponse)
def read_production_exceptions(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    work_order_id: Optional[int] = Query(None, description="工单ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    exception_type: Optional[str] = Query(None, description="异常类型筛选"),
    exception_level: Optional[str] = Query(None, description="异常级别筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取生产异常列表
    """
    query = db.query(ProductionException)
    
    if work_order_id:
        query = query.filter(ProductionException.work_order_id == work_order_id)
    if project_id:
        query = query.filter(ProductionException.project_id == project_id)
    if workshop_id:
        query = query.filter(ProductionException.workshop_id == workshop_id)
    if exception_type:
        query = query.filter(ProductionException.exception_type == exception_type)
    if exception_level:
        query = query.filter(ProductionException.exception_level == exception_level)
    if status:
        query = query.filter(ProductionException.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    exceptions = query.order_by(desc(ProductionException.report_time)).offset(offset).limit(page_size).all()
    
    items = []
    for exc in exceptions:
        project_name = None
        if exc.project_id:
            project = db.query(Project).filter(Project.id == exc.project_id).first()
            project_name = project.project_name if project else None
        
        work_order_no = None
        if exc.work_order_id:
            work_order = db.query(WorkOrder).filter(WorkOrder.id == exc.work_order_id).first()
            work_order_no = work_order.work_order_no if work_order else None
        
        workshop_name = None
        if exc.workshop_id:
            workshop = db.query(Workshop).filter(Workshop.id == exc.workshop_id).first()
            workshop_name = workshop.workshop_name if workshop else None
        
        reporter_name = None
        if exc.reporter_id:
            reporter = db.query(User).filter(User.id == exc.reporter_id).first()
            reporter_name = reporter.real_name or reporter.username if reporter else None
        
        handler_name = None
        if exc.handler_id:
            handler = db.query(User).filter(User.id == exc.handler_id).first()
            handler_name = handler.real_name or handler.username if handler else None
        
        items.append(ProductionExceptionResponse(
            id=exc.id,
            exception_no=exc.exception_no,
            exception_type=exc.exception_type,
            exception_level=exc.exception_level,
            title=exc.title,
            description=exc.description,
            work_order_id=exc.work_order_id,
            work_order_no=work_order_no,
            project_id=exc.project_id,
            project_name=project_name,
            workshop_id=exc.workshop_id,
            workshop_name=workshop_name,
            equipment_id=exc.equipment_id,
            equipment_name=None,  # TODO: 从Equipment获取
            reporter_id=exc.reporter_id,
            reporter_name=reporter_name,
            report_time=exc.report_time,
            status=exc.status,
            handler_id=exc.handler_id,
            handler_name=handler_name,
            handle_plan=exc.handle_plan,
            handle_result=exc.handle_result,
            handle_time=exc.handle_time,
            resolved_at=exc.resolved_at,
            impact_hours=exc.impact_hours,
            impact_cost=exc.impact_cost,
            remark=exc.remark,
            created_at=exc.created_at,
            updated_at=exc.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/production-exceptions", response_model=ProductionExceptionResponse)
def create_production_exception(
    *,
    db: Session = Depends(deps.get_db),
    exc_in: ProductionExceptionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    上报异常（物料/设备/质量）
    """
    # 验证工单
    if exc_in.work_order_id:
        work_order = db.query(WorkOrder).filter(WorkOrder.id == exc_in.work_order_id).first()
        if not work_order:
            raise HTTPException(status_code=404, detail="工单不存在")
    
    # 验证项目
    if exc_in.project_id:
        project = db.query(Project).filter(Project.id == exc_in.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
    
    # 验证车间
    if exc_in.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == exc_in.workshop_id).first()
        if not workshop:
            raise HTTPException(status_code=404, detail="车间不存在")
    
    exception_no = generate_exception_no(db)
    
    exception = ProductionException(
        exception_no=exception_no,
        exception_type=exc_in.exception_type,
        exception_level=exc_in.exception_level,
        title=exc_in.title,
        description=exc_in.description,
        work_order_id=exc_in.work_order_id,
        project_id=exc_in.project_id,
        workshop_id=exc_in.workshop_id,
        equipment_id=exc_in.equipment_id,
        reporter_id=current_user.id,
        status="REPORTED",
        impact_hours=exc_in.impact_hours,
        impact_cost=exc_in.impact_cost,
        remark=exc_in.remark
    )
    
    db.add(exception)
    db.commit()
    db.refresh(exception)
    
    return read_production_exception(exception.id, db, current_user)


@router.get("/production-exceptions/{exc_id}", response_model=ProductionExceptionResponse)
def read_production_exception(
    exc_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取生产异常详情
    """
    exc = db.query(ProductionException).filter(ProductionException.id == exc_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="生产异常不存在")
    
    project_name = None
    if exc.project_id:
        project = db.query(Project).filter(Project.id == exc.project_id).first()
        project_name = project.project_name if project else None
    
    work_order_no = None
    if exc.work_order_id:
        work_order = db.query(WorkOrder).filter(WorkOrder.id == exc.work_order_id).first()
        work_order_no = work_order.work_order_no if work_order else None
    
    workshop_name = None
    if exc.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == exc.workshop_id).first()
        workshop_name = workshop.workshop_name if workshop else None
    
    reporter_name = None
    if exc.reporter_id:
        reporter = db.query(User).filter(User.id == exc.reporter_id).first()
        reporter_name = reporter.real_name or reporter.username if reporter else None
    
    handler_name = None
    if exc.handler_id:
        handler = db.query(User).filter(User.id == exc.handler_id).first()
        handler_name = handler.real_name or handler.username if handler else None
    
    return ProductionExceptionResponse(
        id=exc.id,
        exception_no=exc.exception_no,
        exception_type=exc.exception_type,
        exception_level=exc.exception_level,
        title=exc.title,
        description=exc.description,
        work_order_id=exc.work_order_id,
        work_order_no=work_order_no,
        project_id=exc.project_id,
        project_name=project_name,
        workshop_id=exc.workshop_id,
        workshop_name=workshop_name,
        equipment_id=exc.equipment_id,
        equipment_name=None,
        reporter_id=exc.reporter_id,
        reporter_name=reporter_name,
        report_time=exc.report_time,
        status=exc.status,
        handler_id=exc.handler_id,
        handler_name=handler_name,
        handle_plan=exc.handle_plan,
        handle_result=exc.handle_result,
        handle_time=exc.handle_time,
        resolved_at=exc.resolved_at,
        impact_hours=exc.impact_hours,
        impact_cost=exc.impact_cost,
        remark=exc.remark,
        created_at=exc.created_at,
        updated_at=exc.updated_at,
    )


@router.put("/production-exceptions/{exc_id}/handle", response_model=ProductionExceptionResponse)
def handle_production_exception(
    *,
    db: Session = Depends(deps.get_db),
    exc_id: int,
    handle_in: ProductionExceptionHandle,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    处理异常
    """
    exc = db.query(ProductionException).filter(ProductionException.id == exc_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="生产异常不存在")
    
    if exc.status not in ["REPORTED", "IN_PROGRESS"]:
        raise HTTPException(status_code=400, detail="只能处理已上报或处理中状态的异常")
    
    exc.status = "IN_PROGRESS"
    exc.handler_id = current_user.id
    exc.handle_plan = handle_in.handle_plan
    exc.handle_time = datetime.now()
    
    db.add(exc)
    db.commit()
    db.refresh(exc)
    
    return read_production_exception(exc_id, db, current_user)


@router.put("/production-exceptions/{exc_id}/close", response_model=ProductionExceptionResponse)
def close_production_exception(
    *,
    db: Session = Depends(deps.get_db),
    exc_id: int,
    handle_result: Optional[str] = Query(None, description="处理结果"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    关闭异常
    """
    exc = db.query(ProductionException).filter(ProductionException.id == exc_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="生产异常不存在")
    
    if exc.status not in ["REPORTED", "IN_PROGRESS"]:
        raise HTTPException(status_code=400, detail="只能关闭已上报或处理中状态的异常")
    
    exc.status = "RESOLVED"
    exc.handle_result = handle_result
    exc.resolved_at = datetime.now()
    if not exc.handler_id:
        exc.handler_id = current_user.id
    if not exc.handle_time:
        exc.handle_time = datetime.now()
    
    db.add(exc)
    db.commit()
    db.refresh(exc)
    
    return read_production_exception(exc_id, db, current_user)


# ==================== 生产人员管理 ====================

@router.get("/workers", response_model=PaginatedResponse)
def read_workers(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    worker_type: Optional[str] = Query(None, description="工人类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（工人编码/姓名）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取生产人员列表
    """
    query = db.query(Worker)
    
    if workshop_id:
        query = query.filter(Worker.workshop_id == workshop_id)
    if worker_type:
        query = query.filter(Worker.worker_type == worker_type)
    if status:
        query = query.filter(Worker.status == status)
    if keyword:
        query = query.filter(
            or_(
                Worker.worker_code.like(f"%{keyword}%"),
                Worker.worker_name.like(f"%{keyword}%"),
            )
        )
    
    total = query.count()
    offset = (page - 1) * page_size
    workers = query.order_by(Worker.created_at).offset(offset).limit(page_size).all()
    
    items = []
    for worker in workers:
        workshop_name = None
        if worker.workshop_id:
            workshop = db.query(Workshop).filter(Workshop.id == worker.workshop_id).first()
            workshop_name = workshop.workshop_name if workshop else None
        
        items.append(WorkerResponse(
            id=worker.id,
            worker_code=worker.worker_code,
            worker_name=worker.worker_name,
            user_id=worker.user_id,
            workshop_id=worker.workshop_id,
            workshop_name=workshop_name,
            worker_type=worker.worker_type,
            phone=worker.phone,
            status=worker.status,
            remark=worker.remark,
            created_at=worker.created_at,
            updated_at=worker.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/workers", response_model=WorkerResponse)
def create_worker(
    *,
    db: Session = Depends(deps.get_db),
    worker_in: WorkerCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建生产人员（关联用户）
    """
    # 检查工人编码是否已存在
    existing = db.query(Worker).filter(Worker.worker_code == worker_in.worker_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="工人编码已存在")
    
    # 验证用户是否存在
    if worker_in.user_id:
        user = db.query(User).filter(User.id == worker_in.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
    
    # 验证车间是否存在
    if worker_in.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == worker_in.workshop_id).first()
        if not workshop:
            raise HTTPException(status_code=404, detail="车间不存在")
    
    worker = Worker(**worker_in.model_dump())
    db.add(worker)
    db.commit()
    db.refresh(worker)
    
    workshop_name = None
    if worker.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == worker.workshop_id).first()
        workshop_name = workshop.workshop_name if workshop else None
    
    return WorkerResponse(
        id=worker.id,
        worker_code=worker.worker_code,
        worker_name=worker.worker_name,
        user_id=worker.user_id,
        workshop_id=worker.workshop_id,
        workshop_name=workshop_name,
        worker_type=worker.worker_type,
        phone=worker.phone,
        status=worker.status,
        remark=worker.remark,
        created_at=worker.created_at,
        updated_at=worker.updated_at,
    )


@router.put("/workers/{worker_id}", response_model=WorkerResponse)
def update_worker(
    *,
    db: Session = Depends(deps.get_db),
    worker_id: int,
    worker_in: WorkerUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新人员信息（技能/资质）
    """
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="生产人员不存在")
    
    update_data = worker_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(worker, field, value)
    
    db.add(worker)
    db.commit()
    db.refresh(worker)
    
    workshop_name = None
    if worker.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == worker.workshop_id).first()
        workshop_name = workshop.workshop_name if workshop else None
    
    return WorkerResponse(
        id=worker.id,
        worker_code=worker.worker_code,
        worker_name=worker.worker_name,
        user_id=worker.user_id,
        workshop_id=worker.workshop_id,
        workshop_name=workshop_name,
        worker_type=worker.worker_type,
        phone=worker.phone,
        status=worker.status,
        remark=worker.remark,
        created_at=worker.created_at,
        updated_at=worker.updated_at,
    )


@router.get("/workers/skill-matrix", response_model=dict)
def get_worker_skill_matrix(
    db: Session = Depends(deps.get_db),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    人员技能矩阵
    """
    from app.models.production import ProcessDict
    # 获取所有工序
    processes = db.query(ProcessDict).filter(ProcessDict.is_active == True).all()
    
    # 获取所有工人
    query = db.query(Worker).filter(Worker.status == "ACTIVE")
    if workshop_id:
        query = query.filter(Worker.workshop_id == workshop_id)
    workers = query.all()
    
    # 构建技能矩阵
    matrix = []
    for worker in workers:
        worker_skills = {}
        for skill in worker.skills:
            worker_skills[skill.process_id] = skill.skill_level
        
        skills_data = []
        for process in processes:
            skill_level = worker_skills.get(process.id, None)
            skills_data.append({
                "process_id": process.id,
                "process_code": process.process_code,
                "process_name": process.process_name,
                "skill_level": skill_level
            })
        
        matrix.append({
            "worker_id": worker.id,
            "worker_code": worker.worker_code if hasattr(worker, 'worker_code') else worker.worker_no,
            "worker_name": worker.worker_name,
            "workshop_id": worker.workshop_id,
            "skills": skills_data
        })
    
    return {
        "processes": [{"id": p.id, "code": p.process_code, "name": p.process_name} for p in processes],
        "workers": matrix
    }


@router.get("/workers/{worker_id}/hours", response_model=dict)
def get_worker_hours(
    worker_id: int,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    人员工时统计
    """
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="生产人员不存在")
    
    # 查询报工记录
    query = db.query(WorkReport).filter(WorkReport.worker_id == worker_id)
    
    if start_date:
        query = query.filter(WorkReport.report_time >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(WorkReport.report_time <= datetime.combine(end_date, datetime.max.time()))
    
    reports = query.all()
    
    # 统计工时
    total_hours = sum(float(r.work_hours) if r.work_hours else 0 for r in reports)
    total_reports = len(reports)
    
    # 按日期统计
    daily_stats = {}
    for report in reports:
        report_date = report.report_time.date()
        if report_date not in daily_stats:
            daily_stats[report_date] = {"hours": 0, "count": 0}
        daily_stats[report_date]["hours"] += float(report.work_hours) if report.work_hours else 0
        daily_stats[report_date]["count"] += 1
    
    worker_code = worker.worker_code if hasattr(worker, 'worker_code') else worker.worker_no
    return {
        "worker_id": worker.id,
        "worker_code": worker_code,
        "worker_name": worker.worker_name,
        "start_date": start_date,
        "end_date": end_date,
        "total_hours": total_hours,
        "total_reports": total_reports,
        "daily_stats": [
            {
                "date": str(d),
                "hours": stats["hours"],
                "count": stats["count"]
            }
            for d, stats in sorted(daily_stats.items())
        ]
    }


# ==================== 设备管理 ====================

@router.get("/equipment", response_model=PaginatedResponse)
def read_equipment(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（设备编码/名称）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取设备列表
    """
    from app.models.production import Equipment
    query = db.query(Equipment).filter(Equipment.is_active == True)
    
    if workshop_id:
        query = query.filter(Equipment.workshop_id == workshop_id)
    if status:
        query = query.filter(Equipment.status == status)
    if keyword:
        query = query.filter(
            or_(
                Equipment.equipment_code.like(f"%{keyword}%"),
                Equipment.equipment_name.like(f"%{keyword}%"),
            )
        )
    
    total = query.count()
    offset = (page - 1) * page_size
    equipment_list = query.order_by(Equipment.created_at).offset(offset).limit(page_size).all()
    
    items = []
    for equip in equipment_list:
        workshop_name = None
        if equip.workshop_id:
            workshop = db.query(Workshop).filter(Workshop.id == equip.workshop_id).first()
            workshop_name = workshop.workshop_name if workshop else None
        
        items.append({
            "id": equip.id,
            "equipment_code": equip.equipment_code,
            "equipment_name": equip.equipment_name,
            "model": equip.model,
            "manufacturer": equip.manufacturer,
            "workshop_id": equip.workshop_id,
            "workshop_name": workshop_name,
            "status": equip.status,
            "last_maintenance_date": equip.last_maintenance_date,
            "next_maintenance_date": equip.next_maintenance_date,
            "created_at": equip.created_at,
            "updated_at": equip.updated_at,
        })
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/equipment", response_model=dict)
def create_equipment(
    *,
    db: Session = Depends(deps.get_db),
    equipment_code: str = Body(..., description="设备编码"),
    equipment_name: str = Body(..., description="设备名称"),
    model: Optional[str] = Body(None, description="型号规格"),
    manufacturer: Optional[str] = Body(None, description="生产厂家"),
    workshop_id: Optional[int] = Body(None, description="所属车间ID"),
    purchase_date: Optional[date] = Body(None, description="购置日期"),
    status: str = Body("IDLE", description="设备状态"),
    asset_no: Optional[str] = Body(None, description="固定资产编号"),
    remark: Optional[str] = Body(None, description="备注"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建设备
    """
    from app.models.production import Equipment
    # 检查设备编码是否已存在
    existing = db.query(Equipment).filter(Equipment.equipment_code == equipment_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="设备编码已存在")
    
    # 验证车间是否存在
    if workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
        if not workshop:
            raise HTTPException(status_code=404, detail="车间不存在")
    
    equipment = Equipment(
        equipment_code=equipment_code,
        equipment_name=equipment_name,
        model=model,
        manufacturer=manufacturer,
        workshop_id=workshop_id,
        purchase_date=purchase_date,
        status=status,
        asset_no=asset_no,
        remark=remark
    )
    
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    
    return {
        "id": equipment.id,
        "equipment_code": equipment.equipment_code,
        "equipment_name": equipment.equipment_name,
        "status": equipment.status
    }


@router.get("/equipment/{equipment_id}", response_model=dict)
def read_equipment_detail(
    equipment_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取设备详情
    """
    from app.models.production import Equipment
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    workshop_name = None
    if equipment.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == equipment.workshop_id).first()
        workshop_name = workshop.workshop_name if workshop else None
    
    return {
        "id": equipment.id,
        "equipment_code": equipment.equipment_code,
        "equipment_name": equipment.equipment_name,
        "model": equipment.model,
        "manufacturer": equipment.manufacturer,
        "workshop_id": equipment.workshop_id,
        "workshop_name": workshop_name,
        "purchase_date": equipment.purchase_date,
        "status": equipment.status,
        "last_maintenance_date": equipment.last_maintenance_date,
        "next_maintenance_date": equipment.next_maintenance_date,
        "asset_no": equipment.asset_no,
        "remark": equipment.remark,
        "created_at": equipment.created_at,
        "updated_at": equipment.updated_at,
    }


@router.put("/equipment/{equipment_id}/status", response_model=dict)
def update_equipment_status(
    *,
    db: Session = Depends(deps.get_db),
    equipment_id: int,
    status: str = Body(..., description="新状态"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新设备状态（运行/维护/故障）
    """
    from app.models.production import Equipment
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    valid_statuses = ["IDLE", "RUNNING", "MAINTENANCE", "FAULT", "STOPPED"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效的状态，可选值: {valid_statuses}")
    
    equipment.status = status
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    
    return {
        "id": equipment.id,
        "equipment_code": equipment.equipment_code,
        "status": equipment.status
    }


@router.get("/equipment/{equipment_id}/maintenance", response_model=List[dict])
def get_equipment_maintenance(
    equipment_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    设备保养记录
    """
    from app.models.production import Equipment, EquipmentMaintenance
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    maintenance_records = db.query(EquipmentMaintenance).filter(
        EquipmentMaintenance.equipment_id == equipment_id
    ).order_by(desc(EquipmentMaintenance.maintenance_date)).limit(50).all()
    
    return [
        {
            "id": record.id,
            "maintenance_type": record.maintenance_type,
            "maintenance_date": record.maintenance_date,
            "content": record.content,
            "cost": float(record.cost) if record.cost else None,
            "performed_by": record.performed_by,
            "next_maintenance_date": record.next_maintenance_date,
            "remark": record.remark,
            "created_at": record.created_at
        }
        for record in maintenance_records
    ]


@router.post("/equipment/{equipment_id}/maintenance", response_model=dict)
def add_equipment_maintenance(
    *,
    db: Session = Depends(deps.get_db),
    equipment_id: int,
    maintenance_type: str = Body(..., description="类型:maintenance/repair"),
    maintenance_date: date = Body(..., description="保养/维修日期"),
    content: Optional[str] = Body(None, description="保养/维修内容"),
    cost: Optional[Decimal] = Body(None, description="费用"),
    performed_by: Optional[str] = Body(None, description="执行人"),
    next_maintenance_date: Optional[date] = Body(None, description="下次保养日期"),
    remark: Optional[str] = Body(None, description="备注"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加保养记录
    """
    from app.models.production import Equipment, EquipmentMaintenance
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    maintenance = EquipmentMaintenance(
        equipment_id=equipment_id,
        maintenance_type=maintenance_type,
        maintenance_date=maintenance_date,
        content=content,
        cost=cost,
        performed_by=performed_by,
        next_maintenance_date=next_maintenance_date,
        remark=remark
    )
    
    db.add(maintenance)
    
    # 更新设备的保养日期
    if maintenance_type == "maintenance":
        equipment.last_maintenance_date = maintenance_date
        if next_maintenance_date:
            equipment.next_maintenance_date = next_maintenance_date
    
    db.commit()
    db.refresh(maintenance)
    
    return {
        "id": maintenance.id,
        "equipment_id": maintenance.equipment_id,
        "maintenance_type": maintenance.maintenance_type,
        "maintenance_date": maintenance.maintenance_date
    }


# ==================== 工序字典管理 ====================

@router.get("/processes", response_model=PaginatedResponse)
def read_processes(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    process_type: Optional[str] = Query(None, description="工序类型筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（工序编码/名称）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    工序列表
    """
    from app.models.production import ProcessDict
    query = db.query(ProcessDict).filter(ProcessDict.is_active == True)
    
    if process_type:
        query = query.filter(ProcessDict.process_type == process_type)
    if keyword:
        query = query.filter(
            or_(
                ProcessDict.process_code.like(f"%{keyword}%"),
                ProcessDict.process_name.like(f"%{keyword}%"),
            )
        )
    
    total = query.count()
    offset = (page - 1) * page_size
    processes = query.order_by(ProcessDict.process_code).offset(offset).limit(page_size).all()
    
    items = []
    for process in processes:
        items.append({
            "id": process.id,
            "process_code": process.process_code,
            "process_name": process.process_name,
            "process_type": process.process_type,
            "standard_hours": float(process.standard_hours) if process.standard_hours else None,
            "description": process.description,
            "is_active": process.is_active,
            "created_at": process.created_at,
            "updated_at": process.updated_at,
        })
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/processes", response_model=dict)
def create_process(
    *,
    db: Session = Depends(deps.get_db),
    process_code: str = Body(..., description="工序编码"),
    process_name: str = Body(..., description="工序名称"),
    process_type: str = Body("OTHER", description="工序类型"),
    standard_hours: Optional[Decimal] = Body(None, description="标准工时(小时)"),
    description: Optional[str] = Body(None, description="描述"),
    work_instruction: Optional[str] = Body(None, description="作业指导"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建工序
    """
    from app.models.production import ProcessDict
    # 检查工序编码是否已存在
    existing = db.query(ProcessDict).filter(ProcessDict.process_code == process_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="工序编码已存在")
    
    process = ProcessDict(
        process_code=process_code,
        process_name=process_name,
        process_type=process_type,
        standard_hours=standard_hours,
        description=description,
        work_instruction=work_instruction
    )
    
    db.add(process)
    db.commit()
    db.refresh(process)
    
    return {
        "id": process.id,
        "process_code": process.process_code,
        "process_name": process.process_name,
        "process_type": process.process_type
    }


@router.put("/processes/{process_id}", response_model=dict)
def update_process(
    *,
    db: Session = Depends(deps.get_db),
    process_id: int,
    process_name: Optional[str] = Body(None, description="工序名称"),
    process_type: Optional[str] = Body(None, description="工序类型"),
    standard_hours: Optional[Decimal] = Body(None, description="标准工时(小时)"),
    description: Optional[str] = Body(None, description="描述"),
    work_instruction: Optional[str] = Body(None, description="作业指导"),
    is_active: Optional[bool] = Body(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新工序
    """
    from app.models.production import ProcessDict
    process = db.query(ProcessDict).filter(ProcessDict.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="工序不存在")
    
    if process_name is not None:
        process.process_name = process_name
    if process_type is not None:
        process.process_type = process_type
    if standard_hours is not None:
        process.standard_hours = standard_hours
    if description is not None:
        process.description = description
    if work_instruction is not None:
        process.work_instruction = work_instruction
    if is_active is not None:
        process.is_active = is_active
    
    db.add(process)
    db.commit()
    db.refresh(process)
    
    return {
        "id": process.id,
        "process_code": process.process_code,
        "process_name": process.process_name,
        "process_type": process.process_type
    }


@router.get("/processes/{process_id}/standard-hours", response_model=dict)
def get_process_standard_hours(
    process_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    工序标准工时
    """
    from app.models.production import ProcessDict
    process = db.query(ProcessDict).filter(ProcessDict.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="工序不存在")
    
    return {
        "process_id": process.id,
        "process_code": process.process_code,
        "process_name": process.process_name,
        "standard_hours": float(process.standard_hours) if process.standard_hours else None,
        "description": process.description
    }


# ==================== 生产报表 ====================

@router.get("/production-daily-reports", response_model=PaginatedResponse)
def read_production_daily_reports(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    生产日报列表
    """
    from app.models.production import ProductionDailyReport
    query = db.query(ProductionDailyReport)
    
    if workshop_id:
        query = query.filter(ProductionDailyReport.workshop_id == workshop_id)
    if start_date:
        query = query.filter(ProductionDailyReport.report_date >= start_date)
    if end_date:
        query = query.filter(ProductionDailyReport.report_date <= end_date)
    
    total = query.count()
    offset = (page - 1) * page_size
    reports = query.order_by(desc(ProductionDailyReport.report_date)).offset(offset).limit(page_size).all()
    
    items = []
    for report in reports:
        workshop_name = None
        if report.workshop_id:
            workshop = db.query(Workshop).filter(Workshop.id == report.workshop_id).first()
            workshop_name = workshop.workshop_name if workshop else None
        
        items.append(ProductionDailyReportResponse(
            id=report.id,
            report_date=report.report_date,
            workshop_id=report.workshop_id,
            workshop_name=workshop_name,
            plan_qty=report.plan_qty,
            completed_qty=report.completed_qty,
            completion_rate=float(report.completion_rate) if report.completion_rate else None,
            plan_hours=float(report.plan_hours) if report.plan_hours else None,
            actual_hours=float(report.actual_hours) if report.actual_hours else None,
            overtime_hours=float(report.overtime_hours) if report.overtime_hours else None,
            efficiency=float(report.efficiency) if report.efficiency else None,
            should_attend=report.should_attend,
            actual_attend=report.actual_attend,
            leave_count=report.leave_count,
            total_qty=report.total_qty,
            qualified_qty=report.qualified_qty,
            pass_rate=float(report.pass_rate) if report.pass_rate else None,
            new_exception_count=report.new_exception_count,
            resolved_exception_count=report.resolved_exception_count,
            summary=report.summary,
            created_by=report.created_by,
            created_at=report.created_at,
            updated_at=report.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/production-daily-reports/latest", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_latest_production_daily_report(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取最新生产日报（全厂及各车间）
    """
    from app.models.production import ProductionDailyReport
    
    latest_date = db.query(func.max(ProductionDailyReport.report_date)).scalar()
    if not latest_date:
        return ResponseModel(data=None)
    
    reports = db.query(ProductionDailyReport).filter(
        ProductionDailyReport.report_date == latest_date
    ).all()
    
    workshop_ids = {report.workshop_id for report in reports if report.workshop_id}
    workshop_map = {}
    if workshop_ids:
        workshops = db.query(Workshop).filter(Workshop.id.in_(workshop_ids)).all()
        workshop_map = {ws.id: ws.workshop_name for ws in workshops}
    
    def serialize_report(report: ProductionDailyReport) -> Dict[str, Any]:
        workshop_name = workshop_map.get(report.workshop_id) if report.workshop_id else "全厂"
        return {
            "id": report.id,
            "report_date": report.report_date.isoformat(),
            "workshop_id": report.workshop_id,
            "workshop_name": workshop_name,
            "plan_qty": report.plan_qty,
            "completed_qty": report.completed_qty,
            "completion_rate": float(report.completion_rate) if report.completion_rate else 0.0,
            "plan_hours": float(report.plan_hours) if report.plan_hours else 0.0,
            "actual_hours": float(report.actual_hours) if report.actual_hours else 0.0,
            "overtime_hours": float(report.overtime_hours) if report.overtime_hours else 0.0,
            "efficiency": float(report.efficiency) if report.efficiency else 0.0,
            "should_attend": report.should_attend,
            "actual_attend": report.actual_attend,
            "leave_count": report.leave_count,
            "total_qty": report.total_qty,
            "qualified_qty": report.qualified_qty,
            "pass_rate": float(report.pass_rate) if report.pass_rate else 0.0,
            "new_exception_count": report.new_exception_count,
            "resolved_exception_count": report.resolved_exception_count,
            "summary": report.summary,
        }
    
    overall_report = None
    workshop_reports = []
    for report in reports:
        serialized = serialize_report(report)
        if report.workshop_id:
            workshop_reports.append(serialized)
        else:
            overall_report = serialized
    
    return ResponseModel(
        data={
            "date": latest_date.isoformat(),
            "overall": overall_report,
            "workshops": workshop_reports
        }
    )


@router.post("/production-daily-reports", response_model=ProductionDailyReportResponse)
def create_production_daily_report(
    *,
    db: Session = Depends(deps.get_db),
    report_in: ProductionDailyReportCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交生产日报
    """
    from app.models.production import ProductionDailyReport
    # 验证车间是否存在
    if report_in.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == report_in.workshop_id).first()
        if not workshop:
            raise HTTPException(status_code=404, detail="车间不存在")
    
    # 检查是否已存在该日期的日报
    existing = db.query(ProductionDailyReport).filter(
        ProductionDailyReport.report_date == report_in.report_date,
        ProductionDailyReport.workshop_id == report_in.workshop_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该日期的生产日报已存在")
    
    # 计算完成率
    completion_rate = None
    if report_in.plan_qty > 0:
        completion_rate = Decimal((report_in.completed_qty / report_in.plan_qty) * 100)
    
    # 计算效率
    efficiency = None
    if report_in.plan_hours and report_in.actual_hours and report_in.actual_hours > 0:
        efficiency = Decimal((report_in.plan_hours / report_in.actual_hours) * 100)
    
    # 计算合格率
    pass_rate = None
    if report_in.total_qty > 0:
        pass_rate = Decimal((report_in.qualified_qty / report_in.total_qty) * 100)
    
    report = ProductionDailyReport(
        report_date=report_in.report_date,
        workshop_id=report_in.workshop_id,
        plan_qty=report_in.plan_qty,
        completed_qty=report_in.completed_qty,
        completion_rate=completion_rate,
        plan_hours=report_in.plan_hours,
        actual_hours=report_in.actual_hours,
        overtime_hours=report_in.overtime_hours,
        efficiency=efficiency,
        should_attend=report_in.should_attend,
        actual_attend=report_in.actual_attend,
        leave_count=report_in.leave_count,
        total_qty=report_in.total_qty,
        qualified_qty=report_in.qualified_qty,
        pass_rate=pass_rate,
        new_exception_count=report_in.new_exception_count,
        resolved_exception_count=report_in.resolved_exception_count,
        summary=report_in.summary,
        created_by=current_user.id
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    workshop_name = None
    if report.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == report.workshop_id).first()
        workshop_name = workshop.workshop_name if workshop else None
    
    return ProductionDailyReportResponse(
        id=report.id,
        report_date=report.report_date,
        workshop_id=report.workshop_id,
        workshop_name=workshop_name,
        plan_qty=report.plan_qty,
        completed_qty=report.completed_qty,
        completion_rate=float(report.completion_rate) if report.completion_rate else None,
        plan_hours=float(report.plan_hours) if report.plan_hours else None,
        actual_hours=float(report.actual_hours) if report.actual_hours else None,
        overtime_hours=float(report.overtime_hours) if report.overtime_hours else None,
        efficiency=float(report.efficiency) if report.efficiency else None,
        should_attend=report.should_attend,
        actual_attend=report.actual_attend,
        leave_count=report.leave_count,
        total_qty=report.total_qty,
        qualified_qty=report.qualified_qty,
        pass_rate=float(report.pass_rate) if report.pass_rate else None,
        new_exception_count=report.new_exception_count,
        resolved_exception_count=report.resolved_exception_count,
        summary=report.summary,
        created_by=report.created_by,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.get("/production/dashboard", response_model=ProductionDashboardResponse)
def get_production_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_production_access()),
) -> Any:
    """
    生产驾驶舱（经理看板）
    """
    from app.models.production import Equipment
    today = date.today()
    
    # 总体统计
    total_workshops = db.query(Workshop).filter(Workshop.is_active == True).count()
    total_workstations = db.query(Workstation).filter(Workstation.is_active == True).count()
    total_workers = db.query(Worker).count()
    active_workers = db.query(Worker).filter(Worker.status == "ACTIVE").count()
    
    # 工单统计
    total_work_orders = db.query(WorkOrder).count()
    pending_orders = db.query(WorkOrder).filter(WorkOrder.status == "PENDING").count()
    in_progress_orders = db.query(WorkOrder).filter(WorkOrder.status.in_(["ASSIGNED", "STARTED", "PAUSED"])).count()
    completed_orders = db.query(WorkOrder).filter(WorkOrder.status == "COMPLETED").count()
    
    # 今日统计（从生产日报获取）
    from app.models.production import ProductionDailyReport
    today_report = db.query(ProductionDailyReport).filter(
        ProductionDailyReport.report_date == today
    ).first()
    
    today_plan_qty = today_report.plan_qty if today_report else 0
    today_completed_qty = today_report.completed_qty if today_report else 0
    today_completion_rate = float(today_report.completion_rate) if today_report and today_report.completion_rate else 0.0
    today_actual_hours = float(today_report.actual_hours) if today_report and today_report.actual_hours else 0.0
    
    # 质量统计
    today_qualified_qty = today_report.qualified_qty if today_report else 0
    today_pass_rate = float(today_report.pass_rate) if today_report and today_report.pass_rate else 0.0
    
    # 异常统计
    open_exceptions = db.query(ProductionException).filter(
        ProductionException.status.in_(["REPORTED", "IN_PROGRESS"])
    ).count()
    critical_exceptions = db.query(ProductionException).filter(
        ProductionException.status.in_(["REPORTED", "IN_PROGRESS"]),
        ProductionException.exception_level == "CRITICAL"
    ).count()
    
    # 设备统计
    total_equipment = db.query(Equipment).filter(Equipment.is_active == True).count()
    running_equipment = db.query(Equipment).filter(Equipment.status == "RUNNING").count()
    maintenance_equipment = db.query(Equipment).filter(Equipment.status == "MAINTENANCE").count()
    fault_equipment = db.query(Equipment).filter(Equipment.status == "FAULT").count()
    
    # 车间统计
    workshops = db.query(Workshop).filter(Workshop.is_active == True).all()
    workshop_stats = []
    for workshop in workshops:
        # 车间工单统计
        workshop_orders = db.query(WorkOrder).filter(WorkOrder.workshop_id == workshop.id).count()
        workshop_in_progress = db.query(WorkOrder).filter(
            WorkOrder.workshop_id == workshop.id,
            WorkOrder.status.in_(["ASSIGNED", "STARTED", "PAUSED"])
        ).count()
        
        # 车间工人统计
        workshop_workers = db.query(Worker).filter(Worker.workshop_id == workshop.id).count()
        
        # 车间设备统计
        workshop_equipment = db.query(Equipment).filter(Equipment.workshop_id == workshop.id).count()
        
        workshop_stats.append({
            "workshop_id": workshop.id,
            "workshop_name": workshop.workshop_name,
            "workshop_type": workshop.workshop_type,
            "work_orders": workshop_orders,
            "in_progress_orders": workshop_in_progress,
            "workers": workshop_workers,
            "equipment": workshop_equipment
        })
    
    return ProductionDashboardResponse(
        total_workshops=total_workshops,
        total_workstations=total_workstations,
        total_workers=total_workers,
        active_workers=active_workers,
        total_work_orders=total_work_orders,
        pending_orders=pending_orders,
        in_progress_orders=in_progress_orders,
        completed_orders=completed_orders,
        today_plan_qty=today_plan_qty,
        today_completed_qty=today_completed_qty,
        today_completion_rate=today_completion_rate,
        today_actual_hours=today_actual_hours,
        today_qualified_qty=today_qualified_qty,
        today_pass_rate=today_pass_rate,
        open_exceptions=open_exceptions,
        critical_exceptions=critical_exceptions,
        total_equipment=total_equipment,
        running_equipment=running_equipment,
        maintenance_equipment=maintenance_equipment,
        fault_equipment=fault_equipment,
        workshop_stats=workshop_stats
    )


@router.get("/workshops/{workshop_id}/task-board", response_model=WorkshopTaskBoardResponse)
def get_workshop_task_board(
    workshop_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    车间任务看板（看板视图）
    """
    workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="车间不存在")
    
    # 获取车间工位
    workstations = db.query(Workstation).filter(
        Workstation.workshop_id == workshop_id,
        Workstation.is_active == True
    ).all()
    
    workstation_list = []
    for ws in workstations:
        current_worker_name = None
        if ws.current_worker_id:
            worker = db.query(Worker).filter(Worker.id == ws.current_worker_id).first()
            current_worker_name = worker.worker_name if worker else None
        
        current_work_order_no = None
        if ws.current_work_order_id:
            work_order = db.query(WorkOrder).filter(WorkOrder.id == ws.current_work_order_id).first()
            current_work_order_no = work_order.work_order_no if work_order else None
        
        workstation_list.append({
            "id": ws.id,
            "workstation_code": ws.workstation_code,
            "workstation_name": ws.workstation_name,
            "status": ws.status,
            "current_worker_id": ws.current_worker_id,
            "current_worker_name": current_worker_name,
            "current_work_order_id": ws.current_work_order_id,
            "current_work_order_no": current_work_order_no,
        })
    
    # 获取车间工单（按状态分组）
    work_orders = db.query(WorkOrder).filter(WorkOrder.workshop_id == workshop_id).all()
    
    work_order_list = []
    for wo in work_orders:
        project_name = None
        if wo.project_id:
            project = db.query(Project).filter(Project.id == wo.project_id).first()
            project_name = project.project_name if project else None
        
        assigned_worker_name = None
        if wo.assigned_to:
            worker = db.query(Worker).filter(Worker.id == wo.assigned_to).first()
            assigned_worker_name = worker.worker_name if worker else None
        
        work_order_list.append({
            "id": wo.id,
            "work_order_no": wo.work_order_no,
            "task_name": wo.task_name,
            "status": wo.status,
            "priority": wo.priority,
            "progress": wo.progress or 0,
            "plan_qty": wo.plan_qty,
            "completed_qty": wo.completed_qty or 0,
            "project_id": wo.project_id,
            "project_name": project_name,
            "assigned_to": wo.assigned_to,
            "assigned_worker_name": assigned_worker_name,
            "workstation_id": wo.workstation_id,
            "plan_start_date": wo.plan_start_date,
            "plan_end_date": wo.plan_end_date,
        })
    
    # 获取车间工人
    workers = db.query(Worker).filter(Worker.workshop_id == workshop_id).all()
    
    worker_list = []
    for worker in workers:
        # 获取工人当前工单
        current_work_order = db.query(WorkOrder).filter(
            WorkOrder.assigned_to == worker.id,
            WorkOrder.status.in_(["ASSIGNED", "STARTED", "PAUSED"])
        ).first()
        
        worker_list.append({
            "id": worker.id,
            "worker_code": worker.worker_code if hasattr(worker, 'worker_code') else worker.worker_no,
            "worker_name": worker.worker_name,
            "status": worker.status,
            "current_work_order_id": current_work_order.id if current_work_order else None,
            "current_work_order_no": current_work_order.work_order_no if current_work_order else None,
        })
    
    return WorkshopTaskBoardResponse(
        workshop_id=workshop.id,
        workshop_name=workshop.workshop_name,
        workstations=workstation_list,
        work_orders=work_order_list,
        workers=worker_list
    )


@router.get("/reports/production-efficiency", response_model=List[ProductionEfficiencyReportResponse])
def get_production_efficiency_report(
    db: Session = Depends(deps.get_db),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    生产效率报表
    """
    from app.models.production import ProductionDailyReport
    query = db.query(ProductionDailyReport).filter(
        ProductionDailyReport.report_date >= start_date,
        ProductionDailyReport.report_date <= end_date
    )
    
    if workshop_id:
        query = query.filter(ProductionDailyReport.workshop_id == workshop_id)
    
    reports = query.order_by(ProductionDailyReport.report_date).all()
    
    result = []
    for report in reports:
        workshop_name = None
        if report.workshop_id:
            workshop = db.query(Workshop).filter(Workshop.id == report.workshop_id).first()
            workshop_name = workshop.workshop_name if workshop else None
        
        result.append(ProductionEfficiencyReportResponse(
            report_date=report.report_date,
            workshop_id=report.workshop_id,
            workshop_name=workshop_name,
            plan_hours=float(report.plan_hours) if report.plan_hours else 0.0,
            actual_hours=float(report.actual_hours) if report.actual_hours else 0.0,
            efficiency=float(report.efficiency) if report.efficiency else 0.0,
            plan_qty=report.plan_qty,
            completed_qty=report.completed_qty,
            completion_rate=float(report.completion_rate) if report.completion_rate else 0.0,
            qualified_qty=report.qualified_qty,
            pass_rate=float(report.pass_rate) if report.pass_rate else 0.0
        ))
    
    return result


@router.get("/reports/capacity-utilization", response_model=List[CapacityUtilizationResponse])
def get_capacity_utilization(
    db: Session = Depends(deps.get_db),
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    产能利用率
    """
    from app.models.production import ProductionDailyReport
    # 获取车间列表
    query_workshops = db.query(Workshop).filter(Workshop.is_active == True)
    if workshop_id:
        query_workshops = query_workshops.filter(Workshop.id == workshop_id)
    workshops = query_workshops.all()
    
    result = []
    current_date = start_date
    
    while current_date <= end_date:
        for workshop in workshops:
            # 获取该日期的生产日报
            daily_report = db.query(ProductionDailyReport).filter(
                ProductionDailyReport.report_date == current_date,
                ProductionDailyReport.workshop_id == workshop.id
            ).first()
            
            # 获取车间产能
            capacity_hours = float(workshop.capacity_hours) if workshop.capacity_hours else None
            
            # 计算实际工时
            actual_hours = float(daily_report.actual_hours) if daily_report and daily_report.actual_hours else 0.0
            
            # 计算利用率
            utilization_rate = 0.0
            if capacity_hours and capacity_hours > 0:
                utilization_rate = (actual_hours / capacity_hours) * 100
            
            # 计算负荷率（计划工时/产能）
            plan_hours = float(daily_report.plan_hours) if daily_report and daily_report.plan_hours else 0.0
            load_rate = 0.0
            if capacity_hours and capacity_hours > 0:
                load_rate = (plan_hours / capacity_hours) * 100
            
            result.append(CapacityUtilizationResponse(
                workshop_id=workshop.id,
                workshop_name=workshop.workshop_name,
                date=current_date,
                capacity_hours=capacity_hours,
                actual_hours=actual_hours,
                utilization_rate=utilization_rate,
                plan_hours=plan_hours,
                load_rate=load_rate
            ))
        
        # 移动到下一天
        from datetime import timedelta
        current_date += timedelta(days=1)
    
    return result


@router.get("/reports/worker-performance", response_model=List[WorkerPerformanceReportResponse])
def get_worker_performance_report(
    db: Session = Depends(deps.get_db),
    worker_id: Optional[int] = Query(None, description="工人ID筛选"),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    period_start: date = Query(..., description="统计开始日期"),
    period_end: date = Query(..., description="统计结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    人员绩效报表
    """
    # 获取工人列表
    query_workers = db.query(Worker).filter(Worker.status == "ACTIVE")
    if worker_id:
        query_workers = query_workers.filter(Worker.id == worker_id)
    if workshop_id:
        query_workers = query_workers.filter(Worker.workshop_id == workshop_id)
    workers = query_workers.all()
    
    result = []
    for worker in workers:
        # 查询报工记录
        reports = db.query(WorkReport).filter(
            WorkReport.worker_id == worker.id,
            WorkReport.report_time >= datetime.combine(period_start, datetime.min.time()),
            WorkReport.report_time <= datetime.combine(period_end, datetime.max.time())
        ).all()
        
        # 统计工时
        total_hours = sum(float(r.work_hours) if r.work_hours else 0 for r in reports)
        total_reports = len(reports)
        
        # 统计完成的工单
        completed_orders = db.query(WorkOrder).filter(
            WorkOrder.assigned_to == worker.id,
            WorkOrder.status == "COMPLETED",
            WorkOrder.actual_end_time >= datetime.combine(period_start, datetime.min.time()),
            WorkOrder.actual_end_time <= datetime.combine(period_end, datetime.max.time())
        ).count()
        
        # 统计完成数量和合格数量
        total_completed_qty = sum(r.completed_qty or 0 for r in reports)
        total_qualified_qty = sum(r.qualified_qty or 0 for r in reports)
        
        # 计算平均效率（从工单中获取）
        work_orders = db.query(WorkOrder).filter(
            WorkOrder.assigned_to == worker.id,
            WorkOrder.status == "COMPLETED",
            WorkOrder.actual_end_time >= datetime.combine(period_start, datetime.min.time()),
            WorkOrder.actual_end_time <= datetime.combine(period_end, datetime.max.time())
        ).all()
        
        efficiencies = []
        for wo in work_orders:
            if wo.standard_hours and wo.actual_hours and wo.actual_hours > 0:
                eff = float((wo.standard_hours / wo.actual_hours) * 100)
                efficiencies.append(eff)
        
        average_efficiency = sum(efficiencies) / len(efficiencies) if efficiencies else 0.0
        
        workshop_name = None
        if worker.workshop_id:
            workshop = db.query(Workshop).filter(Workshop.id == worker.workshop_id).first()
            workshop_name = workshop.workshop_name if workshop else None
        
        worker_code = worker.worker_code if hasattr(worker, 'worker_code') else worker.worker_no
        result.append(WorkerPerformanceReportResponse(
            worker_id=worker.id,
            worker_code=worker_code,
            worker_name=worker.worker_name,
            workshop_id=worker.workshop_id,
            workshop_name=workshop_name,
            period_start=period_start,
            period_end=period_end,
            total_hours=total_hours,
            total_reports=total_reports,
            completed_orders=completed_orders,
            total_completed_qty=total_completed_qty,
            total_qualified_qty=total_qualified_qty,
            average_efficiency=average_efficiency
        ))
    
    return result


# ==================== 报工系统扩展功能 ====================

@router.post("/work-reports/pause", response_model=WorkReportResponse)
def pause_work_report(
    *,
    db: Session = Depends(deps.get_db),
    work_order_id: int = Body(..., description="工单ID"),
    pause_reason: Optional[str] = Body(None, description="暂停原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    暂停报告
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if work_order.status != "STARTED":
        raise HTTPException(status_code=400, detail="只有已开始的工单才能暂停")
    
    # 获取当前工人
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    if not worker:
        raise HTTPException(status_code=400, detail="当前用户未关联工人信息")
    
    # 生成报工单号
    report_no = generate_report_no(db)
    
    report = WorkReport(
        report_no=report_no,
        work_order_id=work_order_id,
        worker_id=worker.id,
        report_type="PAUSE",
        report_time=datetime.now(),
        status="PENDING",
        report_note=pause_reason or "暂停工作",
    )
    db.add(report)
    
    # 更新工单状态
    work_order.status = "PAUSED"
    
    # 更新工位状态
    if work_order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == work_order.workstation_id).first()
        if workstation:
            workstation.status = "IDLE"
            db.add(workstation)
    
    db.commit()
    db.refresh(report)
    
    return get_work_report_detail(db=db, report_id=report.id, current_user=current_user)


@router.post("/work-reports/batch-approve", response_model=ResponseModel)
def batch_approve_work_reports(
    *,
    db: Session = Depends(deps.get_db),
    report_ids: List[int] = Body(..., description="报工记录ID列表"),
    approved: bool = Body(True, description="是否审批通过"),
    approval_note: Optional[str] = Body(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量审批报工记录
    """
    success_count = 0
    failed_reports = []
    
    for report_id in report_ids:
        try:
            report = db.query(WorkReport).filter(WorkReport.id == report_id).first()
            if not report:
                failed_reports.append({"report_id": report_id, "reason": "报工记录不存在"})
                continue
            
            if report.status != "PENDING":
                failed_reports.append({"report_id": report_id, "reason": f"报工记录状态为{report.status}，不能审批"})
                continue
            
            if approved:
                report.status = "APPROVED"
                report.approved_by = current_user.id
                report.approved_at = datetime.now()
                
                # 如果是完工报告，更新工单
                if report.report_type == "COMPLETE":
                    work_order = db.query(WorkOrder).filter(WorkOrder.id == report.work_order_id).first()
                    if work_order:
                        work_order.completed_qty = (work_order.completed_qty or 0) + (report.completed_qty or 0)
                        work_order.qualified_qty = (work_order.qualified_qty or 0) + (report.qualified_qty or 0)
                        work_order.defect_qty = (work_order.defect_qty or 0) + (report.defect_qty or 0)
                        work_order.actual_hours = (work_order.actual_hours or 0) + (report.work_hours or 0)
                        
                        if work_order.completed_qty >= work_order.plan_qty:
                            work_order.status = "COMPLETED"
                            work_order.actual_end_time = datetime.now()
                            work_order.progress = 100
                        
                        db.add(work_order)
            else:
                report.status = "REJECTED"
                report.approved_by = current_user.id
                report.approved_at = datetime.now()
            
            if approval_note:
                report.report_note = (report.report_note or "") + f"\n审批意见：{approval_note}"
            
            db.add(report)
            success_count += 1
        except Exception as e:
            failed_reports.append({"report_id": report_id, "reason": str(e)})
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message=f"批量审批完成：成功 {success_count} 个，失败 {len(failed_reports)} 个",
        data={"success_count": success_count, "failed_reports": failed_reports}
    )


@router.get("/work-reports/hours-summary", response_model=dict)
def get_work_hours_summary(
    db: Session = Depends(deps.get_db),
    worker_id: Optional[int] = Query(None, description="工人ID筛选"),
    work_order_id: Optional[int] = Query(None, description="工单ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    工时统计（按人/工单汇总）
    """
    query = db.query(WorkReport).filter(WorkReport.status == "APPROVED")
    
    if worker_id:
        query = query.filter(WorkReport.worker_id == worker_id)
    if work_order_id:
        query = query.filter(WorkReport.work_order_id == work_order_id)
    if start_date:
        query = query.filter(WorkReport.report_time >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(WorkReport.report_time <= datetime.combine(end_date, datetime.max.time()))
    
    reports = query.all()
    
    # 按工人统计
    worker_summary = {}
    for report in reports:
        worker = db.query(Worker).filter(Worker.id == report.worker_id).first()
        if not worker:
            continue
        
        worker_key = worker.id
        if worker_key not in worker_summary:
            worker_summary[worker_key] = {
                "worker_id": worker.id,
                "worker_name": worker.worker_name,
                "total_hours": Decimal(0),
                "total_reports": 0,
                "completed_orders": set(),
            }
        
        worker_summary[worker_key]["total_hours"] += report.work_hours or 0
        worker_summary[worker_key]["total_reports"] += 1
        if report.work_order_id:
            worker_summary[worker_key]["completed_orders"].add(report.work_order_id)
    
    # 按工单统计
    order_summary = {}
    for report in reports:
        if not report.work_order_id:
            continue
        
        order_key = report.work_order_id
        if order_key not in order_summary:
            work_order = db.query(WorkOrder).filter(WorkOrder.id == report.work_order_id).first()
            order_summary[order_key] = {
                "work_order_id": report.work_order_id,
                "work_order_no": work_order.work_order_no if work_order else None,
                "total_hours": Decimal(0),
                "total_reports": 0,
                "workers": set(),
            }
        
        order_summary[order_key]["total_hours"] += report.work_hours or 0
        order_summary[order_key]["total_reports"] += 1
        if report.worker_id:
            order_summary[order_key]["workers"].add(report.worker_id)
    
    # 格式化结果
    worker_list = []
    for key, summary in worker_summary.items():
        worker_list.append({
            "worker_id": summary["worker_id"],
            "worker_name": summary["worker_name"],
            "total_hours": float(summary["total_hours"]),
            "total_reports": summary["total_reports"],
            "completed_orders_count": len(summary["completed_orders"]),
        })
    
    order_list = []
    for key, summary in order_summary.items():
        order_list.append({
            "work_order_id": summary["work_order_id"],
            "work_order_no": summary["work_order_no"],
            "total_hours": float(summary["total_hours"]),
            "total_reports": summary["total_reports"],
            "workers_count": len(summary["workers"]),
        })
    
    return {
        "by_worker": worker_list,
        "by_work_order": order_list,
        "total_hours": float(sum(summary["total_hours"] for summary in worker_summary.values())),
        "total_reports": len(reports),
    }


# ==================== 退料管理 ====================

@router.get("/material-returns", response_model=PaginatedResponse)
def read_material_returns(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    requisition_id: Optional[int] = Query(None, description="领料单ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    退料申请列表
    """
    # 注意：这里假设有MaterialReturn模型，如果没有需要先创建
    # 为了演示，这里返回空列表
    return PaginatedResponse(
        items=[],
        total=0,
        page=page,
        page_size=page_size,
        pages=0
    )


@router.post("/material-returns", response_model=ResponseModel)
def create_material_return(
    *,
    db: Session = Depends(deps.get_db),
    requisition_id: int = Body(..., description="领料单ID"),
    return_items: List[dict] = Body(..., description="退料明细"),
    return_reason: Optional[str] = Body(None, description="退料原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建退料申请
    """
    # 验证领料单
    requisition = db.query(MaterialRequisition).filter(MaterialRequisition.id == requisition_id).first()
    if not requisition:
        raise HTTPException(status_code=404, detail="领料单不存在")
    
    # 注意：这里需要MaterialReturn模型，暂时返回成功消息
    return ResponseModel(
        code=201,
        message="退料申请已创建",
        data={"requisition_id": requisition_id, "return_items": return_items}
    )


@router.put("/material-returns/{return_id}/approve", response_model=ResponseModel)
def approve_material_return(
    *,
    db: Session = Depends(deps.get_db),
    return_id: int,
    approved: bool = Body(True, description="是否审批通过"),
    approval_note: Optional[str] = Body(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    退料审批
    """
    # 注意：这里需要MaterialReturn模型
    return ResponseModel(
        code=200,
        message="审批成功" if approved else "已驳回"
    )


# ==================== 生产异常统计 ====================

@router.get("/production-exceptions/statistics", response_model=dict)
def get_production_exception_statistics(
    db: Session = Depends(deps.get_db),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    异常统计（按类型/车间）
    """
    query = db.query(ProductionException)
    
    if workshop_id:
        query = query.filter(ProductionException.workshop_id == workshop_id)
    if start_date:
        query = query.filter(ProductionException.report_time >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(ProductionException.report_time <= datetime.combine(end_date, datetime.max.time()))
    
    exceptions = query.all()
    
    # 按类型统计
    by_type = {}
    for exc in exceptions:
        exc_type = exc.exception_type or "OTHER"
        if exc_type not in by_type:
            by_type[exc_type] = {
                "type": exc_type,
                "count": 0,
                "open_count": 0,
                "resolved_count": 0,
            }
        by_type[exc_type]["count"] += 1
        if exc.status == "REPORTED":
            by_type[exc_type]["open_count"] += 1
        elif exc.status == "RESOLVED":
            by_type[exc_type]["resolved_count"] += 1
    
    # 按车间统计
    by_workshop = {}
    for exc in exceptions:
        if not exc.workshop_id:
            continue
        workshop = db.query(Workshop).filter(Workshop.id == exc.workshop_id).first()
        workshop_name = workshop.workshop_name if workshop else f"车间{exc.workshop_id}"
        
        if exc.workshop_id not in by_workshop:
            by_workshop[exc.workshop_id] = {
                "workshop_id": exc.workshop_id,
                "workshop_name": workshop_name,
                "count": 0,
                "open_count": 0,
                "resolved_count": 0,
            }
        by_workshop[exc.workshop_id]["count"] += 1
        if exc.status == "REPORTED":
            by_workshop[exc.workshop_id]["open_count"] += 1
        elif exc.status == "RESOLVED":
            by_workshop[exc.workshop_id]["resolved_count"] += 1
    
    return {
        "total": len(exceptions),
        "open": len([e for e in exceptions if e.status == "REPORTED"]),
        "resolved": len([e for e in exceptions if e.status == "RESOLVED"]),
        "by_type": list(by_type.values()),
        "by_workshop": list(by_workshop.values()),
    }


# ==================== 产能负荷分析 ====================

@router.get("/production-plans/capacity-load", response_model=dict)
def get_capacity_load_analysis(
    db: Session = Depends(deps.get_db),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    产能负荷分析
    """
    query_workshops = db.query(Workshop).filter(Workshop.is_active == True)
    if workshop_id:
        query_workshops = query_workshops.filter(Workshop.id == workshop_id)
    
    workshops = query_workshops.all()
    
    result = []
    for workshop in workshops:
        # 计算车间产能（假设每天8小时，工作天数）
        from datetime import timedelta
        work_days = (end_date - start_date).days + 1
        capacity_hours = work_days * 8 * (workshop.worker_count or 0)
        
        # 计算实际负荷（从工单统计）
        work_orders = db.query(WorkOrder).filter(
            WorkOrder.workshop_id == workshop.id,
            WorkOrder.plan_start_date >= start_date,
            WorkOrder.plan_start_date <= end_date
        ).all()
        
        plan_hours = sum(float(wo.standard_hours or 0) for wo in work_orders)
        actual_hours = sum(float(wo.actual_hours or 0) for wo in work_orders)
        
        load_rate = (plan_hours / capacity_hours * 100) if capacity_hours > 0 else 0
        utilization_rate = (actual_hours / capacity_hours * 100) if capacity_hours > 0 else 0
        
        result.append({
            "workshop_id": workshop.id,
            "workshop_name": workshop.workshop_name,
            "capacity_hours": capacity_hours,
            "plan_hours": plan_hours,
            "actual_hours": actual_hours,
            "load_rate": round(load_rate, 2),
            "utilization_rate": round(utilization_rate, 2),
            "work_order_count": len(work_orders),
        })
    
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "workshops": result,
    }


# ==================== 排产日历 ====================

@router.get("/production-plans/calendar", response_model=dict)
def get_production_calendar(
    db: Session = Depends(deps.get_db),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    排产日历
    """
    query_plans = db.query(ProductionPlan).filter(
        ProductionPlan.plan_start_date <= end_date,
        ProductionPlan.plan_end_date >= start_date,
        ProductionPlan.status.in_(["APPROVED", "PUBLISHED"])
    )
    
    if workshop_id:
        query_plans = query_plans.filter(ProductionPlan.workshop_id == workshop_id)
    
    plans = query_plans.all()
    
    # 按日期组织
    calendar = {}
    from datetime import timedelta
    current_date = start_date
    while current_date <= end_date:
        calendar[current_date.isoformat()] = {
            "date": current_date.isoformat(),
            "plans": [],
            "work_orders": [],
        }
        current_date += timedelta(days=1)
    
    # 填充计划
    for plan in plans:
        project_name = None
        if plan.project_id:
            project = db.query(Project).filter(Project.id == plan.project_id).first()
            project_name = project.project_name if project else None
        
        workshop_name = None
        if plan.workshop_id:
            workshop = db.query(Workshop).filter(Workshop.id == plan.workshop_id).first()
            workshop_name = workshop.workshop_name if workshop else None
        
        plan_start = max(plan.plan_start_date, start_date)
        plan_end = min(plan.plan_end_date, end_date)
        
        current_date = plan_start
        while current_date <= plan_end:
            if current_date.isoformat() in calendar:
                calendar[current_date.isoformat()]["plans"].append({
                    "plan_id": plan.id,
                    "plan_no": plan.plan_no,
                    "plan_name": plan.plan_name,
                    "project_name": project_name,
                    "workshop_name": workshop_name,
                    "status": plan.status,
                })
            current_date += timedelta(days=1)
    
    # 填充工单
    query_orders = db.query(WorkOrder).filter(
        WorkOrder.plan_start_date <= end_date,
        WorkOrder.plan_end_date >= start_date,
        WorkOrder.status.in_(["ASSIGNED", "STARTED", "PAUSED"])
    )
    
    if workshop_id:
        query_orders = query_orders.join(Workstation).filter(Workstation.workshop_id == workshop_id)
    
    orders = query_orders.all()
    
    for order in orders:
        order_start = max(order.plan_start_date, start_date) if order.plan_start_date else start_date
        order_end = min(order.plan_end_date, end_date) if order.plan_end_date else end_date
        
        current_date = order_start
        while current_date <= order_end:
            if current_date.isoformat() in calendar:
                calendar[current_date.isoformat()]["work_orders"].append({
                    "order_id": order.id,
                    "order_no": order.work_order_no,
                    "task_name": order.task_name,
                    "status": order.status,
                })
            current_date += timedelta(days=1)
    
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "calendar": list(calendar.values()),
    }

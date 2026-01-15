# -*- coding: utf-8 -*-
"""
研发费用归集 - 自动生成
从 rd_project.py 拆分
"""

# -*- coding: utf-8 -*-
"""
研发项目管理 API endpoints
包含：研发项目立项、审批、结项、费用归集、报表生成
适用场景：IPO合规、高新技术企业认定、研发费用加计扣除
"""
from typing import Any, List, Optional, Dict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func

from app.api import deps
from app.core import security
from app.core.config import settings

# 文档上传目录
DOCUMENT_UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "documents" / "rd_projects"
DOCUMENT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
from app.models.user import User
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.project import ProjectDocument
from app.models.rd_project import (
    RdProject, RdProjectCategory, RdCost, RdCostType,
    RdCostAllocationRule, RdReportRecord
)
from app.schemas.rd_project import (
    RdProjectCategoryCreate, RdProjectCategoryUpdate, RdProjectCategoryResponse,
    RdProjectCreate, RdProjectUpdate, RdProjectResponse,
    RdProjectApproveRequest, RdProjectCloseRequest, RdProjectLinkRequest,
    RdCostTypeCreate, RdCostTypeResponse,
    RdCostCreate, RdCostUpdate, RdCostResponse,
    RdCostCalculateLaborRequest, RdCostSummaryResponse,
    RdCostAllocationRuleCreate, RdCostAllocationRuleResponse,
    RdReportRecordResponse
)
from app.schemas.timesheet import (
    TimesheetCreate, TimesheetUpdate, TimesheetResponse, TimesheetListResponse
)
from app.schemas.project import (
    ProjectDocumentCreate, ProjectDocumentUpdate, ProjectDocumentResponse
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


def generate_project_no(db: Session) -> str:
    """生成研发项目编号：RD-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_project = (
        db.query(RdProject)
        .filter(RdProject.project_no.like(f"RD-{today}-%"))
        .order_by(desc(RdProject.project_no))
        .first()
    )
    if max_project:
        seq = int(max_project.project_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"RD-{today}-{seq:03d}"


def generate_cost_no(db: Session) -> str:
    """生成研发费用编号：RC-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_cost = (
        db.query(RdCost)
        .filter(RdCost.cost_no.like(f"RC-{today}-%"))
        .order_by(desc(RdCost.cost_no))
        .first()
    )
    if max_cost:
        seq = int(max_cost.cost_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"RC-{today}-{seq:03d}"



from fastapi import APIRouter

router = APIRouter(
    prefix="/rd-project/expenses",
    tags=["expenses"]
)

# 共 5 个路由

# ==================== 研发费用归集 ====================

@router.get("/rd-costs", response_model=PaginatedResponse)
def get_rd_costs(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    rd_project_id: Optional[int] = Query(None, description="研发项目ID筛选"),
    cost_type_id: Optional[int] = Query(None, description="费用类型ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期筛选"),
    end_date: Optional[date] = Query(None, description="结束日期筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.require_rd_project_access),
) -> Any:
    """
    获取研发费用列表（支持分页、筛选）
    """
    query = db.query(RdCost)
    
    if rd_project_id:
        query = query.filter(RdCost.rd_project_id == rd_project_id)
    if cost_type_id:
        query = query.filter(RdCost.cost_type_id == cost_type_id)
    if start_date:
        query = query.filter(RdCost.cost_date >= start_date)
    if end_date:
        query = query.filter(RdCost.cost_date <= end_date)
    if status:
        query = query.filter(RdCost.status == status)
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    costs = query.order_by(desc(RdCost.cost_date), desc(RdCost.created_at)).offset(offset).limit(page_size).all()
    
    items = [RdCostResponse.model_validate(cost) for cost in costs]
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/rd-costs", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_rd_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_in: RdCostCreate,
    current_user: User = Depends(security.require_rd_project_access),
) -> Any:
    """
    录入研发费用
    """
    # 验证研发项目是否存在
    project = db.query(RdProject).filter(RdProject.id == cost_in.rd_project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")
    
    # 验证费用类型是否存在
    cost_type = db.query(RdCostType).filter(RdCostType.id == cost_in.cost_type_id).first()
    if not cost_type:
        raise HTTPException(status_code=404, detail="费用类型不存在")
    
    # 生成费用编号
    cost_no = generate_cost_no(db)
    
    # 创建研发费用
    cost = RdCost(
        cost_no=cost_no,
        rd_project_id=cost_in.rd_project_id,
        cost_type_id=cost_in.cost_type_id,
        cost_date=cost_in.cost_date,
        cost_amount=cost_in.cost_amount,
        cost_description=cost_in.cost_description,
        user_id=cost_in.user_id,
        hours=cost_in.hours,
        hourly_rate=cost_in.hourly_rate,
        material_id=cost_in.material_id,
        material_qty=cost_in.material_qty,
        material_price=cost_in.material_price,
        equipment_id=cost_in.equipment_id,
        depreciation_period=cost_in.depreciation_period,
        source_type=cost_in.source_type or 'MANUAL',
        source_id=cost_in.source_id,
        is_allocated=cost_in.is_allocated,
        allocation_rule_id=cost_in.allocation_rule_id,
        allocation_rate=cost_in.allocation_rate,
        deductible_amount=cost_in.deductible_amount,
        status='DRAFT',
        remark=cost_in.remark,
    )
    
    db.add(cost)
    
    # 更新项目总费用
    project.total_cost = (project.total_cost or 0) + cost_in.cost_amount
    
    db.commit()
    db.refresh(cost)
    
    return ResponseModel(
        code=201,
        message="研发费用录入成功",
        data=RdCostResponse.model_validate(cost)
    )


@router.put("/rd-costs/{cost_id}", response_model=ResponseModel)
def update_rd_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_id: int,
    cost_in: RdCostUpdate,
    current_user: User = Depends(security.require_rd_project_access),
) -> Any:
    """
    更新研发费用
    """
    cost = db.query(RdCost).filter(RdCost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="研发费用不存在")
    
    # 只有草稿状态才能更新
    if cost.status != 'DRAFT':
        raise HTTPException(status_code=400, detail="只有草稿状态的研发费用才能更新")
    
    # 更新字段
    update_data = cost_in.model_dump(exclude_unset=True)
    
    # 如果更新了费用金额，需要更新项目总费用
    old_amount = cost.cost_amount
    if 'cost_amount' in update_data:
        new_amount = update_data['cost_amount']
        project = db.query(RdProject).filter(RdProject.id == cost.rd_project_id).first()
        if project:
            project.total_cost = (project.total_cost or 0) - old_amount + new_amount
    
    for field, value in update_data.items():
        setattr(cost, field, value)
    
    db.add(cost)
    db.commit()
    db.refresh(cost)
    
    return ResponseModel(
        code=200,
        message="研发费用更新成功",
        data=RdCostResponse.model_validate(cost)
    )


@router.get("/rd-projects/{project_id}/cost-summary", response_model=ResponseModel)
def get_rd_project_cost_summary(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_rd_project_access),
) -> Any:
    """
    获取项目费用汇总
    """
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")
    
    # 查询所有费用
    costs = db.query(RdCost).filter(
        RdCost.rd_project_id == project_id,
        RdCost.status == 'APPROVED'
    ).all()
    
    # 按类型汇总
    total_cost = Decimal(0)
    labor_cost = Decimal(0)
    material_cost = Decimal(0)
    depreciation_cost = Decimal(0)
    other_cost = Decimal(0)
    deductible_amount = Decimal(0)
    
    cost_by_type = {}
    
    for cost in costs:
        total_cost += cost.cost_amount
        if cost.deductible_amount:
            deductible_amount += cost.deductible_amount
        
        # 获取费用类型
        cost_type = db.query(RdCostType).filter(RdCostType.id == cost.cost_type_id).first()
        if cost_type:
            category = cost_type.category
            if category == 'LABOR':
                labor_cost += cost.cost_amount
            elif category == 'MATERIAL':
                material_cost += cost.cost_amount
            elif category == 'DEPRECIATION':
                depreciation_cost += cost.cost_amount
            else:
                other_cost += cost.cost_amount
            
            # 按类型汇总
            type_name = cost_type.type_name
            if type_name not in cost_by_type:
                cost_by_type[type_name] = {
                    'type_name': type_name,
                    'category': category,
                    'total_amount': Decimal(0),
                    'deductible_amount': Decimal(0),
                    'count': 0
                }
            cost_by_type[type_name]['total_amount'] += cost.cost_amount
            if cost.deductible_amount:
                cost_by_type[type_name]['deductible_amount'] += cost.deductible_amount
            cost_by_type[type_name]['count'] += 1
    
    summary = RdCostSummaryResponse(
        rd_project_id=project_id,
        rd_project_name=project.project_name,
        total_cost=total_cost,
        labor_cost=labor_cost,
        material_cost=material_cost,
        depreciation_cost=depreciation_cost,
        other_cost=other_cost,
        deductible_amount=deductible_amount,
        cost_by_type=list(cost_by_type.values())
    )
    
    return ResponseModel(
        code=200,
        message="success",
        data=summary
    )


@router.post("/rd-costs/calc-labor", response_model=ResponseModel)
def calculate_labor_cost(
    *,
    db: Session = Depends(deps.get_db),
    calc_request: RdCostCalculateLaborRequest,
    current_user: User = Depends(security.require_rd_project_access),
) -> Any:
    """
    人工费用自动计算（工时×时薪）
    """
    # 验证研发项目是否存在
    project = db.query(RdProject).filter(RdProject.id == calc_request.rd_project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")
    
    # 验证用户是否存在
    user = db.query(User).filter(User.id == calc_request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 查询工时记录（从timesheet表）
    from app.models.timesheet import Timesheet
    timesheets = db.query(Timesheet).filter(
        Timesheet.user_id == calc_request.user_id,
        Timesheet.work_date >= calc_request.start_date,
        Timesheet.work_date <= calc_request.end_date,
        Timesheet.status == 'APPROVED'
    ).all()
    
    # 计算总工时
    total_hours = Decimal(0)
    for ts in timesheets:
        total_hours += Decimal(str(ts.hours or 0))
    
    # 获取时薪（如果未提供，使用默认值或从用户配置获取）
    hourly_rate = calc_request.hourly_rate
    if not hourly_rate:
        # TODO: 从用户配置或系统配置获取默认时薪
        hourly_rate = Decimal(100)  # 默认时薪
    
    # 计算费用金额
    cost_amount = total_hours * hourly_rate
    
    # 获取人工费用类型
    labor_cost_type = db.query(RdCostType).filter(
        RdCostType.category == 'LABOR',
        RdCostType.is_active == True
    ).first()
    
    if not labor_cost_type:
        raise HTTPException(status_code=404, detail="未找到人工费用类型，请先配置费用类型")
    
    # 计算加计扣除金额
    deductible_amount = cost_amount * (labor_cost_type.deduction_rate / 100) if labor_cost_type.is_deductible else Decimal(0)
    
    return ResponseModel(
        code=200,
        message="人工费用计算成功",
        data={
            "rd_project_id": calc_request.rd_project_id,
            "user_id": calc_request.user_id,
            "user_name": user.real_name or user.username,
            "start_date": calc_request.start_date.isoformat(),
            "end_date": calc_request.end_date.isoformat(),
            "total_hours": float(total_hours),
            "hourly_rate": float(hourly_rate),
            "cost_amount": float(cost_amount),
            "deductible_amount": float(deductible_amount),
            "cost_type_id": labor_cost_type.id,
            "cost_type_name": labor_cost_type.type_name,
        }
    )




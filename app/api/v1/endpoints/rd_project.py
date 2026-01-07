# -*- coding: utf-8 -*-
"""
研发项目管理 API endpoints
包含：研发项目立项、审批、结项、费用归集、报表生成
适用场景：IPO合规、高新技术企业认定、研发费用加计扣除
"""
from typing import Any, List, Optional, Dict
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.project import Project
from app.models.timesheet import Timesheet
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


# ==================== 研发项目分类 ====================

@router.get("/rd-project-categories", response_model=ResponseModel)
def get_rd_project_categories(
    db: Session = Depends(deps.get_db),
    category_type: Optional[str] = Query(None, description="分类类型筛选：SELF/ENTRUST/COOPERATION"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取研发项目分类列表
    """
    query = db.query(RdProjectCategory)
    
    if category_type:
        query = query.filter(RdProjectCategory.category_type == category_type)
    if is_active is not None:
        query = query.filter(RdProjectCategory.is_active == is_active)
    
    categories = query.order_by(RdProjectCategory.sort_order, RdProjectCategory.category_code).all()
    
    return ResponseModel(
        code=200,
        message="success",
        data=[RdProjectCategoryResponse.model_validate(cat) for cat in categories]
    )


# ==================== 研发项目立项 ====================

@router.get("/rd-projects", response_model=PaginatedResponse)
def get_rd_projects(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（项目名称/编号）"),
    category_id: Optional[int] = Query(None, description="分类ID筛选"),
    category_type: Optional[str] = Query(None, description="项目类型筛选：SELF/ENTRUST/COOPERATION"),
    status: Optional[str] = Query(None, description="状态筛选"),
    approval_status: Optional[str] = Query(None, description="审批状态筛选"),
    project_manager_id: Optional[int] = Query(None, description="项目负责人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取研发项目列表（支持分页、搜索、筛选）
    """
    query = db.query(RdProject)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                RdProject.project_name.contains(keyword),
                RdProject.project_no.contains(keyword),
            )
        )
    
    # 筛选条件
    if category_id:
        query = query.filter(RdProject.category_id == category_id)
    if category_type:
        query = query.filter(RdProject.category_type == category_type)
    if status:
        query = query.filter(RdProject.status == status)
    if approval_status:
        query = query.filter(RdProject.approval_status == approval_status)
    if project_manager_id:
        query = query.filter(RdProject.project_manager_id == project_manager_id)
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    projects = query.order_by(desc(RdProject.created_at)).offset(offset).limit(page_size).all()
    
    items = [RdProjectResponse.model_validate(proj) for proj in projects]
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/rd-projects", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_rd_project(
    *,
    db: Session = Depends(deps.get_db),
    project_in: RdProjectCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建研发项目（立项申请）
    """
    # 生成项目编号
    project_no = generate_project_no(db)
    
    # 获取项目负责人姓名
    project_manager_name = None
    if project_in.project_manager_id:
        manager = db.query(User).filter(User.id == project_in.project_manager_id).first()
        if manager:
            project_manager_name = manager.real_name or manager.username
    
    # 创建研发项目
    project = RdProject(
        project_no=project_no,
        project_name=project_in.project_name,
        category_id=project_in.category_id,
        category_type=project_in.category_type,
        initiation_date=project_in.initiation_date,
        planned_start_date=project_in.planned_start_date,
        planned_end_date=project_in.planned_end_date,
        project_manager_id=project_in.project_manager_id,
        project_manager_name=project_manager_name,
        initiation_reason=project_in.initiation_reason,
        research_goal=project_in.research_goal,
        research_content=project_in.research_content,
        expected_result=project_in.expected_result,
        budget_amount=project_in.budget_amount,
        linked_project_id=project_in.linked_project_id,
        status='DRAFT',
        approval_status='PENDING',
        remark=project_in.remark,
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return ResponseModel(
        code=201,
        message="研发项目创建成功",
        data=RdProjectResponse.model_validate(project)
    )


@router.get("/rd-projects/{project_id}", response_model=ResponseModel)
def get_rd_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取研发项目详情
    """
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")
    
    return ResponseModel(
        code=200,
        message="success",
        data=RdProjectResponse.model_validate(project)
    )


@router.put("/rd-projects/{project_id}", response_model=ResponseModel)
def update_rd_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    project_in: RdProjectUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新研发项目
    """
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")
    
    # 只有草稿状态才能更新
    if project.status != 'DRAFT':
        raise HTTPException(status_code=400, detail="只有草稿状态的研发项目才能更新")
    
    # 更新字段
    update_data = project_in.model_dump(exclude_unset=True)
    
    # 更新项目负责人姓名
    if 'project_manager_id' in update_data and update_data['project_manager_id']:
        manager = db.query(User).filter(User.id == update_data['project_manager_id']).first()
        if manager:
            update_data['project_manager_name'] = manager.real_name or manager.username
    
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return ResponseModel(
        code=200,
        message="研发项目更新成功",
        data=RdProjectResponse.model_validate(project)
    )


@router.put("/rd-projects/{project_id}/approve", response_model=ResponseModel)
def approve_rd_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    approve_request: RdProjectApproveRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    研发项目审批
    """
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")
    
    if project.approval_status != 'PENDING':
        raise HTTPException(status_code=400, detail="只有待审批状态的研发项目才能审批")
    
    if approve_request.approved:
        project.approval_status = 'APPROVED'
        project.status = 'APPROVED'
        project.approved_by = current_user.id
        project.approved_at = datetime.now()
    else:
        project.approval_status = 'REJECTED'
        project.status = 'DRAFT'
    
    project.approval_remark = approve_request.approval_remark
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return ResponseModel(
        code=200,
        message="研发项目审批成功" if approve_request.approved else "研发项目已驳回",
        data=RdProjectResponse.model_validate(project)
    )


@router.put("/rd-projects/{project_id}/close", response_model=ResponseModel)
def close_rd_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    close_request: RdProjectCloseRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    研发项目结项
    """
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")
    
    if project.status in ['COMPLETED', 'CANCELLED']:
        raise HTTPException(status_code=400, detail="项目已结项或已取消")
    
    project.status = 'COMPLETED'
    project.close_date = date.today()
    project.close_reason = close_request.close_reason
    project.close_result = close_request.close_result
    project.closed_by = current_user.id
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return ResponseModel(
        code=200,
        message="研发项目结项成功",
        data=RdProjectResponse.model_validate(project)
    )


@router.put("/rd-projects/{project_id}/link-project", response_model=ResponseModel)
def link_rd_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    link_request: RdProjectLinkRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    关联非标项目
    """
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")
    
    # 验证关联的非标项目是否存在
    linked_project = db.query(Project).filter(Project.id == link_request.linked_project_id).first()
    if not linked_project:
        raise HTTPException(status_code=404, detail="关联的非标项目不存在")
    
    project.linked_project_id = link_request.linked_project_id
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return ResponseModel(
        code=200,
        message="关联非标项目成功",
        data=RdProjectResponse.model_validate(project)
    )


# ==================== 研发费用类型 ====================

@router.get("/rd-cost-types", response_model=ResponseModel)
def get_rd_cost_types(
    db: Session = Depends(deps.get_db),
    category: Optional[str] = Query(None, description="费用大类筛选：LABOR/MATERIAL/DEPRECIATION/OTHER"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取研发费用类型列表
    """
    query = db.query(RdCostType)
    
    if category:
        query = query.filter(RdCostType.category == category)
    if is_active is not None:
        query = query.filter(RdCostType.is_active == is_active)
    
    cost_types = query.order_by(RdCostType.sort_order, RdCostType.type_code).all()
    
    return ResponseModel(
        code=200,
        message="success",
        data=[RdCostTypeResponse.model_validate(ct) for ct in cost_types]
    )


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
    current_user: User = Depends(security.get_current_active_user),
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
    current_user: User = Depends(security.get_current_active_user),
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
    current_user: User = Depends(security.get_current_active_user),
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
    current_user: User = Depends(security.get_current_active_user),
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
    current_user: User = Depends(security.get_current_active_user),
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


# ==================== 费用分摊规则 ====================

@router.get("/rd-cost-allocation-rules", response_model=ResponseModel)
def get_rd_cost_allocation_rules(
    db: Session = Depends(deps.get_db),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取费用分摊规则列表
    """
    query = db.query(RdCostAllocationRule)
    
    if is_active is not None:
        query = query.filter(RdCostAllocationRule.is_active == is_active)
    
    rules = query.order_by(desc(RdCostAllocationRule.created_at)).all()
    
    return ResponseModel(
        code=200,
        message="success",
        data=[RdCostAllocationRuleResponse.model_validate(rule) for rule in rules]
    )


@router.post("/rd-costs/apply-allocation", response_model=ResponseModel)
def apply_cost_allocation(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int = Query(..., description="分摊规则ID"),
    cost_ids: Optional[List[int]] = Query(None, description="费用ID列表（不提供则应用规则范围内的所有费用）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    应用费用分摊规则
    根据分摊规则将共享费用分摊到多个研发项目
    """
    # 验证分摊规则是否存在
    rule = db.query(RdCostAllocationRule).filter(RdCostAllocationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="分摊规则不存在")
    
    if not rule.is_active:
        raise HTTPException(status_code=400, detail="分摊规则未启用")
    
    # 查询需要分摊的费用
    query = db.query(RdCost).filter(
        RdCost.status == 'APPROVED',
        RdCost.is_allocated == False  # 只分摊未分摊的费用
    )
    
    # 如果指定了费用ID列表，则只分摊这些费用
    if cost_ids:
        query = query.filter(RdCost.id.in_(cost_ids))
    else:
        # 根据规则的适用范围筛选费用
        if rule.cost_type_ids:
            query = query.filter(RdCost.cost_type_id.in_(rule.cost_type_ids))
    
    costs = query.all()
    
    if not costs:
        return ResponseModel(
            code=200,
            message="没有需要分摊的费用",
            data={"allocated_count": 0}
        )
    
    # 获取规则适用的项目列表
    target_project_ids = rule.project_ids if rule.project_ids else []
    if not target_project_ids:
        # 如果没有指定项目，则分摊到所有已审批的研发项目
        projects = db.query(RdProject).filter(
            RdProject.status.in_(['APPROVED', 'IN_PROGRESS'])
        ).all()
        target_project_ids = [p.id for p in projects]
    
    if not target_project_ids:
        return ResponseModel(
            code=400,
            message="没有可分摊的目标项目",
            data={"allocated_count": 0}
        )
    
    # 根据分摊依据计算分摊比例
    allocation_rates = {}
    
    if rule.allocation_basis == 'HOURS':
        # 按工时分摊：计算每个项目的工时占比
        total_hours = Decimal(0)
        project_hours = {}
        
        for project_id in target_project_ids:
            project = db.query(RdProject).filter(RdProject.id == project_id).first()
            if project and project.total_hours:
                hours = Decimal(str(project.total_hours))
                project_hours[project_id] = hours
                total_hours += hours
        
        if total_hours > 0:
            for project_id, hours in project_hours.items():
                allocation_rates[project_id] = float(hours / total_hours * 100)
        else:
            # 如果总工时为0，则平均分摊
            rate = 100.0 / len(target_project_ids)
            for project_id in target_project_ids:
                allocation_rates[project_id] = rate
    elif rule.allocation_basis == 'REVENUE':
        # 按收入分摊：需要从项目模块获取收入数据
        # TODO: 从项目模块获取收入数据
        # 暂时使用平均分摊
        rate = 100.0 / len(target_project_ids)
        for project_id in target_project_ids:
            allocation_rates[project_id] = rate
    elif rule.allocation_basis == 'HEADCOUNT':
        # 按人数分摊：计算每个项目的参与人数占比
        total_participants = 0
        project_participants = {}
        
        for project_id in target_project_ids:
            project = db.query(RdProject).filter(RdProject.id == project_id).first()
            if project and project.participant_count:
                participants = project.participant_count
                project_participants[project_id] = participants
                total_participants += participants
        
        if total_participants > 0:
            for project_id, participants in project_participants.items():
                allocation_rates[project_id] = float(participants / total_participants * 100)
        else:
            # 如果总人数为0，则平均分摊
            rate = 100.0 / len(target_project_ids)
            for project_id in target_project_ids:
                allocation_rates[project_id] = rate
    else:
        # 默认平均分摊
        rate = 100.0 / len(target_project_ids)
        for project_id in target_project_ids:
            allocation_rates[project_id] = rate
    
    # 应用分摊规则，创建分摊后的费用记录
    allocated_count = 0
    
    for cost in costs:
        # 为每个目标项目创建分摊后的费用记录
        for project_id, rate in allocation_rates.items():
            # 计算分摊金额
            allocated_amount = cost.cost_amount * Decimal(str(rate)) / 100
            
            # 创建分摊后的费用记录
            allocated_cost = RdCost(
                cost_no=generate_cost_no(db),
                rd_project_id=project_id,
                cost_type_id=cost.cost_type_id,
                cost_date=cost.cost_date,
                cost_amount=allocated_amount,
                cost_description=f"{cost.cost_description or ''}（分摊自费用{cost.cost_no}）",
                source_type='ALLOCATED',
                source_id=cost.id,
                is_allocated=True,
                allocation_rule_id=rule_id,
                allocation_rate=Decimal(str(rate)),
                deductible_amount=allocated_amount * (cost.deductible_amount / cost.cost_amount) if cost.deductible_amount and cost.cost_amount > 0 else None,
                status='APPROVED',  # 分摊的费用直接审批通过
                remark=f"由规则{rule.rule_name}自动分摊"
            )
            
            db.add(allocated_cost)
            
            # 更新目标项目的总费用
            project = db.query(RdProject).filter(RdProject.id == project_id).first()
            if project:
                project.total_cost = (project.total_cost or 0) + allocated_amount
        
        # 标记原费用为已分摊
        cost.is_allocated = True
        cost.allocation_rule_id = rule_id
        db.add(cost)
        allocated_count += 1
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message=f"费用分摊成功，共分摊{allocated_count}条费用到{len(target_project_ids)}个项目",
        data={
            "allocated_count": allocated_count,
            "target_projects": len(target_project_ids),
            "allocation_rates": allocation_rates
        }
    )


@router.get("/rd-projects/{project_id}/timesheet-summary", response_model=ResponseModel)
def get_rd_project_timesheet_summary(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取研发项目工时汇总
    """
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")
    
    # 查询关联的非标项目
    linked_project_ids = []
    if project.linked_project_id:
        linked_project_ids.append(project.linked_project_id)
    
    # 如果没有关联的非标项目，无法统计工时
    if not linked_project_ids:
        return ResponseModel(
            code=200,
            message="success",
            data={
                "rd_project_id": project_id,
                "rd_project_name": project.project_name,
                "total_hours": 0,
                "total_participants": 0,
                "by_user": [],
                "by_date": {},
                "note": "研发项目未关联非标项目，无法统计工时"
            }
        )
    
    # 查询工时记录（从关联的非标项目）
    query = db.query(Timesheet).filter(
        Timesheet.project_id.in_(linked_project_ids),
        Timesheet.status == 'APPROVED'
    )
    
    if start_date:
        query = query.filter(Timesheet.work_date >= start_date)
    if end_date:
        query = query.filter(Timesheet.work_date <= end_date)
    
    timesheets = query.all()
    
    # 统计汇总
    total_hours = Decimal(0)
    by_user = {}
    by_date = {}
    participants = set()
    
    for ts in timesheets:
        hours = Decimal(str(ts.hours or 0))
        total_hours += hours
        participants.add(ts.user_id)
        
        # 按用户统计
        user = db.query(User).filter(User.id == ts.user_id).first()
        user_name = user.real_name or user.username if user else f"用户{ts.user_id}"
        if user_name not in by_user:
            by_user[user_name] = {
                'user_id': ts.user_id,
                'user_name': user_name,
                'total_hours': Decimal(0),
                'days': 0
            }
        by_user[user_name]['total_hours'] += hours
        by_user[user_name]['days'] += 1
        
        # 按日期统计
        date_str = ts.work_date.isoformat()
        if date_str not in by_date:
            by_date[date_str] = Decimal(0)
        by_date[date_str] += hours
    
    # 更新研发项目的总工时和参与人数
    project.total_hours = total_hours
    project.participant_count = len(participants)
    db.add(project)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "rd_project_id": project_id,
            "rd_project_name": project.project_name,
            "total_hours": float(total_hours),
            "total_participants": len(participants),
            "by_user": list(by_user.values()),
            "by_date": {k: float(v) for k, v in by_date.items()},
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }
    )


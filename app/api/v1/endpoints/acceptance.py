# -*- coding: utf-8 -*-
"""
验收管理 API endpoints
包含：验收模板、验收单、检查项、问题管理、签字与报告
"""

import os
import hashlib
from typing import Any, List, Optional
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.project import Project, Machine
from app.models.acceptance import (
    AcceptanceTemplate, TemplateCategory, TemplateCheckItem,
    AcceptanceOrder, AcceptanceOrderItem,
    AcceptanceIssue, IssueFollowUp,
    AcceptanceSignature, AcceptanceReport
)
from app.schemas.acceptance import (
    AcceptanceTemplateCreate, AcceptanceTemplateResponse,
    TemplateCategoryCreate, TemplateCheckItemCreate,
    AcceptanceOrderCreate, AcceptanceOrderUpdate, AcceptanceOrderStart, AcceptanceOrderComplete,
    AcceptanceOrderResponse, AcceptanceOrderListResponse,
    CheckItemResultUpdate, CheckItemResultResponse,
    AcceptanceIssueCreate, AcceptanceIssueUpdate, AcceptanceIssueResponse,
    AcceptanceSignatureCreate, AcceptanceSignatureResponse,
    AcceptanceReportGenerateRequest, AcceptanceReportResponse
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


def generate_order_no(db: Session) -> str:
    """生成验收单号：AC-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_order = (
        db.query(AcceptanceOrder)
        .filter(AcceptanceOrder.order_no.like(f"AC-{today}-%"))
        .order_by(desc(AcceptanceOrder.order_no))
        .first()
    )
    if max_order:
        seq = int(max_order.order_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"AC-{today}-{seq:03d}"


def generate_issue_no(db: Session) -> str:
    """生成问题编号：IS-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_issue = (
        db.query(AcceptanceIssue)
        .filter(AcceptanceIssue.issue_no.like(f"IS-{today}-%"))
        .order_by(desc(AcceptanceIssue.issue_no))
        .first()
    )
    if max_issue:
        seq = int(max_issue.issue_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"IS-{today}-{seq:03d}"


# ==================== 验收模板 ====================

@router.get("/acceptance-templates", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_acceptance_templates(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（编码/名称）"),
    acceptance_type: Optional[str] = Query(None, description="验收类型筛选"),
    equipment_type: Optional[str] = Query(None, description="设备类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收模板列表
    """
    query = db.query(AcceptanceTemplate)
    
    if keyword:
        query = query.filter(
            or_(
                AcceptanceTemplate.template_code.like(f"%{keyword}%"),
                AcceptanceTemplate.template_name.like(f"%{keyword}%"),
            )
        )
    
    if acceptance_type:
        query = query.filter(AcceptanceTemplate.acceptance_type == acceptance_type)
    
    if equipment_type:
        query = query.filter(AcceptanceTemplate.equipment_type == equipment_type)
    
    if is_active is not None:
        query = query.filter(AcceptanceTemplate.is_active == is_active)
    
    total = query.count()
    offset = (page - 1) * page_size
    templates = query.order_by(AcceptanceTemplate.created_at).offset(offset).limit(page_size).all()
    
    items = []
    for template in templates:
        items.append(AcceptanceTemplateResponse(
            id=template.id,
            template_code=template.template_code,
            template_name=template.template_name,
            acceptance_type=template.acceptance_type,
            equipment_type=template.equipment_type,
            version=template.version,
            is_system=template.is_system,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/acceptance-templates/{template_id}", response_model=dict, status_code=status.HTTP_200_OK)
def read_acceptance_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收模板详情（含分类和检查项）
    """
    template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="验收模板不存在")
    
    # 获取分类
    categories_data = []
    categories = db.query(TemplateCategory).filter(TemplateCategory.template_id == template_id).order_by(TemplateCategory.sort_order).all()
    for category in categories:
        # 获取检查项
        items_data = []
        items = db.query(TemplateCheckItem).filter(TemplateCheckItem.category_id == category.id).order_by(TemplateCheckItem.sort_order).all()
        for item in items:
            items_data.append({
                "id": item.id,
                "item_code": item.item_code,
                "item_name": item.item_name,
                "check_method": item.check_method,
                "acceptance_criteria": item.acceptance_criteria,
                "standard_value": item.standard_value,
                "tolerance_min": item.tolerance_min,
                "tolerance_max": item.tolerance_max,
                "unit": item.unit,
                "is_required": item.is_required,
                "is_key_item": item.is_key_item,
                "sort_order": item.sort_order
            })
        
        categories_data.append({
            "id": category.id,
            "category_code": category.category_code,
            "category_name": category.category_name,
            "weight": float(category.weight) if category.weight else 0,
            "sort_order": category.sort_order,
            "is_required": category.is_required,
            "description": category.description,
            "check_items": items_data
        })
    
    return {
        "id": template.id,
        "template_code": template.template_code,
        "template_name": template.template_name,
        "acceptance_type": template.acceptance_type,
        "equipment_type": template.equipment_type,
        "version": template.version,
        "description": template.description,
        "is_system": template.is_system,
        "is_active": template.is_active,
        "categories": categories_data,
        "created_at": template.created_at,
        "updated_at": template.updated_at
    }


@router.post("/acceptance-templates", response_model=AcceptanceTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_acceptance_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: AcceptanceTemplateCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建验收模板
    """
    # 检查编码是否已存在
    existing = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.template_code == template_in.template_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")
    
    template = AcceptanceTemplate(
        template_code=template_in.template_code,
        template_name=template_in.template_name,
        acceptance_type=template_in.acceptance_type,
        equipment_type=template_in.equipment_type,
        version=template_in.version,
        description=template_in.description,
        is_system=False,
        is_active=True,
        created_by=current_user.id
    )
    
    db.add(template)
    db.flush()  # 获取template.id
    
    # 创建分类和检查项
    for cat_in in template_in.categories:
        category = TemplateCategory(
            template_id=template.id,
            category_code=cat_in.category_code,
            category_name=cat_in.category_name,
            weight=cat_in.weight,
            sort_order=cat_in.sort_order,
            is_required=cat_in.is_required,
            description=cat_in.description
        )
        db.add(category)
        db.flush()  # 获取category.id
        
        # 创建检查项
        for item_in in cat_in.check_items:
            item = TemplateCheckItem(
                category_id=category.id,
                item_code=item_in.item_code,
                item_name=item_in.item_name,
                check_method=item_in.check_method,
                acceptance_criteria=item_in.acceptance_criteria,
                standard_value=item_in.standard_value,
                tolerance_min=item_in.tolerance_min,
                tolerance_max=item_in.tolerance_max,
                unit=item_in.unit,
                is_required=item_in.is_required,
                is_key_item=item_in.is_key_item,
                sort_order=item_in.sort_order
            )
            db.add(item)
    
    db.commit()
    db.refresh(template)
    
    return AcceptanceTemplateResponse(
        id=template.id,
        template_code=template.template_code,
        template_name=template.template_name,
        acceptance_type=template.acceptance_type,
        equipment_type=template.equipment_type,
        version=template.version,
        is_system=template.is_system,
        is_active=template.is_active,
        created_at=template.created_at,
        updated_at=template.updated_at
    )


@router.get("/acceptance-templates/{template_id}/items", response_model=List[dict], status_code=status.HTTP_200_OK)
def read_template_items(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取模板检查项列表
    """
    template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="验收模板不存在")
    
    categories = db.query(TemplateCategory).filter(TemplateCategory.template_id == template_id).order_by(TemplateCategory.sort_order).all()
    
    items_data = []
    for category in categories:
        items = db.query(TemplateCheckItem).filter(TemplateCheckItem.category_id == category.id).order_by(TemplateCheckItem.sort_order).all()
        for item in items:
            items_data.append({
                "id": item.id,
                "category_id": category.id,
                "category_code": category.category_code,
                "category_name": category.category_name,
                "item_code": item.item_code,
                "item_name": item.item_name,
                "check_method": item.check_method,
                "acceptance_criteria": item.acceptance_criteria,
                "standard_value": item.standard_value,
                "tolerance_min": item.tolerance_min,
                "tolerance_max": item.tolerance_max,
                "unit": item.unit,
                "is_required": item.is_required,
                "is_key_item": item.is_key_item,
                "sort_order": item.sort_order
            })
    
    return items_data


@router.post("/acceptance-templates/{template_id}/items", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def add_template_items(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    category_id: int = Query(..., description="分类ID"),
    items: List[TemplateCheckItemCreate],
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加模板检查项
    """
    template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="验收模板不存在")
    
    category = db.query(TemplateCategory).filter(
        TemplateCategory.id == category_id,
        TemplateCategory.template_id == template_id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在或不属于该模板")
    
    for item_in in items:
        item = TemplateCheckItem(
            category_id=category_id,
            item_code=item_in.item_code,
            item_name=item_in.item_name,
            check_method=item_in.check_method,
            acceptance_criteria=item_in.acceptance_criteria,
            standard_value=item_in.standard_value,
            tolerance_min=item_in.tolerance_min,
            tolerance_max=item_in.tolerance_max,
            unit=item_in.unit,
            is_required=item_in.is_required,
            is_key_item=item_in.is_key_item,
            sort_order=item_in.sort_order
        )
        db.add(item)
    
    db.commit()
    
    return ResponseModel(message="检查项添加成功")


# ==================== 验收单 ====================

@router.get("/acceptance-orders", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_acceptance_orders(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（验收单号）"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    acceptance_type: Optional[str] = Query(None, description="验收类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收单列表
    """
    query = db.query(AcceptanceOrder)
    
    if keyword:
        query = query.filter(AcceptanceOrder.order_no.like(f"%{keyword}%"))
    
    if project_id:
        query = query.filter(AcceptanceOrder.project_id == project_id)
    
    if machine_id:
        query = query.filter(AcceptanceOrder.machine_id == machine_id)
    
    if acceptance_type:
        query = query.filter(AcceptanceOrder.acceptance_type == acceptance_type)
    
    if status:
        query = query.filter(AcceptanceOrder.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    orders = query.order_by(desc(AcceptanceOrder.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for order in orders:
        project = db.query(Project).filter(Project.id == order.project_id).first()
        machine = None
        if order.machine_id:
            machine = db.query(Machine).filter(Machine.id == order.machine_id).first()
        
        # 统计开放问题数
        open_issues = db.query(AcceptanceIssue).filter(
            AcceptanceIssue.order_id == order.id,
            AcceptanceIssue.status.in_(["OPEN", "IN_PROGRESS"])
        ).count()
        
        items.append(AcceptanceOrderListResponse(
            id=order.id,
            order_no=order.order_no,
            project_name=project.project_name if project else None,
            machine_name=machine.machine_name if machine else None,
            acceptance_type=order.acceptance_type,
            planned_date=order.planned_date,
            status=order.status,
            overall_result=order.overall_result,
            pass_rate=order.pass_rate or Decimal("0"),
            open_issues=open_issues,
            created_at=order.created_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/acceptance-orders/{order_id}", response_model=AcceptanceOrderResponse, status_code=status.HTTP_200_OK)
def read_acceptance_order(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收单详情
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    project = db.query(Project).filter(Project.id == order.project_id).first()
    machine = None
    if order.machine_id:
        machine = db.query(Machine).filter(Machine.id == order.machine_id).first()
    
    template = None
    if order.template_id:
        template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == order.template_id).first()
    
    return AcceptanceOrderResponse(
        id=order.id,
        order_no=order.order_no,
        project_id=order.project_id,
        project_name=project.project_name if project else None,
        machine_id=order.machine_id,
        machine_name=machine.machine_name if machine else None,
        acceptance_type=order.acceptance_type,
        template_id=order.template_id,
        template_name=template.template_name if template else None,
        planned_date=order.planned_date,
        actual_start_date=order.actual_start_date,
        actual_end_date=order.actual_end_date,
        location=order.location,
        status=order.status,
        total_items=order.total_items or 0,
        passed_items=order.passed_items or 0,
        failed_items=order.failed_items or 0,
        na_items=order.na_items or 0,
        pass_rate=order.pass_rate or Decimal("0"),
        overall_result=order.overall_result,
        conclusion=order.conclusion,
        created_at=order.created_at,
        updated_at=order.updated_at
    )


@router.post("/acceptance-orders", response_model=AcceptanceOrderResponse, status_code=status.HTTP_201_CREATED)
def create_acceptance_order(
    *,
    db: Session = Depends(deps.get_db),
    order_in: AcceptanceOrderCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建验收单(FAT/SAT/FINAL)
    """
    # 验证项目
    project = db.query(Project).filter(Project.id == order_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 验证机台（如果提供）
    if order_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == order_in.machine_id).first()
        if not machine or machine.project_id != order_in.project_id:
            raise HTTPException(status_code=400, detail="机台不存在或不属于该项目")
    
    # 验证模板（如果提供）
    template = None
    if order_in.template_id:
        template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == order_in.template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="验收模板不存在")
        if template.acceptance_type != order_in.acceptance_type:
            raise HTTPException(status_code=400, detail="模板类型与验收类型不匹配")
    
    order_no = generate_order_no(db)
    
    order = AcceptanceOrder(
        order_no=order_no,
        project_id=order_in.project_id,
        machine_id=order_in.machine_id,
        acceptance_type=order_in.acceptance_type,
        template_id=order_in.template_id,
        planned_date=order_in.planned_date,
        location=order_in.location,
        status="DRAFT",
        created_by=current_user.id
    )
    
    db.add(order)
    db.flush()  # 获取order.id
    
    # 如果使用了模板，从模板创建检查项
    if template:
        categories = db.query(TemplateCategory).filter(TemplateCategory.template_id == template.id).all()
        item_no = 0
        for category in categories:
            items = db.query(TemplateCheckItem).filter(TemplateCheckItem.category_id == category.id).all()
            for item in items:
                item_no += 1
                order_item = AcceptanceOrderItem(
                    order_id=order.id,
                    category_id=category.id,
                    category_code=category.category_code,
                    category_name=category.category_name,
                    item_code=item.item_code,
                    item_name=item.item_name,
                    check_method=item.check_method,
                    acceptance_criteria=item.acceptance_criteria,
                    standard_value=item.standard_value,
                    tolerance_min=item.tolerance_min,
                    tolerance_max=item.tolerance_max,
                    unit=item.unit,
                    is_required=item.is_required,
                    is_key_item=item.is_key_item,
                    sort_order=item.sort_order,
                    result_status="PENDING"
                )
                db.add(order_item)
        
        order.total_items = item_no
        db.add(order)
    
    db.commit()
    db.refresh(order)
    
    return read_acceptance_order(order.id, db, current_user)


@router.put("/acceptance-orders/{order_id}/start", response_model=AcceptanceOrderResponse, status_code=status.HTTP_200_OK)
def start_acceptance(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    start_in: AcceptanceOrderStart,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    开始验收
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    if order.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能开始草稿状态的验收单")
    
    if order.total_items == 0:
        raise HTTPException(status_code=400, detail="验收单没有检查项，无法开始验收")
    
    order.status = "IN_PROGRESS"
    order.actual_start_date = datetime.now()
    if start_in.location:
        order.location = start_in.location
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_acceptance_order(order_id, db, current_user)


@router.get("/acceptance-orders/{order_id}/items", response_model=List[CheckItemResultResponse], status_code=status.HTTP_200_OK)
def read_acceptance_order_items(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收检查项列表
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    items = db.query(AcceptanceOrderItem).filter(AcceptanceOrderItem.order_id == order_id).order_by(
        AcceptanceOrderItem.category_code, AcceptanceOrderItem.sort_order
    ).all()
    
    items_data = []
    for item in items:
        checked_by_name = None
        if item.checked_by:
            user = db.query(User).filter(User.id == item.checked_by).first()
            checked_by_name = user.real_name or user.username if user else None
        
        items_data.append(CheckItemResultResponse(
            id=item.id,
            category_code=item.category_code,
            category_name=item.category_name,
            item_code=item.item_code,
            item_name=item.item_name,
            check_method=item.check_method,
            acceptance_criteria=item.acceptance_criteria,
            standard_value=item.standard_value,
            tolerance_min=item.tolerance_min,
            tolerance_max=item.tolerance_max,
            unit=item.unit,
            is_required=item.is_required,
            is_key_item=item.is_key_item,
            result_status=item.result_status,
            actual_value=item.actual_value,
            deviation=item.deviation,
            remark=item.remark,
            checked_by=item.checked_by,
            checked_at=item.checked_at,
            created_at=item.created_at,
            updated_at=item.updated_at
        ))
    
    return items_data


@router.put("/acceptance-items/{item_id}", response_model=CheckItemResultResponse, status_code=status.HTTP_200_OK)
def update_check_item_result(
    *,
    db: Session = Depends(deps.get_db),
    item_id: int,
    result_in: CheckItemResultUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新检查项结果
    """
    item = db.query(AcceptanceOrderItem).filter(AcceptanceOrderItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="检查项不存在")
    
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == item.order_id).first()
    if order.status != "IN_PROGRESS":
        raise HTTPException(status_code=400, detail="只能更新进行中验收单的检查项")
    
    # 更新检查项结果
    item.result_status = result_in.result_status
    item.actual_value = result_in.actual_value
    item.deviation = result_in.deviation
    item.remark = result_in.remark
    item.checked_by = current_user.id
    item.checked_at = datetime.now()
    
    db.add(item)
    
    # 更新验收单统计
    items = db.query(AcceptanceOrderItem).filter(AcceptanceOrderItem.order_id == order.id).all()
    passed = len([i for i in items if i.result_status == "PASSED"])
    failed = len([i for i in items if i.result_status == "FAILED"])
    na = len([i for i in items if i.result_status == "NA"])
    total = len([i for i in items if i.result_status != "PENDING"])
    
    order.passed_items = passed
    order.failed_items = failed
    order.na_items = na
    order.total_items = len(items)
    
    if total > 0:
        order.pass_rate = Decimal(str((passed / total) * 100))
    else:
        order.pass_rate = Decimal("0")
    
    db.add(order)
    db.commit()
    db.refresh(item)
    
    return CheckItemResultResponse(
        id=item.id,
        category_code=item.category_code,
        category_name=item.category_name,
        item_code=item.item_code,
        item_name=item.item_name,
        check_method=item.check_method,
        acceptance_criteria=item.acceptance_criteria,
        standard_value=item.standard_value,
        tolerance_min=item.tolerance_min,
        tolerance_max=item.tolerance_max,
        unit=item.unit,
        is_required=item.is_required,
        is_key_item=item.is_key_item,
        result_status=item.result_status,
        actual_value=item.actual_value,
        deviation=item.deviation,
        remark=item.remark,
        checked_by=item.checked_by,
        checked_at=item.checked_at,
        created_at=item.created_at,
        updated_at=item.updated_at
    )


@router.put("/acceptance-orders/{order_id}/complete", response_model=AcceptanceOrderResponse, status_code=status.HTTP_200_OK)
def complete_acceptance(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    complete_in: AcceptanceOrderComplete,
    auto_trigger_invoice: bool = Query(True, description="自动触发开票"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    完成验收（自动触发收款计划开票）
    """
    from app.models.project import ProjectPaymentPlan, ProjectMilestone
    from app.models.sales import Invoice, InvoiceStatusEnum, Contract
    from decimal import Decimal
    from datetime import timedelta
    
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    if order.status != "IN_PROGRESS":
        raise HTTPException(status_code=400, detail="只能完成进行中状态的验收单")
    
    # 检查是否所有必检项都已检查
    pending_items = db.query(AcceptanceOrderItem).filter(
        AcceptanceOrderItem.order_id == order_id,
        AcceptanceOrderItem.is_required == True,
        AcceptanceOrderItem.result_status == "PENDING"
    ).count()
    
    if pending_items > 0:
        raise HTTPException(status_code=400, detail=f"还有 {pending_items} 个必检项未完成检查")
    
    order.status = "COMPLETED"
    order.actual_end_date = datetime.now()
    order.overall_result = complete_in.overall_result
    order.conclusion = complete_in.conclusion
    order.conditions = complete_in.conditions
    
    db.add(order)
    db.flush()
    
    # 如果验收通过，检查是否有绑定的收款计划，自动触发开票
    if auto_trigger_invoice and complete_in.overall_result == "PASSED":
        # 查找与验收相关的里程碑（终验类型）
        milestones = db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == order.project_id,
            ProjectMilestone.milestone_type.in_(["FINAL_ACCEPTANCE", "SAT_PASS"]),
            ProjectMilestone.status == "COMPLETED"
        ).all()
        
        for milestone in milestones:
            # 查找绑定的收款计划
            payment_plans = db.query(ProjectPaymentPlan).filter(
                ProjectPaymentPlan.milestone_id == milestone.id,
                ProjectPaymentPlan.status == "PENDING",
                ProjectPaymentPlan.payment_type == "ACCEPTANCE"
            ).all()
            
            for plan in payment_plans:
                # 检查是否已开票
                if plan.invoice_id:
                    continue
                
                # 获取合同信息
                contract = None
                if plan.contract_id:
                    contract = db.query(Contract).filter(Contract.id == plan.contract_id).first()
                
                if contract:
                    # 自动创建发票
                    # 生成发票编码
                    from sqlalchemy import desc
                    from app.models.sales import Invoice as InvoiceModel
                    today = datetime.now()
                    month_str = today.strftime("%y%m")
                    prefix = f"INV{month_str}-"
                    max_invoice = (
                        db.query(InvoiceModel)
                        .filter(InvoiceModel.invoice_code.like(f"{prefix}%"))
                        .order_by(desc(InvoiceModel.invoice_code))
                        .first()
                    )
                    if max_invoice:
                        try:
                            seq = int(max_invoice.invoice_code.split("-")[-1]) + 1
                        except:
                            seq = 1
                    else:
                        seq = 1
                    invoice_code = f"{prefix}{seq:03d}"
                    invoice = Invoice(
                        invoice_code=invoice_code,
                        contract_id=contract.id,
                        project_id=plan.project_id,
                        payment_id=None,
                        invoice_type="NORMAL",
                        amount=plan.planned_amount,
                        tax_rate=Decimal("13"),
                        tax_amount=plan.planned_amount * Decimal("13") / Decimal("100"),
                        total_amount=plan.planned_amount * Decimal("113") / Decimal("100"),
                        status=InvoiceStatusEnum.DRAFT,
                        payment_status="PENDING",
                        issue_date=date.today(),
                        due_date=date.today() + timedelta(days=30),
                        buyer_name=contract.customer.customer_name if contract.customer else None,
                        buyer_tax_no=contract.customer.tax_no if contract.customer else None,
                    )
                    db.add(invoice)
                    db.flush()
                    
                    # 更新收款计划
                    plan.invoice_id = invoice.id
                    plan.invoice_no = invoice_code
                    plan.invoice_date = date.today()
                    plan.invoice_amount = invoice.total_amount
                    plan.status = "INVOICED"
                    
                    db.add(plan)
    
    db.commit()
    db.refresh(order)
    
    return read_acceptance_order(order_id, db, current_user)


# ==================== 验收问题 ====================

@router.get("/acceptance-orders/{order_id}/issues", response_model=List[AcceptanceIssueResponse], status_code=status.HTTP_200_OK)
def read_acceptance_issues(
    order_id: int,
    db: Session = Depends(deps.get_db),
    status: Optional[str] = Query(None, description="问题状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收问题列表
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    query = db.query(AcceptanceIssue).filter(AcceptanceIssue.order_id == order_id)
    
    if status:
        query = query.filter(AcceptanceIssue.status == status)
    
    issues = query.order_by(desc(AcceptanceIssue.found_at)).all()
    
    items = []
    for issue in issues:
        found_by_name = None
        if issue.found_by:
            user = db.query(User).filter(User.id == issue.found_by).first()
            found_by_name = user.real_name or user.username if user else None
        
        assigned_to_name = None
        if issue.assigned_to:
            user = db.query(User).filter(User.id == issue.assigned_to).first()
            assigned_to_name = user.real_name or user.username if user else None
        
        items.append(AcceptanceIssueResponse(
            id=issue.id,
            issue_no=issue.issue_no,
            order_id=issue.order_id,
            order_item_id=issue.order_item_id,
            issue_type=issue.issue_type,
            severity=issue.severity,
            title=issue.title,
            description=issue.description,
            found_at=issue.found_at,
            found_by=issue.found_by,
            found_by_name=found_by_name,
            status=issue.status,
            assigned_to=issue.assigned_to,
            assigned_to_name=assigned_to_name,
            due_date=issue.due_date,
            solution=issue.solution,
            resolved_at=issue.resolved_at,
            is_blocking=issue.is_blocking,
            created_at=issue.created_at,
            updated_at=issue.updated_at
        ))
    
    return items


@router.post("/acceptance-orders/{order_id}/issues", response_model=AcceptanceIssueResponse, status_code=status.HTTP_201_CREATED)
def create_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    issue_in: AcceptanceIssueCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建验收问题
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    if issue_in.order_id != order_id:
        raise HTTPException(status_code=400, detail="问题所属验收单ID不匹配")
    
    # 验证检查项（如果提供）
    if issue_in.order_item_id:
        item = db.query(AcceptanceOrderItem).filter(AcceptanceOrderItem.id == issue_in.order_item_id).first()
        if not item or item.order_id != order_id:
            raise HTTPException(status_code=400, detail="检查项不存在或不属于该验收单")
    
    issue_no = generate_issue_no(db)
    
    issue = AcceptanceIssue(
        issue_no=issue_no,
        order_id=order_id,
        order_item_id=issue_in.order_item_id,
        issue_type=issue_in.issue_type,
        severity=issue_in.severity,
        title=issue_in.title,
        description=issue_in.description,
        found_by=current_user.id,
        found_at=datetime.now(),
        status="OPEN",
        assigned_to=issue_in.assigned_to,
        due_date=issue_in.due_date,
        is_blocking=issue_in.is_blocking,
        attachments=issue_in.attachments
    )
    
    db.add(issue)
    db.commit()
    db.refresh(issue)
    
    found_by_name = current_user.real_name or current_user.username
    assigned_to_name = None
    if issue.assigned_to:
        user = db.query(User).filter(User.id == issue.assigned_to).first()
        assigned_to_name = user.real_name or user.username if user else None
    
    return AcceptanceIssueResponse(
        id=issue.id,
        issue_no=issue.issue_no,
        order_id=issue.order_id,
        order_item_id=issue.order_item_id,
        issue_type=issue.issue_type,
        severity=issue.severity,
        title=issue.title,
        description=issue.description,
        found_at=issue.found_at,
        found_by=issue.found_by,
        found_by_name=found_by_name,
        status=issue.status,
        assigned_to=issue.assigned_to,
        assigned_to_name=assigned_to_name,
        due_date=issue.due_date,
        solution=issue.solution,
        resolved_at=issue.resolved_at,
        is_blocking=issue.is_blocking,
        created_at=issue.created_at,
        updated_at=issue.updated_at
    )


@router.put("/acceptance-issues/{issue_id}", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def update_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    issue_in: AcceptanceIssueUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新问题状态
    """
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")
    
    update_data = issue_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(issue, field, value)
    
    # 如果状态更新为已解决，记录解决时间
    if issue_in.status == "RESOLVED" and not issue.resolved_at:
        issue.resolved_at = datetime.now()
    
    db.add(issue)
    db.commit()
    db.refresh(issue)
    
    found_by_name = None
    if issue.found_by:
        user = db.query(User).filter(User.id == issue.found_by).first()
        found_by_name = user.real_name or user.username if user else None
    
    assigned_to_name = None
    if issue.assigned_to:
        user = db.query(User).filter(User.id == issue.assigned_to).first()
        assigned_to_name = user.real_name or user.username if user else None
    
    return AcceptanceIssueResponse(
        id=issue.id,
        issue_no=issue.issue_no,
        order_id=issue.order_id,
        order_item_id=issue.order_item_id,
        issue_type=issue.issue_type,
        severity=issue.severity,
        title=issue.title,
        description=issue.description,
        found_at=issue.found_at,
        found_by=issue.found_by,
        found_by_name=found_by_name,
        status=issue.status,
        assigned_to=issue.assigned_to,
        assigned_to_name=assigned_to_name,
        due_date=issue.due_date,
        solution=issue.solution,
        resolved_at=issue.resolved_at,
        is_blocking=issue.is_blocking,
        created_at=issue.created_at,
        updated_at=issue.updated_at
    )


@router.put("/acceptance-issues/{issue_id}/close", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def close_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    solution: Optional[str] = Query(None, description="解决方案"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    关闭问题
    """
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")
    
    if issue.status == "CLOSED":
        raise HTTPException(status_code=400, detail="问题已经关闭")
    
    issue.status = "CLOSED"
    issue.solution = solution
    issue.resolved_at = datetime.now()
    
    db.add(issue)
    db.commit()
    db.refresh(issue)
    
    found_by_name = None
    if issue.found_by:
        user = db.query(User).filter(User.id == issue.found_by).first()
        found_by_name = user.real_name or user.username if user else None
    
    assigned_to_name = None
    if issue.assigned_to:
        user = db.query(User).filter(User.id == issue.assigned_to).first()
        assigned_to_name = user.real_name or user.username if user else None
    
    return AcceptanceIssueResponse(
        id=issue.id,
        issue_no=issue.issue_no,
        order_id=issue.order_id,
        order_item_id=issue.order_item_id,
        issue_type=issue.issue_type,
        severity=issue.severity,
        title=issue.title,
        description=issue.description,
        found_at=issue.found_at,
        found_by=issue.found_by,
        found_by_name=found_by_name,
        status=issue.status,
        assigned_to=issue.assigned_to,
        assigned_to_name=assigned_to_name,
        due_date=issue.due_date,
        solution=issue.solution,
        resolved_at=issue.resolved_at,
        is_blocking=issue.is_blocking,
        created_at=issue.created_at,
        updated_at=issue.updated_at
    )


@router.post("/acceptance-issues/{issue_id}/follow-ups", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def add_issue_follow_up(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    follow_up_note: str = Query(..., description="跟进记录"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加跟进记录
    """
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")
    
    follow_up = IssueFollowUp(
        issue_id=issue_id,
        action_type="FOLLOW_UP",
        action_content=follow_up_note,
        created_by=current_user.id
    )
    
    db.add(follow_up)
    db.commit()
    
    return ResponseModel(message="跟进记录添加成功")


# ==================== 验收签字 ====================

@router.get("/acceptance-orders/{order_id}/signatures", response_model=List[AcceptanceSignatureResponse], status_code=status.HTTP_200_OK)
def read_acceptance_signatures(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收签字列表
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    signatures = db.query(AcceptanceSignature).filter(AcceptanceSignature.order_id == order_id).order_by(AcceptanceSignature.signed_at).all()
    
    items = []
    for sig in signatures:
        items.append(AcceptanceSignatureResponse(
            id=sig.id,
            order_id=sig.order_id,
            signer_type=sig.signer_type,
            signer_role=sig.signer_role,
            signer_name=sig.signer_name,
            signer_company=sig.signer_company,
            signed_at=sig.signed_at,
            ip_address=sig.ip_address,
            created_at=sig.created_at,
            updated_at=sig.updated_at
        ))
    
    return items


@router.post("/acceptance-orders/{order_id}/signatures", response_model=AcceptanceSignatureResponse, status_code=status.HTTP_201_CREATED)
def add_acceptance_signature(
    *,
    db: Session = Depends(deps.get_db),
    request: Request,
    order_id: int,
    signature_in: AcceptanceSignatureCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加签字
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    if order.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="只能为已完成状态的验收单添加签字")
    
    if signature_in.order_id != order_id:
        raise HTTPException(status_code=400, detail="签字所属验收单ID不匹配")
    
    signature = AcceptanceSignature(
        order_id=order_id,
        signer_type=signature_in.signer_type,
        signer_role=signature_in.signer_role,
        signer_name=signature_in.signer_name,
        signer_company=signature_in.signer_company,
        signature_data=signature_in.signature_data,
        signed_at=datetime.now(),
        ip_address=request.client.host if request and request.client else None
    )
    
    # 如果是QA签字，更新验收单
    if signature_in.signer_type == "QA":
        order.qa_signer_id = current_user.id
        order.qa_signed_at = datetime.now()
        db.add(order)
    
    # 如果是客户签字，更新验收单
    if signature_in.signer_type == "CUSTOMER":
        order.customer_signer = signature_in.signer_name
        order.customer_signed_at = datetime.now()
        order.customer_signature = signature_in.signature_data
        db.add(order)
    
    db.add(signature)
    db.commit()
    db.refresh(signature)
    
    return AcceptanceSignatureResponse(
        id=signature.id,
        order_id=signature.order_id,
        signer_type=signature.signer_type,
        signer_role=signature.signer_role,
        signer_name=signature.signer_name,
        signer_company=signature.signer_company,
        signed_at=signature.signed_at,
        ip_address=signature.ip_address,
        created_at=signature.created_at,
        updated_at=signature.updated_at
    )


# ==================== 验收报告 ====================

def generate_report_no(db: Session, report_type: str) -> str:
    """生成报告编号：RPT-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    prefix = f"RPT-{today}-"
    max_report = (
        db.query(AcceptanceReport)
        .filter(AcceptanceReport.report_no.like(f"{prefix}%"))
        .order_by(desc(AcceptanceReport.report_no))
        .first()
    )
    if max_report:
        seq = int(max_report.report_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


@router.post("/acceptance-orders/{order_id}/report", response_model=AcceptanceReportResponse, status_code=status.HTTP_201_CREATED)
def generate_acceptance_report(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    report_in: AcceptanceReportGenerateRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    生成验收报告
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    if order.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="只有已完成的验收单才能生成报告")
    
    # 检查是否已有相同类型的报告
    existing_report = db.query(AcceptanceReport).filter(
        AcceptanceReport.order_id == order_id,
        AcceptanceReport.report_type == report_in.report_type
    ).order_by(desc(AcceptanceReport.version)).first()
    
    version = 1
    if existing_report:
        version = existing_report.version + 1
    
    report_no = generate_report_no(db, report_in.report_type)
    
    # 生成报告内容（简化版，实际应使用模板引擎）
    project_name = order.project.project_name if getattr(order, "project", None) else None
    machine_name = order.machine.machine_name if getattr(order, "machine", None) else None
    qa_signer_name = None
    if order.qa_signer_id:
        qa_user = db.query(User).filter(User.id == order.qa_signer_id).first()
        if qa_user:
            qa_signer_name = qa_user.real_name or qa_user.username
    total_issues = (
        db.query(func.count(AcceptanceIssue.id))
        .filter(AcceptanceIssue.order_id == order_id)
        .scalar()
    ) or 0
    resolved_issues = (
        db.query(func.count(AcceptanceIssue.id))
        .filter(
            AcceptanceIssue.order_id == order_id,
            AcceptanceIssue.status.in_(["RESOLVED", "CLOSED"]),
        )
        .scalar()
    ) or 0
    order_completed_at = order.actual_end_date

    report_content = f"""
验收报告

报告编号：{report_no}
验收单号：{order.order_no}
报告类型：{report_in.report_type}
版本号：{version}

项目信息：
- 项目名称：{project_name or 'N/A'}
- 机台名称：{machine_name or 'N/A'}

验收结果：
- 验收状态：{order.status}
- 验收日期：{order_completed_at.strftime('%Y-%m-%d') if order_completed_at else 'N/A'}
- 合格率：{order.pass_rate or 0}%

检查项统计：
- 总检查项：{order.total_items or 0}
- 合格项：{order.passed_items or 0}
- 不合格项：{order.failed_items or 0}

问题统计：
- 总问题数：{total_issues}
- 已解决：{resolved_issues}
- 待解决：{total_issues - resolved_issues}

签字信息：
- 质检签字：{qa_signer_name or 'N/A'}
- 客户签字：{order.customer_signer or 'N/A'}

报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
生成人：{current_user.real_name or current_user.username}
"""
    
    # 生成报告文件
    report_dir = os.path.join(settings.UPLOAD_DIR, "reports")
    os.makedirs(report_dir, exist_ok=True)
    file_rel_path = f"reports/{report_no}.txt"
    file_full_path = os.path.join(settings.UPLOAD_DIR, file_rel_path)
    file_bytes = report_content.encode("utf-8")
    with open(file_full_path, "wb") as f:
        f.write(file_bytes)
    file_size = len(file_bytes)
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    
    report = AcceptanceReport(
        order_id=order_id,
        report_no=report_no,
        report_type=report_in.report_type,
        version=version,
        report_content=report_content,
        file_path=file_rel_path,
        file_size=file_size,
        file_hash=file_hash,
        generated_at=datetime.now(),
        generated_by=current_user.id
    )
    
    db.add(report)
    
    # 更新验收单的报告文件路径（如果有最新报告）
    if not order.report_file_path or report_in.report_type == "FINAL":
        order.report_file_path = file_rel_path
    
    db.commit()
    db.refresh(report)
    
    return AcceptanceReportResponse(
        id=report.id,
        order_id=report.order_id,
        report_no=report.report_no,
        report_type=report.report_type,
        version=report.version,
        report_content=report.report_content,
        file_path=report.file_path,
        file_size=report.file_size,
        file_hash=report.file_hash,
        generated_at=report.generated_at,
        generated_by=report.generated_by,
        generated_by_name=current_user.real_name or current_user.username,
        created_at=report.created_at,
        updated_at=report.updated_at
    )


@router.get("/acceptance-reports/{report_id}/download", response_class=FileResponse)
def download_acceptance_report(
    report_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    下载验收报告
    """
    report = db.query(AcceptanceReport).filter(AcceptanceReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="验收报告不存在")
    
    if not report.file_path:
        raise HTTPException(status_code=404, detail="报告文件不存在")
    
    file_path = os.path.join(settings.UPLOAD_DIR, report.file_path)
    
    if not os.path.exists(file_path):
        # 如果文件不存在，返回报告内容作为文本
        content = report.report_content or "报告内容为空"
        return Response(
            content=content.encode('utf-8'),
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={report.report_no}.txt"
            }
        )
    
    filename = os.path.basename(file_path)
    media_type = "text/plain" if filename.endswith(".txt") else "application/octet-stream"
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )

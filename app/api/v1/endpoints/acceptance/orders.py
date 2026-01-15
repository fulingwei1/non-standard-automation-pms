# -*- coding: utf-8 -*-
"""
验收单管理端点

包含：验收单CRUD、检查项结果更新、验收流程控制
"""

import logging
from typing import Any, List, Optional
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

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
    AcceptanceOrderCreate, AcceptanceOrderUpdate, AcceptanceOrderStart, AcceptanceOrderComplete,
    AcceptanceOrderResponse, AcceptanceOrderListResponse,
    CheckItemResultUpdate, CheckItemResultResponse
)
from app.schemas.common import ResponseModel, PaginatedResponse

from .utils import (
    validate_acceptance_rules,
    validate_completion_rules,
    validate_edit_rules,
    generate_order_no
)

router = APIRouter()


@router.get("/acceptance-orders", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_acceptance_orders(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（验收单号）"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    acceptance_type: Optional[str] = Query(None, description="验收类型筛选"),
    order_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
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

    if order_status:
        query = query.filter(AcceptanceOrder.status == order_status)

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
            is_officially_completed=order.is_officially_completed or False,
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
        conditions=order.conditions,
        customer_signed_file_path=order.customer_signed_file_path,
        is_officially_completed=order.is_officially_completed or False,
        officially_completed_at=order.officially_completed_at,
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
    machine = None
    machine_no = None
    if order_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == order_in.machine_id).first()
        if not machine or machine.project_id != order_in.project_id:
            raise HTTPException(status_code=400, detail="机台不存在或不属于该项目")
        machine_no = machine.machine_no
    elif order_in.acceptance_type != "FINAL":
        # FAT和SAT验收必须提供设备
        raise HTTPException(status_code=400, detail=f"{order_in.acceptance_type}验收单必须指定设备")

    # 验证验收约束规则（AR001, AR002, AR003）
    validate_acceptance_rules(
        db=db,
        acceptance_type=order_in.acceptance_type,
        project_id=order_in.project_id,
        machine_id=order_in.machine_id
    )

    # 验证模板（如果提供）
    template = None
    if order_in.template_id:
        template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == order_in.template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="验收模板不存在")
        if template.acceptance_type != order_in.acceptance_type:
            raise HTTPException(status_code=400, detail="模板类型与验收类型不匹配")

    # 生成验收单号（符合设计规范）
    order_no = generate_order_no(
        db=db,
        acceptance_type=order_in.acceptance_type,
        project_code=project.project_code,
        machine_no=machine_no
    )

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


@router.put("/acceptance-orders/{order_id}", response_model=AcceptanceOrderResponse, status_code=status.HTTP_200_OK)
def update_acceptance_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    order_in: AcceptanceOrderUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新验收单

    只能更新草稿状态的验收单，且客户签字后不可修改（AR006）
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    # AR006: 客户签字后验收单不可修改
    validate_edit_rules(db, order_id)

    # 只能更新草稿状态的验收单
    if order.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能更新草稿状态的验收单")

    # 更新字段
    update_data = order_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)

    db.add(order)
    db.commit()
    db.refresh(order)

    return read_acceptance_order(order_id, db, current_user)


@router.post("/acceptance-orders/{order_id}/submit", response_model=AcceptanceOrderResponse, status_code=status.HTTP_200_OK)
def submit_acceptance_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交验收单（草稿→待验收）
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    # AR006: 客户签字后验收单不可修改
    validate_edit_rules(db, order_id)

    if order.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能提交草稿状态的验收单")

    if order.total_items == 0:
        raise HTTPException(status_code=400, detail="验收单没有检查项，无法提交")

    order.status = "PENDING"

    db.add(order)
    db.commit()
    db.refresh(order)

    return read_acceptance_order(order_id, db, current_user)


@router.put("/acceptance-orders/{order_id}/start", response_model=AcceptanceOrderResponse, status_code=status.HTTP_200_OK)
def start_acceptance(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    start_in: AcceptanceOrderStart,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    开始验收（待验收→验收中）
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    if order.status not in ["DRAFT", "PENDING"]:
        raise HTTPException(status_code=400, detail="只能开始草稿或待验收状态的验收单")

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


@router.delete("/acceptance-orders/{order_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_acceptance_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除验收单（仅草稿状态）
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    if order.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能删除草稿状态的验收单")

    # AR006: 客户签字后验收单不可删除
    validate_edit_rules(db, order_id)

    # 删除关联的检查项
    db.query(AcceptanceOrderItem).filter(AcceptanceOrderItem.order_id == order_id).delete()

    # 删除关联的问题
    issues = db.query(AcceptanceIssue).filter(AcceptanceIssue.order_id == order_id).all()
    for issue in issues:
        # 删除问题的跟进记录
        db.query(IssueFollowUp).filter(IssueFollowUp.issue_id == issue.id).delete()
    db.query(AcceptanceIssue).filter(AcceptanceIssue.order_id == order_id).delete()

    # 删除关联的签字记录
    db.query(AcceptanceSignature).filter(AcceptanceSignature.order_id == order_id).delete()

    # 删除关联的报告
    db.query(AcceptanceReport).filter(AcceptanceReport.order_id == order_id).delete()

    # 删除验收单
    db.delete(order)
    db.commit()

    return ResponseModel(message="验收单已删除")


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

    # 更新验收单统计（支持有条件通过的权重计算）
    items = db.query(AcceptanceOrderItem).filter(AcceptanceOrderItem.order_id == order.id).all()
    passed = len([i for i in items if i.result_status == "PASSED"])
    failed = len([i for i in items if i.result_status == "FAILED"])
    na = len([i for i in items if i.result_status == "NA"])
    conditional = len([i for i in items if i.result_status == "CONDITIONAL"])
    # 不适用(NA)的项不计入总数
    total = len([i for i in items if i.result_status != "PENDING" and i.result_status != "NA"])

    order.passed_items = passed
    order.failed_items = failed
    order.na_items = na
    order.total_items = len(items)

    # 通过率计算：通过数 + 有条件通过数*0.8
    if total > 0:
        # 有条件通过按0.8权重计算
        effective_passed = passed + conditional * Decimal("0.8")
        order.pass_rate = Decimal(str((effective_passed / total) * 100)).quantize(Decimal("0.01"))
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
    from app.services.acceptance_completion_service import (
        validate_required_check_items,
        update_acceptance_order_status,
        trigger_invoice_on_acceptance,
        handle_acceptance_status_transition,
        handle_progress_integration,
        check_auto_stage_transition_after_acceptance,
        trigger_warranty_period,
        trigger_bonus_calculation
    )

    logger = logging.getLogger(__name__)

    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    if order.status != "IN_PROGRESS":
        raise HTTPException(status_code=400, detail="只能完成进行中状态的验收单")

    # AR005: 检查是否所有必检项都已检查
    validate_required_check_items(db, order_id)

    # AR004: 检查是否存在未闭环的阻塞问题
    validate_completion_rules(db, order_id)

    # 更新验收单状态
    update_acceptance_order_status(
        db,
        order,
        complete_in.overall_result,
        complete_in.conclusion,
        complete_in.conditions
    )

    # Issue 7.4: 如果验收通过，检查是否有绑定的收款计划，自动触发开票
    if auto_trigger_invoice and complete_in.overall_result == "PASSED":
        trigger_invoice_on_acceptance(db, order_id, auto_trigger_invoice)

    # Sprint 2.2: 验收管理状态联动（FAT/SAT）
    handle_acceptance_status_transition(db, order, complete_in.overall_result)

    # 验收联动：处理验收结果对进度跟踪的影响
    handle_progress_integration(db, order, complete_in.overall_result)

    # Issue 1.2: FAT/SAT验收通过后自动触发阶段流转检查
    check_auto_stage_transition_after_acceptance(db, order, complete_in.overall_result)

    # AR007: 如果终验收通过，自动触发质保期
    trigger_warranty_period(db, order, complete_in.overall_result)

    # 如果验收通过，自动触发奖金计算
    trigger_bonus_calculation(db, order, complete_in.overall_result)

    db.commit()
    db.refresh(order)

    return read_acceptance_order(order_id, db, current_user)

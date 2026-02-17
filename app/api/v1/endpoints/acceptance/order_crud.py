# -*- coding: utf-8 -*-
"""
验收单管理 - 基础CRUD操作

包含验收单列表、创建、详情、更新、删除
"""

import logging
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.acceptance import (
    AcceptanceIssue,
    AcceptanceOrder,
    AcceptanceOrderItem,
    AcceptanceReport,
    AcceptanceSignature,
    AcceptanceTemplate,
    IssueFollowUp,
    TemplateCategory,
    TemplateCheckItem,
)
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.acceptance import (
    AcceptanceOrderCreate,
    AcceptanceOrderListResponse,
    AcceptanceOrderResponse,
    AcceptanceOrderUpdate,
)
from app.schemas.common import PaginatedResponse, ResponseModel

from app.services.data_scope.config import DataScopeConfig
from app.services.data_scope_service import DataScopeService

from .utils import generate_order_no, validate_acceptance_rules, validate_edit_rules
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

router = APIRouter()
logger = logging.getLogger(__name__)

# 验收单数据权限配置
ACCEPTANCE_DATA_SCOPE_CONFIG = DataScopeConfig(
    owner_field="created_by",
    project_field="project_id",
)


@router.get("/acceptance-orders", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_acceptance_orders(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（验收单号）"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    acceptance_type: Optional[str] = Query(None, description="验收类型筛选"),
    order_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收单列表（按数据权限过滤）
    """
    query = db.query(AcceptanceOrder)

    # 应用数据权限过滤
    query = DataScopeService.filter_by_scope(
        db, query, AcceptanceOrder, current_user, ACCEPTANCE_DATA_SCOPE_CONFIG
    )

    query = apply_keyword_filter(query, AcceptanceOrder, keyword, ["order_no"])

    if project_id:
        query = query.filter(AcceptanceOrder.project_id == project_id)

    if machine_id:
        query = query.filter(AcceptanceOrder.machine_id == machine_id)

    if acceptance_type:
        query = query.filter(AcceptanceOrder.acceptance_type == acceptance_type)

    if order_status:
        query = query.filter(AcceptanceOrder.status == order_status)

    total = query.count()
    orders = apply_pagination(query.order_by(desc(AcceptanceOrder.created_at)), pagination.offset, pagination.limit).all()

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

    return pagination.to_response(items, total)


@router.get("/acceptance-orders/{order_id}", response_model=AcceptanceOrderResponse, status_code=status.HTTP_200_OK)
def read_acceptance_order(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收单详情
    """
    from decimal import Decimal

    order = get_or_404(db, AcceptanceOrder, order_id, "验收单不存在")

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
    order = get_or_404(db, AcceptanceOrder, order_id, "验收单不存在")

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
    order = get_or_404(db, AcceptanceOrder, order_id, "验收单不存在")

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

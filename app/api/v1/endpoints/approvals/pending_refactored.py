# -*- coding: utf-8 -*-
"""
待办查询 API（重构版）
使用统一响应格式
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core.schemas import list_response, paginated_response, success_response
from app.models.approval import ApprovalCarbonCopy, ApprovalInstance, ApprovalTask
from app.schemas.approval.instance import ApprovalInstanceListResponse, ApprovalInstanceResponse
from app.common.pagination import PaginationParams, get_pagination_query
from app.schemas.approval.task import (
    ApprovalTaskListResponse,
    ApprovalTaskResponse,
    CarbonCopyListResponse,
    CarbonCopyResponse,
)

router = APIRouter()


@router.get("/mine")
def get_my_pending_tasks(
    pagination: PaginationParams = Depends(get_pagination_query),
    urgency: Optional[str] = None,
    template_id: Optional[int] = None,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    获取待我审批的任务

    返回当前用户待处理的所有审批任务
    """
    query = (
        db.query(ApprovalTask)
        .join(ApprovalInstance)
        .filter(
            ApprovalTask.assignee_id == current_user.id,
            ApprovalTask.status == "PENDING",
        )
    )

    if urgency:
        query = query.filter(ApprovalInstance.urgency == urgency)
    if template_id:
        query = query.filter(ApprovalInstance.template_id == template_id)

    total = query.count()
    # Safety check: if count() returns None (SQLite connection issue), default to 0
    if total is None:
        total = 0

    tasks = (
        query.order_by(ApprovalTask.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )

    # 转换响应
    items = []
    for task in tasks:
        item = ApprovalTaskResponse.model_validate(task)
        if task.instance:
            item.instance_title = task.instance.title
            item.instance_no = task.instance.instance_no
            item.instance_urgency = task.instance.urgency
        if task.node:
            item.node_name = task.node.node_name
        items.append(item)

    # 使用统一响应格式（paginated_response 内部会计算 pages）
    return paginated_response(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.get("/initiated")
def get_my_initiated(
    pagination: PaginationParams = Depends(get_pagination_query),
    status: Optional[str] = None,
    template_id: Optional[int] = None,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    获取我发起的审批

    返回当前用户发起的所有审批实例
    """
    query = db.query(ApprovalInstance).filter(
        ApprovalInstance.initiator_id == current_user.id,
    )

    if status:
        query = query.filter(ApprovalInstance.status == status)
    if template_id:
        query = query.filter(ApprovalInstance.template_id == template_id)

    total = query.count()
    items = (
        query.order_by(ApprovalInstance.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )

    pages = pagination.pages_for_total(total)

    # 使用统一响应格式
    return paginated_response(
        items=[ApprovalInstanceResponse.model_validate(i) for i in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.get("/cc")
def get_my_cc(
    pagination: PaginationParams = Depends(get_pagination_query),
    is_read: Optional[bool] = None,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    获取抄送我的

    返回抄送给当前用户的所有审批记录
    """
    query = db.query(ApprovalCarbonCopy).filter(
        ApprovalCarbonCopy.cc_user_id == current_user.id,
    )

    if is_read is not None:
        query = query.filter(ApprovalCarbonCopy.is_read == is_read)

    total = query.count()
    records = (
        query.order_by(ApprovalCarbonCopy.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )

    # 转换响应
    items = []
    for cc in records:
        item = CarbonCopyResponse.model_validate(cc)
        if cc.instance:
            item.instance_title = cc.instance.title
            item.instance_no = cc.instance.instance_no
            item.initiator_name = cc.instance.initiator_name
        items.append(item)

    pages = pagination.pages_for_total(total)

    # 使用统一响应格式
    return paginated_response(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.post("/cc/{cc_id}/read")
def mark_cc_as_read(
    cc_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """标记抄送为已读"""
    from app.services.approval_engine import ApprovalEngineService

    engine = ApprovalEngineService(db)
    success = engine.mark_cc_as_read(cc_id, current_user.id)

    if success:
        # 使用统一响应格式
        return success_response(
            data=None,
            message="标记成功"
        )
    else:
        from fastapi import Depends, HTTPException
        raise HTTPException(status_code=404, detail="记录不存在或无权操作")


@router.get("/processed")
def get_my_processed(
    pagination: PaginationParams = Depends(get_pagination_query),
    action: Optional[str] = None,
    template_id: Optional[int] = None,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    获取我已处理的审批

    返回当前用户已处理的所有审批任务
    """
    query = (
        db.query(ApprovalTask)
        .join(ApprovalInstance)
        .filter(
            ApprovalTask.assignee_id == current_user.id,
            ApprovalTask.status == "COMPLETED",
        )
    )

    if action:
        query = query.filter(ApprovalTask.action == action)
    if template_id:
        query = query.filter(ApprovalInstance.template_id == template_id)

    total = query.count()
    tasks = (
        query.order_by(ApprovalTask.completed_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )

    # 转换响应
    items = []
    for task in tasks:
        item = ApprovalTaskResponse.model_validate(task)
        if task.instance:
            item.instance_title = task.instance.title
            item.instance_no = task.instance.instance_no
            item.instance_urgency = task.instance.urgency
        if task.node:
            item.node_name = task.node.node_name
        items.append(item)

    pages = pagination.pages_for_total(total)

    # 使用统一响应格式
    return paginated_response(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.get("/counts")
def get_pending_counts(
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    获取待办数量统计

    返回待我审批、我发起的、抄送我的各项数量
    """
    # 待我审批数量
    pending_count = (
        db.query(ApprovalTask)
        .filter(
            ApprovalTask.assignee_id == current_user.id,
            ApprovalTask.status == "PENDING",
        )
        .count()
    )

    # 我发起的进行中数量
    initiated_pending_count = (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.initiator_id == current_user.id,
            ApprovalInstance.status == "PENDING",
        )
        .count()
    )

    # 未读抄送数量
    unread_cc_count = (
        db.query(ApprovalCarbonCopy)
        .filter(
            ApprovalCarbonCopy.cc_user_id == current_user.id,
            ApprovalCarbonCopy.is_read == False,
        )
        .count()
    )

    # 紧急待办数量
    urgent_count = (
        db.query(ApprovalTask)
        .join(ApprovalInstance)
        .filter(
            ApprovalTask.assignee_id == current_user.id,
            ApprovalTask.status == "PENDING",
            ApprovalInstance.urgency.in_(["URGENT", "CRITICAL"]),
        )
        .count()
    )

    # 使用统一响应格式
    return success_response(
        data={
            "pending": pending_count,
            "initiated_pending": initiated_pending_count,
            "unread_cc": unread_cc_count,
            "urgent": urgent_count,
            "total": pending_count + unread_cc_count,
        },
        message="获取待办数量统计成功"
    )

# -*- coding: utf-8 -*-
"""
待办查询 API
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.approval import ApprovalCarbonCopy, ApprovalInstance, ApprovalTask
from app.schemas.approval.instance import ApprovalInstanceListResponse, ApprovalInstanceResponse
from app.schemas.approval.task import (
    ApprovalTaskListResponse,
    ApprovalTaskResponse,
    CarbonCopyListResponse,
    CarbonCopyResponse,
)

router = APIRouter()


@router.get("/mine", response_model=ApprovalTaskListResponse)
def get_my_pending_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
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
    tasks = (
        query.order_by(ApprovalTask.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
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

    return ApprovalTaskListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


@router.get("/initiated", response_model=ApprovalInstanceListResponse)
def get_my_initiated(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
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
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return ApprovalInstanceListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ApprovalInstanceResponse.model_validate(i) for i in items],
    )


@router.get("/cc", response_model=CarbonCopyListResponse)
def get_my_cc(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
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
        .offset((page - 1) * page_size)
        .limit(page_size)
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

    return CarbonCopyListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
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
        return {"message": "标记成功"}
    else:
        return {"message": "记录不存在或无权操作"}


@router.get("/processed", response_model=ApprovalTaskListResponse)
def get_my_processed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
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
        .offset((page - 1) * page_size)
        .limit(page_size)
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

    return ApprovalTaskListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
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

    return {
        "pending": pending_count,
        "initiated_pending": initiated_pending_count,
        "unread_cc": unread_cc_count,
        "urgent": urgent_count,
        "total": pending_count + unread_cc_count,
    }

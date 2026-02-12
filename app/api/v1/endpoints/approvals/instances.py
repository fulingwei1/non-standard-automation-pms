# -*- coding: utf-8 -*-
"""
审批实例 API
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.approval import ApprovalActionLog, ApprovalInstance, ApprovalTask
from app.schemas.approval.instance import (
    ApprovalInstanceCreate,
    ApprovalInstanceDetail,
    ApprovalInstanceListResponse,
    ApprovalInstanceResponse,
    ApprovalInstanceSaveDraft,
    ApprovalLogBrief,
    ApprovalTaskBrief,
)
from app.services.approval_engine import ApprovalEngineService
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter

router = APIRouter()


@router.post("/submit", response_model=ApprovalInstanceResponse)
def submit_approval(
    data: ApprovalInstanceCreate,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    提交审批

    根据模板编码和表单数据提交审批申请，系统会自动：
    1. 根据条件路由选择审批流程
    2. 创建第一个节点的审批任务
    3. 通知审批人
    """
    engine = ApprovalEngineService(db)

    try:
        instance = engine.submit(
            template_code=data.template_code,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            form_data=data.form_data or {},
            initiator_id=current_user.id,
            title=data.title,
            summary=data.summary,
            urgency=data.urgency,
            cc_user_ids=data.cc_user_ids,
        )
        return ApprovalInstanceResponse.model_validate(instance)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/draft", response_model=ApprovalInstanceResponse)
def save_draft(
    data: ApprovalInstanceSaveDraft,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """保存审批草稿"""
    engine = ApprovalEngineService(db)

    try:
        instance = engine.save_draft(
            template_code=data.template_code,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            form_data=data.form_data or {},
            initiator_id=current_user.id,
            title=data.title,
        )
        return ApprovalInstanceResponse.model_validate(instance)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=ApprovalInstanceListResponse)
def list_instances(
    pagination: PaginationParams = Depends(get_pagination_query),
    status: Optional[str] = None,
    template_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(deps.get_db),
):
    """获取审批实例列表"""
    query = db.query(ApprovalInstance)

    if status:
        query = query.filter(ApprovalInstance.status == status)
    if template_id:
        query = query.filter(ApprovalInstance.template_id == template_id)
    if entity_type:
        query = query.filter(ApprovalInstance.entity_type == entity_type)
    if entity_id:
        query = query.filter(ApprovalInstance.entity_id == entity_id)
    query = apply_keyword_filter(query, ApprovalInstance, keyword, ["title", "instance_no"])

    total = query.count()
    items = (
        query.order_by(ApprovalInstance.id.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )

    return ApprovalInstanceListResponse(
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        items=[ApprovalInstanceResponse.model_validate(i) for i in items],
    )


@router.get("/{instance_id}", response_model=ApprovalInstanceDetail)
def get_instance(
    instance_id: int,
    db: Session = Depends(deps.get_db),
):
    """获取审批实例详情"""
    instance = db.query(ApprovalInstance).filter(ApprovalInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="审批实例不存在")

    # 获取任务列表
    tasks = (
        db.query(ApprovalTask)
        .filter(ApprovalTask.instance_id == instance_id)
        .order_by(ApprovalTask.created_at)
        .all()
    )

    # 获取操作日志
    logs = (
        db.query(ApprovalActionLog)
        .filter(ApprovalActionLog.instance_id == instance_id)
        .order_by(ApprovalActionLog.action_at.desc())
        .all()
    )

    result = ApprovalInstanceDetail.model_validate(instance)

    # 获取模板名称
    if instance.template:
        result.template_name = instance.template.template_name

    # 获取当前节点名称
    if instance.current_node_id:
        from app.models.approval import ApprovalNodeDefinition
        current_node = db.query(ApprovalNodeDefinition).filter(
            ApprovalNodeDefinition.id == instance.current_node_id
        ).first()
        if current_node:
            result.current_node_name = current_node.node_name

    # 转换任务列表
    result.tasks = []
    for task in tasks:
        task_brief = ApprovalTaskBrief(
            id=task.id,
            node_id=task.node_id,
            node_name=task.node.node_name if task.node else None,
            assignee_id=task.assignee_id,
            assignee_name=task.assignee_name,
            status=task.status,
            action=task.action,
            comment=task.comment,
            completed_at=task.completed_at,
            created_at=task.created_at,
        )
        result.tasks.append(task_brief)

    # 转换日志列表
    result.logs = [
        ApprovalLogBrief(
            id=log.id,
            operator_id=log.operator_id,
            operator_name=log.operator_name,
            action=log.action,
            comment=log.comment,
            action_at=log.action_at,
        )
        for log in logs
    ]

    return result


@router.post("/{instance_id}/withdraw")
def withdraw_instance(
    instance_id: int,
    comment: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    撤回审批

    只有发起人可以撤回，且只能撤回进行中的审批
    """
    engine = ApprovalEngineService(db)

    try:
        instance = engine.withdraw(
            instance_id=instance_id,
            initiator_id=current_user.id,
            comment=comment,
        )
        return {"message": "撤回成功", "instance_id": instance.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{instance_id}/terminate")
def terminate_instance(
    instance_id: int,
    comment: str,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    终止审批（管理员操作）
    """
    engine = ApprovalEngineService(db)

    try:
        instance = engine.terminate(
            instance_id=instance_id,
            operator_id=current_user.id,
            comment=comment,
        )
        return {"message": "终止成功", "instance_id": instance.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/by-entity/{entity_type}/{entity_id}", response_model=ApprovalInstanceListResponse)
def get_instances_by_entity(
    entity_type: str,
    entity_id: int,
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
):
    """根据业务实体获取审批实例列表"""
    query = db.query(ApprovalInstance).filter(
        ApprovalInstance.entity_type == entity_type,
        ApprovalInstance.entity_id == entity_id,
    )

    total = query.count()
    items = (
        query.order_by(ApprovalInstance.id.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )

    return ApprovalInstanceListResponse(
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        items=[ApprovalInstanceResponse.model_validate(i) for i in items],
    )

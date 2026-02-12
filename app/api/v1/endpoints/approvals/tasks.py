# -*- coding: utf-8 -*-
"""
审批任务操作 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.approval import ApprovalComment, ApprovalTask
from app.schemas.approval.task import (
    AddApproverRequest,
    AddCCRequest,
    ApproveRequest,
    ApprovalTaskResponse,
    CommentRequest,
    CommentResponse,
    RejectRequest,
    RemindRequest,
    ReturnRequest,
    TransferRequest,
)
from app.services.approval_engine import ApprovalEngineService

router = APIRouter()


@router.get("/{task_id}", response_model=ApprovalTaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(deps.get_db),
):
    """获取审批任务详情"""
    task = db.query(ApprovalTask).filter(ApprovalTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    result = ApprovalTaskResponse.model_validate(task)

    # 添加关联信息
    if task.instance:
        result.instance_title = task.instance.title
        result.instance_no = task.instance.instance_no
        result.instance_urgency = task.instance.urgency
    if task.node:
        result.node_name = task.node.node_name

    return result


@router.post("/{task_id}/approve")
def approve_task(
    task_id: int,
    data: ApproveRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    审批通过

    对于会签节点，需要所有审批人都通过才能流转
    对于或签节点，任一审批人通过即可流转
    """
    engine = ApprovalEngineService(db)

    try:
        task = engine.approve(
            task_id=task_id,
            approver_id=current_user.id,
            comment=data.comment,
            attachments=data.attachments,
            eval_data=data.eval_data,
        )
        return {
            "message": "审批通过",
            "task_id": task.id,
            "instance_status": task.instance.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/reject")
def reject_task(
    task_id: int,
    data: RejectRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    审批驳回

    可以选择驳回到：
    - START: 发起人（审批结束）
    - PREV: 上一节点
    - 指定节点ID
    """
    engine = ApprovalEngineService(db)

    try:
        task = engine.reject(
            task_id=task_id,
            approver_id=current_user.id,
            comment=data.comment,
            reject_to=data.reject_to,
            attachments=data.attachments,
        )
        return {
            "message": "审批驳回",
            "task_id": task.id,
            "instance_status": task.instance.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/return")
def return_task(
    task_id: int,
    data: ReturnRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """退回到指定节点"""
    engine = ApprovalEngineService(db)

    try:
        task = engine.return_to(
            task_id=task_id,
            approver_id=current_user.id,
            target_node_id=data.target_node_id,
            comment=data.comment,
        )
        return {
            "message": "退回成功",
            "task_id": task.id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/transfer")
def transfer_task(
    task_id: int,
    data: TransferRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    转审

    将当前任务转给其他人处理
    """
    engine = ApprovalEngineService(db)

    try:
        new_task = engine.transfer(
            task_id=task_id,
            from_user_id=current_user.id,
            to_user_id=data.to_user_id,
            comment=data.comment,
        )
        return {
            "message": "转审成功",
            "new_task_id": new_task.id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/add-approver")
def add_approver(
    task_id: int,
    data: AddApproverRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    加签

    - BEFORE: 前加签，加签人审批后再轮到当前审批人
    - AFTER: 后加签，当前审批人审批后再轮到加签人
    """
    engine = ApprovalEngineService(db)

    try:
        new_tasks = engine.add_approver(
            task_id=task_id,
            operator_id=current_user.id,
            approver_ids=data.approver_ids,
            position=data.position,
            comment=data.comment,
        )
        return {
            "message": "加签成功",
            "new_task_ids": [t.id for t in new_tasks],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/remind")
def remind_task(
    task_id: int,
    data: RemindRequest = None,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    催办

    向审批人发送催办通知
    """
    engine = ApprovalEngineService(db)

    try:
        engine.remind(
            task_id=task_id,
            reminder_id=current_user.id,
        )
        return {"message": "催办成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 抄送 ====================

@router.post("/instances/{instance_id}/add-cc")
def add_cc(
    instance_id: int,
    data: AddCCRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """加抄送"""
    engine = ApprovalEngineService(db)

    try:
        records = engine.add_cc(
            instance_id=instance_id,
            operator_id=current_user.id,
            cc_user_ids=data.cc_user_ids,
        )
        return {
            "message": "加抄送成功",
            "cc_count": len(records),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 评论 ====================

@router.post("/instances/{instance_id}/comments", response_model=CommentResponse)
def add_comment(
    instance_id: int,
    data: CommentRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """添加评论"""
    engine = ApprovalEngineService(db)

    try:
        comment = engine.add_comment(
            instance_id=instance_id,
            user_id=current_user.id,
            content=data.content,
            parent_id=data.parent_id,
            reply_to_user_id=data.reply_to_user_id,
            mentioned_user_ids=data.mentioned_user_ids,
            attachments=data.attachments,
        )
        return CommentResponse.model_validate(comment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/instances/{instance_id}/comments", response_model=list[CommentResponse])
def list_comments(
    instance_id: int,
    db: Session = Depends(deps.get_db),
):
    """获取评论列表"""
    comments = (
        db.query(ApprovalComment)
        .filter(
            ApprovalComment.instance_id == instance_id,
            not ApprovalComment.is_deleted,
        )
        .order_by(ApprovalComment.created_at)
        .all()
    )

    return [CommentResponse.model_validate(c) for c in comments]


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """删除评论（软删除）"""
    from datetime import datetime

    comment = db.query(ApprovalComment).filter(ApprovalComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此评论")

    comment.is_deleted = True
    comment.deleted_at = datetime.now()
    comment.deleted_by = current_user.id
    db.commit()

    return {"message": "删除成功"}

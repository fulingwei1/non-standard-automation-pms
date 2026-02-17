# -*- coding: utf-8 -*-
"""
ECN审批工作流 API

使用统一审批引擎实现ECN审批流程。
ECN(工程变更通知)在完成评估后需要提交审批以确认变更。
"""

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.ecn import Ecn, EcnEvaluation
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.approval_engine import ApprovalEngineService
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ecns/approval", tags=["ECN审批工作流"])


# ==================== 请求模型 ====================


class EcnSubmitApprovalRequest(BaseModel):
    """ECN提交审批请求"""

    ecn_ids: List[int] = Field(..., description="ECN ID列表")
    urgency: str = Field("NORMAL", description="紧急程度: LOW/NORMAL/HIGH/URGENT")
    comment: Optional[str] = Field(None, description="提交备注")


class ApprovalActionRequest(BaseModel):
    """审批操作请求"""

    task_id: int = Field(..., description="审批任务ID")
    action: str = Field(..., description="操作类型: approve/reject")
    comment: Optional[str] = Field(None, description="审批意见")


class BatchApprovalRequest(BaseModel):
    """批量审批请求"""

    task_ids: List[int] = Field(..., description="审批任务ID列表")
    action: str = Field(..., description="操作类型: approve/reject")
    comment: Optional[str] = Field(None, description="审批意见")


class WithdrawApprovalRequest(BaseModel):
    """撤回审批请求"""

    ecn_id: int = Field(..., description="ECN ID")
    reason: Optional[str] = Field(None, description="撤回原因")


# ==================== API 端点 ====================


@router.post("/submit", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def submit_for_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: EcnSubmitApprovalRequest,
    current_user: User = Depends(security.require_permission("ecn:create")),
) -> Any:
    """
    提交ECN审批

    将已完成评估的ECN提交到审批流程。
    适用于：
    - ECN评估完成后提交审批
    - 被驳回的ECN修改后重新提交
    """
    engine = ApprovalEngineService(db)
    results = []
    errors = []

    for ecn_id in request.ecn_ids:
        try:
            ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
            if not ecn:
                errors.append({"ecn_id": ecn_id, "error": "ECN不存在"})
                continue

            # 检查状态是否允许提交审批
            if ecn.status not in ("DRAFT", "EVALUATING", "EVALUATED", "REJECTED"):
                errors.append(
                    {
                        "ecn_id": ecn_id,
                        "error": f"当前状态({ecn.status})不允许提交审批",
                    }
                )
                continue

            # 检查是否有未完成的评估
            pending_evals = (
                db.query(EcnEvaluation)
                .filter(
                    EcnEvaluation.ecn_id == ecn_id,
                    EcnEvaluation.status == "PENDING",
                )
                .count()
            )
            if pending_evals > 0:
                errors.append(
                    {
                        "ecn_id": ecn_id,
                        "error": f"还有 {pending_evals} 个评估未完成",
                    }
                )
                continue

            # 构建表单数据
            form_data = {
                "ecn_id": ecn.id,
                "ecn_no": ecn.ecn_no,
                "ecn_title": ecn.ecn_title,
                "ecn_type": ecn.ecn_type,
                "project_id": ecn.project_id,
                "cost_impact": float(ecn.cost_impact) if ecn.cost_impact else 0,
                "schedule_impact_days": ecn.schedule_impact_days or 0,
                "change_reason": ecn.change_reason,
                "change_description": ecn.change_description,
            }

            # 提交到审批引擎
            instance = engine.submit(
                template_code="ECN_STANDARD",
                entity_type="ECN",
                entity_id=ecn_id,
                form_data=form_data,
                initiator_id=current_user.id,
                urgency=request.urgency,
            )

            # 更新ECN状态
            ecn.status = "APPROVING"
            ecn.current_step = "APPROVAL"

            results.append(
                {
                    "ecn_id": ecn_id,
                    "ecn_no": ecn.ecn_no,
                    "instance_id": instance.id,
                    "status": "submitted",
                }
            )
        except Exception as e:
            logger.exception(f"ECN {ecn_id} 提交审批失败")
            errors.append({"ecn_id": ecn_id, "error": str(e)})

    db.commit()

    return ResponseModel(
        code=200,
        message=f"提交完成: 成功 {len(results)} 个, 失败 {len(errors)} 个",
        data={"success": results, "errors": errors},
    )


@router.get("/pending", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_pending_approval_tasks(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    ecn_type: Optional[str] = Query(None, description="ECN类型筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.require_permission("ecn:read")),
) -> Any:
    """
    获取待审批的ECN列表

    返回当前用户待审批的ECN任务。
    """
    engine = ApprovalEngineService(db)
    tasks = engine.get_pending_tasks(user_id=current_user.id, entity_type="ECN")

    # 筛选
    filtered_tasks = []
    for task in tasks:
        ecn = db.query(Ecn).filter(Ecn.id == task.instance.entity_id).first()
        if not ecn:
            continue

        if ecn_type and ecn.ecn_type != ecn_type:
            continue
        if project_id and ecn.project_id != project_id:
            continue

        filtered_tasks.append((task, ecn))

    total = len(filtered_tasks)
    paginated = filtered_tasks[pagination.offset : pagination.offset + pagination.limit]

    items = []
    for task, ecn in paginated:
        instance = task.instance

        items.append(
            {
                "task_id": task.id,
                "instance_id": instance.id,
                "ecn_id": instance.entity_id,
                "ecn_no": ecn.ecn_no,
                "ecn_title": ecn.ecn_title,
                "ecn_type": ecn.ecn_type,
                "project_name": ecn.project.project_name if ecn.project else None,
                "cost_impact": float(ecn.cost_impact) if ecn.cost_impact else 0,
                "schedule_impact_days": ecn.schedule_impact_days or 0,
                "priority": ecn.priority,
                "urgency": instance.urgency,
                "initiator_name": instance.initiator.real_name
                if instance.initiator
                else None,
                "submitted_at": instance.created_at.isoformat()
                if instance.created_at
                else None,
                "node_name": task.node.node_name if task.node else None,
            }
        )

    return ResponseModel(
        code=200,
        message="获取待审批列表成功",
        data={
            "items": items,
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "pages": pagination.pages_for_total(total),
        },
    )


@router.post("/action", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def perform_approval_action(
    *,
    db: Session = Depends(deps.get_db),
    request: ApprovalActionRequest,
    current_user: User = Depends(security.require_permission("ecn:approve")),
) -> Any:
    """
    执行审批操作

    对单个ECN进行审批通过或驳回。
    """
    engine = ApprovalEngineService(db)

    try:
        if request.action == "approve":
            result = engine.approve(
                task_id=request.task_id,
                approver_id=current_user.id,
                comment=request.comment,
            )
        elif request.action == "reject":
            result = engine.reject(
                task_id=request.task_id,
                approver_id=current_user.id,
                comment=request.comment,
            )
        else:
            raise HTTPException(
                status_code=400, detail=f"不支持的操作类型: {request.action}"
            )

        db.commit()

        return ResponseModel(
            code=200,
            message="审批操作成功",
            data={
                "task_id": request.task_id,
                "action": request.action,
                "instance_status": result.status if hasattr(result, "status") else None,
            },
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/batch-action", response_model=ResponseModel, status_code=status.HTTP_200_OK
)
def perform_batch_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: BatchApprovalRequest,
    current_user: User = Depends(security.require_permission("ecn:approve")),
) -> Any:
    """
    批量审批操作

    对多个ECN进行批量审批通过或驳回。
    """
    engine = ApprovalEngineService(db)
    results = []
    errors = []

    for task_id in request.task_ids:
        try:
            if request.action == "approve":
                engine.approve(
                    task_id=task_id,
                    approver_id=current_user.id,
                    comment=request.comment,
                )
            elif request.action == "reject":
                engine.reject(
                    task_id=task_id,
                    approver_id=current_user.id,
                    comment=request.comment,
                )
            else:
                errors.append(
                    {"task_id": task_id, "error": f"不支持的操作: {request.action}"}
                )
                continue

            results.append({"task_id": task_id, "status": "success"})
        except Exception as e:
            errors.append({"task_id": task_id, "error": str(e)})

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量审批完成: 成功 {len(results)} 个, 失败 {len(errors)} 个",
        data={"success": results, "errors": errors},
    )


@router.get(
    "/status/{ecn_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK
)
def get_approval_status(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("ecn:read")),
) -> Any:
    """
    查询ECN审批状态

    获取指定ECN的审批流程状态和历史。
    """
    from app.models.approval import ApprovalInstance, ApprovalTask

    ecn = get_or_404(db, Ecn, ecn_id, "ECN不存在")

    instance = (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == "ECN",
            ApprovalInstance.entity_id == ecn_id,
        )
        .order_by(ApprovalInstance.created_at.desc())
        .first()
    )

    if not instance:
        return ResponseModel(
            code=200,
            message="该ECN暂无审批记录",
            data={
                "ecn_id": ecn_id,
                "ecn_no": ecn.ecn_no,
                "status": ecn.status,
                "approval_instance": None,
            },
        )

    tasks = (
        db.query(ApprovalTask)
        .filter(ApprovalTask.instance_id == instance.id)
        .order_by(ApprovalTask.created_at)
        .all()
    )

    task_history = []
    for task in tasks:
        task_history.append(
            {
                "task_id": task.id,
                "node_name": task.node.node_name if task.node else None,
                "assignee_name": task.assignee.real_name if task.assignee else None,
                "status": task.status,
                "action": task.action,
                "comment": task.comment,
                "completed_at": task.completed_at.isoformat()
                if task.completed_at
                else None,
            }
        )

    # 获取评估汇总
    evaluations = (
        db.query(EcnEvaluation).filter(EcnEvaluation.ecn_id == ecn_id).all()
    )
    eval_summary = {
        "total": len(evaluations),
        "completed": len([e for e in evaluations if e.status == "COMPLETED"]),
        "total_cost": sum(float(e.cost_estimate or 0) for e in evaluations),
        "total_days": sum(e.schedule_estimate or 0 for e in evaluations),
    }

    return ResponseModel(
        code=200,
        message="获取审批状态成功",
        data={
            "ecn_id": ecn_id,
            "ecn_no": ecn.ecn_no,
            "ecn_title": ecn.ecn_title,
            "ecn_type": ecn.ecn_type,
            "ecn_status": ecn.status,
            "project_name": ecn.project.project_name if ecn.project else None,
            "cost_impact": float(ecn.cost_impact) if ecn.cost_impact else 0,
            "schedule_impact_days": ecn.schedule_impact_days or 0,
            "evaluation_summary": eval_summary,
            "instance_id": instance.id,
            "instance_status": instance.status,
            "urgency": instance.urgency,
            "submitted_at": instance.created_at.isoformat()
            if instance.created_at
            else None,
            "completed_at": instance.completed_at.isoformat()
            if instance.completed_at
            else None,
            "task_history": task_history,
        },
    )


@router.post("/withdraw", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def withdraw_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: WithdrawApprovalRequest,
    current_user: User = Depends(security.require_permission("ecn:create")),
) -> Any:
    """
    撤回审批

    撤回正在审批中的ECN。
    """
    from app.models.approval import ApprovalInstance

    ecn = db.query(Ecn).filter(Ecn.id == request.ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")

    instance = (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == "ECN",
            ApprovalInstance.entity_id == request.ecn_id,
            ApprovalInstance.status == "PENDING",
        )
        .first()
    )

    if not instance:
        raise HTTPException(status_code=400, detail="没有进行中的审批流程可撤回")

    if instance.initiator_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能撤回自己提交的审批")

    engine = ApprovalEngineService(db)
    try:
        engine.withdraw(instance_id=instance.id, user_id=current_user.id)

        # 更新ECN状态
        ecn.status = "DRAFT"
        ecn.current_step = None

        db.commit()

        return ResponseModel(
            code=200,
            message="审批撤回成功",
            data={
                "ecn_id": request.ecn_id,
                "ecn_no": ecn.ecn_no,
                "status": "withdrawn",
            },
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_approval_history(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    status_filter: Optional[str] = Query(
        None, description="状态筛选: APPROVED/REJECTED"
    ),
    ecn_type: Optional[str] = Query(None, description="ECN类型筛选"),
    current_user: User = Depends(security.require_permission("ecn:read")),
) -> Any:
    """
    获取审批历史

    获取当前用户处理过的ECN审批历史。
    """
    from app.models.approval import ApprovalInstance, ApprovalTask

    query = (
        db.query(ApprovalTask)
        .join(ApprovalInstance)
        .filter(
            ApprovalTask.assignee_id == current_user.id,
            ApprovalInstance.entity_type == "ECN",
            ApprovalTask.status.in_(["APPROVED", "REJECTED"]),
        )
    )

    if status_filter:
        query = query.filter(ApprovalTask.status == status_filter)

    total = query.count()
    tasks = (
        query.order_by(ApprovalTask.completed_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )

    items = []
    for task in tasks:
        instance = task.instance
        ecn = db.query(Ecn).filter(Ecn.id == instance.entity_id).first()

        # 类型筛选
        if ecn_type and ecn and ecn.ecn_type != ecn_type:
            continue

        items.append(
            {
                "task_id": task.id,
                "ecn_id": instance.entity_id,
                "ecn_no": ecn.ecn_no if ecn else None,
                "ecn_title": ecn.ecn_title if ecn else None,
                "ecn_type": ecn.ecn_type if ecn else None,
                "project_name": ecn.project.project_name
                if ecn and ecn.project
                else None,
                "action": task.action,
                "status": task.status,
                "comment": task.comment,
                "completed_at": task.completed_at.isoformat()
                if task.completed_at
                else None,
            }
        )

    return ResponseModel(
        code=200,
        message="获取审批历史成功",
        data={
            "items": items,
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "pages": pagination.pages_for_total(total),
        },
    )

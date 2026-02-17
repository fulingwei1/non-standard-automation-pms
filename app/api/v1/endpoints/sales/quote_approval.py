# -*- coding: utf-8 -*-
"""
报价审批工作流 API

使用统一审批引擎实现报价审批流程。
报价在完成定价后需要提交审批以确认报价条款。
"""

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales.quotes import Quote, QuoteVersion
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.approval_engine import ApprovalEngineService
from app.common.pagination import PaginationParams, get_pagination_query

logger = logging.getLogger(__name__)

from app.utils.db_helpers import get_or_404
router = APIRouter(prefix="/quotes/approval", tags=["报价审批工作流"])


# ==================== 请求模型 ====================


class QuoteSubmitApprovalRequest(BaseModel):
    """报价提交审批请求"""

    quote_ids: List[int] = Field(..., description="报价ID列表")
    version_ids: Optional[List[int]] = Field(None, description="指定版本ID列表（可选）")
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

    quote_id: int = Field(..., description="报价ID")
    reason: Optional[str] = Field(None, description="撤回原因")


# ==================== API 端点 ====================


@router.post("/submit", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def submit_for_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: QuoteSubmitApprovalRequest,
    current_user: User = Depends(security.require_permission("quote:create")),
) -> Any:
    """
    提交报价审批

    将已完成定价的报价提交到审批流程。
    适用于：
    - 新报价完成后提交审批
    - 被驳回的报价修改后重新提交
    - 报价版本更新后提交审批
    """
    engine = ApprovalEngineService(db)
    results = []
    errors = []

    for i, quote_id in enumerate(request.quote_ids):
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            errors.append({"quote_id": quote_id, "error": "报价不存在"})
            continue

        # 验证状态：只有草稿或被驳回的报价可以提交审批
        if quote.status not in ["DRAFT", "REJECTED"]:
            errors.append(
                {
                    "quote_id": quote_id,
                    "error": f"当前状态 '{quote.status}' 不允许提交审批",
                }
            )
            continue

        # 获取版本信息
        version = None
        if request.version_ids and i < len(request.version_ids):
            version = (
                db.query(QuoteVersion)
                .filter(
                    QuoteVersion.id == request.version_ids[i],
                    QuoteVersion.quote_id == quote_id,
                )
                .first()
            )
        if not version:
            version = quote.current_version
        if not version:
            version = (
                db.query(QuoteVersion)
                .filter(QuoteVersion.quote_id == quote_id)
                .order_by(QuoteVersion.id.desc())
                .first()
            )

        if not version:
            errors.append({"quote_id": quote_id, "error": "报价没有版本，无法提交审批"})
            continue

        try:
            # 构建表单数据
            form_data = {
                "quote_id": quote.id,
                "quote_code": quote.quote_code,
                "version_id": version.id,
                "version_no": version.version_no,
                "total_price": float(version.total_price) if version.total_price else 0,
                "cost_total": float(version.cost_total) if version.cost_total else 0,
                "gross_margin": float(version.gross_margin) if version.gross_margin else 0,
                "customer_id": quote.customer_id,
                "customer_name": quote.customer.name if quote.customer else None,
                "lead_time_days": version.lead_time_days,
            }

            instance = engine.submit(
                template_code="SALES_QUOTE_APPROVAL",
                entity_type="QUOTE",
                entity_id=quote_id,
                form_data=form_data,
                initiator_id=current_user.id,
                urgency=request.urgency,
            )

            results.append(
                {
                    "quote_id": quote_id,
                    "quote_code": quote.quote_code,
                    "version_no": version.version_no,
                    "instance_id": instance.id,
                    "status": "submitted",
                }
            )
        except Exception as e:
            logger.exception(f"报价 {quote_id} 提交审批失败")
            errors.append({"quote_id": quote_id, "error": str(e)})

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
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    current_user: User = Depends(security.require_permission("quote:read")),
) -> Any:
    """
    获取待审批的报价列表

    返回当前用户待审批的报价任务。
    """
    engine = ApprovalEngineService(db)
    tasks = engine.get_pending_tasks(user_id=current_user.id, entity_type="QUOTE")

    # 客户筛选
    if customer_id:
        filtered_tasks = []
        for task in tasks:
            quote = (
                db.query(Quote)
                .filter(Quote.id == task.instance.entity_id)
                .first()
            )
            if quote and quote.customer_id == customer_id:
                filtered_tasks.append(task)
        tasks = filtered_tasks

    total = len(tasks)
    paginated_tasks = tasks[pagination.offset : pagination.offset + pagination.page_size]

    items = []
    for task in paginated_tasks:
        instance = task.instance
        quote = (
            db.query(Quote).filter(Quote.id == instance.entity_id).first()
        )

        # 获取版本信息
        version = quote.current_version if quote else None
        if not version and quote:
            version = (
                db.query(QuoteVersion)
                .filter(QuoteVersion.quote_id == quote.id)
                .order_by(QuoteVersion.id.desc())
                .first()
            )

        items.append(
            {
                "task_id": task.id,
                "instance_id": instance.id,
                "quote_id": instance.entity_id,
                "quote_code": quote.quote_code if quote else None,
                "customer_name": quote.customer.name if quote and quote.customer else None,
                "version_no": version.version_no if version else None,
                "total_price": float(version.total_price) if version and version.total_price else 0,
                "gross_margin": float(version.gross_margin) if version and version.gross_margin else 0,
                "lead_time_days": version.lead_time_days if version else None,
                "initiator_name": instance.initiator.real_name if instance.initiator else None,
                "submitted_at": instance.created_at.isoformat() if instance.created_at else None,
                "urgency": instance.urgency,
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
            "pages": (total + pagination.page_size - 1) // pagination.page_size,
        },
    )


@router.post("/action", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def perform_approval_action(
    *,
    db: Session = Depends(deps.get_db),
    request: ApprovalActionRequest,
    current_user: User = Depends(security.require_permission("quote:approve")),
) -> Any:
    """
    执行审批操作

    对单个报价进行审批通过或驳回。
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
    current_user: User = Depends(security.require_permission("quote:approve")),
) -> Any:
    """
    批量审批操作

    对多个报价进行批量审批通过或驳回。
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
    "/status/{quote_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK
)
def get_approval_status(
    quote_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("quote:read")),
) -> Any:
    """
    查询报价审批状态

    获取指定报价的审批流程状态和历史。
    """
    from app.models.approval import ApprovalInstance, ApprovalTask

    quote = get_or_404(db, Quote, quote_id, detail="报价不存在")

    instance = (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == "QUOTE",
            ApprovalInstance.entity_id == quote_id,
        )
        .order_by(ApprovalInstance.created_at.desc())
        .first()
    )

    if not instance:
        return ResponseModel(
            code=200,
            message="该报价暂无审批记录",
            data={
                "quote_id": quote_id,
                "quote_code": quote.quote_code,
                "status": quote.status,
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

    # 获取版本信息
    version = quote.current_version
    version_info = None
    if version:
        version_info = {
            "version_no": version.version_no,
            "total_price": float(version.total_price) if version.total_price else 0,
            "gross_margin": float(version.gross_margin) if version.gross_margin else 0,
        }

    return ResponseModel(
        code=200,
        message="获取审批状态成功",
        data={
            "quote_id": quote_id,
            "quote_code": quote.quote_code,
            "customer_name": quote.customer.name if quote.customer else None,
            "quote_status": quote.status,
            "version_info": version_info,
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
    current_user: User = Depends(security.require_permission("quote:create")),
) -> Any:
    """
    撤回审批

    撤回正在审批中的报价。
    """
    from app.models.approval import ApprovalInstance

    quote = db.query(Quote).filter(Quote.id == request.quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    instance = (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == "QUOTE",
            ApprovalInstance.entity_id == request.quote_id,
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
        db.commit()

        return ResponseModel(
            code=200,
            message="审批撤回成功",
            data={
                "quote_id": request.quote_id,
                "quote_code": quote.quote_code,
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
    status_filter: Optional[str] = Query(None, description="状态筛选: APPROVED/REJECTED"),
    current_user: User = Depends(security.require_permission("quote:read")),
) -> Any:
    """
    获取审批历史

    获取当前用户处理过的报价审批历史。
    """
    from app.models.approval import ApprovalInstance, ApprovalTask

    query = (
        db.query(ApprovalTask)
        .join(ApprovalInstance)
        .filter(
            ApprovalTask.assignee_id == current_user.id,
            ApprovalInstance.entity_type == "QUOTE",
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
        quote = (
            db.query(Quote)
            .filter(Quote.id == instance.entity_id)
            .first()
        )

        items.append(
            {
                "task_id": task.id,
                "quote_id": instance.entity_id,
                "quote_code": quote.quote_code if quote else None,
                "customer_name": quote.customer.name if quote and quote.customer else None,
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
            "pages": (total + pagination.page_size - 1) // pagination.page_size,
        },
    )

# -*- coding: utf-8 -*-
"""
合同审批工作流 API

使用统一审批引擎实现合同审批流程。
合同在完成条款拟定后需要提交审批以确认合同内容。
"""

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales.contracts import Contract
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.approval_engine import ApprovalEngineService
from app.common.pagination import PaginationParams, get_pagination_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contracts/approval", tags=["合同审批工作流"])


# ==================== 请求模型 ====================


class ContractSubmitApprovalRequest(BaseModel):
    """合同提交审批请求"""

    contract_ids: List[int] = Field(..., description="合同ID列表")
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

    contract_id: int = Field(..., description="合同ID")
    reason: Optional[str] = Field(None, description="撤回原因")


# ==================== API 端点 ====================


@router.post("/submit", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def submit_for_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: ContractSubmitApprovalRequest,
    current_user: User = Depends(security.require_permission("contract:create")),
) -> Any:
    """
    提交合同审批

    将已完成条款拟定的合同提交到审批流程。
    适用于：
    - 新合同拟定完成后提交审批
    - 被驳回的合同修改后重新提交
    - 合同变更后需要重新审批
    """
    engine = ApprovalEngineService(db)
    results = []
    errors = []

    for contract_id in request.contract_ids:
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            errors.append({"contract_id": contract_id, "error": "合同不存在"})
            continue

        # 验证状态：只有草稿或被驳回的合同可以提交审批
        if contract.status not in ["DRAFT", "REJECTED"]:
            errors.append(
                {
                    "contract_id": contract_id,
                    "error": f"当前状态 '{contract.status}' 不允许提交审批",
                }
            )
            continue

        # 验证合同金额
        if not contract.contract_amount or contract.contract_amount <= 0:
            errors.append(
                {"contract_id": contract_id, "error": "合同金额必须大于0"}
            )
            continue

        try:
            # 构建表单数据
            form_data = {
                "contract_id": contract.id,
                "contract_code": contract.contract_code,
                "customer_contract_no": contract.customer_contract_no,
                "contract_amount": float(contract.contract_amount) if contract.contract_amount else 0,
                "customer_id": contract.customer_id,
                "customer_name": contract.customer.name if contract.customer else None,
                "project_id": contract.project_id,
                "signed_date": contract.signed_date.isoformat() if contract.signed_date else None,
                "payment_terms_summary": contract.payment_terms_summary,
                "acceptance_summary": contract.acceptance_summary,
            }

            instance = engine.submit(
                template_code="SALES_CONTRACT_APPROVAL",
                entity_type="CONTRACT",
                entity_id=contract_id,
                form_data=form_data,
                initiator_id=current_user.id,
                urgency=request.urgency,
            )

            results.append(
                {
                    "contract_id": contract_id,
                    "contract_code": contract.contract_code,
                    "contract_amount": float(contract.contract_amount) if contract.contract_amount else 0,
                    "instance_id": instance.id,
                    "status": "submitted",
                }
            )
        except Exception as e:
            logger.exception(f"合同 {contract_id} 提交审批失败")
            errors.append({"contract_id": contract_id, "error": str(e)})

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
    min_amount: Optional[float] = Query(None, description="最小金额筛选"),
    current_user: User = Depends(security.require_permission("contract:read")),
) -> Any:
    """
    获取待审批的合同列表

    返回当前用户待审批的合同任务。
    """
    engine = ApprovalEngineService(db)
    tasks = engine.get_pending_tasks(user_id=current_user.id, entity_type="CONTRACT")

    # 筛选
    filtered_tasks = []
    for task in tasks:
        contract = (
            db.query(Contract)
            .filter(Contract.id == task.instance.entity_id)
            .first()
        )
        if not contract:
            continue
        if customer_id and contract.customer_id != customer_id:
            continue
        if min_amount and (not contract.contract_amount or float(contract.contract_amount) < min_amount):
            continue
        filtered_tasks.append(task)

    tasks = filtered_tasks
    total = len(tasks)
    paginated_tasks = tasks[pagination.offset : pagination.offset + pagination.page_size]

    items = []
    for task in paginated_tasks:
        instance = task.instance
        contract = (
            db.query(Contract).filter(Contract.id == instance.entity_id).first()
        )

        items.append(
            {
                "task_id": task.id,
                "instance_id": instance.id,
                "contract_id": instance.entity_id,
                "contract_code": contract.contract_code if contract else None,
                "customer_contract_no": contract.customer_contract_no if contract else None,
                "customer_name": contract.customer.name if contract and contract.customer else None,
                "contract_amount": float(contract.contract_amount) if contract and contract.contract_amount else 0,
                "project_name": contract.project.project_name if contract and contract.project else None,
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
    current_user: User = Depends(security.require_permission("contract:approve")),
) -> Any:
    """
    执行审批操作

    对单个合同进行审批通过或驳回。
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
    current_user: User = Depends(security.require_permission("contract:approve")),
) -> Any:
    """
    批量审批操作

    对多个合同进行批量审批通过或驳回。
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
    "/status/{contract_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK
)
def get_approval_status(
    contract_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("contract:read")),
) -> Any:
    """
    查询合同审批状态

    获取指定合同的审批流程状态和历史。
    """
    from app.models.approval import ApprovalInstance, ApprovalTask

    contract = get_or_404(db, Contract, contract_id, detail="合同不存在")

    instance = (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == "CONTRACT",
            ApprovalInstance.entity_id == contract_id,
        )
        .order_by(ApprovalInstance.created_at.desc())
        .first()
    )

    if not instance:
        return ResponseModel(
            code=200,
            message="该合同暂无审批记录",
            data={
                "contract_id": contract_id,
                "contract_code": contract.contract_code,
                "status": contract.status,
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

    return ResponseModel(
        code=200,
        message="获取审批状态成功",
        data={
            "contract_id": contract_id,
            "contract_code": contract.contract_code,
            "customer_contract_no": contract.customer_contract_no,
            "customer_name": contract.customer.name if contract.customer else None,
            "contract_amount": float(contract.contract_amount) if contract.contract_amount else 0,
            "contract_status": contract.status,
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
    current_user: User = Depends(security.require_permission("contract:create")),
) -> Any:
    """
    撤回审批

    撤回正在审批中的合同。
    """
    from app.models.approval import ApprovalInstance

    contract = db.query(Contract).filter(Contract.id == request.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    instance = (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == "CONTRACT",
            ApprovalInstance.entity_id == request.contract_id,
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
                "contract_id": request.contract_id,
                "contract_code": contract.contract_code,
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
    current_user: User = Depends(security.require_permission("contract:read")),
) -> Any:
    """
    获取审批历史

    获取当前用户处理过的合同审批历史。
    """
    from app.models.approval import ApprovalInstance, ApprovalTask
from app.utils.db_helpers import get_or_404

    query = (
        db.query(ApprovalTask)
        .join(ApprovalInstance)
        .filter(
            ApprovalTask.assignee_id == current_user.id,
            ApprovalInstance.entity_type == "CONTRACT",
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
        contract = (
            db.query(Contract)
            .filter(Contract.id == instance.entity_id)
            .first()
        )

        items.append(
            {
                "task_id": task.id,
                "contract_id": instance.entity_id,
                "contract_code": contract.contract_code if contract else None,
                "customer_name": contract.customer.name if contract and contract.customer else None,
                "contract_amount": float(contract.contract_amount) if contract and contract.contract_amount else 0,
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

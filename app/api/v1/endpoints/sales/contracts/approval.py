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
from app.models.user import User
from app.schemas.common import ResponseModel
from app.common.pagination import PaginationParams, get_pagination_query
from app.services.contract_approval import ContractApprovalService

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
    service = ContractApprovalService(db)
    results, errors = service.submit_contracts_for_approval(
        contract_ids=request.contract_ids,
        initiator_id=current_user.id,
        urgency=request.urgency,
        comment=request.comment,
    )

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
    service = ContractApprovalService(db)
    items, total = service.get_pending_tasks(
        user_id=current_user.id,
        page=pagination.page,
        page_size=pagination.page_size,
        customer_id=customer_id,
        min_amount=min_amount,
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
    service = ContractApprovalService(db)

    try:
        if request.action == "approve":
            result = service.approve_task(
                task_id=request.task_id,
                approver_id=current_user.id,
                comment=request.comment,
            )
        elif request.action == "reject":
            result = service.reject_task(
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
    service = ContractApprovalService(db)
    results, errors = service.batch_approve_or_reject(
        task_ids=request.task_ids,
        approver_id=current_user.id,
        action=request.action,
        comment=request.comment,
    )

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
    service = ContractApprovalService(db)
    
    try:
        status_data = service.get_contract_approval_status(contract_id)
        
        if not status_data:
            # 获取合同基本信息
            from app.models.sales.contracts import Contract
            from app.utils.db_helpers import get_or_404
            
            contract = get_or_404(db, Contract, contract_id, detail="合同不存在")
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
        
        return ResponseModel(
            code=200,
            message="获取审批状态成功",
            data=status_data,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


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
    service = ContractApprovalService(db)
    
    try:
        result = service.withdraw_approval(
            contract_id=request.contract_id,
            user_id=current_user.id,
            reason=request.reason,
        )
        
        db.commit()
        
        return ResponseModel(
            code=200,
            message="审批撤回成功",
            data=result,
        )
    except ValueError as e:
        db.rollback()
        if "不存在" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        elif "只能撤回" in str(e):
            raise HTTPException(status_code=403, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
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
    service = ContractApprovalService(db)
    items, total = service.get_approval_history(
        user_id=current_user.id,
        page=pagination.page,
        page_size=pagination.page_size,
        status_filter=status_filter,
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

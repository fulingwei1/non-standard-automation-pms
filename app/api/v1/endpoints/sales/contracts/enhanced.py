# -*- coding: utf-8 -*-
"""
合同管理增强 API - 完整的CRUD与审批流程
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.user import User
from app.schemas.sales.contract_enhanced import (
    ContractApprovalResponse,
    ContractApprovalUpdate,
    ContractAttachmentCreate,
    ContractAttachmentResponse,
    ContractCreate,
    ContractResponse,
    ContractStats,
    ContractStatusChange,
    ContractSubmitApproval,
    ContractTermCreate,
    ContractTermResponse,
    ContractTermUpdate,
    ContractUpdate,
)
from app.core.sales_permissions import check_sales_data_permission, filter_sales_data_by_scope
from app.models.sales import Contract, ContractAttachment
from app.services.contract_approval import (
    ContractApprovalService as UnifiedContractApprovalService,
)
from app.services.sales.contract_enhanced import ContractEnhancedService
from .attachment_security import resolve_contract_attachment_path

router = APIRouter()


def _serialize_contract_list_item(contract) -> dict:
    total_amount = contract.total_amount or 0
    received_amount = contract.received_amount or 0
    unreceived_amount = contract.unreceived_amount
    if unreceived_amount is None:
        unreceived_amount = total_amount - received_amount

    return {
        "id": contract.id,
        "contract_code": contract.contract_code,
        "contract_name": contract.contract_name,
        "contract_type": contract.contract_type,
        "customer_id": contract.customer_id,
        "total_amount": float(total_amount),
        "amount_without_tax": float(contract.amount_without_tax or 0),
        "tax_rate": float(contract.tax_rate or 0),
        "tax_amount": float(contract.tax_amount or 0),
        "amount_with_tax": float(contract.amount_with_tax or total_amount),
        "received_amount": float(received_amount),
        "unreceived_amount": float(unreceived_amount or 0),
        "status": contract.status,
        "signing_date": contract.signing_date.isoformat() if contract.signing_date else None,
        "effective_date": contract.effective_date.isoformat() if contract.effective_date else None,
        "expiry_date": contract.expiry_date.isoformat() if contract.expiry_date else None,
        "created_at": contract.created_at.isoformat() if contract.created_at else None,
    }


# ========== 合同CRUD ==========
@router.post("/", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    contract_data: ContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:create")),
):
    """创建合同"""
    try:
        contract = ContractEnhancedService.create_contract(db, contract_data, current_user.id)
        return contract
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=dict)
def get_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    customer_id: Optional[int] = Query(None),
    contract_type: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:view")),
):
    """合同列表（支持搜索/筛选，受数据权限过滤）"""
    contracts, total = ContractEnhancedService.get_contracts(
        db,
        skip=skip,
        limit=limit,
        status=status,
        customer_id=customer_id,
        contract_type=contract_type,
        keyword=keyword,
    )

    # 数据权限：二次过滤（service 层未集成 scope 时的兜底）
    filtered = [
        c for c in contracts
        if check_sales_data_permission(c, current_user, db, "sales_owner_id")
    ]

    serialized_items = [_serialize_contract_list_item(contract) for contract in filtered]

    return {
        "items": serialized_items,
        "total": len(filtered),
        "skip": skip,
        "limit": limit,
    }


@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:view")),
):
    """合同详情"""
    contract = ContractEnhancedService.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    if not check_sales_data_permission(contract, current_user, db, "sales_owner_id"):
        raise HTTPException(status_code=403, detail="无权访问该合同")
    return contract


@router.put("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: int,
    contract_data: ContractUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:update")),
):
    """更新合同"""
    try:
        contract = ContractEnhancedService.update_contract(
            db, contract_id, contract_data, operator_id=current_user.id
        )
        if not contract:
            raise HTTPException(status_code=404, detail="合同不存在")
        return contract
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:delete")),
):
    """删除合同"""
    try:
        success = ContractEnhancedService.delete_contract(
            db, contract_id, operator_id=current_user.id
        )
        if not success:
            raise HTTPException(status_code=404, detail="合同不存在")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== 合同审批流程 ==========
@router.post("/{contract_id}/submit", response_model=ContractResponse)
def submit_contract_for_approval(
    contract_id: int,
    submit_data: ContractSubmitApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:create")),
):
    """提交审批（兼容旧增强路径，但必须走统一审批引擎）。"""
    try:
        service = UnifiedContractApprovalService(db)
        results, errors = service.submit_contracts_for_approval(
            contract_ids=[contract_id],
            initiator_id=current_user.id,
            comment=submit_data.comment if submit_data else None,
        )
        if errors and not results:
            raise ValueError(errors[0].get("error") or "提交合同统一审批失败")
        db.commit()
        contract = ContractEnhancedService.get_contract(db, contract_id)
        if not contract:
            raise ValueError("合同不存在")
        return contract
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{contract_id}/approvals", response_model=List[dict])
def get_contract_approvals(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:view")),
):
    """审批记录（统一审批实例/任务）。"""
    contract = ContractEnhancedService.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    tasks = (
        db.query(ApprovalTask)
        .join(ApprovalInstance, ApprovalTask.instance_id == ApprovalInstance.id)
        .filter(
            ApprovalInstance.entity_type == "CONTRACT",
            ApprovalInstance.entity_id == contract_id,
        )
        .order_by(ApprovalTask.created_at)
        .all()
    )
    return [
        {
            "id": task.id,
            "task_id": task.id,
            "instance_id": task.instance_id,
            "contract_id": contract_id,
            "approval_level": task.task_order or 1,
            "approval_role": task.node.node_name if task.node else "统一审批",
            "approver_id": task.assignee_id,
            "approver_name": task.assignee_name,
            "approval_status": task.status,
            "approval_opinion": task.comment,
            "approved_at": task.completed_at,
        }
        for task in tasks
    ]


@router.post("/{contract_id}/approve", response_model=ContractResponse)
def approve_contract(
    contract_id: int,
    approval_id: int = Query(..., description="审批记录ID"),
    approval_data: ContractApprovalUpdate = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:approve")),
):
    """旧审批入口已停用，避免绕过统一审批任务。"""
    raise HTTPException(
        status_code=400,
        detail="旧增强合同审批入口已下线，请使用统一审批 /sales/contracts/approval/action",
    )


@router.post("/{contract_id}/reject", response_model=ContractResponse)
def reject_contract(
    contract_id: int,
    approval_id: int = Query(..., description="审批记录ID"),
    approval_data: ContractApprovalUpdate = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:approve")),
):
    """旧驳回入口已停用，避免绕过统一审批任务。"""
    raise HTTPException(
        status_code=400,
        detail="旧增强合同审批入口已下线，请使用统一审批 /sales/contracts/approval/action",
    )


@router.get("/approvals/pending", response_model=List[dict])
def get_pending_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:view")),
):
    """待审批列表（我的待办）"""
    approvals = ContractEnhancedService.get_pending_approvals(db, current_user.id)
    return approvals


# ========== 合同条款管理 ==========
@router.post("/{contract_id}/terms", response_model=ContractTermResponse, status_code=status.HTTP_201_CREATED)
def add_contract_term(
    contract_id: int,
    term_data: ContractTermCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:update")),
):
    """添加条款"""
    term = ContractEnhancedService.add_term(
        db, contract_id, term_data, operator_id=current_user.id
    )
    return term


@router.get("/{contract_id}/terms", response_model=List[ContractTermResponse])
def get_contract_terms(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:view")),
):
    """条款列表"""
    terms = ContractEnhancedService.get_terms(db, contract_id)
    return terms


@router.put("/terms/{term_id}", response_model=ContractTermResponse)
def update_contract_term(
    term_id: int,
    term_data: ContractTermUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:update")),
):
    """更新条款"""
    if not term_data.term_content:
        raise HTTPException(status_code=400, detail="条款内容不能为空")
    
    term = ContractEnhancedService.update_term(
        db, term_id, term_data.term_content, operator_id=current_user.id
    )
    if not term:
        raise HTTPException(status_code=404, detail="条款不存在")
    return term


@router.delete("/terms/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract_term(
    term_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:update")),
):
    """删除条款"""
    success = ContractEnhancedService.delete_term(
        db, term_id, operator_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="条款不存在")


# ========== 合同附件管理 ==========
@router.post("/{contract_id}/attachments", response_model=ContractAttachmentResponse, status_code=status.HTTP_201_CREATED)
def upload_attachment(
    contract_id: int,
    attachment_data: ContractAttachmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:update")),
):
    """上传附件"""
    attachment = ContractEnhancedService.add_attachment(db, contract_id, attachment_data, current_user.id)
    return attachment


@router.get("/{contract_id}/attachments", response_model=List[ContractAttachmentResponse])
def get_contract_attachments(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:view")),
):
    """附件列表"""
    attachments = ContractEnhancedService.get_attachments(db, contract_id)
    return attachments


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:update")),
):
    """删除附件"""
    success = ContractEnhancedService.delete_attachment(
        db, attachment_id, operator_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="附件不存在")


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:view")),
):
    """下载附件"""
    attachment = db.query(ContractAttachment).filter(ContractAttachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    file_path = resolve_contract_attachment_path(attachment.file_path)
    return FileResponse(
        path=str(file_path),
        filename=attachment.file_name,
        media_type=attachment.file_type or "application/octet-stream",
    )


# ========== 合同状态流转 ==========
@router.post("/{contract_id}/sign", response_model=ContractResponse)
def mark_contract_as_signed(
    contract_id: int,
    change_data: ContractStatusChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:sign")),
):
    """标记为已签署"""
    try:
        contract = ContractEnhancedService.mark_as_signed(db, contract_id)
        return contract
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{contract_id}/execute", response_model=ContractResponse)
def mark_contract_as_executing(
    contract_id: int,
    change_data: ContractStatusChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:update")),
):
    """标记为执行中"""
    try:
        contract = ContractEnhancedService.mark_as_executing(db, contract_id)
        return contract
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{contract_id}/complete", response_model=ContractResponse)
def mark_contract_as_completed(
    contract_id: int,
    change_data: ContractStatusChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:update")),
):
    """标记为已完成"""
    try:
        contract = ContractEnhancedService.mark_as_completed(db, contract_id)
        return contract
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{contract_id}/void", response_model=ContractResponse)
def void_contract(
    contract_id: int,
    change_data: ContractStatusChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:delete")),
):
    """作废合同"""
    try:
        reason = change_data.comment if change_data else None
        contract = ContractEnhancedService.void_contract(db, contract_id, reason)
        return contract
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== 合同统计 ==========
@router.get("/stats/summary", response_model=ContractStats)
def get_contract_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("contract:view")),
):
    """合同统计（受数据权限过滤）"""
    from decimal import Decimal
    from sqlalchemy import func

    # 数据权限：只统计用户有权访问的合同
    base = filter_sales_data_by_scope(
        db.query(Contract), current_user, db, Contract, "sales_owner_id"
    )

    total_count = base.count()
    from app.services.sales.contract.status_service import fold_contract_status_counts

    status_counts = fold_contract_status_counts(
        base.with_entities(Contract.status, func.count(Contract.id)).group_by(Contract.status).all()
    )

    total_amount = base.with_entities(func.sum(Contract.total_amount)).scalar() or Decimal(0)
    received_amount = base.with_entities(func.sum(Contract.received_amount)).scalar() or Decimal(0)
    unreceived_amount = base.with_entities(func.sum(Contract.unreceived_amount)).scalar() or Decimal(0)

    return ContractStats(
        total_count=total_count,
        draft_count=status_counts.get("DRAFT", 0),
        approving_count=status_counts.get("PENDING_APPROVAL", 0),
        signed_count=status_counts.get("SIGNED", 0),
        executing_count=status_counts.get("EXECUTING", 0),
        completed_count=status_counts.get("COMPLETED", 0),
        voided_count=status_counts.get("CANCELLED", 0),
        total_amount=total_amount,
        received_amount=received_amount,
        unreceived_amount=unreceived_amount,
    )

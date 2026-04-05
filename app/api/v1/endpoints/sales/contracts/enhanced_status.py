# -*- coding: utf-8 -*-
"""
合同状态流转与统计 API
从 enhanced.py 拆分
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.sales.contract_enhanced import (
    ContractResponse,
    ContractStats,
    ContractStatusChange,
)
from app.services.sales.contract_enhanced import ContractEnhancedService

router = APIRouter()


# ========== 合同状态流转 ==========
@router.post("/{contract_id}/sign", response_model=ContractResponse)
def mark_contract_as_signed(
    contract_id: int,
    change_data: ContractStatusChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
):
    """合同统计"""
    stats = ContractEnhancedService.get_contract_stats(db)
    return stats

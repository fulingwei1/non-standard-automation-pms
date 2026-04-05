# -*- coding: utf-8 -*-
"""
合同条款管理 API
从 enhanced.py 拆分
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.sales.contract_enhanced import (
    ContractTermCreate,
    ContractTermResponse,
    ContractTermUpdate,
)
from app.services.sales.contract_enhanced import ContractEnhancedService

router = APIRouter()


@router.post(
    "/{contract_id}/terms",
    response_model=ContractTermResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_contract_term(
    contract_id: int,
    term_data: ContractTermCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加条款"""
    term = ContractEnhancedService.add_term(db, contract_id, term_data)
    return term


@router.get("/{contract_id}/terms", response_model=List[ContractTermResponse])
def get_contract_terms(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """条款列表"""
    terms = ContractEnhancedService.get_terms(db, contract_id)
    return terms


@router.put("/terms/{term_id}", response_model=ContractTermResponse)
def update_contract_term(
    term_id: int,
    term_data: ContractTermUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新条款"""
    if not term_data.term_content:
        raise HTTPException(status_code=400, detail="条款内容不能为空")

    term = ContractEnhancedService.update_term(db, term_id, term_data.term_content)
    if not term:
        raise HTTPException(status_code=404, detail="条款不存在")
    return term


@router.delete("/terms/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract_term(
    term_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除条款"""
    success = ContractEnhancedService.delete_term(db, term_id)
    if not success:
        raise HTTPException(status_code=404, detail="条款不存在")

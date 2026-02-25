# -*- coding: utf-8 -*-
"""
合同审核 API endpoints
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.business_support import ContractReview
from app.models.sales import Contract
from app.models.user import User
from app.schemas.business_support import (
    ContractReviewCreate,
    ContractReviewResponse,
    ContractReviewUpdate,
)
from app.schemas.common import ResponseModel
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.post("/{contract_id}/review", response_model=ResponseModel[ContractReviewResponse], summary="创建合同审核")
async def create_contract_review(
    contract_id: int,
    review_data: ContractReviewCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:create"))
):
    """创建合同审核记录"""
    try:
        # 检查合同是否存在
        contract = get_or_404(db, Contract, contract_id, "合同不存在")

        # 创建审核记录
        contract_review = ContractReview(
            contract_id=contract_id,
            review_type=review_data.review_type,
            review_status="pending",
            reviewer_id=current_user.id,
            review_comment=review_data.review_comment,
            risk_items=review_data.risk_items
        )

        db.add(contract_review)
        db.commit()
        db.refresh(contract_review)

        return ResponseModel(
            code=200,
            message="创建合同审核成功",
            data=ContractReviewResponse(
                id=contract_review.id,
                contract_id=contract_review.contract_id,
                review_type=contract_review.review_type,
                review_status=contract_review.review_status,
                reviewer_id=contract_review.reviewer_id,
                review_comment=contract_review.review_comment,
                reviewed_at=contract_review.reviewed_at,
                risk_items=contract_review.risk_items,
                created_at=contract_review.created_at,
                updated_at=contract_review.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建合同审核失败: {str(e)}")


@router.put("/{contract_id}/review/{review_id}", response_model=ResponseModel[ContractReviewResponse], summary="更新合同审核")
async def update_contract_review(
    contract_id: int,
    review_id: int,
    review_data: ContractReviewUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:approve"))
):
    """更新合同审核记录（审批）"""
    try:
        contract_review = (
            db.query(ContractReview)
            .filter(
                ContractReview.id == review_id,
                ContractReview.contract_id == contract_id
            )
            .first()
        )
        if not contract_review:
            raise HTTPException(status_code=404, detail="审核记录不存在")

        # 更新审核状态
        update_data = review_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(contract_review, key, value)

        # 如果审核通过或拒绝，记录审核时间
        if review_data.review_status in ["passed", "rejected"]:
            contract_review.reviewed_at = datetime.now()

        db.commit()
        db.refresh(contract_review)

        return ResponseModel(
            code=200,
            message="更新合同审核成功",
            data=ContractReviewResponse(
                id=contract_review.id,
                contract_id=contract_review.contract_id,
                review_type=contract_review.review_type,
                review_status=contract_review.review_status,
                reviewer_id=contract_review.reviewer_id,
                review_comment=contract_review.review_comment,
                reviewed_at=contract_review.reviewed_at,
                risk_items=contract_review.risk_items,
                created_at=contract_review.created_at,
                updated_at=contract_review.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新合同审核失败: {str(e)}")

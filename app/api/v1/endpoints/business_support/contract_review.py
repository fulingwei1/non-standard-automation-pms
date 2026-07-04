# -*- coding: utf-8 -*-
"""
合同审核 API endpoints
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.business_support import ContractReview
from app.models.sales import Contract
from app.models.user import User
from app.schemas.business_support import (
    ContractReviewCreate,
    ContractReviewResponse,
    ContractReviewUpdate,
)
from app.schemas.common import PaginatedResponse, ResponseModel
from app.utils.db_helpers import get_or_404

router = APIRouter()


def _contract_review_response(contract_review: ContractReview) -> ContractReviewResponse:
    return ContractReviewResponse(
        id=contract_review.id,
        contract_id=contract_review.contract_id,
        review_type=contract_review.review_type,
        review_status=contract_review.review_status,
        reviewer_id=contract_review.reviewer_id,
        review_comment=contract_review.review_comment,
        reviewed_at=contract_review.reviewed_at,
        risk_items=contract_review.risk_items,
        created_at=contract_review.created_at,
        updated_at=contract_review.updated_at,
    )


def _create_contract_review_record(
    contract_id: int,
    review_data: ContractReviewCreate,
    db: Session,
    current_user: User,
) -> ContractReview:
    get_or_404(db, Contract, contract_id, "合同不存在")

    contract_review = ContractReview(
        contract_id=contract_id,
        review_type=review_data.review_type,
        review_status="pending",
        reviewer_id=current_user.id,
        review_comment=review_data.review_comment,
        risk_items=review_data.risk_items,
    )

    db.add(contract_review)
    db.commit()
    db.refresh(contract_review)
    return contract_review


def _update_contract_review_record(
    contract_review: ContractReview,
    review_data: ContractReviewUpdate,
    db: Session,
) -> ContractReview:
    update_data = review_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(contract_review, key, value)

    if review_data.review_status in ["passed", "rejected"]:
        contract_review.reviewed_at = datetime.now()

    db.commit()
    db.refresh(contract_review)
    return contract_review


@router.get(
    "",
    response_model=ResponseModel[PaginatedResponse[ContractReviewResponse]],
    summary="获取合同审核列表",
)
async def get_contract_reviews(
    pagination: PaginationParams = Depends(get_pagination_query),
    contract_id: Optional[int] = Query(None, description="合同ID筛选"),
    review_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:read")),
):
    """获取合同审核列表。"""
    try:
        query = db.query(ContractReview)
        if contract_id:
            query = query.filter(ContractReview.contract_id == contract_id)
        if review_status:
            query = query.filter(ContractReview.review_status == review_status)

        total = query.count()
        items = (
            query.order_by(desc(ContractReview.created_at))
            .offset(pagination.offset)
            .limit(pagination.limit)
            .all()
        )

        return ResponseModel(
            code=200,
            message="获取合同审核列表成功",
            data=PaginatedResponse(
                items=[_contract_review_response(item) for item in items],
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
                pages=pagination.pages_for_total(total),
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取合同审核列表失败: {str(e)}")


@router.post(
    "",
    response_model=ResponseModel[ContractReviewResponse],
    summary="创建合同审核",
)
async def create_contract_review_from_body(
    review_data: ContractReviewCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:create")),
):
    """按前端 /contract-review 契约创建合同审核记录。"""
    try:
        contract_review = _create_contract_review_record(
            review_data.contract_id,
            review_data,
            db,
            current_user,
        )
        return ResponseModel(
            code=200,
            message="创建合同审核成功",
            data=_contract_review_response(contract_review),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建合同审核失败: {str(e)}")


@router.get(
    "/{review_id}",
    response_model=ResponseModel[ContractReviewResponse],
    summary="获取合同审核详情",
)
async def get_contract_review(
    review_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:read")),
):
    """获取合同审核详情。"""
    try:
        contract_review = get_or_404(db, ContractReview, review_id, "审核记录不存在")
        return ResponseModel(
            code=200,
            message="获取合同审核详情成功",
            data=_contract_review_response(contract_review),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取合同审核详情失败: {str(e)}")


@router.put(
    "/{review_id}",
    response_model=ResponseModel[ContractReviewResponse],
    summary="更新合同审核",
)
async def update_contract_review_by_id(
    review_id: int,
    review_data: ContractReviewUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:approve")),
):
    """按前端 /contract-review/{id} 契约更新合同审核记录。"""
    try:
        contract_review = get_or_404(db, ContractReview, review_id, "审核记录不存在")
        contract_review = _update_contract_review_record(contract_review, review_data, db)
        return ResponseModel(
            code=200,
            message="更新合同审核成功",
            data=_contract_review_response(contract_review),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新合同审核失败: {str(e)}")


@router.post(
    "/{contract_id}/review",
    response_model=ResponseModel[ContractReviewResponse],
    summary="创建合同审核",
)
async def create_contract_review(
    contract_id: int,
    review_data: ContractReviewCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:create")),
):
    """创建合同审核记录"""
    try:
        contract_review = _create_contract_review_record(
            contract_id,
            review_data,
            db,
            current_user,
        )
        return ResponseModel(
            code=200,
            message="创建合同审核成功",
            data=_contract_review_response(contract_review),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建合同审核失败: {str(e)}")


@router.put(
    "/{contract_id}/review/{review_id}",
    response_model=ResponseModel[ContractReviewResponse],
    summary="更新合同审核",
)
async def update_contract_review(
    contract_id: int,
    review_id: int,
    review_data: ContractReviewUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:approve")),
):
    """更新合同审核记录（审批）"""
    try:
        contract_review = (
            db.query(ContractReview)
            .filter(ContractReview.id == review_id, ContractReview.contract_id == contract_id)
            .first()
        )
        if not contract_review:
            raise HTTPException(status_code=404, detail="审核记录不存在")

        contract_review = _update_contract_review_record(contract_review, review_data, db)
        return ResponseModel(
            code=200,
            message="更新合同审核成功",
            data=_contract_review_response(contract_review),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新合同审核失败: {str(e)}")

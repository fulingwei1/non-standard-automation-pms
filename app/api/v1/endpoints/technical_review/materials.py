# -*- coding: utf-8 -*-
"""
评审材料管理端点
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.technical_review import ReviewMaterial, TechnicalReview
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.technical_review import (
    ReviewMaterialCreate,
    ReviewMaterialResponse,
)

router = APIRouter()


@router.post("/technical-reviews/{review_id}/materials", response_model=ReviewMaterialResponse, status_code=status.HTTP_201_CREATED)
def create_review_material(
    review_id: int,
    material_in: ReviewMaterialCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """添加评审材料"""
    review = db.query(TechnicalReview).filter(TechnicalReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="技术评审不存在")

    material = ReviewMaterial(
        review_id=review_id,
        material_type=material_in.material_type,
        material_name=material_in.material_name,
        file_path=material_in.file_path,
        file_size=material_in.file_size,
        version=material_in.version,
        is_required=material_in.is_required,
        upload_by=current_user.id,
    )

    db.add(material)
    db.commit()
    db.refresh(material)

    return ReviewMaterialResponse(
        id=material.id,
        review_id=material.review_id,
        material_type=material.material_type,
        material_name=material.material_name,
        file_path=material.file_path,
        file_size=material.file_size,
        version=material.version,
        is_required=material.is_required,
        upload_by=material.upload_by,
        upload_at=material.upload_at,
        created_at=material.created_at,
        updated_at=material.updated_at,
    )


@router.delete("/technical-reviews/materials/{material_id}", status_code=status.HTTP_200_OK)
def delete_review_material(
    material_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """删除评审材料"""
    material = db.query(ReviewMaterial).filter(ReviewMaterial.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="评审材料不存在")

    db.delete(material)
    db.commit()

    return ResponseModel(message="评审材料已删除")

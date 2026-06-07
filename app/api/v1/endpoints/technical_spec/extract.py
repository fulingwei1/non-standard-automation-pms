# -*- coding: utf-8 -*-
"""
规格提取
"""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.technical_spec import (
    SpecExtractRequest,
    SpecExtractResponse,
)
from app.utils.spec_extractor import SpecExtractor

from .serializers import serialize_requirement

router = APIRouter()


@router.post("/requirements/extract", response_model=SpecExtractResponse)
def extract_requirements(
    extract_request: SpecExtractRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("technical_spec:read")),
) -> Any:
    """从文档中提取规格要求"""
    extractor = SpecExtractor()

    requirements = extractor.extract_from_document(
        db=db,
        document_id=extract_request.document_id,
        project_id=extract_request.project_id,
        extracted_by=current_user.id,
        auto_extract=extract_request.auto_extract,
    )

    # 构建响应
    items = []
    for req in requirements:
        items.append(serialize_requirement(req))

    return SpecExtractResponse(extracted_count=len(requirements), requirements=items)

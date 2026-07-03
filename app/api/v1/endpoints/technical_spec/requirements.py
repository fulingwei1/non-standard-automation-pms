# -*- coding: utf-8 -*-
"""
技术规格要求CRUD操作
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core import security
from app.models.project import Project
from app.models.technical_spec import TechnicalSpecRequirement
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.technical_spec import (
    TechnicalSpecRequirementCreate,
    TechnicalSpecRequirementListResponse,
    TechnicalSpecRequirementResponse,
    TechnicalSpecRequirementUpdate,
)
from app.utils.permission_helpers import (
    check_project_read_access_or_raise,
    filter_by_project_access,
)
from app.utils.spec_extractor import SpecExtractor

from .serializers import serialize_requirement

router = APIRouter()


@router.get("/requirements", response_model=TechnicalSpecRequirementListResponse)
def list_requirements(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
    project_id: Optional[int] = Query(None, description="项目ID"),
    document_id: Optional[int] = Query(None, description="文档ID"),
    material_code: Optional[str] = Query(None, description="物料编码"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    pagination: PaginationParams = Depends(get_pagination_query),
) -> Any:
    """获取技术规格要求列表"""
    query = db.query(TechnicalSpecRequirement)

    # 筛选条件
    if project_id:
        check_project_read_access_or_raise(db, current_user, project_id)
        query = query.filter(TechnicalSpecRequirement.project_id == project_id)
    else:
        query = filter_by_project_access(
            db, query, current_user, TechnicalSpecRequirement.project_id
        )
    if document_id:
        query = query.filter(TechnicalSpecRequirement.document_id == document_id)
    if material_code:
        query = query.filter(TechnicalSpecRequirement.material_code == material_code)

    # 应用关键词过滤（物料名称/规格/物料编码）
    query = apply_keyword_filter(
        query,
        TechnicalSpecRequirement,
        keyword,
        ["material_name", "specification", "material_code"],
    )

    # 总数
    total = query.count()

    # 分页
    requirements = apply_pagination(
        query.order_by(desc(TechnicalSpecRequirement.created_at)),
        pagination.offset,
        pagination.limit,
    ).all()

    # 构建响应
    items = []
    for req in requirements:
        item = serialize_requirement(req)
        items.append(item)

    return TechnicalSpecRequirementListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )


@router.get("/requirements/{requirement_id}", response_model=TechnicalSpecRequirementResponse)
def get_requirement(
    requirement_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取技术规格要求详情"""
    requirement = (
        db.query(TechnicalSpecRequirement)
        .filter(TechnicalSpecRequirement.id == requirement_id)
        .first()
    )

    if not requirement:
        raise HTTPException(status_code=404, detail="规格要求不存在")

    check_project_read_access_or_raise(db, current_user, requirement.project_id)

    return serialize_requirement(requirement)


@router.post(
    "/requirements",
    response_model=TechnicalSpecRequirementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_requirement(
    requirement_in: TechnicalSpecRequirementCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("technical_spec:create")),
) -> Any:
    """创建技术规格要求"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == requirement_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 使用提取器创建规格要求
    extractor = SpecExtractor()
    requirement = extractor.create_requirement(
        db=db,
        project_id=requirement_in.project_id,
        document_id=requirement_in.document_id,
        material_name=requirement_in.material_name,
        specification=requirement_in.specification,
        extracted_by=current_user.id,
        material_code=requirement_in.material_code,
        brand=requirement_in.brand,
        model=requirement_in.model,
        requirement_level=requirement_in.requirement_level,
        remark=requirement_in.remark,
    )

    db.commit()
    db.refresh(requirement)

    return serialize_requirement(requirement)


@router.put("/requirements/{requirement_id}", response_model=TechnicalSpecRequirementResponse)
def update_requirement(
    requirement_id: int,
    requirement_in: TechnicalSpecRequirementUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("technical_spec:update")),
) -> Any:
    """更新技术规格要求"""
    requirement = (
        db.query(TechnicalSpecRequirement)
        .filter(TechnicalSpecRequirement.id == requirement_id)
        .first()
    )

    if not requirement:
        raise HTTPException(status_code=404, detail="规格要求不存在")

    # 更新字段
    update_data = requirement_in.dict(exclude_unset=True)

    # 如果更新了规格，重新提取关键参数
    if "specification" in update_data:
        extractor = SpecExtractor()
        key_parameters = extractor.extract_key_parameters(update_data["specification"])
        if key_parameters:
            update_data["key_parameters"] = key_parameters

    for field, value in update_data.items():
        setattr(requirement, field, value)

    db.commit()
    db.refresh(requirement)

    return serialize_requirement(requirement)


@router.delete("/requirements/{requirement_id}", status_code=status.HTTP_200_OK)
def delete_requirement(
    requirement_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("technical_spec:delete")),
) -> Any:
    """删除技术规格要求"""
    requirement = (
        db.query(TechnicalSpecRequirement)
        .filter(TechnicalSpecRequirement.id == requirement_id)
        .first()
    )

    if not requirement:
        raise HTTPException(status_code=404, detail="规格要求不存在")

    db.delete(requirement)
    db.commit()
    return ResponseModel(code=200, message="技术规格要求删除成功")

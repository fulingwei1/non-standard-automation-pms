# -*- coding: utf-8 -*-
"""
技术规格要求CRUD操作
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
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
from app.utils.spec_extractor import SpecExtractor

router = APIRouter()


@router.get("/requirements", response_model=TechnicalSpecRequirementListResponse)
def list_requirements(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("technical_spec:read")),
    project_id: Optional[int] = Query(None, description="项目ID"),
    document_id: Optional[int] = Query(None, description="文档ID"),
    material_code: Optional[str] = Query(None, description="物料编码"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> Any:
    """获取技术规格要求列表"""
    query = db.query(TechnicalSpecRequirement)

    # 筛选条件
    if project_id:
        query = query.filter(TechnicalSpecRequirement.project_id == project_id)
    if document_id:
        query = query.filter(TechnicalSpecRequirement.document_id == document_id)
    if material_code:
        query = query.filter(TechnicalSpecRequirement.material_code == material_code)
    if keyword:
        query = query.filter(
            or_(
                TechnicalSpecRequirement.material_name.like(f'%{keyword}%'),
                TechnicalSpecRequirement.specification.like(f'%{keyword}%'),
                TechnicalSpecRequirement.material_code.like(f'%{keyword}%')
            )
        )

    # 总数
    total = query.count()

    # 分页
    requirements = query.order_by(desc(TechnicalSpecRequirement.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    # 构建响应
    items = []
    for req in requirements:
        item = TechnicalSpecRequirementResponse(
            id=req.id,
            project_id=req.project_id,
            document_id=req.document_id,
            material_code=req.material_code,
            material_name=req.material_name,
            specification=req.specification,
            brand=req.brand,
            model=req.model,
            key_parameters=req.key_parameters,
            requirement_level=req.requirement_level,
            remark=req.remark,
            extracted_by=req.extracted_by,
            extracted_by_name=req.extractor.name if req.extractor else None,
            created_at=req.created_at,
            updated_at=req.updated_at,
        )
        items.append(item)

    return TechnicalSpecRequirementListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/requirements/{requirement_id}", response_model=TechnicalSpecRequirementResponse)
def get_requirement(
    requirement_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("technical_spec:read")),
) -> Any:
    """获取技术规格要求详情"""
    requirement = db.query(TechnicalSpecRequirement).filter(
        TechnicalSpecRequirement.id == requirement_id
    ).first()

    if not requirement:
        raise HTTPException(status_code=404, detail="规格要求不存在")

    return TechnicalSpecRequirementResponse(
        id=requirement.id,
        project_id=requirement.project_id,
        document_id=requirement.document_id,
        material_code=requirement.material_code,
        material_name=requirement.material_name,
        specification=requirement.specification,
        brand=requirement.brand,
        model=requirement.model,
        key_parameters=requirement.key_parameters,
        requirement_level=requirement.requirement_level,
        remark=requirement.remark,
        extracted_by=requirement.extracted_by,
        extracted_by_name=requirement.extractor.name if requirement.extractor else None,
        created_at=requirement.created_at,
        updated_at=requirement.updated_at,
    )


@router.post("/requirements", response_model=TechnicalSpecRequirementResponse, status_code=status.HTTP_201_CREATED)
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
        remark=requirement_in.remark
    )

    db.commit()
    db.refresh(requirement)

    return TechnicalSpecRequirementResponse(
        id=requirement.id,
        project_id=requirement.project_id,
        document_id=requirement.document_id,
        material_code=requirement.material_code,
        material_name=requirement.material_name,
        specification=requirement.specification,
        brand=requirement.brand,
        model=requirement.model,
        key_parameters=requirement.key_parameters,
        requirement_level=requirement.requirement_level,
        remark=requirement.remark,
        extracted_by=requirement.extracted_by,
        extracted_by_name=requirement.extractor.name if requirement.extractor else None,
        created_at=requirement.created_at,
        updated_at=requirement.updated_at,
    )


@router.put("/requirements/{requirement_id}", response_model=TechnicalSpecRequirementResponse)
def update_requirement(
    requirement_id: int,
    requirement_in: TechnicalSpecRequirementUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("technical_spec:update")),
) -> Any:
    """更新技术规格要求"""
    requirement = db.query(TechnicalSpecRequirement).filter(
        TechnicalSpecRequirement.id == requirement_id
    ).first()

    if not requirement:
        raise HTTPException(status_code=404, detail="规格要求不存在")

    # 更新字段
    update_data = requirement_in.dict(exclude_unset=True)

    # 如果更新了规格，重新提取关键参数
    if 'specification' in update_data:
        extractor = SpecExtractor()
        key_parameters = extractor.extract_key_parameters(update_data['specification'])
        if key_parameters:
            update_data['key_parameters'] = key_parameters

    for field, value in update_data.items():
        setattr(requirement, field, value)

    db.commit()
    db.refresh(requirement)

    return TechnicalSpecRequirementResponse(
        id=requirement.id,
        project_id=requirement.project_id,
        document_id=requirement.document_id,
        material_code=requirement.material_code,
        material_name=requirement.material_name,
        specification=requirement.specification,
        brand=requirement.brand,
        model=requirement.model,
        key_parameters=requirement.key_parameters,
        requirement_level=requirement.requirement_level,
        remark=requirement.remark,
        extracted_by=requirement.extracted_by,
        extracted_by_name=requirement.extractor.name if requirement.extractor else None,
        created_at=requirement.created_at,
        updated_at=requirement.updated_at,
    )


@router.delete("/requirements/{requirement_id}", status_code=status.HTTP_200_OK)
def delete_requirement(
    requirement_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("technical_spec:delete")),
) -> Any:
    """删除技术规格要求"""
    requirement = db.query(TechnicalSpecRequirement).filter(
        TechnicalSpecRequirement.id == requirement_id
    ).first()

    if not requirement:
        raise HTTPException(status_code=404, detail="规格要求不存在")

    db.delete(requirement)
    db.commit()
    return ResponseModel(code=200, message="技术规格要求删除成功")

# -*- coding: utf-8 -*-
"""
技术规格管理 API endpoints
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_

from app.api import deps
from app.core import security
from app.models.technical_spec import TechnicalSpecRequirement, SpecMatchRecord
from app.models.user import User
from app.models.project import Project
from app.models.material import BomItem
from app.models.purchase import PurchaseOrderItem
from app.schemas.technical_spec import (
    TechnicalSpecRequirementCreate,
    TechnicalSpecRequirementUpdate,
    TechnicalSpecRequirementResponse,
    TechnicalSpecRequirementListResponse,
    SpecMatchRecordResponse,
    SpecMatchRecordListResponse,
    SpecMatchCheckRequest,
    SpecMatchCheckResponse,
    SpecMatchResult,
    SpecExtractRequest,
    SpecExtractResponse,
)
from app.utils.spec_extractor import SpecExtractor
from app.utils.spec_matcher import SpecMatcher

router = APIRouter()


# ==================== 技术规格要求 ====================

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
    
    return None


# ==================== 规格匹配检查 ====================

@router.post("/match/check", response_model=SpecMatchCheckResponse)
def check_spec_match(
    check_request: SpecMatchCheckRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("technical_spec:read")),
) -> Any:
    """手动触发规格匹配检查"""
    from app.models.purchase import PurchaseOrderItem
    from app.services.spec_match_service import (
        get_project_requirements,
        check_po_item_match,
        check_bom_item_match,
        check_all_po_items,
        check_all_bom_items,
        calculate_match_statistics
    )
    
    # 获取项目的所有规格要求
    requirements = get_project_requirements(db, check_request.project_id)
    
    if not requirements:
        return SpecMatchCheckResponse(
            total_checked=0,
            matched_count=0,
            mismatched_count=0,
            unknown_count=0,
            results=[]
        )
    
    matcher = SpecMatcher()
    results = []
    
    if check_request.match_type == 'PURCHASE_ORDER':
        # 检查采购订单
        if check_request.match_target_id:
            # 检查特定订单行
            po_item = db.query(PurchaseOrderItem).filter(
                PurchaseOrderItem.id == check_request.match_target_id
            ).first()
            
            if not po_item:
                raise HTTPException(status_code=404, detail="采购订单行不存在")
            
            results = check_po_item_match(
                db, po_item, requirements, check_request.project_id, matcher
            )
        else:
            # 检查所有采购订单
            results = check_all_po_items(
                db, check_request.project_id, requirements, matcher
            )
    
    elif check_request.match_type == 'BOM':
        # 检查BOM
        if check_request.match_target_id:
            # 检查特定BOM行
            bom_item = db.query(BomItem).filter(
                BomItem.id == check_request.match_target_id
            ).first()
            
            if not bom_item:
                raise HTTPException(status_code=404, detail="BOM行不存在")
            
            results = check_bom_item_match(
                db, bom_item, requirements, check_request.project_id, matcher
            )
        else:
            # 检查所有BOM行
            results = check_all_bom_items(
                db, check_request.project_id, requirements, matcher
            )
    
    db.commit()
    
    # 计算统计
    stats = calculate_match_statistics(results)
    
    return SpecMatchCheckResponse(
        total_checked=stats['total'],
        matched_count=stats['matched'],
        mismatched_count=stats['mismatched'],
        unknown_count=stats['unknown'],
        results=results
    )


def _get_match_target_name(db: Session, match_type: str, match_target_id: int) -> Optional[str]:
    """根据匹配类型获取目标名称"""
    if match_type == 'BOM':
        bom_item = db.query(BomItem).filter(BomItem.id == match_target_id).first()
        return bom_item.material_name if bom_item else None
    elif match_type == 'PURCHASE_ORDER':
        po_item = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.id == match_target_id).first()
        return po_item.material_name if po_item else None
    return None


@router.get("/match/records", response_model=SpecMatchRecordListResponse)
def list_match_records(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("technical_spec:read")),
    project_id: Optional[int] = Query(None, description="项目ID"),
    match_type: Optional[str] = Query(None, description="匹配类型"),
    match_status: Optional[str] = Query(None, description="匹配状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> Any:
    """获取规格匹配记录列表"""
    query = db.query(SpecMatchRecord)
    
    if project_id:
        query = query.filter(SpecMatchRecord.project_id == project_id)
    if match_type:
        query = query.filter(SpecMatchRecord.match_type == match_type)
    if match_status:
        query = query.filter(SpecMatchRecord.match_status == match_status)
    
    total = query.count()
    records = query.order_by(desc(SpecMatchRecord.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    items = []
    for record in records:
        items.append(SpecMatchRecordResponse(
            id=record.id,
            project_id=record.project_id,
            spec_requirement_id=record.spec_requirement_id,
            match_type=record.match_type,
            match_target_id=record.match_target_id,
            match_status=record.match_status,
            match_score=record.match_score,
            differences=record.differences,
            alert_id=record.alert_id,
            spec_requirement=TechnicalSpecRequirementResponse(
                id=record.spec_requirement.id,
                project_id=record.spec_requirement.project_id,
                document_id=record.spec_requirement.document_id,
                material_code=record.spec_requirement.material_code,
                material_name=record.spec_requirement.material_name,
                specification=record.spec_requirement.specification,
                brand=record.spec_requirement.brand,
                model=record.spec_requirement.model,
                key_parameters=record.spec_requirement.key_parameters,
                requirement_level=record.spec_requirement.requirement_level,
                remark=record.spec_requirement.remark,
                extracted_by=record.spec_requirement.extracted_by,
                extracted_by_name=record.spec_requirement.extractor.name if record.spec_requirement.extractor else None,
                created_at=record.spec_requirement.created_at,
                updated_at=record.spec_requirement.updated_at,
            ) if record.spec_requirement else None,
            match_target_name=_get_match_target_name(db, record.match_type, record.match_target_id),
            created_at=record.created_at,
            updated_at=record.updated_at,
        ))
    
    return SpecMatchRecordListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


# ==================== 规格提取 ====================

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
        auto_extract=extract_request.auto_extract
    )
    
    # 构建响应
    items = []
    for req in requirements:
        items.append(TechnicalSpecRequirementResponse(
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
        ))
    
    return SpecExtractResponse(
        extracted_count=len(requirements),
        requirements=items
    )



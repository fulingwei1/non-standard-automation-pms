# -*- coding: utf-8 -*-
"""
物料管理 API endpoints
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.material import Material, MaterialCategory, MaterialSupplier, Supplier
from app.models.shortage import MaterialSubstitution
from app.models.shortage import MaterialSubstitution
from app.schemas.material import (
    MaterialCreate,
    MaterialUpdate,
    MaterialResponse,
    MaterialCategoryCreate,
    MaterialCategoryResponse,
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[MaterialResponse])
def read_materials(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（物料编码/名称）"),
    category_id: Optional[int] = Query(None, description="分类ID筛选"),
    material_type: Optional[str] = Query(None, description="物料类型筛选"),
    is_key_material: Optional[bool] = Query(None, description="是否关键物料"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取物料列表（支持分页、搜索、筛选）
    """
    query = db.query(Material)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                Material.material_code.contains(keyword),
                Material.material_name.contains(keyword),
            )
        )
    
    # 分类筛选
    if category_id:
        query = query.filter(Material.category_id == category_id)
    
    # 物料类型筛选
    if material_type:
        query = query.filter(Material.material_type == material_type)
    
    # 关键物料筛选
    if is_key_material is not None:
        query = query.filter(Material.is_key_material == is_key_material)
    
    # 启用状态筛选
    if is_active is not None:
        query = query.filter(Material.is_active == is_active)
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    materials = query.order_by(desc(Material.created_at)).offset(offset).limit(page_size).all()
    
    # 构建响应数据
    items = []
    for material in materials:
        item = MaterialResponse(
            id=material.id,
            material_code=material.material_code,
            material_name=material.material_name,
            category_id=material.category_id,
            category_name=material.category.category_name if material.category else None,
            specification=material.specification,
            brand=material.brand,
            unit=material.unit,
            material_type=material.material_type,
            source_type=material.source_type,
            standard_price=material.standard_price or 0,
            last_price=material.last_price or 0,
            safety_stock=material.safety_stock or 0,
            current_stock=material.current_stock or 0,
            lead_time_days=material.lead_time_days or 0,
            is_key_material=material.is_key_material,
            is_active=material.is_active,
            created_at=material.created_at,
            updated_at=material.updated_at,
        )
        items.append(item)
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/{material_id}", response_model=MaterialResponse)
def read_material(
    *,
    db: Session = Depends(deps.get_db),
    material_id: int,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取物料详情
    """
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")
    
    return MaterialResponse(
        id=material.id,
        material_code=material.material_code,
        material_name=material.material_name,
        category_id=material.category_id,
        category_name=material.category.category_name if material.category else None,
        specification=material.specification,
        brand=material.brand,
        unit=material.unit,
        material_type=material.material_type,
        source_type=material.source_type,
        standard_price=material.standard_price or 0,
        last_price=material.last_price or 0,
        safety_stock=material.safety_stock or 0,
        current_stock=material.current_stock or 0,
        lead_time_days=material.lead_time_days or 0,
        is_key_material=material.is_key_material,
        is_active=material.is_active,
        created_at=material.created_at,
        updated_at=material.updated_at,
    )


@router.post("/", response_model=MaterialResponse)
def create_material(
    *,
    db: Session = Depends(deps.get_db),
    material_in: MaterialCreate,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    创建新物料
    """
    # 检查物料编码是否已存在
    material = (
        db.query(Material)
        .filter(Material.material_code == material_in.material_code)
        .first()
    )
    if material:
        raise HTTPException(
            status_code=400,
            detail="该物料编码已存在",
        )
    
    # 检查分类是否存在
    if material_in.category_id:
        category = db.query(MaterialCategory).filter(MaterialCategory.id == material_in.category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail="物料分类不存在")
    
    # 检查默认供应商是否存在
    if material_in.default_supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == material_in.default_supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=400, detail="默认供应商不存在")
    
    material = Material(**material_in.model_dump())
    material.created_by = current_user.id
    db.add(material)
    db.commit()
    db.refresh(material)
    
    return MaterialResponse(
        id=material.id,
        material_code=material.material_code,
        material_name=material.material_name,
        category_id=material.category_id,
        category_name=material.category.category_name if material.category else None,
        specification=material.specification,
        brand=material.brand,
        unit=material.unit,
        material_type=material.material_type,
        source_type=material.source_type,
        standard_price=material.standard_price or 0,
        last_price=material.last_price or 0,
        safety_stock=material.safety_stock or 0,
        current_stock=material.current_stock or 0,
        lead_time_days=material.lead_time_days or 0,
        is_key_material=material.is_key_material,
        is_active=material.is_active,
        created_at=material.created_at,
        updated_at=material.updated_at,
    )


@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(
    *,
    db: Session = Depends(deps.get_db),
    material_id: int,
    material_in: MaterialUpdate,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    更新物料信息
    """
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")
    
    # 检查分类是否存在
    if material_in.category_id is not None:
        category = db.query(MaterialCategory).filter(MaterialCategory.id == material_in.category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail="物料分类不存在")
    
    # 检查默认供应商是否存在
    if material_in.default_supplier_id is not None:
        supplier = db.query(Supplier).filter(Supplier.id == material_in.default_supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=400, detail="默认供应商不存在")
    
    update_data = material_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(material, field, value)
    
    db.add(material)
    db.commit()
    db.refresh(material)
    
    return MaterialResponse(
        id=material.id,
        material_code=material.material_code,
        material_name=material.material_name,
        category_id=material.category_id,
        category_name=material.category.category_name if material.category else None,
        specification=material.specification,
        brand=material.brand,
        unit=material.unit,
        material_type=material.material_type,
        source_type=material.source_type,
        standard_price=material.standard_price or 0,
        last_price=material.last_price or 0,
        safety_stock=material.safety_stock or 0,
        current_stock=material.current_stock or 0,
        lead_time_days=material.lead_time_days or 0,
        is_key_material=material.is_key_material,
        is_active=material.is_active,
        created_at=material.created_at,
        updated_at=material.updated_at,
    )


@router.get("/categories/", response_model=List[MaterialCategoryResponse])
def read_material_categories(
    db: Session = Depends(deps.get_db),
    parent_id: Optional[int] = Query(None, description="父分类ID，为空则返回顶级分类"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取物料分类列表
    """"""
    获取物料分类列表
    """
    query = db.query(MaterialCategory)
    
    # 父分类筛选
    if parent_id is None:
        query = query.filter(MaterialCategory.parent_id.is_(None))
    else:
        query = query.filter(MaterialCategory.parent_id == parent_id)
    
    # 启用状态筛选
    if is_active is not None:
        query = query.filter(MaterialCategory.is_active == is_active)
    
    categories = query.order_by(MaterialCategory.sort_order, MaterialCategory.category_code).all()
    
    # 构建树形结构
    def build_tree(category_list, parent_id=None):
        result = []
        for cat in category_list:
            if (parent_id is None and cat.parent_id is None) or (parent_id and cat.parent_id == parent_id):
                children = build_tree(category_list, cat.id)
                item = MaterialCategoryResponse(
                    id=cat.id,
                    category_code=cat.category_code,
                    category_name=cat.category_name,
                    parent_id=cat.parent_id,
                    level=cat.level,
                    full_path=cat.full_path,
                    is_active=cat.is_active,
                    children=children,
                    created_at=cat.created_at,
                    updated_at=cat.updated_at,
                )
                result.append(item)
        return result
    
    return build_tree(categories)


@router.get("/{material_id}/suppliers", response_model=List)
def get_material_suppliers(
    *,
    db: Session = Depends(deps.get_db),
    material_id: int,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取物料的供应商列表
    """
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")
    
    # 查询物料供应商关联
    material_suppliers = (
        db.query(MaterialSupplier)
        .filter(MaterialSupplier.material_id == material_id)
        .filter(MaterialSupplier.is_active == True)
        .all()
    )
    
    result = []
    for ms in material_suppliers:
        supplier = ms.supplier
        result.append({
            "id": supplier.id,
            "supplier_code": supplier.supplier_code,
            "supplier_name": supplier.supplier_name,
            "price": float(ms.price) if ms.price else 0,
            "currency": ms.currency,
            "lead_time_days": ms.lead_time_days,
            "min_order_qty": float(ms.min_order_qty) if ms.min_order_qty else 0,
            "is_preferred": ms.is_preferred,
            "supplier_material_code": ms.supplier_material_code,
        })
    
    return result


@router.get("/{material_id}/alternatives", response_model=dict)
def get_material_alternatives(
    *,
    db: Session = Depends(deps.get_db),
    material_id: int,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取物料的替代关系
    返回该物料可以作为替代物料的所有原物料，以及该物料的所有替代物料
    """
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")
    
    # 查询该物料作为替代物料的所有替代记录（即哪些物料可以用该物料替代）
    as_substitute = (
        db.query(MaterialSubstitution)
        .filter(MaterialSubstitution.substitute_material_id == material_id)
        .filter(MaterialSubstitution.status.in_(['APPROVED', 'EXECUTED']))
        .all()
    )
    
    # 查询该物料作为原物料的所有替代记录（即该物料可以用哪些物料替代）
    as_original = (
        db.query(MaterialSubstitution)
        .filter(MaterialSubstitution.original_material_id == material_id)
        .filter(MaterialSubstitution.status.in_(['APPROVED', 'EXECUTED']))
        .all()
    )
    
    # 构建替代物料列表（该物料可以替代的物料）
    can_substitute_for = []
    for sub in as_substitute:
        original_material = db.query(Material).filter(Material.id == sub.original_material_id).first()
        if original_material:
            can_substitute_for.append({
                "material_id": original_material.id,
                "material_code": original_material.material_code,
                "material_name": original_material.material_name,
                "specification": original_material.specification,
                "substitution_ratio": float(sub.substitute_qty / sub.original_qty) if sub.original_qty > 0 else 1.0,
                "substitution_reason": sub.substitution_reason,
                "status": sub.status,
                "substitution_no": sub.substitution_no,
            })
    
    # 构建可替代该物料的物料列表
    can_be_substituted_by = []
    for sub in as_original:
        substitute_material = db.query(Material).filter(Material.id == sub.substitute_material_id).first()
        if substitute_material:
            can_be_substituted_by.append({
                "material_id": substitute_material.id,
                "material_code": substitute_material.material_code,
                "material_name": substitute_material.material_name,
                "specification": substitute_material.specification,
                "substitution_ratio": float(sub.substitute_qty / sub.original_qty) if sub.original_qty > 0 else 1.0,
                "substitution_reason": sub.substitution_reason,
                "status": sub.status,
                "substitution_no": sub.substitution_no,
            })
    
    return {
        "material_id": material.id,
        "material_code": material.material_code,
        "material_name": material.material_name,
        "can_substitute_for": can_substitute_for,  # 该物料可以替代的物料
        "can_be_substituted_by": can_be_substituted_by,  # 可以替代该物料的物料
    }

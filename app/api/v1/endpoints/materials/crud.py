# -*- coding: utf-8 -*-
"""
物料CRUD端点
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.material import Material, MaterialCategory, Supplier
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.material import (
    MaterialCreate,
    MaterialResponse,
    MaterialUpdate,
)

router = APIRouter()


def _build_material_response(material: Material) -> MaterialResponse:
    """构建物料响应对象"""
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
    """获取物料列表（支持分页、搜索、筛选）"""
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
    items = [_build_material_response(m) for m in materials]

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
    """获取物料详情"""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    return _build_material_response(material)


@router.post("/", response_model=MaterialResponse)
def create_material(
    *,
    db: Session = Depends(deps.get_db),
    material_in: MaterialCreate,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    创建新物料

    如果未提供物料编码，系统将根据物料类别自动生成 MAT-{类别}-xxxxx 格式的编码
    """
    from app.utils.number_generator import generate_material_code

    # 检查分类是否存在
    category_code = None
    if material_in.category_id:
        category = db.query(MaterialCategory).filter(MaterialCategory.id == material_in.category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail="物料分类不存在")
        category_code = category.category_code

    # 如果没有提供物料编码，自动生成
    material_data = material_in.model_dump()
    if not material_data.get('material_code'):
        material_data['material_code'] = generate_material_code(db, category_code)

    # 检查物料编码是否已存在
    material = (
        db.query(Material)
        .filter(Material.material_code == material_data['material_code'])
        .first()
    )
    if material:
        raise HTTPException(
            status_code=400,
            detail="该物料编码已存在",
        )

    # 检查默认供应商是否存在
    if material_data.get('default_supplier_id'):
        supplier = db.query(Supplier).filter(Supplier.id == material_data['default_supplier_id']).first()
        if not supplier:
            raise HTTPException(status_code=400, detail="默认供应商不存在")

    material = Material(**material_data)
    material.created_by = current_user.id
    db.add(material)
    db.commit()
    db.refresh(material)

    return _build_material_response(material)


@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(
    *,
    db: Session = Depends(deps.get_db),
    material_id: int,
    material_in: MaterialUpdate,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """更新物料信息"""
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

    return _build_material_response(material)

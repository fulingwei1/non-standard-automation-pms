from typing import Any, List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.material import Supplier, MaterialSupplier, Material
from app.schemas.material import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[SupplierResponse])
def read_suppliers(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（供应商名称/编码）"),
    supplier_type: Optional[str] = Query(None, description="供应商类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    supplier_level: Optional[str] = Query(None, description="供应商等级筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取供应商列表（支持分页、搜索、筛选）
    """
    query = db.query(Supplier)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                Supplier.supplier_name.contains(keyword),
                Supplier.supplier_code.contains(keyword),
                Supplier.supplier_short_name.contains(keyword),
            )
        )
    
    # 供应商类型筛选
    if supplier_type:
        query = query.filter(Supplier.supplier_type == supplier_type)
    
    # 状态筛选
    if status:
        query = query.filter(Supplier.status == status)
    
    # 等级筛选
    if supplier_level:
        query = query.filter(Supplier.supplier_level == supplier_level)
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    suppliers = query.order_by(desc(Supplier.created_at)).offset(offset).limit(page_size).all()
    
    return PaginatedResponse(
        items=suppliers,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/{supplier_id}", response_model=SupplierResponse)
def read_supplier(
    *,
    db: Session = Depends(deps.get_db),
    supplier_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取供应商详情
    """
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    return supplier


@router.post("/", response_model=SupplierResponse)
def create_supplier(
    *,
    db: Session = Depends(deps.get_db),
    supplier_in: SupplierCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建新供应商
    """
    # 检查供应商编码是否已存在
    supplier = (
        db.query(Supplier)
        .filter(Supplier.supplier_code == supplier_in.supplier_code)
        .first()
    )
    if supplier:
        raise HTTPException(
            status_code=400,
            detail="该供应商编码已存在",
        )

    supplier = Supplier(**supplier_in.model_dump())
    supplier.created_by = current_user.id
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    *,
    db: Session = Depends(deps.get_db),
    supplier_id: int,
    supplier_in: SupplierUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新供应商信息
    """
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")

    update_data = supplier_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)

    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.put("/{supplier_id}/rating", response_model=SupplierResponse)
def update_supplier_rating(
    *,
    db: Session = Depends(deps.get_db),
    supplier_id: int,
    quality_rating: Optional[Decimal] = Query(None, ge=0, le=5, description="质量评分"),
    delivery_rating: Optional[Decimal] = Query(None, ge=0, le=5, description="交期评分"),
    service_rating: Optional[Decimal] = Query(None, ge=0, le=5, description="服务评分"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新供应商评级
    """
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")

    # 更新各项评分
    if quality_rating is not None:
        supplier.quality_rating = quality_rating
    if delivery_rating is not None:
        supplier.delivery_rating = delivery_rating
    if service_rating is not None:
        supplier.service_rating = service_rating

    # 计算综合评分（简单平均）
    ratings = []
    if supplier.quality_rating:
        ratings.append(float(supplier.quality_rating))
    if supplier.delivery_rating:
        ratings.append(float(supplier.delivery_rating))
    if supplier.service_rating:
        ratings.append(float(supplier.service_rating))
    
    if ratings:
        supplier.overall_rating = Decimal(sum(ratings) / len(ratings))
        
        # 根据综合评分确定等级
        avg_rating = float(supplier.overall_rating)
        if avg_rating >= 4.5:
            supplier.supplier_level = 'A'
        elif avg_rating >= 3.5:
            supplier.supplier_level = 'B'
        elif avg_rating >= 2.5:
            supplier.supplier_level = 'C'
        else:
            supplier.supplier_level = 'D'

    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/{supplier_id}/materials", response_model=PaginatedResponse)
def get_supplier_materials(
    *,
    db: Session = Depends(deps.get_db),
    supplier_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取供应商的物料列表
    """
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 通过MaterialSupplier关联表查询
    query = (
        db.query(Material)
        .join(MaterialSupplier, Material.id == MaterialSupplier.material_id)
        .filter(MaterialSupplier.supplier_id == supplier_id)
    )
    
    total = query.count()
    offset = (page - 1) * page_size
    materials = query.order_by(desc(Material.created_at)).offset(offset).limit(page_size).all()
    
    return PaginatedResponse(
        items=materials,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


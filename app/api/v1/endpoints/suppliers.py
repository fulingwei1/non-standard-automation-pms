from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.material import Material, MaterialSupplier, Supplier
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.material import (
    SupplierCreate,
    SupplierResponse,
    SupplierUpdate,
)

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
    current_user: User = Depends(security.require_permission("supplier:read")),
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

    # 总数 - 使用独立的查询避免连接问题
    total = query.count()

    # 分页 - 确保 offset 和 limit 都是有效的整数
    offset = max(0, (page - 1) * page_size)
    page_size_int = max(1, int(page_size))

    # 重新构建查询对象以避免 SQLite 连接问题
    suppliers_query = db.query(Supplier)

    # 重新应用所有筛选条件
    if keyword:
        suppliers_query = suppliers_query.filter(
            or_(
                Supplier.supplier_name.contains(keyword),
                Supplier.supplier_code.contains(keyword),
                Supplier.supplier_short_name.contains(keyword),
            )
        )
    if supplier_type:
        suppliers_query = suppliers_query.filter(Supplier.supplier_type == supplier_type)
    if status:
        suppliers_query = suppliers_query.filter(Supplier.status == status)
    if supplier_level:
        suppliers_query = suppliers_query.filter(Supplier.supplier_level == supplier_level)

    # 应用排序和分页
    suppliers_query = suppliers_query.order_by(desc(Supplier.created_at))
    if offset > 0:
        suppliers_query = suppliers_query.offset(offset)
    suppliers = suppliers_query.limit(page_size_int).all()

    # 手动构建响应对象，确保 Decimal 类型正确处理
    items = []
    for supplier in suppliers:
        items.append(SupplierResponse(
            id=supplier.id,
            supplier_code=supplier.supplier_code,
            supplier_name=supplier.supplier_name,
            supplier_short_name=supplier.supplier_short_name,
            supplier_type=supplier.supplier_type,
            contact_person=supplier.contact_person,
            contact_phone=supplier.contact_phone,
            contact_email=supplier.contact_email,
            address=supplier.address,
            quality_rating=supplier.quality_rating or Decimal("0"),
            delivery_rating=supplier.delivery_rating or Decimal("0"),
            service_rating=supplier.service_rating or Decimal("0"),
            overall_rating=supplier.overall_rating or Decimal("0"),
            supplier_level=supplier.supplier_level or "B",
            status=supplier.status or "ACTIVE",
            cooperation_start=supplier.cooperation_start,
            last_order_date=supplier.last_order_date,
            created_at=supplier.created_at,
            updated_at=supplier.updated_at
        ))

    return PaginatedResponse(
        items=items,
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
    current_user: User = Depends(security.require_permission("supplier:read")),
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
    current_user: User = Depends(security.require_permission("supplier:create")),
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
    current_user: User = Depends(security.require_permission("supplier:read")),
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
    current_user: User = Depends(security.require_permission("supplier:read")),
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
    current_user: User = Depends(security.require_permission("supplier:read")),
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


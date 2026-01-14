# -*- coding: utf-8 -*-
"""
物料管理 API endpoints
"""
from typing import Any, List, Optional
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

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
    WarehouseStatistics,
    MaterialSearchResponse,
    SupplierResponse,
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
    
    如果未提供物料编码，系统将根据物料类别自动生成 MAT-{类别}-xxxxx 格式的编码
    """
    from app.utils.number_generator import generate_material_code
    
    # 检查分类是否存在
    category = None
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


@router.get("/suppliers", response_model=PaginatedResponse[SupplierResponse])
def get_suppliers(
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
    此路由作为 /suppliers 的快捷方式，用于物料管理模块中获取供应商列表
    """
    from decimal import Decimal
    
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


# ==================== 仓储统计 ====================

@router.get("/warehouse/statistics", response_model=WarehouseStatistics)
def get_warehouse_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    仓储统计（给生产总监看）
    """
    from app.models.purchase import PurchaseOrder, PurchaseOrderItem, GoodsReceiptItem
    from app.models.production import WorkOrder
    
    # 库存SKU统计
    total_items = db.query(Material).count()
    in_stock_items = db.query(Material).filter(
        Material.current_stock > 0
    ).count()
    
    # 低库存预警（当前库存 < 安全库存）
    low_stock_items = db.query(Material).filter(
        Material.current_stock < Material.safety_stock,
        Material.current_stock > 0
    ).count()
    
    # 缺货
    out_of_stock_items = db.query(Material).filter(
        Material.current_stock <= 0
    ).count()
    
    # 库存周转率（简化计算：本月入库金额 / 平均库存金额）
    today = date.today()
    month_start = date(today.year, today.month, 1)
    
    # 本月入库金额（从入库单计算）
    inbound_amount = db.query(func.sum(GoodsReceiptItem.amount)).filter(
        GoodsReceiptItem.created_at >= datetime.combine(month_start, datetime.min.time())
    ).scalar() or 0
    
    # 平均库存金额（简化：当前库存金额）
    avg_inventory_amount = db.query(func.sum(
        Material.current_stock * Material.standard_price
    )).scalar() or 0
    
    inventory_turnover = 0.0
    if avg_inventory_amount and avg_inventory_amount > 0:
        inventory_turnover = float(inbound_amount) / float(avg_inventory_amount)

    # 仓储利用率计算
    # 基于物料的体积和数量估算占用的仓储空间
    total_volume = 0
    materials = db.query(Material).filter(Material.is_active == True).all()
    for material in materials:
        stock = float(material.current_stock or 0)
        # 假设每个物料单位占用基础体积，可以根据物料规格调整
        unit_volume = 1.0
        # 大件物料占用更多空间
        if material.material_type in ["大型设备", "机架", "机柜"]:
            unit_volume = 10.0
        elif material.material_type in ["板材", "型材"]:
            unit_volume = 3.0
        elif material.material_type in ["电子元件", "标准件"]:
            unit_volume = 0.1
        total_volume += stock * unit_volume

    # 假设仓库总容量为 10000 单位体积（可根据实际仓库配置调整）
    total_warehouse_capacity = 10000.0
    warehouse_utilization = min(100.0, (total_volume / total_warehouse_capacity) * 100) if total_warehouse_capacity > 0 else 0

    # 待入库（已采购但未完全到货的订单）
    pending_inbound = db.query(PurchaseOrder).filter(
        PurchaseOrder.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED"])
    ).count()
    
    # 待出库（从工单领料需求计算）
    pending_outbound = db.query(WorkOrder).filter(
        WorkOrder.status.in_(["ASSIGNED", "STARTED"]),
        # 假设有领料状态字段
    ).count()
    
    return WarehouseStatistics(
        total_items=total_items,
        in_stock_items=in_stock_items,
        low_stock_items=low_stock_items,
        out_of_stock_items=out_of_stock_items,
        inventory_turnover=inventory_turnover,
        warehouse_utilization=warehouse_utilization,
        pending_inbound=pending_inbound,
        pending_outbound=pending_outbound,
    )


# ==================== 物料查找 ====================

@router.get("/search", response_model=PaginatedResponse[MaterialSearchResponse])
def search_materials(
    db: Session = Depends(deps.get_db),
    keyword: str = Query(..., description="搜索关键词（物料编码/名称/规格）"),
    has_stock: Optional[bool] = Query(None, description="是否有库存"),
    category: Optional[str] = Query(None, description="物料类别"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    物料查找（支持编码/名称/规格搜索）
    """
    from app.models.purchase import PurchaseOrderItem, PurchaseOrder
    
    query = db.query(Material)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                Material.material_code.like(f"%{keyword}%"),
                Material.material_name.like(f"%{keyword}%"),
                Material.specification.like(f"%{keyword}%")
            )
        )
    
    # 库存筛选
    if has_stock is not None:
        if has_stock:
            query = query.filter(Material.current_stock > 0)
        else:
            query = query.filter(Material.current_stock <= 0)
    
    # 类别筛选
    if category:
        query = query.join(MaterialCategory).filter(
            MaterialCategory.category_name == category
        )
    
    # 分页
    total = query.count()
    materials = query.offset((page - 1) * page_size).limit(page_size).all()
    
    items = []
    for material in materials:
        # 计算在途数量
        in_transit_qty = db.query(func.sum(
            PurchaseOrderItem.quantity - PurchaseOrderItem.received_qty
        )).join(
            PurchaseOrder, PurchaseOrderItem.po_id == PurchaseOrder.id
        ).filter(
            PurchaseOrderItem.material_id == material.id,
            PurchaseOrder.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED"])
        ).scalar() or 0
        
        # 可用数量 = 当前库存 + 在途数量
        available_qty = (material.current_stock or 0) + in_transit_qty
        
        # 获取供应商名称
        supplier_name = None
        if material.default_supplier_id:
            supplier = db.query(Supplier).filter(Supplier.id == material.default_supplier_id).first()
            supplier_name = supplier.supplier_name if supplier else None
        
        items.append(MaterialSearchResponse(
            material_id=material.id,
            material_code=material.material_code,
            material_name=material.material_name,
            specification=material.specification,
            category=material.category.category_name if material.category else None,
            current_stock=float(material.current_stock or 0),
            safety_stock=float(material.safety_stock or 0),
            in_transit_qty=float(in_transit_qty),
            available_qty=float(available_qty),
            unit=material.unit or "件",
            unit_price=float(material.standard_price or 0),
            supplier_name=supplier_name,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )

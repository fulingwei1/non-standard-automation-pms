# -*- coding: utf-8 -*-
"""
外协供应商 - 自动生成
从 outsourcing.py 拆分
"""

# -*- coding: utf-8 -*-
"""
外协管理 API endpoints
包含：外协供应商、外协订单、交付与质检、进度与付款
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

logger = logging.getLogger(__name__)
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.query_filters import apply_keyword_filter
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.outsourcing import (
    OutsourcingDelivery,
    OutsourcingDeliveryItem,
    OutsourcingEvaluation,
    OutsourcingInspection,
    OutsourcingOrder,
    OutsourcingOrderItem,
    OutsourcingPayment,
    OutsourcingProgress,
)
from app.models.vendor import Vendor
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.outsourcing import (
    OutsourcingDeliveryCreate,
    OutsourcingDeliveryResponse,
    OutsourcingInspectionCreate,
    OutsourcingInspectionResponse,
    OutsourcingOrderCreate,
    OutsourcingOrderItemCreate,
    OutsourcingOrderItemResponse,
    OutsourcingOrderListResponse,
    OutsourcingOrderResponse,
    OutsourcingOrderUpdate,
    OutsourcingPaymentCreate,
    OutsourcingPaymentResponse,
    OutsourcingPaymentUpdate,
    OutsourcingProgressCreate,
    OutsourcingProgressResponse,
    VendorCreate,
    VendorResponse,
    VendorUpdate,
)

router = APIRouter()

# 使用统一的编码生成工具
from app.utils.domain_codes import outsourcing as outsourcing_codes

generate_order_no = outsourcing_codes.generate_order_no
generate_delivery_no = outsourcing_codes.generate_delivery_no
generate_inspection_no = outsourcing_codes.generate_inspection_no


# NOTE: keep flat routes (no extra prefix) to preserve the original API paths.
# 共 5 个路由

# ==================== 外协供应商 ====================

@router.get("/outsourcing-vendors", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_vendors(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（编码/名称）"),
    vendor_type: Optional[str] = Query(None, description="外协商类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取外协商列表
    """
    query = db.query(Vendor).filter(Vendor.vendor_type == 'OUTSOURCING')

    query = apply_keyword_filter(query, Vendor, keyword, ["supplier_code", "supplier_name"])

    if vendor_type:
        query = query.filter(Vendor.supplier_type == vendor_type)

    if status:
        query = query.filter(Vendor.status == status)

    total = query.count()
    vendors = query.order_by(Vendor.created_at).offset(pagination.offset).limit(pagination.limit).all()

    items = []
    for vendor in vendors:
        items.append(VendorResponse(
            id=vendor.id,
            vendor_code=vendor.supplier_code,
            vendor_name=vendor.supplier_name,
            vendor_short_name=vendor.supplier_short_name,
            vendor_type=vendor.vendor_type,
            contact_person=vendor.contact_person,
            contact_phone=vendor.contact_phone,
            quality_rating=vendor.quality_rating or Decimal("0"),
            delivery_rating=vendor.delivery_rating or Decimal("0"),
            service_rating=vendor.service_rating or Decimal("0"),
            overall_rating=vendor.overall_rating or Decimal("0"),
            status=vendor.status,
            cooperation_start=vendor.cooperation_start,
            last_order_date=vendor.last_order_date,
            created_at=vendor.created_at,
            updated_at=vendor.updated_at
        ))

    return pagination.to_response(items, total)


@router.get("/outsourcing-vendors/{vendor_id}", response_model=VendorResponse, status_code=status.HTTP_200_OK)
def read_vendor(
    vendor_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取外协商详情
    """
    vendor = db.query(Vendor).filter(
        Vendor.id == vendor_id,
        Vendor.vendor_type == 'OUTSOURCING'
    ).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="外协商不存在")

    return VendorResponse(
        id=vendor.id,
        vendor_code=vendor.supplier_code,
        vendor_name=vendor.supplier_name,
        vendor_short_name=vendor.supplier_short_name,
        vendor_type=vendor.vendor_type,
        contact_person=vendor.contact_person,
        contact_phone=vendor.contact_phone,
        quality_rating=vendor.quality_rating or Decimal("0"),
        delivery_rating=vendor.delivery_rating or Decimal("0"),
        service_rating=vendor.service_rating or Decimal("0"),
        overall_rating=vendor.overall_rating or Decimal("0"),
        status=vendor.status,
        cooperation_start=vendor.cooperation_start,
        last_order_date=vendor.last_order_date,
        created_at=vendor.created_at,
        updated_at=vendor.updated_at
    )


@router.post("/outsourcing-vendors", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
def create_vendor(
    *,
    db: Session = Depends(deps.get_db),
    vendor_in: VendorCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建外协商
    """
    # 检查编码是否已存在
    existing = db.query(Vendor).filter(
        Vendor.supplier_code == vendor_in.vendor_code,
        Vendor.vendor_type == 'OUTSOURCING'
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="外协商编码已存在")

    vendor = Vendor(
        supplier_code=vendor_in.vendor_code,
        supplier_name=vendor_in.vendor_name,
        supplier_short_name=vendor_in.vendor_short_name,
        vendor_type='OUTSOURCING',
        supplier_type=vendor_in.vendor_type,
        contact_person=vendor_in.contact_person,
        contact_phone=vendor_in.contact_phone,
        contact_email=vendor_in.contact_email,
        address=vendor_in.address,
        business_license=vendor_in.business_license,
        qualification=vendor_in.qualification,
        capabilities=vendor_in.capabilities,
        bank_name=vendor_in.bank_name,
        bank_account=vendor_in.bank_account,
        tax_number=vendor_in.tax_number,
        status="ACTIVE",
        created_by=current_user.id,
        remark=vendor_in.remark
    )

    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    return read_vendor(vendor.id, db, current_user)


@router.put("/outsourcing-vendors/{vendor_id}", response_model=VendorResponse, status_code=status.HTTP_200_OK)
def update_vendor(
    *,
    db: Session = Depends(deps.get_db),
    vendor_id: int,
    vendor_in: VendorUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新外协商
    """
    vendor = db.query(Vendor).filter(
        Vendor.id == vendor_id,
        Vendor.vendor_type == 'OUTSOURCING'
    ).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="外协商不存在")

    update_data = vendor_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vendor, field, value)

    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    return read_vendor(vendor_id, db, current_user)


@router.post("/outsourcing-vendors/{vendor_id}/evaluations", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_vendor_evaluation(
    *,
    db: Session = Depends(deps.get_db),
    vendor_id: int,
    quality_rating: Decimal = Query(..., ge=0, le=5, description="质量评分"),
    delivery_rating: Decimal = Query(..., ge=0, le=5, description="交期评分"),
    service_rating: Decimal = Query(..., ge=0, le=5, description="服务评分"),
    eval_period: Optional[str] = Query(None, description="评价周期（如：2025-01）"),
    remark: Optional[str] = Query(None, description="评价备注"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    外协商评价
    """
    vendor = db.query(Vendor).filter(
        Vendor.id == vendor_id,
        Vendor.vendor_type == 'OUTSOURCING'
    ).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="外协商不存在")

    # 计算综合评分（简单平均）
    overall_rating = (quality_rating + delivery_rating + service_rating) / 3

    # 更新外协商评分（取最近评价的平均值或直接更新）
    vendor.quality_rating = quality_rating
    vendor.delivery_rating = delivery_rating
    vendor.service_rating = service_rating
    vendor.overall_rating = overall_rating

    # 创建评价记录
    evaluation = OutsourcingEvaluation(
        vendor_id=vendor_id,
        eval_period=eval_period or datetime.now().strftime("%Y-%m"),
        quality_score=quality_rating,
        delivery_score=delivery_rating,
        service_score=service_rating,
        overall_score=overall_rating,
        evaluator_id=current_user.id,
        evaluated_at=datetime.now(),
        remark=remark
    )

    db.add(vendor)
    db.add(evaluation)
    db.commit()

    return ResponseModel(message="评价成功")



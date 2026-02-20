# -*- coding: utf-8 -*-
"""
智能采购管理 API

提供10个核心接口:
1. GET /purchase/suggestions - 采购建议列表
2. POST /purchase/suggestions/{id}/approve - 批准建议
3. GET /purchase/suppliers/{id}/performance - 供应商绩效
4. POST /purchase/suppliers/{id}/evaluate - 触发评估
5. GET /purchase/suppliers/ranking - 供应商排名
6. POST /purchase/quotations - 创建报价
7. GET /purchase/quotations/compare - 比价
8. GET /purchase/orders/{id}/tracking - 订单跟踪
9. POST /purchase/orders/{id}/receive - 收货确认
10. POST /purchase/suggestions/{id}/create-order - 建议转订单
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import User, Vendor
from app.schemas.purchase_intelligence import (
    CreateOrderFromSuggestionRequest,
    MessageResponse,
    PurchaseOrderReceiveRequest,
    PurchaseOrderTrackingResponse,
    PurchaseSuggestionApprove,
    PurchaseSuggestionResponse,
    QuotationCompareResponse,
    SupplierPerformanceCalculate,
    SupplierPerformanceResponse,
    SupplierQuotationCreate,
    SupplierQuotationResponse,
    SupplierRankingResponse,
)
from app.services.purchase_intelligence import PurchaseIntelligenceService
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== 1. 采购建议列表 ====================


@router.get("/suggestions", response_model=List[PurchaseSuggestionResponse])
def get_purchase_suggestions(
    status: Optional[str] = None,
    source_type: Optional[str] = None,
    material_id: Optional[int] = None,
    project_id: Optional[int] = None,
    urgency_level: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取采购建议列表

    支持筛选条件:
    - status: 状态（PENDING/APPROVED/REJECTED/ORDERED）
    - source_type: 来源类型（SHORTAGE/SAFETY_STOCK/FORECAST/MANUAL）
    - material_id: 物料ID
    - project_id: 项目ID
    - urgency_level: 紧急程度（LOW/NORMAL/HIGH/URGENT）
    """
    service = PurchaseIntelligenceService(db)
    return service.get_purchase_suggestions(
        status=status,
        source_type=source_type,
        material_id=material_id,
        project_id=project_id,
        urgency_level=urgency_level,
        skip=skip,
        limit=limit,
    )


# ==================== 2. 批准建议 ====================


@router.post("/suggestions/{suggestion_id}/approve", response_model=MessageResponse)
def approve_purchase_suggestion(
    suggestion_id: int,
    approve_data: PurchaseSuggestionApprove,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批准或拒绝采购建议"""
    service = PurchaseIntelligenceService(db)

    try:
        suggestion, message = service.approve_purchase_suggestion(
            suggestion_id=suggestion_id,
            approved=approve_data.approved,
            user_id=current_user.id,
            review_note=approve_data.review_note,
            suggested_supplier_id=approve_data.suggested_supplier_id,
        )
        return MessageResponse(message=message, data={"suggestion_id": suggestion_id})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 3. 供应商绩效 ====================


@router.get(
    "/suppliers/{supplier_id}/performance",
    response_model=List[SupplierPerformanceResponse],
)
def get_supplier_performance(
    supplier_id: int,
    evaluation_period: Optional[str] = None,
    limit: int = Query(12, ge=1, le=24),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取供应商绩效记录

    Args:
        supplier_id: 供应商ID
        evaluation_period: 评估期间（可选，格式：YYYY-MM）
        limit: 返回记录数
    """
    service = PurchaseIntelligenceService(db)
    return service.get_supplier_performance(
        supplier_id=supplier_id,
        evaluation_period=evaluation_period,
        limit=limit,
    )


# ==================== 4. 触发评估 ====================


@router.post(
    "/suppliers/{supplier_id}/evaluate", response_model=SupplierPerformanceResponse
)
def evaluate_supplier_performance(
    supplier_id: int,
    evaluate_data: SupplierPerformanceCalculate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """触发供应商绩效评估"""
    service = PurchaseIntelligenceService(db)

    try:
        performance = service.evaluate_supplier_performance(
            supplier_id=supplier_id,
            evaluation_period=evaluate_data.evaluation_period,
            weight_config=evaluate_data.weight_config,
        )
        return SupplierPerformanceResponse.from_orm(performance)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 5. 供应商排名 ====================


@router.get("/suppliers/ranking", response_model=SupplierRankingResponse)
def get_supplier_ranking(
    evaluation_period: str = Query(..., description="评估期间 YYYY-MM"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取供应商排名"""
    service = PurchaseIntelligenceService(db)
    rankings, total_suppliers = service.get_supplier_ranking(
        evaluation_period=evaluation_period,
        limit=limit,
    )

    return SupplierRankingResponse(
        evaluation_period=evaluation_period,
        total_suppliers=total_suppliers,
        rankings=rankings,
    )


# ==================== 6. 创建报价 ====================


@router.post(
    "/quotations",
    response_model=SupplierQuotationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_supplier_quotation(
    quotation_data: SupplierQuotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建供应商报价"""
    service = PurchaseIntelligenceService(db)

    try:
        quotation = service.create_supplier_quotation(
            supplier_id=quotation_data.supplier_id,
            material_id=quotation_data.material_id,
            unit_price=quotation_data.unit_price,
            currency=quotation_data.currency,
            min_order_qty=quotation_data.min_order_qty,
            lead_time_days=quotation_data.lead_time_days,
            valid_from=quotation_data.valid_from,
            valid_to=quotation_data.valid_to,
            user_id=current_user.id,
            payment_terms=quotation_data.payment_terms,
            warranty_period=quotation_data.warranty_period,
            tax_rate=quotation_data.tax_rate,
            remark=quotation_data.remark,
        )

        # 填充响应数据
        supplier = db.query(Vendor).get(quotation_data.supplier_id)
        response = SupplierQuotationResponse.from_orm(quotation)
        if supplier:
            response.supplier_code = supplier.supplier_code
            response.supplier_name = supplier.supplier_name

        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== 7. 比价 ====================


@router.get("/quotations/compare", response_model=QuotationCompareResponse)
def compare_quotations(
    material_id: int = Query(..., description="物料ID"),
    supplier_ids: Optional[str] = Query(None, description="供应商ID列表，逗号分隔"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """比较供应商报价"""
    service = PurchaseIntelligenceService(db)

    # 解析供应商ID列表
    supplier_id_list = None
    if supplier_ids:
        supplier_id_list = [int(s) for s in supplier_ids.split(',')]

    try:
        (
            material,
            compare_items,
            best_price_supplier_id,
            recommended_supplier_id,
            recommendation_reason,
        ) = service.compare_quotations(
            material_id=material_id,
            supplier_ids=supplier_id_list,
        )

        return QuotationCompareResponse(
            material_id=material_id,
            material_code=material.material_code,
            material_name=material.material_name,
            quotations=compare_items,
            best_price_supplier_id=best_price_supplier_id,
            recommended_supplier_id=recommended_supplier_id,
            recommendation_reason=recommendation_reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== 8. 订单跟踪 ====================


@router.get(
    "/orders/{order_id}/tracking",
    response_model=List[PurchaseOrderTrackingResponse],
)
def get_purchase_order_tracking(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取采购订单跟踪记录"""
    service = PurchaseIntelligenceService(db)

    try:
        return service.get_purchase_order_tracking(order_id=order_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== 9. 收货确认 ====================


@router.post("/orders/{order_id}/receive", response_model=MessageResponse)
def receive_purchase_order(
    order_id: int,
    receive_data: PurchaseOrderReceiveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """收货确认"""
    service = PurchaseIntelligenceService(db)

    try:
        receipt, receipt_no = service.receive_purchase_order(
            order_id=order_id,
            receipt_date=receive_data.receipt_date,
            items=receive_data.items,
            user_id=current_user.id,
            delivery_note_no=receive_data.delivery_note_no,
            logistics_company=receive_data.logistics_company,
            tracking_no=receive_data.tracking_no,
            remark=receive_data.remark,
        )

        return MessageResponse(
            message="收货确认成功",
            data={"receipt_id": receipt.id, "receipt_no": receipt_no},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== 10. 建议转订单 ====================


@router.post("/suggestions/{suggestion_id}/create-order", response_model=MessageResponse)
def create_order_from_suggestion(
    suggestion_id: int,
    order_data: CreateOrderFromSuggestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从采购建议创建采购订单"""
    service = PurchaseIntelligenceService(db)

    try:
        order, order_no = service.create_order_from_suggestion(
            suggestion_id=suggestion_id,
            user_id=current_user.id,
            supplier_id=order_data.supplier_id,
            required_date=order_data.required_date,
            payment_terms=order_data.payment_terms,
            delivery_address=order_data.delivery_address,
            remark=order_data.remark,
        )

        return MessageResponse(
            message="采购订单创建成功",
            data={"order_id": order.id, "order_no": order_no},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

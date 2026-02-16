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
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import (
    GoodsReceipt,
    GoodsReceiptItem,
    Material,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseSuggestion,
    SupplierPerformance,
    SupplierQuotation,
    User,
    Vendor,
    PurchaseOrderTracking,
)
from app.schemas.purchase_intelligence import (
    CreateOrderFromSuggestionRequest,
    MessageResponse,
    PurchaseOrderReceiveRequest,
    PurchaseOrderTrackingCreate,
    PurchaseOrderTrackingResponse,
    PurchaseSuggestionApprove,
    PurchaseSuggestionCreate,
    PurchaseSuggestionResponse,
    QuotationCompareItem,
    QuotationCompareRequest,
    QuotationCompareResponse,
    SupplierPerformanceCalculate,
    SupplierPerformanceResponse,
    SupplierQuotationCreate,
    SupplierQuotationResponse,
    SupplierRankingItem,
    SupplierRankingResponse,
)
from app.services.purchase_suggestion_engine import PurchaseSuggestionEngine
from app.services.supplier_performance_evaluator import SupplierPerformanceEvaluator
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
    query = db.query(PurchaseSuggestion)
    
    if status:
        query = query.filter(PurchaseSuggestion.status == status)
    if source_type:
        query = query.filter(PurchaseSuggestion.source_type == source_type)
    if material_id:
        query = query.filter(PurchaseSuggestion.material_id == material_id)
    if project_id:
        query = query.filter(PurchaseSuggestion.project_id == project_id)
    if urgency_level:
        query = query.filter(PurchaseSuggestion.urgency_level == urgency_level)
    
    suggestions = query.order_by(desc(PurchaseSuggestion.created_at)).offset(skip).limit(limit).all()
    
    # 填充关联数据
    result = []
    for s in suggestions:
        data = PurchaseSuggestionResponse.from_orm(s)
        
        # 填充供应商名称
        if s.suggested_supplier_id:
            supplier = db.query(Vendor).get(s.suggested_supplier_id)
            if supplier:
                data.suggested_supplier_name = supplier.supplier_name
        
        # 填充订单编号
        if s.purchase_order_id:
            order = db.query(PurchaseOrder).get(s.purchase_order_id)
            if order:
                data.purchase_order_no = order.order_no
        
        result.append(data)
    
    return result


# ==================== 2. 批准建议 ====================

@router.post("/suggestions/{suggestion_id}/approve", response_model=MessageResponse)
def approve_purchase_suggestion(
    suggestion_id: int,
    approve_data: PurchaseSuggestionApprove,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    批准或拒绝采购建议
    """
    suggestion = db.query(PurchaseSuggestion).get(suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="采购建议不存在")
    
    if suggestion.status != 'PENDING':
        raise HTTPException(status_code=400, detail=f"当前状态 {suggestion.status} 不允许审批")
    
    if approve_data.approved:
        suggestion.status = 'APPROVED'
        message = "采购建议已批准"
    else:
        suggestion.status = 'REJECTED'
        message = "采购建议已拒绝"
    
    suggestion.reviewed_by = current_user.id
    suggestion.reviewed_at = datetime.now()
    suggestion.review_note = approve_data.review_note
    
    if approve_data.suggested_supplier_id:
        suggestion.suggested_supplier_id = approve_data.suggested_supplier_id
    
    db.commit()
    
    return MessageResponse(message=message, data={"suggestion_id": suggestion_id})


# ==================== 3. 供应商绩效 ====================

@router.get("/suppliers/{supplier_id}/performance", response_model=List[SupplierPerformanceResponse])
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
    query = db.query(SupplierPerformance).filter(
        SupplierPerformance.supplier_id == supplier_id
    )
    
    if evaluation_period:
        query = query.filter(SupplierPerformance.evaluation_period == evaluation_period)
    
    performances = query.order_by(desc(SupplierPerformance.period_end)).limit(limit).all()
    
    return [SupplierPerformanceResponse.from_orm(p) for p in performances]


# ==================== 4. 触发评估 ====================

@router.post("/suppliers/{supplier_id}/evaluate", response_model=SupplierPerformanceResponse)
def evaluate_supplier_performance(
    supplier_id: int,
    evaluate_data: SupplierPerformanceCalculate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    触发供应商绩效评估
    """
    # 验证供应商存在
    supplier = db.query(Vendor).get(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 执行评估
    evaluator = SupplierPerformanceEvaluator(db)
    performance = evaluator.evaluate_supplier(
        supplier_id=supplier_id,
        evaluation_period=evaluate_data.evaluation_period,
        weight_config=evaluate_data.weight_config
    )
    
    if not performance:
        raise HTTPException(status_code=500, detail="绩效评估失败")
    
    return SupplierPerformanceResponse.from_orm(performance)


# ==================== 5. 供应商排名 ====================

@router.get("/suppliers/ranking", response_model=SupplierRankingResponse)
def get_supplier_ranking(
    evaluation_period: str = Query(..., description="评估期间 YYYY-MM"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取供应商排名
    """
    performances = db.query(SupplierPerformance).filter(
        SupplierPerformance.evaluation_period == evaluation_period
    ).order_by(desc(SupplierPerformance.overall_score)).limit(limit).all()
    
    rankings = []
    for idx, p in enumerate(performances, start=1):
        rankings.append(
            SupplierRankingItem(
                supplier_id=p.supplier_id,
                supplier_code=p.supplier_code,
                supplier_name=p.supplier_name,
                overall_score=p.overall_score,
                rating=p.rating,
                on_time_delivery_rate=p.on_time_delivery_rate,
                quality_pass_rate=p.quality_pass_rate,
                price_competitiveness=p.price_competitiveness,
                response_speed_score=p.response_speed_score,
                total_orders=p.total_orders,
                total_amount=p.total_amount,
                evaluation_period=p.evaluation_period,
                rank=idx,
            )
        )
    
    return SupplierRankingResponse(
        evaluation_period=evaluation_period,
        total_suppliers=len(rankings),
        rankings=rankings,
    )


# ==================== 6. 创建报价 ====================

@router.post("/quotations", response_model=SupplierQuotationResponse, status_code=status.HTTP_201_CREATED)
def create_supplier_quotation(
    quotation_data: SupplierQuotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建供应商报价
    """
    # 验证供应商
    supplier = db.query(Vendor).get(quotation_data.supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 验证物料
    material = db.query(Material).get(quotation_data.material_id)
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")
    
    # 生成报价单号
    quotation_no = _generate_quotation_no(db)
    
    # 创建报价
    quotation = SupplierQuotation(
        quotation_no=quotation_no,
        supplier_id=quotation_data.supplier_id,
        material_id=quotation_data.material_id,
        material_code=material.material_code,
        material_name=material.material_name,
        specification=material.specification,
        unit_price=quotation_data.unit_price,
        currency=quotation_data.currency,
        min_order_qty=quotation_data.min_order_qty,
        lead_time_days=quotation_data.lead_time_days,
        valid_from=quotation_data.valid_from,
        valid_to=quotation_data.valid_to,
        payment_terms=quotation_data.payment_terms,
        warranty_period=quotation_data.warranty_period,
        tax_rate=quotation_data.tax_rate,
        remark=quotation_data.remark,
        created_by=current_user.id,
    )
    
    db.add(quotation)
    db.commit()
    db.refresh(quotation)
    
    # 填充响应数据
    response = SupplierQuotationResponse.from_orm(quotation)
    response.supplier_code = supplier.supplier_code
    response.supplier_name = supplier.supplier_name
    
    return response


# ==================== 7. 比价 ====================

@router.get("/quotations/compare", response_model=QuotationCompareResponse)
def compare_quotations(
    material_id: int = Query(..., description="物料ID"),
    supplier_ids: Optional[str] = Query(None, description="供应商ID列表，逗号分隔"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    比较供应商报价
    """
    # 验证物料
    material = db.query(Material).get(material_id)
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")
    
    # 查询报价
    query = db.query(SupplierQuotation).filter(
        and_(
            SupplierQuotation.material_id == material_id,
            SupplierQuotation.status == 'ACTIVE',
            SupplierQuotation.valid_to >= date.today()
        )
    )
    
    if supplier_ids:
        supplier_id_list = [int(s) for s in supplier_ids.split(',')]
        query = query.filter(SupplierQuotation.supplier_id.in_(supplier_id_list))
    
    quotations = query.order_by(SupplierQuotation.unit_price).all()
    
    if not quotations:
        return QuotationCompareResponse(
            material_id=material_id,
            material_code=material.material_code,
            material_name=material.material_name,
            quotations=[],
        )
    
    # 获取供应商绩效
    supplier_performances = {}
    for q in quotations:
        latest_perf = db.query(SupplierPerformance).filter(
            SupplierPerformance.supplier_id == q.supplier_id
        ).order_by(desc(SupplierPerformance.period_end)).first()
        
        if latest_perf:
            supplier_performances[q.supplier_id] = {
                'score': latest_perf.overall_score,
                'rating': latest_perf.rating,
            }
    
    # 构建比较数据
    compare_items = []
    for q in quotations:
        supplier = db.query(Vendor).get(q.supplier_id)
        perf = supplier_performances.get(q.supplier_id, {})
        
        compare_items.append(
            QuotationCompareItem(
                quotation_id=q.id,
                quotation_no=q.quotation_no,
                supplier_id=q.supplier_id,
                supplier_code=supplier.supplier_code if supplier else '',
                supplier_name=supplier.supplier_name if supplier else '',
                unit_price=q.unit_price,
                currency=q.currency,
                min_order_qty=q.min_order_qty,
                lead_time_days=q.lead_time_days,
                valid_from=q.valid_from,
                valid_to=q.valid_to,
                payment_terms=q.payment_terms,
                tax_rate=q.tax_rate,
                is_selected=q.is_selected,
                performance_score=perf.get('score'),
                performance_rating=perf.get('rating'),
            )
        )
    
    # 确定最优价格和推荐供应商
    best_price_supplier_id = quotations[0].supplier_id if quotations else None
    
    # 综合价格和绩效推荐
    recommended_supplier_id = None
    max_combined_score = 0
    
    for item in compare_items:
        # 综合评分 = 价格评分(40%) + 绩效评分(60%)
        price_score = (1 - (item.unit_price - quotations[0].unit_price) / quotations[0].unit_price) * 100
        perf_score = float(item.performance_score) if item.performance_score else 50
        
        combined_score = price_score * 0.4 + perf_score * 0.6
        
        if combined_score > max_combined_score:
            max_combined_score = combined_score
            recommended_supplier_id = item.supplier_id
    
    return QuotationCompareResponse(
        material_id=material_id,
        material_code=material.material_code,
        material_name=material.material_name,
        quotations=compare_items,
        best_price_supplier_id=best_price_supplier_id,
        recommended_supplier_id=recommended_supplier_id,
        recommendation_reason="基于价格和供应商绩效综合评估推荐",
    )


# ==================== 8. 订单跟踪 ====================

@router.get("/orders/{order_id}/tracking", response_model=List[PurchaseOrderTrackingResponse])
def get_purchase_order_tracking(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取采购订单跟踪记录
    """
    order = db.query(PurchaseOrder).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    
    trackings = db.query(PurchaseOrderTracking).filter(
        PurchaseOrderTracking.order_id == order_id
    ).order_by(PurchaseOrderTracking.event_time.desc()).all()
    
    result = []
    for t in trackings:
        data = PurchaseOrderTrackingResponse.from_orm(t)
        
        if t.operator_id:
            operator = db.query(User).get(t.operator_id)
            if operator:
                data.operator_name = operator.username
        
        result.append(data)
    
    return result


# ==================== 9. 收货确认 ====================

@router.post("/orders/{order_id}/receive", response_model=MessageResponse)
def receive_purchase_order(
    order_id: int,
    receive_data: PurchaseOrderReceiveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    收货确认
    """
    order = db.query(PurchaseOrder).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    
    # 生成收货单号
    receipt_no = _generate_receipt_no(db)
    
    # 创建收货单
    receipt = GoodsReceipt(
        receipt_no=receipt_no,
        order_id=order_id,
        supplier_id=order.supplier_id,
        receipt_date=receive_data.receipt_date,
        delivery_note_no=receive_data.delivery_note_no,
        logistics_company=receive_data.logistics_company,
        tracking_no=receive_data.tracking_no,
        remark=receive_data.remark,
        status='PENDING',
        created_by=current_user.id,
    )
    
    db.add(receipt)
    db.flush()
    
    # 创建收货明细
    for item_data in receive_data.items:
        order_item = db.query(PurchaseOrderItem).get(item_data['order_item_id'])
        if not order_item:
            continue
        
        receipt_item = GoodsReceiptItem(
            receipt_id=receipt.id,
            order_item_id=order_item.id,
            material_code=order_item.material_code,
            material_name=order_item.material_name,
            delivery_qty=item_data['delivery_qty'],
            received_qty=item_data.get('received_qty', item_data['delivery_qty']),
            remark=item_data.get('remark'),
        )
        
        db.add(receipt_item)
        
        # 更新订单项收货数量
        order_item.received_qty = (order_item.received_qty or 0) + receipt_item.received_qty
    
    # 创建跟踪记录
    tracking = PurchaseOrderTracking(
        order_id=order_id,
        order_no=order.order_no,
        event_type='RECEIVED',
        event_time=datetime.now(),
        event_description=f"收货确认，收货单号：{receipt_no}",
        new_status='RECEIVED',
        tracking_no=receive_data.tracking_no,
        logistics_company=receive_data.logistics_company,
        operator_id=current_user.id,
    )
    
    db.add(tracking)
    db.commit()
    
    return MessageResponse(
        message="收货确认成功",
        data={"receipt_id": receipt.id, "receipt_no": receipt_no}
    )


# ==================== 10. 建议转订单 ====================

@router.post("/suggestions/{suggestion_id}/create-order", response_model=MessageResponse)
def create_order_from_suggestion(
    suggestion_id: int,
    order_data: CreateOrderFromSuggestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    从采购建议创建采购订单
    """
    suggestion = db.query(PurchaseSuggestion).get(suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="采购建议不存在")
    
    if suggestion.status != 'APPROVED':
        raise HTTPException(status_code=400, detail="只有已批准的建议才能创建订单")
    
    if suggestion.purchase_order_id:
        raise HTTPException(status_code=400, detail="该建议已创建订单")
    
    # 确定供应商
    supplier_id = order_data.supplier_id or suggestion.suggested_supplier_id
    if not supplier_id:
        raise HTTPException(status_code=400, detail="未指定供应商")
    
    supplier = db.query(Vendor).get(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 生成订单编号
    order_no = _generate_purchase_order_no(db)
    
    # 计算金额
    unit_price = suggestion.estimated_unit_price or 0
    amount = suggestion.suggested_qty * unit_price
    tax_amount = amount * (suggestion.material.standard_price or 13) / 100 if suggestion.material else 0
    amount_with_tax = amount + tax_amount
    
    # 创建采购订单
    order = PurchaseOrder(
        order_no=order_no,
        supplier_id=supplier_id,
        project_id=suggestion.project_id,
        order_type='NORMAL',
        order_title=f"采购建议转订单 - {suggestion.material_name}",
        total_amount=amount,
        tax_amount=tax_amount,
        amount_with_tax=amount_with_tax,
        order_date=date.today(),
        required_date=order_data.required_date or suggestion.required_date,
        status='DRAFT',
        payment_terms=order_data.payment_terms,
        delivery_address=order_data.delivery_address,
        remark=order_data.remark,
        created_by=current_user.id,
    )
    
    db.add(order)
    db.flush()
    
    # 创建订单明细
    order_item = PurchaseOrderItem(
        order_id=order.id,
        item_no=1,
        material_id=suggestion.material_id,
        material_code=suggestion.material_code,
        material_name=suggestion.material_name,
        specification=suggestion.specification,
        unit=suggestion.unit,
        quantity=suggestion.suggested_qty,
        unit_price=unit_price,
        amount=amount,
        tax_amount=tax_amount,
        amount_with_tax=amount_with_tax,
        required_date=order_data.required_date or suggestion.required_date,
        status='PENDING',
    )
    
    db.add(order_item)
    
    # 更新建议状态
    suggestion.purchase_order_id = order.id
    suggestion.status = 'ORDERED'
    suggestion.ordered_at = datetime.now()
    
    db.commit()
    
    return MessageResponse(
        message="采购订单创建成功",
        data={"order_id": order.id, "order_no": order_no}
    )


# ==================== 辅助函数 ====================

def _generate_quotation_no(db: Session) -> str:
    """生成报价单号"""
    prefix = 'QT'
    date_str = datetime.now().strftime('%Y%m%d')
    
    latest = db.query(SupplierQuotation).filter(
        SupplierQuotation.quotation_no.like(f'{prefix}{date_str}%')
    ).order_by(desc(SupplierQuotation.quotation_no)).first()
    
    if latest:
        last_seq = int(latest.quotation_no[-4:])
        seq = last_seq + 1
    else:
        seq = 1
    
    return f'{prefix}{date_str}{seq:04d}'


def _generate_receipt_no(db: Session) -> str:
    """生成收货单号"""
    prefix = 'GR'
    date_str = datetime.now().strftime('%Y%m%d')
    
    latest = db.query(GoodsReceipt).filter(
        GoodsReceipt.receipt_no.like(f'{prefix}{date_str}%')
    ).order_by(desc(GoodsReceipt.receipt_no)).first()
    
    if latest:
        last_seq = int(latest.receipt_no[-4:])
        seq = last_seq + 1
    else:
        seq = 1
    
    return f'{prefix}{date_str}{seq:04d}'


def _generate_purchase_order_no(db: Session) -> str:
    """生成采购订单编号"""
    prefix = 'PO'
    date_str = datetime.now().strftime('%Y%m%d')
    
    latest = db.query(PurchaseOrder).filter(
        PurchaseOrder.order_no.like(f'{prefix}{date_str}%')
    ).order_by(desc(PurchaseOrder.order_no)).first()
    
    if latest:
        last_seq = int(latest.order_no[-4:])
        seq = last_seq + 1
    else:
        seq = 1
    
    return f'{prefix}{date_str}{seq:04d}'

# -*- coding: utf-8 -*-
"""
供应商管理 API
- 供应商列表（分页/搜索）
- 新增供应商
- 供应商绩效分析
- 供应商评级排行
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, case, desc, func
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core.schemas import list_response, paginated_response, success_response
from app.models.material import Material, MaterialSupplier
from app.models.purchase import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
)
from app.models.user import User
from app.models.vendor import Vendor

router = APIRouter()
logger = logging.getLogger(__name__)


def _serialize_vendor(v: Vendor) -> Dict[str, Any]:
    """序列化供应商基本信息"""
    return {
        "id": v.id,
        "supplier_code": v.supplier_code,
        "supplier_name": v.supplier_name,
        "vendor_type": v.vendor_type,
        "contact_person": v.contact_person,
        "phone": v.phone,
        "email": v.email,
        "address": v.address,
        "supplier_level": v.supplier_level,
        "payment_terms": v.payment_terms,
        "status": v.status,
        "business_license": v.business_license,
        "remark": v.remark,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    }


# ==================== 供应商列表 ====================


@router.get("/")
def list_suppliers(
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="搜索关键词（名称/编码）"),
    status: Optional[str] = Query(None, description="状态筛选"),
    supplier_level: Optional[str] = Query(None, description="供应商等级筛选"),
    current_user: User = Depends(get_current_active_user),
):
    """
    供应商列表

    支持按名称/编码搜索，按状态和等级筛选
    """
    try:
        query = db.query(Vendor).filter(Vendor.vendor_type == "MATERIAL")

        query = apply_keyword_filter(
            query, Vendor, keyword, ["supplier_name", "supplier_code"]
        )

        if status:
            query = query.filter(Vendor.status == status)
        if supplier_level:
            query = query.filter(Vendor.supplier_level == supplier_level)

        total = query.count()
        vendors = apply_pagination(
            query.order_by(desc(Vendor.created_at)),
            pagination.offset,
            pagination.limit,
        ).all()

        # 批量查询每个供应商的产品类别数和订单数
        vendor_ids = [v.id for v in vendors]
        material_counts = {}
        order_counts = {}
        if vendor_ids:
            mc = (
                db.query(
                    MaterialSupplier.supplier_id,
                    func.count(MaterialSupplier.id).label("cnt"),
                )
                .filter(MaterialSupplier.supplier_id.in_(vendor_ids))
                .group_by(MaterialSupplier.supplier_id)
                .all()
            )
            material_counts = {row[0]: row[1] for row in mc}

            oc = (
                db.query(
                    PurchaseOrder.supplier_id,
                    func.count(PurchaseOrder.id).label("cnt"),
                )
                .filter(PurchaseOrder.supplier_id.in_(vendor_ids))
                .group_by(PurchaseOrder.supplier_id)
                .all()
            )
            order_counts = {row[0]: row[1] for row in oc}

        items = []
        for v in vendors:
            data = _serialize_vendor(v)
            data["material_count"] = material_counts.get(v.id, 0)
            data["order_count"] = order_counts.get(v.id, 0)
            items.append(data)

        return paginated_response(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
    except Exception as e:
        logger.error(f"获取供应商列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取供应商列表失败")


# ==================== 新增供应商 ====================


@router.post("/")
def create_supplier(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    新增供应商

    必填：supplier_code, supplier_name
    """
    supplier_code = payload.get("supplier_code")
    supplier_name = payload.get("supplier_name")

    if not supplier_code or not supplier_name:
        raise HTTPException(status_code=422, detail="supplier_code 和 supplier_name 必填")

    existing = db.query(Vendor).filter(Vendor.supplier_code == supplier_code).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"供应商编码 {supplier_code} 已存在")

    vendor = Vendor(
        supplier_code=supplier_code,
        supplier_name=supplier_name,
        vendor_type="MATERIAL",
        contact_person=payload.get("contact_person"),
        phone=payload.get("phone"),
        email=payload.get("email"),
        address=payload.get("address"),
        supplier_level=payload.get("supplier_level", "B"),
        payment_terms=payload.get("payment_terms"),
        business_license=payload.get("business_license"),
        remark=payload.get("remark"),
        status=payload.get("status", "ACTIVE"),
        created_by=current_user.id,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    return success_response(data=_serialize_vendor(vendor), message="供应商创建成功")


# ==================== 供应商绩效分析 ====================


@router.get("/{supplier_id}/performance")
def get_supplier_performance(
    supplier_id: int,
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    current_user: User = Depends(get_current_active_user),
):
    """
    供应商绩效分析

    返回：
    - 基本信息
    - 合作统计（订单数/总金额/平均金额）
    - 交期准时率
    - 质量合格率
    - 评级详情（质量/交期/价格/服务）
    """
    vendor = db.query(Vendor).filter(Vendor.id == supplier_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="供应商不存在")

    # 时间范围
    dt_start = None
    dt_end = None
    if start_date:
        dt_start = date.fromisoformat(start_date)
    if end_date:
        dt_end = date.fromisoformat(end_date)

    # --- 订单统计 ---
    order_query = db.query(PurchaseOrder).filter(
        PurchaseOrder.supplier_id == supplier_id,
        PurchaseOrder.status.notin_(["DRAFT", "CANCELLED"]),
    )
    if dt_start:
        order_query = order_query.filter(PurchaseOrder.order_date >= dt_start)
    if dt_end:
        order_query = order_query.filter(PurchaseOrder.order_date <= dt_end)

    orders = order_query.all()
    total_orders = len(orders)
    total_amount = sum(float(o.total_amount or 0) for o in orders)
    avg_amount = total_amount / total_orders if total_orders else 0

    # --- 交期准时率 ---
    # 统计有承诺交期的订单行
    item_query = (
        db.query(PurchaseOrderItem)
        .join(PurchaseOrder)
        .filter(
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrderItem.promised_date.isnot(None),
        )
    )
    if dt_start:
        item_query = item_query.filter(PurchaseOrder.order_date >= dt_start)
    if dt_end:
        item_query = item_query.filter(PurchaseOrder.order_date <= dt_end)

    all_items = item_query.all()
    total_lines = len(all_items)
    on_time_lines = 0
    for item in all_items:
        if item.received_qty and item.received_qty > 0:
            # 有收货记录的行视为已交付; 简化判定：已收数量>0 且有承诺交期
            # 通过收货单的收货日期与承诺交期比较
            receipt_item = item.receipt_items.first() if item.receipt_items else None
            if receipt_item:
                receipt = (
                    db.query(GoodsReceipt)
                    .filter(GoodsReceipt.id == receipt_item.receipt_id)
                    .first()
                )
                if receipt and receipt.receipt_date and item.promised_date:
                    if receipt.receipt_date <= item.promised_date:
                        on_time_lines += 1
                    continue
            # 没有收货记录但有收货数量，视为准时
            on_time_lines += 1

    on_time_rate = round(on_time_lines / total_lines * 100, 1) if total_lines else 0

    # --- 质量合格率 ---
    quality_query = (
        db.query(
            func.sum(GoodsReceiptItem.qualified_qty).label("qualified"),
            func.sum(GoodsReceiptItem.rejected_qty).label("rejected"),
        )
        .join(GoodsReceipt)
        .filter(GoodsReceipt.supplier_id == supplier_id)
    )
    if dt_start:
        quality_query = quality_query.filter(GoodsReceipt.receipt_date >= dt_start)
    if dt_end:
        quality_query = quality_query.filter(GoodsReceipt.receipt_date <= dt_end)

    qr = quality_query.first()
    qualified = float(qr.qualified or 0)
    rejected = float(qr.rejected or 0)
    total_inspected = qualified + rejected
    quality_rate = round(qualified / total_inspected * 100, 1) if total_inspected else 0

    # --- 综合评级 ---
    quality_score = min(quality_rate, 100)
    delivery_score = min(on_time_rate, 100)
    # 价格评分：基于该供应商物料价格与市场均价的比较
    price_score = _calc_price_score(db, supplier_id)
    service_score = min((quality_score + delivery_score) / 2, 100)  # 简化：取质量和交期的均值
    overall_score = round(
        quality_score * 0.3 + delivery_score * 0.3 + price_score * 0.25 + service_score * 0.15,
        1,
    )

    # --- 供应产品类别 ---
    categories = (
        db.query(Material.material_code, Material.material_name)
        .join(MaterialSupplier, MaterialSupplier.material_id == Material.id)
        .filter(MaterialSupplier.supplier_id == supplier_id, MaterialSupplier.is_active == True)
        .limit(20)
        .all()
    )

    return success_response(
        data={
            "supplier": _serialize_vendor(vendor),
            "cooperation": {
                "total_orders": total_orders,
                "total_amount": round(total_amount, 2),
                "avg_order_amount": round(avg_amount, 2),
            },
            "delivery": {
                "total_lines": total_lines,
                "on_time_lines": on_time_lines,
                "on_time_rate": on_time_rate,
            },
            "quality": {
                "total_inspected": round(total_inspected, 2),
                "qualified": round(qualified, 2),
                "rejected": round(rejected, 2),
                "quality_rate": quality_rate,
            },
            "rating": {
                "quality_score": round(quality_score, 1),
                "delivery_score": round(delivery_score, 1),
                "price_score": round(price_score, 1),
                "service_score": round(service_score, 1),
                "overall_score": overall_score,
            },
            "product_categories": [
                {"material_code": c[0], "material_name": c[1]} for c in categories
            ],
        },
        message="获取供应商绩效成功",
    )


def _calc_price_score(db: Session, supplier_id: int) -> float:
    """
    计算供应商价格评分（0-100）

    逻辑：该供应商的物料报价与所有供应商均价的对比
    低于均价得分高，高于均价得分低
    """
    # 获取该供应商关联的物料及其价格
    supplier_prices = (
        db.query(MaterialSupplier.material_id, MaterialSupplier.price)
        .filter(
            MaterialSupplier.supplier_id == supplier_id,
            MaterialSupplier.is_active == True,
            MaterialSupplier.price > 0,
        )
        .all()
    )

    if not supplier_prices:
        return 70.0  # 无数据默认中等

    material_ids = [sp[0] for sp in supplier_prices]
    supplier_price_map = {sp[0]: float(sp[1]) for sp in supplier_prices}

    # 所有供应商的均价
    avg_prices = (
        db.query(MaterialSupplier.material_id, func.avg(MaterialSupplier.price).label("avg_price"))
        .filter(
            MaterialSupplier.material_id.in_(material_ids),
            MaterialSupplier.is_active == True,
            MaterialSupplier.price > 0,
        )
        .group_by(MaterialSupplier.material_id)
        .all()
    )
    avg_map = {row[0]: float(row[1]) for row in avg_prices}

    ratios = []
    for mid, price in supplier_price_map.items():
        avg = avg_map.get(mid)
        if avg and avg > 0:
            ratios.append(price / avg)

    if not ratios:
        return 70.0

    avg_ratio = sum(ratios) / len(ratios)
    # ratio < 1 表示低于均价（好）, ratio > 1 表示高于均价（差）
    # 映射到 0-100 分，ratio=0.8 -> 100, ratio=1.0 -> 70, ratio=1.2 -> 40
    score = max(0, min(100, 70 + (1 - avg_ratio) * 150))
    return round(score, 1)


# ==================== 供应商评级排行 ====================


@router.get("/ranking")
def get_supplier_ranking(
    db: Session = Depends(get_db),
    top_n: int = Query(20, ge=1, le=100, description="返回前N名"),
    sort_by: str = Query("overall", description="排序维度: overall/quality/delivery/price"),
    current_user: User = Depends(get_current_active_user),
):
    """
    供应商评级排行

    根据历史采购数据综合评估供应商，返回排行榜
    """
    vendors = (
        db.query(Vendor)
        .filter(Vendor.vendor_type == "MATERIAL", Vendor.status == "ACTIVE")
        .all()
    )

    rankings = []
    for v in vendors:
        # 订单数
        order_count = (
            db.query(func.count(PurchaseOrder.id))
            .filter(
                PurchaseOrder.supplier_id == v.id,
                PurchaseOrder.status.notin_(["DRAFT", "CANCELLED"]),
            )
            .scalar()
            or 0
        )
        if order_count == 0:
            continue  # 没有合作记录的不参与排名

        total_amount = (
            db.query(func.sum(PurchaseOrder.total_amount))
            .filter(
                PurchaseOrder.supplier_id == v.id,
                PurchaseOrder.status.notin_(["DRAFT", "CANCELLED"]),
            )
            .scalar()
            or 0
        )

        # 质量
        qr = (
            db.query(
                func.sum(GoodsReceiptItem.qualified_qty).label("qualified"),
                func.sum(GoodsReceiptItem.rejected_qty).label("rejected"),
            )
            .join(GoodsReceipt)
            .filter(GoodsReceipt.supplier_id == v.id)
            .first()
        )
        qualified = float(qr.qualified or 0)
        rejected = float(qr.rejected or 0)
        total_inspected = qualified + rejected
        quality_score = round(qualified / total_inspected * 100, 1) if total_inspected else 70.0

        # 交期 - 简化：基于收货单数据
        delivery_score = _calc_delivery_score_simple(db, v.id)

        # 价格
        price_score = _calc_price_score(db, v.id)

        service_score = round((quality_score + delivery_score) / 2, 1)
        overall_score = round(
            quality_score * 0.3 + delivery_score * 0.3 + price_score * 0.25 + service_score * 0.15,
            1,
        )

        rankings.append(
            {
                "supplier_id": v.id,
                "supplier_code": v.supplier_code,
                "supplier_name": v.supplier_name,
                "supplier_level": v.supplier_level,
                "order_count": order_count,
                "total_amount": round(float(total_amount), 2),
                "quality_score": quality_score,
                "delivery_score": delivery_score,
                "price_score": price_score,
                "service_score": service_score,
                "overall_score": overall_score,
            }
        )

    sort_key = {
        "overall": "overall_score",
        "quality": "quality_score",
        "delivery": "delivery_score",
        "price": "price_score",
    }.get(sort_by, "overall_score")

    rankings.sort(key=lambda x: x[sort_key], reverse=True)
    rankings = rankings[:top_n]

    # 添加排名序号
    for idx, r in enumerate(rankings, 1):
        r["rank"] = idx

    return list_response(items=rankings, message="获取供应商排行成功")


def _calc_delivery_score_simple(db: Session, supplier_id: int) -> float:
    """简化的交期准时率评分"""
    receipts = (
        db.query(GoodsReceipt)
        .filter(
            GoodsReceipt.supplier_id == supplier_id,
            GoodsReceipt.receipt_date.isnot(None),
        )
        .all()
    )
    if not receipts:
        return 70.0

    total = 0
    on_time = 0
    for r in receipts:
        order = db.query(PurchaseOrder).filter(PurchaseOrder.id == r.order_id).first()
        if order and order.promised_date:
            total += 1
            if r.receipt_date <= order.promised_date:
                on_time += 1

    if total == 0:
        return 70.0
    return round(on_time / total * 100, 1)

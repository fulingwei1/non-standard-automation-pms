# -*- coding: utf-8 -*-
"""
报价智能化API（SALES-13 收口）

- 历史价格参考：做实——按真实 WON 商机 × 已签合同返回成交参考价（报价编辑器侧栏消费）。
- 竞品价格录入/对比、最优价格建议、自动折扣、赢单率预测（单个+批量）：
  原实现为纯常量演示数据且无真实消费方，一律 501 下架；做实排期见 ROADMAP F5。
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User

router = APIRouter()

_STOPGAP_DETAIL = (
    "该智能报价端点此前返回硬编码演示数据，已下架（SALES-13 止损）。"
    "真实报价参考请用 GET /sales/quotes/historical-prices（真实成交数据）、"
    "商机页 AI 报价估算或售前三档报价。"
)


def _not_implemented() -> Any:
    raise HTTPException(status_code=501, detail=_STOPGAP_DETAIL)


# ========== 1. 历史价格参考（真实数据） ==========


@router.get("/quotes/historical-prices", summary="历史价格参考")
def get_historical_prices(
    product_category: str = Query(..., description="产品类型"),
    estimated_amount: Optional[float] = Query(None, description="预估金额（给定时按±30%过滤）"),
    industry: Optional[str] = Query(None, description="行业（按客户行业模糊过滤）"),
    limit: int = Query(5, description="返回数量"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """查询相似项目的真实历史成交价：WON 商机 × 已签合同（按设备类型/商机名匹配）。

    查无匹配返回空列表——宁缺毋假，不再用演示数据兜底。
    """
    from sqlalchemy import or_

    from app.models.project import Customer
    from app.models.sales import Opportunity
    from app.models.sales.contracts import Contract
    from app.services.sales.contract.status_service import contract_status_query_values

    keyword = (product_category or "").strip()
    query = (
        db.query(Opportunity, Contract, Customer)
        .join(Contract, Contract.opportunity_id == Opportunity.id)
        .join(Customer, Customer.id == Opportunity.customer_id)
        .filter(Opportunity.stage == "WON")
        .filter(Contract.status.in_(contract_status_query_values(["SIGNED", "EXECUTING", "COMPLETED"])))
    )
    if keyword:
        query = query.filter(
            or_(
                Opportunity.equipment_type.ilike(f"%{keyword}%"),
                Opportunity.opp_name.ilike(f"%{keyword}%"),
            )
        )
    if industry:
        query = query.filter(Customer.industry.ilike(f"%{industry}%"))
    if estimated_amount and estimated_amount > 0:
        query = query.filter(
            Contract.total_amount >= estimated_amount * 0.7,
            Contract.total_amount <= estimated_amount * 1.3,
        )

    rows = query.order_by(Contract.signing_date.desc(), Contract.id.desc()).limit(limit).all()

    items = []
    for opp, contract, customer in rows:
        final_price = float(contract.total_amount or 0)
        original_quote = float(opp.est_amount) if opp.est_amount else None
        discount_rate = (
            round((original_quote - final_price) / original_quote * 100, 1)
            if original_quote and original_quote > 0
            else None
        )
        items.append(
            {
                "project_name": opp.opp_name,
                "product_category": opp.equipment_type,
                "industry": getattr(customer, "industry", None),
                "final_price": final_price,
                "original_quote": original_quote,
                "discount_rate": discount_rate,
                "deal_date": contract.signing_date.isoformat() if contract.signing_date else None,
                "match_basis": "equipment_type/opp_name 模糊匹配",
            }
        )

    average_price = round(sum(i["final_price"] for i in items) / len(items), 2) if items else 0
    return {
        "product_category": product_category,
        "total": len(items),
        "items": items,
        # 兼容报价编辑器侧栏的旧响应结构
        "historical_prices": items,
        "matched_count": len(items),
        "average_price": average_price,
        "data_source": "real_won_deals",
    }


# ========== 以下端点硬编码演示数据已下架（501） ==========


@router.post("/competitor-prices", summary="录入竞品价格（未实现）")
def add_competitor_price(
    data: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return _not_implemented()


@router.get("/competitor-prices/comparison", summary="竞品价格对比（未实现）")
def get_competitor_price_comparison(
    product_category: str = Query(..., description="产品类型"),
    our_price: Optional[float] = Query(None, description="我方价格"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return _not_implemented()


@router.post("/quotes/{quote_id}/optimal-price", summary="最优价格建议（未实现）")
def get_optimal_price_suggestion(
    quote_id: int = Path(..., description="报价ID"),
    target_margin: Optional[float] = Query(None, description="目标毛利率%"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return _not_implemented()


@router.post("/quotes/{quote_id}/auto-discount", summary="自动折扣计算（未实现）")
def calculate_auto_discount(
    quote_id: int = Path(..., description="报价ID"),
    customer_level: str = Query("A", description="客户等级：A/B/C/D"),
    order_volume: Optional[int] = Query(None, description="订单数量"),
    payment_terms: Optional[str] = Query(None, description="付款条件"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return _not_implemented()


@router.get("/opportunities/{opportunity_id}/win-rate-prediction", summary="赢单率预测（未实现）")
def predict_win_rate(
    opportunity_id: int = Path(..., description="商机ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return _not_implemented()


@router.post("/batch-win-rate-prediction", summary="批量赢单率预测（未实现）")
def batch_predict_win_rate(
    opportunity_ids: List[int] = Body(..., description="商机ID列表"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return _not_implemented()

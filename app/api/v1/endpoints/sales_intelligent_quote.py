# -*- coding: utf-8 -*-
"""
报价智能化API
提供历史价格参考、竞品价格、最优价格建议、赢单率预测
"""

from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api import deps
from app.core import security
from app.models.user import User

router = APIRouter()


# ========== 1. 历史价格参考 ==========

@router.get("/quotes/historical-prices", summary="历史价格参考")
def get_historical_prices(
    product_category: str = Query(..., description="产品类型"),
    estimated_amount: Optional[float] = Query(None, description="预估金额"),
    industry: Optional[str] = Query(None, description="行业"),
    limit: int = Query(5, description="返回数量"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    查询相似项目的历史报价作为参考
    
    匹配维度：
    - 产品类型（精确匹配）
    - 行业（相似匹配）
    - 金额范围（±30%）
    
    返回最近赢单项目的报价信息
    """
    
    # 模拟历史价格数据
    historical_prices = [
        {
            "project_name": "宁德时代FCT测试线",
            "product_category": "FCT",
            "industry": "锂电",
            "final_price": 3200000,
            "original_quote": 3500000,
            "discount_rate": 8.6,
            "deal_date": "2025-08-15",
            "similarity": "95%",
            "notes": "标准配置，60天交付",
        },
        {
            "project_name": "比亚迪EOL测试设备",
            "product_category": "EOL",
            "industry": "锂电",
            "final_price": 2800000,
            "original_quote": 3000000,
            "discount_rate": 6.7,
            "deal_date": "2025-09-20",
            "similarity": "80%",
            "notes": "加急交付，45天",
        },
        {
            "project_name": "中创新航ICT+FCT",
            "product_category": "FCT",
            "industry": "锂电",
            "final_price": 3800000,
            "original_quote": 4200000,
            "discount_rate": 9.5,
            "deal_date": "2025-10-10",
            "similarity": "88%",
            "notes": "一体化测试方案",
        },
    ]
    
    # 过滤匹配的产品类型
    matched = [p for p in historical_prices if p["product_category"] == product_category]
    
    return {
        "query": {
            "product_category": product_category,
            "estimated_amount": estimated_amount,
            "industry": industry,
        },
        "matched_count": len(matched),
        "average_price": sum(p["final_price"] for p in matched) / len(matched) if matched else 0,
        "price_range": {
            "min": min(p["final_price"] for p in matched) if matched else 0,
            "max": max(p["final_price"] for p in matched) if matched else 0,
        },
        "historical_prices": matched[:limit],
    }


# ========== 2. 竞品价格录入与对比 ==========

@router.post("/competitor-prices", summary="录入竞品价格")
def add_competitor_price(
    data: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """录入竞品价格信息"""
    
    return {
        "message": "竞品价格录入成功",
        "competitor_price_id": 123,
    }


@router.get("/competitor-prices/comparison", summary="竞品价格对比")
def get_competitor_price_comparison(
    product_category: str = Query(..., description="产品类型"),
    our_price: Optional[float] = Query(None, description="我们的报价"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    竞品价格对比分析
    
    返回：
    - 各竞品价格分布
    - 我们的价格位置
    - 价格竞争力分析
    """
    
    competitors = [
        {"name": "竞品A", "price": 2800000, "market_share": "25%", "strategy": "低价"},
        {"name": "竞品B", "price": 3200000, "market_share": "20%", "strategy": "品牌"},
        {"name": "竞品C", "price": 3000000, "market_share": "15%", "strategy": "服务"},
    ]
    
    all_prices = [c["price"] for c in competitors]
    if our_price:
        all_prices.append(our_price)
    
    avg_price = sum(all_prices) / len(all_prices)
    
    return {
        "product_category": product_category,
        "our_price": our_price,
        "market_average": avg_price,
        "price_position": "偏高" if our_price and our_price > avg_price * 1.1 else "偏低" if our_price and our_price < avg_price * 0.9 else "适中",
        "competitors": competitors,
        "analysis": {
            "price_gap_with_lowest": our_price - min(c["price"] for c in competitors) if our_price else None,
            "price_gap_with_highest": max(c["price"] for c in competitors) - our_price if our_price else None,
            "competitiveness": "有竞争力" if our_price and our_price <= avg_price else "需调整",
        },
    }


# ========== 3. 最优价格建议 ==========

@router.post("/quotes/{quote_id}/optimal-price", summary="最优价格建议")
def get_optimal_price_suggestion(
    quote_id: int = Path(..., description="报价ID"),
    target_margin: Optional[float] = Query(None, description="目标毛利率%"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    AI给出最优价格建议
    
    平衡因素：
    - 利润率目标
    - 市场竞争力
    - 客户价值
    - 赢单概率
    
    返回：
    - 建议价格
    - 预期赢单率
    - 不同价格下的赢单率预测
    """
    
    # 模拟不同价格下的赢单率
    price_scenarios = [
        {"price": 2800000, "win_rate": 85, "margin_rate": 25, "suggestion": "激进低价，快速抢占市场"},
        {"price": 3200000, "win_rate": 70, "margin_rate": 32, "suggestion": "平衡方案，推荐"},
        {"price": 3500000, "win_rate": 55, "margin_rate": 38, "suggestion": "标准报价"},
        {"price": 3800000, "win_rate": 35, "margin_rate": 42, "suggestion": "利润优先，风险较高"},
    ]
    
    # 推荐最优价格
    optimal = price_scenarios[1]  # 320万，70%赢单率
    
    return {
        "quote_id": quote_id,
        "target_margin": target_margin,
        "optimal_price": optimal["price"],
        "optimal_win_rate": optimal["win_rate"],
        "optimal_margin": optimal["margin_rate"],
        "suggestion": optimal["suggestion"],
        "price_scenarios": price_scenarios,
        "analysis": {
            "profit_vs_win_rate": "当前推荐在利润和赢单率之间取得平衡",
            "market_position": "该价格在市场具有竞争力",
            "customer_value": "基于客户历史价值，可适当让步",
        },
    }


# ========== 4. 自动折扣计算 ==========

@router.post("/quotes/{quote_id}/auto-discount", summary="自动折扣计算")
def calculate_auto_discount(
    quote_id: int = Path(..., description="报价ID"),
    customer_level: str = Query(..., description="客户等级：A/B/C/D"),
    order_volume: Optional[int] = Query(None, description="订单数量"),
    payment_terms: Optional[str] = Query(None, description="付款条件"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    根据客户等级自动计算折扣
    
    折扣规则：
    - A级客户：基础折扣8% + 量大优惠2% + 付款优惠1%
    - B级客户：基础折扣5% + 量大优惠2%
    - C级客户：基础折扣3%
    - D级客户：无折扣
    
    返回：
    - 原始价格
    - 各项折扣
    - 最终价格
    """
    
    # 模拟原始价格
    original_price = 3500000
    
    # 根据等级计算折扣
    discounts = []
    total_discount = 0
    
    if customer_level == "A":
        base_discount = 8
        discounts.append({"name": "A级客户基础折扣", "rate": 8, "amount": original_price * 0.08})
        
        if order_volume and order_volume >= 3:
            volume_discount = 2
            discounts.append({"name": "批量订单优惠", "rate": 2, "amount": original_price * 0.02})
            total_discount += volume_discount
        
        if payment_terms == "预付":
            payment_discount = 1
            discounts.append({"name": "预付优惠", "rate": 1, "amount": original_price * 0.01})
            total_discount += payment_discount
            
        total_discount += base_discount
        
    elif customer_level == "B":
        base_discount = 5
        discounts.append({"name": "B级客户基础折扣", "rate": 5, "amount": original_price * 0.05})
        
        if order_volume and order_volume >= 5:
            volume_discount = 2
            discounts.append({"name": "批量订单优惠", "rate": 2, "amount": original_price * 0.02})
            total_discount += volume_discount
            
        total_discount += base_discount
        
    elif customer_level == "C":
        base_discount = 3
        discounts.append({"name": "C级客户基础折扣", "rate": 3, "amount": original_price * 0.03})
        total_discount = base_discount
    else:
        discounts.append({"name": "D级客户无折扣", "rate": 0, "amount": 0})
        total_discount = 0
    
    final_price = original_price * (1 - total_discount / 100)
    
    return {
        "quote_id": quote_id,
        "customer_level": customer_level,
        "original_price": original_price,
        "discounts": discounts,
        "total_discount_rate": total_discount,
        "total_discount_amount": original_price * total_discount / 100,
        "final_price": final_price,
        "savings": original_price - final_price,
    }


# ========== 5. 赢单率预测 ==========

@router.get("/opportunities/{opportunity_id}/win-rate-prediction", summary="赢单率预测")
def predict_win_rate(
    opportunity_id: int = Path(..., description="商机ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    AI预测报价赢单概率
    
    考虑因素：
    - 客户历史成交率
    - 竞争情况
    - 价格竞争力
    - 项目紧急度
    - 客户关系深度
    
    返回：
    - 赢单率百分比
    - 影响因素分析
    - 提升建议
    """
    
    # 模拟预测逻辑
    factors = [
        {"name": "客户历史成交率", "weight": 25, "score": 80, "impact": "正面"},
        {"name": "价格竞争力", "weight": 20, "score": 70, "impact": "正面"},
        {"name": "技术方案匹配度", "weight": 20, "score": 90, "impact": "正面"},
        {"name": "客户关系深度", "weight": 15, "score": 75, "impact": "正面"},
        {"name": "项目紧急度", "weight": 10, "score": 60, "impact": "中性"},
        {"name": "竞争激烈程度", "weight": 10, "score": 50, "impact": "负面"},
    ]
    
    # 计算加权得分
    total_score = sum(f["score"] * f["weight"] for f in factors) / 100
    win_rate = round(total_score)
    
    # 确定风险等级
    if win_rate >= 70:
        risk_level = "LOW"
        suggestion = "当前状态良好，保持跟进节奏"
    elif win_rate >= 50:
        risk_level = "MEDIUM"
        suggestion = "需要加强客户关系，考虑适当降价"
    else:
        risk_level = "HIGH"
        suggestion = "风险较高，需要高层介入，重新评估方案"
    
    return {
        "opportunity_id": opportunity_id,
        "win_rate": win_rate,
        "risk_level": risk_level,
        "confidence": 75,  # 预测置信度
        "factors": factors,
        "suggestion": suggestion,
        "improvement_actions": [
            "加强与技术决策人的沟通",
            "提供案例参观机会",
            "考虑增加服务承诺",
            "邀请客户参加技术交流会",
        ],
    }


@router.post("/batch-win-rate-prediction", summary="批量赢单率预测")
def batch_predict_win_rate(
    opportunity_ids: List[int] = Body(..., description="商机ID列表"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """批量预测多个商机的赢单率"""
    
    results = []
    for opp_id in opportunity_ids:
        # 模拟预测
        win_rate = 50 + (opp_id % 40)  # 50-90之间的随机值
        results.append({
            "opportunity_id": opp_id,
            "win_rate": win_rate,
            "risk_level": "HIGH" if win_rate < 50 else "MEDIUM" if win_rate < 70 else "LOW",
        })
    
    # 按赢单率排序
    results.sort(key=lambda x: x["win_rate"], reverse=True)
    
    return {
        "total_count": len(results),
        "high_win_rate_count": len([r for r in results if r["win_rate"] >= 70]),
        "medium_win_rate_count": len([r for r in results if 50 <= r["win_rate"] < 70]),
        "low_win_rate_count": len([r for r in results if r["win_rate"] < 50]),
        "predictions": results,
    }

# -*- coding: utf-8 -*-
"""
一键成本推荐 API

提供快速成本推荐接口，简化业务员获取成本建议的流程。
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.models.sales import Opportunity, Quote
from app.models.user import User
from app.schemas.common import ResponseModel

logger = logging.getLogger(__name__)

router = APIRouter()


# 行业成本系数配置
INDUSTRY_COST_FACTORS = {
    "锂电": {"material_factor": 1.0, "labor_factor": 1.0, "complexity_factor": 1.0},
    "汽车": {"material_factor": 1.1, "labor_factor": 1.05, "complexity_factor": 1.1},
    "电子": {"material_factor": 0.95, "labor_factor": 1.0, "complexity_factor": 0.9},
    "医疗": {"material_factor": 1.2, "labor_factor": 1.15, "complexity_factor": 1.2},
    "半导体": {"material_factor": 1.15, "labor_factor": 1.1, "complexity_factor": 1.15},
    "default": {"material_factor": 1.0, "labor_factor": 1.0, "complexity_factor": 1.0},
}

# 项目类型基准成本配置（万元）
PROJECT_TYPE_BASE_COSTS = {
    "FCT": {"base": 80, "range": (50, 150)},
    "EOL": {"base": 100, "range": (70, 200)},
    "ICT": {"base": 60, "range": (40, 120)},
    "AOI": {"base": 70, "range": (45, 130)},
    "一体化": {"base": 150, "range": (100, 300)},
    "default": {"base": 80, "range": (50, 150)},
}

# 毛利率目标配置
TARGET_MARGINS = {
    "锂电": {"min": 25, "target": 30, "max": 35},
    "汽车": {"min": 20, "target": 25, "max": 30},
    "电子": {"min": 30, "target": 35, "max": 40},
    "医疗": {"min": 35, "target": 40, "max": 45},
    "default": {"min": 25, "target": 30, "max": 35},
}


def _get_historical_average(
    db: Session, industry: Optional[str], project_type: Optional[str]
) -> Optional[dict]:
    """
    获取历史平均数据

    基于类似项目的历史成交数据计算平均值
    """
    # 查询历史赢单的商机
    query = db.query(Opportunity).filter(Opportunity.stage == "CLOSED_WON")

    if industry:
        query = query.join(Opportunity.customer).filter(
            Opportunity.customer.has(industry=industry)
        )

    if project_type:
        query = query.filter(Opportunity.project_type == project_type)

    opportunities = query.limit(20).all()

    if not opportunities:
        return None

    # 计算平均值
    amounts = [float(opp.est_amount) for opp in opportunities if opp.est_amount]
    if not amounts:
        return None

    return {
        "count": len(amounts),
        "avg_amount": sum(amounts) / len(amounts),
        "min_amount": min(amounts),
        "max_amount": max(amounts),
    }


@router.get("/opportunities/{opp_id}/quick-cost", response_model=ResponseModel)
def get_quick_cost_recommendation(
    opp_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    一键获取商机成本推荐

    基于商机信息快速生成成本估算和定价建议：
    - 根据行业和项目类型匹配历史数据
    - 应用行业成本系数
    - 计算推荐价格区间
    - 提供毛利率目标

    适合业务员在商机初期快速评估项目成本。
    """
    # 获取商机信息
    opportunity = (
        db.query(Opportunity)
        .options(joinedload(Opportunity.customer))
        .filter(Opportunity.id == opp_id)
        .first()
    )

    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    # 获取基础信息
    industry = opportunity.customer.industry if opportunity.customer else None
    project_type = opportunity.project_type
    est_amount = float(opportunity.est_amount) if opportunity.est_amount else None

    # 获取行业系数
    factors = INDUSTRY_COST_FACTORS.get(industry, INDUSTRY_COST_FACTORS["default"])

    # 获取项目类型基准成本
    base_config = PROJECT_TYPE_BASE_COSTS.get(
        project_type, PROJECT_TYPE_BASE_COSTS["default"]
    )

    # 获取毛利率目标
    margins = TARGET_MARGINS.get(industry, TARGET_MARGINS["default"])

    # 计算估算成本
    base_cost = base_config["base"] * 10000  # 转换为元
    estimated_cost = base_cost * factors["material_factor"] * factors["complexity_factor"]

    # 计算推荐价格
    target_margin = margins["target"] / 100
    min_margin = margins["min"] / 100
    max_margin = margins["max"] / 100

    recommended_price = estimated_cost / (1 - target_margin)
    price_range_low = estimated_cost / (1 - min_margin)
    price_range_high = estimated_cost / (1 - max_margin)

    # 获取历史参考
    historical = _get_historical_average(db, industry, project_type)

    # 生成建议
    suggestions = []
    if est_amount:
        implied_margin = (est_amount - estimated_cost) / est_amount * 100
        if implied_margin < margins["min"]:
            suggestions.append(f"⚠️ 预估金额对应毛利率 {implied_margin:.1f}%，低于目标 {margins['min']}%")
            suggestions.append(f"建议价格调整至 {price_range_low:,.0f} 元以上")
        elif implied_margin > margins["max"]:
            suggestions.append(f"✓ 预估金额对应毛利率 {implied_margin:.1f}%，高于目标区间")
        else:
            suggestions.append(f"✓ 预估金额对应毛利率 {implied_margin:.1f}%，在目标区间内")

    if historical:
        suggestions.append(
            f"参考：类似项目历史平均成交 {historical['avg_amount']:,.0f} 元 "
            f"(基于 {historical['count']} 个项目)"
        )

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "opportunity_id": opp_id,
            "opportunity_name": opportunity.opp_name,
            "customer_name": opportunity.customer.customer_name if opportunity.customer else None,
            "industry": industry,
            "project_type": project_type,
            # 成本估算
            "estimated_cost": round(estimated_cost, 2),
            "cost_factors": {
                "base_cost": base_cost,
                "material_factor": factors["material_factor"],
                "complexity_factor": factors["complexity_factor"],
            },
            # 推荐价格
            "recommended_price": round(recommended_price, 2),
            "price_range": {
                "low": round(price_range_low, 2),
                "high": round(price_range_high, 2),
            },
            # 毛利率目标
            "margin_targets": {
                "min": margins["min"],
                "target": margins["target"],
                "max": margins["max"],
            },
            # 历史参考
            "historical_reference": historical,
            # 当前预估对比
            "current_estimate": {
                "amount": est_amount,
                "implied_margin": round(
                    (est_amount - estimated_cost) / est_amount * 100, 1
                ) if est_amount and est_amount > 0 else None,
            },
            # 建议
            "suggestions": suggestions,
        },
    )


@router.get("/quotes/{quote_id}/quick-cost", response_model=ResponseModel)
def get_quote_quick_cost(
    quote_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    一键获取报价成本分析

    快速分析现有报价的成本结构和优化空间：
    - 计算当前毛利率
    - 与行业目标对比
    - 提供优化建议
    """
    # 获取报价
    quote = (
        db.query(Quote)
        .options(
            joinedload(Quote.customer),
            joinedload(Quote.current_version),
            joinedload(Quote.opportunity),
        )
        .filter(Quote.id == quote_id)
        .first()
    )

    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    version = quote.current_version
    if not version:
        raise HTTPException(status_code=400, detail="报价没有当前版本")

    # 获取基础信息
    industry = quote.customer.industry if quote.customer else None
    total_price = float(version.total_price) if version.total_price else 0
    total_cost = float(version.total_cost) if version.total_cost else 0

    # 获取毛利率目标
    margins = TARGET_MARGINS.get(industry, TARGET_MARGINS["default"])

    # 计算当前毛利率
    current_margin = (
        (total_price - total_cost) / total_price * 100 if total_price > 0 else 0
    )

    # 生成分析
    analysis = {
        "status": "normal",
        "message": "",
    }

    if current_margin < margins["min"]:
        analysis["status"] = "warning"
        analysis["message"] = f"毛利率 {current_margin:.1f}% 低于最低目标 {margins['min']}%"
        suggested_price = total_cost / (1 - margins["min"] / 100)
        analysis["suggested_adjustment"] = round(suggested_price - total_price, 2)
    elif current_margin < margins["target"]:
        analysis["status"] = "attention"
        analysis["message"] = f"毛利率 {current_margin:.1f}% 低于目标 {margins['target']}%"
    else:
        analysis["status"] = "good"
        analysis["message"] = f"毛利率 {current_margin:.1f}% 达到目标"

    # 优化建议
    suggestions = []
    if analysis["status"] == "warning":
        suggestions.append("考虑优化成本结构或调整报价")
        suggestions.append(f"建议价格调整至 {total_cost / (1 - margins['min'] / 100):,.0f} 元以上")
    elif analysis["status"] == "attention":
        potential_increase = total_cost / (1 - margins["target"] / 100) - total_price
        suggestions.append(f"如提价 {potential_increase:,.0f} 元，可达目标毛利率")

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "quote_id": quote_id,
            "quote_code": quote.quote_code,
            "customer_name": quote.customer.customer_name if quote.customer else None,
            "industry": industry,
            # 当前数据
            "current": {
                "total_price": total_price,
                "total_cost": total_cost,
                "margin": round(current_margin, 1),
            },
            # 目标对比
            "targets": {
                "min_margin": margins["min"],
                "target_margin": margins["target"],
                "max_margin": margins["max"],
            },
            # 分析结果
            "analysis": analysis,
            # 优化建议
            "suggestions": suggestions,
        },
    )

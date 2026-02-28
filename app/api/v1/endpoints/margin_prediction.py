# -*- coding: utf-8 -*-
"""
毛利率预测 API
- 基于历史项目数据预测新项目/报价的毛利率
- 按设备类型、客户行业、合同金额区间分析
- 成本结构对比和偏差分析
"""

from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================

class CostBreakdown(BaseModel):
    cost_type: str
    amount: float
    percentage: float


class HistoricalProject(BaseModel):
    project_id: int
    project_name: str
    project_code: str
    product_category: Optional[str] = None
    industry: Optional[str] = None
    contract_amount: float
    actual_cost: float
    gross_margin: float  # (contract - cost) / contract * 100
    cost_breakdown: List[CostBreakdown] = []
    stage: Optional[str] = None


class MarginPrediction(BaseModel):
    predicted_margin: float  # 预测毛利率 %
    confidence: float  # 置信度 0-1
    margin_range: tuple  # (min, max) %
    similar_projects_count: int
    avg_margin: float
    median_margin: float
    risk_level: str  # low/medium/high
    cost_structure: List[CostBreakdown]
    similar_projects: List[HistoricalProject]
    recommendations: List[str]


class MarginAnalysisResponse(BaseModel):
    historical_summary: dict
    by_category: List[dict]
    by_amount_range: List[dict]
    prediction: Optional[MarginPrediction] = None


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/historical", summary="历史毛利率分析")
def get_historical_margins(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """分析所有已完成/进行中项目的毛利率。"""

    sql = text("""
        SELECT 
            p.id, p.project_name, p.project_code,
            p.product_category, p.industry, p.stage,
            p.contract_amount, p.actual_cost,
            CASE WHEN p.contract_amount > 0 
                THEN ROUND((p.contract_amount - p.actual_cost) * 100.0 / p.contract_amount, 2)
                ELSE 0 END as gross_margin
        FROM projects p
        WHERE p.is_active = 1 AND p.contract_amount > 0
        ORDER BY p.id
    """)
    rows = db.execute(sql).fetchall()

    projects = []
    total_margin = 0
    margins = []

    for r in rows:
        # Get cost breakdown
        cost_sql = text("""
            SELECT cost_type, SUM(amount) as total
            FROM project_costs WHERE project_id = :pid
            GROUP BY cost_type ORDER BY total DESC
        """)
        cost_rows = db.execute(cost_sql, {"pid": r.id}).fetchall()
        total_cost = sum(c.total for c in cost_rows) if cost_rows else float(r.actual_cost or 0)

        breakdown = []
        for c in cost_rows:
            breakdown.append(CostBreakdown(
                cost_type=c.cost_type,
                amount=float(c.total),
                percentage=round(float(c.total) / total_cost * 100, 1) if total_cost > 0 else 0,
            ))

        margin = float(r.gross_margin)
        projects.append(HistoricalProject(
            project_id=r.id,
            project_name=r.project_name,
            project_code=r.project_code,
            product_category=r.product_category,
            industry=r.industry,
            contract_amount=float(r.contract_amount),
            actual_cost=float(r.actual_cost or 0),
            gross_margin=margin,
            cost_breakdown=breakdown,
            stage=r.stage,
        ))
        margins.append(margin)
        total_margin += margin

    # By category
    cat_map = {}
    for p in projects:
        cat = p.product_category or "未分类"
        if cat not in cat_map:
            cat_map[cat] = {"margins": [], "count": 0, "total_contract": 0, "total_cost": 0}
        cat_map[cat]["margins"].append(p.gross_margin)
        cat_map[cat]["count"] += 1
        cat_map[cat]["total_contract"] += p.contract_amount
        cat_map[cat]["total_cost"] += p.actual_cost

    by_category = []
    for cat, data in cat_map.items():
        avg_m = sum(data["margins"]) / len(data["margins"]) if data["margins"] else 0
        by_category.append({
            "category": cat,
            "count": data["count"],
            "avg_margin": round(avg_m, 2),
            "min_margin": round(min(data["margins"]), 2) if data["margins"] else 0,
            "max_margin": round(max(data["margins"]), 2) if data["margins"] else 0,
            "total_contract": data["total_contract"],
            "total_cost": data["total_cost"],
        })

    # By amount range
    ranges = [(0, 2000000, "200万以下"), (2000000, 3500000, "200-350万"), (3500000, 99999999, "350万以上")]
    by_amount = []
    for low, high, label in ranges:
        range_projects = [p for p in projects if low <= p.contract_amount < high]
        if range_projects:
            avg_m = sum(p.gross_margin for p in range_projects) / len(range_projects)
            by_amount.append({
                "range": label,
                "count": len(range_projects),
                "avg_margin": round(avg_m, 2),
                "min_margin": round(min(p.gross_margin for p in range_projects), 2),
                "max_margin": round(max(p.gross_margin for p in range_projects), 2),
            })

    avg_margin = total_margin / len(margins) if margins else 0
    sorted_margins = sorted(margins)
    median_margin = sorted_margins[len(sorted_margins) // 2] if sorted_margins else 0

    return {
        "historical_summary": {
            "total_projects": len(projects),
            "avg_margin": round(avg_margin, 2),
            "median_margin": round(median_margin, 2),
            "min_margin": round(min(margins), 2) if margins else 0,
            "max_margin": round(max(margins), 2) if margins else 0,
            "total_contract_value": sum(p.contract_amount for p in projects),
            "total_actual_cost": sum(p.actual_cost for p in projects),
        },
        "projects": [p.model_dump() for p in projects],
        "by_category": by_category,
        "by_amount_range": by_amount,
    }


@router.get("/predict", summary="预测新项目毛利率")
def predict_margin(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    product_category: Optional[str] = Query(None, description="产品类型(ICT/FCT/EOL等)"),
    industry: Optional[str] = Query(None, description="客户行业"),
    contract_amount: float = Query(..., description="预估合同金额"),
) -> Any:
    """
    根据历史数据预测新项目毛利率。
    
    算法：
    1. 找相似项目（同类型/行业/金额区间）
    2. 加权平均毛利率（越相似权重越高）
    3. 根据样本量计算置信度
    """
    # Get all historical projects
    sql = text("""
        SELECT 
            p.id, p.project_name, p.project_code,
            p.product_category, p.industry,
            p.contract_amount, p.actual_cost,
            CASE WHEN p.contract_amount > 0 
                THEN (p.contract_amount - p.actual_cost) * 100.0 / p.contract_amount
                ELSE 0 END as gross_margin
        FROM projects p
        WHERE p.is_active = 1 AND p.contract_amount > 0 AND p.actual_cost > 0
    """)
    rows = db.execute(sql).fetchall()

    if not rows:
        return {"error": "没有足够的历史数据进行预测", "prediction": None}

    # Score similarity
    scored = []
    for r in rows:
        score = 0.0
        # Category match: +40
        if product_category and r.product_category == product_category:
            score += 40
        elif not product_category:
            score += 20  # No filter = neutral

        # Industry match: +20
        if industry and r.industry == industry:
            score += 20
        elif not industry:
            score += 10

        # Amount similarity: +40 (closer = higher)
        if r.contract_amount > 0:
            ratio = min(contract_amount, float(r.contract_amount)) / max(contract_amount, float(r.contract_amount))
            score += ratio * 40

        scored.append((r, score, float(r.gross_margin)))

    # Sort by similarity
    scored.sort(key=lambda x: -x[1])

    # Weighted prediction
    total_weight = 0
    weighted_margin = 0
    margins = []
    similar_projects = []

    for r, score, margin in scored:
        weight = score / 100.0
        weighted_margin += margin * weight
        total_weight += weight
        margins.append(margin)

        similar_projects.append({
            "project_id": r.id,
            "project_name": r.project_name,
            "project_code": r.project_code,
            "product_category": r.product_category,
            "contract_amount": float(r.contract_amount),
            "actual_cost": float(r.actual_cost),
            "gross_margin": round(margin, 2),
            "similarity_score": round(score, 1),
        })

    predicted = weighted_margin / total_weight if total_weight > 0 else 0
    avg_margin = sum(margins) / len(margins) if margins else 0

    # Confidence based on sample size and similarity scores
    top_score = scored[0][1] if scored else 0
    confidence = min(0.95, (len(scored) / 10.0) * 0.5 + (top_score / 100.0) * 0.5)

    # Margin range (mean ± std)
    if len(margins) > 1:
        mean = sum(margins) / len(margins)
        variance = sum((m - mean) ** 2 for m in margins) / len(margins)
        std = variance ** 0.5
        margin_min = round(max(0, predicted - std), 2)
        margin_max = round(min(100, predicted + std), 2)
    else:
        margin_min = round(predicted * 0.8, 2)
        margin_max = round(predicted * 1.2, 2)

    # Risk level
    if predicted < 15:
        risk_level = "high"
    elif predicted < 25:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Average cost structure from similar projects
    cost_sql = text("""
        SELECT cost_type, AVG(pct) as avg_pct FROM (
            SELECT pc.cost_type, 
                   SUM(pc.amount) * 100.0 / NULLIF(p.actual_cost, 0) as pct
            FROM project_costs pc
            JOIN projects p ON pc.project_id = p.id
            WHERE p.actual_cost > 0
            GROUP BY pc.project_id, pc.cost_type
        ) GROUP BY cost_type ORDER BY avg_pct DESC
    """)
    cost_rows = db.execute(cost_sql).fetchall()
    cost_structure = [
        {"cost_type": r.cost_type, "percentage": round(float(r.avg_pct), 1)}
        for r in cost_rows
    ]

    # Recommendations
    recommendations = []
    if predicted < 20:
        recommendations.append("⚠️ 预测毛利率偏低，建议审查报价是否充分覆盖成本")
    if product_category:
        cat_projects = [s for s in scored if s[0].product_category == product_category]
        if len(cat_projects) < 3:
            recommendations.append(f"📊 {product_category}类型项目样本量不足（仅{len(cat_projects)}个），预测参考价值有限")
    if contract_amount > 4000000:
        recommendations.append("💰 大金额项目建议额外预留5-8%风险准备金")
    if any(m < 10 for _, _, m in scored[:3]):
        recommendations.append("⚡ 近似项目中有低毛利案例，注意成本控制")

    predicted_cost = contract_amount * (1 - predicted / 100)

    return {
        "prediction": {
            "predicted_margin": round(predicted, 2),
            "predicted_cost": round(predicted_cost, 0),
            "predicted_profit": round(contract_amount - predicted_cost, 0),
            "confidence": round(confidence, 2),
            "margin_range": [margin_min, margin_max],
            "risk_level": risk_level,
            "avg_historical_margin": round(avg_margin, 2),
            "similar_projects_count": len(similar_projects),
        },
        "cost_structure": cost_structure,
        "similar_projects": similar_projects[:5],
        "recommendations": recommendations,
        "input": {
            "product_category": product_category,
            "industry": industry,
            "contract_amount": contract_amount,
        },
    }


@router.get("/variance", summary="报价vs实际成本偏差分析")
def get_cost_variance(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """项目完结后，报价成本 vs 实际成本对比分析。"""
    sql = text("""
        SELECT 
            p.id, p.project_name, p.project_code,
            p.product_category,
            p.contract_amount, p.budget_amount, p.actual_cost,
            CASE WHEN p.contract_amount > 0 
                THEN ROUND((p.contract_amount - p.actual_cost) * 100.0 / p.contract_amount, 2) 
                ELSE 0 END as actual_margin,
            CASE WHEN p.contract_amount > 0 
                THEN ROUND((p.contract_amount - p.budget_amount) * 100.0 / p.contract_amount, 2) 
                ELSE 0 END as planned_margin,
            CASE WHEN p.budget_amount > 0
                THEN ROUND((p.actual_cost - p.budget_amount) * 100.0 / p.budget_amount, 2)
                ELSE 0 END as budget_variance_pct
        FROM projects p
        WHERE p.is_active = 1 AND p.contract_amount > 0 AND p.budget_amount > 0
        ORDER BY budget_variance_pct DESC
    """)
    rows = db.execute(sql).fetchall()

    projects = []
    for r in rows:
        # Cost breakdown variance
        cost_sql = text("""
            SELECT cost_type, SUM(amount) as total
            FROM project_costs WHERE project_id = :pid
            GROUP BY cost_type
        """)
        costs = {c.cost_type: float(c.total) for c in db.execute(cost_sql, {"pid": r.id}).fetchall()}

        projects.append({
            "project_id": r.id,
            "project_name": r.project_name,
            "project_code": r.project_code,
            "product_category": r.product_category,
            "contract_amount": float(r.contract_amount),
            "budget_amount": float(r.budget_amount),
            "actual_cost": float(r.actual_cost or 0),
            "planned_margin": float(r.planned_margin),
            "actual_margin": float(r.actual_margin),
            "margin_gap": round(float(r.actual_margin) - float(r.planned_margin), 2),
            "budget_variance_pct": float(r.budget_variance_pct),
            "overrun": float(r.actual_cost or 0) > float(r.budget_amount),
            "cost_breakdown": costs,
        })

    # Summary
    if projects:
        avg_variance = sum(p["budget_variance_pct"] for p in projects) / len(projects)
        overrun_count = sum(1 for p in projects if p["overrun"])
    else:
        avg_variance = 0
        overrun_count = 0

    return {
        "summary": {
            "total_projects": len(projects),
            "avg_budget_variance": round(avg_variance, 2),
            "overrun_count": overrun_count,
            "on_budget_count": len(projects) - overrun_count,
        },
        "projects": projects,
    }

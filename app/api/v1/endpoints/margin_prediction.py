# -*- coding: utf-8 -*-
"""
毛利率预测 API
- 基于历史项目数据预测新项目/报价的毛利率
- 按设备类型、客户行业、合同金额区间分析
- 成本结构对比和偏差分析
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
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
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """分析所有已完成/进行中项目的毛利率。"""

    sql = text(
        """
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
    """
    )
    rows = db.execute(sql).fetchall()

    projects = []
    total_margin = 0
    margins = []

    for r in rows:
        # Get cost breakdown
        cost_sql = text(
            """
            SELECT cost_type, SUM(amount) as total
            FROM project_costs WHERE project_id = :pid
            GROUP BY cost_type ORDER BY total DESC
        """
        )
        cost_rows = db.execute(cost_sql, {"pid": r.id}).fetchall()
        total_cost = sum(c.total for c in cost_rows) if cost_rows else float(r.actual_cost or 0)

        breakdown = []
        for c in cost_rows:
            breakdown.append(
                CostBreakdown(
                    cost_type=c.cost_type,
                    amount=float(c.total),
                    percentage=round(float(c.total) / total_cost * 100, 1) if total_cost > 0 else 0,
                )
            )

        margin = float(r.gross_margin)
        projects.append(
            HistoricalProject(
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
            )
        )
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
        by_category.append(
            {
                "category": cat,
                "count": data["count"],
                "avg_margin": round(avg_m, 2),
                "min_margin": round(min(data["margins"]), 2) if data["margins"] else 0,
                "max_margin": round(max(data["margins"]), 2) if data["margins"] else 0,
                "total_contract": data["total_contract"],
                "total_cost": data["total_cost"],
            }
        )

    # By amount range
    ranges = [
        (0, 2000000, "200万以下"),
        (2000000, 3500000, "200-350万"),
        (3500000, 99999999, "350万以上"),
    ]
    by_amount = []
    for low, high, label in ranges:
        range_projects = [p for p in projects if low <= p.contract_amount < high]
        if range_projects:
            avg_m = sum(p.gross_margin for p in range_projects) / len(range_projects)
            by_amount.append(
                {
                    "range": label,
                    "count": len(range_projects),
                    "avg_margin": round(avg_m, 2),
                    "min_margin": round(min(p.gross_margin for p in range_projects), 2),
                    "max_margin": round(max(p.gross_margin for p in range_projects), 2),
                }
            )

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
    current_user: User = Depends(security.get_current_active_user),
    product_category: Optional[str] = Query(None, description="产品类型 (ICT/FCT/EOL 等)"),
    industry: Optional[str] = Query(None, description="客户行业"),
    contract_amount: float = Query(..., description="预估合同金额"),
    estimated_material_cost: Optional[float] = Query(None, description="预计物料成本（BOM 成本）"),
    estimated_design_change_cost: Optional[float] = Query(None, description="预计设计变更物料费用"),
    estimated_travel_cost: Optional[float] = Query(None, description="预计出差费用"),
    estimated_rd_hours: Optional[int] = Query(None, description="预计研发工时 (小时)"),
    project_complexity: Optional[str] = Query("MEDIUM", description="项目复杂度 (LOW/MEDIUM/HIGH)"),
) -> Any:
    """
    根据历史数据 + 实际成本构成预测新项目毛利率。

    成本构成：
    1. 物料成本：BOM 成本 + 设计变更物料费用
    2. 人工成本：研发工时费用 + 生产工时费用
    3. 出差费用：现场调试/验收差旅费
    4. 制造费用：分摊的间接成本
    5. 风险准备金：行业风险系数

    毛利率 = (合同金额 - 总成本) / 合同金额 × 100%
    """

    # ========== 行业成本结构系数 ==========
    INDUSTRY_COEFFICIENTS = {
        "锂电": {
            "labor_ratio": 0.25,
            "overhead_ratio": 0.15,
            "risk_factor": 1.1,
            "travel_ratio": 0.03,
        },
        "光伏": {
            "labor_ratio": 0.22,
            "overhead_ratio": 0.13,
            "risk_factor": 1.05,
            "travel_ratio": 0.02,
        },
        "3C 电子": {
            "labor_ratio": 0.30,
            "overhead_ratio": 0.18,
            "risk_factor": 1.15,
            "travel_ratio": 0.04,
        },
        "汽车": {
            "labor_ratio": 0.28,
            "overhead_ratio": 0.16,
            "risk_factor": 1.2,
            "travel_ratio": 0.03,
        },
        "医疗": {
            "labor_ratio": 0.35,
            "overhead_ratio": 0.20,
            "risk_factor": 1.25,
            "travel_ratio": 0.05,
        },
        "半导体": {
            "labor_ratio": 0.32,
            "overhead_ratio": 0.18,
            "risk_factor": 1.3,
            "travel_ratio": 0.04,
        },
    }

    default_coefficient = {
        "labor_ratio": 0.28,
        "overhead_ratio": 0.16,
        "risk_factor": 1.15,
        "travel_ratio": 0.03,
    }
    industry_coef = INDUSTRY_COEFFICIENTS.get(industry, default_coefficient)

    # ========== 项目复杂度系数 ==========
    COMPLEXITY_COEFFICIENTS = {
        "LOW": {"labor_multiplier": 0.8, "overhead_multiplier": 0.9, "change_risk": 0.02},
        "MEDIUM": {"labor_multiplier": 1.0, "overhead_multiplier": 1.0, "change_risk": 0.05},
        "HIGH": {"labor_multiplier": 1.3, "overhead_multiplier": 1.2, "change_risk": 0.10},
    }
    complexity_coef = COMPLEXITY_COEFFICIENTS.get(
        project_complexity, COMPLEXITY_COEFFICIENTS["MEDIUM"]
    )

    # ========== 1. 物料成本 ==========
    # BOM 成本
    if estimated_material_cost and estimated_material_cost > 0:
        bom_cost = estimated_material_cost
    else:
        material_sql = text(
            """
            SELECT AVG(material_ratio) as avg_material_ratio FROM (
                SELECT pc.amount * 100.0 / NULLIF(p.contract_amount, 0) as material_ratio
                FROM project_costs pc JOIN projects p ON pc.project_id = p.id
                WHERE pc.cost_type = '材料' AND p.contract_amount > 0 LIMIT 20
            )
        """
        )
        material_result = db.execute(material_sql).fetchone()
        material_ratio = float(material_result.avg_material_ratio or 50.0) / 100.0
        bom_cost = contract_amount * material_ratio

    # 设计变更物料费用
    if estimated_design_change_cost and estimated_design_change_cost > 0:
        design_change_cost = estimated_design_change_cost
    else:
        # 根据历史数据和复杂度估算（通常占 BOM 的 2-10%）
        change_ratio = complexity_coef["change_risk"]
        design_change_cost = bom_cost * change_ratio

    total_material_cost = bom_cost + design_change_cost

    # ========== 2. 研发工时费用 ==========
    # 查询历史研发人员工时单价
    rd_rate_sql = text(
        """
        SELECT AVG(hourly_rate) as avg_rd_rate FROM (
            SELECT pc.amount / NULLIF(pc.work_hours, 0) as hourly_rate
            FROM project_costs pc
            JOIN projects p ON pc.project_id = p.id
            WHERE pc.cost_type IN ('研发工时', '设计工时') AND pc.work_hours > 0
            LIMIT 30
        )
    """
    )
    rd_rate_result = db.execute(rd_rate_sql).fetchone()
    rd_hourly_rate = float(rd_rate_result.avg_rd_rate or 150.0)  # 默认 150 元/小时

    # 研发工时费用
    if estimated_rd_hours and estimated_rd_hours > 0:
        rd_hours = estimated_rd_hours
    else:
        # 根据项目金额和复杂度估算
        base_rd_hours = contract_amount / 5000  # 每 5000 元合同约 1 小时研发
        rd_hours = int(base_rd_hours * complexity_coef["labor_multiplier"])

    rd_labor_cost = rd_hours * rd_hourly_rate

    # ========== 3. 生产人工成本 ==========
    # 查询历史生产人工成本占比
    production_labor_sql = text(
        """
        SELECT AVG(labor_ratio) as avg_prod_labor_ratio FROM (
            SELECT pc.amount * 100.0 / NULLIF(p.contract_amount, 0) as labor_ratio
            FROM project_costs pc
            JOIN projects p ON pc.project_id = p.id
            WHERE pc.cost_type IN ('生产工时', '装配工时', '调试工时')
            LIMIT 20
        )
    """
    )
    prod_labor_result = db.execute(production_labor_sql).fetchone()
    prod_labor_ratio = float(prod_labor_result.avg_prod_labor_ratio or 15.0) / 100.0
    production_labor_cost = contract_amount * prod_labor_ratio

    total_labor_cost = rd_labor_cost + production_labor_cost

    # ========== 4. 出差费用 ==========
    if estimated_travel_cost and estimated_travel_cost > 0:
        travel_cost = estimated_travel_cost
    else:
        # 根据行业系数和合同金额估算
        travel_cost = contract_amount * industry_coef["travel_ratio"]
        # 复杂度高的项目出差更多
        if project_complexity == "HIGH":
            travel_cost *= 1.5

    # ========== 5. 制造费用 ==========
    overhead_sql = text(
        """
        SELECT AVG(overhead_ratio) as avg_overhead_ratio FROM (
            SELECT SUM(pc.amount) * 100.0 / NULLIF(p.contract_amount, 0) as overhead_ratio
            FROM project_costs pc JOIN projects p ON pc.project_id = p.id
            WHERE pc.cost_type IN ('制造费用', '折旧', '水电', '场地')
            GROUP BY p.id LIMIT 20
        )
    """
    )
    overhead_result = db.execute(overhead_sql).fetchone()
    base_overhead_ratio = float(overhead_result.avg_overhead_ratio or 12.0) / 100.0
    overhead_cost = contract_amount * base_overhead_ratio * complexity_coef["overhead_multiplier"]

    # ========== 6. 总成本和毛利率 ==========
    base_total_cost = total_material_cost + total_labor_cost + travel_cost + overhead_cost

    # 应用行业风险系数
    risk_adjusted_cost = base_total_cost * industry_coef["risk_factor"]
    risk_reserve = risk_adjusted_cost - base_total_cost

    predicted_profit = contract_amount - risk_adjusted_cost
    predicted_margin = (predicted_profit / contract_amount) * 100 if contract_amount > 0 else 0

    # ========== 7. 置信度评估 ==========
    input_completeness = (
        sum(
            [
                1 if estimated_material_cost else 0,
                1 if estimated_design_change_cost else 0,
                1 if estimated_travel_cost else 0,
                1 if estimated_rd_hours else 0,
            ]
        )
        / 4.0
    )

    confidence = min(0.95, 0.4 + input_completeness * 0.4 + 0.2)
    data_quality = (
        "优秀"
        if input_completeness >= 0.75
        else (
            "良好"
            if input_completeness >= 0.5
            else "一般" if input_completeness >= 0.25 else "不足"
        )
    )

    # ========== 8. 成本结构 ==========
    cost_structure = [
        {
            "cost_type": "BOM 物料成本",
            "amount": round(bom_cost, 0),
            "percentage": (
                round(bom_cost / risk_adjusted_cost * 100, 1) if risk_adjusted_cost > 0 else 0
            ),
        },
        {
            "cost_type": "设计变更物料",
            "amount": round(design_change_cost, 0),
            "percentage": (
                round(design_change_cost / risk_adjusted_cost * 100, 1)
                if risk_adjusted_cost > 0
                else 0
            ),
        },
        {
            "cost_type": "研发工时",
            "amount": round(rd_labor_cost, 0),
            "percentage": (
                round(rd_labor_cost / risk_adjusted_cost * 100, 1) if risk_adjusted_cost > 0 else 0
            ),
            "detail": f"{rd_hours}小时 × ¥{rd_hourly_rate:.0f}/小时",
        },
        {
            "cost_type": "生产人工",
            "amount": round(production_labor_cost, 0),
            "percentage": (
                round(production_labor_cost / risk_adjusted_cost * 100, 1)
                if risk_adjusted_cost > 0
                else 0
            ),
        },
        {
            "cost_type": "出差费用",
            "amount": round(travel_cost, 0),
            "percentage": (
                round(travel_cost / risk_adjusted_cost * 100, 1) if risk_adjusted_cost > 0 else 0
            ),
        },
        {
            "cost_type": "制造费用",
            "amount": round(overhead_cost, 0),
            "percentage": (
                round(overhead_cost / risk_adjusted_cost * 100, 1) if risk_adjusted_cost > 0 else 0
            ),
        },
        {
            "cost_type": "风险准备金",
            "amount": round(risk_reserve, 0),
            "percentage": (
                round(risk_reserve / risk_adjusted_cost * 100, 1) if risk_adjusted_cost > 0 else 0
            ),
        },
    ]

    # ========== 9. 风险等级 ==========
    if predicted_margin < 15:
        risk_level = "high"
    elif predicted_margin < 25:
        risk_level = "medium"
    else:
        risk_level = "low"

    # ========== 10. 智能建议 ==========
    recommendations = []

    if input_completeness < 0.5:
        recommendations.append(
            f"📊 当前输入完整度{int(input_completeness*100)}%, 建议补充：{['物料成本','设计变更费用','出差费用','研发工时'][int((1-input_completeness)*4)]}"
        )

    if not estimated_material_cost:
        recommendations.append("⚠️ 未提供预计物料成本，已根据历史数据估算，建议输入准确 BOM 成本")

    if design_change_cost / bom_cost > 0.08:
        recommendations.append(
            f"⚠️ 设计变更费用占比过高 ({design_change_cost/bom_cost*100:.1f}%), 建议加强前期需求评审，减少后期变更"
        )

    if rd_labor_cost / contract_amount > 0.25:
        recommendations.append(
            f"💰 研发成本占比偏高 ({rd_labor_cost/contract_amount*100:.1f}%), 建议评估模块化设计或复用已有方案"
        )

    if travel_cost / contract_amount > 0.05:
        recommendations.append(
            f"✈️ 出差费用占比过高 ({travel_cost/contract_amount*100:.1f}%), 建议优化现场调试流程或远程支持"
        )

    if predicted_margin < 20:
        recommendations.append(
            "⚠️ 预测毛利率偏低，建议：1) 优化设计方案降低成本 2) 与供应商协商价格 3) 提高报价"
        )

    if industry_coef["risk_factor"] > 1.2:
        recommendations.append(
            f"⚡ {industry or '该'}行业风险系数较高 ({industry_coef['risk_factor']}), 建议预留充足风险准备金"
        )

    if project_complexity == "HIGH":
        recommendations.append("🔧 高复杂度项目人工成本和变更风险上浮，建议加强项目管理和变更控制")

    # ========== 11. 相似项目参考 ==========
    similar_sql = text(
        """
        SELECT p.id, p.project_name, p.project_code, p.product_category, p.industry,
            p.contract_amount, p.actual_cost,
            (p.contract_amount - p.actual_cost) * 100.0 / p.contract_amount as gross_margin
        FROM projects p
        WHERE p.is_active = 1 AND p.contract_amount > 0 AND p.actual_cost > 0
          AND (:industry IS NULL OR p.industry = :industry)
        ORDER BY ABS(p.contract_amount - :amount) LIMIT 5
    """
    )
    similar_rows = db.execute(
        similar_sql, {"industry": industry, "amount": contract_amount}
    ).fetchall()
    similar_projects = [
        {
            "project_id": r.id,
            "project_name": r.project_name,
            "project_code": r.project_code,
            "product_category": r.product_category,
            "industry": r.industry,
            "contract_amount": float(r.contract_amount),
            "actual_cost": float(r.actual_cost),
            "gross_margin": round(float(r.gross_margin), 2),
        }
        for r in similar_rows
    ]

    # ========== 12. 返回结果 ==========
    return {
        "prediction": {
            "predicted_margin": round(predicted_margin, 2),
            "predicted_cost": round(risk_adjusted_cost, 0),
            "predicted_profit": round(predicted_profit, 0),
            "confidence": round(confidence, 2),
            "data_quality": data_quality,
            "margin_range": [round(predicted_margin * 0.85, 2), round(predicted_margin * 1.15, 2)],
            "risk_level": risk_level,
            "similar_projects_count": len(similar_projects),
        },
        "cost_breakdown": {
            "contract_amount": round(contract_amount, 0),
            "bom_material_cost": round(bom_cost, 0),
            "design_change_cost": round(design_change_cost, 0),
            "rd_labor_cost": round(rd_labor_cost, 0),
            "rd_hours": rd_hours,
            "rd_hourly_rate": round(rd_hourly_rate, 0),
            "production_labor_cost": round(production_labor_cost, 0),
            "travel_cost": round(travel_cost, 0),
            "overhead_cost": round(overhead_cost, 0),
            "risk_adjustment": round(risk_reserve, 0),
            "total_cost": round(risk_adjusted_cost, 0),
            "profit": round(predicted_profit, 0),
        },
        "industry_analysis": {
            "industry": industry or "未知",
            "labor_ratio": round(industry_coef["labor_ratio"] * 100, 1),
            "overhead_ratio": round(industry_coef["overhead_ratio"] * 100, 1),
            "travel_ratio": round(industry_coef["travel_ratio"] * 100, 1),
            "risk_factor": industry_coef["risk_factor"],
            "complexity": project_complexity,
        },
        "cost_structure": cost_structure,
        "similar_projects": similar_projects,
        "recommendations": recommendations,
        "input": {
            "product_category": product_category,
            "industry": industry,
            "contract_amount": contract_amount,
            "estimated_material_cost": estimated_material_cost,
            "estimated_design_change_cost": estimated_design_change_cost,
            "estimated_travel_cost": estimated_travel_cost,
            "estimated_rd_hours": estimated_rd_hours,
            "project_complexity": project_complexity,
        },
    }


@router.get("/variance", summary="报价vs实际成本偏差分析")
def get_cost_variance(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """项目完结后，报价成本 vs 实际成本对比分析。"""
    sql = text(
        """
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
    """
    )
    rows = db.execute(sql).fetchall()

    projects = []
    for r in rows:
        # Cost breakdown variance
        cost_sql = text(
            """
            SELECT cost_type, SUM(amount) as total
            FROM project_costs WHERE project_id = :pid
            GROUP BY cost_type
        """
        )
        costs = {
            c.cost_type: float(c.total) for c in db.execute(cost_sql, {"pid": r.id}).fetchall()
        }

        projects.append(
            {
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
            }
        )

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


@router.get("/project/{project_id}/bom-costs", summary="获取项目 BOM 物料成本")
def get_project_bom_costs(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    自动获取项目 BOM 物料成本（从 BOM 表 + 采购价格）

    返回：
    - BOM 总成本
    - 分类成本（机械/电气/标准件/外购件）
    - 已采购/未采购状态
    - 最新采购价格
    """
    from app.models.material import BomHeader, BomItem
    from app.models.purchase import PurchaseOrder, PurchaseOrderItem

    # 查询项目 BOM
    bom_headers = (
        db.query(BomHeader)
        .filter(
            BomHeader.project_id == project_id, BomHeader.status == "RELEASED"  # 只统计已发布的 BOM
        )
        .all()
    )

    if not bom_headers:
        return {
            "project_id": project_id,
            "total_cost": 0,
            "message": "项目暂无已发布 BOM",
            "items": [],
        }

    bom_ids = [bom.id for bom in bom_headers]

    # 查询 BOM 明细
    bom_items = db.query(BomItem).filter(BomItem.bom_id.in_(bom_ids)).all()

    # 查询最新采购价格
    purchase_prices = {}
    purchase_orders = (
        db.query(PurchaseOrderItem, PurchaseOrder.order_date)
        .join(PurchaseOrder)
        .filter(PurchaseOrderItem.material_id.in_([item.material_id for item in bom_items]))
        .order_by(PurchaseOrder.order_date.desc())
        .all()
    )

    for po_item, order_date in purchase_orders:
        if po_item.material_id not in purchase_prices:
            purchase_prices[po_item.material_id] = {
                "unit_price": float(po_item.unit_price or 0),
                "supplier_id": po_item.supplier_id,
                "order_date": order_date.isoformat() if order_date else None,
            }

    # 计算成本
    total_cost = 0
    by_category = {}
    items_detail = []

    for item in bom_items:
        material = item.material if item.material_id else None
        if not material:
            continue

        # 优先使用最新采购价，其次使用物料标准价
        unit_price = 0
        source = "standard"

        if item.material_id in purchase_prices:
            unit_price = purchase_prices[item.material_id]["unit_price"]
            source = "purchase"
        elif material.unit_price:
            unit_price = float(material.unit_price)

        quantity = float(item.quantity or 0)
        item_cost = unit_price * quantity
        total_cost += item_cost

        # 分类统计
        category = material.category or "未分类"
        if category not in by_category:
            by_category[category] = {"cost": 0, "count": 0}
        by_category[category]["cost"] += item_cost
        by_category[category]["count"] += 1

        # 检查是否已采购
        is_purchased = item.material_id in purchase_prices

        items_detail.append(
            {
                "item_no": item.item_no,
                "material_id": material.id,
                "material_code": material.material_code,
                "material_name": material.material_name,
                "specification": material.specification,
                "category": category,
                "quantity": quantity,
                "unit": material.unit,
                "unit_price": unit_price,
                "total_price": item_cost,
                "price_source": source,
                "is_purchased": is_purchased,
                "supplier_name": purchase_prices.get(item.material_id, {}).get("supplier_id"),
            }
        )

    return {
        "project_id": project_id,
        "bom_version": bom_headers[0].version if bom_headers else None,
        "total_cost": round(total_cost, 2),
        "total_items": len(items_detail),
        "by_category": {
            cat: {"cost": round(data["cost"], 2), "count": data["count"]}
            for cat, data in by_category.items()
        },
        "purchased_count": sum(1 for item in items_detail if item["is_purchased"]),
        "unpurchased_count": sum(1 for item in items_detail if not item["is_purchased"]),
        "items": items_detail,
        "purchase_price_update_time": max(
            [p.get("order_date") for p in purchase_prices.values() if p.get("order_date")],
            default=None,
        ),
    }

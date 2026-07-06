# -*- coding: utf-8 -*-
"""Margin prediction routes used by the live margin analysis page."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project, ProjectCost
from app.models.user import User

router = APIRouter()


INDUSTRY_COEFFICIENTS = {
    "锂电": {"labor_ratio": 0.25, "overhead_ratio": 0.15, "risk_factor": 1.10, "travel_ratio": 0.03},
    "光伏": {"labor_ratio": 0.22, "overhead_ratio": 0.13, "risk_factor": 1.05, "travel_ratio": 0.02},
    "3C电子": {"labor_ratio": 0.30, "overhead_ratio": 0.18, "risk_factor": 1.15, "travel_ratio": 0.04},
    "3C 电子": {"labor_ratio": 0.30, "overhead_ratio": 0.18, "risk_factor": 1.15, "travel_ratio": 0.04},
    "汽车": {"labor_ratio": 0.28, "overhead_ratio": 0.16, "risk_factor": 1.20, "travel_ratio": 0.03},
    "医疗": {"labor_ratio": 0.35, "overhead_ratio": 0.20, "risk_factor": 1.25, "travel_ratio": 0.05},
    "半导体": {"labor_ratio": 0.32, "overhead_ratio": 0.18, "risk_factor": 1.30, "travel_ratio": 0.04},
}

DEFAULT_COEFFICIENT = {
    "labor_ratio": 0.28,
    "overhead_ratio": 0.16,
    "risk_factor": 1.15,
    "travel_ratio": 0.03,
}

COMPLEXITY_COEFFICIENTS = {
    "LOW": {"labor_multiplier": 0.8, "overhead_multiplier": 0.9, "change_risk": 0.02},
    "MEDIUM": {"labor_multiplier": 1.0, "overhead_multiplier": 1.0, "change_risk": 0.05},
    "HIGH": {"labor_multiplier": 1.3, "overhead_multiplier": 1.2, "change_risk": 0.10},
}


def _to_float(value: Any) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _round(value: Any, digits: int = 2) -> float:
    return round(_to_float(value), digits)


def _project_margin(project: Project) -> float:
    contract_amount = _to_float(project.contract_amount)
    actual_cost = _to_float(project.actual_cost)
    if contract_amount <= 0:
        return 0.0
    return _round((contract_amount - actual_cost) / contract_amount * 100)


def _planned_margin(project: Project) -> float:
    contract_amount = _to_float(project.contract_amount)
    budget_amount = _to_float(project.budget_amount)
    if contract_amount <= 0:
        return 0.0
    return _round((contract_amount - budget_amount) / contract_amount * 100)


def _load_projects(db: Session, limit: int = 50) -> List[Project]:
    query = (
        db.query(Project)
        .filter(Project.contract_amount.isnot(None))
        .filter(Project.contract_amount > 0)
        .order_by(desc(Project.created_at), desc(Project.id))
        .limit(limit)
    )
    return list(query.all())


def _project_payload(project: Project) -> Dict[str, Any]:
    gross_margin = _project_margin(project)
    return {
        "project_id": project.id,
        "project_name": project.project_name,
        "project_code": project.project_code,
        "product_category": project.product_category or "未分类",
        "industry": project.industry or "",
        "contract_amount": _round(project.contract_amount),
        "actual_cost": _round(project.actual_cost),
        "budget_amount": _round(project.budget_amount),
        "gross_margin": gross_margin,
        "stage": project.stage,
    }


def _amount_range(amount: float) -> str:
    if amount < 2_000_000:
        return "200万以下"
    if amount < 3_500_000:
        return "200-350万"
    return "350万以上"


def _summarize_margins(projects: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    project_list = list(projects)
    margins = [item["gross_margin"] for item in project_list]
    contract_values = [item["contract_amount"] for item in project_list]
    return {
        "total_projects": len(project_list),
        "avg_margin": _round(sum(margins) / len(margins)) if margins else 0,
        "max_margin": _round(max(margins)) if margins else 0,
        "min_margin": _round(min(margins)) if margins else 0,
        "total_contract_value": _round(sum(contract_values)),
    }


def _group_by_category(projects: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in projects:
        grouped[item["product_category"] or "未分类"].append(item)

    rows = []
    for category, items in sorted(grouped.items()):
        margins = [item["gross_margin"] for item in items]
        rows.append(
            {
                "category": category,
                "count": len(items),
                "avg_margin": _round(sum(margins) / len(margins)) if margins else 0,
                "min_margin": _round(min(margins)) if margins else 0,
                "max_margin": _round(max(margins)) if margins else 0,
                "total_contract": _round(sum(item["contract_amount"] for item in items)),
                "total_cost": _round(sum(item["actual_cost"] for item in items)),
            }
        )
    return rows


def _group_by_amount(projects: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in projects:
        grouped[_amount_range(item["contract_amount"])].append(item)

    rows = []
    for label in ["200万以下", "200-350万", "350万以上"]:
        items = grouped.get(label, [])
        margins = [item["gross_margin"] for item in items]
        rows.append(
            {
                "range": label,
                "count": len(items),
                "avg_margin": _round(sum(margins) / len(margins)) if margins else 0,
            }
        )
    return rows


@router.get("/historical")
def get_historical_margins(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
    limit: int = 50,
) -> Dict[str, Any]:
    """Return historical margin data in the shape consumed by MarginPrediction."""
    del current_user
    projects = [_project_payload(project) for project in _load_projects(db, limit)]
    return {
        "historical_summary": _summarize_margins(projects),
        "projects": projects,
        "by_category": _group_by_category(projects),
        "by_amount_range": _group_by_amount(projects),
    }


def _risk_level(predicted_margin: float) -> str:
    if predicted_margin < 15:
        return "high"
    if predicted_margin < 25:
        return "medium"
    return "low"


def _confidence(
    estimated_material_cost: Optional[float],
    estimated_design_change_cost: Optional[float],
    estimated_travel_cost: Optional[float],
    estimated_rd_hours: Optional[float],
) -> float:
    filled = sum(
        1
        for value in [
            estimated_material_cost,
            estimated_design_change_cost,
            estimated_travel_cost,
            estimated_rd_hours,
        ]
        if value not in (None, "")
    )
    return _round(min(0.95, 0.6 + filled / 4 * 0.35))


def _cost_part(label: str, amount: float, total: float) -> Dict[str, Any]:
    return {
        "label": label,
        "amount": _round(amount),
        "percentage": _round(amount / total * 100) if total > 0 else 0,
    }


@router.get("/predict")
def predict_margin(
    contract_amount: float,
    product_category: Optional[str] = None,
    industry: Optional[str] = None,
    estimated_material_cost: Optional[float] = None,
    estimated_design_change_cost: Optional[float] = None,
    estimated_travel_cost: Optional[float] = None,
    estimated_rd_hours: Optional[float] = None,
    project_complexity: str = "MEDIUM",
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Dict[str, Any]:
    """Predict margin from user-supplied assumptions and similar projects."""
    del current_user
    contract = max(_to_float(contract_amount), 0.0)
    coefficient = INDUSTRY_COEFFICIENTS.get(industry or "", DEFAULT_COEFFICIENT)
    complexity = COMPLEXITY_COEFFICIENTS.get(
        (project_complexity or "MEDIUM").upper(),
        COMPLEXITY_COEFFICIENTS["MEDIUM"],
    )

    material_cost = _to_float(estimated_material_cost) or contract * 0.5
    design_change_cost = (
        _to_float(estimated_design_change_cost)
        if estimated_design_change_cost not in (None, "")
        else material_cost * complexity["change_risk"]
    )
    travel_cost = (
        _to_float(estimated_travel_cost)
        if estimated_travel_cost not in (None, "")
        else contract * coefficient["travel_ratio"]
    )
    rd_labor_cost = (
        _to_float(estimated_rd_hours) * 150
        if estimated_rd_hours not in (None, "")
        else contract * coefficient["labor_ratio"] * 0.5
    )
    production_labor_cost = contract * coefficient["labor_ratio"] * 0.5 * complexity["labor_multiplier"]
    overhead_cost = contract * coefficient["overhead_ratio"] * complexity["overhead_multiplier"]

    subtotal = (
        material_cost
        + design_change_cost
        + travel_cost
        + rd_labor_cost
        + production_labor_cost
        + overhead_cost
    )
    predicted_cost = subtotal * coefficient["risk_factor"]
    predicted_profit = contract - predicted_cost
    predicted_margin = _round(predicted_profit / contract * 100) if contract > 0 else 0
    confidence = _confidence(
        estimated_material_cost,
        estimated_design_change_cost,
        estimated_travel_cost,
        estimated_rd_hours,
    )

    similar_projects = []
    try:
        project_rows = _load_projects(db, 50)
        if product_category:
            project_rows = [
                project
                for project in project_rows
                if (project.product_category or "") == product_category
            ]
        similar_projects = sorted(
            [_project_payload(project) for project in project_rows],
            key=lambda item: abs(item["contract_amount"] - contract),
        )[:5]
    except Exception:
        similar_projects = []

    recommendations: List[str] = []
    if predicted_margin < 15:
        recommendations.append("预测毛利率偏低，建议复核物料成本和外协报价。")
    if confidence < 0.75:
        recommendations.append("输入假设较少，补充 BOM、差旅或工时后置信度会更高。")
    if not recommendations:
        recommendations.append("预测毛利率处于可接受区间，建议持续跟踪实际成本偏差。")

    return {
        "prediction": {
            "predicted_margin": predicted_margin,
            "confidence": confidence,
            "risk_level": _risk_level(predicted_margin),
            "margin_range": [
                _round(predicted_margin - (1 - confidence) * 10),
                _round(predicted_margin + (1 - confidence) * 10),
            ],
            "predicted_cost": _round(predicted_cost),
            "predicted_profit": _round(predicted_profit),
        },
        "cost_breakdown": [
            _cost_part("材料成本", material_cost, predicted_cost),
            _cost_part("设计变更", design_change_cost, predicted_cost),
            _cost_part("差旅费用", travel_cost, predicted_cost),
            _cost_part("研发人工", rd_labor_cost, predicted_cost),
            _cost_part("生产人工", production_labor_cost, predicted_cost),
            _cost_part("制造费用", overhead_cost, predicted_cost),
        ],
        "recommendations": recommendations,
        "similar_projects": similar_projects,
    }


@router.get("/variance")
def get_margin_variance(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
    limit: int = 50,
) -> Dict[str, Any]:
    """Return budget-vs-actual margin variance rows for the page table."""
    del current_user
    rows = []
    for project in _load_projects(db, limit):
        planned_margin = _planned_margin(project)
        actual_margin = _project_margin(project)
        actual_cost = _to_float(project.actual_cost)
        budget_amount = _to_float(project.budget_amount)
        variance_amount = actual_cost - budget_amount
        variance_pct = variance_amount / budget_amount * 100 if budget_amount > 0 else 0
        rows.append(
            {
                **_project_payload(project),
                "planned_margin": planned_margin,
                "actual_margin": actual_margin,
                "margin_gap": _round(actual_margin - planned_margin),
                "variance_amount": _round(variance_amount),
                "variance_pct": _round(variance_pct),
                "overrun": variance_amount > 0,
            }
        )

    overrun_rows = [item for item in rows if item["overrun"]]
    return {
        "summary": {
            "total_projects": len(rows),
            "overrun_projects": len(overrun_rows),
            "avg_variance_pct": _round(
                sum(item["variance_pct"] for item in rows) / len(rows)
            )
            if rows
            else 0,
            "total_overrun_amount": _round(sum(item["variance_amount"] for item in overrun_rows)),
        },
        "projects": rows,
    }


def get_cost_variance(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
    limit: int = 50,
) -> Dict[str, Any]:
    """Backward-compatible alias for older tests/integrations."""
    return get_margin_variance(db=db, current_user=current_user, limit=limit)


@router.get("/project/{project_id}/bom-costs")
def get_project_bom_costs(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Dict[str, Any]:
    """Return a lightweight BOM/material cost summary for prediction import."""
    del current_user
    rows = (
        db.query(ProjectCost)
        .filter(ProjectCost.project_id == project_id)
        .filter(ProjectCost.amount.isnot(None))
        .all()
    )
    total_cost = sum(_to_float(row.amount) for row in rows)
    material_rows = [
        row
        for row in rows
        if (row.cost_type or row.cost_category or "").upper()
        in {"MATERIAL", "MATERIALS", "BOM", "PURCHASE", "材料"}
    ]
    return {
        "total_cost": _round(total_cost),
        "total_items": len(rows),
        "purchased_count": len(material_rows),
        "unpurchased_count": max(len(rows) - len(material_rows), 0),
        "message": "未找到 BOM 成本数据" if not rows else "BOM 成本已汇总",
    }


__all__ = [
    "router",
    "get_historical_margins",
    "predict_margin",
    "get_margin_variance",
    "get_cost_variance",
    "get_project_bom_costs",
]

# -*- coding: utf-8 -*-
"""
分解追溯

提供分解树查询和从个人 KPI 追溯到战略的功能
"""

"""
战略管理服务 - 目标分解

实现从公司战略到部门目标到个人 KPI 的层层分解
"""

import json
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.strategy import (
    CSF,
    KPI,
    DepartmentObjective,
    PersonalKPI,
    Strategy,
)
from app.models.user import User
from app.schemas.strategy import (
    DecompositionTreeNode,
    DecompositionTreeResponse,
    TraceToStrategyResponse,
)
from app.services.strategy.decomposition.personal_kpis import get_personal_kpi

# ============================================
# 分解追溯
# ============================================


NODE_ID_OFFSETS = {
    "strategy": 0,
    "csf": 1_000_000,
    "kpi": 2_000_000,
    "department": 3_000_000,
    "personal": 4_000_000,
}


def _node_id(kind: str, raw_id: int) -> int:
    return NODE_ID_OFFSETS[kind] + int(raw_id)


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _completion_rate(current_value: Any, target_value: Any) -> Optional[float]:
    current = _to_float(current_value)
    target = _to_float(target_value)
    if current is None or target in (None, 0):
        return None
    return round(min(100.0, current / target * 100), 2)


def _display_name(user: Optional[User]) -> Optional[str]:
    return user.display_name if user else None


def _department_name(department: Optional[Department], department_id: Optional[int]) -> str:
    if department:
        return department.dept_name
    return f"部门{department_id}" if department_id else "未分配部门"


def _health_level(completion_rate: Optional[float]) -> Optional[str]:
    if completion_rate is None:
        return None
    if completion_rate >= 100:
        return "EXCELLENT"
    if completion_rate >= 80:
        return "GOOD"
    if completion_rate >= 60:
        return "WARNING"
    return "DANGER"


def _frontend_status(status: Optional[str]) -> str:
    if status == "COMPLETED":
        return "COMPLETED"
    if status in {"AT_RISK", "OFF_TRACK", "ON_TRACK"}:
        return status
    return "ON_TRACK"


def _first_objective_text(value: Any) -> str:
    if value is None:
        return ""
    loaded = value
    if isinstance(value, str):
        try:
            loaded = json.loads(value)
        except json.JSONDecodeError:
            return value
    if isinstance(loaded, list):
        return str(loaded[0]) if loaded else ""
    if isinstance(loaded, dict):
        return str(loaded.get("name") or loaded.get("objective") or loaded)
    return str(loaded)


def _personal_kpi_completion(kpi: PersonalKPI) -> float:
    stored_rate = _to_float(kpi.completion_rate)
    if stored_rate is not None:
        return round(stored_rate, 2)
    calculated_rate = _completion_rate(kpi.actual_value, kpi.target_value)
    return round(calculated_rate or 0, 2)


def _personal_kpi_payload(kpi: PersonalKPI) -> dict[str, Any]:
    employee = kpi.employee
    return {
        "id": kpi.id,
        "name": kpi.kpi_name,
        "employee_id": kpi.employee_id,
        "employee_name": _display_name(employee),
        "target_value": _to_float(kpi.target_value) or 0,
        "actual_value": _to_float(kpi.actual_value) or 0,
        "completion_rate": _personal_kpi_completion(kpi),
        "weight": _to_float(kpi.weight) or 0,
        "status": _frontend_status(kpi.status),
        "self_rating_score": kpi.self_rating,
        "self_rating_comment": kpi.self_comment,
        "manager_rating_score": kpi.manager_rating,
        "manager_rating_comment": kpi.manager_comment,
    }


def _build_department_payload(db: Session, obj: DepartmentObjective) -> dict[str, Any]:
    department = db.query(Department).filter(Department.id == obj.department_id).first()
    personal_kpis = (
        db.query(PersonalKPI)
        .filter(PersonalKPI.department_objective_id == obj.id, PersonalKPI.is_active)
        .order_by(PersonalKPI.id)
        .all()
    )
    return {
        "id": obj.id,
        "department_id": obj.department_id,
        "department_name": _department_name(department, obj.department_id),
        "status": _frontend_status(obj.status),
        "objective": _first_objective_text(obj.objectives),
        "key_results": obj.key_results,
        "owner_user_id": obj.owner_user_id,
        "owner_name": _display_name(obj.owner),
        "kpis": [_personal_kpi_payload(kpi) for kpi in personal_kpis],
    }


def get_decomposition_tree(db: Session, strategy_id: int) -> DecompositionTreeResponse:
    """
    获取分解树

    Args:
        db: 数据库会话
        strategy_id: 战略 ID

    Returns:
        DecompositionTreeResponse: 分解树数据
    """
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.is_active).first()

    if not strategy:
        root = DecompositionTreeNode(
            id=_node_id("strategy", strategy_id),
            type="strategy",
            name="",
            level=0,
            children=[],
        )
        return DecompositionTreeResponse(
            strategy_id=strategy_id,
            strategy_name="",
            year=0,
            root=root,
        )

    root = DecompositionTreeNode(
        id=_node_id("strategy", strategy.id),
        type="strategy",
        name=strategy.name,
        level=0,
        children=[],
    )

    # 获取 CSF 节点
    csfs = (
        db.query(CSF)
        .filter(CSF.strategy_id == strategy_id, CSF.is_active)
        .order_by(CSF.dimension, CSF.sort_order)
        .all()
    )
    department_objectives = (
        db.query(DepartmentObjective)
        .filter(DepartmentObjective.strategy_id == strategy_id, DepartmentObjective.is_active)
        .order_by(DepartmentObjective.department_id, DepartmentObjective.id)
        .all()
    )
    department_payloads = [
        _build_department_payload(db, objective) for objective in department_objectives
    ]

    frontend_csfs: list[dict[str, Any]] = []
    personal_completion_rates: list[float] = []

    for csf in csfs:
        csf_node = DecompositionTreeNode(
            id=_node_id("csf", csf.id),
            type="csf",
            name=csf.name,
            level=1,
            parent_id=root.id,
            weight=_to_float(csf.weight) or 0,
            owner_name=_display_name(csf.owner),
            children=[],
        )

        # 获取 KPI 子节点
        kpis = (
            db.query(KPI)
            .filter(KPI.csf_id == csf.id, KPI.is_active)
            .order_by(KPI.id)
            .all()
        )

        for kpi in kpis:
            completion_rate = _completion_rate(kpi.current_value, kpi.target_value)
            kpi_node = DecompositionTreeNode(
                id=_node_id("kpi", kpi.id),
                type="kpi",
                name=kpi.name,
                level=2,
                parent_id=csf_node.id,
                weight=_to_float(kpi.weight) or 0,
                target_value=_to_float(kpi.target_value),
                current_value=_to_float(kpi.current_value),
                completion_rate=completion_rate,
                health_level=_health_level(completion_rate),
                owner_name=_display_name(kpi.owner),
                children=[],
            )
            csf_node.children.append(kpi_node)

        # Department objectives are linked to strategy in the current model, not
        # directly to company KPI. Keep them under CSF so the page has a stable
        # CSF -> department -> personal KPI view.
        for department_payload in department_payloads:
            obj_id = department_payload["id"]
            obj_node = DecompositionTreeNode(
                id=_node_id("department", obj_id),
                type="department",
                name=f"{department_payload['department_name']}目标",
                level=2,
                parent_id=csf_node.id,
                owner_name=department_payload["owner_name"],
                children=[],
            )
            for personal_payload in department_payload["kpis"]:
                personal_completion = personal_payload["completion_rate"]
                personal_completion_rates.append(personal_completion)
                pkpi_node = DecompositionTreeNode(
                    id=_node_id("personal", personal_payload["id"]),
                    type="personal",
                    name=f"{personal_payload['employee_name']}: {personal_payload['name']}",
                    level=3,
                    parent_id=obj_node.id,
                    weight=personal_payload["weight"],
                    target_value=personal_payload["target_value"],
                    current_value=personal_payload["actual_value"],
                    completion_rate=personal_completion,
                    health_level=_health_level(personal_completion),
                    owner_name=personal_payload["employee_name"],
                    children=[],
                )
                obj_node.children.append(pkpi_node)
            csf_node.children.append(obj_node)

        root.children.append(csf_node)
        frontend_csfs.append(
            {
                "id": csf.id,
                "code": csf.code,
                "name": csf.name,
                "description": csf.description,
                "dimension": csf.dimension,
                "weight": _to_float(csf.weight) or 0,
                "owner_name": _display_name(csf.owner),
                "company_kpis": [
                    {
                        "id": kpi.id,
                        "code": kpi.code,
                        "name": kpi.name,
                        "target_value": _to_float(kpi.target_value) or 0,
                        "current_value": _to_float(kpi.current_value) or 0,
                        "completion_rate": _completion_rate(
                            kpi.current_value, kpi.target_value
                        )
                        or 0,
                    }
                    for kpi in kpis
                ],
                "departments": department_payloads,
            }
        )

    total_personal_kpis = sum(len(department["kpis"]) for department in department_payloads)
    avg_completion_rate = (
        round(sum(personal_completion_rates) / len(personal_completion_rates), 2)
        if personal_completion_rates
        else 0
    )

    return DecompositionTreeResponse(
        strategy_id=strategy_id,
        strategy_name=strategy.name,
        year=strategy.year,
        root=root,
        csfs=frontend_csfs,
        total_csfs=len(csfs),
        total_departments=len(department_payloads),
        total_kpis=total_personal_kpis,
        total_personal_kpis=total_personal_kpis,
        avg_completion_rate=avg_completion_rate,
    )


def trace_to_strategy(db: Session, personal_kpi_id: int) -> Optional[TraceToStrategyResponse]:
    """
    从个人 KPI 追溯到战略

    Args:
        db: 数据库会话
        personal_kpi_id: 个人 KPI ID

    Returns:
        Optional[TraceToStrategyResponse]: 追溯链路
    """
    pkpi = get_personal_kpi(db, personal_kpi_id)
    if not pkpi:
        return None

    # 获取用户信息
    from app.models.user import User

    user = db.query(User).filter(User.id == pkpi.user_id).first()
    user_name = user.name if user else None

    # 获取部门目标
    dept_obj = None
    dept_name = None
    if pkpi.dept_objective_id:
        dept_obj = (
            db.query(DepartmentObjective)
            .filter(DepartmentObjective.id == pkpi.dept_objective_id)
            .first()
        )
        if dept_obj and dept_obj.department_id:
            from app.models.organization import Department

            dept = db.query(Department).filter(Department.id == dept_obj.department_id).first()
            dept_name = dept.name if dept else None

    # 获取公司 KPI
    company_kpi = None
    if pkpi.source_kpi_id:
        company_kpi = db.query(KPI).filter(KPI.id == pkpi.source_kpi_id).first()
    elif dept_obj and dept_obj.kpi_id:
        company_kpi = db.query(KPI).filter(KPI.id == dept_obj.kpi_id).first()

    # 获取 CSF
    csf = None
    if company_kpi:
        csf = db.query(CSF).filter(CSF.id == company_kpi.csf_id).first()

    # 获取战略
    strategy = None
    if csf:
        strategy = db.query(Strategy).filter(Strategy.id == csf.strategy_id).first()

    trace_path = [
        part
        for part in [
            pkpi.name,
            dept_name,
            company_kpi.name if company_kpi else None,
            csf.name if csf else None,
            strategy.name if strategy else None,
        ]
        if part
    ]

    return TraceToStrategyResponse(
        personal_kpi=pkpi,
        department_objective=dept_obj,
        kpi=(
            {
                "id": company_kpi.id,
                "name": company_kpi.name,
                "code": company_kpi.code,
            }
            if company_kpi
            else None
        ),
        csf=(
            {
                "id": csf.id,
                "name": csf.name,
                "dimension": csf.dimension,
            }
            if csf
            else None
        ),
        strategy=(
            {
                "id": strategy.id,
                "name": strategy.name,
                "year": strategy.year,
            }
            if strategy
            else None
        ),
        trace_path=trace_path,
    )

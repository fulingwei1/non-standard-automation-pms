# -*- coding: utf-8 -*-
"""Strategy decomposition tree API contract regression tests."""

import json
import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.organization import Department
from app.models.strategy import CSF, KPI, DepartmentObjective, PersonalKPI, Strategy
from app.models.user import User


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _ensure_test_user(db: Session) -> User:
    user = db.query(User).filter(User.username == "tree_contract_user").first()
    if user:
        return user

    user = User(
        username="tree_contract_user",
        password_hash=get_password_hash("tree-contract-pass"),
        real_name="Tree Contract User",
        department="Strategy",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def _assert_tree_node_contract(node: dict) -> None:
    assert isinstance(node["id"], int)
    assert isinstance(node["level"], int)
    assert node["parent_id"] is None or isinstance(node["parent_id"], int)
    for child in node.get("children", []):
        _assert_tree_node_contract(child)


def test_strategy_decomposition_tree_returns_schema_and_frontend_compat_fields(
    client: TestClient, db_session: Session, admin_token: str
):
    user = _ensure_test_user(db_session)
    department = Department(
        dept_code=_unique("TREE"),
        dept_name="Strategy Delivery",
        is_active=True,
    )
    strategy = Strategy(
        code=_unique("STR-TREE"),
        name="Tree Contract Strategy",
        year=2026,
        status="ACTIVE",
        is_active=True,
        created_by=user.id,
    )
    db_session.add_all([department, strategy])
    db_session.flush()

    csf = CSF(
        strategy_id=strategy.id,
        dimension="financial",
        code=_unique("CSF"),
        name="Revenue Growth",
        description="Grow revenue through strategic programs",
        weight=Decimal("35.00"),
        sort_order=1,
        owner_user_id=user.id,
        is_active=True,
    )
    db_session.add(csf)
    db_session.flush()

    kpi = KPI(
        csf_id=csf.id,
        code=_unique("KPI"),
        name="Signed Revenue",
        ipooc_type="OUTCOME",
        unit="million",
        target_value=Decimal("100.00"),
        current_value=Decimal("80.00"),
        weight=Decimal("60.00"),
        owner_user_id=user.id,
        is_active=True,
    )
    db_session.add(kpi)
    db_session.flush()

    objective = DepartmentObjective(
        strategy_id=strategy.id,
        department_id=department.id,
        year=2026,
        objectives=json.dumps(["Deliver revenue program"]),
        key_results=json.dumps(["Win lighthouse customers"]),
        status="IN_PROGRESS",
        owner_user_id=user.id,
        is_active=True,
    )
    db_session.add(objective)
    db_session.flush()

    personal_kpi = PersonalKPI(
        employee_id=user.id,
        year=2026,
        source_type="DEPT_OBJECTIVE",
        source_id=objective.id,
        department_objective_id=objective.id,
        kpi_name="Personal Revenue Contribution",
        target_value=Decimal("10.00"),
        actual_value=Decimal("7.00"),
        completion_rate=Decimal("70.00"),
        weight=Decimal("50.00"),
        self_rating=88,
        manager_rating=91,
        status="MANAGER_RATED",
        is_active=True,
    )
    db_session.add(personal_kpi)
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/strategy/decomposition/tree/{strategy.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["strategy_id"] == strategy.id
    assert payload["strategy_name"] == strategy.name
    assert payload["year"] == 2026
    _assert_tree_node_contract(payload["root"])

    assert payload["total_csfs"] == 1
    assert payload["total_departments"] == 1
    assert payload["total_kpis"] == 1
    assert payload["avg_completion_rate"] == 70.0

    csf_payload = payload["csfs"][0]
    assert csf_payload["id"] == csf.id
    assert csf_payload["dimension"] == "financial"
    assert csf_payload["departments"][0]["department_name"] == "Strategy Delivery"
    assert csf_payload["departments"][0]["kpis"][0]["name"] == "Personal Revenue Contribution"

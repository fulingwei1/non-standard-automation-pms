# -*- coding: utf-8 -*-
"""Permission contracts for HR PII and bonus payment endpoints."""

from datetime import date
from decimal import Decimal
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.models.bonus import BonusCalculation, BonusDistribution, BonusRule
from app.models.organization import Employee, EmployeeHrProfile
from app.models.user import ApiPermission, Role, RoleApiPermission, User, UserRole


def _headers(user: User) -> dict[str, str]:
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def _ensure_permission(db: Session, code: str, name: str) -> ApiPermission:
    permission = db.query(ApiPermission).filter(ApiPermission.perm_code == code).first()
    if permission:
        return permission
    permission = ApiPermission(
        perm_code=code,
        perm_name=name,
        module=code.split(":", 1)[0],
        action=code.split(":", 1)[1] if ":" in code else "read",
        permission_type="API",
        is_system=True,
        is_active=True,
    )
    db.add(permission)
    db.flush()
    return permission


def _create_user(
    db: Session,
    username: str,
    *,
    permissions: list[ApiPermission] | None = None,
) -> User:
    user = User(
        username=username,
        password_hash="not-used",
        auth_type="password",
        real_name=f"权限测试用户-{username}",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.flush()

    if permissions:
        role = Role(
            role_code=f"QA_ROLE_{username.upper()}",
            role_name=f"权限测试角色-{username}",
            is_active=True,
        )
        db.add(role)
        db.flush()
        db.add(UserRole(user_id=user.id, role_id=role.id))
        for permission in permissions:
            db.add(RoleApiPermission(role_id=role.id, permission_id=permission.id))
    db.flush()
    return user


def _create_employee(db: Session, suffix: str) -> Employee:
    employee = Employee(
        employee_code=f"E{suffix[:9]}",
        name=f"员工{suffix[:6]}",
        department="测试部",
        role="测试岗",
        phone="13800000000",
        id_card="440300199001010001",
    )
    db.add(employee)
    db.flush()
    profile = EmployeeHrProfile(
        employee_id=employee.id,
        bank_account="6222000000000000",
        social_security_no="SS-001",
        housing_fund_no="HF-001",
    )
    db.add(profile)
    db.flush()
    return employee


def _create_bonus_distribution(
    db: Session,
    *,
    suffix: str,
    user_id: int,
    status: str = "PENDING",
) -> BonusDistribution:
    rule = BonusRule(
        rule_code=f"BR{suffix}",
        rule_name="权限测试奖金规则",
        bonus_type="PERFORMANCE_BASED",
        is_active=True,
    )
    db.add(rule)
    db.flush()
    calculation = BonusCalculation(
        calculation_code=f"BC{suffix}",
        rule_id=rule.id,
        user_id=user_id,
        calculated_amount=Decimal("1000.00"),
        status="APPROVED",
    )
    db.add(calculation)
    db.flush()
    distribution = BonusDistribution(
        distribution_code=f"BD{suffix}",
        calculation_id=calculation.id,
        user_id=user_id,
        distributed_amount=Decimal("1000.00"),
        distribution_date=date(2026, 7, 3),
        payment_method="BANK",
        status=status,
    )
    db.add(distribution)
    db.flush()
    return distribution


def test_org_employee_and_hr_profile_endpoints_require_hr_permissions(
    client: TestClient,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    user = _create_user(db_session, f"qa_no_hr_{suffix}")
    employee = _create_employee(db_session, suffix)
    db_session.commit()

    headers = _headers(user)
    base = settings.API_V1_PREFIX

    checks = [
        client.get(f"{base}/org/employees", headers=headers),
        client.get(f"{base}/org/employees/{employee.id}", headers=headers),
        client.post(
            f"{base}/org/employees",
            json={"employee_code": f"N{suffix[:9]}", "name": "无权新增"},
            headers=headers,
        ),
        client.put(
            f"{base}/org/employees/{employee.id}",
            json={"phone": "13900000000"},
            headers=headers,
        ),
        client.get(f"{base}/org/hr-profiles", headers=headers),
        client.get(f"{base}/org/hr-profiles/{employee.id}", headers=headers),
        client.put(
            f"{base}/org/hr-profiles/{employee.id}",
            json={"bank_account": "6222999999999999"},
            headers=headers,
        ),
    ]

    for response in checks:
        assert response.status_code == 403, response.text


def test_bonus_payment_endpoints_require_bonus_permissions(
    client: TestClient,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    user = _create_user(db_session, f"qa_no_bonus_{suffix}")
    distribution = _create_bonus_distribution(db_session, suffix=suffix, user_id=user.id)
    db_session.commit()

    headers = _headers(user)
    base = settings.API_V1_PREFIX

    checks = [
        client.get(f"{base}/bonus/payment/distributions", headers=headers),
        client.get(f"{base}/bonus/payment/distributions/{distribution.id}", headers=headers),
        client.post(
            f"{base}/bonus/payment/distributions/{distribution.id}/pay",
            json={"voucher_no": "QA-VOUCHER"},
            headers=headers,
        ),
        client.post(
            f"{base}/bonus/payment/distribute",
            json={
                "calculation_id": distribution.calculation_id,
                "user_id": user.id,
                "distributed_amount": "1000.00",
                "distribution_date": "2026-07-03",
                "payment_method": "BANK",
            },
            headers=headers,
        ),
    ]

    for response in checks:
        assert response.status_code == 403, response.text


def test_bonus_read_permission_is_scoped_to_own_distributions(
    client: TestClient,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    bonus_read = _ensure_permission(db_session, "bonus:read", "查看奖金发放")
    actor = _create_user(db_session, f"qa_bonus_read_{suffix}", permissions=[bonus_read])
    other = _create_user(db_session, f"qa_bonus_other_{suffix}")
    own = _create_bonus_distribution(db_session, suffix=f"{suffix}A", user_id=actor.id)
    other_distribution = _create_bonus_distribution(
        db_session,
        suffix=f"{suffix}B",
        user_id=other.id,
    )
    db_session.commit()

    headers = _headers(actor)
    base = settings.API_V1_PREFIX

    list_response = client.get(f"{base}/bonus/payment/distributions", headers=headers)
    assert list_response.status_code == 200, list_response.text
    body = list_response.json()
    items = body.get("items") or body.get("data", {}).get("items", [])
    ids = {item["id"] for item in items}
    assert own.id in ids
    assert other_distribution.id not in ids

    detail_response = client.get(
        f"{base}/bonus/payment/distributions/{other_distribution.id}",
        headers=headers,
    )
    assert detail_response.status_code == 404, detail_response.text

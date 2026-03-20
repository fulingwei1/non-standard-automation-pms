# -*- coding: utf-8 -*-
"""
sales/targets.py 端点单元测试
"""

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import patch

from sqlalchemy.orm import Session

from app.common.pagination import get_pagination_params
from app.models.organization import Department
from app.models.project.customer import Customer
from app.models.sales import Lead, SalesTarget
from app.models.user import User


def _suffix() -> str:
    return uuid4().hex[:8]


def _create_department(db: Session) -> Department:
    dept = Department(
        dept_code=f"DEP-{_suffix()}",
        dept_name=f"销售目标部-{_suffix()}",
        is_active=True,
    )
    db.add(dept)
    db.flush()
    return dept


def _create_user(db: Session, department: Department) -> User:
    user = User(
        username=f"target_user_{_suffix()}",
        password_hash="hashed-password",
        real_name="目标负责人",
        department_id=department.id,
        department=department.dept_name,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def _create_customer(db: Session) -> Customer:
    customer = Customer(
        customer_code=f"CUST-{_suffix()}",
        customer_name=f"接口测试客户-{_suffix()}",
        status="ACTIVE",
    )
    db.add(customer)
    db.flush()
    return customer


class TestSalesTargetsEndpoint:

    def test_get_sales_targets_returns_real_actual_value(self, db_session: Session):
        from app.api.v1.endpoints.sales.targets import get_sales_targets

        department = _create_department(db_session)
        owner = _create_user(db_session, department)
        _create_customer(db_session)

        db_session.add_all(
            [
                Lead(
                    lead_code=f"LEAD-{_suffix()}",
                    customer_name="客户A",
                    owner_id=owner.id,
                    created_at=datetime(2026, 1, 3, 10, 0, 0),
                ),
                Lead(
                    lead_code=f"LEAD-{_suffix()}",
                    customer_name="客户B",
                    owner_id=owner.id,
                    created_at=datetime(2026, 1, 20, 9, 0, 0),
                ),
                Lead(
                    lead_code=f"LEAD-{_suffix()}",
                    customer_name="客户C",
                    owner_id=owner.id,
                    created_at=datetime(2026, 2, 2, 12, 0, 0),
                ),
            ]
        )

        target = SalesTarget(
            target_scope="PERSONAL",
            user_id=owner.id,
            department_id=department.id,
            target_type="LEAD_COUNT",
            target_period="MONTHLY",
            period_value="2026-01",
            target_value=Decimal("4"),
            created_by=owner.id,
        )
        db_session.add(target)
        db_session.flush()

        current_user = SimpleNamespace(id=999, department_id=None, department=None)

        with patch("app.api.v1.endpoints.sales.targets.get_user_role_code", return_value="SALES_DIR"):
            result = get_sales_targets(
                db=db_session,
                pagination=get_pagination_params(page=1, page_size=20),
                target_scope=None,
                target_type=None,
                target_period=None,
                period_value=None,
                user_id=None,
                department_id=None,
                status=None,
                current_user=current_user,
            )

        assert result.total >= 1
        first_item = result.items[0]
        assert first_item["actual_value"] == 2.0
        assert first_item["completion_rate"] == 50.0
        assert first_item["user_name"] == "目标负责人"
        assert first_item["department_name"] == department.dept_name

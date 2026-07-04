# -*- coding: utf-8 -*-
"""AS-09: after-sales endpoints must not 500 when optional tables are absent."""

from datetime import date

import pytest
from sqlalchemy import inspect

from app.api.v1.endpoints import after_sales
from app.models.after_sales import (
    AfterSalesFieldService,
    AfterSalesKnowledge,
    AfterSalesSLA,
    AfterSalesSatisfaction,
    AfterSalesSparePart,
    AfterSalesWarranty,
)
from app.models.project import Customer, Project
from app.models.user import User


def _user(username: str) -> User:
    return User(
        username=username,
        password_hash="x",
        real_name=username.title(),
        is_active=True,
        is_superuser=True,
    )


def _project(db_session):
    customer = Customer(customer_code="AS09-CUST", customer_name="AS09 客户")
    db_session.add(customer)
    db_session.flush()
    project = Project(
        project_code="AS09-PROJ",
        project_name="AS09 项目",
        customer_id=customer.id,
    )
    db_session.add(project)
    db_session.flush()
    return project


def _drop_table(db_session, model) -> None:
    bind = db_session.get_bind()
    db_session.commit()
    model.__table__.drop(bind=bind, checkfirst=True)
    db_session.expire_all()


def _table_exists(db_session, model) -> bool:
    return inspect(db_session.get_bind()).has_table(model.__tablename__)


@pytest.mark.parametrize(
    ("model", "call", "assert_empty"),
    [
        (
            AfterSalesWarranty,
            lambda db, project, user: after_sales.get_warranty(project.id, db=db, current_user=user),
            lambda result: result == [],
        ),
        (
            AfterSalesSparePart,
            lambda db, project, user: after_sales.get_spare_parts(project.id, db=db, current_user=user),
            lambda result: result == [],
        ),
        (
            AfterSalesFieldService,
            lambda db, project, user: after_sales.get_field_services(project.id, db=db, current_user=user),
            lambda result: result == [],
        ),
        (
            AfterSalesSLA,
            lambda db, project, user: after_sales.get_sla_stats(project.id, db=db, current_user=user),
            lambda result: result["total"] == 0,
        ),
        (
            AfterSalesSatisfaction,
            lambda db, project, user: after_sales.get_satisfaction(project.id, db=db, current_user=user),
            lambda result: result["total"] == 0,
        ),
        (
            AfterSalesKnowledge,
            lambda db, project, user: after_sales.search_knowledge(
                keyword="",
                category=None,
                db=db,
                current_user=user,
            ),
            lambda result: result == [],
        ),
    ],
)
def test_after_sales_read_endpoints_recreate_missing_tables(
    db_session,
    model,
    call,
    assert_empty,
):
    user = _user("as09-reader")
    db_session.add(user)
    project = _project(db_session)

    _drop_table(db_session, model)

    result = call(db_session, project, user)

    assert assert_empty(result)
    assert _table_exists(db_session, model)


@pytest.mark.parametrize(
    ("model", "call", "id_field"),
    [
        (
            AfterSalesWarranty,
            lambda db, project, user: after_sales.create_warranty(
                project_id=project.id,
                warranty_type="STANDARD",
                warranty_months=12,
                scope="整机",
                db=db,
                current_user=user,
            ),
            "id",
        ),
        (
            AfterSalesSparePart,
            lambda db, project, user: after_sales.create_spare_part(
                project_id=project.id,
                part_name="测试备件",
                part_spec="SP-09",
                quantity=2,
                supplier="供应商",
                db=db,
                current_user=user,
            ),
            "id",
        ),
        (
            AfterSalesFieldService,
            lambda db, project, user: after_sales.create_field_service(
                project_id=project.id,
                service_type="REPAIR",
                service_content="现场维修",
                planned_date=date(2026, 7, 4),
                engineer_name="工程师",
                db=db,
                current_user=user,
            ),
            "id",
        ),
        (
            AfterSalesSatisfaction,
            lambda db, project, user: after_sales.create_satisfaction(
                project_id=project.id,
                overall_score=9,
                response_score=9,
                quality_score=9,
                attitude_score=9,
                nps_score=9,
                comments="满意",
                db=db,
                current_user=user,
            ),
            "id",
        ),
        (
            AfterSalesKnowledge,
            lambda db, project, user: after_sales.create_knowledge(
                title="常见问题",
                category="FAQ",
                content="处理方法",
                keywords="FAQ",
                project_type="ICT",
                db=db,
                current_user=user,
            ),
            "id",
        ),
    ],
)
def test_after_sales_write_endpoints_recreate_missing_tables(
    db_session,
    model,
    call,
    id_field,
):
    user = _user("as09-writer")
    db_session.add(user)
    project = _project(db_session)

    _drop_table(db_session, model)

    result = call(db_session, project, user)

    assert result[id_field] > 0
    assert _table_exists(db_session, model)

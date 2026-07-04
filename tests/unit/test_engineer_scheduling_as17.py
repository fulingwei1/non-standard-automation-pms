# -*- coding: utf-8 -*-
"""AS-17: engineer scheduling frontend routes must exist on the backend."""

from datetime import date

from fastapi.routing import APIRoute

from app.api.v1.endpoints.engineer_scheduling import (
    create_assignment,
    delete_assignment,
    get_engineer_availability,
    get_workload_board,
    router,
    update_assignment,
)
from app.models.project import Customer, Project
from app.models.user import User


def test_engineer_scheduling_frontend_routes_are_registered():
    routes = {
        (route.path, method)
        for route in router.routes
        if isinstance(route, APIRoute)
        for method in route.methods
    }

    assert ("/workload-board", "GET") in routes
    assert ("/engineers/{engineer_id}/availability", "GET") in routes
    assert ("/assignments/{assignment_id}", "PUT") in routes
    assert ("/assignments/{assignment_id}", "DELETE") in routes


def test_engineer_scheduling_frontend_routes_work(db_session):
    engineer = User(
        username="as17-engineer",
        password_hash="x",
        real_name="AS17 工程师",
        is_active=True,
    )
    current_user = User(
        username="as17-admin",
        password_hash="x",
        real_name="AS17 Admin",
        is_active=True,
        is_superuser=True,
    )
    customer = Customer(customer_code="AS17-CUST", customer_name="AS17 客户")
    db_session.add_all([engineer, current_user, customer])
    db_session.flush()
    project = Project(
        project_code="AS17-PROJ",
        project_name="AS17 项目",
        customer_id=customer.id,
        planned_start_date=date(2026, 7, 4),
        planned_end_date=date(2026, 7, 11),
    )
    db_session.add(project)
    db_session.commit()

    created = create_assignment(
        payload={
            "project_id": project.id,
            "engineer_id": engineer.id,
            "allocation_pct": 80,
            "estimated_hours": 16,
        },
        db=db_session,
        current_user=current_user,
    )

    board = get_workload_board(db=db_session, current_user=current_user)
    availability = get_engineer_availability(
        engineer_id=engineer.id,
        start_date="2026-07-04",
        end_date="2026-07-11",
        db=db_session,
        current_user=current_user,
    )
    updated = update_assignment(
        assignment_id=created["id"],
        payload={"allocation_pct": 60, "estimated_hours": 12},
        db=db_session,
        current_user=current_user,
    )
    deleted = delete_assignment(
        assignment_id=created["id"],
        db=db_session,
        current_user=current_user,
    )

    assert board["total"] >= 1
    assert board["items"][0]["engineer_id"] == engineer.id
    assert availability["engineer_id"] == engineer.id
    assert availability["is_available"] is True
    assert updated["id"] == created["id"]
    assert updated["allocation_pct"] == 60
    assert updated["estimated_hours"] == 12
    assert deleted["status"] == "CANCELLED"

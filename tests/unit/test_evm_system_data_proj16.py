# -*- coding: utf-8 -*-
import asyncio
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
import uuid

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.projects.costs.evm import calculate_evm_metrics, get_evm_analysis
from app.models.project import Project
from app.services.evm_service import EVMService


def _project(db_session):
    suffix = uuid.uuid4().hex[:8]
    project = Project(
        project_code=f"PJ-EVM-{suffix}",
        project_name="PROJ-16 系统推导 EVM 项目",
        stage="S2",
        status="ST02",
        health="H1",
        planned_start_date=date(2026, 1, 1),
        planned_end_date=date(2026, 1, 11),
        progress_pct=Decimal("40"),
        budget_amount=Decimal("1000.00"),
        actual_cost=Decimal("450.00"),
    )
    db_session.add(project)
    db_session.flush()
    return project


def test_system_evm_data_uses_project_plan_progress_and_actual_cost(db_session):
    project = _project(db_session)

    evm_data = EVMService(db_session).calculate_system_evm_data(
        project.id, period_type="MONTH", period_date=date(2026, 1, 6)
    )

    assert evm_data.id == 0
    assert evm_data.data_source == "SYSTEM"
    assert evm_data.planned_value == Decimal("500.0000")
    assert evm_data.earned_value == Decimal("400.0000")
    assert evm_data.actual_cost == Decimal("450.0000")
    assert evm_data.budget_at_completion == Decimal("1000.0000")
    assert evm_data.schedule_performance_index == Decimal("0.800000")
    assert evm_data.cost_performance_index == Decimal("0.888889")
    assert evm_data.planned_percent_complete == Decimal("50.00")
    assert evm_data.actual_percent_complete == Decimal("40.00")


def test_metrics_endpoint_derives_system_values_when_inputs_are_absent(db_session):
    project = _project(db_session)

    result = asyncio.run(
        calculate_evm_metrics(
            project.id,
            pv=None,
            ev=None,
            ac=None,
            bac=None,
            db=db_session,
            current_user=SimpleNamespace(id=1),
        )
    )

    assert result["data_source"] == "SYSTEM"
    assert result["pv"] == 1000.0
    assert result["ev"] == 400.0
    assert result["ac"] == 450.0
    assert result["bac"] == 1000.0


def test_evm_analysis_falls_back_to_system_snapshot_without_manual_data(db_session):
    project = _project(db_session)

    response = asyncio.run(
        get_evm_analysis.__wrapped__(
            project.id,
            db=db_session,
            current_user=SimpleNamespace(id=1, username="admin", is_superuser=True),
        )
    )

    assert response.latest_data is not None
    assert response.latest_data.id == 0
    assert response.latest_data.data_source == "SYSTEM"
    assert response.latest_data.earned_value == Decimal("400.0000")


def test_metrics_endpoint_rejects_partial_manual_inputs(db_session):
    project = _project(db_session)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            calculate_evm_metrics(
                project.id,
                pv=Decimal("100"),
                ev=None,
                ac=None,
                bac=None,
                db=db_session,
                current_user=SimpleNamespace(id=1),
            )
        )

    assert exc_info.value.status_code == 400
    assert "pv/ev/ac/bac" in exc_info.value.detail

# -*- coding: utf-8 -*-
"""RPT-14: cost dashboard chart configs must persist."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints.dashboard.cost_dashboard import (
    get_chart_config,
    router,
    save_chart_config,
)
from app.schemas.dashboard import ChartConfigSchema


def _chart_config() -> ChartConfigSchema:
    return ChartConfigSchema(
        chart_type="line",
        title="RPT14 monthly cost trend",
        x_axis="month",
        y_axis="actual_cost",
        data_source="monthly_costs",
        filters={"project_id": 7, "period": "month"},
        custom_metrics=["budget", "actual_cost", "variance"],
    )


def test_cost_dashboard_chart_config_save_then_get_round_trips(db_session: Session):
    user = SimpleNamespace(id=42)

    saved = save_chart_config(
        db=db_session,
        chart_config=_chart_config(),
        current_user=user,
    )

    assert saved.data.id is not None
    fetched = get_chart_config(
        db=db_session,
        config_id=saved.data.id,
        current_user=user,
    )

    assert fetched.data.id == saved.data.id
    assert fetched.data.chart_type == "line"
    assert fetched.data.title == "RPT14 monthly cost trend"
    assert fetched.data.x_axis == "month"
    assert fetched.data.y_axis == "actual_cost"
    assert fetched.data.data_source == "monthly_costs"
    assert fetched.data.filters == {"project_id": 7, "period": "month"}
    assert fetched.data.custom_metrics == ["budget", "actual_cost", "variance"]


def test_cost_dashboard_chart_config_missing_id_returns_404(db_session: Session):
    with pytest.raises(HTTPException) as exc_info:
        get_chart_config(
            db=db_session,
            config_id=999999,
            current_user=SimpleNamespace(id=42),
        )

    assert exc_info.value.status_code == 404


def test_chart_config_get_route_is_registered_before_project_id_route():
    get_paths = [
        route.path
        for route in router.routes
        if "GET" in getattr(route, "methods", set())
    ]

    assert get_paths.index("/chart-config/{config_id}") < get_paths.index(
        "/{project_id}"
    )

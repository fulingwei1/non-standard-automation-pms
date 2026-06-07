# -*- coding: utf-8 -*-
"""项目数据流通 API 端点测试。"""

from unittest.mock import Mock

import pytest
from fastapi import HTTPException


def test_project_data_flow_routes_are_registered():
    from app.api.v1.endpoints.projects import router

    data_flow_paths = {
        route.path
        for route in router.routes
        if "data-flow" in getattr(route, "path", "")
    }

    assert data_flow_paths == {
        "/{project_id}/data-flow/wbs-work-orders",
        "/{project_id}/data-flow/bom-purchase-requests",
        "/{project_id}/data-flow/delivery-schedule",
        "/{project_id}/data-flow/after-sales",
    }


def test_create_work_orders_from_wbs_endpoint_invokes_service(monkeypatch, mock_db_session):
    from app.api.v1.endpoints.projects import data_flow

    current_user = Mock(id=7)
    service = Mock()
    service.create_work_orders_from_wbs.return_value = {
        "project_id": 42,
        "created_count": 2,
    }
    check_access = Mock()

    monkeypatch.setattr(data_flow, "check_project_access_or_raise", check_access)
    monkeypatch.setattr(data_flow, "get_project_data_flow_service", Mock(return_value=service))

    response = data_flow.create_work_orders_from_wbs(
        project_id=42,
        db=mock_db_session,
        current_user=current_user,
    )

    check_access.assert_called_once_with(mock_db_session, current_user, 42)
    service.create_work_orders_from_wbs.assert_called_once_with(42)
    assert response.code == 200
    assert response.data["created_count"] == 2


def test_create_delivery_schedule_endpoint_uses_current_user(monkeypatch, mock_db_session):
    from app.api.v1.endpoints.projects import data_flow

    current_user = Mock(id=7)
    service = Mock()
    service.create_delivery_schedule_from_project.return_value = {
        "project_id": 42,
        "schedule_id": 99,
    }
    monkeypatch.setattr(data_flow, "check_project_access_or_raise", Mock())
    monkeypatch.setattr(data_flow, "get_project_data_flow_service", Mock(return_value=service))

    response = data_flow.create_delivery_schedule_from_project(
        project_id=42,
        db=mock_db_session,
        current_user=current_user,
    )

    service.create_delivery_schedule_from_project.assert_called_once_with(
        42,
        initiator_id=7,
    )
    assert response.data["schedule_id"] == 99


def test_data_flow_endpoint_converts_service_error_to_http_400(monkeypatch, mock_db_session):
    from app.api.v1.endpoints.projects import data_flow

    current_user = Mock(id=7)
    service = Mock()
    service.create_purchase_requests_from_bom.return_value = {
        "error": "项目无 BOM 数据",
    }
    monkeypatch.setattr(data_flow, "check_project_access_or_raise", Mock())
    monkeypatch.setattr(data_flow, "get_project_data_flow_service", Mock(return_value=service))

    with pytest.raises(HTTPException) as exc:
        data_flow.create_purchase_requests_from_bom(
            project_id=42,
            db=mock_db_session,
            current_user=current_user,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "项目无 BOM 数据"

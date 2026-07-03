# -*- coding: utf-8 -*-
"""OpenAPI route contract regressions."""

import re
from collections import defaultdict

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.core.config import settings


HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_openapi_path_parameters_match_route_paths(
    client: TestClient, admin_token: str
):
    response = client.get(
        f"{settings.API_V1_PREFIX}/openapi.json",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    spec = response.json()
    missing = []
    extra = []

    for path, operations in spec.get("paths", {}).items():
        expected = set(re.findall(r"\{([^}]+)\}", path))
        for method, details in operations.items():
            if method not in HTTP_METHODS:
                continue

            declared = {
                param.get("name")
                for param in details.get("parameters", [])
                if param.get("in") == "path"
            }
            missing_params = sorted(expected - declared)
            extra_params = sorted(declared - expected)
            if missing_params:
                missing.append(
                    {
                        "method": method.upper(),
                        "path": path,
                        "operationId": details.get("operationId"),
                        "missing": missing_params,
                    }
                )
            if extra_params:
                extra.append(
                    {
                        "method": method.upper(),
                        "path": path,
                        "operationId": details.get("operationId"),
                        "extra": extra_params,
                    }
                )

    assert not missing
    assert not extra


def test_openapi_operation_ids_are_unique(client: TestClient, admin_token: str):
    response = client.get(
        f"{settings.API_V1_PREFIX}/openapi.json",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    spec = response.json()
    operation_ids = {}
    duplicates = {}

    for path, operations in spec.get("paths", {}).items():
        for method, details in operations.items():
            if method not in HTTP_METHODS:
                continue

            operation_id = details.get("operationId")
            if not operation_id:
                continue

            item = {"method": method.upper(), "path": path}
            if operation_id in operation_ids:
                duplicates.setdefault(operation_id, [operation_ids[operation_id]]).append(item)
            else:
                operation_ids[operation_id] = item

    assert not duplicates


def test_registered_api_routes_do_not_duplicate_method_paths(client: TestClient):
    routes_by_key = defaultdict(list)

    for route in client.app.routes:
        if not isinstance(route, APIRoute):
            continue

        for method in route.methods or []:
            if method in {"HEAD", "OPTIONS"}:
                continue
            routes_by_key[(method, route.path)].append(
                f"{route.endpoint.__module__}.{route.endpoint.__qualname__}"
            )

    duplicates = {
        f"{method} {path}": sorted(endpoints)
        for (method, path), endpoints in sorted(routes_by_key.items())
        if len(endpoints) > 1
    }

    assert not duplicates


def test_after_sales_routes_are_registered():
    from app.api.v1.api import create_api_router

    router = create_api_router()
    registered = {
        (method, route.path)
        for route in router.routes
        if isinstance(route, APIRoute)
        for method in route.methods or []
        if method not in {"HEAD", "OPTIONS"}
    }

    assert ("GET", "/after-sales/projects/{project_id}/feedback") in registered
    assert ("GET", "/after-sales/projects/{project_id}/maintenance") in registered
    assert (
        "GET",
        "/after-sales/projects/{project_id}/support-tickets",
    ) in registered


def test_qualification_model_detail_route_is_registered():
    from app.api.v1.api import create_api_router

    router = create_api_router()
    registered = {
        (method, route.path)
        for route in router.routes
        if isinstance(route, APIRoute)
        for method in route.methods or []
        if method not in {"HEAD", "OPTIONS"}
    }

    assert ("GET", "/qualifications/models/{model_id}") in registered


def test_batch2_dynamic_detail_routes_are_registered():
    from app.api.v1.api import create_api_router

    router = create_api_router()
    registered = {
        (method, route.path)
        for route in router.routes
        if isinstance(route, APIRoute)
        for method in route.methods or []
        if method not in {"HEAD", "OPTIONS"}
    }

    assert ("GET", "/purchase-orders/goods-receipts/{receipt_id}") in registered
    assert ("GET", "/purchase-orders/goods-receipts/{receipt_id}/items") in registered
    assert ("PUT", "/purchase-orders/goods-receipts/{receipt_id}/receive") in registered
    assert ("GET", "/stage-templates/{template_id}") in registered
    assert ("GET", "/schedule-generation/schedule-plans/{plan_id}") in registered
    assert ("GET", "/kit-rate/project/{project_id}/time-based-kit-rate") in registered
    assert ("GET", "/projects/{project_id}/overview") in registered


def test_batch3_dynamic_detail_routes_are_registered():
    from app.api.v1.api import create_api_router

    router = create_api_router()
    registered = {
        (method, route.path)
        for route in router.routes
        if isinstance(route, APIRoute)
        for method in route.methods or []
        if method not in {"HEAD", "OPTIONS"}
    }

    assert ("POST", "/team-generation/projects/{project_id}/generate-team") in registered
    assert ("POST", "/team-generation/projects/{project_id}/save-team-plan") in registered
    assert ("POST", "/team-generation/team-plans/{plan_id}/submit") in registered
    assert ("GET", "/template-configs/configs/{config_id}") in registered
    assert ("GET", "/warehouse/inbound/{order_id}") in registered
    assert ("GET", "/warehouse/outbound/{order_id}") in registered


def test_multirole_project_detail_legacy_routes_are_registered():
    from app.api.v1.api import create_api_router

    router = create_api_router()
    registered = {
        (method, route.path)
        for route in router.routes
        if isinstance(route, APIRoute)
        for method in route.methods or []
        if method not in {"HEAD", "OPTIONS"}
    }

    assert ("GET", "/members/projects/{project_id}/members") in registered
    assert ("GET", "/stages/projects/{project_id}/stages") in registered

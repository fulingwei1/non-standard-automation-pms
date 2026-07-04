# -*- coding: utf-8 -*-
"""MISC-18 business-support frontend route contracts."""

from fastapi.routing import APIRoute


def _method_paths(router) -> set[tuple[str, str]]:
    return {
        (method, route.path)
        for route in router.routes
        if isinstance(route, APIRoute)
        for method in route.methods or []
        if method not in {"HEAD", "OPTIONS"}
    }


def test_business_support_frontend_routes_are_registered_under_expected_prefix():
    from app.api.v1.api import api_router

    registered = _method_paths(api_router)

    expected_routes = {
        ("GET", "/business-support/dashboard"),
        ("GET", "/business-support/dashboard/active-contracts"),
        ("GET", "/business-support/dashboard/active-bidding"),
        ("GET", "/business-support/dashboard/todos"),
        ("GET", "/business-support/bidding"),
        ("POST", "/business-support/bidding"),
        ("GET", "/business-support/bidding/{bidding_id}"),
        ("PUT", "/business-support/bidding/{bidding_id}"),
        ("GET", "/business-support/contract-review"),
        ("POST", "/business-support/contract-review"),
        ("GET", "/business-support/contract-review/{review_id}"),
        ("PUT", "/business-support/contract-review/{review_id}"),
        ("GET", "/business-support/payment-reminder"),
        ("POST", "/business-support/payment-reminder"),
        ("GET", "/business-support/payment-reminder/{reminder_id}"),
        ("PUT", "/business-support/payment-reminder/{reminder_id}"),
    }

    assert not sorted(expected_routes - registered)

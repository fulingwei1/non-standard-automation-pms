# -*- coding: utf-8 -*-
"""销售聚合路由 import 守护。"""


def test_sales_router_imports_and_exposes_contract_amendment_route():
    from app.api.v1.endpoints.sales import router

    paths = {route.path for route in router.routes}

    assert "/contracts/{contract_id}/amendments" in paths

import asyncio
import importlib
import importlib.util
import sys
from datetime import date
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request


FALLBACK_MODULES = [
    "app.api.v1.endpoints.account_unlock",
    "app.api.v1.endpoints.audits",
    "app.api.v1.endpoints.backup",
    "app.api.v1.endpoints.change_impact",
    "app.api.v1.endpoints.cost_collection",
    "app.api.v1.endpoints.cost_variance_analysis",
    "app.api.v1.endpoints.culture_wall_config",
    "app.api.v1.endpoints.engineer_scheduling",
    "app.api.v1.endpoints.field_commissioning",
    "app.api.v1.endpoints.gantt_dependency",
    "app.api.v1.endpoints.inventory_analysis",
    "app.api.v1.endpoints.itr",
    "app.api.v1.endpoints.lessons_learned",
    "app.api.v1.endpoints.margin_prediction",
    "app.api.v1.endpoints.multi_currency",
    "app.api.v1.endpoints.project_contributions",
    "app.api.v1.endpoints.project_workspace",
    "app.api.v1.endpoints.quality_risk",
    "app.api.v1.endpoints.quote_actual_compare",
    "app.api.v1.endpoints.requirement_extraction",
    "app.api.v1.endpoints.resource_overview",
    "app.api.v1.endpoints.resource_scheduling",
    "app.api.v1.endpoints.schedule_generation",
    "app.api.v1.endpoints.schedule_optimization",
    "app.api.v1.endpoints.stage_templates",
    "app.api.v1.endpoints.team_generation",
]


def _load_module_from_path(module_name, relative_path):
    root = Path(__file__).resolve().parents[2]
    module_path = root / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("module_name", FALLBACK_MODULES)
def test_fallback_endpoint_modules_export_callable_router(module_name):
    module = importlib.import_module(module_name)

    assert hasattr(module, "router")
    assert len(module.router.routes) == 1
    assert module.router.routes[0].endpoint()["message"].endswith("module placeholder")


def test_stub_endpoints_cover_auth_and_strict_mode():
    module = importlib.import_module("app.api.v1.endpoints.stub_endpoints")
    module.ALLOW_STUB_SUCCESS = False

    auth_request = Request({"type": "http", "method": "GET", "path": "/auth/login", "headers": []})
    strict_request = Request({"type": "http", "method": "POST", "path": "/demo", "headers": []})

    auth_response = asyncio.run(module.stub_handler(auth_request, "auth/login"))
    strict_response = asyncio.run(module.stub_handler(strict_request, "demo"))

    assert auth_response.status_code == 404
    assert strict_response.status_code == 501


def test_stub_endpoints_cover_success_modes():
    module = importlib.import_module("app.api.v1.endpoints.stub_endpoints")
    module.ALLOW_STUB_SUCCESS = True

    get_request = Request({"type": "http", "method": "GET", "path": "/demo", "headers": []})
    post_request = Request({"type": "http", "method": "POST", "path": "/demo", "headers": []})

    get_response = asyncio.run(module.stub_handler(get_request, "demo"))
    post_response = asyncio.run(module.stub_handler(post_request, "demo"))

    assert get_response.status_code == 200
    assert post_response.status_code == 200


def test_tenants_module_falls_back_to_placeholder_router(monkeypatch):
    monkeypatch.setitem(sys.modules, "app.api.v1.endpoints.auth", ModuleType("app.api.v1.endpoints.auth"))
    sys.modules.pop("app.api.v1.endpoints.tenants", None)

    module = importlib.import_module("app.api.v1.endpoints.tenants")

    assert len(module.router.routes) == 1
    assert module.router.routes[0].endpoint() == {"message": "tenants module placeholder"}


def _install_alert_trends_stubs(monkeypatch, date_range=None, trend_stats=None):
    deps_mod = ModuleType("app.api.deps")
    deps_mod.get_db = lambda: None
    monkeypatch.setitem(sys.modules, "app.api.deps", deps_mod)

    core_mod = ModuleType("app.core")
    core_mod.security = SimpleNamespace(get_current_active_user=lambda: None)
    monkeypatch.setitem(sys.modules, "app.core", core_mod)

    alert_mod = ModuleType("app.models.alert")

    class _Field:
        def isnot(self, _value):
            return ("isnot", _value)

        def __eq__(self, other):
            return ("eq", other)

        def __ge__(self, other):
            return ("ge", other)

        def __le__(self, other):
            return ("le", other)

    class AlertRecord:
        triggered_at = _Field()
        project_id = _Field()

    alert_mod.AlertRecord = AlertRecord
    monkeypatch.setitem(sys.modules, "app.models.alert", alert_mod)

    user_mod = ModuleType("app.models.user")
    user_mod.User = object
    monkeypatch.setitem(sys.modules, "app.models.user", user_mod)

    service_mod = ModuleType("app.services.alert.alert_trend_service")
    service_mod.build_trend_statistics = lambda alerts, period: trend_stats or {
        "date_trends": {},
        "level_trends": {},
        "type_trends": {},
        "status_trends": {},
    }
    service_mod.generate_date_range = lambda start, end, period: date_range or []
    service_mod.build_summary_statistics = lambda alerts: {"by_level": {}, "by_type": {}, "by_status": {}}
    monkeypatch.setitem(sys.modules, "app.services.alert.alert_trend_service", service_mod)

    sys.modules.pop("app.api.v1.endpoints.alerts.statistics.trends", None)
    return _load_module_from_path(
        "app.api.v1.endpoints.alerts.statistics.trends",
        "app/api/v1/endpoints/alerts/statistics/trends.py",
    )


def test_alert_trends_applies_project_filter(monkeypatch):
    module = _install_alert_trends_stubs(monkeypatch)

    class FakeQuery:
        def __init__(self):
            self.filters = []

        def filter(self, *args):
            self.filters.append(args)
            return self

        def all(self):
            return []

    class FakeDB:
        def __init__(self):
            self.query_obj = FakeQuery()

        def query(self, _model):
            return self.query_obj

    db = FakeDB()
    result = module.get_alert_trends(
        db=db,
        project_id=123,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 4, 14),
        period="DAILY",
        current_user=object(),
    )

    assert any(("eq", 123) in args for args in db.query_obj.filters)
    assert result["period"] == "DAILY"


def test_alert_trends_fills_default_dates_and_builds_trend_rows(monkeypatch):
    module = _install_alert_trends_stubs(
        monkeypatch,
        date_range=["2026-04-14"],
        trend_stats={
            "date_trends": {"2026-04-14": 2},
            "level_trends": {"2026-04-14": {"HIGH": 1}},
            "type_trends": {"2026-04-14": {"质量": 2}},
            "status_trends": {"2026-04-14": {"OPEN": 2}},
        },
    )

    class FakeQuery:
        def filter(self, *args):
            return self

        def all(self):
            return [object(), object()]

    class FakeDB:
        def query(self, _model):
            return FakeQuery()

    result = module.get_alert_trends(
        db=FakeDB(),
        project_id=None,
        start_date=None,
        end_date=None,
        period="DAILY",
        current_user=object(),
    )

    assert result["trends"][0]["total"] == 2
    assert result["summary"]["total"] == 2


def test_customer_related_rejects_forbidden_access(monkeypatch):
    deps_mod = ModuleType("app.api.deps")
    deps_mod.get_db = lambda: None
    monkeypatch.setitem(sys.modules, "app.api.deps", deps_mod)

    pagination_mod = ModuleType("app.common.pagination")

    class PaginationParams:
        offset = 0
        limit = 20
        page = 1
        page_size = 20

        def pages_for_total(self, total):
            return 0

    pagination_mod.PaginationParams = PaginationParams
    pagination_mod.get_pagination_query = lambda: PaginationParams()
    monkeypatch.setitem(sys.modules, "app.common.pagination", pagination_mod)

    query_filters_mod = ModuleType("app.common.query_filters")
    query_filters_mod.apply_pagination = lambda query, offset, limit: query
    monkeypatch.setitem(sys.modules, "app.common.query_filters", query_filters_mod)

    core_mod = ModuleType("app.core")
    core_mod.security = SimpleNamespace(require_permission=lambda _perm: (lambda: None))
    monkeypatch.setitem(sys.modules, "app.core", core_mod)

    sales_permissions_mod = ModuleType("app.core.sales_permissions")
    sales_permissions_mod.check_sales_data_permission = lambda *args, **kwargs: False
    monkeypatch.setitem(sys.modules, "app.core.sales_permissions", sales_permissions_mod)

    project_mod = ModuleType("app.models.project")
    project_mod.Customer = object
    project_mod.Project = SimpleNamespace(customer_id="customer_id", created_at="created_at")
    monkeypatch.setitem(sys.modules, "app.models.project", project_mod)

    user_mod = ModuleType("app.models.user")
    user_mod.User = object
    monkeypatch.setitem(sys.modules, "app.models.user", user_mod)

    schema_mod = ModuleType("app.schemas.common")
    schema_mod.PaginatedResponse = lambda **kwargs: kwargs
    monkeypatch.setitem(sys.modules, "app.schemas.common", schema_mod)

    helpers_mod = ModuleType("app.utils.db_helpers")
    helpers_mod.get_or_404 = lambda db, model, customer_id, msg: object()
    monkeypatch.setitem(sys.modules, "app.utils.db_helpers", helpers_mod)

    sys.modules.pop("app.api.v1.endpoints.customers.related", None)
    module = _load_module_from_path(
        "app.api.v1.endpoints.customers.related",
        "app/api/v1/endpoints/customers/related.py",
    )

    with pytest.raises(HTTPException) as exc:
        module.get_customer_projects(
            db=object(),
            customer_id=1,
            pagination=PaginationParams(),
            current_user=object(),
        )

    assert exc.value.detail == "无权访问该客户的项目列表"


def test_customer_related_returns_paginated_projects(monkeypatch):
    deps_mod = ModuleType("app.api.deps")
    deps_mod.get_db = lambda: None
    monkeypatch.setitem(sys.modules, "app.api.deps", deps_mod)

    pagination_mod = ModuleType("app.common.pagination")

    class PaginationParams:
        offset = 0
        limit = 20
        page = 1
        page_size = 20

        def pages_for_total(self, total):
            return 1

    pagination_mod.PaginationParams = PaginationParams
    pagination_mod.get_pagination_query = lambda: PaginationParams()
    monkeypatch.setitem(sys.modules, "app.common.pagination", pagination_mod)

    query_filters_mod = ModuleType("app.common.query_filters")
    query_filters_mod.apply_pagination = lambda query, offset, limit: query
    monkeypatch.setitem(sys.modules, "app.common.query_filters", query_filters_mod)

    core_mod = ModuleType("app.core")
    core_mod.security = SimpleNamespace(require_permission=lambda _perm: (lambda: None))
    monkeypatch.setitem(sys.modules, "app.core", core_mod)

    sales_permissions_mod = ModuleType("app.core.sales_permissions")
    sales_permissions_mod.check_sales_data_permission = lambda *args, **kwargs: True
    monkeypatch.setitem(sys.modules, "app.core.sales_permissions", sales_permissions_mod)

    class _Field:
        def desc(self):
            return self

    project_mod = ModuleType("app.models.project")
    project_mod.Customer = object
    project_mod.Project = SimpleNamespace(customer_id=_Field(), created_at=_Field())
    monkeypatch.setitem(sys.modules, "app.models.project", project_mod)

    user_mod = ModuleType("app.models.user")
    user_mod.User = object
    monkeypatch.setitem(sys.modules, "app.models.user", user_mod)

    schema_mod = ModuleType("app.schemas.common")
    schema_mod.PaginatedResponse = lambda **kwargs: kwargs
    monkeypatch.setitem(sys.modules, "app.schemas.common", schema_mod)

    helpers_mod = ModuleType("app.utils.db_helpers")
    helpers_mod.get_or_404 = lambda db, model, customer_id, msg: object()
    monkeypatch.setitem(sys.modules, "app.utils.db_helpers", helpers_mod)

    sys.modules.pop("app.api.v1.endpoints.customers.related", None)
    module = _load_module_from_path(
        "app.api.v1.endpoints.customers.related",
        "app/api/v1/endpoints/customers/related.py",
    )
    module.desc = lambda value: value

    class FakeQuery:
        def filter(self, *args):
            return self

        def count(self):
            return 2

        def order_by(self, *args):
            return self

        def all(self):
            return ["p1", "p2"]

    class FakeDB:
        def query(self, _model):
            return FakeQuery()

    result = module.get_customer_projects(
        db=FakeDB(),
        customer_id=1,
        pagination=PaginationParams(),
        current_user=object(),
    )

    assert result["items"] == ["p1", "p2"]
    assert result["total"] == 2
